#!/usr/bin/env python3
"""No-ROM regressions for saved map object-event template capacity."""
import importlib.util
from pathlib import Path
import re
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]
ENGINE = SCRIPTS.parent / "engine"
SPEC = importlib.util.spec_from_file_location(
    "averon_map_registry", SCRIPTS / "check-averon-map-registry.py")
registry = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(registry)


class ObjectEventCapacityTests(unittest.TestCase):
    def check_count(self, count):
        groups = {"group_order": ["gMapGroup_Synthetic"],
                  "gMapGroup_Synthetic": ["Synthetic"]}
        maps = {"Synthetic": {"id": "MAP_SYNTHETIC", "name": "Synthetic",
                              "object_events": [{} for _ in range(count)]}}
        pins = ([(0, "gMapGroup_Synthetic", 1, 1)],
                [(0, 0, "MAP_SYNTHETIC", "Synthetic", 1)])
        return registry.validate(groups, maps, pins)

    def test_sixty_four_object_events_is_last_safe_count(self):
        self.assertEqual(self.check_count(64), [])

    def test_sixty_five_objects_fail_before_overwriting_saveblock(self):
        errors = self.check_count(65)
        self.assertIn("event-capacity", {e["code"] for e in errors})
        self.assertIn("65 > 64", next(e["detail"] for e in errors
                                        if e["code"] == "event-capacity"))

    def test_old_two_hundred_fifty_five_limit_is_rejected(self):
        self.assertIn("event-capacity",
                      {e["code"] for e in self.check_count(255)})

    def test_checker_limit_matches_real_engine_save_array(self):
        source = (ENGINE / "include/constants/global.h").read_text()
        match = re.search(
            r"^\s*#define\s+OBJECT_EVENT_TEMPLATES_COUNT\s+(\d+)\b",
            source, re.M)
        self.assertIsNotNone(match)
        self.assertEqual(registry.EVENTS["object_events"], int(match.group(1)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
