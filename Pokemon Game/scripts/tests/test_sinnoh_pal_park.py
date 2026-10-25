"""W6 Pal Park staging: reproducible, attested words, reachable gate door and beach, reciprocal Route 221 pair."""
import importlib.util
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/pal-park"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("pal_park", HERE / "build_pal_park.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
ti = importlib.util.spec_from_file_location("w1_tests", ROOT / "scripts/tests/test_sinnoh_iron_island.py")
t = importlib.util.module_from_spec(ti)
ti.loader.exec_module(t)


class PalParkTest(unittest.TestCase):
    def setUp(self):
        self.eng, self.cells, self.hdr, self.r221, self.door, self.gate = b.build(ENGINE)

    def test_staged_matches_fresh_build(self):
        self.assertEqual((HERE / "staged/PalPark/map.bin").read_bytes(), struct.pack("<%dH" % len(self.cells), *self.cells))
        self.assertEqual(json.loads((HERE / "staged/PalPark/map.json").read_text()), self.hdr)
        self.assertEqual(json.loads((HERE / "staged/Route221-dev-overlay/map.json").read_text()), self.r221)

    def test_every_word_exists_in_source_layouts(self):
        known = set()
        for n in b.w1.OCEAN_CORPUS + ("LakeVerity",):
            known |= set(self.eng.cells(n)[2])
        self.assertFalse(set(self.cells) - known)

    def test_unattested_pond_refused(self):
        old = b.POND
        try:
            b.POND = (22, 9, 22, 16)               # one tile wide: never drawn in Lake Verity
            with self.assertRaisesRegex(SystemExit, "unattested pond pattern"):
                b.build(ENGINE)
        finally:
            b.POND = old

    def test_door_reachable_closed_edges_and_reciprocal_pair(self):
        beh = t.behaviours("general", "dewford")
        x, y = self.door
        got = t.reach(self.cells, b.W, beh, (x, y + 1))
        self.assertIn((20, b.SAND_TOP + 1), got)                                   # walk to the beach
        self.assertFalse({p for p in got if p[0] in (0, b.W - 1) or p[1] in (0, b.H - 1)})
        # Route 221 door -> gate mats 0/1; gate mats 2/3 -> park door; park door -> gate mat 2.
        self.assertEqual(self.r221["warp_events"], [{"x": 82, "y": 15, "elevation": 0, "dest_map": "MAP_PAL_PARK_GATE",
                                                     "dest_warp_id": "0"}])
        g = self.gate["warp_events"]
        self.assertEqual([(w["dest_map"], w["dest_warp_id"]) for w in g],
                         [("MAP_ROUTE221", "0")] * 2 + [("MAP_PAL_PARK", "0")] * 2)
        self.assertEqual((self.hdr["warp_events"][0]["dest_map"], self.hdr["warp_events"][0]["dest_warp_id"]),
                         ("MAP_PAL_PARK_GATE", "2"))


if __name__ == "__main__":
    unittest.main()
