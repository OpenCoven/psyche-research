import json
import os
import tempfile
from pathlib import Path
from unittest import skipIf
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from config import database
from config.database import (STARTUP_TIMEOUTS, SESSION_TIMEOUTS_SQL, postgres_config, session_timeouts_within_bounds,
    timeouts_pinned_at_startup, verify_session_timeouts)

VERIFY_FULL_URL='postgres://user:password@db.example/test?sslmode=verify-full'

class RootCertificateResolution(SimpleTestCase):
    """verify-full must find trusted roots on Vercel without a PGSSLROOTCERT override."""
    def setUp(self):
        directory=tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root=Path(directory.name)
        self.environment=patch.dict(os.environ)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        os.environ.pop('PGSSLROOTCERT',None)

    def bundle(self,name):
        path=self.root/name
        path.write_text('synthetic CA bundle placeholder\n')
        return str(path)

    def resolve(self,*candidates,url=VERIFY_FULL_URL,local=False):
        with patch.object(database,'CA_BUNDLES',tuple(str(path) for path in candidates)):
            return postgres_config(url,local=local)['OPTIONS']

    def test_default_candidates_are_the_reviewed_os_bundles_in_order(self):
        self.assertEqual(database.CA_BUNDLES,('/etc/pki/tls/certs/ca-bundle.crt',
            '/etc/ssl/certs/ca-certificates.crt','/etc/ssl/cert.pem'))

    def test_unset_override_uses_first_existing_regular_file_and_keeps_verify_full(self):
        (self.root/'directory').mkdir()
        (self.root/'dangling').symlink_to(self.root/'absent')
        target=self.bundle('tls-ca-bundle.pem')
        # Amazon Linux publishes ca-bundle.crt as a symlink to the extracted bundle.
        (self.root/'linked').symlink_to(target)
        later=self.bundle('later.pem')
        options=self.resolve(self.root/'missing',self.root/'directory',self.root/'dangling',self.root/'linked',later)
        self.assertEqual(options['sslrootcert'],str(self.root/'linked'))
        self.assertEqual(options['sslmode'],'verify-full')
        self.assertEqual(self.resolve(self.root/'missing',later)['sslrootcert'],later)

    @skipIf(hasattr(os,'geteuid') and os.geteuid()==0,'root can read files regardless of mode')
    def test_unreadable_bundle_is_skipped(self):
        unreadable=self.bundle('unreadable.pem')
        os.chmod(unreadable,0)
        self.addCleanup(os.chmod,unreadable,0o600)
        readable=self.bundle('readable.pem')
        self.assertEqual(self.resolve(unreadable,readable)['sslrootcert'],readable)

    def test_explicit_override_wins_and_empty_override_is_unset(self):
        first=self.bundle('first.pem')
        os.environ['PGSSLROOTCERT']='/approved/provider-ca.pem'
        self.assertEqual(self.resolve(first)['sslrootcert'],'/approved/provider-ca.pem')
        os.environ['PGSSLROOTCERT']='system'
        self.assertEqual(self.resolve(first)['sslrootcert'],'system')
        os.environ['PGSSLROOTCERT']=''
        self.assertEqual(self.resolve(first)['sslrootcert'],first)

    def test_no_bundle_falls_back_to_libpq_system_store(self):
        (self.root/'directory').mkdir()
        options=self.resolve(self.root/'missing',self.root/'directory')
        self.assertEqual(options['sslrootcert'],'system')
        self.assertEqual(options['sslmode'],'verify-full')

    def test_local_non_verifying_modes_do_not_gain_a_root_setting(self):
        first=self.bundle('first.pem')
        for mode in ['disable','require']:
            with self.subTest(mode=mode):
                options=self.resolve(first,url=f'postgres://u:p@127.0.0.1/test_only?sslmode={mode}',local=True)
                self.assertEqual(options['sslmode'],mode)
                self.assertNotIn('sslrootcert',options)
        with self.assertRaises(ImproperlyConfigured):
            self.resolve(first,url='postgres://u:p@db.example/test?sslmode=require')

class FakeCursor:
    def __init__(self,connection):
        self.connection=connection
    def __enter__(self):
        return self
    def __exit__(self,*exc):
        return False
    def execute(self,sql):
        self.connection.executed.append(sql)
        if self.connection.error:
            raise self.connection.error
    def fetchall(self):
        return list(self.connection.rows)

