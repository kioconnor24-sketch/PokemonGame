"""Current W25 DEV scene retains accepted maps, B1F and every old save identity."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest
from unittest import mock

# Historical DEV/source receipt replay uses its exact accepted checkout.
# Production installer tests remain bound to the current checkout.
from sinnoh_replay_fixture import post_c_source_root
ROOT = post_c_source_root(Path(__file__).resolve().parents[3])

HERE = ROOT / "Pokemon Game/Averon_Codex_Handoff/design/sinnoh/cycling-road-join"
spec = importlib.util.spec_from_file_location("cycling_current", HERE / "prepare_current_runtime.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CyclingCurrentRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = m.current_inputs(ROOT)
        cls.old = m.legacy.current_inputs()
        cls.legacy, _ = m.legacy.assemble(ROOT)
        cls.files, cls.receipt = m.compose(ROOT)

    def test_all_accepted_slots_and_all_existing_layouts_remain_ordered(self):
        before = json.loads(self.current[m.GROUPS])["gMapGroup_Sinnoh"]
        after = json.loads(self.files[m.GROUPS])["gMapGroup_Sinnoh"]
        self.assertIn(len(before), (22, 30, 41))
        self.assertEqual(after[:len(before)], before)
        # After west packet C the City is production, so W25 appends Route207 and the mines only.
        self.assertEqual(len(after), len(before) + (8 if "OreburghCity" in before else 9))
        layouts = json.loads(self.current[m.LAYOUTS])["layouts"]
        self.assertEqual(json.loads(self.files[m.LAYOUTS])["layouts"][:len(layouts)], layouts)

    def test_gate_ladder_and_city_returns_have_separate_reciprocal_indices(self):
        gate = json.loads(self.files[m.GATE])["warp_events"]
        self.assertEqual(gate[:2], json.loads(self.current[m.GATE])["warp_events"][:2])
        self.assertEqual(len(gate), 3)
        self.assertEqual(gate[2]["dest_map"], "MAP_OREBURGH_CITY")
        city = json.loads(self.files["data/maps/OreburghCity/map.json"])
        self.assertEqual(city["warp_events"][0]["dest_warp_id"], "2")
        self.assertNotIn("data/maps/OreburghGate_B1F/map.json", self.files)

    def test_b1f_ladder_graphic_survives_disjoint_east_restoration(self):
        path = "data/layouts/OreburghGate_1F/map.bin"
        words = lambda b: struct.unpack("<%dH" % (len(b) // 2), b)
        current, after = words(self.current[path]), words(self.files[path])
        self.assertEqual(after[163], 0x323F)
        self.assertEqual([i for i, (a, b) in enumerate(zip(current, after)) if a != b],
                         [] if m.production_city(self.current) else [605, 633, 634, 635])

    def test_nine_original_seam_pairs_and_every_donor_physics_word_are_reused(self):
        join = m.load("join_fixture", HERE / "build_cycling_road_join.py")
        a, b, ca, cb, pairs, _ = join.build()
        self.assertEqual(len(pairs), 9)
        self.assertEqual(self.files["data/layouts/Route206/map.bin"], struct.pack("<%dH" % len(ca), *ca))
        self.assertEqual(self.files["data/layouts/Route207/map.bin"], struct.pack("<%dH" % len(cb), *cb))
        for name, h in (("Route206", a), ("Route207", b)):
            self.assertEqual(json.loads(self.files[f"data/maps/{name}/map.json"])["connections"], h["connections"])

    def test_generated_native_fixture_retains_old_cases_and_checks_new_ladder(self):
        raw = self.files["test/averon_oreburgh_candidate.c"].decode()
        old = self.legacy["test/averon_oreburgh_candidate.c"].decode()
        self.assertEqual(raw.count('TEST("'), old.count('TEST("') + 1)
        self.assertIn("EXPECT_EQ(gate->warpCount, 3)", raw)
        self.assertIn("EXPECT_EQ(city->warps[0].warpId, 2)", raw)
        self.assertIn("MAP_OREBURGH_GATE_B1F", raw)
        self.assertIn("EXPECT_EQ(route->count, 2)", raw)
        count = len(json.loads(self.current[m.GROUPS])["gMapGroup_Sinnoh"])
        self.assertIn(f"EXPECT_EQ(MAP_NUM(maps[i]), {count}+i);",
                      self.files["test/averon_eterna_runtime.c"].decode())
        self.assertIn("19+i", (HERE.parent / "eterna-cycle/native-runtime.c").read_text())

    def test_generated_eterna_section_count_matches_the_profile(self):
        raw = self.files["test/averon_eterna_runtime.c"].decode()
        self.assertIn("MAPSEC_COUNT == 227", (HERE.parent / "eterna-cycle/native-runtime.c").read_text())
        if m.production_city(self.current):
            self.assertIn("STATIC_ASSERT(MAPSEC_COUNT == 228, eterna_no_new_origins);", raw)
            self.assertIn("STATIC_ASSERT(MAPSEC_OREBURGH_CITY == 227,", raw)
            self.assertNotIn("MAPSEC_COUNT == 227", raw)
        else:
            self.assertIn("STATIC_ASSERT(MAPSEC_COUNT == 227, eterna_no_new_origins);", raw)
            self.assertNotIn("MAPSEC_OREBURGH_CITY", raw)

    def test_unknown_eterna_section_assert_is_rejected_after_packet_c(self):
        if not m.production_city(self.current):
            self.skipTest("legacy profiles keep the historical count")
        original = Path.read_bytes
        target = HERE.parent / "eterna-cycle/native-runtime.c"
        def read(p):
            raw = original(p)
            return raw.replace(b"MAPSEC_COUNT == 227", b"MAPSEC_COUNT == 226") if p == target else raw
        with mock.patch.object(Path, "read_bytes", read), self.assertRaises(ValueError):
            m.compose(ROOT)

    def test_unknown_eterna_native_fixture_is_rejected(self):
        original = Path.read_bytes
        target = HERE.parent / "eterna-cycle/native-runtime.c"
        def read(p):
            raw = original(p)
            return raw.replace(b"19+i", b"999+i") if p == target else raw
        with mock.patch.object(Path, "read_bytes", read), self.assertRaises(ValueError):
            m.compose(ROOT)

    def reject_change(self, path, transform):
        current = dict(self.current)
        current[path] = transform(current[path])
        adapt = m.rebase_on_production_city if m.production_city(self.current) else m.rebase
        adapt(self.legacy, self.old, dict(self.current))       # the unchanged inputs are accepted
        with self.assertRaises(ValueError):
            adapt(self.legacy, self.old, current)

    def test_production_city_overlay_restores_route207_and_mine_doors_only(self):
        if not m.production_city(self.current):
            self.skipTest("pre-packet-C profile")
        city, prod = (json.loads(x[m.CITY]) for x in (self.files, self.current))
        self.assertEqual(city["warp_events"][:11], prod["warp_events"])
        self.assertEqual([(w["x"], w["y"], w["dest_map"]) for w in city["warp_events"][11:]],
                         [(x, 57, "MAP_OREBURGH_MINE_B1F") for x in (50, 51, 52, 53)])
        self.assertEqual(city["connections"], [{"map": "MAP_ROUTE207", "offset": 35, "direction": "up"}])
        self.assertEqual({k: v for k, v in city.items() if k not in ("warp_events", "connections")},
                         {k: v for k, v in prod.items() if k not in ("warp_events", "connections")})
        words = lambda b: struct.unpack("<%dH" % (len(b) // 2), b)
        changed = [(i % 70, i // 70) for i, (a, b) in enumerate(zip(words(self.current[m.CITY_BLOCKS]),
                                                                      words(self.files[m.CITY_BLOCKS]))) if a != b]
        self.assertEqual(changed, m.MINE_CELLS)
        b1f = json.loads(self.files["data/maps/OreburghMine_B1F/map.json"])["warp_events"]
        self.assertEqual([w["dest_warp_id"] for w in b1f[:2]], ["11", "14"])
        for path in ("data/layouts/OreburghCity/border.bin", "data/maps/OreburghCity/scripts.inc"):
            self.assertNotIn(path, self.files)

    def test_production_city_with_a_connection_is_rejected(self):
        if not m.production_city(self.current):
            self.skipTest("pre-packet-C profile")
        self.reject_change(m.CITY, lambda b: m.encode(dict(json.loads(b), connections=[
            {"map": "MAP_ROUTE207", "offset": 35, "direction": "up"}])))

    def test_unexpected_production_gate_header_is_rejected(self):
        self.reject_change(m.GATE, lambda b: m.encode(dict(json.loads(b), music="MUS_DUMMY")))

    def test_unexpected_gate_block_change_is_rejected(self):
        path = "data/layouts/OreburghGate_1F/map.bin"
        self.reject_change(path, lambda b: b[:2] + bytes([b[2] ^ 1]) + b[3:])

    def test_legacy_slot_renumbering_is_rejected(self):
        def change(b):
            v = json.loads(b)
            v["gMapGroup_Sinnoh"][0] = "NotSandgem"
            return m.encode(v)
        self.reject_change(m.GROUPS, change)

    def test_wrong_registry_count_is_rejected(self):
        self.reject_change(m.REGISTRY, lambda b: b.replace(b"gMapGroup_Sinnoh, ", b"NotSinnoh, ", 1))

    def test_dirty_current_input_is_rejected_without_writes(self):
        original = Path.read_bytes
        target = ROOT / m.ENGINE / m.GATE
        def read(p): return b"tampered" if p == target else original(p)
        with mock.patch.object(Path, "read_bytes", read), self.assertRaises(ValueError):
            m.current_inputs(ROOT)

    def test_unapproved_engine_tree_is_rejected_before_reading_inputs(self):
        with mock.patch.object(m.subprocess, "check_output", return_value=b"wrong-tree\n"), self.assertRaises(ValueError):
            m.current_inputs(ROOT)


if __name__ == "__main__":
    unittest.main()
