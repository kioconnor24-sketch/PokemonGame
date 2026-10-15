"""Fixture tests for Averon source inventory; no game engine or emulator required."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).with_name("audit-averon-species.py")
spec = importlib.util.spec_from_file_location("species_audit", SOURCE)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class SpeciesAuditTests(unittest.TestCase):
    def test_inventory_reports_definitions_and_references_without_claiming_obtainability(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = {
                "include/constants/species.h": "enum __attribute__((packed)) Species {\n SPECIES_NONE = 0,\n SPECIES_SPRIGATITO = 1,\n SPECIES_FLORAGATO = 2,\n SPECIES_EGG,\n};\n",
                "include/config/species_enabled.h": "#define P_GEN_1_POKEMON TRUE\n#define P_GEN_9_POKEMON FALSE\n",
                "src/data/wild_encounters.json": json.dumps({"groups": [{"map": "MAP_TEST", "mons": [{"species": "SPECIES_SPRIGATITO"}, {"species": "SPECIES_SPRIGATITO"}, {"species": "SPECIES_UNKNOWN"}]}]}),
            }
            for number in range(1, 10):
                paths[f"src/data/pokemon/species_info/gen_{number}_families.h"] = "[SPECIES_SPRIGATITO] = {}" if number == 9 else ""
            for path, contents in paths.items():
                target = root / "engine" / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(contents, encoding="utf-8")
            habitat = root / "Averon_Codex_Handoff/data/habitat_examples.csv"
            habitat.parent.mkdir(parents=True, exist_ok=True)
            habitat.write_text('ecology_zone,example_species\nMeadow,"Sprigatito, Floragato"\n', encoding="utf-8")
            report = audit.compile_report(root)
            self.assertEqual(report["declared_species_ids"], 2)
            self.assertEqual(report["species_info_source_entries"], 1)
            self.assertEqual(report["unique_wild_reference_ids"], 2)
            self.assertEqual(report["wild_encounter_slots"], 3)
            self.assertEqual(report["wild_references_without_species_info"], ["SPECIES_UNKNOWN"])
            self.assertEqual(report["generation_summary"][-1]["family_config"], "FALSE")
            self.assertIn("NOT a complete Pokédex", report["interpretation"])
            self.assertEqual(len(report["habitat_design_examples"]), 2)

    def test_missing_generation_file_fails_instead_of_silently_skipping_data(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "Expected nine generation"):
                audit.info_by_generation(Path(temp))

    def test_enum_parser_does_not_include_other_enums(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "species.h"
            file.write_text("enum Other {\n SPECIES_FAKE,\n};\nenum Species {\n SPECIES_NONE = 0,\n SPECIES_REAL = 1,\n};", encoding="utf-8")
            self.assertEqual(audit.names_in_enum(file), {"SPECIES_REAL"})


if __name__ == "__main__":
    unittest.main()
