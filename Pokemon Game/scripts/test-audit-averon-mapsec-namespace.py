"""Tests for the read-only map-section / met-location namespace inventory."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("audit-averon-mapsec-namespace.py")
SPEC = importlib.util.spec_from_file_location("mapsec_namespace_audit", SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class Fixture(unittest.TestCase):
    """A synthetic engine tree: four sections, Averon group and upstream maps."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.engine = Path(self.tmp.name)
        self.write("src/data/region_map/region_map_sections.json", {"map_sections": [
            {"id": "MAPSEC_ROUTE_101", "name": "ROUTE 101"},
            {"id": "MAPSEC_BATTLE_FRONTIER", "name": "BATTLE FRONTIER"},
            {"id": "MAPSEC_UNUSED_CAVE", "name": "UNUSED CAVE"},
            {"id": "MAPSEC_SALTMERE", "name": "SALTMERE"},
        ]})
        self.write("data/maps/map_groups.json", {
            "group_order": ["gMapGroup_Upstream", "gMapGroup_AveronOpening"],
            "gMapGroup_Upstream": ["Route101", "Frontier"],
            "gMapGroup_AveronOpening": ["Saltmere", "SaltmereHome"],
        })
        for name, section in (("Route101", "MAPSEC_ROUTE_101"), ("Frontier", "MAPSEC_BATTLE_FRONTIER"),
                              ("Saltmere", "MAPSEC_SALTMERE"), ("SaltmereHome", "MAPSEC_SALTMERE")):
            self.write(f"data/maps/{name}/map.json", {"id": f"MAP_{name.upper()}",
                                                       "region_map_section": section})
        # Lookup-table use only, behavioural use, and the generated header.
        self.text("src/map_name_popup.c", "[MAPSEC_ROUTE_101] = THEME, [MAPSEC_UNUSED_CAVE] = THEME,")
        self.text("src/data/region_map/region_map_layout.h", "MAPSEC_SALTMERE, MAPSEC_UNUSED_CAVE")
        self.text("src/frontier_util.c", "if (mapsec == MAPSEC_BATTLE_FRONTIER) return TRUE;")
        self.text("include/constants/region_map_sections.h", "MAPSEC_ROUTE_101, MAPSEC_BATTLE_FRONTIER")

    def write(self, rel, data):
        self.text(rel, json.dumps(data))

    def text(self, rel, body):
        path = self.engine / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    def rows(self, report):
        return {row["id"]: row for row in report["rows"]}


