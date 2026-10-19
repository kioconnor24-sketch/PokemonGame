"""Regression coverage for the current read-only live PR advisory workflow."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/averon-agent-board.yml"

class AgentBoardDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.trigger_section = cls.source.split("\npermissions:", 1)[0]

    def test_pr_events_refresh_without_duplicate_main_push(self):
        self.assertRegex(self.trigger_section, r"(?m)^  pull_request_target:$")
        self.assertIn("closed", self.trigger_section)
        self.assertNotRegex(self.trigger_section, r"(?m)^  push:$")

    def test_schedule_manual_and_claim_only_comment_refresh(self):
        self.assertRegex(self.trigger_section, r"(?m)^  schedule:$")
        self.assertRegex(self.trigger_section, r"(?m)^  workflow_dispatch:$")
        self.assertIn("github.event.issue.number == 15", self.source)
        self.assertIn("startsWith(github.event.comment.body, 'CLAIM |')", self.source)

    def test_read_only_and_no_pr_checkout(self):
        permissions = self.source.split("\npermissions:", 1)[1].split("\nconcurrency:", 1)[0]
        self.assertNotIn("write", permissions)
        self.assertNotIn("actions/checkout", self.source)
        self.assertNotIn("issues.update", self.source)
        self.assertNotIn("pulls.merge", self.source)
        self.assertNotIn("render_board.py", self.source)
        self.assertNotIn("registry.tasks", self.source)
        self.assertIn("cancel-in-progress: false", self.source)

    def test_actual_javascript_with_fixture_api(self):
        result = subprocess.run(
            ["node", str(ROOT / "Pokemon Game/scripts/coordination/test_live_pr_board.cjs")],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: 6 board scenarios", result.stdout)

if __name__ == "__main__":
    unittest.main()
