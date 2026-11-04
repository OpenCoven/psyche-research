from django.conf import settings
from django.db import connection
from django.core.management.base import BaseCommand, CommandError
from archive.recovery import copy_database

class Command(BaseCommand):
    help='Create a consistent mode-0600 snapshot at a new private path. Never overwrites.'
    def add_arguments(self,parser):
        parser.add_argument('destination')
    def handle(self,*args,**options):
        if connection.vendor!='sqlite':
            raise CommandError('This file snapshot helper is SQLite-only. Use the approved PostgreSQL backup/PITR and isolated restore runbook.')
        try:
            digest=copy_database(settings.DATABASE_PATH,options['destination'])
        except Exception as exc:
            raise CommandError(str(exc))
        self.stdout.write('Snapshot verified. SHA-256: '+digest)
