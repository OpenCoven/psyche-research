"""Live PostgreSQL guarantees in disposable schemas of an explicitly dedicated test database.

SQLite runs skip these tests honestly. Set POSTGRES_GUARANTEE_TESTS=1 and
LOCAL_DEVELOPMENT=1 with DATABASE_URL naming a test_ database for a live run.
Only randomly created cr_test_ schemas and a newly created test_coven_restore_ database are changed or dropped.
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
    def test_live_pause_orderings_and_competing_moderation_decisions(self):
        self.run_in_disposable_schema('''
from archive.tests.moderation_race_fixture import run_moderation_races
run_moderation_races()
''')

    def test_live_refresh_claim_commits_before_exchange_and_survives_view_rollback(self):
        self.run_in_disposable_schema('''
from archive.tests.session_overlap_fixture import run_durable_refresh_boundary
run_durable_refresh_boundary()
''')

    def run_in_disposable_schema(self, body, timeout=120):
        # This subprocess has ordinary connections rather than Django test flush or disabled guards.
        indented = textwrap.indent(textwrap.dedent(body).strip(), '    ')
        script = SCHEMA_HARNESS.replace('    BODY', indented)
        environment = {**os.environ, 'DJANGO_SETTINGS_MODULE': 'config.settings'}
        result = subprocess.run([sys.executable, '-c', script], cwd=ROOT, env=environment,
                                capture_output=True, text=True, timeout=timeout)
        self.assertEqual(result.returncode, 0, result.stdout + '\n' + result.stderr)

    def test_live_workos_callback_is_consumed_once_across_connections(self):
        self.run_in_disposable_schema('''
import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import Client, override_settings
from workos import WorkOSClient
from archive.models import WorkOSIdentity, WorkOSLoginAttempt
from archive.tests.test_workos_auth import SYNTHETIC_SETTINGS

author = get_user_model().objects.create_user('synthetic-workos-postgres-author')
WorkOSIdentity.objects.create(user=author,client_id='client_synthetic',subject='user_synthetic')
key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
token = jwt.encode({'iss':SYNTHETIC_SETTINGS['WORKOS_ISSUER'],'sub':'user_synthetic',
    'sid':'session_synthetic','client_id':'client_synthetic','iat':int(time.time())-5,
    'exp':int(time.time())+300},key,algorithm='RS256')
response = SimpleNamespace(user=SimpleNamespace(id='user_synthetic',email_verified=True),
    access_token=token,refresh_token='synthetic-postgres-refresh',impersonator=None)
real = WorkOSClient(api_key='sk_test_synthetic_only',client_id='client_synthetic')
committed_attempt_counts = []
def exchange_after_durable_consumption(**kwargs):
    probe = db.copy(alias='synthetic-callback-commit-probe')
    try:
        with probe.cursor() as cursor:
            cursor.execute('SELECT count(*) FROM archive_workosloginattempt')
            committed_attempt_counts.append(cursor.fetchone()[0])
        assert committed_attempt_counts[-1] == 0, 'Callback state must be durably consumed before provider exchange'
    finally:
        probe.close()
    return response
with override_settings(**SYNTHETIC_SETTINGS), patch('archive.workos_auth.client') as factory, patch('archive.workos_auth.jwks') as keys:
    api = factory.return_value
    api.user_management.get_authorization_url.side_effect = real.user_management.get_authorization_url
    api.user_management.authenticate_with_code.side_effect = exchange_after_durable_consumption
    keys.return_value.get_signing_key_from_jwt.return_value = SimpleNamespace(key=key.public_key())
    browser = Client()
    started = browser.post('/accounts/workos/start/',urlencode({'next':'/workspace/'}),content_type='application/x-www-form-urlencoded')
    assert started.status_code==302, started.status_code
    state = parse_qs(urlsplit(started['Location']).query)['state'][0]
    cookies = browser.cookies.copy()
    def callback_once():
        close_old_connections()
        try:
            browser = Client()
            browser.cookies = cookies.copy()
            return browser.get('/accounts/workos/callback/',{'state':state,'code':'synthetic-postgres-code'}).status_code
        finally:
            close_old_connections()
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _:callback_once(),range(2)))
    assert sorted(outcomes)==[302,400], outcomes
    assert api.user_management.authenticate_with_code.call_count==1
    assert committed_attempt_counts==[0], committed_attempt_counts
    assert WorkOSLoginAttempt.objects.count()==0
''')

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

    def test_live_logical_dump_restore_preserves_representative_records_and_prepares_only_new_target(self):
        self.run_in_disposable_schema(FIXTURE_IMPORTS + r'''
import hashlib
import json
from io import StringIO
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
from urllib.parse import urlsplit, urlunsplit
from datetime import timedelta
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.utils import timezone
from archive.models import Appeal, Report, RateBucket, Work, WorkOSIdentity, WorkOSLoginAttempt, WorkOSCredential, CONTENT_FIELDS

# Use the exact ephemeral CI service's clients rather than an unrelated runner version.
container = os.environ.get('POSTGRES_TEST_CONTAINER_ID', '')
assert shutil.which('docker') and re.fullmatch(r'[a-f0-9]{12,64}', container), 'Logical recovery requires the dedicated PostgreSQL CI service container'
assert db.pg_version // 10000 == 16, 'This recovery drill requires the PostgreSQL 16 service'
sensitive_values = [os.environ.get('DATABASE_URL'), database.get('PASSWORD'), database.get('USER'), str(database['NAME'])]

def container_command(tool, *arguments, input_file=None, output_file=None):
    assert tool in ('pg_dump', 'pg_restore')
    script = 'case "$POSTGRES_DB" in test_*) ;; *) exit 97;; esac; test "$POSTGRES_DB" = "$1" || exit 98; shift; export PGUSER="$POSTGRES_USER" PGDATABASE="$POSTGRES_DB" PGPASSWORD="$POSTGRES_PASSWORD"; exec "$@"'
    command = ['docker', 'exec', '-i', container, 'sh', '-c', script, 'coven-recovery-client', str(database['NAME']), tool, *arguments]
    result = subprocess.run(command, stdin=input_file, stdout=output_file if output_file is not None else subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=60)
    if result.returncode:
        # Never let connection/session credentials from tool errors enter test logs.
        diagnostic = result.stderr.decode('utf-8', 'replace')
        for private in sensitive_values:
            if private:
                diagnostic = diagnostic.replace(private, '[redacted]')
        raise AssertionError(tool + ' failed: ' + diagnostic[:2000])
    return result.stdout if output_file is None else b''

for tool in ('pg_dump', 'pg_restore'):
    version = container_command(tool, '--version').decode()
    assert re.search(r'\(PostgreSQL\) 16\.', version), 'Recovery client/server major versions differ'

# Cover private intake, human decisions, appeals, reports, exact versions, withdrawal, roles and sessions.
withdrawn_sentinel = 'SYNTHETIC-PG-RESTORE-WITHDRAWN-BODY-8c410'
first = publish(submit(author, content(title='SYNTHETIC withdrawn version one', claims=withdrawn_sentinel)))
second = publish(submit(author, content(title='SYNTHETIC withdrawn version two', claims=withdrawn_sentinel,
                                      change_note='Synthetic correction preserved by logical restore.'), first.work_id))
services.withdraw(author, first.work_id, 'Synthetic logical-restore withdrawal notice.')
visible = publish(submit(author, content(title='SYNTHETIC visible restored publication')))
private_decision = 'SYNTHETIC-PG-RESTORE-PRIVATE-DECISION-63d21'
private_appeal = 'SYNTHETIC-PG-RESTORE-PRIVATE-APPEAL-6c326'
private_report = 'SYNTHETIC-PG-RESTORE-PRIVATE-REPORT-92ab1'
declined = submit(author, content(title='SYNTHETIC declined private submission'))
services.decide(moderator, declined.pk, 'decline', private_decision, declined.revision, conflicts='None; synthetic restore fixture')
appeal = services.appeal(author, declined.pk, private_appeal)
report = services.report(visible.work_id, private_report)
private_draft = 'SYNTHETIC-PG-RESTORE-PRIVATE-DRAFT-4b199'
draft = services.create_submission(author)
draft = services.save_submission(author, draft.pk, content(title=private_draft, methods='', claims='', limitations=''), draft.revision)
pending_title = 'SYNTHETIC-PG-RESTORE-PRIVATE-PENDING-bb277'
pending = submit(author, content(title=pending_title))
author_password = secrets.token_urlsafe(32)
author.set_password(author_password)
author.save(update_fields=['password'])
sensitive_values.append(author_password)
session = SessionStore()
session['_auth_user_id'] = str(author.pk)
session['_auth_user_backend'] = 'django.contrib.auth.backends.ModelBackend'
session['_auth_user_hash'] = author.get_session_auth_hash()
session.save()
sensitive_values.extend([session.session_key, Session.objects.get(session_key=session.session_key).session_data])
RateBucket.objects.create(key='synthetic-postgres-logical-restore', count=3, expires_at=timezone.now()+timedelta(minutes=5))
identity=WorkOSIdentity.objects.create(user=author,client_id='client_synthetic',subject='user_synthetic')
WorkOSCredential.objects.create(session_id=session.session_key,identity=identity,sealed='synthetic-sealed-only',provider_session_id='session_synthetic',expires_at=timezone.now()+timedelta(hours=1))
WorkOSLoginAttempt.objects.create(state_hash='synthetic-state',browser_hash='synthetic-browser',verifier='synthetic-verifier',expires_at=timezone.now()+timedelta(minutes=5))

def source_state():
    return {
        'counts': {model._meta.label: model.objects.count() for model in (User, Group, Work, Submission, Version, Decision, Event, Appeal, Report, Session, RateBucket, WorkOSIdentity, WorkOSLoginAttempt, WorkOSCredential)},
        'workos_credentials':list(WorkOSCredential.objects.order_by('id').values('id','session_id','identity_id','sealed','provider_session_id','expires_at','claim','claimed_at')),
        'workos_identities':list(WorkOSIdentity.objects.order_by('id').values('user_id','client_id','subject','enabled')),
        'workos_attempts':list(WorkOSLoginAttempt.objects.order_by('state_hash').values('state_hash','browser_hash','verifier','next_path','expires_at')),
        'capacity': list(Capacity.objects.values('intake_open','queue_limit','per_author_limit','draft_limit','revision')),
        'versions': list(Version.objects.order_by('id').values('id','work_id','number','digest','snapshot','published_at')),
        'submissions': list(Submission.objects.order_by('id').values('id','state','revision','digest','frozen_snapshot',*CONTENT_FIELDS)),
        'events': list(Event.objects.order_by('id').values('id','actor_id','kind','target','details','created_at')),
        'withdrawals': list(Work.objects.order_by('id').values('id','withdrawn_at','withdrawal_reason')),
        'roles': list(moderator.groups.order_by('name').values_list('name',flat=True)),
        'accounts': [{'id':user.pk,'username':user.username,'password':user.password,'is_active':user.is_active,
                      'is_staff':user.is_staff,'is_superuser':user.is_superuser,'last_login':user.last_login,
                      'groups':list(user.groups.order_by('name').values_list('name',flat=True))}
                     for user in User.objects.order_by('pk')],
    }

before = source_state()
sensitive_values.extend(item['password'] for item in before['accounts'])
baseline_events = Event.objects.count()
assert before['counts']['sessions.Session'] == 1 and before['counts']['archive.RateBucket'] == 1
assert before['capacity'][0]['intake_open']
fixture = {
    'schema': schema, 'author_id': author.pk, 'other_id': other.pk, 'moderator_id': moderator.pk,
    'draft_id': str(draft.pk), 'pending_id': str(pending.pk), 'declined_id': str(declined.pk),
    'withdrawn_work_id': str(first.work_id), 'visible_work_id': str(visible.work_id),
    'appeal_id': appeal.pk, 'report_id': str(report.pk), 'session_key': session.session_key,
    'private_draft': private_draft, 'pending_title': pending_title, 'private_decision': private_decision,
    'private_appeal': private_appeal, 'private_report': private_report, 'withdrawn_sentinel': withdrawn_sentinel,
    'event_count': baseline_events, 'capacity': before['capacity'][0],
    'accounts': before['accounts'], 'author_password':author_password,
    'events': [{**item,'created_at':item['created_at'].isoformat()} for item in before['events']],
    'versions': [{'id': item['id'], 'work_id': str(item['work_id']), 'number': item['number'],
                  'digest': item['digest'], 'snapshot': item['snapshot'], 'published_at': item['published_at'].isoformat()}
                 for item in before['versions']],
}
target = 'test_coven_restore_' + uuid.uuid4().hex
assert target != database['NAME'] and re.fullmatch(r'test_coven_restore_[a-f0-9]{32}', target)
created_target = False
failed = False
try:
    # CREATE DATABASE refuses an existing target; only a successfully created UUID target is cleaned up.
    with db.cursor() as cursor:
        cursor.execute('CREATE DATABASE ' + db.ops.quote_name(target))
    created_target = True
    with tempfile.TemporaryDirectory(prefix='coven-postgres-private-dump-') as directory:
        private_directory = Path(directory)
        assert stat.S_IMODE(private_directory.stat().st_mode) == 0o700
        dump_path = private_directory / 'synthetic-logical-snapshot.dump'
        descriptor = os.open(dump_path, os.O_CREAT|os.O_EXCL|os.O_WRONLY, 0o600)
        with os.fdopen(descriptor,'wb') as output:
            container_command('pg_dump', '--format=custom', '--strict-names', '--no-owner', '--no-acl', '--schema='+schema, output_file=output)
            output.flush()
            os.fsync(output.fileno())
        assert stat.S_IMODE(dump_path.stat().st_mode) == 0o600
        snapshot_hash = hashlib.sha256(dump_path.read_bytes()).hexdigest()
        assert dump_path.read_bytes().startswith(b'PGDMP'), 'Expected a PostgreSQL custom-format archive'
        with dump_path.open('rb') as snapshot:
            container_command('pg_restore', '--dbname='+target, '--exit-on-error', '--single-transaction', '--no-owner', '--no-acl', input_file=snapshot)
        assert hashlib.sha256(dump_path.read_bytes()).hexdigest() == snapshot_hash

        parsed = urlsplit(os.environ['DATABASE_URL'])
        target_url = urlunsplit(parsed._replace(path='/'+target))
        target_environment = {**os.environ, 'DATABASE_URL':target_url, 'RECOVERY_MODE':'isolated-restore',
                              'POSTGRES_RESTORE_FIXTURE':json.dumps(fixture)}
        target_script = textwrap.dedent(r"""
