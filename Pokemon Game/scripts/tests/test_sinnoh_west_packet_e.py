"""Packet E production installer: 37 maps after packet D, sections 231-238, Route 208 <-> Coronet South reopened."""
import importlib.util
import json
import pathlib
import shutil
import struct
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/west-packet-e"
ENGINE = ROOT / "engine"
D_INPUTS = ROOT / "Averon_Codex_Handoff/design/sinnoh/west-packet-d/inputs"
spec = importlib.util.spec_from_file_location("packet_e_install", HERE / "install_packet_e.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
INPUTS = ["data/maps/map_groups.json", "data/layouts/layouts.json", "data/event_scripts.s", p.REGISTRY, p.SECTIONS,
          "include/tilesets.h", "src/data/tilesets/headers.h", "src/data/tilesets/metatiles.h"]
D_ORDER = ["Route206_North", "Route206", "Route206_South", "Route207", p.SOUTH]
D_SECTIONS = [("MAPSEC_ROUTE_206", 228, "ROUTE 206"), ("MAPSEC_ROUTE_207", 229, "ROUTE 207"),
              ("MAPSEC_MT_CORONET", 230, "MT. CORONET")]


def cells(raw):
    return list(struct.unpack("<%dH" % (len(raw) // 2), raw))


def simulate_packet_d(eng):
    """Until packet D is on main: its five slots, sections 228-230 and Coronet South exactly as #347 builds it
    (west-packet-d inputs; west port reopened, east port and 2F ladder walled). Only what packet E reads."""
    groups = json.loads((eng / "data/maps/map_groups.json").read_text())
    last = groups["gMapGroup_Sinnoh"][-1]
    n = len(groups["gMapGroup_Sinnoh"])
    groups["gMapGroup_Sinnoh"] += D_ORDER
    (eng / "data/maps/map_groups.json").write_text(json.dumps(groups, indent=2) + "\n")
    scripts = (eng / "data/event_scripts.s").read_text()
    inc = f'\t.include "data/maps/{last}/scripts.inc"\n'
    (eng / "data/event_scripts.s").write_text(scripts.replace(
        inc, inc + "".join(f'\t.include "data/maps/{m}/scripts.inc"\n' for m in D_ORDER), 1))
    reg = (eng / p.REGISTRY).read_text().replace(f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {n}, 1)",
                                                 f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {n + 5}, 1)")
    reg += "".join(f"REGISTRY_SLOT(76, {i}, {p.const(m)}, {m}, 1)\n" for i, m in enumerate(D_ORDER, n))
    (eng / p.REGISTRY).write_text(reg)
    sections = json.loads((eng / p.SECTIONS).read_text())
    sections["map_sections"] += [dict(id=i, value=v, name=t, region="REGION_SINNOH") for i, v, t in D_SECTIONS]
    (eng / p.SECTIONS).write_text(json.dumps(sections, indent=2) + "\n")
    header = json.loads((D_INPUTS / "source-header.json").read_text())
    header.update(warp_events=[dict(x=5, y=7, elevation=0, dest_map="MAP_ROUTE207", dest_warp_id="0")],
                  region_map_section="MAPSEC_MT_CORONET")
    (eng / f"data/maps/{p.SOUTH}").mkdir(parents=True)
    (eng / f"data/maps/{p.SOUTH}/map.json").write_text(json.dumps(header, indent=2) + "\n")
    raw = cells((D_INPUTS / "averon-map.bin").read_bytes())
    raw[299], raw[876], raw[113] = 0x321A, 0x3604, 0x3604
    (eng / f"data/layouts/{p.SOUTH}").mkdir(parents=True)
    (eng / f"data/layouts/{p.SOUTH}/map.bin").write_bytes(struct.pack("<%dH" % len(raw), *raw))
    layouts = json.loads((eng / "data/layouts/layouts.json").read_text())
    layouts["layouts"].append(dict(id=header["layout"], name=p.SOUTH + "_Layout", width=42, height=32,
                                   primary_tileset="gTileset_General", secondary_tileset="gTileset_Cave",
                                   border_filepath=f"data/layouts/{p.SOUTH}/border.bin",
                                   blockdata_filepath=f"data/layouts/{p.SOUTH}/map.bin"))
    (eng / "data/layouts/layouts.json").write_text(json.dumps(layouts, indent=2) + "\n")


class WestPacketETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.eng = pathlib.Path(cls.tmp.name) / "engine"
        for rel in INPUTS:
            (cls.eng / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ENGINE / rel, cls.eng / rel)
        sinnoh = json.loads((ENGINE / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]
        cls.simulated = not p.PACKET_D <= set(sinnoh)
        if cls.simulated:
            simulate_packet_d(cls.eng)
        else:                                          # real packet D on main: copy its Coronet South
            for rel in (f"data/maps/{p.SOUTH}/map.json",
                        p.layout_of(ENGINE, json.loads((ENGINE / f"data/maps/{p.SOUTH}/map.json").read_text())["layout"])["blockdata_filepath"]):
                (cls.eng / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ENGINE / rel, cls.eng / rel)
        cls.before = json.loads((cls.eng / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]
        cls.south_before = (cls.eng / f"data/layouts/{p.SOUTH}/map.bin").read_bytes() if cls.simulated else None
        p.install(cls.eng)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def header(self, name):
        return json.loads((self.eng / f"data/maps/{name}/map.json").read_text())

    def test_a_fresh_install_checks_clean_and_refuses_to_run_twice(self):
        self.assertEqual(p.check(self.eng), [])
        with self.assertRaises(SystemExit):
            p.install(self.eng)

    def test_install_refuses_without_packet_d(self):
        with tempfile.TemporaryDirectory() as tmp:
            eng = pathlib.Path(tmp) / "engine"
            for rel in INPUTS:
                (eng / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ENGINE / rel, eng / rel)
            groups = json.loads((eng / "data/maps/map_groups.json").read_text())
            groups["gMapGroup_Sinnoh"] = [m for m in groups["gMapGroup_Sinnoh"] if m not in p.PACKET_D | set(p.SLOTS)]
            (eng / "data/maps/map_groups.json").write_text(json.dumps(groups))
            with self.assertRaises(SystemExit):
                p.install(eng)

    def test_37_slots_follow_packet_d_and_registry_matches(self):
        sinnoh = json.loads((self.eng / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]
        self.assertEqual(sinnoh, self.before + p.SLOTS)
        self.assertEqual(len(p.SLOTS), 37)
        registry = (self.eng / p.REGISTRY).read_text()
        self.assertIn(f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {len(sinnoh)}, 1)", registry)
        for i, m in enumerate(sinnoh):
            self.assertIn(f"REGISTRY_SLOT(76, {i}, {p.const(m)}, {m}, 1)", registry)

    def test_sections_231_to_238_are_appended_and_assigned(self):
        entries = json.loads((self.eng / p.SECTIONS).read_text())["map_sections"]
        self.assertEqual([(e["id"], e["value"], e["name"]) for e in entries[-8:]], p.SECTIONS_NEW)
        self.assertEqual(entries[-9]["value"], p.LAST_D_SECTION)
        expect = {"Route208_House1": "MAPSEC_ROUTE_208", "HearthomeCity_ContestHall": "MAPSEC_HEARTHOME_CITY",
                  "Route209_Access": "MAPSEC_ROUTE_209", "SolaceonTown_Mart": "MAPSEC_SOLACEON_TOWN",
                  "SolaceonRuins_B3F_Sanctum": "MAPSEC_SOLACEON_RUINS", "LostTower_6F": "MAPSEC_LOST_TOWER",
                  "Route210_South_House1": "MAPSEC_ROUTE_210", "AmitySquare": "MAPSEC_AMITY_SQUARE"}
        for name, section in expect.items():
            self.assertEqual(self.header(name)["region_map_section"], section, name)
        self.assertFalse({self.header(m)["region_map_section"] for m in p.SLOTS}
                         & {"MAPSEC_PENDING_OWNER", "MAPSEC_ROUTE_201"})

    def test_route208_and_coronet_south_reopen_one_cell_each_as_a_reciprocal_pair(self):
        r208 = self.header("Route208")["warp_events"]
        south = self.header(p.SOUTH)["warp_events"]
        self.assertEqual((r208[2]["x"], r208[2]["y"], r208[2]["dest_map"], r208[2]["dest_warp_id"]),
                         (8, 19, "MAP_MT_CORONET_1F_SOUTH", "1"))
        self.assertEqual((south[1]["x"], south[1]["y"], south[1]["dest_map"], south[1]["dest_warp_id"]),
                         (36, 20, "MAP_ROUTE208", "2"))
        self.assertEqual(south[0]["dest_map"], "MAP_ROUTE207")
        staged = cells((p.CENTRAL / "staged/Route208/averon-map.bin").read_bytes())
        after = cells((self.eng / "data/layouts/Route208/map.bin").read_bytes())
        self.assertEqual([(i % 68, i // 68, hex(b)) for i, (a, b) in enumerate(zip(staged, after)) if a != b],
                         [(8, 19, "0xa7")])
        if self.simulated:
            before = cells(self.south_before)
            south_after = cells((self.eng / f"data/layouts/{p.SOUTH}/map.bin").read_bytes())
            self.assertEqual([(i % 42, i // 42, hex(b)) for i, (a, b) in enumerate(zip(before, south_after)) if a != b],
                             [(36, 20, "0x321a")])

    def test_only_route209_triggers_and_no_gameplay_objects(self):
        for name in p.SLOTS:
            h = self.header(name)
            self.assertEqual((h["object_events"], h["bg_events"]), ([], []), name)
            coords = h["coord_events"]
            if name == "Route209":
                self.assertEqual(len(coords), 4)
                self.assertEqual({c["var"] for c in coords}, {"VAR_TEMP_1"})
                script = (self.eng / "data/maps/Route209/scripts.inc").read_text()
                for c in coords:
                    self.assertIn(c["script"] + "::", script)
            else:
                self.assertEqual(coords, [], name)

    def test_outdoor_banks_bind_existing_graphics(self):
        headers = (self.eng / "src/data/tilesets/headers.h").read_text()
        for symbol, _, graphics, _ in p.TILESETS.values():
            block = headers.split(f"const struct Tileset gTileset_{symbol} =", 1)[1].split("};", 1)[0]
            existing = headers.split(f"const struct Tileset gTileset_{graphics} =", 1)[1].split("};", 1)[0]
            tiles = existing.split(".tiles", 1)[1].split("=", 1)[1].split(",", 1)[0].strip()
            self.assertIn(f".tiles={tiles},", block)

    def test_a_tampered_engine_file_is_reported(self):
        target = self.eng / "data/maps/LostTower_3F/map.json"
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\n")
            self.assertIn("data/maps/LostTower_3F/map.json", p.check(self.eng))
        finally:
            target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
