"""Operator recovery guarantees with synthetic sessions and private failure sentinels."""
import io
import os
from unittest.mock import patch

from django.contrib.sessions.models import Session
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError, connection
from django.test import TestCase
from django.utils import timezone

from archive.models import Capacity, Event, RateBucket, WorkOSLoginAttempt, WorkOSCredential, WorkOSIdentity


class RestorePreparation(TestCase):
    def setUp(self):
        self.capacity = Capacity.objects.get(pk=1)
        self.capacity.intake_open = True
        self.capacity.save()
        session = Session.objects.create(session_key='synthetic-restored-session', session_data='synthetic-only', expire_date=timezone.now())
        from django.contrib.auth import get_user_model
        user = get_user_model().objects.create_user('synthetic-restore-credential')
        identity = WorkOSIdentity.objects.create(user=user, client_id='client_synthetic', subject='user_synthetic')
        WorkOSCredential.objects.create(session=session, identity=identity, sealed='synthetic-sealed-only',
            provider_session_id='session_synthetic', expires_at=timezone.now())
        RateBucket.objects.create(key='synthetic-restored-rate', count=4, expires_at=timezone.now())
        WorkOSLoginAttempt.objects.create(state_hash='synthetic-restored-state', browser_hash='synthetic-browser',
            verifier='synthetic-verifier', expires_at=timezone.now())
        self.arguments = {'expected_database': str(connection.settings_dict['NAME']),
                          'expected_host': 'local-file', 'expected_port': 0,
                          'reason': 'Synthetic isolated restore approval reference'}

    def prepare(self, **changes):
        arguments = {**self.arguments, **changes}
        output = io.StringIO()
        call_command('prepare_restored_archive', stdout=output, stderr=io.StringIO(), **arguments)
        return output.getvalue()

    def unchanged(self):
        self.capacity.refresh_from_db()
        self.assertTrue(self.capacity.intake_open)
        self.assertTrue(Session.objects.filter(session_key='synthetic-restored-session').exists())
        self.assertTrue(WorkOSCredential.objects.exists())
        self.assertTrue(RateBucket.objects.filter(pk='synthetic-restored-rate').exists())
        self.assertTrue(WorkOSLoginAttempt.objects.filter(pk='synthetic-restored-state').exists())
        self.assertFalse(Event.objects.filter(kind='restored_paused').exists())

    def test_offline_mode_is_required_before_database_verification_or_changes(self):
        with patch.dict(os.environ, {'RECOVERY_MODE': '', 'VERCEL': ''}):
            with patch('archive.management.commands.prepare_restored_archive.call_command') as verify:
                with self.assertRaises(CommandError):
                    self.prepare()
                verify.assert_not_called()
        self.unchanged()

    def test_serving_vercel_context_refuses_even_with_recovery_opt_in(self):
        with patch.dict(os.environ, {'RECOVERY_MODE': 'isolated-restore', 'VERCEL': '1'}):
            with self.assertRaises(CommandError):
                self.prepare()
        self.unchanged()

    def test_database_host_and_port_must_all_match_explicit_target(self):
        with patch.dict(os.environ, {'RECOVERY_MODE': 'isolated-restore', 'VERCEL': ''}):
            for wrong in [{'expected_database': 'other'}, {'expected_host': 'other'}, {'expected_port': 5432}]:
                with self.subTest(wrong=wrong), self.assertRaises(CommandError):
                    self.prepare(**wrong)
                self.unchanged()

    def test_success_revokes_and_pauses_without_deleting_records_and_safe_retry(self):
        with patch.dict(os.environ, {'RECOVERY_MODE': 'isolated-restore', 'VERCEL': ''}):
            output = self.prepare()
            self.assertIn('No serving cutover occurred', output)
            self.assertIn('revoked access since the snapshot', output)
            self.assertFalse(Session.objects.exists())
            self.assertFalse(WorkOSCredential.objects.exists())
            self.assertFalse(RateBucket.objects.exists())
            self.assertFalse(WorkOSLoginAttempt.objects.exists())
            self.capacity.refresh_from_db()
            self.assertFalse(self.capacity.intake_open)
            self.assertEqual(Event.objects.filter(kind='restored_paused').count(), 1)
            # Retrying an offline preparation keeps access revoked and creates a new audit event.
            self.prepare()
            self.capacity.refresh_from_db()
            self.assertFalse(self.capacity.intake_open)
            self.assertEqual(Event.objects.filter(kind='restored_paused').count(), 2)

    def test_verification_failure_is_redacted_and_does_not_modify_restore(self):
        with patch.dict(os.environ, {'RECOVERY_MODE': 'isolated-restore', 'VERCEL': ''}):
            with patch('archive.management.commands.prepare_restored_archive.call_command', side_effect=CommandError('PRIVATE_FAILURE_SENTINEL')):
                with self.assertRaises(CommandError) as caught:
                    self.prepare()
        self.assertNotIn('PRIVATE_FAILURE_SENTINEL', str(caught.exception))
        self.unchanged()

    def test_audit_failure_rolls_back_session_rate_and_intake_changes(self):
        with patch.dict(os.environ, {'RECOVERY_MODE': 'isolated-restore', 'VERCEL': ''}):
            with patch('archive.management.commands.prepare_restored_archive.Event.objects.create', side_effect=OperationalError('PRIVATE_SQL_SENTINEL')):
                with self.assertRaises(CommandError) as caught:
                    self.prepare()
        self.assertNotIn('PRIVATE_SQL_SENTINEL', str(caught.exception))
        self.unchanged()
