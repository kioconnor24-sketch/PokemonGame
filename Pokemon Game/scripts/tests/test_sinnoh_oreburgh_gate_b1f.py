"""W16 Oreburgh Gate B1F: one ladder cell added to production 1F, reciprocal, B1F connected and closed."""
import importlib.util
import json
import pathlib
import struct
import unittest
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/oreburgh-gate-b1f"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("oreburgh_gate_b1f", HERE / "build_oreburgh_gate_b1f.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def reach(cells, width, start):
    height = len(cells) // width
    seen, todo = {start}, deque([start])
    while todo:
        x, y = todo.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and 0 <= n[0] < width and 0 <= n[1] < height and not cells[n[1] * width + n[0]] & 0xC00:
                seen.add(n)
                todo.append(n)
    return seen


class OreburghGateB1FTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng, cls.gate, cls.blocks, cls.hdr, cls.cv = b.build(ENGINE)
        cls.source = json.loads((ENGINE / "data/maps/OreburghGate_1F/map.json").read_text())

    def test_staged_files_match_a_fresh_build(self):
        st = HERE / "staged"
        self.assertEqual(json.loads((st / "OreburghGate_1F-dev-overlay/map.json").read_text()), self.gate)
        self.assertEqual((st / "OreburghGate_1F-dev-overlay/map.bin").read_bytes(),
                         struct.pack("<%dH" % len(self.blocks), *self.blocks))
        self.assertEqual(json.loads((st / "OreburghGate_B1F/map.json").read_text()), self.hdr)
        self.assertEqual((st / "OreburghGate_B1F/map.bin").read_bytes(), struct.pack("<%dH" % len(self.cv.cells),
                                                                                     *self.cv.cells))

    def test_1f_changes_one_cell_and_appends_one_warp(self):
        width, _, cells = self.eng.cells("OreburghGate_1F")
        changed = [(i % width, i // width) for i, (a, c) in enumerate(zip(cells, self.blocks)) if a != c]
        self.assertEqual(changed, [b.LADDER_1F])
        self.assertEqual(self.gate["warp_events"][:-1], self.source["warp_events"])
        self.assertEqual({k: v for k, v in self.gate.items() if k != "warp_events"},
                         {k: v for k, v in self.source.items() if k != "warp_events"})
        # The alcove ladder is reachable on foot from the Route 203 exit.
        exit_ = (self.source["warp_events"][0]["x"], self.source["warp_events"][0]["y"])
        self.assertIn(b.LADDER_1F, reach(self.blocks, width, exit_))

    def test_ladders_are_reciprocal(self):
        down = self.gate["warp_events"][-1]
        up = self.hdr["warp_events"][int(down["dest_warp_id"])]
        self.assertEqual((down["dest_map"], up["dest_map"]), ("MAP_OREBURGH_GATE_B1F", "MAP_OREBURGH_GATE_1F"))
        self.assertEqual(int(up["dest_warp_id"]), len(self.gate["warp_events"]) - 1)

    def test_b1f_is_one_closed_region(self):
        cells, w, h = self.cv.cells, self.cv.w, self.cv.h
        got = reach(cells, w, b.b1f(self.eng)[1])
        self.assertEqual(got, {(i % w, i // w) for i, v in enumerate(cells) if not v & 0xC00})   # no stranded floor
        self.assertFalse({(x, y) for x, y in got if x in (0, w - 1) or y in (0, h - 1)})

    def test_a_block_crowding_another_is_refused(self):
        cv = b.w1.Cave(self.eng, 44, 34)
        cv.room(3, 3, 40, 30)
        cv.block(19, 16, 30, 20)
        with self.assertRaises(AssertionError):
            cv.block(32, 19, 37, 26)

    def test_no_objects_or_sections(self):
        self.assertEqual(self.hdr["region_map_section"], "MAPSEC_PENDING_OWNER")
        self.assertEqual((self.hdr["object_events"], self.hdr["coord_events"], self.hdr["bg_events"]), ([], [], []))


if __name__ == "__main__":
    unittest.main()
