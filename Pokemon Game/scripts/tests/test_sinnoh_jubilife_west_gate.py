"""W27 Jubilife west gate: staging equals a fresh build; the pair is reciprocal; one collision bit per side."""
import importlib.util
import json
import pathlib
import struct
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/jubilife-west-gate"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("w27", HERE / "build_jubilife_west_gate.py")
w27 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w27)


def cells(raw):
    return struct.unpack("<%dH" % (len(raw) // 2), raw)


class JubilifeWestGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jub, cls.gate, cls.jb, cls.gb, _ = w27.build(ENGINE)

    def test_committed_staging_equals_a_fresh_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            w27.write(ENGINE, tmp)
            fresh = sorted(p.relative_to(tmp) for p in pathlib.Path(tmp).rglob("*") if p.is_file())
            committed = sorted(p.relative_to(HERE) for p in HERE.rglob("*") if p.is_file() and p.suffix != ".py"
                               and "__pycache__" not in p.parts)
            self.assertEqual(fresh, committed)
            for rel in fresh:
                self.assertEqual((pathlib.Path(tmp) / rel).read_bytes(), (HERE / rel).read_bytes(), rel)

    def test_pair_is_reciprocal(self):
        a, b = self.jub["warp_events"][-1], self.gate["warp_events"][-1]
        self.assertEqual((a["x"], a["y"], a["dest_map"]), (4, 20, "MAP_ROUTE218_EAST"))
        self.assertEqual((b["x"], b["y"], b["dest_map"]), (11, 5, "MAP_JUBILIFE_CITY"))
        self.assertEqual(self.gate["warp_events"][int(a["dest_warp_id"])], b)
        self.assertEqual(self.jub["warp_events"][int(b["dest_warp_id"])], a)

    def test_headers_only_gain_one_warp(self):
        for new, path in ((self.jub, ENGINE / "data/maps/JubilifeCity/map.json"),
                          (self.gate, w27.CANALAVE / "staged/Route218_East/map.json")):
            old = json.loads(path.read_text())
            self.assertEqual(new["warp_events"][:-1], old["warp_events"])
            self.assertEqual({k: v for k, v in new.items() if k != "warp_events"},
                             {k: v for k, v in old.items() if k != "warp_events"})

    def test_one_collision_bit_per_side(self):
        for blocks, path, width, xy in ((self.jb, ENGINE / "data/layouts/JubilifeCity/map.bin", 70, (4, 20)),
                                        (self.gb, w27.CANALAVE / "staged/Route218_East/averon-map.bin", 13, (11, 5))):
            before = cells(path.read_bytes())
            changed = [((i % width, i // width), a ^ b) for i, (a, b) in enumerate(zip(before, blocks)) if a != b]
            self.assertEqual(changed, [(xy, 0x400)])


if __name__ == "__main__":
    unittest.main()
