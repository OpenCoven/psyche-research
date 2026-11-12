import io
import json
import os
import tempfile
from datetime import timedelta
from pathlib import Path
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django.utils import timezone
from waitlist.models import CollectionState, Registration


@override_settings(WAITLIST_COLLECTION_ENABLED=True, WAITLIST_OPERATOR_MODE=True)
class OperatorTests(TestCase):
    def setUp(self):
        CollectionState.objects.update_or_create(pk=1, defaults={'paused': False, 'retained_count': 1})
        self.row = Registration.objects.create(email='private@example.net', name='=2+2', interest='both', privacy_version='2026-11-11')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def command(self, action, **kwargs):
        output = io.StringIO()
        call_command('waitlist_ops', action, stdout=output, **kwargs)
        self.assertNotIn('private@example.net', output.getvalue())
        return output.getvalue()

    def test_pause_and_resume_only_through_operator_mode(self):
        self.command('pause')
        self.assertTrue(CollectionState.objects.get().paused)
        self.command('resume')
        self.assertFalse(CollectionState.objects.get().paused)
        with override_settings(WAITLIST_OPERATOR_MODE=False):
            with self.assertRaises(CommandError):
                self.command('pause')

    def test_export_is_private_json_and_refuses_overwrite_or_public_path(self):
        target = self.root / 'private.json'
        self.command('export', output=str(target))
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        self.assertEqual(json.loads(target.read_text())[0]['name'], '=2+2')
        with self.assertRaises(CommandError):
            self.command('export', output=str(target))
        with self.assertRaises(CommandError):
            self.command('export', output=str(Path.cwd() / 'static' / 'leak.json'))

    def test_delete_uses_private_file_and_leaves_recovery_suppression(self):
        source = self.root / 'address.txt'
        source.write_text('PRIVATE@example.net\n')
        source.chmod(0o600)
        self.command('delete', email_file=str(source), ledger=str(self.root / 'erasures.jsonl'))
        self.assertFalse(Registration.objects.exists())
        self.assertEqual(CollectionState.objects.get().retained_count, 0)
        from waitlist.models import Erasure
        erasure = Erasure.objects.get()
        self.assertNotIn('private', erasure.key)
        source.chmod(0o644)
        with self.assertRaises(CommandError):
                self.command('delete', email_file=str(source), ledger=str(self.root / 'erasures.jsonl'))

    def test_expiry_cleanup_preserves_fresh_registrations(self):
        Registration.objects.filter(pk=self.row.pk).update(created_at=timezone.now() - timedelta(days=91))
        Registration.objects.create(email='fresh@example.net', interest='reader', privacy_version='2026-11-11')
        CollectionState.objects.update(retained_count=2)
        self.command('purge')
        self.assertEqual(list(Registration.objects.values_list('email', flat=True)), ['fresh@example.net'])
        self.assertEqual(CollectionState.objects.get().retained_count, 1)
