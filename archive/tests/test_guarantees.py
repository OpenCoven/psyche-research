"""Product guarantee tests. Every manuscript/account here is a synthetic fixture."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sqlite3
import sys
import tempfile
import textwrap
from unittest.mock import patch
from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, OperationalError, connection, transaction
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from archive.forms import SubmissionForm, validate_artifacts
from archive.models import Appeal, Capacity, Decision, Event, RateBucket, Report, Submission, Version, Work
from archive import services


def content(**changes):
    data = {
        'title': 'SYNTHETIC EXAMPLE: a measured agent retry experiment',
        'byline': 'Synthetic Contributor',
        'kind': Submission.Kind.EXPERIMENT,
        'abstract': 'Synthetic test-only abstract; no research claim is made.',
        'methods': 'Synthetic procedure: inspect a fixed test fixture and record retries.',
        'claims': 'The synthetic fixture produced one expected retry.',
        'limitations': 'Synthetic fixture only; does not establish real agent reliability.',
        'artifacts': 'https://example.org/synthetic-fixture',
        'provenance': 'All data and names are synthetic test fixtures.',
        'license': 'CC-BY-4.0',
        'ai_disclosure': 'AI generated these synthetic test fixtures; no independent review.',
        'change_note': '',
        'rights_confirmed': True,
        'privacy_confirmed': True,
    }
    data.update(changes)
    return data


class Accounts:
    def accounts(self):
        users = get_user_model().objects
        self.author = users.create_user('synthetic-author', password='synthetic-password-12345')
        self.other = users.create_user('synthetic-other', password='synthetic-password-12345')
        self.moderator = users.create_user('synthetic-moderator', password='synthetic-password-12345')
        group, _ = Group.objects.get_or_create(name='moderators')
        self.moderator.groups.add(group)
        self.capacity, _ = Capacity.objects.get_or_create(pk=1)
        self.capacity.intake_open = True
        self.capacity.queue_limit = 5
        self.capacity.per_author_limit = 2
        self.capacity.draft_limit = 20
        self.capacity.save()

    def draft(self, author=None, work_id=None):
        return services.create_submission(author or self.author, work_id=work_id)

    def submitted(self, author=None, data=None, work_id=None):
        author = author or self.author
        submission = self.draft(author, work_id)
        services.save_submission(author, submission.pk, data or content(), submission.revision, submit=True)
        submission.refresh_from_db()
        return submission

    def published(self, author=None, data=None):
        submission = self.submitted(author, data)
        services.decide(self.moderator, submission.pk, 'publish', 'Synthetic moderation: completeness and rights only.', submission.revision, conflicts='None; synthetic fixture')
        submission.refresh_from_db()
        return submission, Version.objects.get(submission=submission)


@override_settings(PILOT_APPROVED=True)
class WorkflowGuarantees(Accounts, TestCase):
    def setUp(self):
        self.accounts()

    def test_moderator_requires_active_explicit_group_not_staff_or_superuser(self):
        self.assertFalse(services.is_moderator(AnonymousUser()))
        self.assertFalse(services.is_moderator(self.author))
        self.assertTrue(services.is_moderator(self.moderator))
        self.author.is_staff = True
        self.author.is_superuser = True
        self.author.save()
        self.assertFalse(services.is_moderator(self.author))
        self.moderator.is_active = False
        self.moderator.save()
        self.assertFalse(services.is_moderator(self.moderator))

    def test_inactive_and_anonymous_cannot_create_drafts(self):
        self.author.is_active = False
        self.author.save()
        for actor in (self.author, AnonymousUser()):
            with self.subTest(actor=str(actor)), self.assertRaises(services.WorkflowError):
                self.draft(actor)
        self.assertEqual(Submission.objects.count(), 0)

    def test_partial_draft_survives_resume_without_becoming_public(self):
        submission = self.draft()
        services.save_submission(self.author, submission.pk, content(title='SYNTHETIC private draft', abstract='', methods='', claims='', limitations='', artifacts='', provenance='', license='', ai_disclosure='', rights_confirmed=False, privacy_confirmed=False), 0)
        resumed = Submission.objects.get(pk=submission.pk)
        self.assertEqual(resumed.title, 'SYNTHETIC private draft')
        self.assertEqual(resumed.revision, 1)
        self.assertEqual(resumed.state, Submission.State.DRAFT)
        self.assertFalse(resumed.digest)
        self.assertFalse(Version.objects.exists())

    def test_stale_draft_save_does_not_overwrite_accepted_content(self):
        submission = self.draft()
        services.save_submission(self.author, submission.pk, content(title='SYNTHETIC accepted draft'), 0)
        with self.assertRaises(services.WorkflowError):
            services.save_submission(self.author, submission.pk, content(title='SYNTHETIC stale overwrite'), 0)
        submission.refresh_from_db()
        self.assertEqual(submission.title, 'SYNTHETIC accepted draft')
        self.assertEqual(submission.revision, 1)

    def test_unrelated_contributor_cannot_save_or_submit_draft(self):
        submission = self.draft()
        for submit in (False, True):
            with self.subTest(submit=submit), self.assertRaises(services.WorkflowError):
                services.save_submission(self.other, submission.pk, content(), 0, submit=submit)
        submission.refresh_from_db()
        self.assertEqual(submission.revision, 0)
        self.assertEqual(submission.title, '')

    def test_submit_requires_each_evidence_field_and_confirmations(self):
        required = ('title', 'byline', 'abstract', 'methods', 'claims', 'limitations', 'provenance', 'license', 'ai_disclosure', 'rights_confirmed', 'privacy_confirmed')
        for field in required:
            with self.subTest(field=field):
                submission = self.draft()
                invalid = content(**{field: False if field.endswith('_confirmed') else ''})
                with self.assertRaises(services.WorkflowError):
                    services.save_submission(self.author, submission.pk, invalid, 0, submit=True)
                submission.refresh_from_db()
                self.assertEqual(submission.state, Submission.State.DRAFT)
                self.assertEqual(submission.revision, 0)
                self.assertEqual(submission.title, '')
                submission.delete()

    def test_invalid_field_values_rejected_at_service_boundary(self):
        for invalid in (content(title='x' * 201), content(kind='forged-kind'), content(license='forged-license'), content(artifacts='javascript:alert(1)')):
            with self.subTest(invalid=invalid):
                submission = self.draft()
                with self.assertRaises(services.WorkflowError):
                    services.save_submission(self.author, submission.pk, invalid, 0, submit=True)
                submission.refresh_from_db()
                self.assertEqual(submission.revision, 0)
                submission.delete()

    def test_observation_with_no_artifact_url_still_requires_provenance(self):
        submission = self.submitted(data=content(artifacts='', provenance='Synthetic observation-only fixture; no downloadable artifacts exist.'))
        self.assertEqual(submission.state, Submission.State.SUBMITTED)

    def test_submitted_payload_is_frozen_and_content_digest_is_exact(self):
        submission = self.submitted()
        self.assertEqual(submission.frozen_snapshot, submission.payload())
        self.assertEqual(len(submission.digest), 64)
        canonical = json.dumps(submission.frozen_snapshot, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        self.assertEqual(submission.digest, hashlib.sha256(canonical).hexdigest())
        with self.assertRaises(services.WorkflowError):
            services.save_submission(self.author, submission.pk, content(title='SYNTHETIC mutated after submit'), submission.revision)
        submission.refresh_from_db()
        self.assertEqual(submission.title, content()['title'])

    def test_exact_submit_retry_creates_no_duplicate(self):
        submission = self.draft()
        services.save_submission(self.author, submission.pk, content(), 0, submit=True)
        services.save_submission(self.author, submission.pk, content(), 0, submit=True)
        submission.refresh_from_db()
        self.assertEqual(Submission.objects.filter(pk=submission.pk).count(), 1)
        self.assertEqual(submission.revision, 1)
        with self.assertRaises(services.WorkflowError):
            services.save_submission(self.author, submission.pk, content(title='SYNTHETIC different retry'), 0, submit=True)

    def test_closed_intake_preserves_draft_but_rejects_submit(self):
        self.capacity.intake_open = False
        self.capacity.save()
        submission = self.draft()
        services.save_submission(self.author, submission.pk, content(title='SYNTHETIC safely paused'), 0)
        with self.assertRaises(services.WorkflowError):
            services.save_submission(self.author, submission.pk, content(), 1, submit=True)
        submission.refresh_from_db()
        self.assertEqual(submission.title, 'SYNTHETIC safely paused')
        self.assertEqual(submission.state, Submission.State.DRAFT)

    def test_global_queue_limit_and_per_author_limit_are_enforced(self):
        self.capacity.queue_limit = 2
        self.capacity.per_author_limit = 2
        self.capacity.save()
        self.submitted()
        second = self.draft()
        with self.assertRaises(services.WorkflowError):
            services.save_submission(self.author, second.pk, content(), 0, submit=True)
        self.submitted(self.other)
        third = self.draft(self.moderator)
        with self.assertRaises(services.WorkflowError):
            services.save_submission(self.moderator, third.pk, content(), 0, submit=True)
        self.assertEqual(Submission.objects.filter(state=Submission.State.SUBMITTED).count(), 2)

    def test_per_author_active_draft_limit_is_enforced_at_creation(self):
        self.capacity.per_author_limit = 1
        self.capacity.save()
        self.draft()
        with self.assertRaises(services.WorkflowError):
            self.draft()
        self.assertEqual(Submission.objects.count(), 1)

    def test_draft_creation_is_bounded(self):
        self.capacity.draft_limit = 1
        self.capacity.save()
        self.draft()
        with self.assertRaises(services.WorkflowError):
            self.draft()
        self.assertEqual(Submission.objects.count(), 1)

    def test_non_moderator_cannot_decide_and_no_partial_publication(self):
        submission = self.submitted()
        for actor in (self.author, self.other, AnonymousUser()):
            with self.subTest(actor=str(actor)), self.assertRaises(services.WorkflowError):
                services.decide(actor, submission.pk, 'publish', 'Synthetic forbidden approval', submission.revision, conflicts='None; synthetic fixture')
        self.assertFalse(Decision.objects.exists())
        self.assertFalse(Version.objects.exists())

    def test_moderator_and_superuser_author_cannot_self_publish(self):
        self.moderator.is_staff = True
        self.moderator.is_superuser = True
        self.moderator.save()
        submission = self.submitted(self.moderator)
        with self.assertRaises(services.WorkflowError):
            services.decide(self.moderator, submission.pk, 'publish', 'Synthetic self approval', submission.revision, conflicts='None; synthetic fixture')
        self.assertFalse(Version.objects.exists())

    def test_stale_moderation_decision_fails_without_publishing(self):
        submission = self.submitted()
        with self.assertRaises(services.WorkflowError):
            services.decide(self.moderator, submission.pk, 'publish', 'Synthetic stale decision', submission.revision - 1, conflicts='None; synthetic fixture')
        self.assertFalse(Version.objects.exists())
        self.assertFalse(Decision.objects.exists())

    def test_moderation_requires_explicit_conflict_declaration(self):
        submission = self.submitted()
        for conflicts in (None, '', '   '):
            with self.subTest(conflicts=conflicts), self.assertRaises(services.WorkflowError):
                services.decide(self.moderator, submission.pk, 'publish', 'Synthetic moderation reason.', submission.revision, conflicts=conflicts)
        self.assertFalse(Version.objects.exists())
        self.assertFalse(Decision.objects.exists())

    def test_duplicate_decision_cannot_change_conflict_disclosure(self):
        submission = self.submitted()
        expected = submission.revision
        services.decide(self.moderator, submission.pk, 'publish', 'Synthetic reason.', expected, conflicts='None; synthetic fixture')
        with self.assertRaises(services.WorkflowError):
            services.decide(self.moderator, submission.pk, 'publish', 'Synthetic reason.', expected, conflicts='Synthetic newly disclosed collaboration')
        self.assertEqual(Decision.objects.get().conflicts, 'None; synthetic fixture')

    def test_request_changes_and_resubmit_requires_new_exact_decision(self):
        submission = self.submitted()
        services.decide(self.moderator, submission.pk, 'changes', 'Synthetic request: clarify methods.', submission.revision, conflicts='None; synthetic fixture')
        submission.refresh_from_db()
        self.assertEqual(submission.state, Submission.State.CHANGES)
        old_digest = submission.digest
        services.save_submission(self.author, submission.pk, content(methods='Synthetic revised methods with extra detail.'), submission.revision, submit=True)
        submission.refresh_from_db()
        self.assertNotEqual(submission.digest, old_digest)
        self.assertFalse(Version.objects.exists())
        services.decide(self.moderator, submission.pk, 'publish', 'Synthetic accepted revised scope.', submission.revision, conflicts='None; synthetic fixture')
        self.assertEqual(Decision.objects.count(), 2)
        self.assertEqual(Version.objects.get().digest, submission.digest)

    def test_published_version_is_exact_snapshot_and_private_decision_excluded(self):
        submission, version = self.published()
        self.assertEqual(version.snapshot, submission.frozen_snapshot)
        self.assertEqual(version.digest, submission.digest)
        self.assertEqual(version.number, 1)
        self.assertEqual(Decision.objects.get().actor, self.moderator)
        self.assertNotIn('reason', version.snapshot)
        self.assertNotIn('author_id', version.snapshot)

    def test_duplicate_publication_does_not_create_second_version(self):
        submission = self.submitted()
        expected = submission.revision
        reason = 'Synthetic moderation completed.'
        services.decide(self.moderator, submission.pk, 'publish', reason, expected, conflicts='None; synthetic fixture')
        services.decide(self.moderator, submission.pk, 'publish', reason, expected, conflicts='None; synthetic fixture')
        self.assertEqual(Version.objects.count(), 1)
        self.assertEqual(Decision.objects.count(), 1)

    def test_publication_transaction_rolls_back_on_storage_error(self):
        submission = self.submitted()
        with patch.object(Version.objects, 'create', side_effect=DatabaseError('synthetic failure')):
            with self.assertRaises(DatabaseError):
                services.decide(self.moderator, submission.pk, 'publish', 'Synthetic atomicity check.', submission.revision, conflicts='None; synthetic fixture')
        submission.refresh_from_db()
        self.assertEqual(submission.state, Submission.State.SUBMITTED)
        self.assertFalse(Version.objects.exists())
        self.assertFalse(Decision.objects.exists())
        self.assertFalse(Work.objects.exists())

    def test_published_versions_decisions_events_are_append_only_in_database(self):
        _, version = self.published()
        with self.assertRaises(ValidationError):
            version.snapshot = {'title': 'SYNTHETIC forbidden mutation'}
            version.save()
        for record in (version, Decision.objects.get(), Event.objects.first()):
            self.assertIsNotNone(record)
            queryset = record.__class__.objects.filter(pk=record.pk)
            with self.subTest(model=record.__class__.__name__), self.assertRaises(DatabaseError), transaction.atomic():
                queryset.delete()
        with self.assertRaises(DatabaseError), transaction.atomic():
            Version.objects.filter(pk=version.pk).update(snapshot={'title': 'SYNTHETIC bypass mutation'})

    def test_all_append_only_triggers_survive_latest_schema_migrations(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
            installed = {row[0] for row in cursor.fetchall()}
        expected = {f'archive_{table}_no_{action}' for table in ('version', 'decision', 'event') for action in ('update', 'delete')}
        self.assertTrue(expected.issubset(installed), f'Missing integrity triggers: {expected - installed}')

    def test_revision_requires_ownership_reason_and_separate_moderation(self):
        _, first = self.published()
        with self.assertRaises(services.WorkflowError):
            self.draft(self.other, first.work_id)
        correction = self.draft(work_id=first.work_id)
        with self.assertRaises(services.WorkflowError):
            services.save_submission(self.author, correction.pk, content(title='SYNTHETIC correction'), correction.revision, submit=True)
        correction.refresh_from_db()
        services.save_submission(self.author, correction.pk, content(title='SYNTHETIC correction', change_note='Synthetic correction: repaired fixture count.'), correction.revision, submit=True)
        self.assertEqual(Version.objects.count(), 1)
        correction.refresh_from_db()
        services.decide(self.moderator, correction.pk, 'publish', 'Synthetic correction moderated.', correction.revision, conflicts='None; synthetic fixture')
        first.refresh_from_db()
        self.assertEqual(first.snapshot['title'], content()['title'])
        self.assertEqual(list(Version.objects.filter(work=first.work).order_by('number').values_list('number', flat=True)), [1, 2])

    def test_only_one_active_revision_per_work(self):
        _, version = self.published()
        self.draft(work_id=version.work_id)
        with self.assertRaises(services.WorkflowError):
            self.draft(work_id=version.work_id)

    def test_withdrawal_scopes_whole_work_and_blocks_new_revisions(self):
        _, version = self.published()
        with self.assertRaises(services.WorkflowError):
            services.withdraw(self.other, version.work_id, 'Synthetic unrelated withdrawal')
        services.withdraw(self.author, version.work_id, 'Synthetic safety withdrawal: fixture removed.')
        version.work.refresh_from_db()
        self.assertIsNotNone(version.work.withdrawn_at)
        self.assertEqual(Version.objects.count(), 1)
        with self.assertRaises(services.WorkflowError):
            self.draft(work_id=version.work_id)

    def test_appeal_is_owner_only_bounded_and_cannot_publish(self):
        submission = self.submitted()
        services.decide(self.moderator, submission.pk, 'decline', 'Synthetic out of scope decision.', submission.revision, conflicts='None; synthetic fixture')
        with self.assertRaises(services.WorkflowError):
            services.appeal(self.other, submission.pk, 'Synthetic unauthorized appeal.')
        services.appeal(self.author, submission.pk, 'Synthetic appeal: please reconsider scope.')
        with self.assertRaises(services.WorkflowError):
            services.appeal(self.author, submission.pk, 'Synthetic duplicate appeal.')
        appeal = Appeal.objects.get()
        with self.assertRaises(services.WorkflowError):
            services.resolve_appeal(self.author, appeal.pk, 'Synthetic author resolution.')
        services.resolve_appeal(self.moderator, appeal.pk, 'Synthetic response: reopen for revised scope.', reopen=True)
        submission.refresh_from_db()
        appeal.refresh_from_db()
        self.assertIsNotNone(appeal.resolved_at)
        self.assertEqual(appeal.resolved_by, self.moderator)
        self.assertNotEqual(submission.state, Submission.State.PUBLISHED)
        self.assertFalse(Version.objects.exists())

    def test_reopening_declined_appeal_cannot_exceed_active_capacity(self):
        submission = self.submitted()
        services.decide(self.moderator, submission.pk, 'decline', 'Synthetic declined scope.', submission.revision, conflicts='None; synthetic fixture')
        appeal = services.appeal(self.author, submission.pk, 'Synthetic reconsideration request.')
        self.draft()
        self.draft()
        with self.assertRaises(services.WorkflowError):
            services.resolve_appeal(self.moderator, appeal.pk, 'Synthetic reopening while full.', reopen=True)
        submission.refresh_from_db()
        appeal.refresh_from_db()
        self.assertEqual(submission.state, Submission.State.DECLINED)
        self.assertIsNone(appeal.resolved_at)
        self.assertEqual(Submission.objects.filter(author=self.author, state__in=['draft', 'changes', 'submitted']).count(), 2)

    def test_old_appeal_cannot_reopen_a_later_moderation_decision(self):
        submission = self.submitted()
        services.decide(self.moderator, submission.pk, 'changes', 'Synthetic first decision.', submission.revision, conflicts='None; synthetic fixture')
        old_appeal = services.appeal(self.author, submission.pk, 'Synthetic appeal of first decision.')
        submission.refresh_from_db()
        services.save_submission(self.author, submission.pk, content(methods='Synthetic new evidence in revised methods.'), submission.revision, submit=True)
        submission.refresh_from_db()
        services.decide(self.moderator, submission.pk, 'decline', 'Synthetic later decision.', submission.revision, conflicts='None; synthetic fixture')
        with self.assertRaises(services.WorkflowError):
            services.resolve_appeal(self.moderator, old_appeal.pk, 'Synthetic obsolete appeal reopening.', reopen=True)
        submission.refresh_from_db()
        self.assertEqual(submission.state, Submission.State.DECLINED)

    def test_capacity_configuration_requires_moderator_and_revision(self):
        values = {'intake_open': False, 'queue_limit': 3, 'per_author_limit': 1, 'draft_limit': 10}
        with self.assertRaises(services.WorkflowError):
            services.configure(self.author, values, self.capacity.revision, 'Synthetic capacity change.')
        services.configure(self.moderator, values, self.capacity.revision, 'Synthetic schedule pause.')
        with self.assertRaises(services.WorkflowError):
            services.configure(self.moderator, values, self.capacity.revision, 'Synthetic stale change.')
        self.capacity.refresh_from_db()
        self.assertFalse(self.capacity.intake_open)
        self.assertEqual(self.capacity.queue_limit, 3)

    def test_abuse_reports_are_bounded_per_work_and_resolution_is_moderator_only(self):
        _, version = self.published()
        for number in range(10):
            services.report(version.work_id, f'Synthetic private report {number}')
        with self.assertRaises(services.WorkflowError):
            services.report(version.work_id, 'Synthetic overflow report')
        report = Report.objects.first()
        with self.assertRaises(services.WorkflowError):
            services.resolve_report(self.author, report.pk, 'Synthetic unauthorized resolution')
        services.resolve_report(self.moderator, report.pk, 'Synthetic bounded triage response')
        report.refresh_from_db()
        self.assertIsNotNone(report.resolved_at)
        self.assertEqual(report.resolved_by, self.moderator)
        self.assertEqual(Report.objects.count(), 10)

    @override_settings(PILOT_APPROVED=False, LOCAL_DEVELOPMENT=False)
    def test_unapproved_pilot_cannot_open_production_intake(self):
        values = {'intake_open': True, 'queue_limit': 3, 'per_author_limit': 1, 'draft_limit': 10}
        with self.assertRaises(services.WorkflowError):
            services.configure(self.moderator, values, self.capacity.revision, 'Synthetic forbidden opening.')


class InputGuarantees(TestCase):
    def test_artifact_validation_rejects_credentials_local_targets_and_active_schemes(self):
        invalid = [
            'javascript:alert(1)', 'data:text/html,hello', 'http://example.org/path',
            'https://user:secret@example.org/file', 'https://example.org/file?token=secret',
            'https://localhost/file', 'https://host.local/file', 'https://host.internal/file',
            'https://127.0.0.1/file', 'https://169.254.169.254/latest/meta-data',
            'https://10.0.0.1/file', 'https://[::1]/file', 'https://example.org:8443/file',
            'https://example.org/a b', 'https://example.org/' + 'x' * 2001,
            '\n'.join(f'https://example.org/{n}' for n in range(9)),
        ]
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(ValidationError):
                validate_artifacts(text)

    def test_artifact_validation_is_bounded_and_does_not_fetch_links(self):
        with patch('socket.getaddrinfo', side_effect=AssertionError('URL validation must not perform DNS')):
            self.assertEqual(validate_artifacts(' https://example.org/fixture \n\nhttps://example.net/repository'), 'https://example.org/fixture\nhttps://example.net/repository')

    def test_form_never_accepts_identity_state_or_reputation_fields(self):
        forbidden = {'author', 'owner', 'state', 'digest', 'frozen_snapshot', 'published_at', 'score', 'followers', 'stars', 'reputation', 'role'}
        self.assertFalse(forbidden.intersection(SubmissionForm().fields))


@override_settings(PILOT_APPROVED=True)
class HTTPBoundaryGuarantees(Accounts, TestCase):
    def setUp(self):
        self.accounts()

    def test_anonymous_public_routes_never_reveal_private_sentinels(self):
        secret = 'SYNTHETIC-PRIVATE-MANUSCRIPT-73ad2'
        submission = self.submitted(data=content(title=secret, abstract=secret, artifacts='https://example.org/' + secret))
        for name, args, query in (
            ('home', [], {}), ('archive', [], {}), ('archive', [], {'q': secret}),
            ('policies', [], {}), ('edit', [submission.pk], {}),
            ('export_submission', [submission.pk], {}), ('queue', [], {}), ('operations', [], {}),
        ):
            with self.subTest(route=name, query=query):
                response = self.client.get(reverse(name, args=args), query)
                if query:
                    # A search form reflects its caller's query; only database-derived results are private.
                    self.assertEqual(list(response.context['versions']), [])
                    self.assertContains(response, 'No published records match')
                else:
                    self.assertNotContains(response, secret, status_code=response.status_code)
        self.assertFalse(Version.objects.exists())

    def test_unrelated_user_cannot_view_edit_export_or_appeal_private_submission(self):
        secret = 'SYNTHETIC-OTHER-AUTHOR-PRIVATE-f7012'
        submission = self.submitted(data=content(title=secret))
        self.client.force_login(self.other)
        for name in ('edit', 'export_submission'):
            with self.subTest(name=name):
                response = self.client.get(reverse(name, args=[submission.pk]))
                self.assertIn(response.status_code, (403, 404))
                self.assertNotContains(response, secret, status_code=response.status_code)
        response = self.client.post(reverse('appeal', args=[submission.pk]), urlencode({'reason': 'Synthetic unrelated appeal'}), content_type='application/x-www-form-urlencoded')
        self.assertIn(response.status_code, (403, 404))
        self.assertFalse(Appeal.objects.exists())

    def test_contributor_cannot_access_private_moderation_or_operations(self):
        self.client.force_login(self.author)
        for name in ('queue', 'operations'):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertIn(response.status_code, (403, 404))

    def test_private_pending_appeals_are_discoverable_to_moderator(self):
        submission = self.submitted()
        services.decide(self.moderator, submission.pk, 'decline', 'Synthetic declined scope.', submission.revision, conflicts='None; synthetic fixture')
        reason = 'SYNTHETIC-PENDING-APPEAL-PRIVATE-a102f'
        services.appeal(self.author, submission.pk, reason)
        self.client.force_login(self.moderator)
        response = self.client.get(reverse('operations'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('moderate', args=[submission.pk]))
        self.assertContains(response, reason)

    def test_private_responses_disable_shared_caching(self):
        submission = self.draft()
        self.client.force_login(self.author)
        for name, args in (('dashboard', []), ('edit', [submission.pk]), ('export_submission', [submission.pk])):
            with self.subTest(route=name):
                response = self.client.get(reverse(name, args=args))
                self.assertEqual(response.status_code, 200)
                self.assertIn('no-store', response.headers.get('Cache-Control', ''))

    def test_csrf_required_for_state_changing_requests_and_logout_is_post_only(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.author)
        response = client.post(reverse('new_submission'), 'csrf_probe=1', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Submission.objects.count(), 0)
        self.assertEqual(client.get(reverse('logout')).status_code, 405)

    def test_browser_login_keeps_csrf_origin_checks_and_query_private_referrer_policy(self):
        browser = Client(enforce_csrf_checks=True)
        page = browser.get(reverse('login'), secure=True)
        self.assertEqual(page['Referrer-Policy'], 'strict-origin')
        data = urlencode({'username': self.author.username, 'password': 'synthetic-password-12345',
                          'csrfmiddlewaretoken': browser.cookies['csrftoken'].value})
        for origin in ['null', 'https://attacker.invalid']:
            response = browser.post(reverse('login'), data, secure=True,
                content_type='application/x-www-form-urlencoded', HTTP_ORIGIN=origin)
            self.assertEqual(response.status_code, 403)
        response = browser.post(reverse('login'), data, secure=True,
            content_type='application/x-www-form-urlencoded', HTTP_ORIGIN='https://testserver')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(browser.get(reverse('dashboard'), secure=True).status_code, 200)

    def test_database_contention_returns_controlled_retry_without_partial_draft(self):
        self.client.force_login(self.author)
        self.client.raise_request_exception = False
        with patch('archive.views.services.create_submission', side_effect=OperationalError('synthetic database lock')):
            response = self.client.post(reverse('new_submission'), 'action=new', content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 503)
        self.assertIn('Retry-After', response.headers)
        self.assertEqual(Submission.objects.count(), 0)

    def test_uploads_are_rejected_before_draft_can_change(self):
        submission = self.draft()
        self.client.force_login(self.author)
        data = content(title='SYNTHETIC forbidden multipart mutation')
        data.update({'revision': 0, 'action': 'save', 'file': SimpleUploadedFile('attack.html', b'<script>alert(1)</script>', content_type='text/html')})
        response = self.client.post(reverse('edit', args=[submission.pk]), data)
        self.assertIn(response.status_code, (400, 413, 415))
        submission.refresh_from_db()
        self.assertEqual(submission.revision, 0)

    def test_oversized_body_rejected_before_draft_can_change(self):
        submission = self.draft()
        self.client.force_login(self.author)
        response = self.client.post(reverse('edit', args=[submission.pk]), 'methods=' + 'x' * (97 * 1024), content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 413)
        submission.refresh_from_db()
        self.assertEqual(submission.revision, 0)

    def test_public_snapshot_escapes_untrusted_text_and_excludes_private_decisions(self):
        script = '<script>window.synthetic_attack = true</script>'
        submission = self.submitted(data=content(title=script))
        private_reason = 'SYNTHETIC-PRIVATE-MODERATION-NOTE-6209'
        services.decide(self.moderator, submission.pk, 'publish', private_reason, submission.revision, conflicts='None; synthetic fixture')
        version = Version.objects.get(submission=submission)
        response = self.client.get(reverse('version', args=[version.work_id, version.number]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, script)
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, private_reason)
        self.assertContains(response, 'not available')
        export = self.client.get(reverse('export_version', args=[version.work_id, version.number]))
        self.assertEqual(export.status_code, 200)
        self.assertNotContains(export, private_reason)

    def test_pending_correction_stays_private_and_v1_remains_exact(self):
        _, version = self.published()
        correction = self.draft(work_id=version.work_id)
        secret = 'SYNTHETIC-UNPUBLISHED-CORRECTION-5f7dc'
        services.save_submission(self.author, correction.pk, content(title=secret, change_note='Synthetic pending correction.'), correction.revision, submit=True)
        search = self.client.get(reverse('archive'), {'q': secret})
        self.assertEqual(list(search.context['versions']), [])
        self.assertContains(search, 'No published records match')
        for response in (
            self.client.get(reverse('work', args=[version.work_id]), follow=True),
            self.client.get(reverse('version', args=[version.work_id, 1])),
            self.client.get(reverse('export_version', args=[version.work_id, 1])),
        ):
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, secret)
        self.assertEqual(self.client.get(reverse('version', args=[version.work_id, 2])).status_code, 404)

    def test_older_version_notice_tracks_only_published_corrections_and_respects_withdrawal(self):
        _, first = self.published()
        exact_export = self.client.get(reverse('export_version', args=[first.work_id, 1])).json()
        notice = 'A newer version is available.'
        for number in (2, 3):
            correction = self.draft(work_id=first.work_id)
            services.save_submission(self.author, correction.pk,
                content(title=f'SYNTHETIC correction {number}', change_note=f'Synthetic correction {number}.'),
                correction.revision, submit=True)
            if number == 2:
                self.assertNotContains(self.client.get(reverse('version', args=[first.work_id, 1])), notice)
            correction.refresh_from_db()
            services.decide(self.moderator, correction.pk, 'publish', 'Synthetic correction moderation.',
                correction.revision, conflicts='None; synthetic fixture')
            for older_number in range(1, number):
                older = self.client.get(reverse('version', args=[first.work_id, older_number]))
                self.assertContains(older, notice)
                latest_url = reverse('version', args=[first.work_id, number])
                self.assertContains(older, f'<a href="{latest_url}">Read version {number}</a>', html=True)
            self.assertNotContains(self.client.get(reverse('version', args=[first.work_id, number])), notice)
            self.assertEqual(self.client.get(reverse('export_version', args=[first.work_id, 1])).json(), exact_export)
        services.withdraw(self.author, first.work_id, 'Synthetic all-version withdrawal.')
        for number in (1, 2, 3):
            tombstone = self.client.get(reverse('version', args=[first.work_id, number]))
            self.assertContains(tombstone, 'This research has been withdrawn.')
            self.assertNotContains(tombstone, notice)
            self.assertNotContains(tombstone, 'SYNTHETIC correction')

    def test_withdrawn_body_absent_from_latest_versions_search_and_export(self):
        sentinel = 'SYNTHETIC-WITHDRAWN-PRIVATE-BODY-1efc0'
        _, first = self.published(data=content(abstract=sentinel, claims=sentinel))
        correction = self.draft(work_id=first.work_id)
        services.save_submission(self.author, correction.pk, content(abstract=sentinel, change_note='Synthetic second version.'), correction.revision, submit=True)
        correction.refresh_from_db()
        services.decide(self.moderator, correction.pk, 'publish', 'Synthetic second moderation.', correction.revision, conflicts='None; synthetic fixture')
        services.withdraw(self.author, first.work_id, 'Synthetic withdrawal record.')
        search = self.client.get(reverse('archive'), {'q': sentinel})
        self.assertEqual(list(search.context['versions']), [])
        self.assertContains(search, 'No published records match')
        paths = [reverse('work', args=[first.work_id])]
        paths.extend(reverse(name, args=[first.work_id, number]) for name in ('version', 'export_version') for number in (1, 2))
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path, follow=True)
                self.assertIn(response.status_code, (200, 404, 410))
                self.assertNotContains(response, sentinel, status_code=response.status_code)
        self.assertContains(self.client.get(reverse('version', args=[first.work_id, 1])), 'withdrawn')

    def test_reputation_inputs_do_not_change_public_order_or_admission(self):
        first, _ = self.published(data=content(title='SYNTHETIC first chronologically'))
        self.published(self.other, content(title='SYNTHETIC second chronologically'))
        baseline = self.client.get(reverse('archive')).content
        changed = self.client.get(reverse('archive'), {'score': 999999, 'stars': 999999, 'followers': 999999, 'reputation': str(first.author_id)}).content
        self.assertEqual(baseline, changed)
        self.assertFalse({'reputation', 'score', 'followers', 'stars'}.intersection(field.name for field in get_user_model()._meta.fields))

    def test_health_is_minimal_and_has_no_manuscript_or_contact_data(self):
        self.submitted(data=content(title='SYNTHETIC-HEALTH-PRIVATE-TITLE-78eab'))
        response = self.client.get(reverse('health'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'SYNTHETIC-HEALTH-PRIVATE-TITLE-78eab')
        self.assertNotContains(response, self.author.username)
        self.assertLess(len(response.content), 512)

    def test_login_throttle_persists_across_clients_and_source_ip_changes(self):
        body = urlencode({'username': self.author.username, 'password': 'synthetic-incorrect-password'})
        with patch('archive.middleware.time.time', return_value=1700000000):
            for number in range(10):
                response = Client().post(reverse('login'), body, content_type='application/x-www-form-urlencoded', REMOTE_ADDR=f'192.0.2.{number + 1}')
                self.assertEqual(response.status_code, 200)
            response = Client().post(reverse('login'), body, content_type='application/x-www-form-urlencoded', REMOTE_ADDR='198.51.100.90')
        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response.headers)
        self.assertTrue(RateBucket.objects.exists())
        for key in RateBucket.objects.values_list('key', flat=True):
            self.assertEqual(len(key), 64)
            self.assertNotIn(self.author.username, key)
            self.assertNotIn('192.0.2', key)


class ConcurrentCapacityGuarantee(SimpleTestCase):
    """Use the supported file database, retaining every production integrity trigger."""

    def test_real_file_database_serializes_final_queue_slot_and_duplicate_publication(self):
        script = textwrap.dedent('''
            import django
            django.setup()
            import json
            from concurrent.futures import ThreadPoolExecutor
            from threading import Barrier
            from django.core.management import call_command
            from django.contrib.auth import get_user_model
            from django.contrib.auth.models import Group
            from django.db import close_old_connections
            from archive import services
            from archive.models import Capacity, Submission, Decision, Version
            from archive.tests.test_guarantees import content
            call_command('migrate', verbosity=0)
            users = get_user_model().objects
            first_author = users.create_user('synthetic-file-author-one')
            second_author = users.create_user('synthetic-file-author-two')
            moderator = users.create_user('synthetic-file-moderator')
            moderator.groups.add(Group.objects.get(name='moderators'))
            cap = Capacity.objects.get(pk=1)
            cap.intake_open = True
            cap.queue_limit = 1
            cap.save()
            first = services.create_submission(first_author)
            second = services.create_submission(second_author)
            barrier = Barrier(2)
            def submit(author_id, submission_id):
                close_old_connections()
                try:
                    actor = users.get(pk=author_id)
                    barrier.wait(timeout=10)
                    services.save_submission(actor, submission_id, content(), 0, submit=True)
                    return 'submitted'
                except services.WorkflowError:
                    return 'bounded'
                finally:
                    close_old_connections()
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(submit, first_author.pk, first.pk), pool.submit(submit, second_author.pk, second.pk)]
                results = [future.result(timeout=30) for future in futures]
            queued = Submission.objects.get(state='submitted')
            queue_count = Submission.objects.filter(state='submitted').count()
            barrier = Barrier(2)
            def decide():
                close_old_connections()
                try:
                    actor = users.get(pk=moderator.pk)
                    barrier.wait(timeout=10)
                    services.decide(actor, queued.pk, 'publish', 'Synthetic concurrent exact decision.', queued.revision, conflicts='None; synthetic fixture')
                    return 'decided'
                finally:
                    close_old_connections()
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(decide), pool.submit(decide)]
                decisions = [future.result(timeout=30) for future in futures]
            print(json.dumps({'submissions': sorted(results), 'queue_count': queue_count,
                'decisions': decisions, 'version_count': Version.objects.count(), 'decision_count': Decision.objects.count()}))
        ''')
        with tempfile.TemporaryDirectory(prefix='coven-research-concurrency-') as directory:
            environment = {**os.environ, 'LOCAL_DEVELOPMENT': '1', 'PILOT_APPROVED': '1',
                           'DATABASE_PATH': str(Path(directory) / 'isolated.sqlite3'),
                           'DJANGO_SETTINGS_MODULE': 'config.settings'}
            result = subprocess.run([sys.executable, '-c', script], cwd=Path(__file__).resolve().parents[2], env=environment, text=True, capture_output=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr)
        evidence = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(evidence['submissions'], ['bounded', 'submitted'])
        self.assertEqual(evidence['queue_count'], 1)
        self.assertEqual(evidence['decisions'], ['decided', 'decided'])
        self.assertEqual(evidence['version_count'], 1)
        self.assertEqual(evidence['decision_count'], 1)


class RecoveryPathGuarantees(SimpleTestCase):
    def test_dangling_destination_symlink_is_rejected_without_following_or_removing_it(self):
        from archive.recovery import copy_database
        with tempfile.TemporaryDirectory(prefix='coven-research-paths-') as directory:
            source = Path(directory) / 'source.sqlite3'
            with sqlite3.connect(source) as database:
                database.execute('CREATE TABLE synthetic_example (id INTEGER)')
                database.execute('INSERT INTO synthetic_example VALUES (1)')
            target = Path(directory) / 'unexpected-target.sqlite3'
            destination = Path(directory) / 'candidate.sqlite3'
            destination.symlink_to(target)
            # Isolate the filesystem contract; complete archive-schema verification is a separate gate.
            with patch('archive.recovery.verify'):
                with self.assertRaises((FileExistsError, ValueError)):
                    copy_database(source, destination)
            self.assertTrue(destination.is_symlink())
            self.assertFalse(target.exists())

    def test_existing_destination_is_never_overwritten_or_removed(self):
        from archive.recovery import copy_database
        with tempfile.TemporaryDirectory(prefix='coven-research-paths-') as directory:
            source = Path(directory) / 'source.sqlite3'
            with sqlite3.connect(source) as database:
                database.execute('CREATE TABLE synthetic_example (id INTEGER)')
                database.execute('INSERT INTO synthetic_example VALUES (1)')
            destination = Path(directory) / 'existing.sqlite3'
            destination.write_bytes(b'SYNTHETIC existing destination must survive')
            with patch('archive.recovery.verify'), self.assertRaises((FileExistsError, ValueError)):
                copy_database(source, destination)
            self.assertEqual(destination.read_bytes(), b'SYNTHETIC existing destination must survive')

    def test_corrupt_source_rejected_and_only_failed_new_candidate_removed(self):
        from archive.recovery import copy_database
        with tempfile.TemporaryDirectory(prefix='coven-research-paths-') as directory:
            source = Path(directory) / 'corrupt.sqlite3'
            source.write_bytes(b'SYNTHETIC corrupt source')
            destination = Path(directory) / 'candidate.sqlite3'
            with self.assertRaises((ValueError, sqlite3.DatabaseError)):
                copy_database(source, destination, restore=True)
            self.assertFalse(destination.exists())
            self.assertEqual(source.read_bytes(), b'SYNTHETIC corrupt source')
