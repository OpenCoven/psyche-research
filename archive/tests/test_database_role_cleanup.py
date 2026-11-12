"""Exercise the real fixture's persisted failure report without starting a server."""

import ast
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest


FIXTURE = Path(__file__).with_name('rehearse_database_roles.py')


class RoleCleanupReportTests(unittest.TestCase):
    def execute_cleanup(self, *, stop_fails=False, first_failure=None, omit_report_fix=False):
        tree = ast.parse(FIXTURE.read_text())
        blocks = [node for node in tree.body if isinstance(node, ast.Try) and node.finalbody]
        self.assertEqual(len(blocks), 1)
        body = copy.deepcopy(blocks[0].finalbody)
        if omit_report_fix:
            # Reproduce the reviewed defect while retaining the nonzero-exit safeguard.
            fixes = [node for node in body if isinstance(node, ast.If) and any(
                isinstance(child, ast.Assign) and any(
                    isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Name) and target.value.id == 'report'
                    and isinstance(target.slice, ast.Constant) and target.slice.value == 'status'
                    for target in child.targets)
                for child in ast.walk(node))]
            self.assertEqual(len(fixes), 1)
            body.remove(fixes[0])

        statuses = iter([0] if stop_fails else [0, 3])
        stopped = []

        def status_probe(*args, **kwargs):
            return SimpleNamespace(returncode=next(statuses))

        def stop_owned_server(*args, **kwargs):
            stopped.append(True)
            if stop_fails:
                raise RuntimeError('SYNTHETIC forced stop-command failure')
            return ''

        report = {'status': 'failed' if first_failure else 'passed',
                  'first_failure': first_failure, 'checks': []}
        with tempfile.TemporaryDirectory(prefix='psyche-cleanup-control-') as directory:
            root = Path(directory)
            namespace = {'start_attempted': True, 'subprocess': SimpleNamespace(run=status_probe),
                         'BIN': Path('/synthetic-bin'), 'ROOT': root, 'ENV': {},
                         'run': stop_owned_server, 'report': report, 'json': json}
            error = None
            with contextlib.redirect_stdout(io.StringIO()):
                try:
                    exec(compile(ast.Module(body=body, type_ignores=[]), str(FIXTURE), 'exec'), namespace)
                except RuntimeError as exc:
                    error = exc
            persisted = json.loads((root / 'role-report.json').read_text())
        self.assertEqual(stopped, [True])
        return persisted, error

    def assert_failed_report(self, report, error):
        self.assertIsInstance(error, RuntimeError)
        self.assertFalse(report['server_stopped'])
        self.assertEqual(report['status'], 'failed')
        self.assertTrue(report['first_failure'])

    def test_successful_cleanup_preserves_a_passed_report(self):
        report, error = self.execute_cleanup()
        self.assertIsNone(error)
        self.assertTrue(report['server_stopped'])
        self.assertEqual(report['final_server_status_exit'], 3)
        self.assertEqual(report['status'], 'passed')
        self.assertIsNone(report['first_failure'])

    def test_cleanup_failure_is_persisted_before_nonzero_exit(self):
        report, error = self.execute_cleanup(stop_fails=True)
        self.assert_failed_report(report, error)

    def test_cleanup_failure_preserves_the_original_failure(self):
        original = 'ValueError: SYNTHETIC first failure'
        report, error = self.execute_cleanup(stop_fails=True, first_failure=original)
        self.assert_failed_report(report, error)
        self.assertEqual(report['first_failure'], original)

    def test_historical_passed_receipt_on_cleanup_failure_is_rejected(self):
        report, error = self.execute_cleanup(stop_fails=True, omit_report_fix=True)
        self.assertIsInstance(error, RuntimeError)
        self.assertFalse(report['server_stopped'])
        with self.assertRaises(AssertionError):
            self.assert_failed_report(report, error)


if __name__ == '__main__':
    unittest.main(verbosity=2)
