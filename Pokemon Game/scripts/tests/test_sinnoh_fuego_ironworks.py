"""W3 Fuego Ironworks staging: reproducible, attested words, closed edges, reachable ironworks door."""
import importlib.util
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/fuego-ironworks"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("fuego_builder", HERE / "build_fuego.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
ti = importlib.util.spec_from_file_location("w1_tests", ROOT / "scripts/tests/test_sinnoh_iron_island.py")
t = importlib.util.module_from_spec(ti)
ti.loader.exec_module(t)


class FuegoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng, cls.maps = b.build(ENGINE)

    def test_staged_files_match_a_fresh_build(self):
        cells = self.maps["FuegoIronworks"][1][0]
        self.assertEqual((HERE / "staged/FuegoIronworks/map.bin").read_bytes(), struct.pack("<%dH" % len(cells), *cells))
        for name, (hdr, _) in self.maps.items():
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)

    def test_every_cell_word_is_an_existing_averon_cell(self):
        known = set()
        for n in b.w1.OCEAN_CORPUS + ("LakeVerity", "SlateportCity"):
            known |= set(self.eng.cells(n)[2])
        self.assertFalse(set(self.maps["FuegoIronworks"][1][0]) - known)

    def test_unattested_shore_is_refused(self):
        old = dict(b.LAND)
        try:
            b.LAND[3] = (7, 27)
            with self.assertRaisesRegex(SystemExit, "unattested shore pattern"):
                b.outdoor(self.eng)
        finally:
            b.LAND.clear()
            b.LAND.update(old)

    def test_door_reachable_edges_closed_and_warps_reciprocal(self):
        cells, w = self.maps["FuegoIronworks"][1][0], b.W
        beh = t.behaviours("general", "slateport")
        door = self.maps["FuegoIronworks"][0]["warp_events"][0]
        self.assertIn(beh[cells[door["y"] * w + door["x"]] & 1023], ("MB_ANIMATED_DOOR", "MB_NON_ANIMATED_DOOR"))
        got = t.reach(cells, w, beh, (door["x"], door["y"] + 1))
        self.assertGreater(len(got), 300)
        self.assertFalse({(x, y) for x, y in got if x in (0, w - 1) or y in (0, b.H - 1)})
        inside = self.maps["FuegoIronworks_Inside"][0]["warp_events"]
        self.assertEqual({(e["dest_map"], e["dest_warp_id"]) for e in inside}, {("MAP_FUEGO_IRONWORKS", "0")})
        self.assertEqual(door["dest_map"], "MAP_FUEGO_IRONWORKS_INSIDE")


if __name__ == "__main__":
    unittest.main()
