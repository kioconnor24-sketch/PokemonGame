"""W18 Great Marsh areas: reproducible, attested, reciprocal seams on open cells, one connected 2 x 2 loop."""
import copy
import importlib.util
import json
import pathlib
import struct
import unittest
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/great-marsh-areas"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("great_marsh_areas", HERE / "build_great_marsh_areas.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
WATER = None


def walkable(v):
    return not v & 0xC00 and v & 1023 not in WATER


class GreatMarshAreasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global WATER
        cls.eng, cls.maps = b.build(ENGINE)
        WATER = b.pal.POND_IDS
        cls.w10 = b.w10.build(ENGINE)

    def test_staged_files_match_a_fresh_build(self):
        for name, (hdr, cells) in self.maps.items():
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)
            self.assertEqual((HERE / "staged" / name / "map.bin").read_bytes(), struct.pack("<%dH" % len(cells), *cells))

    def test_w10_marsh_changes_only_at_its_two_gaps(self):
        src, got = self.w10[1], self.maps["GreatMarsh"][1]
        changed = {(i % b.W, i // b.W) for i, (a, c) in enumerate(zip(src, got)) if a != c}
        expect = {(tx + dx, ty + dy) for side in ("up", "left") for tx, ty in b.gap_trees(side)
                  for dx in (0, 1) for dy in (0, 1)}
        self.assertEqual(changed, expect)
        hdr, w10hdr = self.maps["GreatMarsh"][0], self.w10[2]
        self.assertEqual({k: v for k, v in hdr.items() if k != "connections"},
                         {k: v for k, v in w10hdr.items() if k != "connections"})

    def test_every_word_is_attested(self):
        known = set(self.eng.cells("LakeVerity")[2]) | set(self.eng.cells("DewfordTown")[2])
        for name, (_, cells) in self.maps.items():
            self.assertFalse(set(cells) - known, name)

    def test_seams_are_reciprocal_and_a_closed_gap_is_refused(self):
        self.assertTrue(b.check(self.maps))
        maps = copy.deepcopy(self.maps)
        hdr, cells = maps["GreatMarsh_West"]
        x, y = b.gap_cells("up")[0]
        cells[y * b.W + x] |= 0x400                                           # one seam cell walled
        with self.assertRaises(AssertionError):
            b.check(maps)
        maps = copy.deepcopy(self.maps)
        maps["GreatMarsh_North"][0]["connections"][0]["offset"] = 2
        with self.assertRaises(AssertionError):
            b.check(maps)

    def test_one_walkable_world_through_the_seams(self):
        start = ("GreatMarsh", (b.w10.GATE[0] + 2, b.w10.GATE[1] + 4))      # the gate house doorstep
        by_id = {h["id"]: n for n, (h, _) in self.maps.items()}
        seen, todo = {start}, deque([start])
        while todo:
            name, (x, y) = todo.popleft()
            hdr, cells = self.maps[name]
            steps = [(name, (x + dx, y + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
            for c in hdr["connections"]:
                if (x, y) in b.gap_cells(c["direction"]):
                    nx = {"up": (x, b.H - 1), "down": (x, 0), "left": (b.W - 1, y), "right": (0, y)}[c["direction"]]
                    steps.append((by_id[c["map"]], nx))
            for n, (px, py) in steps:
                if (n, (px, py)) in seen or not (0 <= px < b.W and 0 <= py < b.H):
                    continue
                if walkable(self.maps[n][1][py * b.W + px]):
                    seen.add((n, (px, py)))
                    todo.append((n, (px, py)))
        for name, (hdr, _) in self.maps.items():
            for c in hdr["connections"]:
                for p in b.gap_cells(c["direction"]):
                    self.assertIn((name, p), seen, (name, c["direction"]))
        for name, (_, cells) in self.maps.items():                           # the ring is otherwise closed
            edge = {(n, p) for n, p in seen if n == name and (p[0] in (0, b.W - 1) or p[1] in (0, b.H - 1))}
            gaps = {(name, p) for c in self.maps[name][0]["connections"] for p in b.gap_cells(c["direction"])}
            self.assertLessEqual(edge, gaps, name)

    def test_no_objects_or_sections(self):
        for hdr, _ in self.maps.values():
            self.assertEqual(hdr["region_map_section"], "MAPSEC_PENDING_OWNER")
            self.assertEqual(hdr["object_events"], [])


if __name__ == "__main__":
    unittest.main()
