"""Test that level economy reports source data without inventing player EXP."""
import importlib.util
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "audit-averon-level-economy.py"
spec = importlib.util.spec_from_file_location("averon_level_economy", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class EconomyTests(unittest.TestCase):
    def test_trainerproc_party_blocks_and_held_item(self):
        text = """
=== TRAINER_AVERON_ELIO ===
Name: ELIO
Class: Leader
Pic: Leader Norman
Gender: Male

Bunnelby
Level: 12
IVs: 15 HP / 15 Atk / 15 Def

Lillipup @ Oran Berry
Level: 15
- Work Up

=== TRAINER_OTHER ===
Name: SALLY
Class: Youngster

Rattata
Level: 10
"""
        rows = mod.parse_party_data(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["trainer"], "TRAINER_AVERON_ELIO")
        self.assertEqual(rows[0]["name"], "ELIO")
        self.assertEqual(rows[0]["pokemon"], [
            {"species": "Bunnelby", "level": 12, "default_level": False},
            {"species": "Lillipup", "level": 15, "default_level": False}])

    def test_missing_level_is_explicitly_defaulted(self):
        text = "=== TRAINER_AVERON_X ===\nName: X\n\nBulbasaur\n- Tackle\n"
        rows = mod.parse_party_data(text)
        self.assertEqual(rows[0]["pokemon"][0]["level"], 100)
        self.assertTrue(rows[0]["pokemon"][0]["default_level"])

    def test_source_species_nested_braces(self):
        text = """
/* [SPECIES_COMMENT] = { .speciesName = _("Fake"), }, */
[SPECIES_BULBASAUR] = {
    .speciesName = _("Bulbasaur"),
    .expYield = 64,
    .growthRate = GROWTH_MEDIUM_SLOW,
    .abilities = { ABILITY_OVERGROW, ABILITY_NONE },
},
"""
        records = list(mod.species_initializers(text))
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0][0], "SPECIES_BULBASAUR")
        self.assertIn(".growthRate", records[0][1])

    def test_growth_at_known_milestones(self):
        self.assertEqual(mod.required_experience("GROWTH_MEDIUM_FAST", 50), 125000)
        self.assertEqual(mod.required_experience("GROWTH_FAST", 100), 800000)
        self.assertEqual(mod.required_experience("GROWTH_SLOW", 100), 1250000)
        self.assertEqual(mod.required_experience("GROWTH_MEDIUM_SLOW", 100), 1059860)
        self.assertEqual(mod.required_experience("GROWTH_ERRATIC", 100), 600000)
        self.assertEqual(mod.required_experience("GROWTH_FLUCTUATING", 100), 1640000)

    def test_invalid_growth_group_or_level_raises(self):
        with self.assertRaises(ValueError):
            mod.required_experience("UNKNOWN", 50)
        with self.assertRaises(ValueError):
            mod.required_experience("GROWTH_FAST", 101)


if __name__ == "__main__":
    unittest.main()
