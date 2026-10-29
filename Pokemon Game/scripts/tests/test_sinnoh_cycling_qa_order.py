"""Directed W25 traversal preserves checks and validates immutable source."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parents[2] / "Averon_Codex_Handoff/design/sinnoh/cycling-road-join"
spec = importlib.util.spec_from_file_location("w25_qa_order", HERE / "run_current_qa.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CyclingQAOrderTest(unittest.TestCase):
    def test_north_ports_are_checked_before_descent_with_no_port_removed(self):
        points = [dict(kind="connection", direction="down", tile=[1, 31]),
                  dict(kind="warp", tile=[3, 4]),
                  dict(kind="connection", direction="up", tile=[13, 0]),
                  dict(kind="connection", direction="up", tile=[21, 0])]
        ordered = m.ordered_points(points)
        self.assertEqual(ordered, [points[2], points[3], points[0], points[1]])
        self.assertEqual(Counter(json.dumps(p, sort_keys=True) for p in ordered),
                         Counter(json.dumps(p, sort_keys=True) for p in points))

    def test_route207_keeps_original_map_checks_and_adds_real_mud_refusal(self):
        runner = m.W25Runner.__new__(m.W25Runner)
        runner.plan = {"MAP_ROUTE207": {"points": [dict(kind="connection", direction="down"),
                                                   dict(kind="connection", direction="up")]}}
        runner.blocked = mock.Mock()
        with mock.patch.object(m.qa.Runner, "run_map") as original:
            runner.run_map("MAP_ROUTE207")
        original.assert_called_once_with("MAP_ROUTE207")
        runner.blocked.assert_called_once_with("MAP_ROUTE207", "18", "16", "up")
        self.assertEqual(runner.plan["MAP_ROUTE207"]["points"][0]["direction"], "up")

    def test_northern_maps_precede_oreburgh_descent(self):
        self.assertLess(m.MAPS.index("MAP_ROUTE206"), m.MAPS.index("MAP_ROUTE207"))
        self.assertLess(m.MAPS.index("MAP_ROUTE207"), m.MAPS.index("MAP_OREBURGH_CITY"))
        self.assertIn("MAP_OREBURGH_GATE_B1F", m.MAPS)
        self.assertIn("MAP_OREBURGH_MINE_B2F", m.MAPS)

    def fixture(self, root):
        engine = root / "engine"
        engine.mkdir()
        (engine / ".map_qa_throwaway").touch()
        files = {}
        for i in range(63):
            name = f"input{i}"
            (engine / name).write_bytes(b"source")
            files[name] = hashlib.sha256(b"source").hexdigest()
        return engine, dict(files=files)

    def test_changed_source_and_missing_marker_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine, receipt = self.fixture(Path(tmp))
            m.validate(engine, receipt)
            (engine / "input0").write_bytes(b"changed")
            with self.assertRaises(ValueError): m.validate(engine, receipt)
            (engine / "input0").write_bytes(b"source")
            (engine / ".map_qa_throwaway").unlink()
            with self.assertRaises(ValueError): m.validate(engine, receipt)

    def test_source_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine, receipt = self.fixture(root)
            outside = root / "outside"
            outside.write_bytes(b"source")
            (engine / "input0").unlink()
            (engine / "input0").symlink_to(outside)
            with self.assertRaises(ValueError): m.validate(engine, receipt)

    def test_unlisted_legacy_registry_symlink_cannot_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine, receipt = self.fixture(root)
            outside = root / "outside-groups.json"
            outside.write_text(json.dumps({"gMapGroup_Sinnoh": ["legacy"] * 31}))
            link = engine / "data/maps/map_groups.json"
            link.parent.mkdir(parents=True)
            link.symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "escapes"):
                m.validate(engine, receipt)

    def test_other_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine, receipt = self.fixture(Path(tmp))
            receipt["files"].pop("input0")
            with self.assertRaises(ValueError): m.validate(engine, receipt)


    def post_c_fixture(self, root):
        engine = root / "engine"
        engine.mkdir()
        (engine / ".map_qa_throwaway").touch()
        contract = json.loads((HERE / "post-c-qa-contract.json").read_text())
        document = json.loads((HERE.parents[4] / "Pokemon Game/engine/data/maps/map_groups.json").read_text())
        document["gMapGroup_Sinnoh"] = contract["production_prefix"] + contract["temporary_suffix"]
        values = dict.fromkeys(contract["payload_paths"], b"source")
        values["data/maps/map_groups.json"] = json.dumps(document).encode()
        values["data/maps/OreburghCity/map.json"] = json.dumps({
            "region_map_section": "MAPSEC_OREBURGH_CITY", "warp_events": [{}] * 15}).encode()
        for path, raw in values.items():
            target = engine / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        return engine, dict(files={p: hashlib.sha256(b).hexdigest() for p, b in values.items()})

    def change_json(self, engine, receipt, path, change):
        target = engine / path
        value = json.loads(target.read_text())
        change(value)
        target.write_text(json.dumps(value))
        receipt["files"][path] = hashlib.sha256(target.read_bytes()).hexdigest()

    def test_post_c_61_file_contract_passes(self):
        with tempfile.TemporaryDirectory() as t:
            engine, receipt = self.post_c_fixture(Path(t))
            m.validate(engine, receipt)

    def test_post_c_moved_duplicate_or_reordered_identity_fails(self):
        def moved(g):
            g[30], g[31] = g[31], g[30]
        def duplicate(g):
            g[31] = "OreburghCity"
        def reordered(g):
            g[41], g[42] = g[42], g[41]
        for change in (moved, duplicate, reordered):
            with self.subTest(change=change.__name__), tempfile.TemporaryDirectory() as t:
                engine, receipt = self.post_c_fixture(Path(t))
                self.change_json(engine, receipt, "data/maps/map_groups.json", lambda x: change(x["gMapGroup_Sinnoh"]))
                with self.assertRaisesRegex(ValueError, "identity contract"):
                    m.validate(engine, receipt)

    def test_other_production_slots_cannot_swap_with_updated_receipt_hash(self):
        with tempfile.TemporaryDirectory() as t:
            engine, receipt = self.post_c_fixture(Path(t))
            def swap(value):
                g = value["gMapGroup_Sinnoh"]
                g[31], g[32] = g[32], g[31]
            self.change_json(engine, receipt, "data/maps/map_groups.json", swap)
            with self.assertRaisesRegex(ValueError, "identity contract"):
                m.validate(engine, receipt)

    def test_unrelated_payload_cannot_replace_expected_path(self):
        with tempfile.TemporaryDirectory() as t:
            engine, receipt = self.post_c_fixture(Path(t))
            original = "data/layouts/Route207/map.bin"
            receipt["files"].pop(original)
            (engine / "unrelated").write_bytes(b"source")
            receipt["files"]["unrelated"] = hashlib.sha256(b"source").hexdigest()
            with self.assertRaisesRegex(ValueError, "path set"):
                m.validate(engine, receipt)

    def test_non_sinnoh_registry_change_is_rejected_by_existing_pin(self):
        with tempfile.TemporaryDirectory() as t:
            engine, receipt = self.post_c_fixture(Path(t))
            def change(value):
                group = next(k for k in value if k.startswith("gMapGroup_") and k != "gMapGroup_Sinnoh" and len(value[k]) > 1)
                value[group][0], value[group][1] = value[group][1], value[group][0]
            self.change_json(engine, receipt, "data/maps/map_groups.json", change)
            with self.assertRaisesRegex(ValueError, "registry pin"):
                m.validate(engine, receipt)

    def test_post_c_cannot_pad_to_legacy_size(self):
        with tempfile.TemporaryDirectory() as t:
            engine, receipt = self.post_c_fixture(Path(t))
            for name in ("extra0", "extra1"):
                (engine / name).write_bytes(b"source")
                receipt["files"][name] = hashlib.sha256(b"source").hexdigest()
            with self.assertRaisesRegex(ValueError, "legacy63"):
                m.validate(engine, receipt)

    def test_legacy_31_and_39_map_profiles_still_pass(self):
        for count in (31, 39):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as t:
                engine, receipt = self.fixture(Path(t))
                receipt["files"].pop("input0")
                name = "data/maps/map_groups.json"
                path = engine / name
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({"gMapGroup_Sinnoh": [f"Legacy{i}" for i in range(count)]}))
                receipt["files"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
                m.validate(engine, receipt)

    def test_post_c_alias_or_lost_production_warp_fails(self):
        for field, value in [("region_map_section", "MAPSEC_ROUTE_201"), ("warp_events", [{}] * 14)]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as t:
                engine, receipt = self.post_c_fixture(Path(t))
                self.change_json(engine, receipt, "data/maps/OreburghCity/map.json", lambda x: x.update({field: value}))
                with self.assertRaisesRegex(ValueError, "identity contract"):
                    m.validate(engine, receipt)

    def test_post_c_cannot_replace_production_scripts_to_fill_receipt(self):
        with tempfile.TemporaryDirectory() as t:
            engine, receipt = self.post_c_fixture(Path(t))
            receipt["files"].pop("data/layouts/Route207/map.bin")
            path = "data/maps/OreburghCity/scripts.inc"
            (engine / path).write_bytes(b"source")
            receipt["files"][path] = hashlib.sha256(b"source").hexdigest()
            with self.assertRaisesRegex(ValueError, "preservation contract"):
                m.validate(engine, receipt)

    def test_actual_pinned_composition_is_accepted(self):
        spec = importlib.util.spec_from_file_location("qa_receipt_composer", HERE / "prepare_current_runtime.py")
        composer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(composer)
        files, receipt = composer.compose(HERE.parents[4])
        with tempfile.TemporaryDirectory() as t:
            engine = Path(t)
            (engine / ".map_qa_throwaway").touch()
            for path, raw in files.items():
                target = engine / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            m.validate(engine, receipt)

if __name__ == "__main__": unittest.main()
