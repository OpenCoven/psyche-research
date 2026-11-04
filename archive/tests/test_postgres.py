"""Live PostgreSQL guarantees in disposable schemas of an explicitly dedicated test database.

SQLite runs skip these tests honestly. Set POSTGRES_GUARANTEE_TESTS=1 and
LOCAL_DEVELOPMENT=1 with DATABASE_URL naming a test_ database for a live run.
No schema outside the randomly created cr_test_ schema is migrated or dropped.
"""
import os
from pathlib import Path
import subprocess
import sys
import textwrap
from unittest import skipUnless

from django.db import connection
from django.test import SimpleTestCase


ROOT = Path(__file__).resolve().parents[2]

SCHEMA_HARNESS = '''
import os
import uuid
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.db import connections

database = connections.databases['default']
if (database['ENGINE'] != 'django.db.backends.postgresql'
        or not settings.LOCAL_DEVELOPMENT
        or os.environ.get('POSTGRES_GUARANTEE_TESTS') != '1'
        or not str(database['NAME']).startswith('test_')):
    raise RuntimeError('Live PostgreSQL guarantees require explicit opt-in and a dedicated test_ database in local test mode.')

schema = 'cr_test_' + uuid.uuid4().hex
db = connections['default']
created = False
try:
    with db.cursor() as cursor:
        cursor.execute('CREATE SCHEMA ' + db.ops.quote_name(schema))
    created = True
    db.close()
    options = dict(database.get('OPTIONS', {}))
    options['options'] = (options.get('options', '') + ' -c search_path=' + schema).strip()
    database['OPTIONS'] = options
    db.settings_dict['OPTIONS'] = options
    call_command('migrate', verbosity=0)
    BODY
finally:
    connections.close_all()
    if created:
        with db.cursor() as cursor:
            cursor.execute('DROP SCHEMA ' + db.ops.quote_name(schema) + ' CASCADE')
        db.close()
'''

FIXTURE_IMPORTS = '''
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import DatabaseError, transaction
from archive import services
from archive.models import Capacity, Decision, Event, Submission, Version
from archive.tests.test_guarantees import content

User = get_user_model()
author = User.objects.create_user('synthetic-postgres-author')
other = User.objects.create_user('synthetic-postgres-other')
moderator = User.objects.create_user('synthetic-postgres-moderator')
moderator.groups.add(Group.objects.get(name='moderators'))
capacity = Capacity.objects.get(pk=1)
assert not capacity.intake_open, 'Fresh migrations must pause intake'
capacity.intake_open = True
capacity.save()

def assert_integrity_triggers():
    expected = {f'archive_{table}_no_{action}' for table in ('version','decision','event') for action in ('update','delete')}
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT t.tgname, t.tgenabled, pg_get_triggerdef(t.oid)
            FROM pg_trigger AS t
            JOIN pg_class AS c ON c.oid = t.tgrelid
            JOIN pg_namespace AS n ON n.oid = c.relnamespace
            WHERE n.nspname = current_schema() AND NOT t.tgisinternal
        """)
        actual = {name: (enabled, definition) for name, enabled, definition in cursor.fetchall()}
    assert set(actual) == expected, 'Every append-only trigger must be installed in this schema'
    for name, (enabled, definition) in actual.items():
        assert enabled == 'O', 'An append-only trigger is disabled'
        assert 'archive_reject_append_only()' in definition
        if name.endswith('_no_delete'):
            assert 'BEFORE DELETE OR TRUNCATE' in definition and 'FOR EACH STATEMENT' in definition
        else:
            assert 'BEFORE UPDATE' in definition and 'FOR EACH ROW' in definition

def submit(actor, payload=None, work_id=None):
    row = services.create_submission(actor, work_id)
    return services.save_submission(actor, row.pk, payload or content(), row.revision, submit=True)

def publish(row):
    services.decide(moderator, row.pk, 'publish', 'Synthetic PostgreSQL completeness moderation.', row.revision, conflicts='None; synthetic fixture')
    row.refresh_from_db()
    return Version.objects.get(submission=row)
'''


