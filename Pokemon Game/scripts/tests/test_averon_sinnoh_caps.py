"""Regression tests for post-Averon, Sinnoh and final Red level caps."""
import importlib.util
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "install-averon-sinnoh-caps.py"
spec = importlib.util.spec_from_file_location("averon_sinnoh_caps", FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class SinnohCapTests(unittest.TestCase):
    def base_flags(self):
        return "\n".join(
            f"#define FLAG_UNUSED_0x{num:03X} 0x{num:02X} // Unused Flag"
            for num, _, _ in mod.CAP_STAGES
        ) + "\n"

    def test_safe_flag_reservation_idempotent(self):
        modified = mod.flags_edit(self.base_flags())
        self.assertEqual(mod.flags_edit(modified), modified)
        self.assertEqual(modified.count("FLAG_AVERON_SINNOH_BADGE"), 8)
        self.assertIn("FLAG_AVERON_RED_ACCESS", modified)

    def test_does_not_steal_claimed_flags(self):
        source = self.base_flags().replace(
            "FLAG_UNUSED_0x030", "FLAG_SOME_OTHER_0x030"
        )
        with self.assertRaisesRegex(ValueError, "occupied or unavailable"):
            mod.flags_edit(source)

    def test_cap_source_extension_idempotent(self):
        source = ("void f(void) {\n"
                  "        {FLAG_IS_CHAMPION, 76},\n"
                  "    };\n}\n")
        updated = mod.caps_edit(source)
        self.assertEqual(mod.caps_edit(updated), updated)
        self.assertTrue(mod.verify_caps(updated))
        self.assertLess(updated.index("FLAG_IS_CHAMPION"), updated.index("FLAG_AVERON_SINNOH_BADGE01"))
        self.assertLess(updated.index("FLAG_AVERON_SINNOH_CHAMPION"), updated.index("FLAG_AVERON_RED_ACCESS"))

    def test_progression_through_red(self):
        earlier = ["FLAG_BADGE01_GET", "FLAG_BADGE02_GET",
                   "FLAG_BADGE03_GET", "FLAG_BADGE04_GET",
                   "FLAG_BADGE05_GET", "FLAG_BADGE06_GET",
                   "FLAG_BADGE07_GET", "FLAG_BADGE08_GET",
                   "FLAG_AVERON_ASSAULT_COMPLETE", "FLAG_IS_CHAMPION"]
        self.assertEqual(mod.stage_cap(set()), 15)
        state = set(earlier)
        self.assertEqual(mod.stage_cap(state), 79)
        for _, name, expected in mod.CAP_STAGES:
            self.assertEqual(mod.stage_cap(state), expected)
            state.add(name)
        self.assertEqual(mod.stage_cap(state), 100)

    def test_cap_rejects_partial_insertion(self):
        partial = ("        {FLAG_IS_CHAMPION, 76},\n"
                   "        {FLAG_AVERON_SINNOH_BADGE01, 79},\n")
        with self.assertRaisesRegex(ValueError, "Partial"):
            mod.caps_edit(partial)


if __name__ == "__main__":
    unittest.main()
