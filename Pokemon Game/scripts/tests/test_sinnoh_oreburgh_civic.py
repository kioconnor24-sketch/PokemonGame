"""W21 Oreburgh civic shells: committed staging equals a fresh build; warps reciprocal; the Gym stays closed."""
import importlib.util
import json
import pathlib
import struct
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/oreburgh-civic"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("w21", HERE / "build_oreburgh_civic.py")
w21 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w21)


class OreburghCivicTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hdr, cls.maps, cls.blocks, cls.hashes = w21.build(ENGINE)

    def test_committed_staging_equals_a_fresh_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            w21.write(ENGINE, tmp)
            fresh = sorted(p.relative_to(tmp) for p in pathlib.Path(tmp).rglob("*") if p.is_file())
            committed = sorted(p.relative_to(HERE) for p in HERE.rglob("*") if p.is_file() and p.suffix != ".py"
                               and "__pycache__" not in p.parts and p.name != "CHECKPOINT.md")
            self.assertEqual(fresh, committed)
            for rel in fresh:
                self.assertEqual((pathlib.Path(tmp) / rel).read_bytes(), (HERE / rel).read_bytes(), rel)

    def test_codex_city_events_are_kept_and_doors_appended(self):
        source = json.loads(w21.RECIPE.read_text())["source_headers"]["OreburghCity"]
        n = len(source["warp_events"])
        self.assertEqual(self.hdr["warp_events"][:n], source["warp_events"])
        added = {(w["x"], w["y"]) for w in self.hdr["warp_events"][n:]}
        self.assertEqual(len(added), 10)
        self.assertNotIn((30, 22), added)
        self.assertEqual({k: v for k, v in self.hdr.items() if k != "warp_events"},
                         {k: v for k, v in source.items() if k != "warp_events"})

    def test_every_warp_is_reciprocal(self):
        self.assertTrue(w21.check(self.hdr, self.maps))

    def test_new_maps_are_neutral(self):
        self.assertEqual(len(self.maps), 10)
        for h in self.maps.values():
            self.assertEqual((h["object_events"], h["coord_events"], h["bg_events"]), ([], [], []))
            self.assertEqual(h["region_map_section"], "MAPSEC_PENDING_OWNER")
            self.assertFalse(any(w["dest_map"].startswith("MAP_LILYCOVE") or w["dest_map"].startswith("MAP_OLDALE")
                                 for w in h["warp_events"]), h["id"])

    def test_only_the_museum_door_collision_changes(self):
        raw = (w21.FAMILY / "OreburghCity/map.bin").read_bytes()
        cells = struct.unpack("<%dH" % (len(raw) // 2), raw)
        changed = [(i % 70, i // 70, a ^ b) for i, (a, b) in enumerate(zip(cells, self.blocks)) if a != b]
        self.assertEqual(len(changed), 1)
        x, y, delta = changed[0]
        self.assertEqual((x, y), (54, 14))
        self.assertEqual(delta & ~0xC00, 0)

    def test_a_door_cell_with_a_wall_doorstep_is_refused(self):
        cells = list(self.blocks)
        cells[23 * 70 + 51] |= 0x400                        # the Center's doorstep
        hdr, _, attrs, _ = w21.inputs()
        orig = w21.inputs
        try:
            w21.inputs = lambda: (json.loads(json.dumps(hdr)), cells, attrs, {})
            with self.assertRaises(AssertionError):
                w21.build(ENGINE)
        finally:
            w21.inputs = orig


if __name__ == "__main__":
    unittest.main()
