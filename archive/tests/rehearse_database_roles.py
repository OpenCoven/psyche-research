"""Synthetic local role rehearsal only; no remote target or provider credentials accepted."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile

import psycopg
from psycopg import sql

if not __debug__:
    raise SystemExit('Role assertions require an interpreter without optimization.')

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--pg-bin', type=Path, required=True, help='Existing trusted PostgreSQL client/server bin directory')
parser.add_argument('--expected-major', type=int, choices=(16, 18), required=True)
parser.add_argument('--source-revision', required=True, help='Exact committed application source SHA to archive')
parser.add_argument('--output', type=Path, required=True, help='New private directory; an existing path is refused')
arguments = parser.parse_args()
BIN = arguments.pg_bin.resolve()
assert all((BIN / name).is_file() and os.access(BIN / name, os.X_OK)
           for name in ('postgres', 'initdb', 'pg_ctl', 'pg_dump', 'pg_restore')), 'Required existing tools missing'
assert re.fullmatch(r'[0-9a-f]{40}', arguments.source_revision), 'An exact committed source SHA is required'
EXPECTED_MAJOR = arguments.expected_major
REPO = Path(__file__).resolve().parents[2]
REVISION = arguments.source_revision
ROOT = arguments.output.resolve()
ROOT.mkdir(mode=0o700, exist_ok=False)
os.chmod(ROOT, 0o700)
DB = 'synthetic_role_contract'
RUNTIME, MIGRATOR, BACKUP = 'psyche_runtime', 'psyche_migrator', 'psyche_backup'
SOCKET = Path(tempfile.mkdtemp(prefix='ps-'))
os.chmod(SOCKET, 0o700)
os.umask(0o077)
# Parent libpq reads the process environment, not the child ENV below.
# Never use the operator's service/password files for this synthetic cluster.
EMPTY_LIBPQ_CONFIG = ROOT / 'empty-libpq-config'
EMPTY_LIBPQ_CONFIG.write_text('')
os.chmod(EMPTY_LIBPQ_CONFIG, 0o600)
for key in tuple(os.environ):
    if key.startswith('PG'):
        del os.environ[key]
os.environ.update(PGPASSFILE=str(EMPTY_LIBPQ_CONFIG), PGSERVICEFILE=str(EMPTY_LIBPQ_CONFIG))
ENV = {key: value for key, value in os.environ.items()
       if key in {'PATH', 'HOME', 'TMPDIR', 'LANG', 'USER', 'LOGNAME', 'TZ'} or key.startswith('LC_')}
ENV.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', LOCAL_DEVELOPMENT='1',
           AUTH_PROVIDER='local', PILOT_APPROVED='0', PGPASSFILE=str(EMPTY_LIBPQ_CONFIG),
           PGSERVICEFILE=str(EMPTY_LIBPQ_CONFIG))
report = {'revision': REVISION, 'synthetic_only': True, 'transport': 'private UNIX socket; no TCP/TLS',
          'provider_acceptance': False, 'checks': [], 'first_failure': None,
          'expected_major': EXPECTED_MAJOR, 'fixture_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def run(arguments, name, env=None):
    result = subprocess.run(arguments, env=env or ENV, cwd=ROOT, text=True, capture_output=True, timeout=90)
    (ROOT / (name + '.log')).write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'{name} exited {result.returncode}; retained synthetic log')
    return result.stdout


def connect(user='synthetic_owner', database=DB):
    assert SOCKET.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve())
    assert database in {'postgres', DB, DB + '_restored'}
    return psycopg.connect(host=str(SOCKET), dbname=database, user=user, autocommit=True)


def schema_grants(database):
    with connect(database=database) as admin:
        admin.execute(sql.SQL('REVOKE ALL ON DATABASE {} FROM PUBLIC').format(sql.Identifier(database)))
        admin.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO psyche_migrator, psyche_runtime, psyche_backup').format(sql.Identifier(database)))
        admin.execute('REVOKE ALL ON SCHEMA public FROM PUBLIC')
        admin.execute('GRANT USAGE, CREATE ON SCHEMA public TO psyche_migrator')
        admin.execute('GRANT USAGE ON SCHEMA public TO psyche_runtime, psyche_backup')
        # Default privileges are database-local; apply before migrations or restore.
        admin.execute('ALTER DEFAULT PRIVILEGES FOR ROLE psyche_migrator REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC')


def check_function_privileges(database):
    """Verify existing and future function ACLs in this exact database."""
    with connect(database=database) as admin:
        owner, public_execute = admin.execute("SELECT pg_get_userbyid(p.proowner), EXISTS (SELECT 1 FROM aclexplode(coalesce(p.proacl,acldefault('f',p.proowner))) a WHERE a.grantee=0 AND a.privilege_type='EXECUTE') FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' AND p.proname='archive_reject_append_only' AND p.pronargs=0").fetchone()
        assert owner == MIGRATOR and public_execute is False, 'Application function retains PUBLIC EXECUTE in ' + database
        for role in (RUNTIME, BACKUP):
            assert admin.execute("SELECT has_function_privilege(%s,'public.archive_reject_append_only()','EXECUTE')", (role,)).fetchone()[0] is False
    report['checks'].append(database + ': migration-owned append-only function denies PUBLIC/runtime/backup execution')
    with connect(MIGRATOR, database) as migration:
        migration.execute("CREATE FUNCTION public.synthetic_function_acl_probe() RETURNS integer LANGUAGE sql AS 'SELECT 1'")
    try:
        for role in (RUNTIME, BACKUP):
            with connect(role, database) as connection:
                try:
                    connection.execute('SELECT public.synthetic_function_acl_probe()')
                except psycopg.errors.InsufficientPrivilege as error:
                    assert error.sqlstate == '42501'
                    report['checks'].append(database + ': ' + role + ' cannot execute a newly created migration function')
                else:
                    raise AssertionError('Future function EXECUTE was not refused: ' + role)
    finally:
        with connect(MIGRATOR, database) as migration:
            migration.execute('DROP FUNCTION public.synthetic_function_acl_probe()')


def data_grants(database):
    with connect(database=database) as admin:
        admin.execute('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO psyche_runtime')
        admin.execute('REVOKE INSERT, UPDATE, DELETE ON django_migrations FROM psyche_runtime')
        admin.execute('REVOKE UPDATE, DELETE ON archive_version, archive_decision, archive_event FROM psyche_runtime')
        admin.execute('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO psyche_runtime')
        admin.execute('GRANT SELECT ON ALL TABLES IN SCHEMA public TO psyche_backup')
        admin.execute('GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO psyche_backup')


def app_env(user, database=DB):
    return {**ENV, 'PYTHONPATH': str(ROOT) + os.pathsep + str(ROOT / 'source'),
            'DJANGO_SETTINGS_MODULE': 'role_settings', 'ROLE_SOCKET': str(SOCKET),
            'ROLE_DATABASE': database, 'ROLE_USER': user}


def denied(user, statement, label):
    with connect(user) as connection:
        try:
            connection.execute(statement)
        except psycopg.errors.InsufficientPrivilege as error:
            assert error.sqlstate == '42501'
            report['checks'].append(label)
        else:
            raise AssertionError('Expected privilege refusal: ' + label)


def database_rows(database):
    """Snapshot every public table through the read-only identity; synthetic data only."""
    with connect(BACKUP, database) as connection:
        tables = connection.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename").fetchall()
        return {name: sorted(row[0] for row in connection.execute(
            sql.SQL('SELECT row_to_json(t)::text FROM public.{} AS t').format(sql.Identifier(name))))
            for (name,) in tables}


start_attempted = False
try:
    assert {key for key in os.environ if key.startswith('PG')} == {'PGPASSFILE', 'PGSERVICEFILE'}
    assert all(os.environ[key] == ENV[key] == str(EMPTY_LIBPQ_CONFIG)
               for key in ('PGPASSFILE', 'PGSERVICEFILE'))
    assert EMPTY_LIBPQ_CONFIG.stat().st_mode & 0o777 == 0o600 and not EMPTY_LIBPQ_CONFIG.read_bytes()
    assert ENV['PYTHONNOUSERSITE'] == '1'
    report['checks'].append('parent and child libpq settings use only a private empty configuration; child user-site imports disabled')
    report['tool_versions'] = {}
    for tool in ('postgres', 'initdb', 'pg_dump', 'pg_restore'):
        actual = run([str(BIN / tool), '--version'], tool + '-version').strip()
        assert re.search(r'\(PostgreSQL\) ' + str(EXPECTED_MAJOR) + r'\.', actual), 'Unexpected client/server major'
        report['tool_versions'][tool] = actual
    run([str(BIN / 'initdb'), '-D', str(ROOT / 'data'), '-U', 'synthetic_owner', '-A', 'trust',
         '--no-locale', '-E', 'UTF8'], 'initdb')
    archive = subprocess.check_output(['git', 'archive', REVISION], cwd=REPO)
    (ROOT / 'source').mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        source.extractall(ROOT / 'source', filter='data')
    report['source_archive_sha256'] = hashlib.sha256(archive).hexdigest()
    from importlib.metadata import version
    pins = re.findall(r'^([A-Za-z0-9_-]+)==([^\s]+)', (ROOT / 'source/requirements.txt').read_text(), re.M)
    assert pins and all(version(name) == expected for name, expected in pins)
    report['installed_pins_matched'] = len(pins)
    (ROOT / 'role_settings.py').write_text('from config.settings import *\n'
        'DATABASES={"default":{"ENGINE":"django.db.backends.postgresql","NAME":os.environ["ROLE_DATABASE"],'
        '"USER":os.environ["ROLE_USER"],"HOST":os.environ["ROLE_SOCKET"],"CONN_MAX_AGE":0,'
        '"OPTIONS":{"sslmode":"disable","connect_timeout":10,"prepare_threshold":None,'
        '"options":"-c statement_timeout=10000 -c lock_timeout=5000"}}}\n')
    start_attempted = True
    run([str(BIN / 'pg_ctl'), '-D', str(ROOT / 'data'), '-l', str(ROOT / 'server.log'),
         '-o', "-h '' -k " + str(SOCKET), '-w', 'start'], 'start')
    with connect(database='postgres') as admin:
        assert admin.info.server_version // 10000 == EXPECTED_MAJOR
        report['server_version'] = admin.info.server_version
        assert admin.execute('SHOW listen_addresses').fetchone()[0] == ''
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(DB)))
        for role in (MIGRATOR, RUNTIME, BACKUP):
            admin.execute(sql.SQL('CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS').format(sql.Identifier(role)))
    schema_grants(DB)
    run([sys.executable, '-B', str(ROOT / 'source/manage.py'), 'migrate', '--noinput'], 'migrate', app_env(MIGRATOR))
    report['checks'].append('migrations succeed with the separate non-owner migration role')
    data_grants(DB)
    check_function_privileges(DB)
    for role in (MIGRATOR, RUNTIME, BACKUP):
        with connect(role) as connection:
            flags = connection.execute('SELECT rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone()
            assert flags == (False, False, False, False, False)
            assert not connection.execute("SELECT pg_has_role(current_user,'synthetic_owner','MEMBER')").fetchone()[0]
            assert connection.execute('SELECT count(*) FROM pg_auth_members WHERE member=(SELECT oid FROM pg_roles WHERE rolname=current_user)').fetchone()[0] == 0
    report['checks'].append('all three roles lack elevated flags and role memberships')
    workflow = '''import django
django.setup()
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sessions.backends.db import SessionStore
from django.utils import timezone
from datetime import timedelta
from archive import services
from archive.models import Capacity, Version, Decision, WorkOSIdentity, WorkOSLoginAttempt, WorkOSCredential
from archive.tests.test_guarantees import content
from django.core.management import call_command
author=get_user_model().objects.create_user('synthetic-author')
moderator=get_user_model().objects.create_user('synthetic-moderator')
moderator.groups.add(Group.objects.get(name='moderators'))
config=Capacity.objects.get(pk=1)
services.configure(moderator,{'intake_open':True},config.revision,'SYNTHETIC local role rehearsal')
row=services.create_submission(author)
row=services.save_submission(author,row.pk,content(),row.revision,submit=True)
services.decide(moderator,row.pk,'publish','SYNTHETIC role rehearsal',row.revision,conflicts='None; synthetic')
version=Version.objects.get(submission=row)
correction=services.create_submission(author,version.work_id)
correction=services.save_submission(author,correction.pk,content(change_note='SYNTHETIC correction'),correction.revision,submit=True)
services.decide(moderator,correction.pk,'publish','SYNTHETIC correction',correction.revision,conflicts='None; synthetic')
services.report(version.work_id,'SYNTHETIC report')
services.withdraw(author,version.work_id,'SYNTHETIC withdrawal')
draft=services.create_submission(author)
session=SessionStore();session['_auth_user_id']=str(author.pk);session.save()
identity=WorkOSIdentity.objects.create(user=author,client_id='client_synthetic',subject='user_synthetic')
credential=WorkOSCredential.objects.create(session_id=session.session_key,identity=identity,sealed='SYNTHETIC inert sealed text',provider_session_id='session_synthetic',expires_at=timezone.now()+timedelta(hours=1))
credential.claimed_at=timezone.now();credential.save(update_fields=['claimed_at'])
WorkOSLoginAttempt.objects.create(state_hash='synthetic-state',browser_hash='synthetic-browser',verifier='synthetic-verifier',expires_at=timezone.now()+timedelta(minutes=5))
config.refresh_from_db();services.configure(moderator,{'intake_open':False},config.revision,'SYNTHETIC complete')
assert Version.objects.count()==2 and Decision.objects.count()==2 and not Capacity.objects.get(pk=1).intake_open
call_command('verify_archive')
print('SYNTHETIC runtime role workflow passed; two exact versions, withdrawal, private draft, session and WorkOS credential/attempt records; intake paused')
'''
    (ROOT / 'workflow.py').write_text(workflow)
    run([sys.executable, '-B', str(ROOT / 'workflow.py')], 'runtime-workflow', app_env(RUNTIME))
    report['checks'].append('restricted runtime publication/correction/withdrawal/private/session/credential workflow and verifier')
    for statement, label in (
        ('CREATE TABLE public.synthetic_forbidden(id integer)', 'runtime cannot create tables'),
        ('CREATE SCHEMA synthetic_forbidden', 'runtime cannot create schemas'),
        ('CREATE ROLE synthetic_forbidden', 'runtime cannot create roles'),
        ('CREATE DATABASE synthetic_forbidden', 'runtime cannot create databases'),
        ('SET ROLE psyche_migrator', 'runtime cannot assume migration role'),
        ('ALTER TABLE archive_submission ADD COLUMN synthetic_forbidden integer', 'runtime cannot alter tables'),
        ('TRUNCATE archive_submission', 'runtime cannot truncate mutable application tables'),
        ("UPDATE django_migrations SET app=app", 'runtime cannot rewrite migration history'),
        ("UPDATE archive_version SET digest=digest", 'runtime cannot update immutable versions'),
        ('DELETE FROM archive_decision', 'runtime cannot delete immutable decisions'),
    ):
        denied(RUNTIME, statement, label)
    for statement, label in (
        ('DELETE FROM archive_submission', 'backup cannot delete application rows'),
        ("UPDATE archive_submission SET title=title", 'backup cannot update application rows'),
        ('TRUNCATE archive_submission', 'backup cannot truncate application tables'),
        ('CREATE TABLE public.synthetic_backup_forbidden(id integer)', 'backup cannot create tables'),
        ('SET ROLE psyche_migrator', 'backup cannot assume migration role'),
    ):
        denied(BACKUP, statement, label)
    snapshot = ROOT / 'synthetic.dump'
    run([str(BIN / 'pg_dump'), '-h', str(SOCKET), '-U', BACKUP, '-d', DB, '-Fc', '--no-owner', '--no-acl', '-f', str(snapshot)], 'backup-dump')
    assert snapshot.stat().st_mode & 0o777 == 0o600
    report['checks'].append('separate read-only backup role creates mode-0600 custom dump')
    with connect(database='postgres') as admin:
        admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(DB + '_restored')))
    schema_grants(DB + '_restored')
    run([str(BIN / 'pg_restore'), '-h', str(SOCKET), '-U', MIGRATOR, '-d', DB + '_restored', '--no-owner', '--no-acl', '--exit-on-error', '--single-transaction', str(snapshot)], 'restore-as-migrator')
    data_grants(DB + '_restored')
    check_function_privileges(DB + '_restored')
    run([sys.executable, '-B', str(ROOT / 'source/manage.py'), 'verify_archive'], 'restored-runtime-verifier', app_env(RUNTIME, DB + '_restored'))
    for database in (DB, DB + '_restored'):
        with connect(BACKUP, database) as connection:
            assert connection.execute('SELECT count(*) FROM archive_version').fetchone()[0] == 2
            assert connection.execute('SELECT intake_open FROM archive_capacity WHERE id=1').fetchone()[0] is False
    report['checks'].append('migration-role restore into a new database and runtime-role archive verifier pass')
    source_rows = database_rows(DB)
    restored_database = DB + '_restored'
    # Seed only this disposable restore target with an open-intake/active-rate snapshot.
    # Source stays paused, and the fixture never accepts a serving database URL.
    with connect(RUNTIME, restored_database) as connection:
        connection.execute('UPDATE archive_capacity SET intake_open=true WHERE id=1')
        connection.execute("INSERT INTO archive_ratebucket(key,count,expires_at) VALUES ('synthetic-recovery-rate',1,now()+interval '1 hour')")
    restored_before = database_rows(restored_database)
    assert all(len(restored_before[name]) == 1 for name in (
        'django_session', 'archive_workoscredential', 'archive_workosloginattempt', 'archive_ratebucket'))
    recovery_env = {**app_env(RUNTIME, restored_database), 'RECOVERY_MODE': 'isolated-restore'}
    recovery_arguments = [sys.executable, '-B', str(ROOT / 'source/manage.py'), 'prepare_restored_archive',
                          '--expected-host', str(SOCKET), '--expected-port', '5432',
                          '--expected-database', restored_database,
                          '--reason', 'SYNTHETIC restricted-role offline preparation']
    wrong_target_arguments = recovery_arguments.copy()
    wrong_target_arguments[wrong_target_arguments.index('--expected-database') + 1] = DB
    refused = subprocess.run(wrong_target_arguments, env=recovery_env, cwd=ROOT,
                             text=True, capture_output=True, timeout=90)
    (ROOT / 'wrong-restore-target.log').write_text(refused.stdout + refused.stderr)
    assert refused.returncode == 1 and 'does not match the explicitly expected isolated target' in refused.stderr
    assert database_rows(restored_database) == restored_before
    report['checks'].append('runtime-role restore preparation refuses wrong target without changing any public table')
    run(recovery_arguments, 'restricted-offline-preparation', recovery_env)
    restored_after = database_rows(restored_database)
    expected_changes = {'django_session', 'archive_workoscredential', 'archive_workosloginattempt',
                        'archive_ratebucket', 'archive_capacity', 'archive_event'}
    assert set(restored_after) == set(restored_before)
    assert all(restored_after[name] == restored_before[name] for name in restored_before if name not in expected_changes)
    assert all(restored_after[name] == [] for name in expected_changes - {'archive_capacity', 'archive_event'})
    prior_capacity, capacity = (json.loads(rows['archive_capacity'][0]) for rows in (restored_before, restored_after))
    assert prior_capacity['intake_open'] is True and capacity['intake_open'] is False
    assert capacity['revision'] == prior_capacity['revision'] + 1
    assert {key: value for key, value in capacity.items() if key not in {'intake_open', 'revision', 'updated_at'}} == {
        key: value for key, value in prior_capacity.items() if key not in {'intake_open', 'revision', 'updated_at'}}
    new_events = set(restored_after['archive_event']) - set(restored_before['archive_event'])
    assert len(new_events) == 1 and set(restored_before['archive_event']).issubset(restored_after['archive_event'])
    event = json.loads(new_events.pop())
    assert event['kind'] == 'restored_paused' and event['actor_id'] is None
    assert event['details'] == {'reason': 'SYNTHETIC restricted-role offline preparation', 'scope': 'offline_preparation_only'}
    assert database_rows(DB) == source_rows, 'Source rows changed during isolated restore preparation'
    run([sys.executable, '-B', str(ROOT / 'source/manage.py'), 'verify_archive'],
        'prepared-runtime-verifier', app_env(RUNTIME, restored_database))
    report['checks'].append('restricted runtime offline preparation revokes restored sessions/credentials/attempts/rates, pauses intake and appends one audit event; all other restored and source rows unchanged')
    report['dump_sha256'] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    report['status'] = 'passed'
except BaseException as error:
    report['status'] = 'failed'
    report['first_failure'] = type(error).__name__ + ': ' + str(error)
    raise
finally:
    if start_attempted:
        # A failed/timed-out start command can still leave its server running.
        # Inspect only this freshly allocated cluster, never an unrelated PID.
        try:
            status = subprocess.run([str(BIN / 'pg_ctl'), '-D', str(ROOT / 'data'), 'status'],
                                    env=ENV, text=True, capture_output=True, timeout=10)
            if status.returncode == 0:
                run([str(BIN / 'pg_ctl'), '-D', str(ROOT / 'data'), '-m', 'fast', '-w', 'stop'], 'stop')
            after = subprocess.run([str(BIN / 'pg_ctl'), '-D', str(ROOT / 'data'), 'status'],
                                   env=ENV, text=True, capture_output=True, timeout=10)
            report['server_stopped'] = after.returncode == 3 and not (ROOT / 'data/postmaster.pid').exists()
            report['final_server_status_exit'] = after.returncode
        except Exception:
            report['server_stopped'] = False
    if report.get('server_stopped') is False:
        report['status'] = 'failed'
        if report['first_failure'] is None:
            report['first_failure'] = 'RuntimeError: Owned temporary server cleanup was not verified'
    (ROOT / 'role-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    if report.get('server_stopped') is False:
        raise RuntimeError('Owned temporary server cleanup was not verified; inspect retained report')
