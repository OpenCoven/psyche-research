"""The only application write boundary. No publication endpoint accepts an agent identity."""
import hashlib
import json
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from .forms import SubmissionForm
from .models import Capacity, Work, Submission, Version, Decision, Event, Appeal, Report, CONTENT_FIELDS

class WorkflowError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status

def is_moderator(user):
    return bool(user.is_authenticated and user.is_active and user.groups.filter(name='moderators').exists())

def human(user):
    if not user.is_authenticated or not user.is_active:
        raise WorkflowError('Sign in with an active contributor account.', 403)

def moderator(user):
    human(user)
    if not is_moderator(user):
        raise WorkflowError('A human moderator role is required.', 403)

def digest(snapshot):
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()

def event(actor, kind, target, **details):
    Event.objects.create(actor=actor, kind=kind, target=str(target), details=details)

def capacity():
    # The seeded singleton and SQLite BEGIN IMMEDIATE serialize limits and state changes.
    return Capacity.objects.select_for_update().get(pk=1)

def owned(user, submission_id):
    human(user)
    try:
        return Submission.objects.select_for_update().get(pk=submission_id, author=user)
    except Submission.DoesNotExist:
        raise WorkflowError('Submission not found.', 404)

def reason_text(reason, limit=2000):
    if not isinstance(reason, str) or not reason.strip() or len(reason) > limit:
        raise WorkflowError('Provide a nonempty reason within the stated limit.')
    return reason.strip()

@transaction.atomic
def create_submission(user, work_id=None):
    human(user)
    config = capacity()
    active = Submission.objects.filter(state__in=['draft','changes','submitted'])
    if active.filter(author=user).count() >= config.per_author_limit or active.count() >= config.draft_limit:
        raise WorkflowError('Active draft capacity is full. Resume existing work or try after the founder frees capacity.', 429)
    work = None
    initial = {}
    if work_id:
        try:
            work = Work.objects.select_for_update().get(pk=work_id, author=user, withdrawn_at__isnull=True)
        except Work.DoesNotExist:
            raise WorkflowError('Published work not found or unavailable for revision.', 404)
        if active.filter(work=work).exists():
            raise WorkflowError('Resume the existing revision draft.', 409)
        latest = work.versions.order_by('-number').first()
        if not latest:
            raise WorkflowError('Published version not found.', 404)
        initial = {k: v for k,v in latest.snapshot.items() if k in CONTENT_FIELDS}
        initial['change_note'] = ''
    row = Submission.objects.create(author=user, work=work, **initial)
    event(user, 'draft_created', row.id, revision_of=str(work.id) if work else None)
    return row

@transaction.atomic
def save_submission(user, submission_id, data, expected_revision, submit=False):
    config = capacity()
    row = owned(user, submission_id)
    if row.work_id and row.work.withdrawn_at:
        raise WorkflowError('Withdrawn work cannot receive a revision.', 409)
    allowed = set(CONTENT_FIELDS) | {'rights_confirmed','privacy_confirmed'}
    if set(data) - allowed:
        raise WorkflowError('Unknown submission fields.')
    values = {key: data.get(key, getattr(row,key)) for key in allowed}
    bound = SubmissionForm({**values, 'revision': expected_revision}, instance=Submission())
    if not bound.is_valid():
        raise WorkflowError('Check the field lengths, choices and artifact links.')
    clean = bound.cleaned_data
    payload = {k: clean[k] for k in CONTENT_FIELDS}
    if (submit and row.state == Submission.State.SUBMITTED and row.revision == expected_revision + 1
            and row.frozen_snapshot == payload and clean['rights_confirmed'] and clean['privacy_confirmed']):
        return row  # Safe duplicate retry after a lost response, with identical exact content.
    if row.state not in [Submission.State.DRAFT, Submission.State.CHANGES]:
        raise WorkflowError('This submission is frozen. A moderator must request changes, or start a revision after publication.', 409)
    if row.revision != expected_revision:
        raise WorkflowError('A newer save exists. Reload the saved draft before editing again.', 409)
    for key in allowed:
        setattr(row, key, clean[key])
    if submit:
        required = ['title','byline','kind','abstract','methods','claims','limitations','provenance','license','ai_disclosure']
        if any(not str(getattr(row,k)).strip() for k in required) or not row.rights_confirmed or not row.privacy_confirmed:
            raise WorkflowError('Complete all research fields, license, AI disclosure, and rights/privacy confirmations before submitting.')
        if row.work_id and not row.change_note.strip():
            raise WorkflowError('Explain the revision or correction in a change note.')
        if not config.intake_open:
            raise WorkflowError('Intake is paused. Save your draft and return after the founder reopens intake.', 409)
        if not (settings.LOCAL_DEVELOPMENT or settings.PILOT_APPROVED):
            raise WorkflowError('Pilot acceptance has not been recorded; intake remains paused.', 409)
        queued = Submission.objects.filter(state=Submission.State.SUBMITTED)
        if queued.count() >= config.queue_limit or queued.filter(author=user).exists():
            raise WorkflowError('Moderation capacity is full. One queued submission per contributor is allowed.', 429)
        row.frozen_snapshot = row.payload()
        row.digest = digest(row.frozen_snapshot)
        row.state = Submission.State.SUBMITTED
        row.submitted_at = timezone.now()
    row.revision += 1
    row.save()
    event(user, 'submitted' if submit else 'draft_saved', row.id, revision=row.revision,
          digest=row.digest if submit else '')
    return row

