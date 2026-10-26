"""W13 Spring Path / Sendoff Spring / Turnback Cave / Maniac Tunnel staging: reproducible, attested, reciprocal."""
import copy
import importlib.util
import json
import pathlib
import struct
import unittest
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/sendoff-spring"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("sendoff_spring", HERE / "build_sendoff_spring.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def reach(cells, width, start):
    """On-foot BFS over collision-free cells (the new outdoor maps have no water on foot paths)."""
    height = len(cells) // width
    seen, todo = {start}, deque([start])
    while todo:
        x, y = todo.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and 0 <= n[0] < width and 0 <= n[1] < height and not cells[n[1] * width + n[0]] & 0xC00 \
                    and cells[n[1] * width + n[0]] & 1023 != 161:
                seen.add(n)
                todo.append(n)
    return seen


class SendoffSpringTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng, cls.fam, cls.maps, cls.coords, (cls.r214, cls.r214_hdr) = b.build(ENGINE)

    def test_staged_files_match_a_fresh_build(self):
        for name, (hdr, (cells, *_)) in self.maps.items():
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)
            self.assertEqual((HERE / "staged" / name / "map.bin").read_bytes(), struct.pack("<%dH" % len(cells), *cells))
            self.assertEqual((HERE / "staged" / name / "scripts.inc").read_text(), b.w1.scripts(name, self.coords.get(name, ())))
        self.assertEqual(json.loads((HERE / "staged/Route214-dev-overlay/map.json").read_text()), self.r214_hdr)
        self.assertEqual((HERE / "staged/Route214-dev-overlay/map.bin").read_bytes(),
                         struct.pack("<%dH" % len(self.r214), *self.r214))

    def test_route214_overlay_cuts_one_tree_row_and_opens_the_cliff_mouth(self):
        width, src = self.fam.maps["Route214"]
        changed = {(i % width, i // width) for i, (a, c) in enumerate(zip(src, self.r214)) if a != c}
        cut = {(x, y) for y in b.CUT_ROWS for x in range(b.CUT_X, width)}
        edge = {(x, b.CUT_ROWS[0] - 1) for x in range(b.CUT_X, width)}
        self.assertEqual(changed, cut | edge)
        source = json.loads((b.FAMILY / "staged/Route214/map.json").read_text())
        self.assertEqual(self.r214_hdr["warp_events"][:-1], source["warp_events"])
        self.assertEqual(self.r214_hdr["connections"][:-1], source["connections"])
        self.assertEqual(self.r214_hdr["connections"][-1], {"map": "MAP_SPRING_PATH", "offset": b.SP_OFFSET,
                                                            "direction": "right"})
        w = self.r214_hdr["warp_events"][-1]
        self.assertEqual(((w["x"], w["y"]), w["dest_map"]), (b.MANIAC_MOUTH, "MAP_MANIAC_TUNNEL"))

    def test_every_outdoor_pair_is_attested_and_a_new_one_is_refused(self):
        for name, cells, width in (("Route214", self.r214, b.R214_W),
                                   ("SpringPath", self.maps["SpringPath"][1][0], b.SP_W),
                                   ("SendoffSpring", self.maps["SendoffSpring"][1][0], b.SS_W)):
            self.fam.check(name, cells, width)
        bad = list(self.maps["SpringPath"][1][0])
        bad[b.SP_W * 11 + 2] = self.fam.word("Route214", 30, 13, 478)      # a tree bottom alone on grass
        with self.assertRaisesRegex(SystemExit, "unattested"):
            self.fam.check("SpringPath", bad, b.SP_W)

    def test_warps_and_connections_are_reciprocal_and_a_one_way_is_refused(self):
        self.assertTrue(b.check(self.maps, self.r214_hdr))
        maps = copy.deepcopy(self.maps)
        maps["TurnbackCave_B1F"][0]["warp_events"][0]["dest_warp_id"] = "0"   # up-ladder onto the cave mouth
        with self.assertRaises(AssertionError):
            b.check(maps, self.r214_hdr)
        maps = copy.deepcopy(self.maps)
        maps["SpringPath"][0]["connections"][0]["offset"] = 0
        with self.assertRaises(AssertionError):
            b.check(maps, self.r214_hdr)

    def test_the_chain_is_walkable_seam_to_seam(self):
        # Route 214's cut rows reach its east edge from the open ground west of the forest.
        got = reach(self.r214, b.R214_W, (29, 20))
        self.assertIn((b.R214_W - 1, 20), got)
        # Spring Path: west seam rows (Route 214 rows 20-21 shifted by the offset) reach the east seam rows.
        sp = self.maps["SpringPath"][1][0]
        got = reach(sp, b.SP_W, (0, 20 - b.SP_OFFSET))
        east = {(b.SP_W - 1, y) for y in range(b.SP_H) if not sp[y * b.SP_W + b.SP_W - 1] & 0xC00}
        self.assertTrue(east and east <= got)
        # Sendoff Spring: its west seam rows are Spring Path's east ones (offset 0) and reach the cave portal.
        ss = self.maps["SendoffSpring"][1][0]
        for x, y in east:
            self.assertFalse(ss[y * b.SS_W] & 0xC00)
        got = reach(ss, b.SS_W, (0, min(y for _, y in east)))
        self.assertIn(b.TURNBACK_PORTAL, got)
        h = b.SS_H
        self.assertFalse({(x, y) for x, y in got if x == b.SS_W - 1 or y in (0, h - 1)})   # only the west seam is open

    def test_caves_are_connected_and_closed(self):
        for name in ("ManiacTunnel", "TurnbackCave_1F", "TurnbackCave_B1F", "TurnbackCave_B2F"):
            hdr, (cells, w, h, *_) = self.maps[name]
            warps = [(e["x"], e["y"]) for e in hdr["warp_events"]]
            got = reach(cells, w, warps[0])
            for p in warps:
                self.assertIn(p, got, name)
            self.assertFalse({(x, y) for x, y in got if x in (0, w - 1) or y in (0, h - 1)}, name)

    def test_no_objects_sections_or_story(self):
        for name, (hdr, _) in self.maps.items():
            self.assertEqual(hdr["region_map_section"], "MAPSEC_PENDING_OWNER")
            self.assertEqual((hdr["object_events"], hdr["bg_events"]), ([], []))
        self.assertEqual(self.r214_hdr["object_events"], json.loads((b.FAMILY / "staged/Route214/map.json").read_text())["object_events"])


if __name__ == "__main__":
    unittest.main()
