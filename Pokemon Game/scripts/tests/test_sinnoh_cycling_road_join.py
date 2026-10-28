"""W25 Cycling Road <-> Route 207 seam: staging equals a fresh build; only the matching closures reopen."""
import importlib.util
import json
import pathlib
import struct
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/cycling-road-join"
spec = importlib.util.spec_from_file_location("w25", HERE / "build_cycling_road_join.py")
w25 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w25)


class CyclingRoadJoinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r206, cls.r207, cls.b206, cls.b207, cls.pairs, _ = w25.build()

    def test_committed_staging_equals_a_fresh_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            w25.write(tmp)
            fresh = sorted(p.relative_to(tmp) for p in pathlib.Path(tmp).rglob("*") if p.is_file())
            committed = sorted(p.relative_to(HERE) for p in HERE.rglob("*") if p.is_file() and p.suffix != ".py"
                               and "__pycache__" not in p.parts
                               and p.name not in ("CHECKPOINT.md", "current-runtime-base-pins.json"))
            self.assertEqual(fresh, committed)
            for rel in fresh:
                self.assertEqual((pathlib.Path(tmp) / rel).read_bytes(), (HERE / rel).read_bytes(), rel)

    def test_the_nine_donor_cells_pair_at_offset_minus_two(self):
        self.assertEqual(self.pairs, [((x, 119), (x + 2, 0)) for x in range(11, 20)])

    def test_connections_are_reciprocal_and_only_appended(self):
        src206 = json.loads((w25.R206 / "staged/Route206/map.json").read_text())
        src207 = json.loads(w25.RECIPE.read_text())["source_headers"]["Route207"]
        self.assertEqual(self.r206["connections"], src206["connections"]
                         + [{"map": "MAP_ROUTE207", "offset": -2, "direction": "down"}])
        self.assertEqual(self.r207["connections"], src207["connections"]
                         + [{"map": "MAP_ROUTE206", "offset": 2, "direction": "up"}])
        for new, old in ((self.r206, src206), (self.r207, src207)):
            self.assertEqual({k: v for k, v in new.items() if k != "connections"},
                             {k: v for k, v in old.items() if k != "connections"})

    def test_only_collision_bits_of_the_paired_cells_change(self):
        raw = (w25.R206 / "staged/Route206/averon-map.bin").read_bytes()
        before206 = struct.unpack("<%dH" % (len(raw) // 2), raw)
        changed = [(i % 28, i // 28, a ^ b) for i, (a, b) in enumerate(zip(before206, self.b206)) if a != b]
        self.assertEqual([(x, y) for x, y, _ in changed], [a for a, _ in self.pairs])
        self.assertTrue(all(d == 0x400 for _, _, d in changed))
        top = [(i % 64, i // 64) for i, b in enumerate(self.b207[:64]) if not b & 0xC00]
        self.assertEqual(top, [b for _, b in self.pairs])


if __name__ == "__main__":
    unittest.main()
