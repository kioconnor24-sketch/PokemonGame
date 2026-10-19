"""Map preflight regressions; geometry mutations stay in memory, never in engine."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
import zlib
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


class VisualContainerTests(unittest.TestCase):
    @staticmethod
    def png(width=8, height=8, depth=4, color=3):
        def chunk(kind, data):
            return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data) & 0xffffffff)
        return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, depth, color, 0, 0, 0))
                + chunk(b'PLTE', b'\0\0\0'*16)
                + chunk(b'IDAT', zlib.compress(b'\0'*(((width*depth+7)//8+1)*height))) + chunk(b'IEND', b''))

    def test_tile_footprint_and_crc(self):
        self.assertEqual(tool.png_geometry(self.png(16, 8))['raw_tiles'], 2)
        bad = bytearray(self.png());bad[-1] ^= 1
        for data in (bytes(bad), self.png()[:-2], self.png()+b'extra', self.png(9, 8), self.png(0, 8)):
            with self.subTest(data=data[:20]):
                with self.assertRaises(ValueError): tool.png_geometry(data)

    def test_illegal_png_header_is_rejected(self):
        for data in (self.png(depth=3), self.png(color=9)):
            with self.assertRaises(ValueError): tool.png_geometry(data)

    def test_palette_color_count_and_components(self):
        good = b'JASC-PAL\n0100\n16\n' + b'0 0 0\n'*16
        tool.palette_errors(good)
        for bad in (good[:-6], good.replace(b'0 0 0', b'256 0 0', 1), good.replace(b'16', b'17', 1), b'bad'):
            with self.assertRaises(ValueError): tool.palette_errors(bad)


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

    def audit_mutated(self, changes, names=('Saltmere',), **options):
        original = Path.read_bytes

        def read(path):
            if not path.is_relative_to(ENGINE.resolve()):
                return original(path)
            relative = path.relative_to(ENGINE.resolve()).as_posix()
            if relative in changes:
                value = changes[relative]
                if value is None:
                    raise FileNotFoundError(relative)
                return value if isinstance(value, bytes) else json.dumps(value).encode()
            return self.snapshot[relative] if relative in self.snapshot else original(path)
        with patch.object(Path, 'read_bytes', read):
            return tool.audit(ENGINE, names, **options)

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

    def test_missing_invalid_and_reserved_map_constants_fail(self):
        for ident in (None, '', True, 'MAP_DYNAMIC', 'MAP_NONE', 'MAP_bad-name'):
            source = self.map_data()
            source['id'] = ident
            with self.subTest(ident=ident):
                self.assertIn('map-identity', self.codes(self.audit_mutated({'data/maps/Saltmere/map.json': source})))

    def test_duplicate_layout_id_is_rejected(self):
        layouts = json.loads((ENGINE / 'data/layouts/layouts.json').read_text())
        layouts['layouts'].append(deepcopy(next(l for l in layouts['layouts'] if l['id'] == 'LAYOUT_SALTMERE')))
        self.assertIn('layout-identity', self.codes(self.audit_mutated({'data/layouts/layouts.json': layouts})))

    def test_sinnoh_map_in_mixed_hoenn_group_is_header_eligible(self):
        data = self.map_data()
        data['region'] = 'REGION_SINNOH'
        data['region_map_section'] = 'MAPSEC_SANDGEM_TOWN'
        result = self.audit_mutated({'data/maps/Saltmere/map.json': data})
        self.assertEqual(result['errors'], [])
        self.assertTrue(result['maps'][0]['header_eligible'])

    def test_sinnoh_header_rejects_legacy_region_section_fallback(self):
        for section in ('MAPSEC_SALTMERE', 'MAPSEC_PALLET_TOWN', 'MAPSEC_DYNAMIC'):
            source = self.map_data()
            source.update(region='REGION_SINNOH', region_map_section=section)
            with self.subTest(section=section):
                result = self.audit_mutated({'data/maps/Saltmere/map.json': source})
                self.assertIn('section-region-mismatch', self.codes(result))

    def test_unnamed_sinnoh_section_fails_but_legacy_none_still_requires_review(self):
        for region in ('REGION_HOENN', 'REGION_SINNOH'):
            source = self.map_data()
            source.update(region=region, region_map_section='MAPSEC_NONE')
            with self.subTest(region=region):
                result = self.audit_mutated({'data/maps/Saltmere/map.json': source})
                self.assertEqual('section-none' in self.codes(result), region == 'REGION_SINNOH')
                self.assertEqual('section-none' in {e['code'] for e in result['warnings']}, region == 'REGION_HOENN')

    def test_two_physical_maps_can_share_one_approved_sinnoh_parent_origin(self):
        # Existing documents changed only in memory: this does not place either
        # real Averon map in Sinnoh or approve any new geography/section alias.
        changes = {}
        for name in ('Saltmere', 'SaltmereGreenhouse'):
            source = self.map_data(name)
            source.update(region='REGION_SINNOH', region_map_section='MAPSEC_SANDGEM_TOWN')
            changes[f'data/maps/{name}/map.json'] = source
        result = self.audit_mutated(changes, names=('Saltmere', 'SaltmereGreenhouse'))
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['warnings'], [])
        self.assertEqual(len({row['id'] for row in result['maps']}), 2)
        self.assertEqual({row['section_value'] for row in result['maps']}, {216})
        self.assertEqual({row['section_engine_region'] for row in result['maps']}, {'REGION_SINNOH'})

    def test_kanto_and_unknown_regions_are_excluded_in_mixed_groups(self):
        for region in ('REGION_KANTO', 'REGION_JOHTO', 'REGION_sinnoh', False, 0, [], {}):
            data = self.map_data()
            data['region'] = region
            with self.subTest(region=region):
                result = self.audit_mutated({'data/maps/Saltmere/map.json': data})
                self.assertIn('map-excluded', self.codes(result))
                self.assertFalse(result['maps'][0]['header_eligible'])

    def test_mixed_disabled_slot_does_not_invalidate_enabled_map(self):
        data = self.map_data('Alderfield')
        data['region'] = 'REGION_KANTO'
        result = self.audit_mutated({'data/maps/Alderfield/map.json': data})
        self.assertEqual(result['errors'], [])

    def test_sinnoh_still_requires_emerald_layout(self):
        data = self.map_data()
        data['region'] = 'REGION_SINNOH'
        layouts = json.loads((ENGINE / 'data/layouts/layouts.json').read_text())
        next(l for l in layouts['layouts'] if l['id'] == data['layout'])['layout_version'] = 'frlg'
        result = self.audit_mutated({'data/maps/Saltmere/map.json': data, 'data/layouts/layouts.json': layouts})
        self.assertIn('layout-excluded', self.codes(result))

    def test_excluded_warp_and_connection_targets_remain_invalid(self):
        for target, code in (('SaltmereGreenhouse', 'warp-excluded'), ('CoastalMeadow', 'connection-target')):
            data = self.map_data(target)
            data['region'] = 'REGION_KANTO'
            with self.subTest(target=target):
                result = self.audit_mutated({f'data/maps/{target}/map.json': data})
                self.assertIn(code, self.codes(result))

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
        for before, after in ((b'REGION_HOENN', b'REGION_KANTO'),
                              (b'&& region != "REGION_SINNOH"', b''),
                              (b'&& region != "REGION_SINNOH"', b'&& region != "REGION_KANTO"'),
                              (b'version == "emerald" && region', b'false && version == "emerald" && region'),
                              (b'valid_maps.push_back("NULL");', b''),
                              (b'if (has_valid_map)', b'if (valid_maps.size() > 0)')):
            with self.subTest(mutation=(before, after)):
                self.assertIn(before, code)
                with self.assertRaisesRegex(ValueError, 'inclusion contract'):
                    self.audit_mutated({'tools/mapjson/mapjson.cpp': code.replace(before, after)})

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

    def test_missing_and_invalid_visual_dependencies(self):
        png = 'data/tilesets/primary/general/tiles.png'
        pal = 'data/tilesets/primary/general/palettes/00.pal'
        for changes in ({png: None}, {png: b'not PNG'}, {pal: None}, {pal: b'JASC-PAL\n0100\n15\n'}):
            with self.subTest(changes=list(changes)):
                self.assertIn('asset-dependency', self.codes(self.audit_mutated(changes)))

    def test_visual_sources_are_recorded_using_actual_symbols(self):
        row = tool.audit(ENGINE, ['Saltmere'])
        self.assertEqual(row['errors'], [])
        self.assertTrue(any(d['kind'] == 'tiles_png' for d in row['geometry_dependencies']))
        self.assertTrue(any(d['kind'] == 'palette' for d in row['geometry_dependencies']))
        pins = json.loads((SCRIPT.parent / 'averon-mapsec-pins.json').read_text())['pins']
        self.assertEqual(row['namespace_contract']['saved_pins_checked'], len(pins))

    def test_connection_nonoverlap_and_wrong_inverse_offset(self):
        source = self.map_data()
        source['connections'][0]['offset'] = 10000
        codes = self.codes(self.audit_mutated({'data/maps/Saltmere/map.json': source}))
        self.assertTrue({'connection-overlap', 'connection-offset-return'} <= codes)

    def test_intentional_one_way_connection_requires_review(self):
        target = self.map_data('CoastalMeadow')
        target['connections'] = []
        result = self.audit_mutated({'data/maps/CoastalMeadow/map.json': target})
        self.assertEqual(result['errors'], [])
        self.assertIn('connection-return', {e['code'] for e in result['warnings']})

    def test_strict_seams_reject_missing_return_in_an_unselected_target(self):
        target = self.map_data('CoastalMeadow')
        target['connections'] = []
        changes = {'data/maps/CoastalMeadow/map.json': target}
        default = self.audit_mutated(changes)
        strict = self.audit_mutated(changes, strict_connections=True)
        self.assertEqual(default['errors'], [])
        self.assertIn('connection-return', self.codes(strict))
        self.assertNotIn('connection-return', {e['code'] for e in strict['warnings']})

    def test_strict_seams_reject_ambiguous_reciprocal_edges(self):
        target = self.map_data('CoastalMeadow')
        back = next(c for c in target['connections'] if c['map'] == 'MAP_SALTMERE')
        target['connections'].append(deepcopy(back))
        changes = {'data/maps/CoastalMeadow/map.json': target}
        self.assertEqual(self.audit_mutated(changes)['errors'], [])
        self.assertIn('connection-return-ambiguous',
                      self.codes(self.audit_mutated(changes, strict_connections=True)))

    def test_strict_seams_do_not_accept_one_good_offset_beside_a_wrong_return(self):
        target = self.map_data('CoastalMeadow')
        back = deepcopy(next(c for c in target['connections'] if c['map'] == 'MAP_SALTMERE'))
        back['offset'] = int(back['offset']) + 1
        target['connections'].append(back)
        result = self.audit_mutated({'data/maps/CoastalMeadow/map.json': target}, strict_connections=True)
        self.assertIn('connection-return-ambiguous', self.codes(result))

    def test_strict_seams_keep_wrong_inverse_offset_and_nonoverlap_errors(self):
        source = self.map_data()
        source['connections'][0]['offset'] = 10000
        result = self.audit_mutated({'data/maps/Saltmere/map.json': source}, strict_connections=True)
        self.assertTrue({'connection-overlap', 'connection-offset-return'} <= self.codes(result))

    def test_integrated_sinnoh_and_averon_strict_seams_pass_without_new_ids(self):
        registry = json.loads((ENGINE / 'data/maps/map_groups.json').read_text())
        for group in ('gMapGroup_AveronOpening', 'gMapGroup_Sinnoh'):
            names = registry[group]
            with self.subTest(group=group):
                result = tool.audit(ENGINE, names, strict_connections=True)
                self.assertEqual(result['errors'], [])
                self.assertEqual(result['warnings'], [])
                self.assertEqual(len(result['maps']), len(names))
                self.assertEqual(result['connection_policy'], 'strict reciprocal cardinal seams')

    def test_strict_cli_forwards_policy_and_exits_nonzero_on_a_broken_seam(self):
        broken = dict(errors=[dict(code='connection-return', map='Saltmere', detail='fixture')],
                      warnings=[], maps=[{}], geometry_dependencies=[])
        with patch.object(sys, 'argv', [str(SCRIPT), '--engine', str(ENGINE), '--map', 'Saltmere',
                                       '--strict-connections']), patch.object(tool, 'audit', return_value=broken) as run:
            with self.assertRaises(SystemExit) as result:
                tool.main()
            self.assertEqual(result.exception.code, 1)
            run.assert_called_once_with(ENGINE, ['Saltmere'], strict_connections=True)

    def test_section_reference_and_reused_saved_pin_checks(self):
        source = self.map_data()
        source['region_map_section'] = 'MAPSEC_UNDEFINED_IN_MEMORY'
        self.assertIn('section-reference', self.codes(self.audit_mutated({'data/maps/Saltmere/map.json': source})))
        sections = json.loads((ENGINE / 'src/data/region_map/region_map_sections.json').read_text())
        entries = sections['map_sections']
        entries[-1], entries[-2] = entries[-2], entries[-1]
        with self.assertRaisesRegex(ValueError, 'legacy|moved value'):
            self.audit_mutated({'src/data/region_map/region_map_sections.json': sections})

    def test_section_namespace_mismatch_is_explicit(self):
        source = self.map_data()
        source['region'] = 'REGION_SINNOH'
        result = self.audit_mutated({'data/maps/Saltmere/map.json': source})
        self.assertIn('section-region-mismatch', self.codes(result))
        self.assertNotIn('section-region-mismatch', {e['code'] for e in result['warnings']})
        self.assertEqual(result['maps'][0]['section_engine_region'], 'REGION_HOENN')

    def test_explicit_section_region_is_used_without_allocating_ids(self):
        source = self.map_data()
        source['region'] = 'REGION_SINNOH'
        source['region_map_section'] = 'MAPSEC_SANDGEM_TOWN'
        result = self.audit_mutated({'data/maps/Saltmere/map.json': source})
        self.assertEqual(result['maps'][0]['section_value'], 216)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['maps'][0]['section_engine_region'], 'REGION_SINNOH')
        self.assertNotIn('section-region-mismatch', {e['code'] for e in result['warnings']})

    def test_invalid_return_warp_cannot_hide_behind_valid_arrival(self):
        target = self.map_data('SaltmereGreenhouse')
        target['warp_events'][0]['dest_warp_id'] = '999'
        self.assertIn('warp-return-index', self.codes(self.audit_mutated({'data/maps/SaltmereGreenhouse/map.json': target})))

    def test_selected_group_capacity_is_checked(self):
        groups = json.loads((ENGINE / 'data/maps/map_groups.json').read_text())
        groups['gMapGroup_AveronOpening'] += ['CoastalMeadow'] * 128
        self.assertIn('map-capacity', self.codes(self.audit_mutated({'data/maps/map_groups.json': groups})))

    def test_unsupported_event_containers_report_errors(self):
        for key, value, expected in (('warp_events', 'bad', 'warp-format'),
                                     ('warp_events', {}, 'warp-format'),
                                     ('warp_events', '', 'warp-format'),
                                     ('warp_events', [None], 'warp-format'),
                                     ('connections', 'bad', 'connection-format'),
                                     ('connections', {}, 'connection-format'),
                                     ('connections', [None], 'connection-format')):
            source = self.map_data()
            source[key] = value
            with self.subTest(key=key, value=value):
                self.assertIn(expected, self.codes(self.audit_mutated({'data/maps/Saltmere/map.json': source})))

    def test_dynamic_return_warp_is_not_silently_certified(self):
        target = self.map_data('SaltmereGreenhouse')
        target['warp_events'][0]['dest_warp_id'] = '-1'
        result = self.audit_mutated({'data/maps/SaltmereGreenhouse/map.json': target})
        self.assertIn('dynamic-return-warp', {w['code'] for w in result['warnings']})

    def test_map_dynamic_slot_is_reserved_even_within_signed_bounds(self):
        groups = json.loads((ENGINE / 'data/maps/map_groups.json').read_text())
        for i in range(128-len(groups['group_order'])):
            key = f'gMapGroup_InMemory{i}'
            groups['group_order'].append(key);groups[key] = []
        last = groups['group_order'][-1]
        groups[last] = ['CoastalMeadow']*127 + ['Saltmere']
        self.assertIn('reserved-map-id', self.codes(self.audit_mutated({'data/maps/map_groups.json': groups})))

    def test_cli_success_and_missing_map_failure(self):
        for name, expected in (('Saltmere', 0), ('MissingMap', 1)):
            result = subprocess.run([sys.executable, str(SCRIPT), '--engine', str(ENGINE), '--map', name],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, expected, result.stderr)
            self.assertIn('SOURCE:', result.stdout)

    def test_cli_registered_group_and_map_selectors_are_deduplicated(self):
        result = subprocess.run([sys.executable, str(SCRIPT), '--engine', str(ENGINE),
                                 '--group', 'gMapGroup_AveronOpening', '--map', 'Saltmere'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('SOURCE: 16 maps;', result.stdout)

    def test_cli_missing_group_and_empty_selection_fail_cleanly(self):
        for options in ([], ['--group', 'MissingGroup']):
            result = subprocess.run([sys.executable, str(SCRIPT), '--engine', str(ENGINE), *options], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Preflight input error', result.stderr)
            self.assertNotIn('Traceback', result.stderr)

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
