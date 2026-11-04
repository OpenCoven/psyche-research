import json
import os
from pathlib import Path
from unittest.mock import patch
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from config.database import postgres_config

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