@skipUnless(connection.vendor == 'postgresql', 'Live PostgreSQL backend not selected; SQLite does not prove PostgreSQL guarantees.')
class PostgreSQLGuarantees(SimpleTestCase):
    def run_in_disposable_schema(self, body):
        # This subprocess has ordinary connections rather than Django test flush or disabled guards.
        indented = textwrap.indent(textwrap.dedent(body).strip(), '    ')
        script = SCHEMA_HARNESS.replace('    BODY', indented)
        environment = {**os.environ, 'DJANGO_SETTINGS_MODULE': 'config.settings'}
        result = subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=environment,
                                capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + '\n' + result.stderr)

    def test_live_migrations_freeze_publication_withdrawal_and_six_immutable_guards(self):
        self.run_in_disposable_schema(FIXTURE_IMPORTS + '''
assert_integrity_triggers()
sentinel = 'SYNTHETIC-POSTGRES-WITHDRAWN-BODY-916c0'
row = submit(author, content(abstract=sentinel))
frozen = row.frozen_snapshot.copy()
try:
    services.save_submission(author, row.pk, content(title='Synthetic forbidden edit'), row.revision)
except services.WorkflowError as error:
    assert error.status == 409
else:
    raise AssertionError('Submitted snapshot was editable')
author.groups.add(Group.objects.get(name='moderators'))
try:
    services.decide(author, row.pk, 'publish', 'Synthetic forbidden self approval.', row.revision, conflicts='None; synthetic fixture')
except services.WorkflowError as error:
    assert error.status == 403
else:
    raise AssertionError('Moderator author could self-approve')
first = publish(row)
assert first.snapshot == frozen and first.digest == row.digest
assert Decision.objects.get(submission=row).conflicts == 'None; synthetic fixture'

# Direct SQL exercises database enforcement, bypassing model save/delete methods.
for table, identifier, column in (
        ('archive_version', first.pk, 'digest'),
        ('archive_decision', Decision.objects.get(submission=row).pk, 'reason'),
        ('archive_event', Event.objects.first().pk, 'target')):
    for statement in (
            f'UPDATE {table} SET {column}={column} WHERE id=%s',
            f'DELETE FROM {table} WHERE id=%s'):
        try:
            with transaction.atomic(), db.cursor() as cursor:
                cursor.execute(statement, [identifier])
        except DatabaseError as error:
            assert getattr(error.__cause__, 'sqlstate', None) == '23514'
            assert 'append-only record' in str(error)
        else:
            raise AssertionError('Append-only SQL mutation succeeded')
    try:
        with transaction.atomic(), db.cursor() as cursor:
            cursor.execute(f'TRUNCATE TABLE {table} CASCADE')
    except DatabaseError as error:
        assert getattr(error.__cause__, 'sqlstate', None) == '23514'
    else:
        raise AssertionError('TRUNCATE bypassed append-only protection')

correction = submit(author, content(abstract=sentinel, change_note='Synthetic PostgreSQL correction.'), first.work_id)
second = publish(correction)
first.refresh_from_db()
assert first.snapshot == frozen and second.number == 2
services.withdraw(author, first.work_id, 'Synthetic PostgreSQL withdrawal.')
from django.test import Client
from django.urls import reverse
from archive.views import public_versions
client = Client()
for number in (1, 2):
    for route in ('version', 'export_version'):
        response = client.get(reverse(route, args=[first.work_id, number]))
        assert response.status_code == 200 and sentinel.encode() not in response.content
assert not public_versions().filter(work_id=first.work_id).exists()
assert sentinel.encode() not in client.get(reverse('archive')).content
assert_integrity_triggers()
''')

    def test_live_concurrent_capacity_and_duplicate_decision_are_serialized(self):
        self.run_in_disposable_schema(FIXTURE_IMPORTS + '''
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from django.db import close_old_connections

capacity.queue_limit = 1
capacity.save()
first = services.create_submission(author)
second = services.create_submission(other)
barrier = Barrier(2)
def attempt_submission(author_id, submission_id):
    close_old_connections()
    try:
        actor = User.objects.get(pk=author_id)
        barrier.wait(timeout=10)
        services.save_submission(actor, submission_id, content(), 0, submit=True)
        return 'submitted'
    except services.WorkflowError as error:
        assert error.status == 429
        return 'bounded'
    finally:
        close_old_connections()
with ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(attempt_submission, author.pk, first.pk), pool.submit(attempt_submission, other.pk, second.pk)]
    outcomes = [future.result(timeout=30) for future in futures]
assert sorted(outcomes) == ['bounded', 'submitted']
queued = Submission.objects.get(state='submitted')
barrier = Barrier(2)
def attempt_decision():
    close_old_connections()
    try:
        actor = User.objects.get(pk=moderator.pk)
        barrier.wait(timeout=10)
        result = services.decide(actor, queued.pk, 'publish', 'Synthetic exact concurrent decision.', queued.revision, conflicts='None; synthetic fixture')
        return result.pk
    finally:
        close_old_connections()
with ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(attempt_decision), pool.submit(attempt_decision)]
    decisions = [future.result(timeout=30) for future in futures]
assert decisions[0] == decisions[1]
assert Decision.objects.count() == Version.objects.count() == 1
assert_integrity_triggers()
''')

    def test_live_same_principal_rate_limit_cannot_lose_concurrent_attempts(self):
        self.run_in_disposable_schema(FIXTURE_IMPORTS + '''
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import patch
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from django.test import RequestFactory
from archive.middleware import WriteLimitMiddleware
from archive.models import RateBucket

barrier = Barrier(12)
def attempt():
    close_old_connections()
    try:
        request = RequestFactory().post('/synthetic-rate-probe/', 'probe=1', content_type='application/x-www-form-urlencoded', REMOTE_ADDR='192.0.2.123')
        request.user = AnonymousUser()
        barrier.wait(timeout=10)
        response = WriteLimitMiddleware(lambda request: None).process_view(request, lambda request: None, (), {})
        return response.status_code if response is not None else 200
    finally:
        close_old_connections()
with patch('archive.middleware.time.time', return_value=1700000000), ThreadPoolExecutor(max_workers=12) as pool:
    futures = [pool.submit(attempt) for _ in range(12)]
    outcomes = [future.result(timeout=30) for future in futures]
assert outcomes.count(200) == 10 and outcomes.count(429) == 2, outcomes
assert RateBucket.objects.count() == 1 and RateBucket.objects.get().count == 10
''')

    def test_live_verifier_rejects_weakened_function_conditional_or_scoped_trigger_and_missing_column(self):
        self.run_in_disposable_schema(FIXTURE_IMPORTS + '''
from io import StringIO
from django.core.management.base import CommandError

def verify_good():
    call_command('verify_archive', stdout=StringIO())

def verify_refuses(label):
    try:
        call_command('verify_archive', stdout=StringIO())
    except CommandError as error:
        message = str(error)
        for private in (schema, str(database['NAME']), database.get('USER'), database.get('PASSWORD'), os.environ.get('DATABASE_URL')):
            if private:
                assert private not in message, 'Verification error exposed connection or schema material'
    else:
        raise AssertionError('Archive verifier accepted corruption: ' + label)

verify_good()
with db.cursor() as cursor:
    cursor.execute("SELECT pg_get_functiondef('archive_reject_append_only()'::regprocedure)")
    original_function = cursor.fetchone()[0]
    cursor.execute("SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname='archive_version_no_update' AND tgrelid='archive_version'::regclass")
    original_trigger = cursor.fetchone()[0]

# Correct trigger names do not compensate for a reject function that now permits writes.
try:
    with db.cursor() as cursor:
        cursor.execute("CREATE OR REPLACE FUNCTION archive_reject_append_only() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$")
    verify_refuses('no-op append-only function')
finally:
    with db.cursor() as cursor:
        cursor.execute(original_function)
verify_good()

for replacement, label in (
        ('CREATE TRIGGER archive_version_no_update BEFORE UPDATE ON archive_version FOR EACH ROW WHEN (false) EXECUTE FUNCTION archive_reject_append_only()', 'disabled-by-condition trigger'),
        ('CREATE TRIGGER archive_version_no_update BEFORE UPDATE OF snapshot ON archive_version FOR EACH ROW EXECUTE FUNCTION archive_reject_append_only()', 'column-scoped update trigger')):
    try:
        with db.cursor() as cursor:
            cursor.execute('DROP TRIGGER archive_version_no_update ON archive_version')
            cursor.execute(replacement)
        verify_refuses(label)
    finally:
        with db.cursor() as cursor:
            cursor.execute('DROP TRIGGER IF EXISTS archive_version_no_update ON archive_version')
            cursor.execute(original_trigger)
    verify_good()

# A matching migration ledger alone cannot establish that required application columns exist.
try:
    with db.cursor() as cursor:
        cursor.execute('ALTER TABLE archive_report DROP COLUMN resolution')
    verify_refuses('missing application column')
finally:
    with db.cursor() as cursor:
        cursor.execute("ALTER TABLE archive_report ADD COLUMN resolution text NOT NULL DEFAULT ''")
        cursor.execute('ALTER TABLE archive_report ALTER COLUMN resolution DROP DEFAULT')
verify_good()
''')

    def test_live_existing_publication_survives_upgrade_reverse_and_trigger_reinstallation(self):
        self.run_in_disposable_schema('''
import hashlib
import json
from django.db import DatabaseError, transaction
from django.db.migrations.executor import MigrationExecutor

call_command('migrate', 'archive', '0002_pilot_invariants', verbosity=0)
historical = MigrationExecutor(db).loader.project_state([('archive','0002_pilot_invariants')]).apps
user = historical.get_model('auth', 'User').objects.create(username='synthetic-postgres-upgrade')
work = historical.get_model('archive', 'Work').objects.create(author_id=user.pk)
submission = historical.get_model('archive', 'Submission').objects.create(author_id=user.pk, work_id=work.pk, state='published')
snapshot = {'title': 'SYNTHETIC PostgreSQL preserved publication'}
digest = hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(',',':')).encode()).hexdigest()
historical.get_model('archive', 'Version').objects.create(work_id=work.pk, submission_id=submission.pk, number=1, snapshot=snapshot, digest=digest)
historical.get_model('archive', 'Decision').objects.create(submission_id=submission.pk, actor_id=user.pk, revision=0, digest=digest, action='publish', reason='Synthetic historical decision.')
for target in ('0004_appeal_decision_binding', '0002_pilot_invariants', '0001_initial', '0004_appeal_decision_binding'):
    call_command('migrate', 'archive', target, verbosity=0)
    with db.cursor() as cursor:
        cursor.execute("""
            SELECT t.tgname FROM pg_trigger AS t
            JOIN pg_class AS c ON c.oid=t.tgrelid
            JOIN pg_namespace AS n ON n.oid=c.relnamespace
            WHERE n.nspname=current_schema() AND NOT t.tgisinternal
        """)
        installed = {row[0] for row in cursor.fetchall()}
        cursor.execute("SELECT count(*) FROM pg_proc WHERE proname='archive_reject_append_only' AND pronamespace=current_schema()::regnamespace")
        functions = cursor.fetchone()[0]
    if target == '0001_initial':
        assert installed == set() and functions == 0
    else:
        assert installed == {f'archive_{table}_no_{action}' for table in ('version','decision','event') for action in ('update','delete')}
        assert functions == 1
        try:
            with transaction.atomic(), db.cursor() as cursor:
                cursor.execute('UPDATE archive_decision SET reason=reason')
        except DatabaseError as error:
            assert getattr(error.__cause__, 'sqlstate', None) == '23514'
        else:
            raise AssertionError('Migration left historical decisions mutable')
from archive.models import Version, Decision
assert Version.objects.get().snapshot == snapshot and Version.objects.get().digest == digest
assert Decision.objects.get().conflicts == 'Not recorded for this legacy decision'
''')
