"""Packet G side connection (C53): Solaceon Ruins <-> Maniac Tunnel <-> Route 214, staged on packet E's 37 maps."""
import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/west-packet-g"
spec = importlib.util.spec_from_file_location("packet_g_tunnel", HERE / "stage_tunnel_link.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


class PacketGTunnelStageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = g.read_sources()
        cls.hdrs = g.headers(cls.files)

    def edited(self, path, change):
        files = dict(self.files)
        header = json.loads(files[path])
        change(header)
        files[path] = json.dumps(header).encode()
        return g.graph_errors(g.headers(files))

    def test_pins_graph_and_declared_externals_are_clean(self):
        self.assertEqual(g.check(self.files), [])
        self.assertEqual(len(g.MAPS), 40)

    def test_tunnel_ladder_exists_only_in_packet_g(self):
        east = [w["dest_map"] for w in self.hdrs["SolaceonRuins_B2F_East"]["warp_events"]]
        self.assertEqual(east, ["MAP_SOLACEON_RUINS_B1F", "MAP_SOLACEON_RUINS_B3F_SANCTUM", "MAP_MANIAC_TUNNEL_B1F"])
        packet_e = g.e.headers(g.e.read_sources())["SolaceonRuins_B2F_East"]["warp_events"]
        self.assertEqual([w["dest_map"] for w in packet_e], east[:2])

    def test_route214_to_ruins_chain_is_reciprocal_index_for_index(self):
        chain = [("Route214", 2), ("ManiacTunnel", 0), ("ManiacTunnel", 1), ("ManiacTunnel_B1F", 0),
                 ("ManiacTunnel_B1F", 1), ("SolaceonRuins_B2F_East", 2)]
        ids = {h["id"]: m for m, h in self.hdrs.items()}
        for (m, i), (n, j) in zip(chain[::2], chain[1::2]):
            w = self.hdrs[m]["warp_events"][i]
            self.assertEqual((ids[w["dest_map"]], int(w["dest_warp_id"])), (n, j))
            back = self.hdrs[n]["warp_events"][j]
            self.assertEqual((ids[back["dest_map"]], int(back["dest_warp_id"])), (m, i))

    def test_every_ruins_stair_returns_to_its_source_floor(self):
        ruins = [m for m in g.MAPS if m.startswith("SolaceonRuins")]
        ids = {h["id"]: m for m, h in self.hdrs.items()}
        for m in ruins:
            for i, w in enumerate(self.hdrs[m]["warp_events"]):
                back = self.hdrs[ids[w["dest_map"]]]["warp_events"][int(w["dest_warp_id"])]
                self.assertEqual(ids[back["dest_map"]], m, (m, i))

    def test_one_way_tunnel_ladder_is_rejected(self):
        def change(h):
            h["warp_events"][1]["dest_warp_id"] = "0"
        errors = self.edited("maniac-ruins-link/staged/ManiacTunnel_B1F/map.json", change)
        self.assertTrue(any("does not lead back" in x for x in errors), errors)

    def test_an_undeclared_exit_is_rejected(self):
        def change(h):
            h["warp_events"].append(dict(x=1, y=1, elevation=0, dest_map="MAP_VEILSTONE_CITY", dest_warp_id="0"))
        errors = self.edited("maniac-ruins-link/staged/ManiacTunnel/map.json", change)
        self.assertTrue(any("leaves the packet (MAP_VEILSTONE_CITY)" in x for x in errors), errors)

    def test_a_vanished_declared_exit_is_reported(self):
        def change(h):
            h["connections"] = [c for c in h["connections"] if c["map"] != "MAP_SPRING_PATH"]
        errors = self.edited("sendoff-spring/staged/Route214-dev-overlay/map.json", change)
        self.assertIn("declared external exit missing: Route214: connection leaves the packet (MAP_SPRING_PATH)",
                      errors)

    def test_a_changed_dev_context_byte_is_reported(self):
        files = dict(self.files)
        path = "sendoff-spring/staged/SpringPath/map.json"
        files[path] = files[path] + b"\n"
        self.assertIn("pin mismatch: " + path, g.check(files))

    def test_a_declared_exit_repeated_in_another_direction_is_rejected(self):
        def change(h):
            extra = dict(next(c for c in h["connections"] if c["map"] == "MAP_SPRING_PATH"), direction="up")
            h["connections"].append(extra)
        errors = self.edited("sendoff-spring/staged/Route214-dev-overlay/map.json", change)
        self.assertIn("declared external exit repeated 2 times: "
                      "Route214: connection leaves the packet (MAP_SPRING_PATH)", errors)

    def test_batch_swaps_b2f_east_and_carries_spring_context(self):
        with tempfile.TemporaryDirectory() as out:
            g.write_batch(self.files, out)
            staged = pathlib.Path(out) / "staged"
            names = {p.name for p in staged.iterdir()}
            east = json.loads((staged / "SolaceonRuins_B2F_East/map.json").read_text())
        self.assertIn("Route214-dev-overlay", names)
        self.assertTrue({"ManiacTunnel", "ManiacTunnel_B1F", *g.CONTEXT} <= names)
        self.assertEqual(len(east["warp_events"]), 3)


if __name__ == "__main__":
    unittest.main()