@transaction.atomic
def decide(user, submission_id, action, reason, expected_revision, conflicts=None):
    moderator(user)
    capacity()
    if action not in ['publish','changes','decline']:
        raise WorkflowError('Unknown moderation action.')
    reason = reason_text(reason)
    conflicts = reason_text(conflicts)
    try:
        row = Submission.objects.select_for_update().get(pk=submission_id)
    except Submission.DoesNotExist:
        raise WorkflowError('Submission not found.', 404)
    if row.author_id == user.id:
        raise WorkflowError('You cannot moderate or approve your own submission.', 403)
    previous = Decision.objects.filter(submission=row, revision=expected_revision).first()
    if previous:
        if previous.actor_id == user.id and previous.action == action and previous.reason == reason and previous.conflicts == conflicts:
            return previous
        raise WorkflowError('This version already has a moderation decision.', 409)
    if row.state != Submission.State.SUBMITTED or row.revision != expected_revision:
        raise WorkflowError('The submitted version changed or was already decided. Reload the queue.', 409)
    if digest(row.frozen_snapshot) != row.digest or row.payload() != row.frozen_snapshot:
        raise WorkflowError('Submitted content integrity check failed. Pause and investigate.', 409)
    decision = Decision.objects.create(submission=row, actor=user, action=action, reason=reason,
                                      revision=row.revision, digest=row.digest, conflicts=conflicts)
    if action == 'publish':
        work = row.work
        if work and work.withdrawn_at:
            raise WorkflowError('Withdrawn work cannot be published.', 409)
        if work is None:
            work = Work.objects.create(author=row.author)
            row.work = work
        number = (work.versions.aggregate(n=Max('number'))['n'] or 0) + 1
        Version.objects.create(work=work, number=number, submission=row, snapshot=row.frozen_snapshot, digest=row.digest)
        row.state = Submission.State.PUBLISHED
    elif action == 'changes':
        row.state = Submission.State.CHANGES
    else:
        row.state = Submission.State.DECLINED
    row.revision += 1
    row.save()
    event(user, 'moderation_'+action, row.id, digest=decision.digest, revision=decision.revision)
    return decision

@transaction.atomic
def withdraw(user, work_id, reason):
    human(user)
    capacity()
    try:
        row = Work.objects.select_for_update().get(pk=work_id)
    except Work.DoesNotExist:
        raise WorkflowError('Work not found.', 404)
    if row.author_id != user.id and not is_moderator(user):
        raise WorkflowError('Work not found.', 404)
    if row.withdrawn_at:
        return row
    row.withdrawal_reason = reason_text(reason, 1000)
    row.withdrawn_at = timezone.now()
    row.save(update_fields=['withdrawn_at','withdrawal_reason'])
    event(user, 'withdrawn', row.id)
    return row

