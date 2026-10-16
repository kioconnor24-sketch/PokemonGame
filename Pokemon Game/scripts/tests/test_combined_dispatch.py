"""Test the expensive combined GBA workflow's explicit-only dispatch policy."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "averon-combined-build.yml"


class CombinedBuildDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.events = cls.workflow.split("\npermissions:", 1)[0]

    def test_only_manual_dispatch_triggers_expensive_build(self):
        self.assertIn("on:\n  workflow_dispatch:", self.events)
        self.assertNotIn("issue_comment:", self.events)
        self.assertNotIn("pull_request:", self.events)
        self.assertNotIn("push:", self.events)
        self.assertNotIn("schedule:", self.events)

    def test_manual_pr_selection_and_main_only_mode_preserved(self):
        self.assertIn("first_pr:", self.events)
        self.assertIn("second_pr:", self.events)
        self.assertIn('default: "14"', self.events)
        self.assertIn('default: "25"', self.events)
        self.assertIn("FIRST_PR: ${{ inputs.first_pr }}", self.workflow)
        self.assertIn("SECOND_PR: ${{ inputs.second_pr }}", self.workflow)
        self.assertIn('bash "Pokemon Game/scripts/coordination/run_combined_build.sh" prepare', self.workflow)

    def test_optional_graphical_smoke_retained(self):
        self.assertIn("graphical_smoke:", self.events)
        self.assertIn("if: ${{ inputs.graphical_smoke }}", self.workflow)
        self.assertIn('run: bash "Pokemon Game/scripts/coordination/run_combined_build.sh" smoke', self.workflow)

    def test_checks_remain_real_and_read_only(self):
        self.assertIn("ref: main", self.workflow)
        self.assertIn("persist-credentials: false", self.workflow)
        self.assertIn('run: bash "Pokemon Game/scripts/coordination/run_combined_build.sh" test', self.workflow)
        self.assertIn('run: bash "Pokemon Game/scripts/coordination/run_combined_build.sh" report', self.workflow)
        self.assertIn("Verify SHA, real test counts", self.workflow)
        self.assertIn("Attach logs, checksums and screenshots ONLY", self.workflow)
        self.assertIn("contents: read", self.workflow)


if __name__ == "__main__":
    unittest.main()
