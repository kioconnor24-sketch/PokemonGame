"""Offline tests for map_qa's static layer and fixture safety (no ROM, no emulator)."""
import json
import pathlib
import struct
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import map_qa  # noqa: E402

BEHAVIOR = {"v": "MB_JUMP_SOUTH", "D": "MB_ANIMATED_DOOR", "M": "MB_SOUTH_ARROW_WARP"}


class FakeMap:
    def __init__(self, map_id, rows, warps=(), connections=()):
        self.id, self.rows = map_id, rows
        self.width, self.height = len(rows[0]), len(rows)
        self.warps = list(warps)
        self.connections = list(connections)
        self.objects = []

    def inside(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def behavior(self, x, y):
        return BEHAVIOR.get(self.rows[y][x], "MB_NORMAL")

    def walkable(self, x, y):
        return self.inside(x, y) and self.rows[y][x] in ".M"

    def warp_at(self, x, y):
        for wx, wy, dest, warp in self.warps:
            if (wx, wy) == (x, y):
                return dest, warp
        return None


class FakeWorld:
    def __init__(self, *maps):
        self.maps = {m.id: m for m in maps}

    def map(self, map_id):
        return self.maps[map_id]


TOWN = ["###..###",
        "#......#",
        "#..D...#",
        "#......#",
        "###..###"]


def town(**kw):
    return FakeMap("TOWN", TOWN, warps=[(3, 2, "ROOM", 0)], **kw)


def codes(findings):
    return sorted({f["code"] for f in findings})


class StaticLayer(unittest.TestCase):
    def test_clean_map_passes_and_plans_runtime_checks(self):
        findings, plan = map_qa.static_audit(FakeWorld(town()), ["TOWN"])
        self.assertEqual(findings, [])
        self.assertEqual({c["direction"] for c in plan["TOWN"]["closed"]}, {"up", "down"})
        warp = [p for p in plan["TOWN"]["points"] if p["kind"] == "warp"][0]
        self.assertEqual(warp["tile"], (3, 3))   # stand below a door
        self.assertEqual(warp["push"], "up")

    def test_ledge_pocket_is_found(self):
        rows = ["#..####",
                "#.....#",
                "#.v####",
                "##.####",   # landing tile under the ledge: no way back up, no way out
                "#######"]
        m = FakeMap("POCKET", rows, connections=[("up", "POCKET", 0)])
        findings, plan = map_qa.static_audit(FakeWorld(m), ["POCKET"])
        self.assertIn("one-way-pocket", codes(findings))
        self.assertEqual(plan["POCKET"]["pocket"]["into"], (2, 3))

    def test_ledge_landing_on_a_wall(self):
        rows = ["#...#",
                "#.v.#",
                "#.#.#",
                "#...#",
                "##.##"]
        m = FakeMap("LEDGE", rows, connections=[("down", "LEDGE", 0), ("up", "LEDGE", 0)])
        self.assertIn("ledge-landing", codes(map_qa.static_audit(FakeWorld(m), ["LEDGE"])[0]))

    def test_seam_mismatch_depends_on_offset(self):
        a = FakeMap("A", ["##..##", "#....#", "######"], connections=[("up", "B", 0)])
        b = FakeMap("B", ["######", "#....#", "##..##"], connections=[("down", "A", 0)])
        self.assertEqual(map_qa.static_audit(FakeWorld(a, b), ["A", "B"])[0], [])
        a.connections = [("up", "B", 1)]
        found = map_qa.static_audit(FakeWorld(a, b), ["A"])[0]
        self.assertEqual(codes(found), ["seam-mismatch"])
        self.assertEqual(found[0]["detail"]["faces"], ("B", (1, 2)))

    def test_walled_off_seam_is_unreachable(self):
        rows = ["###..###",
                "########",
                "#..D...#",
                "#......#",
                "########"]
        m = FakeMap("TOWN", rows, warps=[(3, 2, "ROOM", 0)], connections=[("up", "TOWN", 0)])
        self.assertIn("exit-unreachable", codes(map_qa.static_audit(FakeWorld(m), ["TOWN"])[0]))

    def test_closed_edges_skip_warp_mats_and_split_runs(self):
        rows = ["#######",
                "#.....#",
                "..MM...",]
        m = FakeMap("ROOM", rows, warps=[(2, 2, "TOWN", 0), (3, 2, "TOWN", 0)])
        _, plan = map_qa.static_audit(FakeWorld(m), ["ROOM"])
        bottom = [c for c in plan["ROOM"]["closed"] if c["direction"] == "down"]
        self.assertEqual([c["span"] for c in bottom], [[(0, 2), (1, 2)], [(4, 2), (6, 2)]])
        mats = [p for p in plan["ROOM"]["points"] if p["kind"] == "warp"]
        self.assertEqual([(p["tile"], p["push"]) for p in mats], [((2, 2), "down"), ((3, 2), "down")])

    def test_across_matches_engine_offset_rule(self):
        a, b = FakeMap("A", ["." * 10] * 6), FakeMap("B", ["." * 8] * 4)
        # fieldmap.c: crossing subtracts the offset along the shared edge.
        self.assertEqual(map_qa.across(a, b, "up", 2, (5, 0)), (3, 3))
        self.assertEqual(map_qa.across(a, b, "down", -2, (5, 5)), (7, 0))
        self.assertEqual(map_qa.across(a, b, "left", 1, (0, 3)), (7, 2))
        self.assertEqual(map_qa.across(a, b, "right", -1, (9, 3)), (0, 4))


class Fixtures(unittest.TestCase):
    def _tree(self, marker):
        root = pathlib.Path(tempfile.mkdtemp())
        (root / "data/maps/Town").mkdir(parents=True)
        (root / "data/layouts/Town").mkdir(parents=True)
        (root / "data/maps/Town/map.json").write_text(json.dumps({"id": "MAP_TOWN", "connections": None,
                                                                  "warp_events": []}))
        (root / "data/layouts/layouts.json").write_text(json.dumps({"layouts": [
            {"id": "LAYOUT_TOWN", "width": 4, "height": 2, "blockdata_filepath": "data/layouts/Town/map.bin"}]}))
        (root / "data/layouts/Town/map.bin").write_bytes(bytes(16))
        if marker:
            (root / map_qa.MARKER).touch()
        return root

    FIX = {"edits": [
        {"op": "connection", "map": "Town", "add": {"map": "MAP_TOWN", "offset": 0, "direction": "up"}},
        {"op": "warp", "map": "Town", "add": {"x": 1, "y": 0, "elevation": 0, "dest_map": "MAP_TOWN", "dest_warp_id": "0"}},
        {"op": "blocks", "layout": "LAYOUT_TOWN", "set": [[3, 1, 135, 1, 3]]}]}

    def test_refuses_a_tree_without_the_throwaway_marker(self):
        root = self._tree(marker=False)
        with self.assertRaises(SystemExit):
            map_qa.apply_fixture(root, self.FIX)
        self.assertEqual(json.loads((root / "data/maps/Town/map.json").read_text())["connections"], None)

    def test_applies_connections_warps_and_blocks(self):
        root = self._tree(marker=True)
        map_qa.apply_fixture(root, self.FIX)
        info = json.loads((root / "data/maps/Town/map.json").read_text())
        self.assertEqual(info["connections"][0]["direction"], "up")
        self.assertEqual(info["warp_events"][0]["x"], 1)
        block = struct.unpack_from("<H", (root / "data/layouts/Town/map.bin").read_bytes(), 2 * (1 * 4 + 3))[0]
        self.assertEqual(block, 135 | (1 << 10) | (3 << 12))

    def test_grant_adds_one_on_transition_script_and_section_relabels(self):
        root = self._tree(marker=True)
        (root / "data/maps/Town/scripts.inc").write_text("Town_MapScripts::\n\t.byte 0\n\nTown_EventScript_Sign::\n\tend\n")
        map_qa.apply_fixture(root, {"edits": [
            {"op": "grant", "map": "Town", "flags": ["FLAG_A"], "items": ["ITEM_B", "ITEM_C"]},
            {"op": "section", "map": "Town", "section": "MAPSEC_X"}]})
        text = (root / "data/maps/Town/scripts.inc").read_text()
        self.assertIn("Town_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, Town_OnTransition_MapQaGrant\n"
                      "\t.byte 0\n", text)
        self.assertIn("\tsetflag FLAG_A\n", text)
        # Each item is given once: guarded by checkitem so re-entering the map doesn't stack copies.
        self.assertEqual(text.count("\tadditem "), 2)
        self.assertEqual(text.count("\tcheckitem "), 2)
        self.assertIn("Town_EventScript_Sign::", text)        # existing scripts untouched
        self.assertEqual(json.loads((root / "data/maps/Town/map.json").read_text())["region_map_section"], "MAPSEC_X")

    def test_grant_refuses_to_shadow_an_existing_on_transition_script(self):
        root = self._tree(marker=True)
        original = "Town_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, Town_OnTransition\n\t.byte 0\n"
        (root / "data/maps/Town/scripts.inc").write_text(original)
        with self.assertRaises(SystemExit):
            map_qa.apply_fixture(root, {"edits": [{"op": "grant", "map": "Town", "flags": ["FLAG_A"]}]})
        self.assertEqual((root / "data/maps/Town/scripts.inc").read_text(), original)

    def test_party_menu_layout_matches_engine_source(self):
        engine = map_qa.HERE.parents[1] / "engine"
        if not (engine / "src/party_menu.c").exists():
            self.skipTest("engine source not present")
        menu = map_qa.party_menu_layout(engine)
        self.assertEqual((menu["actions"], menu["cursor"]), (15, 2))
        self.assertGreaterEqual(menu["count"], 8)
        self.assertGreater(menu["MENU_FIELD_MOVES"], menu["MENU_FIELD_TOOLKIT"])

    def test_shipped_fixtures_are_well_formed(self):
        files = sorted((map_qa.HERE / "map_qa_fixtures").glob("*.json"))
        self.assertGreaterEqual(len(files), 4)
        kinds = set()
        for f in files:
            spec = json.loads(f.read_text())
            kinds.add(spec["expect"])
            self.assertIn("TEST-ONLY" if spec["edits"] else "no edits", spec["description"])
            if spec["expect"] == "FAIL":
                self.assertTrue(spec["must_fail"], f.name)
        self.assertEqual(kinds, {"PASS", "FAIL"})


if __name__ == "__main__":
    unittest.main()