@transaction.atomic
def appeal(user, submission_id, reason):
    capacity()
    row = owned(user, submission_id)
    if row.state not in [Submission.State.DECLINED, Submission.State.CHANGES]:
        raise WorkflowError('Appeals are available after changes are requested or publication is declined.', 409)
    if row.appeals.filter(resolved_at__isnull=True).exists():
        raise WorkflowError('An appeal is already awaiting a human response.', 409)
    # Bound repeat appeals on one record; an operator can export and assess exceptional cases privately.
    if row.appeals.count() >= 3:
        raise WorkflowError('Appeal capacity reached; ask the operator for an exceptional-case review.', 429)
    source = row.decisions.order_by('-created_at','-id').first()
    if not source or Appeal.objects.filter(decision=source).exists():
        raise WorkflowError('One substantive appeal is available for each recorded decision.', 409)
    result = Appeal.objects.create(submission=row, decision=source, author=user, reason=reason_text(reason))
    event(user, 'appeal_opened', row.id, appeal=result.id)
    return result

@transaction.atomic
def resolve_appeal(user, appeal_id, reason, reopen=False):
    moderator(user)
    config = capacity()
    try:
        row = Appeal.objects.select_for_update().select_related('submission').get(pk=appeal_id)
    except Appeal.DoesNotExist:
        raise WorkflowError('Appeal not found.', 404)
    if row.author_id == user.id:
        raise WorkflowError('You cannot resolve your own appeal.', 403)
    if row.resolved_at:
        raise WorkflowError('This appeal already has a recorded response.', 409)
    row.response = reason_text(reason)
    row.resolved_by = user
    row.resolved_at = timezone.now()
    row.save()
    if reopen:
        submission = row.submission
        if submission.state not in [Submission.State.CHANGES, Submission.State.DECLINED]:
            raise WorkflowError('The submission moved on; do not overwrite its state.', 409)
        latest_decision = submission.decisions.order_by('-created_at','-id').first()
        if not latest_decision or row.decision_id != latest_decision.id:
            raise WorkflowError('This appeal concerns an earlier decision; record a response without reopening the newer decision.',409)
        if submission.state == Submission.State.DECLINED:
            active = Submission.objects.filter(state__in=['draft','changes','submitted']).exclude(pk=submission.pk)
            if active.filter(author_id=submission.author_id).count() >= config.per_author_limit or active.count() >= config.draft_limit:
                raise WorkflowError('Active draft capacity is full; resolve capacity before reopening.',429)
        submission.state = Submission.State.CHANGES
        submission.revision += 1
        submission.save()
    event(user, 'appeal_resolved', row.submission_id, appeal=row.id, reopen=bool(reopen))
    return row

@transaction.atomic
def configure(user, data, expected_revision, reason):
    moderator(user)
    row = capacity()
    if row.revision != expected_revision:
        raise WorkflowError('Capacity configuration changed. Reload before applying your change.', 409)
    if set(data) - {'intake_open','queue_limit','per_author_limit','draft_limit'}:
        raise WorkflowError('Unknown capacity fields.')
    for key,value in data.items():
        setattr(row,key,value)
    if row.intake_open and not (settings.LOCAL_DEVELOPMENT or settings.PILOT_APPROVED):
        raise WorkflowError('Pilot go/no-go acceptance is required before opening intake.', 409)
    try:
        row.full_clean()
    except ValidationError:
        raise WorkflowError('Capacity limits must remain within their permitted bounds.')
    reason = reason_text(reason,1000)
    row.revision += 1
    row.save()
    event(user, 'capacity_changed', 'capacity', intake_open=row.intake_open, queue_limit=row.queue_limit,
          per_author_limit=row.per_author_limit, draft_limit=row.draft_limit, reason=reason)
    return row

@transaction.atomic
def report(work_id, reason):
    capacity()
    if not Version.objects.filter(work_id=work_id).exists():
        raise WorkflowError('Published work not found.',404)
    if Report.objects.filter(resolved_at__isnull=True).count() >= 100 or Report.objects.filter(work_id=work_id,resolved_at__isnull=True).count() >= 10:
        raise WorkflowError('Report capacity is temporarily full. Use the operator contact listed in the policy.',429)
    row = Report.objects.create(work_id=work_id,reason=reason_text(reason))
    event(None,'abuse_reported',row.id)
    return row

@transaction.atomic
def resolve_report(user, report_id, reason):
    moderator(user)
    capacity()
    try:
        row=Report.objects.select_for_update().get(pk=report_id)
    except Report.DoesNotExist:
        raise WorkflowError('Report not found.',404)
    if row.resolved_at:
        raise WorkflowError('This report is already resolved.',409)
    row.resolution=reason_text(reason)
    row.resolved_by=user
    row.resolved_at=timezone.now()
    row.save()
    event(user,'report_resolved',row.id)
    return row