import os,json
from io import StringIO
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.db import connections
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.test import Client
from django.urls import reverse
from archive.models import Capacity,Version,Submission,Work,Decision,Appeal,Report,Event,RateBucket,WorkOSIdentity,WorkOSLoginAttempt,WorkOSCredential
from archive import services
from archive.views import public_versions
fixture=json.loads(os.environ['POSTGRES_RESTORE_FIXTURE'])
database=connections.databases['default']
assert settings.LOCAL_DEVELOPMENT and database['NAME'].startswith('test_coven_restore_') and os.environ.get('POSTGRES_GUARANTEE_TESTS')=='1'
options=dict(database.get('OPTIONS',{}))
options['options']=(options.get('options','')+' -c search_path='+fixture['schema']).strip()
database['OPTIONS']=options
db=connections['default'];db.settings_dict['OPTIONS']=options
assert Session.objects.count()==RateBucket.objects.count()==WorkOSCredential.objects.count()==1
assert Capacity.objects.get(pk=1).intake_open
call_command('verify_archive',stdout=StringIO())
call_command('prepare_restored_archive',expected_database=database['NAME'],expected_host=database['HOST'],
             expected_port=int(database['PORT'] or 5432),reason='Synthetic PostgreSQL logical restore rehearsal.',stdout=StringIO())
