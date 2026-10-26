"""W23 Eterna Forest south gate: staging equals a fresh build; warps reciprocal; only the two mouth cells open."""
import importlib.util
import json
import pathlib
import struct
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/eterna-forest-gate"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("w23", HERE / "build_eterna_forest_gate.py")
w23 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w23)


class EternaForestGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.route, cls.forest, cls.gate, cls.blocks, cls.hashes = w23.build(ENGINE)

    def test_committed_staging_equals_a_fresh_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            w23.write(ENGINE, tmp)
            fresh = sorted(p.relative_to(tmp) for p in pathlib.Path(tmp).rglob("*") if p.is_file())
            committed = sorted(p.relative_to(HERE) for p in HERE.rglob("*") if p.is_file() and p.suffix != ".py"
                               and "__pycache__" not in p.parts and p.name != "CHECKPOINT.md")
            self.assertEqual(fresh, committed)
            for rel in fresh:
                self.assertEqual((pathlib.Path(tmp) / rel).read_bytes(), (HERE / rel).read_bytes(), rel)

    def test_sources_only_gain_appended_warps(self):
        route = json.loads((ENGINE / "data/maps/Route205_South/map.json").read_text())
        forest = json.loads((w23.FOREST / "staged/EternaForest/map.json").read_text())
        for new, old, added in ((self.route, route, 1), (self.forest, forest, 2)):
            self.assertEqual(new["warp_events"][:len(old["warp_events"])], old["warp_events"])
            self.assertEqual(len(new["warp_events"]) - len(old["warp_events"]), added)
            self.assertEqual({k: v for k, v in new.items() if k != "warp_events"},
                             {k: v for k, v in old.items() if k != "warp_events"})

    def test_every_warp_is_reciprocal(self):
        self.assertTrue(w23.check(self.route, self.forest, self.gate))

    def test_gate_is_neutral_stock_layout(self):
        self.assertEqual(self.gate["layout"], "LAYOUT_ROUTE114_FOSSIL_MANIACS_HOUSE")
        self.assertEqual((self.gate["object_events"], self.gate["coord_events"], self.gate["bg_events"]), ([], [], []))
        self.assertEqual(self.gate["region_map_section"], "MAPSEC_PENDING_OWNER")

    def test_only_the_two_mouth_cells_open(self):
        raw = (w23.FOREST / "staged/EternaForest/averon-map.bin").read_bytes()
        cells = struct.unpack("<%dH" % (len(raw) // 2), raw)
        changed = [(i % 82, i // 82, a ^ b) for i, (a, b) in enumerate(zip(cells, self.blocks)) if a != b]
        self.assertEqual([(x, y) for x, y, _ in changed], [(16, 80), (17, 80)])
        self.assertTrue(all(delta & ~0xC00 == 0 for _, _, delta in changed))

    def test_an_already_warped_route_door_is_refused(self):
        route = ENGINE / "data/maps/Route205_South/map.json"
        original = route.read_bytes()
        try:
            hdr = json.loads(original)
            hdr["warp_events"].append({"x": 21, "y": 22, "elevation": 0, "dest_map": "MAP_FLOAROMA_TOWN",
                                       "dest_warp_id": "0"})
            route.write_text(json.dumps(hdr, indent=2) + "\n")
            with self.assertRaises(AssertionError):
                w23.build(ENGINE)
        finally:
            route.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
