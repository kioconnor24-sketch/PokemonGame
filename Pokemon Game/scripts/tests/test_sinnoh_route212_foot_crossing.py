"""Real thirteen-map world with PR300's rail semantics, no GUI acceptance."""
import importlib.util
import copy
from pathlib import Path
import struct
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


crossing = load('route212_crossing', HERE / 'route212-foot-crossing/prepare_crossing.py')
hotel = load('crossing_existing_hotel_tests', ROOT / 'Pokemon Game/scripts/tests/test_sinnoh_eastern_hotel_link.py')
RAILS = ('MB_BUMPY_SLOPE', 'MB_ISOLATED_VERTICAL_RAIL', 'MB_ISOLATED_HORIZONTAL_RAIL', 'MB_VERTICAL_RAIL', 'MB_HORIZONTAL_RAIL')


class CrossingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        files, receipt = crossing.eastern().assemble(ROOT)
        cls.before, cls.receipt = dict(files), copy.deepcopy(receipt)
        cls.before[crossing.PATH] = (HERE / 'eastern-loop/staged/Route212_South/averon-map.bin').read_bytes()
        cls.receipt.pop('foot_crossing', None)
        cls.receipt['files'][crossing.PATH] = crossing.sha(cls.before[crossing.PATH])
        cls.after, cls.evidence = crossing.compose(cls.before, cls.receipt)

    def world_audit(self, files):
        case = hotel.HotelLinkTest()
        case.files, case.receipt = files, self.receipt
        with case.world() as (world, qa):
            # Exact added predicate from PR300 a0a1bcc2, locally scoped only.
            original = qa.mapdata.MapInfo.walkable
            def on_foot(m, x, y):
                return original(m, x, y) and m.behavior(x, y) not in RAILS
            with mock.patch.object(qa.mapdata.MapInfo, 'walkable', on_foot):
                ids = [h['id'] for h in self.receipt['source_headers'].values()]
                findings, _ = qa.static_audit(world, ids)
                reached = qa.batch_reach(world, ids, 'MAP_ROUTE212_SOUTH', (129, 12))
                return findings, reached

    def test_original_defect_and_fixed_thirteen_map_audit(self):
        findings, before = self.world_audit(self.before)
        self.assertTrue(any('exit-unreachable' in str(f) and 'ROUTE212_SOUTH' in str(f) for f in findings), findings)
        self.assertNotIn(('MAP_ROUTE212_SOUTH', (10, 0)), before)
        findings, after = self.world_audit(self.after)
        self.assertEqual(findings, [])
        self.assertIn(('MAP_ROUTE212_SOUTH', (10, 0)), after)
        self.assertIn(('MAP_ROUTE212_NORTH', (10, 99)), after)
        self.assertEqual({mid for mid, point in after}, {h['id'] for h in self.receipt['source_headers'].values()})

    def test_exact_single_cell_and_all_other_files_preserved(self):
        self.assertEqual(self.before.keys(), self.after.keys())
        self.assertEqual([p for p in self.before if self.before[p] != self.after[p]], [crossing.PATH])
        old = struct.unpack('<4420H', self.before[crossing.PATH])
        new = struct.unpack('<4420H', self.after[crossing.PATH])
        self.assertEqual([i for i, pair in enumerate(zip(old, new)) if pair[0] != pair[1]], [11 * 130 + 38])
        self.assertTrue(all((a & 0xFC00) == (b & 0xFC00) for a, b in zip(old, new)))
        self.assertEqual(new[11 * 130 + 38], 0xF001)
        self.assertNotIn('foot_crossing', self.receipt)

    def test_committed_packet_reproduces_exactly(self):
        folder = HERE / 'route212-foot-crossing'
        import json
        self.assertEqual((folder / 'route212-south-map.bin').read_bytes(), self.after[crossing.PATH])
        self.assertEqual(json.loads((folder / 'receipt.json').read_text()), self.evidence['foot_crossing'])

    def test_changed_bank_semantics_fail_before_mutating_inputs(self):
        original = Path.read_bytes
        for name in ('primary-attributes.bin', 'secondary-attributes.bin'):
            def mutated(path):
                raw = original(path)
                if path.name == name:
                    return bytes(len(raw)) if name.startswith('secondary') else bytes([255]) * len(raw)
                return raw
            with self.subTest(bank=name), mock.patch.object(Path, 'read_bytes', mutated), self.assertRaises(ValueError):
                crossing.compose(self.before, self.receipt)
        self.assertNotIn('foot_crossing', self.receipt)

    def test_wrong_or_already_patched_source_rejected(self):
        raw = self.before[crossing.PATH]
        for value in (raw[:-2], raw + b'00', self.after[crossing.PATH], bytes(len(raw))):
            with self.subTest(length=len(value)), self.assertRaises(ValueError):
                crossing.patch(value)

    def test_closing_only_crossing_reproduces_failure(self):
        files = dict(self.after)
        raw = bytearray(files[crossing.PATH])
        offset = 2 * (11 * 130 + 38)
        struct.pack_into('<H', raw, offset, 0xF401)
        files[crossing.PATH] = bytes(raw)
        findings, reached = self.world_audit(files)
        self.assertTrue(any('exit-unreachable' in str(f) for f in findings))
        self.assertNotIn(('MAP_ROUTE212_SOUTH', (10, 0)), reached)

    def test_existing_hotel_world_audit_remains_clean(self):
        case = hotel.HotelLinkTest('test_actual_world_audit_is_clean_and_pre_cap_frontier_is_exactly_four_cells')
        case.files, case.receipt = self.after, self.receipt
        case.test_actual_world_audit_is_clean_and_pre_cap_frontier_is_exactly_four_cells()


if __name__ == '__main__':
    unittest.main()
