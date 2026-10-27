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

    def test_other_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine, receipt = self.fixture(Path(tmp))
            receipt["files"].pop("input0")
            with self.assertRaises(ValueError): m.validate(engine, receipt)


if __name__ == "__main__": unittest.main()
