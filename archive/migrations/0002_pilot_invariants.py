from django.db import migrations

TABLES = ('archive_version','archive_decision','archive_event')
POSTGRES_FUNCTION = 'archive_reject_append_only'

def bootstrap(apps,schema_editor):
    apps.get_model('archive','Capacity').objects.get_or_create(pk=1)
    apps.get_model('auth','Group').objects.get_or_create(name='moderators')

def install_triggers(apps,schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == 'sqlite':
        for table in TABLES:
            for action in ('UPDATE','DELETE'):
                schema_editor.execute(f"CREATE TRIGGER {table}_no_{action.lower()} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'append-only record'); END")
    elif vendor == 'postgresql':
        # Keep the reject function in the same schema as the application tables.
        # SQLSTATE 23514 makes the immutable-record violation a database integrity error.
        schema_editor.execute(f"""
            CREATE FUNCTION {POSTGRES_FUNCTION}() RETURNS trigger
            LANGUAGE plpgsql AS $archive_append_only$
            BEGIN
                RAISE EXCEPTION 'append-only record' USING ERRCODE = '23514';
            END;
            $archive_append_only$
        """)
        for table in TABLES:
            schema_editor.execute(f"CREATE TRIGGER {table}_no_update BEFORE UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION {POSTGRES_FUNCTION}()")
            # PostgreSQL TRUNCATE bypasses row DELETE triggers; block it explicitly.
            schema_editor.execute(f"CREATE TRIGGER {table}_no_delete BEFORE DELETE OR TRUNCATE ON {table} FOR EACH STATEMENT EXECUTE FUNCTION {POSTGRES_FUNCTION}()")
    else:
        raise RuntimeError('Archive immutability supports only SQLite and PostgreSQL.')

def remove_triggers(apps,schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == 'sqlite':
        for table in TABLES:
            for action in ('update','delete'):
                schema_editor.execute(f'DROP TRIGGER IF EXISTS {table}_no_{action}')
    elif vendor == 'postgresql':
        for table in TABLES:
            for action in ('update','delete'):
                schema_editor.execute(f'DROP TRIGGER IF EXISTS {table}_no_{action} ON {table}')
        schema_editor.execute(f'DROP FUNCTION IF EXISTS {POSTGRES_FUNCTION}()')
    else:
        raise RuntimeError('Archive immutability supports only SQLite and PostgreSQL.')

class Migration(migrations.Migration):
    dependencies = [('archive','0001_initial')]
    operations = [migrations.RunPython(bootstrap,migrations.RunPython.noop),
                  migrations.RunPython(install_triggers,remove_triggers)]
