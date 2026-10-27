"""W4 Verity Cavern staging: reproducible, one-cell DEV overlay of Lake Verity, reachable reciprocal exit."""
import importlib.util
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/verity-cavern"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("verity_cavern", HERE / "build_verity_cavern.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
ti = importlib.util.spec_from_file_location("w1_tests", ROOT / "scripts/tests/test_sinnoh_iron_island.py")
t = importlib.util.module_from_spec(ti)
ti.loader.exec_module(t)


class VerityCavernTest(unittest.TestCase):
    def setUp(self):
        self.eng, self.hdr, self.cv, self.lake, self.lake_hdr = b.build(ENGINE)

    def test_staged_matches_fresh_build(self):
        self.assertEqual((HERE / "staged/VerityCavern/map.bin").read_bytes(), struct.pack("<%dH" % len(self.cv.cells), *self.cv.cells))
        self.assertEqual(json.loads((HERE / "staged/VerityCavern/map.json").read_text()), self.hdr)

    def test_lake_overlay_changes_only_the_mouth_collision(self):
        _, _, orig = self.eng.cells("LakeVerity")
        diff = [i for i, (a, c) in enumerate(zip(orig, self.lake)) if a != c]
        self.assertEqual(diff, [b.MOUTH[1] * 48 + b.MOUTH[0]])
        self.assertEqual(orig[diff[0]] & 0xF3FF, self.lake[diff[0]])
        self.assertEqual(self.lake_hdr["warp_events"][2]["dest_map"], "MAP_VERITY_CAVERN")
        self.assertEqual(self.hdr["warp_events"][0]["dest_warp_id"], "2")

    def test_exit_reachable_and_room_closed(self):
        beh = t.behaviours("general", "cave")
        got = t.reach(self.cv.cells, self.cv.w, beh, b.EXIT)
        self.assertGreater(len(got), 80)
        self.assertFalse({(x, y) for x, y in got if x in (0, self.cv.w - 1) or y in (0, self.cv.h - 1)})


if __name__ == "__main__":
    unittest.main()
