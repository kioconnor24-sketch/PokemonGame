"""Regression tests for sensitive files, QA maps, PR collisions and approvals."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "coordination" / "check_protected_files.py"
SPEC = importlib.util.spec_from_file_location("guard", SCRIPT)
GUARD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GUARD)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.conf = {"pull_request": {"number": 25, "files": []},
                     "other_open_prs": [], "handoffs": []}

    def add(self, path, status="modified"):
        self.conf["pull_request"]["files"].append({"filename": path, "status": status})

    def test_disjoint_change_allowed(self):
        self.add("Pokemon Game/engine/test/averon_scripted_battle.c")
        self.assertEqual(GUARD.validate(self.conf)[0], [])

    def test_shared_config_requires_explicit_handoff(self):
        path = "Pokemon Game/engine/include/config/battle.h"
        self.add(path)
        self.assertIn("handoff NOT recorded", GUARD.validate(self.conf)[0][0])
        self.conf["handoffs"] = [{"pr": 25, "association": "OWNER", "paths": [path]}]
        self.assertEqual(GUARD.validate(self.conf)[0], [])

    def test_other_pr_approval_does_not_work(self):
        path = "Pokemon Game/engine/data/event_scripts.s"
        self.add(path)
        self.conf["handoffs"] = [{"pr": 30, "association": "OWNER", "paths": [path]}]
        self.assertEqual(len(GUARD.validate(self.conf)[0]), 1)

    def test_untrusted_approval_does_not_work(self):
        path = "Pokemon Game/engine/data/event_scripts.s"
        self.add(path)
        self.conf["handoffs"] = [{"pr": 25, "association": "NONE", "paths": [path]}]
        self.assertEqual(len(GUARD.validate(self.conf)[0]), 1)

    def test_protected_pr_collision_fails_with_even_valid_handoff(self):
        path = "Pokemon Game/engine/include/config/battle.h"
        self.add(path)
        self.conf["other_open_prs"] = [{"number": 14, "files": [path]}]
        self.conf["handoffs"] = [{"pr": 25, "association": "OWNER", "paths": [path]}]
        self.assertEqual(len(GUARD.validate(self.conf)[0]), 1)

    def test_nonprotected_overlap_only_warns(self):
        self.add("README.md")
        self.conf["other_open_prs"] = [{"number": 18, "files": ["README.md"]}]
        errors, warns = GUARD.validate(self.conf)
        self.assertFalse(errors)
        self.assertEqual(len(warns), 1)

    def test_frozen_map_fails_on_existing_or_new_layout(self):
        self.add("Pokemon Game/engine/data/maps/Alderfield/map.json")
        self.assertIn("NO MAP", GUARD.validate(self.conf)[0][0])

    def test_historical_quest_grandfathered(self):
        self.conf["pull_request"]["number"] = 14
        self.add("Pokemon Game/engine/data/maps/Alderfield/map.json")
        self.add("Pokemon Game/engine/include/constants/flags.h")
        self.assertEqual(GUARD.validate(self.conf)[0], [])


if __name__ == "__main__":
    unittest.main()
