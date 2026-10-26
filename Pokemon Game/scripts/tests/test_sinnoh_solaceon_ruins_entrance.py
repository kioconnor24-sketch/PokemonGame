"""W20 Solaceon Ruins entrance: two cliff warps appended, entrance chamber reciprocal, B1F one ladder cell added."""
import copy
import importlib.util
import json
import pathlib
import struct
import unittest
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/solaceon-ruins-entrance"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("solaceon_ruins_entrance", HERE / "build_solaceon_ruins_entrance.py")
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


class SolaceonRuinsEntranceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng, cls.sol, cls.maps = b.build(ENGINE)
        cls.w12 = b.w12.build(ENGINE)[0]["SolaceonTown"]
        _, cls.w15, cls.w15_layouts = b.w15.build(ENGINE)

    def test_staged_files_match_a_fresh_build(self):
        st = HERE / "staged"
        self.assertEqual(json.loads((st / "SolaceonTown-dev-overlay/map.json").read_text()), self.sol)
        for name, (hdr, (cells, _, _)) in self.maps.items():
            self.assertEqual(json.loads((st / name / "map.json").read_text()), hdr)
            self.assertEqual((st / name / "map.bin").read_bytes(), struct.pack("<%dH" % len(cells), *cells))

    def test_town_overlay_only_appends_the_two_cliff_warps(self):
        n = len(self.w12["warp_events"])
        self.assertEqual(self.sol["warp_events"][:n], self.w12["warp_events"])
        self.assertEqual([(w["x"], w["y"]) for w in self.sol["warp_events"][n:]], b.CLIFF_DOORS)
        self.assertEqual({k: v for k, v in self.sol.items() if k != "warp_events"},
                         {k: v for k, v in self.w12.items() if k != "warp_events"})

    def test_b1f_changes_one_cell_and_appends_one_warp(self):
        src, width = self.w15_layouts["SolaceonRuins_B1F"][:2]
        hdr, (cells, _, _) = self.maps["SolaceonRuins_B1F"]
        self.assertEqual([(i % width, i // width) for i, (a, c) in enumerate(zip(src, cells)) if a != c], [b.B1F_LADDER])
        self.assertEqual(hdr["warp_events"][:-1], self.w15["SolaceonRuins_B1F"]["warp_events"])

    def test_warps_reciprocal_and_a_one_way_is_refused(self):
        self.assertTrue(b.check(self.sol, self.maps))
        maps = copy.deepcopy(self.maps)
        maps["SolaceonRuins_Entrance"][0]["warp_events"][1]["dest_warp_id"] = "3"   # foot mouth onto the ledge door
        with self.assertRaises(AssertionError):
            b.check(self.sol, maps)

    def test_entrance_chamber_connected_and_closed(self):
        hdr, (cells, w, h) = self.maps["SolaceonRuins_Entrance"]
        warps = [(e["x"], e["y"]) for e in hdr["warp_events"]]
        got = reach(cells, w, warps[-1])
        for p in warps:
            self.assertIn(p, got)
        self.assertFalse({(x, y) for x, y in got if x in (0, w - 1) or y in (0, h - 1)})

    def test_no_objects_or_sections(self):
        for hdr, _ in self.maps.values():
            self.assertEqual(hdr["region_map_section"], "MAPSEC_PENDING_OWNER")
            self.assertEqual(hdr["object_events"], [])


if __name__ == "__main__":
    unittest.main()
