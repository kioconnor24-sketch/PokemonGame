"""W19 Maniac Tunnel -> Solaceon Ruins link: one ladder cell per re-staged map, reciprocal, passage connected."""
import copy
import importlib.util
import json
import pathlib
import struct
import unittest
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/maniac-ruins-link"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("maniac_ruins_link", HERE / "build_maniac_ruins_link.py")
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


class ManiacRuinsLinkTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng, cls.maps = b.build(ENGINE)
        cls.w13 = b.w13.build(ENGINE)[2]
        _, cls.w15, cls.w15_layouts = b.w15.build(ENGINE)

    def test_staged_files_match_a_fresh_build(self):
        for name, (hdr, (cells, _, _)) in self.maps.items():
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)
            self.assertEqual((HERE / "staged" / name / "map.bin").read_bytes(), struct.pack("<%dH" % len(cells), *cells))

    def test_restaged_maps_change_one_cell_and_append_one_warp(self):
        cases = [("ManiacTunnel", self.w13["ManiacTunnel"][0], self.w13["ManiacTunnel"][1][:2], b.TUNNEL_LADDER),
                 ("SolaceonRuins_B2F_East", self.w15["SolaceonRuins_B2F_East"],
                  self.w15_layouts["SolaceonRuins_B2F_East"][:2], b.RUINS_LADDER)]
        for name, src_hdr, (src, width), ladder in cases:
            hdr, (cells, _, _) = self.maps[name]
            self.assertEqual([(i % width, i // width) for i, (a, c) in enumerate(zip(src, cells)) if a != c], [ladder])
            self.assertEqual(hdr["warp_events"][:-1], src_hdr["warp_events"])
            self.assertEqual((hdr["warp_events"][-1]["x"], hdr["warp_events"][-1]["y"]), ladder)

    def test_ladders_reciprocal_and_a_one_way_is_refused(self):
        self.assertTrue(b.check(self.maps))
        maps = copy.deepcopy(self.maps)
        maps["ManiacTunnel_B1F"][0]["warp_events"][1]["dest_warp_id"] = "0"
        with self.assertRaises(AssertionError):
            b.check(maps)

    def test_every_ladder_reachable_on_its_floor(self):
        for name, (hdr, (cells, w, h)) in self.maps.items():
            warps = [(e["x"], e["y"]) for e in hdr["warp_events"]]
            got = reach(cells, w, warps[-1])
            for p in warps:
                self.assertIn(p, got, name)
            self.assertFalse({(x, y) for x, y in got if x in (0, w - 1) or y in (0, h - 1)}, name)

    def test_no_objects_or_sections(self):
        for hdr, _ in self.maps.values():
            self.assertEqual(hdr["region_map_section"], "MAPSEC_PENDING_OWNER")
            self.assertEqual(hdr["object_events"], [])


if __name__ == "__main__":
    unittest.main()
