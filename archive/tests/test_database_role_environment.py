"""Prevent ambient hosting and libpq settings reaching the local fixture parent."""

import os
import sys
import unittest
from unittest.mock import patch

from archive.tests import run_database_role_rehearsal as launcher


class RoleParentEnvironmentTests(unittest.TestCase):
    def test_hostile_database_and_interpreter_settings_are_not_forwarded(self):
        hostile = {'PATH': '/synthetic-bin', 'HOME': '/synthetic-home', 'LC_ALL': 'C',
                   'PGHOSTADDR': '127.0.0.1', 'PGPORT': '1', 'PGSERVICE': 'synthetic',
                   'PGPASSWORD': 'SYNTHETIC', 'PGOPTIONS': '-c default_transaction_read_only=on',
                   'PGPASSFILE': '/synthetic-secret', 'PGSERVICEFILE': '/synthetic-service',
                   'PGSYSCONFDIR': '/synthetic-config', 'DATABASE_URL': 'synthetic-invalid',
                   'PYTHONPATH': '/synthetic-import', 'PYTHONOPTIMIZE': '1',
                   'GIT_DIR': '/synthetic-repository', 'VERCEL': '1', 'WORKOS_API_KEY': 'SYNTHETIC'}
        actual = launcher.sanitized_environment(hostile)
        self.assertEqual(actual, {'PATH': '/synthetic-bin', 'HOME': '/synthetic-home',
                                  'LC_ALL': 'C', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONNOUSERSITE': '1',
                                  'PGPASSFILE': os.devnull, 'PGSERVICEFILE': os.devnull})

    def test_exec_boundary_uses_reviewed_fixture_and_explicit_arguments(self):
        args = ['launcher', '--expected-major', '18', '--source-revision', 'a' * 40]
        with patch.object(sys, 'argv', args), patch.dict(os.environ, {'PGHOSTADDR': '127.0.0.1'}, clear=True), \
                patch.object(launcher.os, 'execve') as execute:
            launcher.main()
        interpreter, command, environment = execute.call_args.args
        self.assertEqual(interpreter, sys.executable)
        self.assertEqual(command, [sys.executable, '-I', '-B', str(launcher.FIXTURE), *args[1:]])
        self.assertNotIn('PGHOSTADDR', environment)
        self.assertEqual(environment['PGPASSFILE'], os.devnull)
        self.assertEqual(environment['PGSERVICEFILE'], os.devnull)


if __name__ == '__main__':
    unittest.main(verbosity=2)
