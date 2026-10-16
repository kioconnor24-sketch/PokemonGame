"""Prevent agent startup files from reintroducing obsolete task routing.

Keep these generic: the owner may reassign engineers, and Issue #15 is live.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
ENTRYPOINTS = (
    ROOT / "AGENTS.md",
    ROOT / "Pokemon Game" / "AGENTS.md",
    ROOT / "Pokemon Game" / "Averon_Codex_Handoff" / "AGENTS.md",
)


class AgentEntrypointTests(unittest.TestCase):
    def test_every_entrypoint_starts_with_live_ownership(self):
        for path in ENTRYPOINTS:
            with self.subTest(path=str(path)):
                beginning = path.read_text(encoding="utf-8")[:1800]
                self.assertIn("Issue #15", beginning)
                self.assertIn("Codex", beginning)
                self.assertIn("Playtest", beginning)
                self.assertIn("main", beginning)
                self.assertRegex(beginning.lower(), r"map")

    def test_old_milestones_are_not_startup_orders(self):
        handoff = ENTRYPOINTS[2].read_text(encoding="utf-8")
        self.assertNotIn("Start with tasks M0–M2", handoff)
        self.assertIn("## Current work order", handoff)
        self.assertIn("Older `CODEX_WORK_ORDER.md` is historical", handoff)

    def test_historical_colead_labels_are_superseded(self):
        for path in ENTRYPOINTS[:2]:
            with self.subTest(path=str(path)):
                beginning = path.read_text(encoding="utf-8")[:1800]
                self.assertNotIn("MOST RECENT OWNER EXECUTION ORDER", beginning)
                self.assertNotIn("LATEST OWNER BACKEND-FIRST EXECUTION CONTRACT", beginning)


if __name__ == "__main__":
    unittest.main()
