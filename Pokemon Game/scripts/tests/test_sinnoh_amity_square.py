"""W11 Amity Square staging: reproducible, attested, connected closed park, reciprocal Hearthome mats."""
import importlib.util
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/amity-square"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("amity", HERE / "build_amity_square.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
ti = importlib.util.spec_from_file_location("w1_tests", ROOT / "scripts/tests/test_sinnoh_iron_island.py")
t = importlib.util.module_from_spec(ti)
ti.loader.exec_module(t)


class AmitySquareTest(unittest.TestCase):
    def setUp(self):
        self.eng, self.cells, self.amity, self.hh, self.doors = b.build(ENGINE)

    def test_staged_matches_fresh_build(self):
        self.assertEqual((HERE / "staged/AmitySquare/map.bin").read_bytes(), struct.pack("<%dH" % len(self.cells), *self.cells))
        self.assertEqual(json.loads((HERE / "staged/AmitySquare/map.json").read_text()), self.amity)
        self.assertEqual(json.loads((HERE / "staged/HearthomeCity-dev-overlay/map.json").read_text()), self.hh)

    def test_words_attested(self):
        known = set(self.eng.cells("LakeVerity")[2]) | set(self.eng.cells("DewfordTown")[2])
        self.assertFalse(set(self.cells) - known)

    def test_both_gates_connected_and_park_closed(self):
        beh = t.behaviours("general", "dewford")
        (wx, wy), (ex, ey) = self.doors["west"], self.doors["east"]
        got = t.reach(self.cells, b.W, beh, (wx, wy + 1))
        self.assertIn((ex, ey + 1), got)
        self.assertFalse({p for p in got if p[0] in (0, b.W - 1) or p[1] in (0, b.H - 1)})

    def test_hearthome_mats_reciprocal(self):
        source = json.loads((b.HEARTHOME / "map.json").read_text())
        n = len(source["warp_events"])
        self.assertEqual(self.hh["warp_events"][:n], source["warp_events"])
        added = self.hh["warp_events"][n:]
        self.assertEqual([(w["x"], w["y"]) for w in added], b.MATS["west"] + b.MATS["east"])
        self.assertEqual([w["dest_warp_id"] for w in added], ["0", "0", "1", "1"])
        aw = self.amity["warp_events"]
        self.assertEqual([(w["dest_map"], int(w["dest_warp_id"])) for w in aw],
                         [("MAP_HEARTHOME_CITY", n), ("MAP_HEARTHOME_CITY", n + 2)])


if __name__ == "__main__":
    unittest.main()
