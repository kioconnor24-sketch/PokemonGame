"""Source evolution audit tests: direct trade and solo alternatives."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "audit-averon-solo-evolutions.py"
spec = importlib.util.spec_from_file_location("solo_evo", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SoloEvolutionsTests(unittest.TestCase):
    def test_alternative_same_destination(self):
        source = """
[SPECIES_HAUNTER] = {
  .evolutions = EVOLUTION(
       {EVO_TRADE, 0, SPECIES_GENGAR},
       {EVO_ITEM, ITEM_LINKING_CORD, SPECIES_GENGAR}),
},
"""
        rows = mod.audit_family("gen_1_families.h", source)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "SOURCE_ALTERNATIVE_FOUND")
        self.assertIn("ITEM_LINKING_CORD", rows[0]["solo_alternatives"])

    def test_condition_in_trade_line_does_not_hide_item(self):
        source = """
[SPECIES_SCYTHER] = {
  .evolutions = EVOLUTION(
       {EVO_TRADE, 0, SPECIES_SCIZOR, CONDITIONS({IF_HOLD_ITEM, ITEM_METAL_COAT})},
       {EVO_ITEM, ITEM_METAL_COAT, SPECIES_SCIZOR}),
},
"""
        rows = mod.audit_family("g.h", source)
        self.assertEqual(rows[0]["status"], "SOURCE_ALTERNATIVE_FOUND")

    def test_other_destination_does_not_count(self):
        source = """
[SPECIES_POLIWHIRL] = {
   .evolutions = EVOLUTION(
     {EVO_TRADE, 0, SPECIES_POLITOED},
     {EVO_ITEM, ITEM_WATER_STONE, SPECIES_POLIWRATH}),
},
"""
        rows = mod.audit_family("g.h", source)
        self.assertEqual(rows[0]["status"], "TRADE_ONLY_SOURCE")

    def test_comments_ignored(self):
        source = """
/* [SPECIES_FAKE] = { .evolutions = EVOLUTION({EVO_TRADE, 0, SPECIES_X})}, */
[SPECIES_TRUE] = {
  .evolutions = EVOLUTION({EVO_TRADE, 0, SPECIES_Z}),
},
"""
        rows = mod.audit_family("g.h", source)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["origin"], "SPECIES_TRUE")

    def test_unknown_family_source_errors(self):
        with self.assertRaises(ValueError):
            list(mod.species_entries("[SPECIES_HAUNTER] = { .x = {"))

if __name__ == "__main__":
    unittest.main()
