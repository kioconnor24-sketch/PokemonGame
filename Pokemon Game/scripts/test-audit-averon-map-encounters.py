"""Tests for the scoped Averon wild-encounter source audit."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("audit-averon-map-encounters.py")
SPEC = importlib.util.spec_from_file_location("map_encounter_audit", SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class MapEncounterAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        self.engine = self.project / "engine"
        self.write("data/maps/map_groups.json", {
            "group_order": ["gMapGroup_AveronOpening", "gMapGroup_Upstream"],
            "gMapGroup_AveronOpening": ["Saltmere", "CoastalMeadow", "House"],
            "gMapGroup_Upstream": ["Route101"],
        })
        for name, ident, type_ in [
            ("Saltmere", "MAP_SALTMERE", "MAP_TYPE_TOWN"),
            ("CoastalMeadow", "MAP_COASTALMEADOW", "MAP_TYPE_ROUTE"),
            ("House", "MAP_HOUSE", "MAP_TYPE_INDOOR"),
        ]:
            self.write(f"data/maps/{name}/map.json", {"id": ident, "map_type": type_})
        self.write("src/data/wild_encounters.json", {
            "wild_encounter_groups": [{"encounters": [
                {"map": "MAP_COASTALMEADOW", "land_mons": {"mons": [
                    {"min_level": 2, "max_level": 3, "species": "SPECIES_FLETCHLING"},
                    {"min_level": 3, "max_level": 4, "species": "SPECIES_BUNNELBY"},
                    {"min_level": 4, "max_level": 5, "species": "SPECIES_FLETCHLING"},
                ]}},
                {"map": "MAP_ROUTE101", "land_mons": {"mons": [{"species": "SPECIES_ZIGZAGOON"}]}},
                {"map": "MAP_SALTMERE", "water_mons": {"mons": [{"species": "SPECIES_MAGIKARP"}]}},
                {"map": "MAP_HOUSE", "fishing_mons": {}},
                {"map": "MAP_COASTALMEADOW", "fishing_mons": {"mons": [{"species": "SPECIES_MAGIKARP"}]}},
            ]}]})

    def write(self, relative_path, value):
        path = self.engine / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_only_registered_averon_maps_are_counted(self):
        report = audit.create_report(self.engine)
        self.assertEqual(report["registered_map_count"], 3)
        self.assertEqual(report["maps_with_wild_species"], 2)
        self.assertEqual(report["unique_species_references"], 3)
        by_map = {x["directory"]: x for x in report["map_records"]}
        self.assertEqual(by_map["CoastalMeadow"]["species_slot_counts"], {
            "SPECIES_BUNNELBY": 1, "SPECIES_FLETCHLING": 2, "SPECIES_MAGIKARP": 1
        })
        self.assertEqual(by_map["CoastalMeadow"]["wild_record_count"], 2)
        self.assertEqual(by_map["Saltmere"]["encounter_slot_references"], 1)
        self.assertEqual(by_map["House"]["wild_record_count"], 1)
        self.assertEqual(report["maps_with_wild_records_but_no_literal_species"], ["MAP_HOUSE"])
        self.assertNotIn("SPECIES_ZIGZAGOON", str(report))
        self.assertIn("NOT confirmed", report["interpretation"])

    def test_missing_group_is_explicit_failure(self):
        with self.assertRaisesRegex(ValueError, "No nonempty registered map group"):
            audit.create_report(self.engine, "gMapGroup_Missing")

    def test_duplicate_map_ids_are_rejected(self):
        self.write("data/maps/House/map.json", {"id": "MAP_SALTMERE"})
        with self.assertRaisesRegex(ValueError, "Duplicate map ID"):
            audit.create_report(self.engine)

    def test_irrelevant_species_text_does_not_become_encounter(self):
        self.assertEqual(audit.referenced_species({"description": "SPECIES_FAKE", "script": "SPECIES_OTHER", "data": {"species": "something"}}), {})

    def test_cli_json_output(self):
        output = self.project / "reports/map-report.json"
        rc = audit.main(["--project", str(self.project), "--json-out", str(output)])
        self.assertEqual(rc, 0)
        saved = json.loads(output.read_text())
        self.assertEqual(saved["registered_map_count"], 3)


if __name__ == "__main__":
    unittest.main()
