"""Safety tests for the advisory, evidence-based team board."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "coordination" / "render_board.py"
SPEC = importlib.util.spec_from_file_location("board", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BoardTests(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            {"id": "Q", "agent": "codex", "pr": 14, "deps": [],
             "qa_cases": ["Q1", "Q2"], "next": "Accept actual QA"},
            {"id": "B", "agent": "claude", "pr": 25, "deps": ["Q"],
             "requires_handoff": True, "next": "Exclusive two-file handoff"},
            {"id": "P", "agent": "playtest", "pr": 20, "deps": [],
             "next": "Run actual screenshots"},
        ]
        self.conf = {"tasks": self.tasks}
        self.snap = {
            "main_sha": "a" * 40, "generated_at": "fixture",
            "pull_requests": [
                {"number": 14, "state": "open", "merged": False, "head_sha": "b" * 40, "checks": "success"},
                {"number": 25, "state": "open", "merged": False, "head_sha": "c" * 40},
                {"number": 20, "state": "open", "merged": False, "head_sha": "d" * 40},
            ], "qa_signoffs": [],
        }

    def test_open_quest_requires_visual_acceptance(self):
        results = MODULE.calculate(self.tasks, self.snap)
        self.assertEqual(results["Q"]["status"], "OPEN PR / QA PENDING")
        self.assertEqual(results["B"]["status"], "BLOCKED ON Q")

    def test_native_green_does_not_accept_quest(self):
        self.snap["pull_requests"][0]["state"] = "closed"
        self.snap["pull_requests"][0]["merged"] = True
        results = MODULE.calculate(self.tasks, self.snap)
        self.assertIn("QA SIGNOFF NOT FOUND", results["Q"]["status"])
        self.assertEqual(results["B"]["status"], "MANUAL SHARED-FILE HANDOFF REQUIRED")

    def test_qa_requires_same_sha_all_cases_and_authorization(self):
        self.snap["pull_requests"][0].update(state="closed", merged=True)
        marker = {"pr": 14, "sha": "b" * 40, "status": "PASS",
                  "cases": ["Q1", "Q2"], "association": "NONE"}
        self.snap["qa_signoffs"] = [marker]
        self.assertFalse(MODULE.is_qa_accepted(self.tasks[0], self.snap, self.snap["pull_requests"][0]))
        marker["association"] = "OWNER"
        marker["sha"] = "e" * 40
        self.assertFalse(MODULE.is_qa_accepted(self.tasks[0], self.snap, self.snap["pull_requests"][0]))
        marker["sha"] = "b" * 40
        marker["cases"] = ["Q1"]
        self.assertFalse(MODULE.is_qa_accepted(self.tasks[0], self.snap, self.snap["pull_requests"][0]))
        marker["cases"] = ["Q1", "Q2"]
        self.assertTrue(MODULE.is_qa_accepted(self.tasks[0], self.snap, self.snap["pull_requests"][0]))
        self.assertEqual(MODULE.calculate(self.tasks, self.snap)["B"]["status"], "MANUAL SHARED-FILE HANDOFF REQUIRED")

    def test_parallel_development_is_not_blocked_by_unmerged_quest(self):
        # A downstream PR can be developed independently but never described as
        # integrated, merged or QA accepted until exact-SHA gates pass.
        self.tasks[1]["parallel_development"] = True
        results = MODULE.calculate(self.tasks, self.snap)
        self.assertEqual(results["B"]["status"], "DEVELOPMENT OPEN; MERGE GATED ON Q")
        displayed = MODULE.render(self.conf, self.snap)
        self.assertIn("DEVELOPMENT OPEN; MERGE GATED ON Q", displayed["claude"])
        self.assertIn("HARD FREEZE", displayed["board"])
        self.assertIn("No automated agent launch", displayed["board"])
        self.assertIn("QA evidence rule", displayed["board"])

    def test_parallel_development_does_not_release_file_handoff(self):
        self.tasks[1]["parallel_development"] = True
        self.snap["pull_requests"][0].update(state="closed", merged=True)
        self.snap["qa_signoffs"] = [{
            "pr": 14, "sha": "b" * 40, "status": "PASS",
            "cases": ["Q1", "Q2"], "association": "OWNER"
        }]
        results = MODULE.calculate(self.tasks, self.snap)
        self.assertEqual(results["B"]["status"], "DEVELOPMENT OPEN; SHARED-FILE MERGE HANDOFF REQUIRED")
        self.assertNotIn("MERGED", results["B"]["status"])

    def test_parallel_work_is_not_a_qa_shortcut(self):
        self.tasks[1]["parallel_development"] = True
        self.snap["pull_requests"][0].update(state="closed", merged=True)
        # Missing Gate B QA is still recorded, but a real upstream merge
        # releases downstream merge-dependency tracking.
        results = MODULE.calculate(self.tasks, self.snap)
        self.assertEqual(results["B"]["status"], "DEVELOPMENT OPEN; SHARED-FILE MERGE HANDOFF REQUIRED")
        self.assertIn("QA SIGNOFF NOT FOUND", results["Q"]["status"])

    def test_actual_upstream_merge_releases_downstream_dependency_but_not_qa_verdict(self):
        self.tasks[1]["parallel_development"] = True
        self.snap["pull_requests"][0].update(state="closed", merged=True)
        results = MODULE.calculate(self.tasks, self.snap)
        self.assertEqual(results["Q"]["status"], "MERGED; REQUIRED QA SIGNOFF NOT FOUND")
        self.assertEqual(results["B"]["status"],
                         "DEVELOPMENT OPEN; SHARED-FILE MERGE HANDOFF REQUIRED")

    def test_merged_without_extra_qa_is_done(self):
        self.snap["pull_requests"][2].update(state="closed", merged=True)
        self.assertEqual(MODULE.calculate(self.tasks, self.snap)["P"]["status"], "MERGED")

    def test_failing_check_is_not_green(self):
        self.snap["pull_requests"][2]["checks"] = "failure"
        self.assertIn("FAILING CHECKS", MODULE.calculate(self.tasks, self.snap)["P"]["status"])

    def test_missing_dependency_fails_closed(self):
        self.tasks[1]["deps"] = ["UNDEFINED"]
        with self.assertRaises(ValueError):
            MODULE.calculate(self.tasks, self.snap)

    def test_duplicate_task_fails_closed(self):
        self.tasks.append(dict(self.tasks[0]))
        with self.assertRaises(ValueError):
            MODULE.calculate(self.tasks, self.snap)

    def test_large_epic_links_are_visible_without_releasing_gates(self):
        self.tasks[0]["issue"] = 34
        self.tasks[1]["issue"] = 35
        self.tasks[2]["issue"] = 36
        rendered = MODULE.render(self.conf, self.snap)
        self.assertIn("[epic #34](https://github.com/kioconnor24-sketch/PokemonGame/issues/34)", rendered["board"])
        self.assertIn("[epic #35](https://github.com/kioconnor24-sketch/PokemonGame/issues/35)", rendered["claude"])
        self.assertIn("[epic #36](https://github.com/kioconnor24-sketch/PokemonGame/issues/36)", rendered["playtest"])
        self.assertIn("BLOCKED ON Q", rendered["board"])

    def test_generated_board_never_assigns_ownership_from_stale_registry(self):
        # Issue #31 is overwritten on every Actions refresh.  Its static
        # registry must never pretend to supersede newer Issue #15 claims.
        self.tasks[0]["next"] = "EDIT SHARED FILES NOW (stale historical text)"
        rendered = MODULE.render(self.conf, self.snap)
        for name, body in rendered.items():
            with self.subTest(output=name):
                self.assertIn("STATIC REGISTRY — NOT LIVE FILE OWNERSHIP", body)
                self.assertIn("https://github.com/kioconnor24-sketch/PokemonGame/issues/15", body)
                self.assertIn("ACTIVE M1", body)
        self.assertIn("M1 responsible lane (not file claim)", rendered["board"])
        self.assertIn("M1 action (verify #15)", rendered["board"])
        self.assertIn(
            "ACTIVE M1 — verify current #15 claim and PR scope first. "
            "EDIT SHARED FILES NOW",
            rendered["board"],
        )
        self.assertNotIn("## Live task/dependency routing", rendered["board"])
        self.assertIn("advisory inbox (verify live claims)", rendered["codex"])
        self.assertIn("advisory inbox (verify live claims)", rendered["claude"])

    def test_generated_board_says_no_auto_merge_or_map_work(self):
        result = MODULE.render(self.conf, self.snap)
        self.assertEqual(set(result), {"board", "codex", "claude", "playtest", "summary"})
        self.assertIn("HARD FREEZE", result["board"])
        self.assertIn("No automated agent launch", result["board"])
        self.assertIn("BLOCKED ON Q", result["claude"])
        self.assertNotIn("BLOCKED ON Q", result["playtest"])


if __name__ == "__main__":
    unittest.main()
