"""West packet C: production Oreburgh City (section 227) and W21's ten interiors at slots 30-40."""
import hashlib
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
        self.assertGreaterEqual(len(sinnoh), 41)
        self.assertEqual((sinnoh[29], sinnoh[30:41]), ("ValleyWindworks_Inside", p.SLOTS))
        registry = (self.eng / p.REGISTRY).read_text()
        self.assertIn(f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {len(sinnoh)}, 1)", registry)
        slots = re.findall(r"REGISTRY_SLOT\(76, (\d+), (\w+), (\w+), 1\)", registry)
        self.assertEqual([(int(i), n) for i, _, n in slots], list(enumerate(sinnoh)))
        self.assertIn(("30", "MAP_OREBURGH_CITY", "OreburghCity"), slots)

    def test_section_227_and_complete_installed_prefix_stay_fixed(self):
        document = json.loads((self.eng / p.SECTIONS).read_text())
        sections = document["map_sections"]
        index = next(i for i, section in enumerate(sections) if section["id"] == p.SECTION["id"])
        self.assertEqual(sections[index], p.SECTION)
        prefix = dict(document, map_sections=sections[:index + 1])
        self.assertEqual(hashlib.sha256(p.encode(prefix)).hexdigest(),
                         "89c14b9186efc42f345c49b84481b6448432458825fde3a2f4b58073b426db82")
        self.assertEqual(sections[index - 1]["id"], "MAPSEC_ROUTE_205")
        self.assertEqual(sections[index - 1]["value"], 226)
        for name in p.SLOTS:
            hdr = self.header(name)
            self.assertEqual(hdr["region_map_section"], "MAPSEC_OREBURGH_CITY")
            self.assertEqual((hdr["object_events"], hdr["coord_events"], hdr["bg_events"]), ([], [], []))

    def test_route207_and_mine_stay_closed(self):
        city = self.header("OreburghCity")
        self.assertEqual(city["connections"], [p.CITY_ROUTE207_JOIN] if p.has_production_route207_join(self.eng) else [])
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

    def test_only_the_registered_reciprocal_later_route207_join_is_accepted(self):
        # A disposable copy exercises C's consumer after D without mutating
        # production or pretending the synthetic headers are D acceptance.
        with tempfile.TemporaryDirectory() as tmp:
            engine = pathlib.Path(tmp) / "engine"
            payload, _ = p.plan(self.eng)
            for rel in set(INPUTS) | set(payload):
                target = engine / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(self.eng / rel, target)
            groups = json.loads((engine / "data/maps/map_groups.json").read_text())
            groups["gMapGroup_Sinnoh"] = groups["gMapGroup_Sinnoh"][:41] + p.D_SLOTS
            (engine / "data/maps/map_groups.json").write_text(json.dumps(groups))
            route = engine / "data/maps/Route207/map.json"
            route.parent.mkdir(exist_ok=True)
            header = dict(id="MAP_ROUTE207", region="REGION_SINNOH", region_map_section="MAPSEC_ROUTE_207",
                          connections=[dict(map="MAP_OREBURGH_CITY", offset=-35, direction="down")])
            route.write_text(json.dumps(header))
            city_path = engine / "data/maps/OreburghCity/map.json"
            city = json.loads(city_path.read_text())
            city["connections"] = [dict(p.CITY_ROUTE207_JOIN)]
            city_path.write_bytes(p.encode(city))
            self.assertEqual(p.check(engine), [])
            header["connections"][0]["offset"] = -34
            route.write_text(json.dumps(header))
            self.assertIn("data/maps/OreburghCity/map.json", p.check(engine))
            header["connections"][0]["offset"] = -35
            route.write_text(json.dumps(header))
            city["connections"].append(dict(map="MAP_ROUTE208", offset=0, direction="right"))
            city_path.write_bytes(p.encode(city))
            self.assertIn("data/maps/OreburghCity/map.json", p.check(engine))


if __name__ == "__main__":
    unittest.main()
