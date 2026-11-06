"""Synthetic, separate-connection moderation probes for disposable databases only."""
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from itertools import combinations
from threading import Barrier, Event as ThreadEvent

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import close_old_connections, connection, transaction

from archive import services
from archive.models import Capacity, Decision, Event, Submission, Version
from archive.tests.test_guarantees import content


def run_moderation_races():
    """Caller owns a fresh migrated SQLite file or the PostgreSQL disposable schema."""
    users = get_user_model().objects
    moderator = users.create_user('synthetic-race-moderator')
    moderator.groups.add(Group.objects.get(name='moderators'))
    config = Capacity.objects.get(pk=1)
    assert not config.intake_open, 'Fresh migrations must pause intake'
    services.configure(moderator, {'intake_open': True}, config.revision, 'Synthetic race setup.')

    def wait_for_blocked_operation(holder, contender):
        attempted = ThreadEvent()

        def observe_lock(execute, sql, params, many, context):
            normalized = sql.upper()
            if normalized.startswith('BEGIN IMMEDIATE') or ('ARCHIVE_CAPACITY' in normalized and 'FOR UPDATE' in normalized):
                attempted.set()
            return execute(sql, params, many, context)

        def run_contender():
            close_old_connections()
            try:
                with connection.execute_wrapper(observe_lock):
                    return contender()
            finally:
                close_old_connections()

        # The outer transaction deliberately holds the actual production lock.
        # The second connection must reach the locking SQL and remain blocked.
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                holder()
                future = pool.submit(run_contender)
                assert attempted.wait(10), 'Contender never reached the database lock'
                try:
                    future.result(timeout=0.2)
                except TimeoutError:
                    pass
                else:
                    raise AssertionError('Contender completed before the capacity lock committed')
            return future.result(timeout=10)

    author = users.create_user('synthetic-pause-first-author')
    row = services.create_submission(author)
    config.refresh_from_db()

    def submit_after_pause():
        try:
            services.save_submission(author, row.pk, content(), row.revision, submit=True)
        except services.WorkflowError as error:
            assert error.status == 409 and 'paused' in str(error)
            return 'paused'
        raise AssertionError('Submission passed a pause committed before it acquired capacity')

    assert wait_for_blocked_operation(
        lambda: services.configure(moderator, {'intake_open': False}, config.revision, 'Synthetic pause wins.'),
        submit_after_pause,
    ) == 'paused'
    row.refresh_from_db()
    assert row.state == 'draft' and row.revision == 0 and not row.digest
    assert not Event.objects.filter(kind='submitted', target=str(row.pk)).exists()
    services.save_submission(author, row.pk, content(title='SYNTHETIC saved during pause'), row.revision)
    row.refresh_from_db()
    assert row.title == 'SYNTHETIC saved during pause' and row.state == 'draft'

    config.refresh_from_db()
    services.configure(moderator, {'intake_open': True}, config.revision, 'Synthetic second ordering setup.')
    second_author = users.create_user('synthetic-submit-first-author')
    second = services.create_submission(second_author)
    config.refresh_from_db()

    def pause_after_submit():
        services.configure(moderator, {'intake_open': False}, config.revision, 'Synthetic submit wins before pause.')
        return 'paused'

    assert wait_for_blocked_operation(
        lambda: services.save_submission(second_author, second.pk, content(), second.revision, submit=True),
        pause_after_submit,
    ) == 'paused'
    second.refresh_from_db()
    config.refresh_from_db()
    assert second.state == 'submitted' and second.frozen_snapshot == content_payload()
    assert second.digest == services.digest(second.frozen_snapshot) and not config.intake_open
    submitted_event = Event.objects.get(kind='submitted', target=str(second.pk))
    pause_event = Event.objects.filter(kind='capacity_changed').latest('id')
    assert submitted_event.id < pause_event.id
    assert pause_event.actor_id == moderator.pk and not pause_event.details['intake_open']
    assert pause_event.details['reason'] == 'Synthetic submit wins before pause.'
    # A lost-response retry acknowledges the prior committed submission, even paused.
    services.save_submission(second_author, second.pk, content(), 0, submit=True)
    assert Event.objects.filter(kind='submitted', target=str(second.pk)).count() == 1

    services.configure(moderator, {'intake_open': True}, config.revision, 'Synthetic conflicting-decision setup.')
    results = []
    for index, actions in enumerate(combinations(('publish', 'changes', 'decline'), 2)):
        actor = users.create_user(f'synthetic-conflicting-author-{index}')
        queued = services.create_submission(actor)
        queued = services.save_submission(actor, queued.pk, content(), 0, submit=True)
        barrier = Barrier(2)

        def decide(action):
            close_old_connections()
            try:
                barrier.wait(timeout=10)
                try:
                    result = services.decide(moderator, queued.pk, action, 'Synthetic competing decision.', queued.revision, conflicts='None; synthetic fixture')
                    return action, result.pk
                except services.WorkflowError as error:
                    assert error.status == 409
                    return 'conflict', None
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(decide, action) for action in actions]
            outcomes = [future.result(timeout=15) for future in futures]
        assert sum(action == 'conflict' for action, _ in outcomes) == 1, outcomes
        decision = Decision.objects.get(submission=queued)
        assert (decision.action, decision.pk) in outcomes
        assert decision.digest == queued.digest and decision.revision == queued.revision
        queued.refresh_from_db()
        expected = {'publish': 'published', 'changes': 'changes', 'decline': 'declined'}[decision.action]
        assert queued.state == expected
        assert queued.revision == decision.revision + 1
        versions = Version.objects.filter(submission=queued)
        assert versions.count() == int(decision.action == 'publish')
        if versions.exists():
            assert versions.get().snapshot == queued.frozen_snapshot
            assert versions.get().digest == queued.digest
        assert Event.objects.filter(target=str(queued.pk), kind__startswith='moderation_').count() == 1
        results.append(sorted(action for action, _ in outcomes))
    return {'pause_first': 'submission_rejected_draft_saved', 'submit_first': 'submission_retained_then_paused', 'competing_decisions': results}


def content_payload():
    return {key: value for key, value in content().items() if key not in ('rights_confirmed', 'privacy_confirmed')}
