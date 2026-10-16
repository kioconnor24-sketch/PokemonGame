"""Guard the owner-approved pre-Sinnoh assignment registry against duplicate work."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "coordination" / "tasks.json"
BOARD = ROOT / "coordination" / "render_board.py"
SPEC = importlib.util.spec_from_file_location("backend_board", BOARD)
board = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(board)


class BackendOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.conf = json.loads(REGISTRY.read_text(encoding="utf-8"))
        cls.tasks = cls.conf["tasks"]
        cls.by_id = {t["id"]: t for t in cls.tasks}

    def test_all_task_identifiers_unique(self):
        self.assertEqual(len(self.tasks), len(self.by_id))

    def test_backend_before_sinnoh_is_required(self):
        policy = self.conf["policies"]
        self.assertTrue(policy["backend_before_sinnoh"])
        self.assertTrue(policy["sinnoh_maps_require_owner_approval"])
        self.assertTrue(policy["creative_freeze"])
        self.assertFalse(policy["auto_merge"])
        self.assertFalse(policy["auto_agent_execution"])
        self.assertTrue(policy["do_not_auto_awaken_agents"])

    def test_one_writer_per_backend_interface(self):
        owners = {}
        for task in self.tasks:
            for interface in task.get("owned_interfaces", []):
                self.assertNotIn(interface, owners,
                                 f"{interface} claimed by both {owners.get(interface)} and {task['id']}")
                owners[interface] = task["agent"]
        self.assertEqual(owners["region_specific_caps_obedience"], "codex")
        self.assertEqual(owners["generic_battle_exp_items_followers_ai"], "claude")

    def test_legend_not_restarted_or_owned_by_codex(self):
        task = self.by_id["LEGEND"]
        self.assertEqual(task["pr"], 47)
        self.assertEqual(task["agent"], "claude")
        self.assertFalse(any("LEGEND" in interface for interface in
                             self.by_id["TWO-REGION"]["owned_interfaces"]))

    def test_all_active_tasks_have_fallback_and_resume_trigger(self):
        active = ["QUEST", "TWO-REGION", "SCRIPTED-BATTLE",
                  "LEGEND", "POKEMON-MECHANICS", "REGION-PLATFORM",
                  "QUEST-PLAYTEST"]
        for name in active:
            task = self.by_id[name]
            with self.subTest(task=name):
                self.assertGreaterEqual(len(task["fallback_order"]), 1)
                self.assertTrue(task["resume_when"].strip())
                self.assertTrue(task["next"].strip())

    def test_fallback_does_not_waive_qa(self):
        self.assertEqual(self.by_id["QUEST"]["qa_cases"],
                         ["Q1", "Q2", "Q3", "Q4", "Q5"])
        self.assertIn("QUEST", self.by_id["SCRIPTED-BATTLE"]["deps"])
        self.assertIn("QUEST", self.by_id["TWO-REGION"]["deps"])
        self.assertTrue(self.conf["policies"]["dependency_gates_apply_to_merge"])

    def test_no_map_production_task_was_activated(self):
        forbidden = ("SINNOH-MAPS", "AVERON-MAPS", "MAP-PRODUCTION")
        self.assertFalse(set(forbidden) & set(self.by_id))
        self.assertTrue(self.conf["policies"]["creative_freeze"])

    def test_board_renders_real_legend_task_and_no_wait_alternative(self):
        prs = [{"number": int(task["pr"]), "state": "open",
                "merged": False, "head_sha": "a" * 40, "checks": "success"}
               for task in self.tasks if task.get("pr")]
        snapshot = {"main_sha": "f" * 40, "generated_at": "synthetic",
                    "pull_requests": prs, "qa_signoffs": []}
        result = board.render(self.conf, snapshot)
        self.assertIn("| LEGEND | claude |", result["board"])
        self.assertIn("| POKEMON-MECHANICS | claude |", result["board"])
        self.assertIn("While waiting:", result["codex"])
        self.assertIn("While waiting:", result["claude"])
        self.assertIn("BACKEND FIRST", result["board"])
        self.assertIn("No automated agent launch", result["board"])

    def test_board_dependencies_do_not_block_independent_coding(self):
        computed = board.calculate(self.tasks, {
            "pull_requests": [
                {"number": 14, "state": "open", "merged": False,
                 "head_sha": "b" * 40, "checks": "success"},
                {"number": 25, "state": "open", "merged": False,
                 "head_sha": "c" * 40, "checks": "success"}
            ],
            "qa_signoffs": []
        })
        self.assertIn("DEVELOPMENT OPEN", computed["SCRIPTED-BATTLE"]["status"])
        self.assertIn("MERGE GATED", computed["TWO-REGION"]["status"])
        self.assertNotIn("MERGED", computed["QUEST"]["status"])

    def test_no_invented_pr_for_region_groundwork(self):
        task = self.by_id["TWO-REGION"]
        self.assertNotIn("pr", task)
        self.assertEqual(task["branch"], "codex/two-region-groundwork")


if __name__ == "__main__":
    unittest.main()
