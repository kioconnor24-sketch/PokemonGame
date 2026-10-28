"""Packet E source stage (C51): 37 pinned maps whose combined warp/connection graph is closed and reciprocal."""
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/west-packet-e"
spec = importlib.util.spec_from_file_location("packet_e_stage", HERE / "stage_packet_e.py")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)


class PacketEStageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = e.read_sources()

    def edited(self, path, change):
        files = dict(self.files)
        header = json.loads(files[path])
        change(header)
        files[path] = json.dumps(header).encode()
        return e.graph_errors(e.headers(files))

    def test_pins_and_graph_are_clean(self):
        self.assertEqual(e.check(self.files), [])
        self.assertEqual(len(e.MAPS), 37)
        self.assertEqual(json.loads(e.PINS.read_text())["maps"], e.MAPS)

    def test_a_changed_source_byte_is_reported(self):
        files = dict(self.files)
        path = "solaceon-depths/staged/SolaceonRuins_B3F_Sanctum/map.bin"
        files[path] = files[path] + b"\0"
        self.assertIn("pin mismatch: " + path, e.check(files))

    def test_wrong_return_index_is_rejected(self):
        def change(h):
            h["warp_events"][0]["dest_warp_id"] = "4"
        errors = self.edited("city-shells/staged/SolaceonTown_Mart/map.json", change)
        self.assertTrue(any("does not lead back" in x for x in errors), errors)

    def test_wrong_return_entrance_is_rejected(self):
        def change(h):
            # West Hearthome door would return through the eastern door.
            h["warp_events"][2]["dest_warp_id"] = "1"
        errors = self.edited("amity-square/staged/HearthomeCity-dev-overlay/map.json", change)
        self.assertTrue(any("wrong entrance" in x for x in errors), errors)

    def test_negative_destination_index_is_rejected(self):
        def change(h):
            h["warp_events"][2]["dest_warp_id"] = "-1"
        errors = self.edited("amity-square/staged/HearthomeCity-dev-overlay/map.json", change)
        self.assertTrue(any("does not lead back" in x for x in errors), errors)

    def test_duplicate_internal_connection_is_rejected(self):
        def change(h):
            h["connections"].append(dict(h["connections"][0]))
        errors = self.edited("city-shells/staged/Route208-dev-overlay/map.json", change)
        self.assertTrue(any("duplicate" in x for x in errors), errors)

    def test_adjacent_door_tile_aliases_remain_valid(self):
        hearthome = e.headers(self.files)["HearthomeCity"]
        self.assertEqual(hearthome["warp_events"][2]["dest_warp_id"], "0")
        self.assertEqual(hearthome["warp_events"][3]["dest_warp_id"], "0")
        self.assertEqual(e.graph_errors(e.headers(self.files)), [])

    def test_one_sided_connection_offset_is_rejected(self):
        def change(h):
            h["connections"][0]["offset"] += 1
        errors = self.edited("lost-tower/staged/Route209-dev-overlay/map.json", change)
        self.assertTrue(any("not reciprocal" in x for x in errors), errors)

    def test_stock_tower_exterior_exits_share_the_source_portal(self):
        hdrs = e.headers(self.files)
        self.assertEqual(e.graph_errors(hdrs), [])
        stock = json.loads((ROOT / "engine/data/maps/MtPyre_1F/map.json").read_text())
        for i in range(4):
            w = hdrs["LostTower_1F"]["warp_events"][i]
            self.assertEqual((w["x"], w["y"]), (stock["warp_events"][i]["x"], stock["warp_events"][i]["y"]))
            self.assertEqual((w["dest_map"], w["dest_warp_id"]), ("MAP_ROUTE209", "1"))

    def test_tower_exception_rejects_changed_exit_and_return(self):
        for index, field, value in ((1, "x", 5), (3, "elevation", 3),
                                    (0, "x", 16)):
            with self.subTest(index=index, field=field):
                errors = self.edited("lost-tower/staged/LostTower_1F/map.json",
                                     lambda h: h["warp_events"][index].update({field: value}))
                self.assertTrue(any("wrong entrance" in x for x in errors), errors)
        errors = self.edited("lost-tower/staged/Route209-dev-overlay/map.json",
                             lambda h: h["warp_events"][1].update(dest_warp_id="1"))
        self.assertTrue(any("wrong entrance" in x for x in errors), errors)

    def test_the_tunnel_variant_of_b2f_east_would_leave_the_packet(self):
        files = dict(self.files)
        tunnel = ROOT / "Averon_Codex_Handoff/design/sinnoh/maniac-ruins-link/staged/SolaceonRuins_B2F_East/map.json"
        files["solaceon-depths/staged/SolaceonRuins_B2F_East/map.json"] = tunnel.read_bytes()
        errors = e.graph_errors(e.headers(files))
        self.assertTrue(any("leaves the packet (MAP_MANIAC_TUNNEL_B1F)" in x for x in errors), errors)

    def test_route212_doors_stay_closed_and_hearthome_keeps_w11_order(self):
        hearthome = e.headers(self.files)["HearthomeCity"]
        dests = [w["dest_map"] for w in hearthome["warp_events"]]
        self.assertEqual(len(dests), 15)
        self.assertNotIn("MAP_ROUTE212_ACCESS", dests)
        self.assertEqual(dests[:2], ["MAP_ROUTE208_ACCESS", "MAP_ROUTE209_ACCESS"])
        self.assertEqual(dests[2:6], ["MAP_AMITY_SQUARE"] * 4)

    def test_coronet_join_is_still_closed(self):
        route208 = e.headers(self.files)["Route208"]
        self.assertNotIn("MAP_MT_CORONET_1F_SOUTH", [w["dest_map"] for w in route208["warp_events"]])

    def test_extra_trigger_or_object_is_rejected(self):
        def change(h):
            h["object_events"] = [{"graphics_id": "OBJ_EVENT_GFX_BOY_1", "x": 1, "y": 1}]
        errors = self.edited("amity-square/staged/AmitySquare/map.json", change)
        self.assertIn("AmitySquare: has object or bg events", errors)

    def test_batch_contains_overlays_and_new_maps_only(self):
        with tempfile.TemporaryDirectory() as out:
            e.write_batch(self.files, out)
            staged = {p.name for p in (pathlib.Path(out) / "staged").iterdir()}
        self.assertEqual(staged, {m + "-dev-overlay" for m in e.OVERLAYS} | set(e.INTERIORS))


if __name__ == "__main__":
    unittest.main()

