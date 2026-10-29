"""West packet B: W28's Floaroma interiors, W23's Route 205 South house and W5's Valley Windworks at slots 22-29."""
import importlib.util
import json
import pathlib
import re
import shutil
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/west-packet-b"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("packet_b", HERE / "install_packet_b.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
# The engine files the packet reads (pre-install), copied into a scratch engine so the install never touches ENGINE.
INPUTS = ["data/maps/map_groups.json", "data/layouts/layouts.json", "data/event_scripts.s", p.REGISTRY,
          "include/tilesets.h", "src/data/tilesets/headers.h", "src/data/tilesets/metatiles.h",
          "data/maps/JubilifeCity_Mart/map.json", "src/data/region_map/region_map_sections.json",
          "data/tilesets/primary/building/metatiles.bin", "data/tilesets/primary/building/metatile_attributes.bin"]


def installed(engine):
    return len(json.loads((engine / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]) > p.PRIOR_SLOTS


class WestPacketBTest(unittest.TestCase):
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

    def test_the_engine_is_either_untouched_or_exactly_installed(self):
        if installed(ENGINE):
            self.assertEqual(p.check(ENGINE), [])
        else:
            for town in ("FloaromaTown", "FloaromaMeadow", "Route205_South", "Route205_North"):
                self.assertEqual((ENGINE / f"data/maps/{town}/map.json").read_bytes(),
                                 (p.BASE / f"data/maps/{town}/map.json").read_bytes(), town)

    def test_slots_0_to_21_unchanged_and_eight_appended(self):
        sinnoh = json.loads((self.eng / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]
        self.assertGreaterEqual(len(sinnoh), 30)                    # later packets append after slot 29
        self.assertEqual(sinnoh[21], "OreburghGate_B1F")
        self.assertEqual(sinnoh[22:30], p.SLOTS)
        registry = (self.eng / p.REGISTRY).read_text()
        self.assertIn(f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {len(sinnoh)}, 1)", registry)
        slots = re.findall(r"REGISTRY_SLOT\(76, (\d+), (\w+), (\w+), 1\)", registry)
        self.assertEqual([(int(i), n) for i, _, n in slots], list(enumerate(sinnoh)))
        self.assertIn(("22", "MAP_FLOAROMA_TOWN_FLOWER_SHOP", "FloaromaTown_FlowerShop"), slots)
        self.assertIn(("27", "MAP_ROUTE205_SOUTH_HOUSE", "Route205_South_House"), slots)
        self.assertIn(("29", "MAP_VALLEY_WINDWORKS_INSIDE", "ValleyWindworks_Inside"), slots)

    def test_only_existing_sections_and_neutral_rooms(self):
        sections = {s["id"] for s in json.loads(
            (self.eng / "src/data/region_map/region_map_sections.json").read_text())["map_sections"]}
        for name in p.SLOTS:
            hdr = self.header(name)
            self.assertIn(hdr["region_map_section"], sections)
            self.assertEqual(hdr["region_map_section"],
                             "MAPSEC_FLOAROMA_TOWN" if name in p.ROOMS else "MAPSEC_ROUTE_205")
            self.assertEqual((hdr["object_events"], hdr["coord_events"], hdr["bg_events"]), ([], [], []))
            self.assertEqual(hdr["map_type"], "MAP_TYPE_ROUTE" if name == "ValleyWindworks" else "MAP_TYPE_INDOOR")

    def test_new_layouts_use_the_production_tileset_pair(self):
        layouts = {l.get("id"): l for l in json.loads((self.eng / "data/layouts/layouts.json").read_text())["layouts"]}
        for room in p.ROOMS:
            l = layouts[p.const(room, "LAYOUT_")]
            self.assertEqual((l["primary_tileset"], l["secondary_tileset"]),
                             ("gTileset_Building", "gTileset_AveronFloaromaInteriorSecondary"))
            self.assertEqual((self.eng / l["border_filepath"]).read_bytes(), b"\x01\x00" * 4)   # black void
            self.assertEqual((self.eng / l["blockdata_filepath"]).stat().st_size, l["width"] * l["height"] * 2)
        self.assertEqual(self.header(p.HOUSE)["layout"], "LAYOUT_HOUSE1")
        for name, (w, h, primary, secondary) in p.WINDWORKS.items():     # stock banks, no new tileset
            l = layouts[p.const(name, "LAYOUT_")]
            self.assertEqual((l["width"], l["height"], l["primary_tileset"], l["secondary_tileset"]),
                             (w, h, primary, secondary))
        self.assertFalse(any("Claude" in (l.get("primary_tileset", "") + l.get("secondary_tileset", ""))
                             for l in layouts.values()))

    def test_tileset_pair_binds_stock_building_and_shop_graphics(self):
        headers = (self.eng / "src/data/tilesets/headers.h").read_text()
        self.assertNotIn("AveronFloaromaInteriorPrimary", headers)        # stock gTileset_Building serves as primary
        for sym, tiles, secondary in (("AveronFloaromaInteriorSecondary", "gTilesetTiles_Shop", "TRUE"),):
            block = re.search(r"const struct Tileset gTileset_" + sym + r" =\s*\{(.*?)\};", headers, re.S)[1]
            self.assertIn(f".tiles={tiles},", block)
            self.assertIn(f".isSecondary={secondary}", block)
            self.assertIn(f".metatiles=gMetatiles_{sym},", block)
        for t in json.loads((p.W28 / "staged/tilesets.json").read_text()):
            if t["secondary"]:
                dest = self.eng / f"data/tilesets/secondary/{p.folder(p.TILESETS[True])}"
                self.assertEqual((dest / "metatiles.bin").read_bytes(), (p.W28 / t["metatiles"]).read_bytes())
            else:
                stock = (ENGINE / "data/tilesets/primary/building/metatiles.bin").read_bytes()
                packed = (p.W28 / t["metatiles"]).read_bytes()
                self.assertEqual(stock[:len(packed)], packed)

    def test_every_new_warp_is_reciprocal(self):
        names = p.SLOTS + ["FloaromaTown", "FloaromaMeadow", "Route205_South", "Route205_North"]
        hdrs = {self.header(n)["id"]: self.header(n) for n in names}
        for mid, h in hdrs.items():
            for w in h["warp_events"]:
                if w["dest_map"] in hdrs:
                    back = hdrs[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                    self.assertEqual(back["dest_map"], mid, (mid, w))

    def test_production_maps_gain_only_appended_door_warps_and_windworks_connections(self):
        doors = {"FloaromaTown": [(22, 13), (13, 16), (26, 19), (26, 28)], "FloaromaMeadow": [(35, 41)],
                 "Route205_South": [(21, 22)], "Route205_North": []}
        joins = {"Route205_South": [("right", 0)], "Route205_North": [("down", 9)]}
        for town, added in doors.items():
            base = json.loads((p.BASE / f"data/maps/{town}/map.json").read_text())
            hdr = self.header(town)
            keep = ("warp_events", "connections")
            self.assertEqual({k: v for k, v in hdr.items() if k not in keep},
                             {k: v for k, v in base.items() if k not in keep})
            self.assertEqual(hdr["warp_events"][:len(base["warp_events"])], base["warp_events"])
            self.assertEqual([(w["x"], w["y"]) for w in hdr["warp_events"][len(base["warp_events"]):]], added)
            self.assertEqual(hdr["connections"][:len(base["connections"])], base["connections"])
            self.assertEqual([(c["direction"], c["offset"]) for c in hdr["connections"][len(base["connections"]):]
                              if c["map"] == "MAP_VALLEY_WINDWORKS"], joins.get(town, []))
            self.assertEqual(len(hdr["connections"]) - len(base["connections"]), len(joins.get(town, [])))
        self.assertFalse(any((self.eng / f"data/layouts/{t}/map.bin").exists() and self.eng != ENGINE for t in doors))

    def test_windworks_connections_are_reciprocal(self):
        vw = self.header("ValleyWindworks")
        pairs = {"left": "right", "up": "down"}
        for c in vw["connections"]:
            other = self.header({"MAP_ROUTE205_SOUTH": "Route205_South", "MAP_ROUTE205_NORTH": "Route205_North"}[c["map"]])
            back = [b for b in other["connections"] if b["map"] == "MAP_VALLEY_WINDWORKS"]
            self.assertEqual([(b["direction"], b["offset"]) for b in back], [(pairs[c["direction"]], -c["offset"])])

    def test_a_tampered_engine_file_is_reported(self):
        if self.eng == ENGINE:
            self.skipTest("only on the scratch install")
        target = self.eng / "data/maps/FloaromaTown_Mart/scripts.inc"
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\n")
            self.assertIn("data/maps/FloaromaTown_Mart/scripts.inc", p.check(self.eng))
        finally:
            target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
