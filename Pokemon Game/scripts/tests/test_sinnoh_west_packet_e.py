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
          "include/tilesets.h", "src/data/tilesets/headers.h", "src/data/tilesets/metatiles.h"] + list(p.COMPAT_HASHES)
D_ORDER = ["Route206_North", "Route206", "Route206_South", "Route207", p.SOUTH]
D_SECTIONS = [("MAPSEC_ROUTE_206", 228, "ROUTE 206"), ("MAPSEC_ROUTE_207", 229, "ROUTE 207"),
              ("MAPSEC_MT_CORONET", 230, "MT. CORONET")]


def cells(raw):
    return list(struct.unpack("<%dH" % (len(raw) // 2), raw))


def simulate_packet_d(eng):
    """Synthetic pre-E consumer fixture from the reviewed actual D header contract, not production acceptance.
    The west port is reopened; the east port and 2F ladder stay walled. Only what packet E reads."""
    groups = json.loads((eng / "data/maps/map_groups.json").read_text())
    if p.PACKET_D <= set(groups["gMapGroup_Sinnoh"]):
        for rel in (f"data/maps/{p.SOUTH}/map.json", f"data/layouts/{p.SOUTH}/map.bin"):
            (eng / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ENGINE / rel, eng / rel)
        return
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
    header = p.expected_south_header()
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


def pre_e_fixture(eng):
    """Test only: copy a real D tree, or undo only verified E appends in a private fixture.

    This keeps installer regression tests usable after E is actually committed;
    it never rewrites production and does not relabel fixture results as runtime QA.
    """
    for rel in INPUTS:
        (eng / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ENGINE / rel, eng / rel)
    names = json.loads((ENGINE / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]
    if names != p.BASELINE["sinnoh_prefix"] + p.SLOTS:
        simulate_packet_d(eng)
        return
    if p.check(ENGINE):
        raise AssertionError("actual installed E must verify before making the pre-E test fixture")
    _, added_layouts = p.plan_installed(ENGINE)
    groups = json.loads((eng / "data/maps/map_groups.json").read_text())
    groups["gMapGroup_Sinnoh"] = p.BASELINE["sinnoh_prefix"]
    (eng / "data/maps/map_groups.json").write_bytes(p.encode(groups))
    layouts = json.loads((eng / "data/layouts/layouts.json").read_text())
    new_ids = {layout["id"] for layout in added_layouts}
    layouts["layouts"] = [layout for layout in layouts["layouts"] if layout["id"] not in new_ids]
    (eng / "data/layouts/layouts.json").write_bytes(p.encode(layouts))
    sections = json.loads((eng / p.SECTIONS).read_text())
    sections["map_sections"] = sections["map_sections"][:-len(p.SECTIONS_NEW)]
    (eng / p.SECTIONS).write_bytes(p.encode(sections))
    registry = (eng / p.REGISTRY).read_text()
    registry = registry.replace("REGISTRY_GROUP(76, gMapGroup_Sinnoh, 83, 1)",
                                "REGISTRY_GROUP(76, gMapGroup_Sinnoh, 46, 1)")
    scripts = (eng / "data/event_scripts.s").read_text()
    for index, name in enumerate(p.SLOTS, 46):
        registry = registry.replace(f"REGISTRY_SLOT(76, {index}, {p.const(name)}, {name}, 1)\n", "")
        scripts = scripts.replace(f'\t.include "data/maps/{name}/scripts.inc"\n', "")
    (eng / p.REGISTRY).write_text(registry)
    (eng / "data/event_scripts.s").write_text(scripts)
    for rel, marker in (("src/data/tilesets/headers.h", "\nconst struct Tileset gTileset_AveronCentralOutdoorPrimary ="),
                        ("src/data/tilesets/metatiles.h", "const u16 gMetatiles_AveronCentralOutdoorPrimary[] =")):
        (eng / rel).write_text((eng / rel).read_text().split(marker, 1)[0])
    include = (eng / "include/tilesets.h").read_text()
    decls = "".join(f"extern const struct Tileset gTileset_{symbol};\n" for symbol, _, _, _ in p.TILESETS.values())
    (eng / "include/tilesets.h").write_text(include.replace("\n" + decls + "\n#endif", "\n#endif", 1))
    for rel, raw in p.compatibility_baseline(ENGINE, installed=True).items():
        (eng / rel).write_bytes(raw)
    for rel in (f"data/maps/{p.SOUTH}/map.json", f"data/layouts/{p.SOUTH}/map.bin"):
        (eng / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ENGINE / rel, eng / rel)
    (eng / f"data/maps/{p.SOUTH}/map.json").write_bytes(p.encode(p.expected_south_header()))
    path = eng / f"data/layouts/{p.SOUTH}/map.bin"
    values = cells(path.read_bytes())
    values[876] = 0x3604
    path.write_bytes(p.pack(values))


class WestPacketETest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.eng = pathlib.Path(cls.tmp.name) / "engine"
        pre_e_fixture(cls.eng)
        cls.simulated = not p.PACKET_D <= set(json.loads((ENGINE / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"])
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

    def test_changed_tileset_bindings_and_declarations_are_reported(self):
        symbol = "AveronCentralOutdoorPrimary"
        headers = "src/data/tilesets/headers.h"
        for field, changed in (("tiles", "gTilesetTiles_Rustboro"),
                               ("palettes", "gTilesetPalettes_Rustboro"),
                               ("callback", "NULL")):
            with self.subTest(field=field):
                original = p.tileset_fields(symbol, False, "General")[field]
                def change(raw, field=field, original=original, changed=changed):
                    text = raw.decode()
                    start = text.index(f"const struct Tileset gTileset_{symbol} =")
                    return (text[:start] + text[start:].replace(f".{field}={original},",
                                                              f".{field}={changed},", 1)).encode()
                self.assertIn(headers, self.mutated(headers, change))
        declarations = "src/data/tilesets/metatiles.h"
        for declaration in p.metatile_declarations(symbol, False):
            with self.subTest(declaration=declaration):
                self.assertIn(declarations, self.mutated(declarations, lambda raw: raw.replace(
                    declaration.encode(), declaration.replace(".bin", "-wrong.bin").encode(), 1)))
        include = "include/tilesets.h"
        declaration = f"extern const struct Tileset gTileset_{symbol};"
        self.assertIn(include, self.mutated(include, lambda raw: raw.replace(declaration.encode(), b"", 1)))

    def test_paired_origin_pins_preserve_old_values_and_reject_reassignment(self):
        pins = json.loads((self.eng / p.COMPAT_PINS).read_text())["pins"]
        baseline = json.loads(p.compatibility_baseline(self.eng, installed=True)[p.COMPAT_PINS])["pins"]
        self.assertEqual({key: pins[key] for key in baseline}, baseline)
        self.assertEqual({key: value for key, value in pins.items() if key not in baseline},
                         {symbol: value for symbol, value, _ in p.SECTIONS_NEW})
        def change(raw):
            data = json.loads(raw)
            data["pins"]["MAPSEC_AMITY_SQUARE"] = 237
            return p.encode(data)
        self.assertTrue(any("saved-origin pin differs" in error
                            for error in self.mutated(p.COMPAT_PINS, change)))

    def test_install_refuses_changed_legacy_assertions_and_existing_untracked_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            eng = pathlib.Path(tmp) / "engine"
            pre_e_fixture(eng)
            target = eng / p.COMPAT_FILE
            original = target.read_bytes()
            self.assertIn(b"MAPSEC_NONE == 215", original)
            target.write_bytes(original.replace(b"MAPSEC_NONE == 215", b"MAPSEC_NONE == 214", 1))
            with self.assertRaisesRegex(SystemExit, "native assertions or saved-origin pins"):
                p.install(eng)
            self.assertFalse((eng / "data/maps/Route208/map.json").exists())
            target.write_bytes(original)
            existing = eng / "data/maps/Route208/scripts.inc"
            existing.parent.mkdir(parents=True)
            existing.write_text("preserve existing work")
            with self.assertRaisesRegex(SystemExit, "existing/untracked E output"):
                p.install(eng)
            self.assertEqual(existing.read_text(), "preserve existing work")
            self.assertFalse((eng / "data/maps/Route208/map.json").exists())

    def test_installed_new_interior_layout_and_blockdata_tampering_are_rejected(self):
        _, added = p.plan_installed(self.eng)
        layout = next(l for l in added if l["name"].removesuffix("_Layout") not in p.stage.OUTDOORS)
        rel = layout["blockdata_filepath"]
        self.assertIn(rel, self.mutated(rel, lambda raw: bytes([raw[0] ^ 1]) + raw[1:]))
        path = "data/layouts/layouts.json"
        for mode in ("width", "duplicate"):
            with self.subTest(mode=mode):
                def change(raw):
                    data = json.loads(raw)
                    if mode == "duplicate":
                        data["layouts"].append(dict(data["layouts"][-1]))
                    else:
                        target = next(l for l in data["layouts"] if l["id"] == layout["id"])
                        target["width"] += 1
                    return p.encode(data)
                self.assertIn(path, self.mutated(path, change))

    def mutated(self, rel, change):
        """check() with one engine file changed in place, then restored."""
        target = self.eng / rel
        original = target.read_bytes()
        try:
            target.write_bytes(change(original))
            return p.check(self.eng)
        finally:
            target.write_bytes(original)

    def test_a_changed_non_seam_coronet_south_cell_is_reported(self):
        def change(raw):
            values = cells(raw)
            values[10 * 42 + 10] ^= 0x400
            return struct.pack("<%dH" % len(values), *values)
        self.assertIn("Coronet South's blockdata differs from packet D's pinned baseline",
                      self.mutated(f"data/layouts/{p.SOUTH}/map.bin", change))

    def test_a_changed_coronet_south_return_index_is_reported(self):
        def change(raw):
            header = json.loads(raw)
            header["warp_events"][0]["dest_warp_id"] = "3"
            return json.dumps(header).encode()
        self.assertIn("Coronet South's packet D warps differ from the pinned baseline",
                      self.mutated(f"data/maps/{p.SOUTH}/map.json", change))

    def test_changed_coronet_south_non_warp_header_fields_are_reported(self):
        rel = f"data/maps/{p.SOUTH}/map.json"
        for field, value in (("region_map_section", "MAPSEC_ROUTE_201"), ("region", "REGION_HOENN"),
                             ("layout", "LAYOUT_OTHER"), ("map_type", "MAP_TYPE_ROUTE"),
                             ("music", "MUS_ROUTE110")):
            with self.subTest(field=field):
                def change(raw, field=field, value=value):
                    header = json.loads(raw)
                    header[field] = value
                    return json.dumps(header).encode()
                self.assertIn("Coronet South's complete header differs from the pinned production baseline",
                              self.mutated(rel, change))

    def test_install_refuses_wrong_south_section_with_warps_and_cells_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            eng = pathlib.Path(tmp) / "engine"
            pre_e_fixture(eng)
            target = eng / f"data/maps/{p.SOUTH}/map.json"
            header = json.loads(target.read_text())
            header["region_map_section"] = "MAPSEC_ROUTE_201"
            target.write_text(json.dumps(header))
            with self.assertRaisesRegex(SystemExit, "complete header"):
                p.install(eng)

    def test_a_reordered_existing_slot_is_reported(self):
        def change(raw):
            groups = json.loads(raw)
            s = groups["gMapGroup_Sinnoh"]
            s[3], s[4] = s[4], s[3]
            return json.dumps(groups).encode()
        self.assertIn("gMapGroup_Sinnoh is not the pinned prefix followed by packet E",
                      self.mutated("data/maps/map_groups.json", change))

    def test_install_refuses_a_reordered_or_changed_packet_d_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            eng = pathlib.Path(tmp) / "engine"
            pre_e_fixture(eng)
            header = json.loads((eng / f"data/maps/{p.SOUTH}/map.json").read_text())
            header["warp_events"][0]["dest_warp_id"] = "1"
            (eng / f"data/maps/{p.SOUTH}/map.json").write_text(json.dumps(header))
            with self.assertRaises(SystemExit):
                p.install(eng)

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
