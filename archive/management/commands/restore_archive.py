from django.db import connection
from django.core.management.base import BaseCommand, CommandError
from archive.recovery import copy_database

class Command(BaseCommand):
    help='Restore into a NEW destination, verify, invalidate sessions and pause intake. Does not cut over.'
    def add_arguments(self,parser):
        parser.add_argument('source')
        parser.add_argument('destination')
    def handle(self,*args,**options):
        if connection.vendor!='sqlite':
            raise CommandError('This file snapshot helper is SQLite-only. Use the approved PostgreSQL backup/PITR and isolated restore runbook.')
        try:
            digest=copy_database(options['source'],options['destination'],restore=True)
        except Exception as exc:
            raise CommandError(str(exc))
        self.stdout.write('Restore candidate verified; sessions revoked and intake paused. SHA-256: '+digest)