class FakeConnection:
    def __init__(self,vendor='postgresql',options=None,rows=(),error=None):
        self.vendor,self.rows,self.error=vendor,rows,error
        self.settings_dict={'HOST':'ep-synthetic-pooler.invalid','PASSWORD':'SYNTHETIC-SECRET','OPTIONS':options or {}}
        self.executed,self.closed=[],0
    def cursor(self):
        return FakeCursor(self)
    def close(self):
        self.closed+=1

ROLE_DEFAULTS=[('lock_timeout','5000','ms','database user'),('statement_timeout','10000','ms','database user')]

class PooledTimeoutContract(SimpleTestCase):
    """Pooled endpoints cannot take startup options; their sessions must prove role defaults instead."""
    DIRECT=['ep-synthetic-123456.c-16.us-east-1.aws.neon.tech','127.0.0.1','db.example',
            'pooler.example','ep-synthetic.pooler-region.example','ep-synthetic-pooler-2.example']
    POOLED=['ep-synthetic-123456-pooler.c-16.us-east-1.aws.neon.tech','EP-SYNTHETIC-POOLER.example']

    def config(self,host):
        return postgres_config(f'postgres://user:password@{host}/test_only?sslmode=verify-full')

    def test_direct_hosts_pin_both_timeouts_in_startup_options(self):
        for host in self.DIRECT:
            with self.subTest(host=host):
                options=self.config(host)['OPTIONS']
                self.assertEqual(options['options'],'-c statement_timeout=10000 -c lock_timeout=5000')
                self.assertTrue(timeouts_pinned_at_startup(options))

    def test_pooled_hosts_omit_startup_options_without_relaxing_other_limits(self):
        for host in self.POOLED:
            with self.subTest(host=host):
                config=self.config(host)
                self.assertNotIn('options',config['OPTIONS'])
                self.assertFalse(timeouts_pinned_at_startup(config['OPTIONS']))
                self.assertEqual(config['OPTIONS']['sslmode'],'verify-full')
                self.assertIn('sslrootcert',config['OPTIONS'])
                self.assertEqual(config['OPTIONS']['connect_timeout'],10)
                self.assertIsNone(config['OPTIONS']['prepare_threshold'])
                self.assertEqual(config['CONN_MAX_AGE'],0)

    def test_only_final_exact_startup_values_count_as_pinned(self):
        self.assertTrue(timeouts_pinned_at_startup({'options':STARTUP_TIMEOUTS+' -c search_path=cr_test_synthetic'}))
        for value in ['', '-c statement_timeout=10000', STARTUP_TIMEOUTS+' -c statement_timeout=0',
                      '-c statement_timeout=100000 -c lock_timeout=5000', '-c lock_timeout=5000 -c statement_timeout=9999']:
            with self.subTest(value=value):
                self.assertFalse(timeouts_pinned_at_startup({'options':value}))
        self.assertFalse(timeouts_pinned_at_startup({}))

    def test_effective_role_defaults_must_be_non_zero_within_bounds(self):
        self.assertTrue(session_timeouts_within_bounds(ROLE_DEFAULTS))
        self.assertTrue(session_timeouts_within_bounds([('statement_timeout','1','ms','database user'),('lock_timeout','2000','ms','database user')]))
        def replace(name,**changes):
            rows=[]
            for row in ROLE_DEFAULTS:
                fields=dict(zip(['name','setting','unit','source'],row))
                if fields['name']==name:
                    fields.update(changes)
                rows.append(tuple(fields.values()))
            return rows
        for name,bound in [('statement_timeout',10000),('lock_timeout',5000)]:
            for changes in [{'setting':'0'},{'setting':str(bound+1)},{'setting':'-1'},{'setting':''},
                            {'unit':'s'},{'unit':None},{'source':'session'},{'source':'client'},
                            {'source':'default'},{'source':'database'},{'source':'user'}]:
                with self.subTest(name=name,changes=changes):
                    self.assertFalse(session_timeouts_within_bounds(replace(name,**changes)))
            with self.subTest(missing=name):
                self.assertFalse(session_timeouts_within_bounds([row for row in ROLE_DEFAULTS if row[0]!=name]))

    def test_receiver_skips_sqlite_and_pinned_postgres_sessions(self):
        for connection in [FakeConnection(vendor='sqlite'),FakeConnection(options={'options':STARTUP_TIMEOUTS})]:
            verify_session_timeouts(sender=None,connection=connection)
            self.assertEqual(connection.executed,[])
            self.assertEqual(connection.closed,0)

    def test_receiver_accepts_verified_pooled_session(self):
        connection=FakeConnection(rows=ROLE_DEFAULTS)
        verify_session_timeouts(sender=None,connection=connection)
        self.assertEqual(connection.executed,[SESSION_TIMEOUTS_SQL])
        self.assertEqual(connection.closed,0)

    def test_receiver_closes_and_refuses_unverified_pooled_session_without_echoing_material(self):
        from django.db import OperationalError
        for rows in [[],[('statement_timeout','0','ms','default'),('lock_timeout','0','ms','default')],
                     [('statement_timeout','10000','ms','session'),('lock_timeout','5000','ms','session')]]:
            connection=FakeConnection(rows=rows)
            with self.subTest(rows=rows),self.assertRaises(OperationalError) as raised:
                verify_session_timeouts(sender=None,connection=connection)
            self.assertEqual(connection.closed,1)
            self.assertNotIn('SYNTHETIC-SECRET',str(raised.exception))
            self.assertNotIn('ep-synthetic',str(raised.exception))
        failing=FakeConnection(error=RuntimeError('synthetic driver failure'))
        with self.assertRaisesMessage(RuntimeError,'synthetic driver failure'):
            verify_session_timeouts(sender=None,connection=failing)
        self.assertEqual(failing.closed,1)

    def test_receiver_is_connected_to_every_new_database_connection(self):
        from django.db import OperationalError
        from django.db.backends.signals import connection_created
        connection=FakeConnection()
        with self.assertRaises(OperationalError):
            connection_created.send(sender=FakeConnection,connection=connection)
        self.assertEqual(connection.executed,[SESSION_TIMEOUTS_SQL])
        self.assertEqual(connection.closed,1)

