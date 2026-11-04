"""Read-only product invariant check for a restored database; never switches serving or opens intake."""
from django.core.management.base import BaseCommand,CommandError
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from archive.models import Version,Capacity
from archive.services import digest
from archive.recovery import verify,REQUIRED_TRIGGERS

class Command(BaseCommand):
    help='Read-only schema/content integrity check for an isolated restored database; no hosted recovery certification.'
    def handle(self,*args,**options):
        try:
            connection.ensure_connection()
            if connection.vendor=='sqlite':
                verify(connection.connection)
            elif connection.vendor=='postgresql':
                loader=MigrationLoader(connection)
                if set(loader.graph.leaf_nodes())-set(loader.applied_migrations):
                    raise ValueError('Database is not at current migrations.')
                from django.apps import apps
                tables=set(connection.introspection.table_names())
                for model in apps.get_models(include_auto_created=True):
                    if model._meta.managed:
                        if model._meta.db_table not in tables:
                            raise ValueError('Required application table missing.')
                        with connection.cursor() as cursor:
                            columns={column.name for column in connection.introspection.get_table_description(cursor,model._meta.db_table)}
                        if not {field.column for field in model._meta.local_concrete_fields}<=columns:
                            raise ValueError('Required application column missing.')
                with connection.cursor() as cursor:
                    cursor.execute("SELECT oid,prosrc,prosecdef FROM pg_proc WHERE oid='archive_reject_append_only()'::regprocedure AND prorettype='trigger'::regtype AND prolang=(SELECT oid FROM pg_language WHERE lanname='plpgsql')")
                    function=cursor.fetchone()
                    expected="begin raise exception 'append-only record' using errcode = '23514'; end;"
                    if not function or ' '.join(function[1].lower().split())!=expected or function[2]:
                        raise ValueError('Append-only function contract mismatch.')
                    cursor.execute("SELECT tgname,tgenabled,tgtype,tgfoid,tgnargs,tgqual IS NULL,relname,tgattr::text FROM pg_trigger JOIN pg_class ON pg_class.oid=tgrelid WHERE tgrelid IN ('archive_version'::regclass,'archive_decision'::regclass,'archive_event'::regclass) AND NOT tgisinternal")
                    found={row[0]:row[1:] for row in cursor.fetchall()}
                for name in REQUIRED_TRIGGERS:
                    row=found.get(name)
                    expected_type=19 if name.endswith('_update') else 42
                    if not row or row!=('O',expected_type,function[0],0,True,name.rsplit('_no_',1)[0],''):
                        raise ValueError('Required enabled unconditional append-only trigger contract missing.')
                for version in Version.objects.iterator(chunk_size=100):
                    if digest(version.snapshot)!=version.digest:
                        raise ValueError('Published content digest mismatch.')
            else:
                raise ValueError('Unsupported database backend.')
            if Capacity.objects.count()!=1:
                raise ValueError('Invalid capacity singleton.')
        except Exception:
            # Connection exceptions can contain credentials/hostnames or private SQL values.
            raise CommandError('Archive verification failed. Keep the restore offline and investigate in the approved private operating environment.') from None
        self.stdout.write('Schema and published digests checked. This does not verify provider backups, access reconciliation or hosted acceptance.')
