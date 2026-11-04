"""Offline restore preparation only. Never selects a target, restores data, or changes serving."""
import io
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.contrib.sessions.models import Session
from django.db import connection, transaction

from archive.models import Capacity, Event, RateBucket


class Command(BaseCommand):
    help = 'Verify an explicitly identified isolated restore, revoke sessions and pause intake. No cutover or access reconciliation.'

    def add_arguments(self, parser):
        parser.add_argument('--expected-database', required=True)
        parser.add_argument('--expected-host', required=True)
        parser.add_argument('--expected-port', required=True, type=int)
        parser.add_argument('--reason', required=True)

    def handle(self, *args, **options):
        # Check offline intent and all endpoint identifiers before opening the connection.
        if os.environ.get('VERCEL') == '1' or os.environ.get('RECOVERY_MODE') != 'isolated-restore':
            raise CommandError('Use an offline recovery runner with RECOVERY_MODE=isolated-restore. Never run restore preparation in the serving application.')
        reason = options['reason'].strip()
        if not reason or len(reason) > 1000:
            raise CommandError('Provide a bounded operator reason or approval reference without private manuscript material.')
        configured = connection.settings_dict
        if connection.vendor == 'postgresql':
            endpoint = (str(configured.get('HOST', '')).lower().rstrip('.'), int(configured.get('PORT') or 5432))
        elif connection.vendor == 'sqlite':
            endpoint = ('local-file', 0)
        else:
            raise CommandError('Unsupported recovery backend.')
        expected = (options['expected_host'].lower().rstrip('.'), options['expected_port'])
        if endpoint != expected or str(configured['NAME']) != options['expected_database']:
            raise CommandError('The configured endpoint does not match the explicitly expected isolated target. No changes were made.')
        try:
            with transaction.atomic():
                if connection.vendor == 'postgresql':
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT current_database()')
                        if cursor.fetchone()[0] != options['expected_database']:
                            raise CommandError('The connected database does not match the explicitly expected isolated target.')
                capacity = Capacity.objects.select_for_update().get(pk=1)
                call_command('verify_archive', stdout=io.StringIO(), stderr=io.StringIO())
                Session.objects.all().delete()
                RateBucket.objects.all().delete()
                capacity.intake_open = False
                capacity.revision += 1
                capacity.save(update_fields=['intake_open', 'revision', 'updated_at'])
                Event.objects.create(actor=None, kind='restored_paused', target='capacity',
                                     details={'reason': reason, 'scope': 'offline_preparation_only'})
        except Exception:
            # Driver/verification errors may contain connection or private SQL values.
            raise CommandError('Restore preparation failed and its changes were rolled back. Keep the target offline and investigate through the approved private recovery process.') from None
        self.stdout.write('Restored archive verified and prepared offline: sessions revoked, rate buckets cleared, intake paused. Keep it offline until withdrawals, privacy changes and revoked access since the snapshot are reconciled. No serving cutover occurred.')
