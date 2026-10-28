"""W15 Solaceon Ruins depths: reproducible, ladder pairs reciprocal, every floor connected, W8's chambers preserved."""
import copy
import importlib.util
import json
import pathlib
import struct
import unittest
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/solaceon-depths"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("solaceon_depths", HERE / "build_solaceon_depths.py")
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


class SolaceonDepthsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng, cls.maps, cls.layouts = b.build(ENGINE)
        cls.w8 = b.w8.build(ENGINE)[0]

    def test_staged_files_match_a_fresh_build(self):
        for name, hdr in self.maps.items():
            cells, w, h = self.layouts[name]
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)
            self.assertEqual((HERE / "staged" / name / "map.bin").read_bytes(), struct.pack("<%dH" % len(cells), *cells))
            self.assertEqual(json.loads((HERE / "staged" / name / "layout.json").read_text())["width"], w)

    def test_chambers_keep_w8_warps_and_change_one_cell(self):
        for name, stock, _ in b.w8.RUINS:
            hdr, src = self.maps[name], self.w8[name]
            self.assertEqual(hdr["warp_events"][:-1], src["warp_events"])
            self.assertEqual(hdr["warp_events"][-1]["dest_map"], "MAP_SOLACEON_RUINS_B1F")
            self.assertNotEqual(hdr["layout"], src["layout"])             # own layout: the Hoenn one is untouched
            width, _, cells = self.eng.cells(stock)
            changed = [(i % width, i // width) for i, (a, c) in enumerate(zip(cells, self.layouts[name][0])) if a != c]
            self.assertEqual(changed, [b.CHAMBER_LADDER])

    def test_ladders_are_reciprocal_and_a_one_way_is_refused(self):
        self.assertTrue(b.check(self.maps))
        ids = {h["id"] for h in self.maps.values()}
        for hdr in self.maps.values():
            for w in hdr["warp_events"]:
                self.assertIn(w["dest_map"], ids | {"MAP_ROUTE209"})
        maps = copy.deepcopy(self.maps)
        maps["SolaceonRuins_B2F_East"]["warp_events"][1]["dest_warp_id"] = "0"   # down-ladder onto the wrong ladder
        with self.assertRaises(AssertionError):
            b.check(maps)

    def test_every_ladder_is_reachable_from_every_other_on_its_floor(self):
        for name in b.FLOORS:
            cells, w, h = self.layouts[name]
            warps = [(e["x"], e["y"]) for e in self.maps[name]["warp_events"]]
            got = reach(cells, w, warps[0])
            for p in warps:
                self.assertIn(p, got, name)
            self.assertFalse({(x, y) for x, y in got if x in (0, w - 1) or y in (0, h - 1)}, name)   # closed
        for name, _, _ in b.w8.RUINS:                                     # inner room: entry arrow to ladder
            cells, w, _ = self.layouts[name]
            self.assertIn(b.CHAMBER_LADDER, reach(cells, w, (8, 11)))

    def test_network_joins_all_three_chambers_by_two_routes(self):
        edges = {}
        for hdr in self.maps.values():
            for w in hdr["warp_events"]:
                if w["dest_map"] not in (hdr["id"], "MAP_ROUTE209"):
                    edges.setdefault(hdr["id"], set()).add(w["dest_map"])
        seen, todo = {"MAP_SOLACEON_RUINS_A"}, ["MAP_SOLACEON_RUINS_A"]
        while todo:
            for n in edges.get(todo.pop(), ()):
                if n not in seen:
                    seen.add(n)
                    todo.append(n)
        self.assertEqual(seen, {h["id"] for h in self.maps.values()})
        self.assertEqual(edges["MAP_SOLACEON_RUINS_B3F_SANCTUM"],
                         {"MAP_SOLACEON_RUINS_B2F_WEST", "MAP_SOLACEON_RUINS_B2F_EAST"})   # the loop

    def test_no_objects_story_or_sections(self):
        for hdr in self.maps.values():
            self.assertEqual(hdr["region_map_section"], "MAPSEC_PENDING_OWNER")
            self.assertEqual((hdr["object_events"], hdr["coord_events"], hdr["bg_events"]), ([], [], []))


if __name__ == "__main__":
    unittest.main()
