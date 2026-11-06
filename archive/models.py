import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

CONTENT_FIELDS = ('title', 'byline', 'kind', 'abstract', 'methods', 'claims', 'limitations',
                  'artifacts', 'provenance', 'license', 'ai_disclosure', 'change_note')

class Capacity(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    intake_open = models.BooleanField(default=False)
    queue_limit = models.PositiveSmallIntegerField(default=5)
    per_author_limit = models.PositiveSmallIntegerField(default=2)
    draft_limit = models.PositiveSmallIntegerField(default=20)
    revision = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(id=1), name='singleton_capacity'),
            models.CheckConstraint(condition=models.Q(queue_limit__gte=1, queue_limit__lte=20), name='bounded_queue'),
            models.CheckConstraint(condition=models.Q(per_author_limit__gte=1, per_author_limit__lte=5), name='bounded_author'),
            models.CheckConstraint(condition=models.Q(draft_limit__gte=1, draft_limit__lte=100), name='bounded_drafts')]

class Work(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    withdrawal_reason = models.CharField(max_length=1000, blank=True)

class Submission(models.Model):
    class State(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Awaiting human moderation'
        CHANGES = 'changes', 'Changes requested'
        DECLINED = 'declined', 'Declined; appeal available'
        PUBLISHED = 'published', 'Published'
    class Kind(models.TextChoices):
        EXPERIMENT = 'experiment', 'Experiment / replication'
        REPORT = 'report', 'Practice / negative result'
        TOOL = 'tool', 'Tool / dataset'
        IDEA = 'idea', 'Evidence-supported idea'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    work = models.ForeignKey(Work, null=True, blank=True, on_delete=models.PROTECT)
    state = models.CharField(max_length=16, choices=State, default=State.DRAFT)
    revision = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=200, blank=True)
    byline = models.CharField('Public author names', max_length=400, blank=True)
    kind = models.CharField(max_length=16, choices=Kind, default=Kind.REPORT)
    abstract = models.TextField(max_length=3000, blank=True)
    methods = models.TextField('Methods or linked methods', max_length=10000, blank=True)
    claims = models.TextField('Results and claims', max_length=10000, blank=True)
    limitations = models.TextField(max_length=5000, blank=True)
    artifacts = models.TextField('Public artifact links', max_length=8000, blank=True)
    provenance = models.TextField(max_length=5000, blank=True)
    license = models.CharField(max_length=16, choices=[('CC-BY-4.0', 'CC BY 4.0'), ('CC0-1.0', 'CC0 1.0')], blank=True)
    ai_disclosure = models.TextField('AI assistance disclosure', max_length=3000, blank=True)
    change_note = models.TextField('Revision or correction note', max_length=2000, blank=True)
    rights_confirmed = models.BooleanField(default=False)
    privacy_confirmed = models.BooleanField(default=False)
    frozen_snapshot = models.JSONField(default=dict)
    digest = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    def payload(self):
        return {key: getattr(self, key) for key in CONTENT_FIELDS}
    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(state__in=['draft','submitted','changes','declined','published']), name='valid_submission_state')]

class AppendOnly(models.Model):
    class Meta:
        abstract = True
    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Append-only record; create a new record instead.')
        return super().save(*args, **kwargs)
    def delete(self, *args, **kwargs):
        raise ValidationError('Append-only record cannot be deleted.')

class Version(AppendOnly):
    work = models.ForeignKey(Work, related_name='versions', on_delete=models.PROTECT)
    number = models.PositiveIntegerField()
    submission = models.OneToOneField(Submission, on_delete=models.PROTECT)
    snapshot = models.JSONField()
    digest = models.CharField(max_length=64)
    published_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['work','number'], name='unique_work_version')]
        ordering = ['-published_at', '-id']

class Decision(AppendOnly):
    submission = models.ForeignKey(Submission, related_name='decisions', on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    digest = models.CharField(max_length=64)
    action = models.CharField(max_length=16, choices=[('publish','Publish'),('changes','Request changes'),('decline','Decline')])
    reason = models.TextField(max_length=2000)
    conflicts = models.TextField(max_length=2000, default='Not recorded for this legacy decision')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['submission','revision'], name='unique_submission_decision')]
        ordering = ['created_at', 'id']

class Event(AppendOnly):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    kind = models.CharField(max_length=40)
    target = models.CharField(max_length=64)
    details = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

class Appeal(models.Model):
    decision = models.OneToOneField(Decision, on_delete=models.PROTECT)
    submission = models.ForeignKey(Submission, related_name='appeals', on_delete=models.PROTECT)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.TextField(max_length=2000)
    response = models.TextField(max_length=2000, blank=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT, related_name='+')
    resolved_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['submission'], condition=models.Q(resolved_at__isnull=True), name='one_open_appeal')]

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work = models.ForeignKey(Work, on_delete=models.PROTECT)
    reason = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.PROTECT)
    resolution = models.TextField(max_length=2000, blank=True)

class RateBucket(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField()

class WorkOSIdentity(models.Model):
    """Operator binding; emails and external roles never select a local account."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    client_id = models.CharField(max_length=128)
    subject = models.CharField(max_length=128)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['client_id', 'subject'], name='unique_workos_identity')]

class WorkOSLoginAttempt(models.Model):
    """Short-lived server-side PKCE exchange; consumed before any provider call."""
    state_hash = models.CharField(max_length=64, primary_key=True)
    browser_hash = models.CharField(max_length=64, unique=True)
    verifier = models.CharField(max_length=128)
    next_path = models.CharField(max_length=2048, default='/workspace/')
    expires_at = models.DateTimeField()


class WorkOSCredential(models.Model):
    """Provider tokens have durable consumption state independent of response saves."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField('sessions.Session', on_delete=models.CASCADE)
    identity = models.ForeignKey(WorkOSIdentity, on_delete=models.CASCADE)
    sealed = models.TextField()
    provider_session_id = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    claim = models.UUIDField(null=True, editable=False)
    claimed_at = models.DateTimeField(null=True, editable=False)