class MapsecNamespaceTests(Fixture):
    def test_values_follow_json_order_and_capacity(self):
        report = audit.inventory(self.engine)
        rows = self.rows(report)
        self.assertEqual([rows[k]["value"] for k in ("MAPSEC_ROUTE_101", "MAPSEC_SALTMERE")], [0, 3])
        self.assertEqual(report["mapsec_none"], 4)
        self.assertEqual(report["spare_codes_before_reserved"], 0xFD - 4 - 1)
        self.assertEqual(set(report["reserved_met_codes"]), {"0xFD", "0xFE", "0xFF"})

    def test_averon_use_and_reuse_candidates(self):
        report = audit.inventory(self.engine)
        rows = self.rows(report)
        self.assertEqual(report["averon_sections"], ["MAPSEC_SALTMERE"])
        self.assertEqual(rows["MAPSEC_SALTMERE"]["averon_maps"], ["Saltmere", "SaltmereHome"])
        self.assertTrue(rows["MAPSEC_SALTMERE"]["saved_by_averon"])
        self.assertFalse(rows["MAPSEC_SALTMERE"]["reuse_candidate"])  # old saves hold this value
        # Upstream map only and lookup-table use only: a candidate, not a decision.
        self.assertTrue(rows["MAPSEC_ROUTE_101"]["reuse_candidate"])
        self.assertEqual(rows["MAPSEC_ROUTE_101"]["upstream_map_count"], 1)
        self.assertEqual(rows["MAPSEC_ROUTE_101"]["table_files"], ["src/map_name_popup.c"])
        # Behavioural code names it: never a candidate.
        self.assertEqual(rows["MAPSEC_BATTLE_FRONTIER"]["behaviour_files"], ["src/frontier_util.c"])
        self.assertFalse(rows["MAPSEC_BATTLE_FRONTIER"]["reuse_candidate"])
        self.assertTrue(rows["MAPSEC_UNUSED_CAVE"]["reuse_candidate"])
        self.assertEqual(report["unassigned_sections"], 1)
        self.assertEqual(report["reuse_candidates"], 2)

    def test_generated_header_and_definitions_are_not_references(self):
        rows = self.rows(audit.inventory(self.engine))
        for row in rows.values():
            self.assertNotIn("include/constants/region_map_sections.h", row["behaviour_files"])

    def test_unknown_section_on_a_map_is_reported_and_fails(self):
        self.write("data/maps/Bad/map.json", {"id": "MAP_BAD", "region_map_section": "MAPSEC_TYPO"})
        report = audit.inventory(self.engine)
        self.assertEqual(report["unknown_map_sections"], ["MAPSEC_TYPO"])
        self.assertEqual(audit.main(["--engine", str(self.engine)]), 1)

    def test_duplicate_section_ids_are_refused(self):
        self.write("src/data/region_map/region_map_sections.json", {"map_sections": [
            {"id": "MAPSEC_A"}, {"id": "MAPSEC_A"}]})
        with self.assertRaises(ValueError):
            audit.inventory(self.engine)


class SavedValuePinTests(Fixture):
    def test_pins_hold_and_a_shift_is_caught(self):
        self.assertEqual(audit.check_pins(self.engine, {"MAPSEC_SALTMERE": 3}), [])
        # Inserting a section before Saltmere moves its saved value.
        self.write("src/data/region_map/region_map_sections.json", {"map_sections": [
            {"id": "MAPSEC_NEW"}, {"id": "MAPSEC_ROUTE_101"}, {"id": "MAPSEC_BATTLE_FRONTIER"},
            {"id": "MAPSEC_UNUSED_CAVE"}, {"id": "MAPSEC_SALTMERE"}]})
        self.assertEqual(audit.check_pins(self.engine, {"MAPSEC_SALTMERE": 3}),
                         ["MAPSEC_SALTMERE: pinned 3, now 4"])
        self.assertEqual(audit.check_pins(self.engine, {"MAPSEC_GONE": 1}),
                         ["MAPSEC_GONE: pinned 1, now missing"])

    def test_namespace_must_stay_below_reserved_codes(self):
        self.write("src/data/region_map/region_map_sections.json", {"map_sections": [
            {"id": f"MAPSEC_S{i}"} for i in range(0xFD)]})
        errors = audit.check_pins(self.engine, {})
        self.assertEqual(len(errors), 1)
        self.assertIn("0xFD", errors[0])

    def test_cli_exit_codes(self):
        pins = self.engine / "pins.json"
        pins.write_text(json.dumps({"pins": {"MAPSEC_SALTMERE": 3}}))
        self.assertEqual(audit.main(["--engine", str(self.engine), "--check-pins", str(pins)]), 0)
        pins.write_text(json.dumps({"pins": {"MAPSEC_SALTMERE": 2}}))
        self.assertEqual(audit.main(["--engine", str(self.engine), "--check-pins", str(pins)]), 1)


class RepositoryPinTests(unittest.TestCase):
    def test_current_engine_keeps_every_saved_value(self):
        engine = SCRIPT.resolve().parents[1] / "engine"
        pins = json.loads(SCRIPT.with_name("averon-mapsec-pins.json").read_text())["pins"]
        self.assertEqual(audit.check_pins(engine, pins), [])


if __name__ == "__main__":
    unittest.main()
