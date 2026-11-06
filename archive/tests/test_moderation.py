"""Issue #5 acceptance audit. All manuscripts and identities are synthetic."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urlencode

from django.contrib.auth.models import Group
from django.db import transaction
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from archive import services
from archive.models import Appeal, Decision, Event, Submission, Version
from archive.tests.test_guarantees import Accounts


@override_settings(PILOT_APPROVED=True)
class ModerationAcceptance(Accounts, TestCase):
    def setUp(self):
        self.accounts()

    def at_state(self, state):
        if state == 'draft':
            return self.draft()
        row = self.submitted()
        if state != 'submitted':
            action = {'changes': 'changes', 'declined': 'decline', 'published': 'publish'}[state]
            services.decide(self.moderator, row.pk, action, 'Synthetic setup decision.', row.revision, conflicts='None; synthetic fixture')
            row.refresh_from_db()
        return row

    def test_all_submission_states_and_moderation_actions(self):
        for state in Submission.State.values:
            for action in ('publish', 'changes', 'decline'):
                with self.subTest(state=state, action=action), transaction.atomic():
                    row = self.at_state(state)
                    before = (row.revision, row.digest, row.frozen_snapshot)
                    counts = (Decision.objects.count(), Version.objects.count(), Event.objects.count())
                    if state == 'submitted':
                        decision = services.decide(self.moderator, row.pk, action, 'Synthetic matrix reason.', row.revision, conflicts='None; synthetic fixture')
                        row.refresh_from_db()
                        self.assertEqual(row.state, {'publish': 'published', 'changes': 'changes', 'decline': 'declined'}[action])
                        self.assertEqual(row.revision, before[0] + 1)
                        self.assertEqual((decision.revision, decision.digest), before[:2])
                        self.assertEqual(decision.actor, self.moderator)
                        self.assertEqual(decision.reason, 'Synthetic matrix reason.')
                        self.assertIsNotNone(decision.created_at)
                        self.assertEqual(Decision.objects.count(), counts[0] + 1)
                        self.assertEqual(Version.objects.count(), counts[1] + int(action == 'publish'))
                        audit = Event.objects.get(kind='moderation_' + action, target=str(row.pk))
                        self.assertEqual(audit.actor, self.moderator)
                        self.assertEqual(audit.details, {'revision': before[0], 'digest': before[1]})
                    else:
                        with self.assertRaises(services.WorkflowError) as rejected:
                            services.decide(self.moderator, row.pk, action, 'Synthetic forbidden matrix reason.', row.revision, conflicts='None; synthetic fixture')
                        self.assertEqual(rejected.exception.status, 409)
                        row.refresh_from_db()
                        self.assertEqual(row.state, state)
                        self.assertEqual((row.revision, row.digest, row.frozen_snapshot), before)
                        self.assertEqual((Decision.objects.count(), Version.objects.count(), Event.objects.count()), counts)
                    transaction.set_rollback(True)

    def test_direct_moderation_posts_cannot_bypass_role_or_self_decision(self):
        row = self.submitted()
        self.other.is_staff = self.other.is_superuser = True
        self.other.save()
        self.author.groups.add(Group.objects.get(name='moderators'))
        self.author.is_staff = self.author.is_superuser = True
        self.author.save()
        self.moderator.is_active = False
        self.moderator.save()
        for actor in (None, self.other, self.author, self.moderator):
            client = Client()
            if actor:
                client.force_login(actor)
            for action in ('publish', 'changes', 'decline'):
                with self.subTest(actor=actor, action=action):
                    response = client.post(reverse('moderate', args=[row.pk]), urlencode({
                        'action': action, 'reason': 'Synthetic forbidden direct post.',
                        'conflicts': 'None; synthetic fixture', 'revision': row.revision,
                    }), content_type='application/x-www-form-urlencoded')
                    self.assertIn(response.status_code, (302, 403))
                    if response.status_code == 302:
                        self.assertIn('/accounts/login/', response['Location'])
        row.refresh_from_db()
        self.assertEqual(row.state, 'submitted')
        self.assertFalse(Decision.objects.exists())
        self.assertFalse(Version.objects.exists())
        self.assertFalse(Event.objects.filter(kind__startswith='moderation_').exists())

    def test_tampered_current_content_frozen_snapshot_or_digest_cannot_be_decided(self):
        for corruption in ('title', 'frozen_snapshot', 'digest'):
            for action in ('publish', 'changes', 'decline'):
                with self.subTest(corruption=corruption, action=action), transaction.atomic():
                    row = self.submitted()
                    value = {'title': 'SYNTHETIC tampered value', 'frozen_snapshot': {**row.frozen_snapshot, 'claims': 'SYNTHETIC tampered claim'}, 'digest': '0' * 64}[corruption]
                    Submission.objects.filter(pk=row.pk).update(**{corruption: value})
                    with self.assertRaises(services.WorkflowError) as rejected:
                        services.decide(self.moderator, row.pk, action, 'Synthetic corrupted-content decision.', row.revision, conflicts='None; synthetic fixture')
                    self.assertEqual(rejected.exception.status, 409)
                    self.assertIn('integrity', str(rejected.exception))
                    self.assertFalse(Decision.objects.exists())
                    self.assertFalse(Version.objects.exists())
                    row.refresh_from_db()
                    self.assertEqual(row.state, 'submitted')
                    transaction.set_rollback(True)

    def test_private_history_records_appeal_response_and_moderation_boundary(self):
        row = self.submitted()
        services.decide(self.moderator, row.pk, 'decline', 'SYNTHETIC private scope reason.', row.revision, conflicts='None; synthetic fixture')
        decision = Decision.objects.get(submission=row)
        appeal = services.appeal(self.author, row.pk, 'SYNTHETIC private appeal reason.')
        self.author.groups.add(Group.objects.get(name='moderators'))
        with self.assertRaises(services.WorkflowError) as rejected:
            services.resolve_appeal(self.author, appeal.pk, 'Synthetic self-resolved appeal.', reopen=True)
        self.assertEqual(rejected.exception.status, 403)
        services.resolve_appeal(self.moderator, appeal.pk, 'SYNTHETIC private recorded response.')
        appeal.refresh_from_db()
        self.assertEqual((appeal.author, appeal.decision), (self.author, decision))
        self.assertEqual(appeal.resolved_by, self.moderator)
        self.assertIsNotNone(appeal.created_at)
        self.assertIsNotNone(appeal.resolved_at)
        self.assertEqual(appeal.response, 'SYNTHETIC private recorded response.')
        self.client.force_login(self.author)
        response = self.client.get(reverse('edit', args=[row.pk]))
        for text in (decision.reason, appeal.reason, appeal.response):
            self.assertContains(response, text)
        self.assertIn('no-store', response['Cache-Control'])
        for route, args, boundary in (
            ('queue', [], 'A publication decision is not scientific validation or independent peer review.'),
            ('moderate', [row.pk], 'This is a moderation action and must not be described as scientific peer review.'),
        ):
            self.client.force_login(self.moderator)
            rendered = self.client.get(reverse(route, args=args))
            self.assertContains(rendered, boundary)
            self.assertIn('no-store', rendered['Cache-Control'])
        self.assertFalse(Version.objects.exists())
        self.assertEqual(Appeal.objects.count(), 1)


class ModerationConnectionRaces(SimpleTestCase):
    def test_file_database_pause_orderings_and_competing_decisions(self):
        with tempfile.TemporaryDirectory(prefix='psyche-moderation-races-') as directory:
            environment = {**os.environ, 'LOCAL_DEVELOPMENT': '1', 'PILOT_APPROVED': '1',
                           'DATABASE_PATH': str(Path(directory) / 'isolated.sqlite3'),
                           'DJANGO_SETTINGS_MODULE': 'config.settings'}
            environment.pop('DATABASE_URL', None)
            script = 'import django; django.setup(); from django.core.management import call_command; call_command("migrate", verbosity=0); from archive.tests.moderation_race_fixture import run_moderation_races; import json; print(json.dumps(run_moderation_races()))'
            result = subprocess.run([sys.executable, '-c', script], cwd=Path(__file__).resolve().parents[2], env=environment, text=True, capture_output=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr)
        evidence = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(evidence['pause_first'], 'submission_rejected_draft_saved')
        self.assertEqual(evidence['submit_first'], 'submission_retained_then_paused')
        self.assertEqual(len(evidence['competing_decisions']), 3)
