"""West packet C: production Oreburgh City (section 227) and W21's ten interiors at slots 30-40."""
import importlib.util
import json
import pathlib
import re
import shutil
import struct
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/west-packet-c"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("packet_c", HERE / "install_packet_c.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
INPUTS = ["data/maps/map_groups.json", "data/layouts/layouts.json", "data/event_scripts.s", p.REGISTRY, p.SECTIONS,
          "include/tilesets.h", "src/data/tilesets/headers.h", "src/data/tilesets/metatiles.h",
          "data/maps/JubilifeCity_Mart/map.json"]


def installed(engine):
    return len(json.loads((engine / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]) > p.PRIOR_SLOTS


def cells(raw):
    return struct.unpack("<%dH" % (len(raw) // 2), raw)


class WestPacketCTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.eng = pathlib.Path(cls.tmp.name) / "engine"
        if installed(ENGINE):                       # the engine already carries the packet: test it as it is
            cls.eng = ENGINE
            return
        for rel in INPUTS:
            (cls.eng / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ENGINE / rel, cls.eng / rel)
        p.install(cls.eng)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def header(self, name):
        return json.loads((self.eng / f"data/maps/{name}/map.json").read_text())

    def test_a_fresh_install_checks_clean_and_refuses_to_run_twice(self):
        self.assertEqual(p.check(self.eng), [])
        if self.eng != ENGINE:
            with self.assertRaises(SystemExit):
                p.install(self.eng)

    def test_slots_0_to_29_unchanged_and_eleven_appended(self):
        sinnoh = json.loads((self.eng / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]
        self.assertEqual((len(sinnoh), sinnoh[29], sinnoh[30:]), (41, "ValleyWindworks_Inside", p.SLOTS))
        registry = (self.eng / p.REGISTRY).read_text()
        self.assertIn("REGISTRY_GROUP(76, gMapGroup_Sinnoh, 41, 1)", registry)
        slots = re.findall(r"REGISTRY_SLOT\(76, (\d+), (\w+), (\w+), 1\)", registry)
        self.assertEqual([(int(i), n) for i, _, n in slots], list(enumerate(sinnoh)))
        self.assertIn(("30", "MAP_OREBURGH_CITY", "OreburghCity"), slots)

    def test_section_227_is_the_only_new_code(self):
        sections = json.loads((self.eng / p.SECTIONS).read_text())["map_sections"]
        before = json.loads((ENGINE / p.SECTIONS).read_text())["map_sections"] if self.eng != ENGINE else sections[:-1]
        self.assertEqual(sections[:len(before)], before)
        self.assertEqual(sections[len(before):], [p.SECTION])
        for name in p.SLOTS:
            hdr = self.header(name)
            self.assertEqual(hdr["region_map_section"], "MAPSEC_OREBURGH_CITY")
            self.assertEqual((hdr["object_events"], hdr["coord_events"], hdr["bg_events"]), ([], [], []))

    def test_route207_and_mine_stay_closed(self):
        city = self.header("OreburghCity")
        self.assertEqual(city["connections"], [])
        self.assertFalse(any("MINE" in w["dest_map"] or "ROUTE207" in w["dest_map"] for w in city["warp_events"]))
        raw = cells((self.eng / "data/layouts/OreburghCity/map.bin").read_bytes())
        for x, y in p.MINE_CELLS:
            self.assertEqual((raw[y * p.CITY_WIDTH + x] >> 10) & 3, 1, (x, y))

    def test_every_warp_is_reciprocal_including_the_gate(self):
        names = p.SLOTS + ["OreburghGate_1F"]
        hdrs = {self.header(n)["id"]: self.header(n) for n in names}
        for mid, h in hdrs.items():
            for w in h["warp_events"]:
                if w["dest_map"] in hdrs:
                    back = hdrs[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                    self.assertEqual(back["dest_map"], mid, (mid, w))
        gate = self.header("OreburghGate_1F")
        base = json.loads((p.BASE / "data/maps/OreburghGate_1F/map.json").read_text())
        self.assertEqual(gate["warp_events"][:2], base["warp_events"])          # Route 203, packet A's B1F ladder
        self.assertEqual(gate["warp_events"][2]["dest_map"], "MAP_OREBURGH_CITY")

    def test_gate_changes_only_the_four_east_cells(self):
        before = cells((p.BASE / "data/layouts/OreburghGate_1F/map.bin").read_bytes())
        after = cells((self.eng / "data/layouts/OreburghGate_1F/map.bin").read_bytes())
        changed = sorted((i % 29, i // 29) for i, (a, b) in enumerate(zip(before, after)) if a != b)
        self.assertEqual(changed, sorted([(25, 20), (24, 21), (25, 21), (26, 21)]))

    def test_city_tileset_pair_binds_stock_general_and_rustboro(self):
        headers = (self.eng / "src/data/tilesets/headers.h").read_text()
        for sym, tiles in (("AveronOreburghCityPrimary", "gTilesetTiles_General"),
                           ("AveronOreburghCitySecondary", "gTilesetTiles_Rustboro")):
            block = re.search(r"const struct Tileset gTileset_" + sym + r" =\s*\{(.*?)\};", headers, re.S)[1]
            self.assertIn(f".tiles={tiles},", block)
            self.assertIn(f".metatiles=gMetatiles_{sym},", block)
        self.assertNotIn("OreburghCandidate", headers)

    def test_a_tampered_engine_file_is_reported(self):
        if self.eng == ENGINE:
            self.skipTest("only on the scratch install")
        target = self.eng / "data/maps/OreburghCity_Mart/scripts.inc"
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\n")
            self.assertIn("data/maps/OreburghCity_Mart/scripts.inc", p.check(self.eng))
        finally:
            target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