class DatabaseConfiguration(SimpleTestCase):
    def test_managed_postgres_requires_verified_tls_and_never_echoes_url(self):
        for url in ['sqlite:///tmp/file','postgres://u:SECRET@db.example/test?sslmode=disable',
                    'postgres://u:SECRET@db.example/test?sslmode=require',
                    'postgres://u:SECRET@db.example/test?sslmode=verify-full&options=unsafe',
                    'postgres://u:SECRET@db.example/test?sslmode=verify-full&sslmode=disable',
                    'postgres://u:SECRET@db.example/test?broken',
                    'postgres://u:SECRET@db.example:invalid/test','postgres://u:SECRET@/test']:
            with self.subTest(url=url),self.assertRaises(ImproperlyConfigured) as raised:
                postgres_config(url)
            self.assertNotIn('SECRET',str(raised.exception))
        with patch.dict(os.environ,{'PGSSLROOTCERT':'system'}):
            config=postgres_config('postgres://user:password@db.example/test?sslmode=verify-full')
        self.assertEqual(config['ENGINE'],'django.db.backends.postgresql')
        self.assertEqual(config['OPTIONS']['sslmode'],'verify-full')
        self.assertEqual(config['OPTIONS']['sslrootcert'],'system')
        self.assertEqual(config['CONN_MAX_AGE'],0)
        self.assertIsNone(config['OPTIONS']['prepare_threshold'])

    def test_disposable_local_postgres_can_use_explicit_non_tls_and_unescapes_credentials(self):
        config=postgres_config('postgres://user%40name:p%40ss@127.0.0.1:5432/test_only?sslmode=disable',local=True)
        self.assertEqual(config['USER'],'user@name')
        self.assertEqual(config['PASSWORD'],'p@ss')
        self.assertEqual(config['OPTIONS']['sslmode'],'disable')

    def test_vercel_refuses_ephemeral_sqlite_or_local_mode(self):
        import subprocess,sys,secrets
        base={**os.environ,'VERCEL':'1','DJANGO_SECRET_KEY':secrets.token_urlsafe(64),'DJANGO_ALLOWED_HOSTS':'research.example.invalid','DATABASE_URL':'','LOCAL_DEVELOPMENT':'0'}
        result=subprocess.run([sys.executable,'manage.py','check'],env=base,text=True,capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('persistent PostgreSQL',result.stderr)
        base.update(DATABASE_URL='postgres://u:p@db.example/test',LOCAL_DEVELOPMENT='1')
        result=subprocess.run([sys.executable,'manage.py','check'],env=base,text=True,capture_output=True)
        self.assertNotEqual(result.returncode,0)

    def test_vercel_bundle_excludes_private_runtime_and_fixture_material(self):
        root=Path(__file__).resolve().parents[2]
        config=json.loads((root/'vercel.json').read_text())
        self.assertEqual(config['framework'],'django')
        self.assertIn('config/wsgi.py',config['functions'])
        self.assertNotIn('migrate',json.dumps(config))
        ignores=(root/'.vercelignore').read_text().splitlines()
        for item in ['.env*','var','*.sqlite3','archive/tests']:
            self.assertIn(item,ignores)
