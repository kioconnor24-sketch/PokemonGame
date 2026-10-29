"""C36 west packet A (narrowed, option (a)): Global Terminal 1F/2F + Oreburgh Gate B1F at slots 19-21 on the pinned base."""
import importlib.util
import json
import pathlib
import re
import struct
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = ROOT / "Averon_Codex_Handoff/design/sinnoh/west-packet-a"
ENGINE = ROOT / "engine"
spec = importlib.util.spec_from_file_location("packet_a", HERE / "install_packet_a.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
PRIOR = ["SandgemTown", "SandgemTown_PokemonCenter_1F", "Route201", "TwinleafTown", "Route202", "VerityLakefront",
         "LakeVerity", "JubilifeCity", "Route203", "OreburghGate_1F", "JubilifeCity_PokemonCenter_1F", "JubilifeCity_Mart",
         "JubilifeCity_PokemonSchool", "Route204", "RavagedPath", "FloaromaTown", "FloaromaMeadow", "Route205_South",
         "Route205_North"]


class WestPacketATest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.names, cls.files, cls.cv = p.plan(ENGINE)

    def test_engine_equals_a_fresh_install(self):
        self.assertEqual(p.check(ENGINE), [])

    def test_slots_0_to_18_unchanged_and_ten_appended(self):
        sinnoh = json.loads((ENGINE / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]
        self.assertEqual(sinnoh[:len(PRIOR) + len(self.names)], PRIOR + self.names)   # later packets append after
        self.assertEqual(self.names, ["JubilifeCity_GlobalTerminal_1F", "JubilifeCity_GlobalTerminal_2F", "OreburghGate_B1F"])
        registry = (ENGINE / p.REGISTRY).read_text()
        self.assertIn(f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {len(sinnoh)}, 1)", registry)
        slots = re.findall(r"REGISTRY_SLOT\(76, (\d+), (\w+), (\w+), 1\)", registry)
        self.assertEqual([(int(i), n) for i, _, n in slots], list(enumerate(sinnoh)))

    def test_only_existing_sections_and_layouts(self):
        sections = {s["id"] for s in json.loads((ENGINE / "src/data/region_map/region_map_sections.json").read_text())["map_sections"]}
        layouts = {l.get("id") for l in json.loads((ENGINE / "data/layouts/layouts.json").read_text())["layouts"]}
        new_layouts = set()
        for n in self.names:
            hdr = json.loads((ENGINE / f"data/maps/{n}/map.json").read_text())
            self.assertIn(hdr["region_map_section"], {"MAPSEC_JUBILIFE_CITY", "MAPSEC_OREBURGH_GATE"})
            self.assertIn(hdr["region_map_section"], sections)
            self.assertIn(hdr["layout"], layouts)
            self.assertEqual((hdr["object_events"], hdr["coord_events"], hdr["bg_events"]), ([], [], []))
            if hdr["layout"] == "LAYOUT_OREBURGH_GATE_B1F":
                new_layouts.add(hdr["layout"])
        self.assertEqual(new_layouts, {"LAYOUT_OREBURGH_GATE_B1F"})

    def test_every_new_warp_is_reciprocal_in_the_engine(self):
        names = self.names + ["JubilifeCity", "OreburghGate_1F"]
        hdrs = {json.loads((ENGINE / f"data/maps/{n}/map.json").read_text())["id"]:
                json.loads((ENGINE / f"data/maps/{n}/map.json").read_text()) for n in names}
        for mid, h in hdrs.items():
            for w in h["warp_events"]:
                if w["dest_map"] in hdrs:
                    back = hdrs[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                    self.assertEqual(back["dest_map"], mid, (mid, w))

    def test_base_snapshot_is_the_pre_integration_source(self):
        base_jub = json.loads((p.BASE / "data/maps/JubilifeCity/map.json").read_text())
        jub = json.loads((ENGINE / "data/maps/JubilifeCity/map.json").read_text())
        self.assertEqual(jub["warp_events"][:len(base_jub["warp_events"])], base_jub["warp_events"])
        added = jub["warp_events"][len(base_jub["warp_events"]):]
        self.assertEqual([(w["x"], w["y"], w["dest_map"]) for w in added],
                         [(19, 13, "MAP_JUBILIFE_CITY_GLOBAL_TERMINAL_1F"), (20, 13, "MAP_JUBILIFE_CITY_GLOBAL_TERMINAL_1F")])
        base_gate = json.loads((p.BASE / "data/maps/OreburghGate_1F/map.json").read_text())
        gate = json.loads((ENGINE / "data/maps/OreburghGate_1F/map.json").read_text())
        self.assertEqual(gate["warp_events"][:len(base_gate["warp_events"])], base_gate["warp_events"])
        self.assertEqual(gate["warp_events"][len(base_gate["warp_events"])]["dest_map"], "MAP_OREBURGH_GATE_B1F")

    def test_only_the_west_hall_door_cells_change(self):
        def cells(path):
            raw = path.read_bytes()
            return struct.unpack("<%dH" % (len(raw) // 2), raw)
        before = cells(p.BASE / "data/layouts/JubilifeCity/map.bin")
        after = cells(ENGINE / "data/layouts/JubilifeCity/map.bin")
        changed = [(i % 70, i // 70) for i, (a, b) in enumerate(zip(before, after)) if a != b]
        self.assertEqual(changed, [(19, 13), (20, 13)])
        for x, y in changed:
            self.assertEqual(after[y * 70 + x] & 0x3FF, before[y * 70 + x] & 0x3FF)
            self.assertEqual(after[y * 70 + x] & 0xC00, 0)

    def test_a_tampered_engine_file_is_reported(self):
        target = ENGINE / "data/maps/OreburghGate_B1F/scripts.inc"
        original = target.read_bytes()
        try:
            target.write_bytes(original + b"\n")
            self.assertIn("data/maps/OreburghGate_B1F/scripts.inc", p.check(ENGINE))
        finally:
            target.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
