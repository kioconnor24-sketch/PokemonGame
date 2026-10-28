"""Packet F corridor stage (C52): Hearthome -> Route 212 -> Pastoria -> Great Marsh, reconciled with packet E."""
import importlib.util
import json
import pathlib
import struct
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/west-packet-f"
spec = importlib.util.spec_from_file_location("packet_f_stage", HERE / "stage_packet_f.py")
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


class PacketFStageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = f.read_sources()
        cls.hdrs = f.headers(cls.files)

    def test_pins_graph_and_declared_externals_are_clean(self):
        self.assertEqual(f.check(self.files), [])
        self.assertEqual(len(f.MAPS), 57)

    def test_hearthome_keeps_packet_e_indices_and_appends_route212_doors(self):
        packet_e = f.e.headers(f.e.read_sources())["HearthomeCity"]["warp_events"]
        warps = self.hdrs["HearthomeCity"]["warp_events"]
        self.assertEqual(warps[:15], packet_e)
        self.assertEqual([(w["x"], w["y"], w["dest_map"], w["dest_warp_id"]) for w in warps[15:]],
                         [(8, 46, "MAP_ROUTE212_ACCESS", "1"), (9, 46, "MAP_ROUTE212_ACCESS", "1")])
        back = self.hdrs["Route212_Access"]["warp_events"][1]
        self.assertEqual((back["dest_map"], back["dest_warp_id"]), ("MAP_HEARTHOME_CITY", "15"))

    def test_hearthome_map_changes_only_the_two_door_collisions(self):
        w11 = self.files[f"{f.W11}/map.bin"]
        derived = f.derive(self.files)["HearthomeCity-dev-overlay/map.bin"]
        a = struct.unpack("<%dH" % (len(w11) // 2), w11)
        b = struct.unpack("<%dH" % (len(derived) // 2), derived)
        changed = [(i % f.HEARTHOME_WIDTH, i // f.HEARTHOME_WIDTH, x ^ y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
        self.assertEqual(changed, [(8, 46, 0x400), (9, 46, 0x400)])

    def test_a_reordered_w11_hearthome_is_refused(self):
        files = dict(self.files)
        h = json.loads(files[f"{f.W11}/map.json"])
        h["warp_events"] = h["warp_events"][:14]
        files[f"{f.W11}/map.json"] = json.dumps(h).encode()
        self.assertIn("W11 Hearthome order changed", f.check(files))

    def test_a_changed_crossing_source_is_refused(self):
        files = dict(self.files)
        path = f"{f.FAMILY}/staged/Route212_South/averon-map.bin"
        files[path] = b"\0\0" + files[path][2:]
        self.assertIn("Route 212 South foot crossing no longer matches its source", f.check(files))

    def test_mansion_and_marsh_are_reciprocal_and_pastoria_uses_the_stock_center(self):
        pastoria = self.hdrs["PastoriaCity"]["warp_events"]
        self.assertEqual(pastoria[2]["dest_map"], "MAP_PASTORIA_CITY_POKEMON_CENTER_1F")
        self.assertEqual(self.hdrs["PastoriaCity_PokemonCenter_1F"]["layout"], "LAYOUT_POKEMON_CENTER_1F")
        north = self.hdrs["Route212_North"]["warp_events"]
        self.assertEqual(north[2]["dest_map"], "MAP_ROUTE212_NORTH_MANSION_1F")

    def test_batch_carries_the_derived_files(self):
        with tempfile.TemporaryDirectory() as out:
            f.write_batch(self.files, out)
            staged = pathlib.Path(out) / "staged"
            hearthome = json.loads((staged / "HearthomeCity-dev-overlay/map.json").read_text())
            south_bin = (staged / "Route212_South-dev-overlay/map.bin").read_bytes()
            names = {p.name for p in staged.iterdir()}
        self.assertEqual(len(hearthome["warp_events"]), 17)
        self.assertEqual(south_bin, self.files[f"{f.CROSSING}/route212-south-map.bin"])
        self.assertTrue({"Route212_Access-dev-overlay", "GreatMarsh_West", "Route212_North_Mansion_2F"} <= names)


if __name__ == "__main__":
    unittest.main()
