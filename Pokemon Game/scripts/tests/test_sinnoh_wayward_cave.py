"""W7 Wayward Cave staging: reproducible, attested kit words, connected closed floors, one-warp Route 206 overlay."""
import importlib.util
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/wayward-cave"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("wayward", HERE / "build_wayward_cave.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
ti = importlib.util.spec_from_file_location("w1_tests", ROOT / "scripts/tests/test_sinnoh_iron_island.py")
t = importlib.util.module_from_spec(ti)
ti.loader.exec_module(t)


class WaywardCaveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng, cls.maps, cls.r206 = b.build(ENGINE)

    def test_staged_matches_fresh_build(self):
        for name, (hdr, cv) in self.maps.items():
            self.assertEqual((HERE / "staged" / name / "map.bin").read_bytes(), struct.pack("<%dH" % len(cv.cells), *cv.cells))
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)
        self.assertEqual(json.loads((HERE / "staged/Route206-dev-overlay/map.json").read_text()), self.r206)

    def test_words_from_cave_corpus(self):
        known = set()
        for n in b.w1.CAVE_CORPUS:
            known |= set(self.eng.cells(n)[2])
        for name, (_, cv) in self.maps.items():
            self.assertFalse(set(cv.cells) - known, name)

    def test_floors_connected_and_closed(self):
        beh = t.behaviours("general", "cave")
        for name, (hdr, cv) in self.maps.items():
            warps = [(w["x"], w["y"]) for w in hdr["warp_events"]]
            got = t.reach(cv.cells, cv.w, beh, warps[0])
            for p in warps:
                self.assertIn(p, got, name)
            self.assertFalse({p for p in got if p[0] in (0, cv.w - 1) or p[1] in (0, cv.h - 1)}, name)

    def test_route206_overlay_appends_one_reciprocal_warp(self):
        source = json.loads((b.ROUTE206 / "map.json").read_text())
        self.assertEqual(self.r206["warp_events"][:-1], source["warp_events"])
        added = self.r206["warp_events"][-1]
        self.assertEqual(((added["x"], added["y"]), added["dest_map"]), (b.MOUTH, "MAP_WAYWARD_CAVE_1F"))
        back = self.maps["WaywardCave_1F"][0]["warp_events"][0]
        self.assertEqual((back["dest_map"], int(back["dest_warp_id"])), ("MAP_ROUTE206", len(source["warp_events"])))


if __name__ == "__main__":
    unittest.main()
