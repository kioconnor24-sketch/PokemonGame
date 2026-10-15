"""Fixture tests for the conservative source graphics inventory."""
import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "audit-averon-graphics.py"
spec = importlib.util.spec_from_file_location("averon_graphics_audit", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class GraphicsAuditTests(unittest.TestCase):
    def test_species_and_form_entries(self):
        header = """enum Species {
            SPECIES_NONE = 0,
            SPECIES_BULBASAUR = 1,
            SPECIES_RAICHU_ALOLA,
        };"""
        source = """
        [SPECIES_NONE] = {},
        [SPECIES_BULBASAUR] = {
            .frontPic = gMonFrontPic_Bulbasaur,
            .backPic = gMonBackPic_Bulbasaur,
            .palette = gMonPalette_Bulbasaur,
            .shinyPalette = gMonShinyPalette_Bulbasaur,
            .iconSprite = gMonIcon_Bulbasaur,
            OVERWORLD(gObjPic_Bulbasaur, SIZE_32x32, 0, 0, 0)
        },
        #if P_ALOLAN_FORMS
        [SPECIES_RAICHU_ALOLA] = {
            .frontPic = gMonFrontPic_RaichuAlola,
        },
        #endif
        """
        report = mod.audit(source, header)
        self.assertEqual(report["declared_species_count"], 2)
        self.assertEqual(report["species_entry_count"], 2)
        self.assertEqual(report["declared_without_entry"], [])
        self.assertIn("OVERWORLD", report["rows"][0]["overworld_macro"])
        self.assertIn("No direct assignment", report["rows"][1]["notes"])
        self.assertTrue(all(row["conditional"] for row in report["rows"]))

    def test_nested_initializer_and_comment(self):
        text = """
        // [SPECIES_FAKE] = { },
        [SPECIES_A] = {
            .something = { .inner = { 1, 2 } },
            .frontPic = gFront_A,
        },
        /* [SPECIES_BOGUS] = { }, */
        [SPECIES_B] = { .frontPic = gFront_B },
        """
        report = mod.audit(text, "SPECIES_A,\nSPECIES_B,")
        self.assertEqual([row["species"] for row in report["rows"]],
                         ["SPECIES_A", "SPECIES_B"])

    def test_unclosed_species_entry(self):
        with self.assertRaisesRegex(ValueError, "Unclosed species"):
            list(mod.entries("[SPECIES_X] = { .frontPic = x"))


if __name__ == "__main__":
    unittest.main()
