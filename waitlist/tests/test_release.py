from django.conf import settings
import unittest
if settings.ROOT_URLCONF != 'waitlist.urls':
    raise unittest.SkipTest('Waitlist guarantees run separately with config.waitlist_settings.')

import subprocess
import tempfile
from pathlib import Path
from django.test import SimpleTestCase
from tools.prepare_waitlist_release import prepare


class PublicPackageTests(SimpleTestCase):
    def test_prepared_upload_keeps_python_pin_and_excludes_private_surfaces(self):
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            receipt = prepare(revision, source)
            self.assertIn('.python-version', receipt['files'])
            self.assertEqual((source / '.python-version').read_text().strip(), '3.13')
            self.assertFalse(any((source / name).exists() for name in ['archive', 'var', 'docs', 'waitlist/tests', 'waitlist/management']))
            self.assertIn('config.waitlist_wsgi:application', (source / 'pyproject.toml').read_text())
