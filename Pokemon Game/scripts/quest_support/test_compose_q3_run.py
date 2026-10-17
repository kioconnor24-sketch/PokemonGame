"""Fixture tests for compose_q3_run.py: exact cut point, env export, fail-closed."""
import importlib.util
import unittest
from pathlib import Path

FILE = Path(__file__).with_name("compose_q3_run.py")
spec = importlib.util.spec_from_file_location("compose_q3_run", FILE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

STEP_BODY = """      - name: Launch actual graphical mGBA and capture controller milestones
        shell: bash
        env:
          SDL_AUDIODRIVER: dummy
        run: |
          echo start
          if true; then
            echo q3
          else
            echo "QA_Q3_GYM_NOT_RUN: genuine gifted party prerequisite not proven"
          fi
          echo after-q3
"""
WORKFLOW = "jobs:\n  rendered-smoke:\n    steps:\n      - uses: actions/checkout@v4\n" + STEP_BODY


class ComposeTests(unittest.TestCase):
    def test_cuts_after_the_q3_block_and_appends(self):
        out = tool.compose(WORKFLOW, "echo continuation\n")
        self.assertEqual(out.splitlines(), [
            "export SDL_AUDIODRIVER=dummy", "echo start", "if true; then", "  echo q3", "else",
            '  echo "QA_Q3_GYM_NOT_RUN: genuine gifted party prerequisite not proven"', "fi",
            "echo continuation"])

    def test_missing_or_repeated_marker_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "found 0"):
            tool.compose(WORKFLOW.replace("QA_Q3_GYM_NOT_RUN", "OTHER"), "")
        twice = WORKFLOW.replace("echo after-q3", "echo after-q3\n" + "\n".join(
            "          " + line for line in ['if false; then', 'else',
                                             '  echo "QA_Q3_GYM_NOT_RUN: genuine gifted party prerequisite not proven"',
                                             'fi']))
        with self.assertRaisesRegex(ValueError, "found 2"):
            tool.compose(twice, "")

    def test_missing_step_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "found 0"):
            tool.compose(WORKFLOW.replace("Launch actual graphical mGBA", "Launch"), "")

    def test_live_pinned_workflow_if_present(self):
        live = Path(__file__).resolve().parents[3] / ".github/workflows/averon-rendered-playtest.yml"
        if not live.exists():
            self.skipTest("rendered workflow not in this checkout")
        prefix, env = tool.q3_prefix(live.read_text())
        self.assertEqual(prefix[-2:], list(tool.Q3_END))
        self.assertEqual(env.get("SDL_AUDIODRIVER"), "dummy")


if __name__ == "__main__":
    unittest.main(verbosity=2)
