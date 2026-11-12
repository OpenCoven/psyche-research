import argparse, getpass, json, os, pathlib, socket, subprocess, sys, tempfile
parser=argparse.ArgumentParser(description='Disposable local PostgreSQL waitlist and purpose-role qualification; never a hosted DSN.')
parser.add_argument('--pg-bin',required=True)
parser.add_argument('--receipt',required=True)
args=parser.parse_args()
root=pathlib.Path(__file__).resolve().parents[2]
os.chdir(root)
pg=pathlib.Path(args.pg_bin).resolve()
work=pathlib.Path(tempfile.mkdtemp(prefix='psyche-waitlist-pg-'))
base={'PATH':os.environ['PATH'],'HOME':os.environ['HOME'],'LC_ALL':'C','LOCAL_DEVELOPMENT':'1'}
report={'work':str(work),'steps':[],'server_stopped':False}
def run(args, env=None, input=None):
 p=subprocess.run([str(a) for a in args],input=input,capture_output=True,text=True,env=env or base,timeout=180)
 if p.returncode: raise RuntimeError('command failed: '+str(args[:2])+'\n'+p.stdout[-6000:]+'\n'+p.stderr[-6000:])
 return p.stdout + p.stderr
with socket.socket() as sock:
 sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
data=work/'data'
started=False
try:
 report['version']=run([pg/'postgres','--version']).strip()
 run([pg/'initdb','-D',data,'--auth-local=trust','--auth-host=trust','--no-locale','-E','UTF8'])
 run([pg/'pg_ctl','-D',data,'-l',work/'server.log','-o',f'-h 127.0.0.1 -p {port} -k {work}','-w','start']);started=True
 owner=f'postgresql://{getpass.getuser()}@127.0.0.1:{port}/postgres?sslmode=disable'
 sql="""CREATE ROLE psyche_waitlist_migrator LOGIN; CREATE ROLE psyche_waitlist_runtime LOGIN; CREATE ROLE psyche_waitlist_operator LOGIN;
 CREATE DATABASE psyche_waitlist_20261111 OWNER psyche_waitlist_migrator;"""
 run([pg/'psql','-X','-v','ON_ERROR_STOP=1','-d',owner],input=sql)
 def uri(role):return f'postgresql://psyche_waitlist_{role}@127.0.0.1:{port}/psyche_waitlist_20261111?sslmode=disable'
 env=base|{'DATABASE_URL':uri('migrator'),'DJANGO_SETTINGS_MODULE':'config.waitlist_settings','WAITLIST_COLLECTION_ENABLED':'1'}
 run([root/'.venv/bin/python','manage.py','migrate','--noinput'],env=env)
 run([pg/'psql','-X','-v','ON_ERROR_STOP=1','-d',owner.replace('/postgres?','/psyche_waitlist_20261111?')],input=(root/'deploy/waitlist_grants.sql.in').read_text())
 report['steps'].append('migrate_and_grants')
 # Full isolated suite on real PostgreSQL using the disposable owner (Django creates its own test DB).
 test_env=env|{'DATABASE_URL':owner.replace('/postgres?','/psyche_waitlist_20261111?')}
 report['suite']=run([root/'.venv/bin/python','manage.py','test','waitlist.tests','--verbosity','1'],env=test_env)
 code='''import os; os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.waitlist_settings")
import django;django.setup()
import concurrent.futures,json
from django.db import connections
from waitlist.models import CollectionState,Registration
from waitlist.services import register
CollectionState.objects.filter(pk=1).update(paused=False)
def submit(i):
 try:return register({'email':'race@example.net','name':'Synthetic','interest':'reader','website':''})
 finally:connections.close_all()
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:r=list(pool.map(submit,range(12)))
assert r.count('accepted')==3 and r.count('limited')==9,r
assert Registration.objects.filter(email='race@example.net').count()==1
assert CollectionState.objects.get().retained_count==1
print(json.dumps({'concurrent_duplicate_results':{v:r.count(v) for v in set(r)}}))
'''
 report['concurrency']=run([root/'.venv/bin/python','-c',code],env=env)
 capacity_code=code.replace("'race@example.net'", "f'unique-{i}@example.net'").replace("CollectionState.objects.filter(pk=1).update(paused=False)","from django.conf import settings; settings.WAITLIST_CAPACITY=2").replace("assert r.count('accepted')==3 and r.count('limited')==9,r","assert r.count('accepted')==1 and r.count('paused')==11,r").replace("assert Registration.objects.filter(email=f'unique-{i}@example.net').count()==1", "assert Registration.objects.count()==2").replace("assert CollectionState.objects.get().retained_count==1", "assert CollectionState.objects.get().retained_count==2")
 report['capacity_concurrency']=run([root/'.venv/bin/python','-c',capacity_code],env=env)
 # Use real runtime credentials via connection role, not merely application flags.
 runtime_code='''import os;os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.waitlist_settings")
import django;django.setup()
from waitlist.services import register
assert register({'email':'runtime@example.net','name':'Synthetic','interest':'both','website':''})=='accepted'
print('restricted_runtime_registration_passed')
'''
 report['runtime_insert']=run([root/'.venv/bin/python','-c',runtime_code],env=env|{'DATABASE_URL':uri('runtime')})
 import psycopg
 denials=[]
 with psycopg.connect(uri('runtime'),autocommit=True) as c:
  for sql in ['SELECT name FROM waitlist_registration','SELECT interest FROM waitlist_registration','DELETE FROM waitlist_registration',
              'UPDATE waitlist_collectionstate SET paused=false','SELECT * FROM waitlist_erasure','CREATE TABLE public.evil(id int)',
              'TRUNCATE waitlist_registration','SET ROLE psyche_waitlist_operator','SELECT * FROM django_migrations']:
   try:c.execute(sql)
   except psycopg.errors.InsufficientPrivilege:denials.append(sql.split()[0])
   else:raise AssertionError('runtime privilege unexpectedly allowed '+sql)
 report['runtime_denials']=len(denials)
 with psycopg.connect(uri('operator'),autocommit=True) as c:
  assert c.execute('SELECT count(*) FROM waitlist_registration').fetchone()[0]==3
  c.execute('UPDATE waitlist_collectionstate SET paused=true WHERE id=1')
 report['steps'].append('operator_read_and_pause')
 op_env=env|{'DATABASE_URL':uri('operator'),'WAITLIST_OPERATOR_MODE':'1'}
 operator_dir=work/'operator';operator_dir.mkdir(mode=0o700)
 ledger=operator_dir/'erasures.jsonl';ledger.touch(mode=0o600)
 address=operator_dir/'address.txt';address.write_text('runtime@example.net');address.chmod(0o600)
 for action,extra in [('export',['--output',str(operator_dir/'export.json')]),('delete',['--email-file',str(address)]),('purge',[]),('reconcile',[])]:
  report['steps'].append('actual_operator_'+action)
  run([root/'.venv/bin/python','manage.py','waitlist_ops',action,'--ledger',ledger,*extra],env=op_env)
 with psycopg.connect(uri('operator'),autocommit=True) as c:
  assert c.execute('SELECT count(*) FROM waitlist_registration').fetchone()[0]==2
 report['operator_workflow']='export_delete_purge_reconcile_passed'

 report['pause_probe']=run([root/'.venv/bin/python','-c',runtime_code.replace("=='accepted'","=='paused'")],env=env|{'DATABASE_URL':uri('runtime')})
 # Actual database outage, no simulated exception.
 run([pg/'pg_ctl','-D',data,'-m','fast','-w','stop'])
 outage='''import os;os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.waitlist_settings")
import django;django.setup()
from django.test import Client
from urllib.parse import urlencode
r=Client().post('/',urlencode({'email':'outage@example.invalid','interest':'reader','consent':'on'}),content_type='application/x-www-form-urlencoded')
assert r.status_code==503,r.status_code
assert b'outage@example.invalid' not in r.content
print('actual_database_outage_safe_503')
'''
 report['database_outage']=run([root/'.venv/bin/python','-c',outage],env=env|{'DATABASE_URL':uri('runtime')})
 report['ok']=True
except BaseException as e:
 report['first_failure']=str(e); report['ok']=False
finally:
 stop=subprocess.run([str(pg/'pg_ctl'),'-D',str(data),'-m','fast','-w','stop'],capture_output=True,text=True,env=base,timeout=30)
 status=subprocess.run([str(pg/'pg_ctl'),'-D',str(data),'status'],capture_output=True,text=True,env=base)
 report['server_stopped']=status.returncode==3 and not (data/'postmaster.pid').exists()
 pathlib.Path(args.receipt).write_text(json.dumps(report,indent=2))
 print(json.dumps(report,indent=2))
 sys.exit(0 if report.get('ok') and report['server_stopped'] else 1)
