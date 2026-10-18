"""Map preflight regressions; geometry mutations stay in memory, never in engine."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / 'audit-averon-map-readiness.py'
ENGINE = SCRIPT.parent.parent / 'engine'
SPEC = importlib.util.spec_from_file_location('map_readiness', SCRIPT)
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)
LIMITS = tool.source_limits((ENGINE / 'include/fieldmap.h').read_text(),
                            (ENGINE / 'include/global.fieldmap.h').read_text())


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.layout = {'width': 2, 'height': 1, 'layout_version': 'emerald'}
        self.blocks = struct.pack('<HH', 0x3001, 0x3201)
        self.border = b'\0' * 8
        self.counts = [(512, 512), (512, 512)]

    def errors(self, **changes):
        values = dict(layout=self.layout, blocks=self.blocks, border=self.border,
                      counts=self.counts, limits=LIMITS)
        values.update(changes)
        return tool.layout_errors(**values)

    def test_collision_and_elevation_bits_do_not_change_metatile_index(self):
        self.assertEqual(self.errors(), [])

    def test_short_extra_and_odd_raw_blocks_are_rejected(self):
        for data in (b'\0', b'\0' * 2, b'\0' * 6):
            with self.subTest(size=len(data)):
                self.assertTrue(any('block byte count' in e for e in self.errors(blocks=data)))

    def test_positive_integer_dimensions(self):
        for width in (0, -1, True, 1.5, '2', None):
            with self.subTest(width=width):
                self.assertTrue(self.errors(layout={**self.layout, 'width': width}))

    def test_padded_buffer_boundary(self):
        layout = {'width': 100, 'height': 75}
        self.assertEqual(self.errors(layout=layout, blocks=b'\0' * 15000), [])
        layout['height'] = 76
        self.assertIn('padded layout exceeds MAX_MAP_DATA_SIZE',
                      self.errors(layout=layout, blocks=b'\0' * 15200))

    def test_emerald_border_requires_four_u16_cells(self):
        self.assertTrue(self.errors(border=b'\0' * 6))

    def test_missing_primary_and_secondary_metatiles(self):
        for counts in ([(1, 1), (512, 512)], [(512, 512), (1, 1)]):
            with self.subTest(counts=counts):
                self.assertTrue(any('undefined metatiles' in e for e in self.errors(counts=counts)))
        self.assertTrue(any('border references undefined' in e for e in
                            self.errors(border=struct.pack('<4H', 3, 3, 3, 3), counts=[(2, 2), (512, 512)])))

    def test_mismatched_attribute_count_and_capacity(self):
        self.assertTrue(self.errors(counts=[(512, 511), (512, 512)]))
        self.assertTrue(self.errors(counts=[(513, 513), (512, 512)]))

    def test_frlg_split_and_border_dimensions_are_distinct(self):
        layout = {**self.layout, 'layout_version': 'frlg', 'border_width': 3, 'border_height': 1}
        self.assertEqual(self.errors(layout=layout, border=b'\0' * 6,
                                     blocks=struct.pack('<2H', 639, 640),
                                     counts=[(640, 640), (384, 384)]), [])

    def test_tileset_alias_uses_c_references(self):
        headers = (ENGINE / 'src/data/tilesets/headers.h').read_text()
        metatiles = (ENGINE / 'src/data/tilesets/metatiles.h').read_text()
        paths = tool.tileset_dependencies(headers, metatiles, 'gTileset_Building', False)
        self.assertEqual(paths[0][0], 'data/tilesets/primary/building/metatiles.bin')
        with self.assertRaises(ValueError):
            tool.tileset_dependencies(headers, metatiles, 'gTileset_Building', True)


class SourceBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse an unchanged source snapshot for negative cases; no fixture maps
        # are written, and the real-tree integration test below still uses disk.
        paths = list((ENGINE / 'data/maps').glob('*/map.json'))
        paths += [ENGINE / p for p in ('data/maps/map_groups.json', 'data/layouts/layouts.json',
                                      'include/fieldmap.h', 'include/global.fieldmap.h',
                                      'tools/mapjson/mapjson.cpp', 'map_data_rules.mk', 'Makefile',
                                      'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h')]
        cls.snapshot = {p.relative_to(ENGINE).as_posix(): p.read_bytes() for p in paths}

    def audit_mutated(self, changes, names=('Saltmere',)):
        original = Path.read_bytes

        def read(path):
            relative = path.relative_to(ENGINE.resolve()).as_posix()
            if relative in changes:
                value = changes[relative]
                if value is None:
                    raise FileNotFoundError(relative)
                return value if isinstance(value, bytes) else json.dumps(value).encode()
            return self.snapshot[relative] if relative in self.snapshot else original(path)
        with patch.object(Path, 'read_bytes', read):
            return tool.audit(ENGINE, names)

    def codes(self, result):
        return {e['code'] for e in result['errors']}

    def map_data(self, name='Saltmere'):
        return json.loads((ENGINE / f'data/maps/{name}/map.json').read_text())

    def test_existing_complete_opening_batch_and_deterministic_report(self):
        groups = json.loads((ENGINE / 'data/maps/map_groups.json').read_text())
        names = groups['gMapGroup_AveronOpening']
        first = tool.audit(ENGINE, names)
        self.assertEqual(first['errors'], [])
        self.assertEqual(first['warnings'], [])
        self.assertEqual(len(first['maps']), 16)
        self.assertEqual(first, tool.audit(ENGINE, reversed(names)))
        self.assertIn('tools/mapjson/mapjson.cpp', first['input_sha256'])
        self.assertIn('map_data_rules.mk', first['input_sha256'])

    def test_duplicate_map_constant_is_rejected(self):
        data = self.map_data('CoastalMeadow')
        data['id'] = 'MAP_SALTMERE'
        self.assertIn('map-identity', self.codes(self.audit_mutated({'data/maps/CoastalMeadow/map.json': data})))

    def test_duplicate_layout_id_is_rejected(self):
        layouts = json.loads((ENGINE / 'data/layouts/layouts.json').read_text())
        layouts['layouts'].append(deepcopy(next(l for l in layouts['layouts'] if l['id'] == 'LAYOUT_SALTMERE')))
        self.assertIn('layout-identity', self.codes(self.audit_mutated({'data/layouts/layouts.json': layouts})))

    def test_non_hoenn_map_and_mixed_group_fail(self):
        data = self.map_data()
        data['region'] = 'REGION_SINNOH'
        codes = self.codes(self.audit_mutated({'data/maps/Saltmere/map.json': data}))
        self.assertTrue({'map-excluded', 'mixed-build-group'} <= codes)

    def test_unselected_target_layout_and_border_are_checked(self):
        layouts = json.loads((ENGINE / 'data/layouts/layouts.json').read_text())
        target = self.map_data('SaltmereGreenhouse')['layout']
        next(l for l in layouts['layouts'] if l['id'] == target)['layout_version'] = 'frlg'
        self.assertIn('warp-layout', self.codes(self.audit_mutated({'data/layouts/layouts.json': layouts})))
        path = next(l for l in layouts['layouts'] if l['id'] == target)['border_filepath']
        self.assertIn('warp-layout', self.codes(self.audit_mutated({path: None})))

    def test_missing_asset_and_escaping_source_path_fail(self):
        layouts = json.loads((ENGINE / 'data/layouts/layouts.json').read_text())
        layout = next(l for l in layouts['layouts'] if l['id'] == 'LAYOUT_SALTMERE')
        self.assertIn('asset-dependency', self.codes(self.audit_mutated({layout['blockdata_filepath']: None})))
        layout['blockdata_filepath'] = '../outside.bin'
        self.assertIn('asset-dependency', self.codes(self.audit_mutated({'data/layouts/layouts.json': layouts})))

    def test_invalid_numeric_and_malformed_warp_ids_fail(self):
        for value in (128, '999', '-999', '010', None, True, [], ''):
            data = self.map_data()
            data['warp_events'][0]['dest_warp_id'] = value
            with self.subTest(value=value):
                self.assertIn('warp-index', self.codes(self.audit_mutated({'data/maps/Saltmere/map.json': data})))

    def test_symbolic_target_warp_is_resolved(self):
        source, target = self.map_data(), self.map_data('SaltmereGreenhouse')
        source['warp_events'][0]['dest_warp_id'] = 'WARP_SYNTHETIC_IN_MEMORY'
        target['warp_events'][0]['warp_id'] = 'WARP_SYNTHETIC_IN_MEMORY'
        result = self.audit_mutated({'data/maps/Saltmere/map.json': source,
                                     'data/maps/SaltmereGreenhouse/map.json': target})
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['warnings'], [])

    def test_bad_arrival_and_source_coordinates_fail(self):
        source, target = self.map_data(), self.map_data('SaltmereGreenhouse')
        source['warp_events'][0]['x'] = -1
        target['warp_events'][0]['y'] = 10000
        codes = self.codes(self.audit_mutated({'data/maps/Saltmere/map.json': source,
                                               'data/maps/SaltmereGreenhouse/map.json': target}))
        self.assertTrue({'warp-arrival', 'warp-coordinates'} <= codes)

    def test_generator_filter_drift_fails_closed(self):
        code = (ENGINE / 'tools/mapjson/mapjson.cpp').read_bytes()
        with self.assertRaisesRegex(ValueError, 'inclusion contract'):
            self.audit_mutated({'tools/mapjson/mapjson.cpp': code.replace(b'REGION_HOENN', b'REGION_SINNOH')})

    def test_dynamic_and_shared_events_require_review(self):
        source = self.map_data()
        source['warp_events'][0]['dest_map'] = 'MAP_DYNAMIC'
        result = self.audit_mutated({'data/maps/Saltmere/map.json': source})
        self.assertEqual(result['errors'], [])
        self.assertIn('dynamic-warp', {e['code'] for e in result['warnings']})
        source['shared_events_map'] = 'SaltmereHome'
        source['warp_events'][0]['dest_map'] = 'MAP_MISSING_IGNORED_BY_GENERATOR'
        result = self.audit_mutated({'data/maps/Saltmere/map.json': source})
        self.assertEqual(result['errors'], [])
        self.assertIn('shared-events', {e['code'] for e in result['warnings']})

    def test_invalid_connection_direction_and_offset_fail(self):
        for direction, offset in (('sideways', 0), ('up', None), ('up', True), ('up', 2**31), ('up', '010')):
            source = self.map_data()
            source['connections'][0].update(direction=direction, offset=offset)
            with self.subTest(direction=direction, offset=offset):
                self.assertIn('connection-format', self.codes(self.audit_mutated({'data/maps/Saltmere/map.json': source})))

    def test_empty_region_uses_generator_default(self):
        source = self.map_data()
        source['region'] = ''
        self.assertEqual(self.audit_mutated({'data/maps/Saltmere/map.json': source})['errors'], [])

    def test_invalid_shared_event_reference_fails(self):
        for value in ('', None, [], 'MissingMap'):
            source = self.map_data()
            source['shared_events_map'] = value
            with self.subTest(value=value):
                self.assertIn('shared-events-reference', self.codes(self.audit_mutated({'data/maps/Saltmere/map.json': source})))

    def test_cli_success_and_missing_map_failure(self):
        for name, expected in (('Saltmere', 0), ('MissingMap', 1)):
            result = subprocess.run([sys.executable, str(SCRIPT), '--engine', str(ENGINE), '--map', name],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, expected, result.stderr)
            self.assertIn('SOURCE:', result.stdout)

    def test_cli_cannot_overwrite_engine_source_with_report(self):
        path = ENGINE / 'data/maps/Saltmere/map.json'
        before = path.read_bytes()
        result = subprocess.run([sys.executable, str(SCRIPT), '--engine', str(ENGINE),
                                 '--map', 'Saltmere', '--json', str(path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('outside the read-only engine', result.stderr)
        self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
