"""Current W25 DEV scene retains accepted maps, B1F and every old save identity."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
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
        self.assertIn(len(before), (22, 30))
        self.assertEqual(after[:len(before)], before)
        self.assertEqual(len(after), len(before) + 9)
        layouts = json.loads(self.current[m.LAYOUTS])["layouts"]
        self.assertEqual(json.loads(self.files[m.LAYOUTS])["layouts"][:len(layouts)], layouts)

    def test_gate_ladder_and_city_returns_have_separate_reciprocal_indices(self):
        gate = json.loads(self.files[m.GATE])["warp_events"]
        self.assertEqual(gate[:2], json.loads(self.current[m.GATE])["warp_events"])
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
                         [605, 633, 634, 635])

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

    def reject_change(self, path, transform):
        current = dict(self.current)
        current[path] = transform(current[path])
        with self.assertRaises(ValueError):
            m.rebase(self.legacy, self.old, current)

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
