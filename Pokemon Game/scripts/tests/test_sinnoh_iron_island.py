"""W1 Iron Island / Canalave harbor staging: reproducible, attested art, reciprocal and reachable topology.

Off-engine source checks only. The DEV runtime evidence (mGBA traversal, Save/Continue) lives in the design folder.
"""
import copy
import importlib.util
import json
import pathlib
import re
import struct
import unittest
from collections import deque

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/iron-island"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("iron_island_builder", HERE / "build_iron_island.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)

NEW = ("IronIsland", "IronIsland_1F", "IronIsland_B1F", "IronIsland_B2F")
SHARED = {"IronIsland_House": "LAYOUT_HOUSE1", "CanalaveCity_House1": "LAYOUT_HOUSE1", "CanalaveCity_House2": "LAYOUT_HOUSE1", "CanalaveCity_Harbor": "LAYOUT_HARBOR",
          "CanalaveCity_PokemonCenter_1F": "LAYOUT_POKEMON_CENTER_1F"}


def behaviours(primary, secondary):
    names = re.findall(r"^\s*(MB_\w+)", (ENGINE / "include/constants/metatile_behaviors.h").read_text(), re.M)
    pa = (ENGINE / f"data/tilesets/primary/{primary}/metatile_attributes.bin").read_bytes()
    sa = (ENGINE / f"data/tilesets/secondary/{secondary}/metatile_attributes.bin").read_bytes()
    pa += b"\0" * (1024 - len(pa))
    attrs = struct.unpack("<%dH" % ((len(pa) + len(sa)) // 2), pa + sa)
    return [names[a & 0xFF] for a in attrs]


def reach(cells, width, beh, start):
    """On-foot BFS: collision 0 and not water; returns the reached set."""
    height = len(cells) // width
    ok = lambda x, y: 0 <= x < width and 0 <= y < height and not cells[y * width + x] & 0xC00 \
        and not any(k in beh[cells[y * width + x] & 1023] for k in ("WATER", "OCEAN"))
    seen, todo = {start}, deque([start])
    while todo:
        x, y = todo.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and ok(*n):
                seen.add(n)
                todo.append(n)
    return seen


class IronIslandTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng, cls.maps, cls.coords, cls.canal = b.build(ENGINE)

    def cells(self, name):
        return self.maps[name][1][0], self.maps[name][1][1]

    def test_staged_files_match_a_fresh_build(self):
        for name in NEW:
            cells, w, h, *_ = self.maps[name][1]
            self.assertEqual((HERE / "staged" / name / "map.bin").read_bytes(), struct.pack("<%dH" % len(cells), *cells))
        for name, (hdr, _) in self.maps.items():
            self.assertEqual(json.loads((HERE / "staged" / name / "map.json").read_text()), hdr)
            self.assertEqual((HERE / "staged" / name / "scripts.inc").read_text(), b.scripts(name, self.coords.get(name, ())))
        self.assertEqual((HERE / "staged/CanalaveCity/averon-map.bin").read_bytes(), self.canal[0])
        self.assertEqual(json.loads((HERE / "staged/CanalaveCity/map.json").read_text()), self.canal[1])

    def test_every_cell_word_is_an_existing_averon_cell(self):
        """ID, collision and elevation of every new cell occur together in the layouts the builder reads."""
        for name, corpus in (("IronIsland", b.OCEAN_CORPUS + ("LakeVerity",)), ("IronIsland_1F", b.CAVE_CORPUS),
                             ("IronIsland_B1F", b.CAVE_CORPUS), ("IronIsland_B2F", b.CAVE_CORPUS)):
            known = set()
            for n in corpus:
                known |= set(self.eng.cells(n)[2])
            cells, _ = self.cells(name)
            self.assertFalse(set(cells) - known, name)

    def test_unattested_shore_shape_is_refused(self):
        old = dict(b.LAND)
        try:
            b.LAND[4] = (8, 30)               # a stepped corner: concave water notches never drawn in Averon
            with self.assertRaisesRegex(SystemExit, "unattested shore pattern"):
                b.island(self.eng)
        finally:
            b.LAND.clear()
            b.LAND.update(old)

    def test_cave_block_must_leave_a_corridor(self):
        cave = b.Cave(self.eng, 26, 19)
        cave.room(3, 3, 22, 14)
        with self.assertRaises(AssertionError):
            cave.block(4, 6, 10, 10)          # one floor column to the wall

    def test_no_objects_sections_or_foreign_exits(self):
        for name, (hdr, layout) in self.maps.items():
            self.assertEqual(hdr["region_map_section"], "MAPSEC_PENDING_OWNER")
            self.assertEqual((hdr["object_events"], hdr["bg_events"], hdr["connections"]), ([], [], []))
            if layout is None:
                self.assertEqual(hdr["layout"], SHARED[name])
                self.assertIn(hdr["layout"], self.eng.layout_ids)
        self.assertTrue(b.check(self.eng, self.maps, self.canal))

    def test_one_way_portal_is_refused(self):
        maps = copy.deepcopy(self.maps)
        maps["CanalaveCity_Harbor"][0]["warp_events"][2]["dest_warp_id"] = "1"   # back to the house door
        with self.assertRaises(AssertionError):
            b.check(self.eng, maps, self.canal)

    def test_portal_scripts_target_the_reciprocal_arrivals(self):
        isl = self.maps["IronIsland"][0]
        har = self.maps["CanalaveCity_Harbor"][0]
        (tx, ty, _, (dest, warp)), = self.coords["IronIsland"]
        self.assertEqual((dest, warp), ("MAP_CANALAVE_CITY_HARBOR", 2))
        self.assertEqual(har["warp_events"][2]["dest_map"], "MAP_IRON_ISLAND")
        arrive = isl["warp_events"][int(har["warp_events"][2]["dest_warp_id"])]
        self.assertEqual((arrive["x"], arrive["y"]), (tx, ty))      # step-on portal: trigger on the arrival warp
        for x, y, _, (dest, warp) in self.coords["CanalaveCity_Harbor"]:
            self.assertEqual((dest, warp), ("MAP_IRON_ISLAND", 2))
            self.assertEqual((har["warp_events"][2]["x"], har["warp_events"][2]["y"]), (x, y))
        for name in ("IronIsland", "CanalaveCity_Harbor"):
            text = b.scripts(name, self.coords[name])
            self.assertEqual(text.count("\twarp "), len(self.coords[name]))
            self.assertEqual(text.count("\twaitstate\n"), len(self.coords[name]))

    def test_island_is_connected_on_foot(self):
        cells, w = self.cells("IronIsland")
        beh = behaviours("general", "dewford")
        hdr = self.maps["IronIsland"][0]
        arrive = next((e["x"], e["y"]) for e in hdr["warp_events"] if e["dest_map"] == "MAP_CANALAVE_CITY_HARBOR")
        got = reach(cells, w, beh, arrive)
        cave = next((e["x"], e["y"]) for e in hdr["warp_events"] if e["dest_map"] == "MAP_IRON_ISLAND_1F")
        house = next((e["x"], e["y"]) for e in hdr["warp_events"] if e["dest_map"] == "MAP_IRON_ISLAND_HOUSE")
        self.assertIn(cave, got)                                  # open cave mouth (no collision)
        self.assertIn((house[0], house[1] + 1), got)              # in front of the animated door
        self.assertEqual(beh[cells[house[1] * w + house[0]] & 1023], "MB_ANIMATED_DOOR")
        self.assertEqual(beh[cells[cave[1] * w + cave[0]] & 1023], "MB_NON_ANIMATED_DOOR")
        self.assertIn((self.coords["IronIsland"][0][0], self.coords["IronIsland"][0][1]), got)
        border = {(x, y) for x in range(w) for y in range(len(cells) // w) if x in (0, w - 1) or y in (0, len(cells) // w - 1)}
        self.assertFalse(got & border)                            # the map edge is never reachable on foot

    def test_caves_are_connected_and_closed(self):
        beh = behaviours("general", "cave")
        for name in ("IronIsland_1F", "IronIsland_B1F", "IronIsland_B2F"):
            cells, w = self.cells(name)
            warps = [(e["x"], e["y"]) for e in self.maps[name][0]["warp_events"]]
            got = reach(cells, w, beh, warps[0])
            for p in warps:
                self.assertIn(p, got, name)
                self.assertIn(beh[cells[p[1] * w + p[0]] & 1023], ("MB_LADDER", "MB_SOUTH_ARROW_WARP"))
            h = len(cells) // w
            self.assertFalse({(x, y) for x, y in got if x in (0, w - 1) or y in (0, h - 1)}, name)

    def test_canalave_overlay_changes_one_cell_and_appends_two_doors(self):
        data, hdr, receipt = self.canal
        src = (b.CANALAVE / "staged/CanalaveCity/averon-map.bin").read_bytes()
        self.assertEqual(receipt["changed_cells"], [(29, 13)])
        a, c = struct.unpack("<%dH" % (len(src) // 2), src), struct.unpack("<%dH" % (len(data) // 2), data)
        self.assertEqual(a[13 * 38 + 29] & 0xFC00, c[13 * 38 + 29] & 0xFC00)   # collision/elevation kept
        source = json.loads((b.CANALAVE / "staged/CanalaveCity/map.json").read_text())
        self.assertEqual(hdr["warp_events"][:1], source["warp_events"])
        self.assertEqual({k: v for k, v in hdr.items() if k != "warp_events"},
                         {k: v for k, v in source.items() if k != "warp_events"})
        self.assertEqual([(e["x"], e["y"]) for e in hdr["warp_events"][1:]], [(28, 22), (29, 13), (7, 17), (9, 31)])


if __name__ == "__main__":
    unittest.main()