assert Session.objects.count()==RateBucket.objects.count()==WorkOSCredential.objects.count()==0
assert WorkOSLoginAttempt.objects.count()==0
assert WorkOSIdentity.objects.get(user_id=fixture['author_id']).subject=='user_synthetic'
capacity=Capacity.objects.get(pk=1)
assert not capacity.intake_open and capacity.revision==fixture['capacity']['revision']+1
assert (capacity.queue_limit,capacity.per_author_limit,capacity.draft_limit)==(fixture['capacity']['queue_limit'],fixture['capacity']['per_author_limit'],fixture['capacity']['draft_limit'])
assert Event.objects.count()==fixture['event_count']+1
recovery=Event.objects.get(kind='restored_paused')
assert recovery.details['scope']=='offline_preparation_only'
assert recovery.actor_id is None
prior_events=[{'id':item.id,'actor_id':item.actor_id,'kind':item.kind,'target':item.target,'details':item.details,'created_at':item.created_at.isoformat()} for item in Event.objects.exclude(pk=recovery.pk).order_by('id')]
assert prior_events==fixture['events'], 'Historical audit records changed during logical restore'
restored_versions=[{'id':item.id,'work_id':str(item.work_id),'number':item.number,'digest':item.digest,'snapshot':item.snapshot,'published_at':item.published_at.isoformat()} for item in Version.objects.order_by('id')]
assert restored_versions==fixture['versions'], 'Publication content, digest, identifiers or history changed during restore'
assert list(Version.objects.filter(work_id=fixture['withdrawn_work_id']).order_by('number').values_list('number',flat=True))==[1,2]
assert Work.objects.get(pk=fixture['withdrawn_work_id']).withdrawn_at is not None
assert Decision.objects.get(submission_id=fixture['declined_id']).reason==fixture['private_decision']
restored_appeal=Appeal.objects.select_related('decision').get(pk=fixture['appeal_id'])
assert restored_appeal.reason==fixture['private_appeal'] and str(restored_appeal.decision.submission_id)==fixture['declined_id']
restored_report=Report.objects.get(pk=fixture['report_id'])
assert restored_report.reason==fixture['private_report'] and str(restored_report.work_id)==fixture['visible_work_id']
User=get_user_model()
restored_accounts=[{'id':user.pk,'username':user.username,'password':user.password,'is_active':user.is_active,
                    'is_staff':user.is_staff,'is_superuser':user.is_superuser,'last_login':user.last_login,
                    'groups':list(user.groups.order_by('name').values_list('name',flat=True))}
                   for user in User.objects.order_by('pk')]
