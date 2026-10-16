"""Keep the advisory dispatch board responsive during high-volume merges.

These are source-level trigger checks; no GitHub credentials or network needed.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "averon-agent-board.yml"


class AgentBoardDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = WORKFLOW.read_text(encoding="utf-8")
        cls.trigger_section = cls.source.split("\npermissions:", 1)[0]

    def test_refreshes_on_pr_changes_and_qa_comments(self):
        self.assertRegex(self.trigger_section, r"(?m)^  pull_request_target:$")
        self.assertRegex(self.trigger_section, r"(?m)^  issue_comment:$")
        self.assertIn("closed", self.trigger_section)
        self.assertIn("types: [created]", self.trigger_section)

    def test_preserves_manual_and_scheduled_fallback(self):
        self.assertRegex(self.trigger_section, r"(?m)^  workflow_dispatch:$")
        self.assertRegex(self.trigger_section, r"(?m)^  schedule:$")

    def test_merges_do_not_double_trigger_on_main_push(self):
        # Each normal PR merge emits pull_request_target.closed.
        self.assertNotRegex(self.trigger_section, r"(?m)^  push:$")
        self.assertIn("types: [opened, synchronize, reopened, closed", self.trigger_section)

    def test_running_snapshot_is_not_cancelled_by_traffic(self):
        concurrency = self.source.split("\nconcurrency:", 1)[1].split("\njobs:", 1)[0]
        self.assertRegex(concurrency, r"(?m)^  group: averon-agent-board$")
        self.assertRegex(concurrency, r"(?m)^  cancel-in-progress: false$")
        self.assertNotIn("cancel-in-progress: true", concurrency)

    def test_board_stays_advisory_and_uses_trusted_main(self):
        self.assertIn("ref: main", self.source)
        self.assertIn("persist-credentials: false", self.source)
        self.assertIn("issue_number: registry.qa_issue", self.source)
        self.assertIn("issue_number:config.board_issue", self.source)
        self.assertIn("github.event.issue.number == 15", self.source)
        self.assertIn("github.event.issue.number == 23", self.source)


if __name__ == "__main__":
    unittest.main()
