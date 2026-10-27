"""W17 Route 212 North mansion: one door cell opened, one warp appended, stock two-floor interior reciprocal."""
import copy
import importlib.util
import json
import pathlib
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/route212-mansion"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("route212_mansion", HERE / "build_route212_mansion.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


class Route212MansionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hdr, cls.blocks, cls.rooms = b.build(ENGINE)
        cls.source = json.loads((b.SINNOH / b.FAMILY / "staged/Route212_North/map.json").read_text())

    def test_staged_files_match_a_fresh_build(self):
        st = HERE / "staged"
        self.assertEqual(json.loads((st / "Route212_North-dev-overlay/map.json").read_text()), self.hdr)
        self.assertEqual((st / "Route212_North-dev-overlay/map.bin").read_bytes(),
                         struct.pack("<%dH" % len(self.blocks), *self.blocks))
        for name, room in self.rooms.items():
            self.assertEqual(json.loads((st / name / "map.json").read_text()), room)

    def test_only_the_door_cell_changes_and_one_warp_is_appended(self):
        width, cells = b.w12.map_bin(b.FAMILY, "Route212_North")
        changed = [(i % width, i // width) for i, (a, c) in enumerate(zip(cells, self.blocks)) if a != c]
        self.assertEqual(changed, [b.DOOR])
        x, y = b.DOOR
        self.assertEqual((cells[y * width + x] & 1023, self.blocks[y * width + x] & 1023), (529, 533))
        vwidth, vcells = b.w12.map_bin(b.FAMILY, b.DONOR_DOOR[0])
        sx, sy = b.DONOR_DOOR[1]
        self.assertEqual(self.blocks[y * width + x], vcells[sy * vwidth + sx])     # the family's working door word
        self.assertEqual(self.hdr["warp_events"][:-1], self.source["warp_events"])
        self.assertEqual({k: v for k, v in self.hdr.items() if k != "warp_events"},
                         {k: v for k, v in self.source.items() if k != "warp_events"})

    def test_interior_is_the_stock_graph_and_reciprocal(self):
        self.assertTrue(b.check(self.hdr, self.rooms))
        for name, stock in b.FLOORS:
            src = json.loads((ENGINE / f"data/maps/{stock}/map.json").read_text())
            self.assertEqual(self.rooms[name]["layout"], src["layout"])
            self.assertEqual([(w["x"], w["y"]) for w in src["warp_events"]],
                             [(w["x"], w["y"]) for w in self.rooms[name]["warp_events"]])
        rooms = copy.deepcopy(self.rooms)
        rooms["Route212_North_Mansion_2F"]["warp_events"][0]["dest_warp_id"] = "0"   # stairs onto the street mat
        with self.assertRaises(AssertionError):
            b.check(self.hdr, rooms)

    def test_interior_layouts_are_in_the_emerald_build(self):
        layouts = json.loads((ENGINE / "data/layouts/layouts.json").read_text())["layouts"]
        emerald = {l["id"] for l in layouts if l.get("layout_version", "emerald") == "emerald"}
        for room in self.rooms.values():
            self.assertIn(room["layout"], emerald)

    def test_no_objects_or_sections(self):
        for room in self.rooms.values():
            self.assertEqual(room["region_map_section"], "MAPSEC_PENDING_OWNER")
            self.assertEqual((room["object_events"], room["coord_events"], room["bg_events"]), ([], [], []))


if __name__ == "__main__":
    unittest.main()