assert restored_accounts==fixture['accounts'], 'Restored account identity, password hash, access state or roles changed'
moderator=User.objects.get(pk=fixture['moderator_id'])
assert services.is_moderator(moderator) and not services.is_moderator(User.objects.get(pk=fixture['author_id']))
pending=Submission.objects.get(pk=fixture['pending_id'])
assert pending.state=='submitted' and pending.frozen_snapshot['title']==fixture['pending_title']
draft=Submission.objects.get(pk=fixture['draft_id'])
assert draft.state=='draft' and draft.revision==1 and draft.title==fixture['private_draft']
reader=Client()
archive=reader.get(reverse('archive'))
assert archive.status_code==200 and b'SYNTHETIC visible restored publication' in archive.content
for key in ('private_draft','pending_title','private_decision','private_appeal','private_report','withdrawn_sentinel'):
    assert fixture[key].encode() not in archive.content
assert list(public_versions().values_list('work_id',flat=True))==[Work.objects.get(pk=fixture['visible_work_id']).pk]
for number in (1,2):
    for route in ('version','export_version'):
        response=reader.get(reverse(route,args=[fixture['withdrawn_work_id'],number]))
        assert response.status_code==200 and fixture['withdrawn_sentinel'].encode() not in response.content
assert reader.get(reverse('export_submission',args=[fixture['draft_id']])).status_code==302
# A copied pre-backup authenticated cookie must no longer grant access.
reader.cookies[settings.SESSION_COOKIE_NAME]=fixture['session_key']
assert reader.get(reverse('export_submission',args=[fixture['draft_id']])).status_code==302
owner=Client()
assert owner.login(username=User.objects.get(pk=fixture['author_id']).username,password=fixture['author_password']), 'A restored contributor could not authenticate with the original password'
assert owner.get(reverse('export_submission',args=[fixture['draft_id']])).json()['research']['title']==fixture['private_draft']
resumed=services.save_submission(User.objects.get(pk=fixture['author_id']),draft.pk,{'methods':'Synthetic draft resumed after logical restore.'},draft.revision)
assert resumed.state=='draft' and resumed.revision==2 and resumed.methods=='Synthetic draft resumed after logical restore.'
owner_export=owner.get(reverse('export_submission',args=[fixture['declined_id']]))
assert fixture['private_decision'].encode() in owner_export.content and fixture['private_appeal'].encode() in owner_export.content
other=Client();other.force_login(User.objects.get(pk=fixture['other_id']))
assert other.get(reverse('export_submission',args=[fixture['draft_id']])).status_code==404
moderation=Client();moderation.force_login(moderator)
assert fixture['pending_title'].encode() in moderation.get(reverse('queue')).content
operations=moderation.get(reverse('operations'))
assert fixture['private_appeal'].encode() in operations.content and fixture['private_report'].encode() in operations.content
call_command('verify_archive',stdout=StringIO())
connections.close_all()
""")
        prepared = subprocess.run([sys.executable,'-c',target_script],env=target_environment,capture_output=True,text=True,timeout=60)
        if prepared.returncode:
            diagnostic=prepared.stderr
            for private in [target_url,*sensitive_values]:
                if private:
                    diagnostic=diagnostic.replace(private,'[redacted]')
            raise AssertionError('Restored target verification failed: '+diagnostic[:3000])
    assert source_state()==before, 'Logical restore or target preparation changed the source database'
    assert Session.objects.filter(session_key=session.session_key).exists()
    assert Event.objects.filter(kind='restored_paused').count()==0
except BaseException:
    failed=True
    raise
finally:
    if created_target:
        try:
            with db.cursor() as cursor:
                cursor.execute('DROP DATABASE '+db.ops.quote_name(target)+' WITH (FORCE)')
        except Exception:
            if not failed:
                raise
''', timeout=240)

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

    def test_live_overlapping_workos_requests_preserve_rotated_session(self):
        self.run_in_disposable_schema('''
from archive.tests.session_overlap_fixture import run_session_overlap
run_session_overlap()
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
for target in ('0004_appeal_decision_binding', '0002_pilot_invariants', '0001_initial', '0004_appeal_decision_binding', '0005_workos_identity_login_attempt','0006_durable_workos_credential'):
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
