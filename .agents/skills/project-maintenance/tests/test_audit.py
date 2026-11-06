import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("audit", Path(__file__).parents[1] / "scripts/audit.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditTests(unittest.TestCase):
    def test_worktree_paths_with_spaces_and_newlines(self):
        trees = audit.worktrees("worktree /tmp/one tree\nreview\0HEAD abc\0detached\0\0worktree /tmp/two\0HEAD def\0branch refs/heads/main\0\0")
        self.assertEqual(trees[0]["worktree"], "/tmp/one tree\nreview")
        self.assertTrue(trees[0]["detached"])
        self.assertEqual(trees[1]["branch"], "refs/heads/main")

    def test_pagination_reads_past_first_page(self):
        with patch.object(audit, "api", side_effect=[list(range(100)), [100]]) as read:
            self.assertEqual(audit.pages(Path.cwd(), "issues?state=open"), list(range(101)))
        self.assertTrue(read.call_args_list[1].args[1].endswith("page=2"))

    def test_failed_page_does_not_return_partial_success(self):
        with patch.object(audit, "api", side_effect=[list(range(100)), RuntimeError("offline")]):
            with self.assertRaises(RuntimeError):
                audit.pages(Path.cwd(), "issues")

    def test_network_failure_is_explicit_and_never_empty_success(self):
        with patch.object(audit, "api", side_effect=RuntimeError("private diagnostic")):
            data = audit.remote_inventory(Path.cwd())
        self.assertFalse(data["complete"])
        self.assertEqual(len(data["errors"]), 5)
        self.assertNotIn("private diagnostic", str(data))
        self.assertNotIn("issues", data)

    def test_receipt_is_private_and_atomic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            audit.write_receipt(path, {"complete": False})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            audit.write_receipt(path, {"complete": True})
            self.assertEqual(path.read_text(), '{\n  "complete": true\n}\n')
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_local_summary_does_not_expose_machine_paths(self):
        data = {"local": {"head": "abc", "worktrees": [{"worktree": "/private/owner/path"}]}, "collected_at": "now", "remote": {"skipped": True}}
        self.assertNotIn("/private", audit.summary(data))
        self.assertIn("local evidence only", audit.summary(data))

    def test_failed_remote_counts_are_unknown(self):
        data = {"local": {"head": "abc", "worktrees": []}, "collected_at": "now", "remote": {"complete": False, "errors": []}}
        self.assertIn("Open issues: unknown; open PRs: unknown", audit.summary(data))

    def test_current_main_and_pr_heads_both_get_checks_and_statuses(self):
        def response(root, path):
            if path == "branches/main":
                return {"name": "main", "protected": False, "commit": {"sha": "mainsha"}}
            if path.startswith("pulls?"):
                return [{"number": 5, "title": "change", "head": {"sha": "prsha", "ref": "feature"}, "base": {"ref": "main"}, "draft": True}]
            if path.startswith("actions/runs?"):
                return {"workflow_runs": []}
            if "/check-runs?" in path:
                return {"check_runs": []}
            return []
        with patch.object(audit, "api", side_effect=response) as read:
            data = audit.remote_inventory(Path.cwd())
        self.assertTrue(data["complete"])
        for sha in ("mainsha", "prsha"):
            self.assertIn("checks:" + sha, data)
            self.assertIn("statuses:" + sha, data)
        self.assertFalse(data["main"]["protected"])


if __name__ == "__main__":
    unittest.main()
