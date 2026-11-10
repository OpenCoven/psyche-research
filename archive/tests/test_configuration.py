import json
import os
import tempfile
from pathlib import Path
from unittest import skipIf
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from config import database
from config.database import postgres_config

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
