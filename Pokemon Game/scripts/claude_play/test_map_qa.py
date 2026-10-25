"""Offline tests for map_qa's static layer and fixture safety (no ROM, no emulator)."""
import inspect
import json
import pathlib
import struct
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import map_qa  # noqa: E402

BEHAVIOR = {"v": "MB_JUMP_SOUTH", "D": "MB_ANIMATED_DOOR", "M": "MB_SOUTH_ARROW_WARP", "L": "MB_LADDER",
            "H": "MB_MT_PYRE_HOLE", "N": "MB_NON_ANIMATED_DOOR", "n": "MB_NON_ANIMATED_DOOR"}


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
        return self.inside(x, y) and self.rows[y][x] in ".MLHn"

    def warp_at(self, x, y):
        for wx, wy, dest, warp in self.warps:
            if (wx, wy) == (x, y):
                return dest, warp
        return None


class FakeElevMap(FakeMap):
    """FakeMap plus per-tile elevations (one hex digit per tile, so 'f' is a 15 bridge)."""
    def __init__(self, map_id, rows, elev, **kw):
        super().__init__(map_id, rows, **kw)
        self.elev = elev

    def elevation(self, x, y):
        return int(self.elev[y][x], 16)


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

    def test_step_on_trigger_warps_are_entered_from_their_approach_tile(self):
        # A warp tile with a coord trigger (no arrow/door metatile) is walked onto; the player lands on it.
        lake = FakeMap("LAKE", ["####",
                                "#..#",
                                "#..#",
                                "##.#"], warps=[(2, 3, "FRONT", 0)])
        lake.triggers = {(2, 3)}
        self.assertEqual(map_qa.warp_stand(lake, 2, 3), (2, 2))
        self.assertEqual(map_qa.warp_push(lake, 2, 3), "down")
        self.assertEqual(map_qa.warp_arrive(lake, 2, 3), (2, 3))
        # Without the trigger it is an ordinary walkable warp tile: stand and arrive on it.
        lake.triggers = set()
        self.assertEqual((map_qa.warp_stand(lake, 2, 3), map_qa.warp_arrive(lake, 2, 3)), ((2, 3), (2, 3)))
        # A trigger with no warp is not a warp; a door keeps its doorstep arrival.
        lake.triggers = {(1, 1)}
        self.assertIsNone(map_qa.mapdata.trigger_entry(lake, 1, 1))
        self.assertEqual(map_qa.warp_arrive(town(), 3, 2), (3, 3))

    def test_a_route_split_by_a_cliff_is_joined_through_a_cave_in_the_batch(self):
        # Route: south half (rows 3-4) and north half (rows 0-1) split by a wall; each half has a cave door.
        route = FakeMap("ROUTE", ["#D###",
                                  "#...#",
                                  "#####",
                                  "#..D#",
                                  "#...#"], warps=[(3, 3, "CAVE", 0), (1, 0, "CAVE", 1)])
        cave = FakeMap("CAVE", ["#M.M#",
                                "#...#"], warps=[(1, 0, "ROUTE", 0), (3, 0, "ROUTE", 1)])
        joined, _ = map_qa.static_audit(FakeWorld(route, cave), ["ROUTE", "CAVE"])
        self.assertNotIn("exit-unreachable", codes(joined))
        alone, _ = map_qa.static_audit(FakeWorld(route, cave), ["ROUTE"])
        self.assertIn("exit-unreachable", codes(alone))
        # The cave's own two exits really are joined inside it; walling it off splits the batch again.
        sealed = FakeMap("CAVE", ["#M#M#",
                                  "#.#.#"], warps=cave.warps)
        split, _ = map_qa.static_audit(FakeWorld(route, sealed), ["ROUTE", "CAVE"])
        self.assertIn("exit-unreachable", codes(split))

    def test_driver_routes_through_a_cave_when_the_edge_is_in_the_other_half(self):
        import driver as drv
        route = FakeMap("ROUTE", ["#.D.#",
                                  "#...#",
                                  "#####",
                                  "#.D.#",
                                  "#...#"], warps=[(2, 3, "CAVE", 0), (2, 0, "CAVE", 1)],
                        connections=[("up", "TOWN", 0)])
        cave = FakeMap("CAVE", ["#M.M#",
                                "#...#"], warps=[(1, 0, "ROUTE", 0), (3, 0, "ROUTE", 1)])
        town = FakeMap("TOWN", ["#...#"])
        world = FakeWorld(route, cave, town)
        world.map_ids = {"ROUTE": 0, "CAVE": 1, "TOWN": 2}
        for m in (route, cave, town):
            m.world = world
        d = drv.Driver.__new__(drv.Driver)
        d.w = world
        legs = d.map_route("ROUTE", "TOWN", (2, 4))            # south half: the north edge is not walkable from here
        self.assertEqual([leg[:2] for leg in legs], [("ROUTE", "warp"), ("CAVE", "warp"), ("ROUTE", "edge")])
        self.assertEqual(legs[0][2], (2, 3))                    # the south door, not the unreachable north one
        self.assertEqual(d.map_route("ROUTE", "TOWN", (2, 1))[0][:2], ("ROUTE", "edge"))   # north half: straight up

    def test_elevation_blocks_a_plateau_except_through_a_transition_tile(self):
        # Row 0: grass (3) | plateau (4). Row 1: the same, but x 2 is an elevation-0 stair joining them.
        m = FakeElevMap("M", ["....",
                              "...."], ["3344",
                                        "3304"])
        self.assertEqual(map_qa.reach(m, [(0, 0)]), {(0, 0), (1, 0), (0, 1), (1, 1), (2, 1), (3, 1), (2, 0), (3, 0)})
        flat = FakeElevMap("M", ["....",
                                 "...."], ["3344",
                                           "3344"])
        self.assertEqual(map_qa.reach(flat, [(0, 0)]), {(0, 0), (1, 0), (0, 1), (1, 1)})
        self.assertEqual(map_qa.reach(flat, [(3, 0)], reverse=True), {(2, 0), (3, 0), (2, 1), (3, 1)})
        self.assertIsNone(map_qa.mapdata.bfs(flat, (0, 0), {(3, 0)}))
        self.assertEqual(len(map_qa.mapdata.bfs(m, (0, 0), {(3, 0)})), 5)

    def test_a_route_starting_on_a_bridge_keeps_the_arrival_elevation(self):
        # Ground (3) | bridge (15) | ground (3) over a lower floor (4) the bridge spans; start on the bridge.
        m = FakeElevMap("M", ["...",
                              "..."], ["3f3",
                                       "444"])
        self.assertEqual(len(map_qa.mapdata.bfs(m, (1, 0), {(2, 0)})), 1)
        self.assertEqual(len(map_qa.mapdata.bfs(m, (1, 0), {(2, 0)}, elevation=3)), 1)
        self.assertIsNone(map_qa.mapdata.bfs(m, (1, 0), {(2, 0)}, elevation=15))  # warped onto it: stuck at 15
        self.assertIsNone(map_qa.mapdata.bfs(m, (1, 0), {(0, 1)}, elevation=3))   # mismatch protection kept
        self.assertEqual(map_qa.reach(m, [(1, 0)]), {(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)})
        self.assertEqual(map_qa.reach(m, [(0, 0)]), {(0, 0), (1, 0), (2, 0)})
        self.assertEqual(map_qa.mapdata.start_elevations(m, (1, 0)), [3, 4, 15])
        self.assertEqual(map_qa.mapdata.start_elevations(m, (0, 0)), [3])
        far = FakeElevMap("M", ["....",
                                "...."], ["3f35",
                                          "4445"])
        self.assertEqual(map_qa.mapdata.start_elevations(far, (1, 0)), [3, 4, 15])  # 5 never touches the bridge

    def test_a_seam_from_a_bridge_uses_the_actual_elevation(self):
        # A: ground 3, then a bridge (15) on its east edge; B: ground 3. Walking 3 -> 15 keeps 3, so the
        # seam onto B's 3 is open. With ground 4 instead (actual elevation 4 on the bridge) it is refused.
        import driver as drv

        def world(ground):
            a = FakeElevMap("A", ["..."], [ground * 2 + "f"], connections=[("right", "B", 0)])
            b = FakeElevMap("B", ["..."], ["333"], connections=[("left", "A", 0)])
            w = FakeWorld(a, b)
            w.map_ids = {"A": 0, "B": 1}
            a.world = b.world = w
            d = drv.Driver.__new__(drv.Driver)
            d.w = w
            return w, d

        w, d = world("3")
        md = map_qa.mapdata
        self.assertTrue(md.crossable(w.map("A"), (2, 0), w.map("B"), (0, 0)))
        self.assertEqual(md.step_across(3, 15, 3), 3)
        self.assertIsNone(md.step_across(4, 15, 3))
        self.assertEqual([leg[:2] for leg in d.map_route("A", "B", (0, 0))], [("A", "edge")])
        self.assertEqual([leg[:2] for leg in d.map_route("A", "B", (2, 0))], [("A", "edge")])   # starting on it
        self.assertNotIn("seam-mismatch", codes(map_qa.static_audit(w, ["A", "B"])[0]))
        w, d = world("4")
        self.assertFalse(md.crossable(w.map("A"), (2, 0), w.map("B"), (0, 0)))
        with self.assertRaises(drv.Stuck):
            d.map_route("A", "B", (0, 0))
        self.assertIn("seam-mismatch", codes(map_qa.static_audit(w, ["A", "B"])[0]))

    def test_a_seam_between_different_elevations_is_a_mismatch(self):
        a = FakeElevMap("A", ["....."], ["33344"], connections=[("down", "B", 0)])
        b = FakeElevMap("B", ["....."], ["33333"], connections=[("up", "A", 0)])
        findings, _ = map_qa.static_audit(FakeWorld(a, b), ["A", "B"])
        bad = [f["detail"]["tile"] for f in findings if f["code"] == "seam-mismatch"]
        self.assertEqual(sorted(bad), [(3, 0), (3, 0), (4, 0), (4, 0)])   # both sides of x 3-4

    def test_driver_reaches_a_plateau_only_through_the_neighbouring_map(self):
        import driver as drv
        # South: grass (3) at x 0-1, a raised strip (4) at x 3 reachable from nowhere inside South.
        south = FakeElevMap("SOUTH", ["..#.",
                                      "..#."], ["3304",
                                                "3304"], connections=[("up", "NORTH", 0)])
        # North: grass (3), an elevation-0 stair at x 2, the same raised strip (4) at x 3 down to the seam.
        north = FakeElevMap("NORTH", ["....",
                                      "...."], ["3304",
                                                "3304"], connections=[("down", "SOUTH", 0)])
        world = FakeWorld(south, north)
        world.map_ids = {"SOUTH": 0, "NORTH": 1}
        for m in (south, north):
            m.world = world
        d = drv.Driver.__new__(drv.Driver)
        d.w = world
        self.assertNotIn((3, 1), map_qa.reach(south, [(0, 1)]))
        legs = d.map_route("SOUTH", "SOUTH", (0, 1), target=(3, 1))
        self.assertEqual([leg[:2] for leg in legs], [("SOUTH", "edge"), ("NORTH", "edge")])
        self.assertEqual(legs[1][3], ((3, 1),))       # down from North's raised column, landing on the strip

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

    def test_ladder_is_a_step_on_warp(self):
        """Arriving on a ladder and pushing away walks off it; the plan must step back onto it instead."""
        cave = FakeMap("CAVE", ["#####", "#.L.#", "#...#", "#####"], warps=[(2, 1, "DOWN", 0)])
        self.assertEqual(cave.behavior(2, 1), "MB_LADDER")
        entry = map_qa.mapdata.trigger_entry(cave, 2, 1)
        self.assertIsNotNone(entry)
        (ax, ay), d = entry
        dx, dy = map_qa.DIRS[d]
        self.assertEqual((ax + dx, ay + dy), (2, 1))
        self.assertTrue(cave.walkable(ax, ay))
        self.assertEqual(map_qa.warp_stand(cave, 2, 1), (ax, ay))

    def test_two_connections_on_one_side_each_own_their_span(self):
        """Route 205 North opens down to two maps; a tile belongs only to the connection whose span holds it."""
        north = FakeMap("N", ["##########", "#........#", "#..#.##..#"],
                        connections=[("down", "L", 0), ("down", "R", 6)])
        left = FakeMap("L", ["#..#", "#..#", "####"], connections=[("up", "N", 0)])
        right = FakeMap("R", ["#..#", "#..#", "####"], connections=[("up", "N", -6)])
        world = FakeWorld(north, left, right)
        for m in (north, left, right):
            m.world = world
        found, _ = map_qa.static_audit(world, ["N", "L", "R"])
        self.assertNotIn("seam-mismatch", codes(found))
        self.assertEqual(map_qa.edge_tiles(north, "down", ("R", 6)), [(7, 2), (8, 2)])
        self.assertEqual(map_qa.uncovered_edge_tiles(north, "down"), [(4, 2)])   # spanned by neither: closed
        north.connections = [("down", "L", 0), ("down", "R", 5)]                 # R shifted: its seam breaks
        right.connections = [("up", "N", -5)]
        self.assertIn("seam-mismatch", codes(map_qa.static_audit(world, ["N"])[0]))

    def test_walled_off_seam_is_unreachable(self):
        rows = ["###..###",
                "########",
                "#..D...#",
                "#......#",
                "########"]
        m = FakeMap("TOWN", rows, warps=[(3, 2, "ROOM", 0)], connections=[("up", "TOWN", 0)])
        self.assertIn("exit-unreachable", codes(map_qa.static_audit(FakeWorld(m), ["TOWN"])[0]))

    def test_a_hole_drop_lands_on_an_arrival_only_warp(self):
        # Upper floor: a hole (step-on, one way down). Lower floor: the landing is a plain floor warp the engine
        # never takes (Mt. Pyre), and a stair mat back up.
        upper = FakeMap("UP", ["#####",
                               "#.H.#",
                               "#.M.#"], warps=[(2, 1, "LOW", 0), (2, 2, "LOW", 1)])
        low = FakeMap("LOW", ["#####",
                              "#...#",
                              "#.M.#"], warps=[(2, 1, "UP", 0), (2, 2, "UP", 1)])
        md = map_qa.mapdata
        self.assertTrue(md.takeable(upper, 2, 1))
        self.assertIn(md.trigger_entry(upper, 2, 1)[0], {(1, 1), (3, 1)})   # stepped onto from beside, never the mat
        self.assertFalse(md.takeable(low, 2, 1))                              # arrival only
        self.assertTrue(md.takeable(low, 2, 2))
        self.assertEqual(len(md.bfs(low, (1, 1), {(3, 1)})), 2)               # walking over the landing is safe
        findings, plan = map_qa.static_audit(FakeWorld(upper, low), ["UP", "LOW"])
        self.assertEqual(findings, [])
        self.assertEqual([p["exit"] for p in plan["LOW"]["points"]], [False, True])
        # Wall the landing off from the stairs: whoever drops in is stuck, which the audit must report.
        pit = FakeMap("LOW", ["#####",
                              "#.#.#",
                              "#.M.#"], warps=[(2, 1, "UP", 0), (2, 2, "UP", 1)])
        pit.rows = ["#####", "##.##", "#####", "#.M.#"]
        pit.warps = [(2, 1, "UP", 0), (2, 3, "UP", 1)]
        pit.height = 4
        self.assertIn("exit-unreachable", codes(map_qa.static_audit(FakeWorld(upper, pit), ["LOW"])[0]))

    def test_a_solid_non_animated_door_is_shut(self):
        # A non-animated door warps only when stepped onto (IsWarpMetatileBehavior); drawn solid it never opens,
        # unlike an animated door, which is pushed into. 'N' is solid, 'n' walkable.
        rows = ["#N#n#D#",
                "#.....#"]
        m = FakeMap("TOWN", rows, warps=[(1, 0, "ROOM", 0), (3, 0, "ROOM", 0), (5, 0, "ROOM", 0)])
        md = map_qa.mapdata
        self.assertEqual([md.takeable(m, x, 0) for x in (1, 3, 5)], [False, True, True])
        room = FakeMap("ROOM", ["#M#"], warps=[(1, 0, "TOWN", 1)])
        closed = [f for f in map_qa.static_audit(FakeWorld(m, room), ["TOWN"])[0] if f["code"] == "warp-closed"]
        self.assertEqual([f["detail"]["warp"] for f in closed], [(1, 0)])

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

    def test_wildbattle_takes_over_one_existing_script(self):
        root = self._tree(marker=True)
        (root / "data/maps/Town/scripts.inc").write_text(
            "Town_MapScripts::\n\t.byte 0\n\nTown_EventScript_Boy::\n\tmsgbox Town_Text_Boy, MSGBOX_NPC\n\tend\n")
        map_qa.apply_fixture(root, {"edits": [
            {"op": "wildbattle", "map": "Town", "script": "Town_EventScript_Boy", "species": "SPECIES_X", "level": 80}]})
        text = (root / "data/maps/Town/scripts.inc").read_text()
        self.assertIn("Town_EventScript_Boy::\n@ TEST-ONLY", text)
        self.assertIn("\tsetwildbattle SPECIES_X, 80\n\tdowildbattle\n\trelease\n\tend\n", text)
        self.assertLess(text.index("dowildbattle"), text.index("msgbox Town_Text_Boy"))

    def test_wildbattle_refuses_a_missing_script(self):
        root = self._tree(marker=True)
        original = "Town_MapScripts::\n\t.byte 0\n"
        (root / "data/maps/Town/scripts.inc").write_text(original)
        with self.assertRaises(SystemExit):
            map_qa.apply_fixture(root, {"edits": [
                {"op": "wildbattle", "map": "Town", "script": "Town_EventScript_Boy", "species": "SPECIES_X", "level": 5}]})
        self.assertEqual((root / "data/maps/Town/scripts.inc").read_text(), original)

    def test_strip_removes_exactly_one_line(self):
        root = self._tree(marker=True)
        path = root / "data/maps/Town/scripts.inc"
        path.write_text("Town_OnTransition:\n\tsetrespawn HEAL_X\n\tend\n")
        map_qa.apply_fixture(root, {"edits": [
            {"op": "strip", "file": "data/maps/Town/scripts.inc", "line": "\tsetrespawn HEAL_X"}]})
        self.assertEqual(path.read_text(), "Town_OnTransition:\n\tend\n")
        with self.assertRaises(SystemExit):  # gone now: a stale fixture must not pass silently
            map_qa.apply_fixture(root, {"edits": [
                {"op": "strip", "file": "data/maps/Town/scripts.inc", "line": "\tsetrespawn HEAL_X"}]})

    def test_seam_legs_take_single_real_steps(self):
        # A timed hold can start a second step (seen on Route 201: one run overshot to (62, 6)).
        source = inspect.getsource(map_qa.Runner.seam)
        self.assertEqual(source.count("self.d.step("), 2)
        self.assertNotIn("self.press(", source)

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
