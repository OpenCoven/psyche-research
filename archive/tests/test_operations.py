"""Fresh-file migration and recovery drill; all records are labeled synthetic fixtures."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from django.test import SimpleTestCase

ROOT=Path(__file__).resolve().parents[2]

class OperationalDrill(SimpleTestCase):
    def test_refresh_claim_commits_before_exchange_and_survives_view_rollback(self):
        with tempfile.TemporaryDirectory(prefix='psyche-refresh-durable-') as directory:
            env = {**os.environ, 'LOCAL_DEVELOPMENT': '1', 'DJANGO_SETTINGS_MODULE': 'config.settings',
                   'DATABASE_PATH': str(Path(directory) / 'synthetic.sqlite3')}
            env.pop('DATABASE_URL', None)
            self.run_python('''
import django
django.setup()
from django.core.management import call_command
call_command('migrate', verbosity=0)
from archive.tests.session_overlap_fixture import run_durable_refresh_boundary
run_durable_refresh_boundary()
''', env)

    def test_workos_callback_consumption_commits_before_provider_exchange(self):
        with tempfile.TemporaryDirectory(prefix='psyche-callback-commit-') as directory:
            env = {**os.environ, 'LOCAL_DEVELOPMENT': '1', 'DJANGO_SETTINGS_MODULE': 'config.settings',
                   'DATABASE_PATH': str(Path(directory) / 'synthetic.sqlite3')}
            env.pop('DATABASE_URL', None)
            self.run_python('''
import django
django.setup()
from django.core.management import call_command
call_command('migrate', verbosity=0)
from archive.tests.session_overlap_fixture import run_callback_commit_boundary
run_callback_commit_boundary()
print('Callback state was durably consumed before provider exchange')
''', env)

    def test_overlapping_workos_requests_preserve_rotated_session_in_real_file_database(self):
        with tempfile.TemporaryDirectory(prefix='psyche-session-race-') as directory:
            env = {**os.environ, 'LOCAL_DEVELOPMENT': '1', 'DJANGO_SETTINGS_MODULE': 'config.settings',
                   'DATABASE_PATH': str(Path(directory) / 'synthetic.sqlite3')}
            env.pop('DATABASE_URL', None)
            self.run_python('''
import django
django.setup()
from django.core.management import call_command
call_command('migrate', verbosity=0)
from archive.tests.session_overlap_fixture import run_session_overlap
run_session_overlap()
print('Concurrent session rotation preserved one-use refresh and authenticated access')
''', env)

    def run_python(self,script,env):
        result=subprocess.run([sys.executable,'-c',script],cwd=ROOT,env=env,text=True,capture_output=True,timeout=90)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)
        return result.stdout

    def test_fresh_migrations_representative_restore_and_corruption_refusal(self):
        with tempfile.TemporaryDirectory(prefix='coven-research-drill-') as directory:
            env={**os.environ,'LOCAL_DEVELOPMENT':'1','DJANGO_SETTINGS_MODULE':'config.settings',
                 'DATABASE_PATH':str(Path(directory)/'source.sqlite3'),'DRILL_DIRECTORY':directory}
            self.run_python(r'''
import os,stat,sqlite3,hashlib
from pathlib import Path
import django
django.setup()
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sessions.backends.db import SessionStore
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from archive import services
from archive.models import Capacity,Submission,Version,Event,Appeal,Report,RateBucket,WorkOSIdentity,WorkOSLoginAttempt,WorkOSCredential
from archive.recovery import copy_database,verify,REQUIRED_TRIGGERS
from archive.tests.test_guarantees import content
from django.utils import timezone
call_command('migrate',verbosity=0)
# Exercise real backwards/forwards schema operations before data and require every trigger each time.
for target in ('0002_pilot_invariants','0004_appeal_decision_binding','0005_workos_identity_login_attempt','0006_durable_workos_credential'):
 call_command('migrate','archive',target,verbosity=0)
 with connection.cursor() as c:
  c.execute("SELECT name FROM sqlite_master WHERE type='trigger'")
  assert REQUIRED_TRIGGERS=={x[0] for x in c.fetchall()}
User=get_user_model()
a=User.objects.create_user('synthetic-drill-author',password='synthetic-only-password-123')
m=User.objects.create_user('synthetic-drill-moderator',password='synthetic-only-password-456')
m.groups.add(Group.objects.get(name='moderators'))
c=Capacity.objects.get(pk=1);c.intake_open=True;c.save()
s=services.create_submission(a)
s=services.save_submission(a,s.pk,content(title='SYNTHETIC v1 withdrawal sentinel'),0,submit=True)
services.decide(m,s.pk,'publish','Synthetic complete only',s.revision,conflicts='None; synthetic fixture')
s.refresh_from_db();work=s.work
r=services.create_submission(a,work.pk)
r=services.save_submission(a,r.pk,content(title='SYNTHETIC v2 withdrawal sentinel',change_note='Synthetic correction'),0,submit=True)
services.decide(m,r.pk,'publish','Synthetic complete only',r.revision,conflicts='None; synthetic fixture')
services.withdraw(a,work.pk,'Synthetic withdrawal reason')
p=services.create_submission(a)
p=services.save_submission(a,p.pk,content(title='SYNTHETIC still public'),0,submit=True)
services.decide(m,p.pk,'publish','Synthetic complete only',p.revision,conflicts='None; synthetic fixture')
p.refresh_from_db()
report=services.report(p.work_id,'SYNTHETIC confidential report sentinel')
d=services.create_submission(a)
d=services.save_submission(a,d.pk,content(title='SYNTHETIC private appeal sentinel'),0,submit=True)
services.decide(m,d.pk,'decline','SYNTHETIC private decision sentinel',d.revision,conflicts='None; synthetic fixture')
services.appeal(a,d.pk,'SYNTHETIC private appeal reason')
private=services.create_submission(a)
services.save_submission(a,private.pk,content(title='SYNTHETIC unfinished private sentinel'),0)
session=SessionStore();session['synthetic']='private';session.save()
RateBucket.objects.create(key='synthetic-drill',expires_at=timezone.now())
identity=WorkOSIdentity.objects.create(user=a,client_id='client_synthetic',subject='user_synthetic')
WorkOSCredential.objects.create(session_id=session.session_key,identity=identity,sealed='synthetic-sealed-only',provider_session_id='session_synthetic',expires_at=timezone.now())
WorkOSLoginAttempt.objects.create(state_hash='synthetic-state',browser_hash='synthetic-browser',verifier='synthetic-verifier',expires_at=timezone.now())
base=Path(os.environ['DRILL_DIRECTORY']);source=Path(os.environ['DATABASE_PATH']);backup=base/'backup.sqlite3';restore=base/'restored.sqlite3'
before=list(Version.objects.order_by('id').values_list('digest',flat=True))
backup_hash=copy_database(source,backup)
assert backup_hash==hashlib.sha256(backup.read_bytes()).hexdigest()
restored_hash=copy_database(backup,restore,restore=True)
assert restored_hash==hashlib.sha256(restore.read_bytes()).hexdigest()
assert stat.S_IMODE(backup.stat().st_mode)==stat.S_IMODE(restore.stat().st_mode)==0o600
with sqlite3.connect(restore) as db:
 verify(db)
 assert db.execute('SELECT count(*) FROM django_session').fetchone()[0]==0
 assert db.execute('SELECT count(*) FROM archive_workoscredential').fetchone()[0]==0
 assert db.execute('SELECT count(*) FROM archive_ratebucket').fetchone()[0]==0
 assert db.execute('SELECT count(*) FROM archive_workosloginattempt').fetchone()[0]==0
 assert db.execute('SELECT subject FROM archive_workosidentity').fetchone()[0]=='user_synthetic'
 assert db.execute('SELECT intake_open FROM archive_capacity').fetchone()[0]==0
 assert db.execute('SELECT count(*) FROM archive_appeal').fetchone()[0]==1
 assert db.execute('SELECT count(*) FROM archive_report').fetchone()[0]==1
 assert db.execute('SELECT count(*) FROM archive_decision').fetchone()[0]==4
 assert [x[0] for x in db.execute('SELECT digest FROM archive_version ORDER BY id')]==before
 assert db.execute("SELECT count(*) FROM archive_event WHERE kind='restored_paused'").fetchone()[0]==1
# Restore must reject existing files and dangling symlinks without changing them.
existing=base/'existing';existing.write_bytes(b'keep')
link=base/'dangling';missing=base/'never-create';link.symlink_to(missing)
for dest in (existing,link):
 try: copy_database(source,dest)
 except FileExistsError: pass
 else: raise AssertionError('Existing destination accepted')
assert existing.read_bytes()==b'keep' and link.is_symlink() and not missing.exists()
# A malicious/incomplete snapshot must not pass current-schema or append-only verification.
for name,damage in [('missing-table','DROP TABLE archive_report'),('missing-auth-junction','DROP TABLE auth_user_groups'),('disabled-trigger',"DROP TRIGGER archive_version_no_update")]:
 corrupt=base/(name+'.sqlite3')
 with sqlite3.connect(backup) as origin,sqlite3.connect(corrupt) as target:
  origin.backup(target);target.execute(damage)
  if name=='disabled-trigger': target.execute("CREATE TRIGGER archive_version_no_update BEFORE UPDATE ON archive_version WHEN 0 BEGIN SELECT RAISE(ABORT, 'append-only record'); END")
 try: copy_database(corrupt,base/(name+'-output.sqlite3'),restore=True)
 except ValueError: pass
 else: raise AssertionError('Corrupt schema accepted: '+name)
 assert not (base/(name+'-output.sqlite3')).exists()
print('representative backup/restore and schema refusal passed')
''',env)
            restored_env={**env,'DATABASE_PATH':str(Path(directory)/'restored.sqlite3')}
            self.run_python(r'''
import django
django.setup()
from django.test import Client
from archive.models import Work,Version,Submission,Capacity
from django.contrib.auth import get_user_model
from django.urls import reverse
c=Client()
assert b'SYNTHETIC still public' in c.get('/archive/').content
for marker in (b'SYNTHETIC private',b'SYNTHETIC unfinished',b'withdrawal sentinel',b'confidential report'):
 assert marker not in c.get('/archive/').content
for work in Work.objects.filter(withdrawn_at__isnull=False):
 for version in work.versions.all():
  html=c.get(reverse('version',args=[work.pk,version.number]));meta=c.get(reverse('export_version',args=[work.pk,version.number]))
  assert html.status_code==meta.status_code==200 and b'withdrawal sentinel' not in html.content+meta.content
private=Submission.objects.get(title='SYNTHETIC unfinished private sentinel')
assert c.get(reverse('export_submission',args=[private.pk])).status_code==302
c.force_login(get_user_model().objects.get(username='synthetic-drill-author'))
assert c.get(reverse('export_submission',args=[private.pk])).json()['research']['title']==private.title
assert not Capacity.objects.get(pk=1).intake_open
print('restored private/public/correction/withdrawal boundaries passed')
''',restored_env)

    def test_upgrade_with_existing_published_record_preserves_content_and_triggers(self):
        with tempfile.TemporaryDirectory(prefix='coven-research-upgrade-') as directory:
            env={**os.environ,'LOCAL_DEVELOPMENT':'1','DJANGO_SETTINGS_MODULE':'config.settings','DATABASE_PATH':str(Path(directory)/'upgrade.sqlite3')}
            self.run_python(r'''
import django,hashlib,json
django.setup()
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from archive.recovery import REQUIRED_TRIGGERS,verify
call_command('migrate',verbosity=0)
call_command('migrate','archive','0002_pilot_invariants',verbosity=0)
old=MigrationExecutor(connection).loader.project_state([('archive','0002_pilot_invariants')]).apps
User=old.get_model('auth','User');user=User.objects.create(username='synthetic-upgrade')
Work=old.get_model('archive','Work');work=Work.objects.create(author_id=user.pk)
Submission=old.get_model('archive','Submission');sub=Submission.objects.create(author_id=user.pk,work_id=work.pk,state='published')
snapshot={'title':'SYNTHETIC preserved upgrade'}
digest=hashlib.sha256(json.dumps(snapshot,sort_keys=True,separators=(',',':')).encode()).hexdigest()
old.get_model('archive','Version').objects.create(work_id=work.pk,submission_id=sub.pk,number=1,snapshot=snapshot,digest=digest)
old.get_model('archive','Decision').objects.create(submission_id=sub.pk,actor_id=user.pk,revision=0,digest=digest,action='publish',reason='Synthetic historical decision')
for target in ('0004_appeal_decision_binding','0002_pilot_invariants','0004_appeal_decision_binding','0005_workos_identity_login_attempt','0006_durable_workos_credential'):
 call_command('migrate','archive',target,verbosity=0)
 with connection.cursor() as c:
  c.execute("SELECT name FROM sqlite_master WHERE type='trigger'");assert REQUIRED_TRIGGERS=={x[0] for x in c.fetchall()}
from archive.models import Version,Decision
assert Version.objects.get().snapshot==snapshot and Version.objects.get().digest==digest
assert Decision.objects.get().conflicts=='Not recorded for this legacy decision'
verify(connection.connection)
print('existing publication survived forward/reverse/reapply with all triggers')
''',env)

    def test_production_settings_fail_closed_and_pass_deployment_checks(self):
        env={**os.environ,'LOCAL_DEVELOPMENT':'0','DJANGO_SECRET_KEY':'','DJANGO_ALLOWED_HOSTS':''}
        bad=subprocess.run([sys.executable,'manage.py','check'],cwd=ROOT,env=env,capture_output=True,text=True)
        self.assertNotEqual(bad.returncode,0)
        env.update(DJANGO_SECRET_KEY='local-development-only-never-a-deployment-key-coven-research',DJANGO_ALLOWED_HOSTS='research.example.invalid')
        known=subprocess.run([sys.executable,'manage.py','check'],cwd=ROOT,env=env,capture_output=True,text=True)
        self.assertNotEqual(known.returncode,0)
        import secrets
        env['DJANGO_SECRET_KEY']=secrets.token_urlsafe(64)
        valid=subprocess.run([sys.executable,'manage.py','check','--deploy','--fail-level','WARNING'],cwd=ROOT,env=env,capture_output=True,text=True)
        self.assertEqual(valid.returncode,0,valid.stdout+valid.stderr)
        env['DJANGO_ALLOWED_HOSTS']='*'
        wildcard=subprocess.run([sys.executable,'manage.py','check'],cwd=ROOT,env=env,capture_output=True,text=True)
        self.assertNotEqual(wildcard.returncode,0)
