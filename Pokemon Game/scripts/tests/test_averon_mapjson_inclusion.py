"""Exercise the real C++ generator in temporary roots, never production maps.

Run with unittest discovery. AVERON_MAPJSON may select an already built binary
for RED/mutation checks; by default compile the checked-out tool from source.
"""
import json
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest


ENGINE = Path(__file__).resolve().parents[2] / 'engine'


class MapjsonInclusionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('AVERON_MAPJSON'):
            cls.binary = Path(os.environ['AVERON_MAPJSON']).resolve(strict=True)
        else:
            build = TemporaryDirectory(prefix='averon-mapjson-build-')
            cls.addClassCleanup(build.cleanup)
            cls.binary = Path(build.name) / 'mapjson'
            source = ENGINE / 'tools/mapjson'
            subprocess.run([os.environ.get('CXX', 'c++'), '-Wall', '-std=c++17', '-O2',
                            str(source / 'mapjson.cpp'), str(source / 'json11.cpp'),
                            '-o', str(cls.binary)], check=True, timeout=120)

    def setUp(self):
        temp = TemporaryDirectory(prefix='averon-mapjson-fixture-')
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for directory in ('data/maps', 'data/layouts', 'include/constants', 'src/data', 'tools/mapjson'):
            (self.root / directory).mkdir(parents=True)
        self.write('tools/mapjson/required_map_defines.json', {'required_maps': [], 'required_layouts': []})
        self.write('src/data/heal_locations.json', {'heal_locations': []})
        self.map_paths = []

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def map(self, name, **changes):
        data = dict(name=name, id='MAP_' + name.upper(), layout='LAYOUT_FIXTURE',
                    music='MUS_NONE', region_map_section='MAPSEC_NONE',
                    weather='WEATHER_NONE', map_type='MAP_TYPE_TOWN', battle_scene='MAP_BATTLE_SCENE_NORMAL',
                    allow_cycling=True, allow_escaping=False, allow_running=True,
                    show_map_name=True, requires_flash=False)
        data.update(changes)
        relative = f'data/maps/{name}/map.json'
        self.write(relative, data)
        self.map_paths.append(relative)

    def groups(self, version='emerald', **groups):
        self.write('data/maps/map_groups.json', {'group_order': list(groups), **groups})
        return self.run_tool('groups', version, 'data/maps/map_groups.json', *self.map_paths,
                             'data/maps', 'include/constants')

    def run_tool(self, *args, success=True):
        result = subprocess.run([str(self.binary), *args], cwd=self.root, text=True,
                                capture_output=True, timeout=30)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def text(self, relative):
        return (self.root / relative).read_text()

    def pointers(self, label):
        text = self.text('data/maps/groups.inc')
        self.assertIn(label + '::\n', text)
        body = text.split(label + '::\n', 1)[1].split('\n\n', 1)[0]
        return re.findall(r'\.4byte (\w+)', body)

    def assert_includes(self, names):
        for kind in ('headers', 'events', 'connections'):
            actual = re.findall(r'\.include "data/maps/(\w+)/', self.text(f'data/maps/{kind}.inc'))
            self.assertEqual(actual, names, kind)

    def test_emerald_keeps_hoenn_and_missing_null_empty_defaults(self):
        for name, changes in (('Hoenn', {'region': 'REGION_HOENN'}), ('Missing', {}),
                              ('Null', {'region': None}), ('Empty', {'region': ''})):
            self.map(name, **changes)
        self.groups(gHoenn=['Hoenn', 'Missing', 'Null', 'Empty'])
        self.assertEqual(self.pointers('gHoenn'), ['Hoenn', 'Missing', 'Null', 'Empty'])
        self.assert_includes(['Hoenn', 'Missing', 'Null', 'Empty'])

    def test_emerald_explicitly_includes_sinnoh_headers_events_connections(self):
        self.map('Sinnoh', region='REGION_SINNOH')
        self.groups(gSinnoh=['Sinnoh'])
        self.assertEqual(self.pointers('gSinnoh'), ['Sinnoh'])
        self.assert_includes(['Sinnoh'])

    def test_kanto_and_unknown_regions_stay_disabled(self):
        regions = ('REGION_KANTO', 'REGION_JOHTO', 'REGION_sinnoh', 'SINNOH', False, 0)
        for index, region in enumerate(regions):
            self.map(f'Disabled{index}', region=region)
        self.groups(gDisabled=[f'Disabled{i}' for i in range(len(regions))], gEmpty=[])
        self.assertEqual(self.pointers('gMapGroups'), ['NULL', 'NULL'])
        self.assertNotIn('gDisabled::', self.text('data/maps/groups.inc'))
        self.assert_includes([])

    def test_mixed_groups_keep_every_map_index_and_disabled_slot(self):
        for name, region in (('Before', 'REGION_KANTO'), ('A', 'REGION_KANTO'),
                             ('Hoenn', 'REGION_HOENN'), ('B', 'REGION_KANTO'),
                             ('Sinnoh', 'REGION_SINNOH'), ('After', 'REGION_KANTO')):
            self.map(name, region=region)
        self.map('Default')
        groups = dict(gBefore=['Before'], gMixed=['A', 'Hoenn', 'B', 'Sinnoh', 'After'],
                      gEmpty=[], gAfter=['Default'])
        self.groups(**groups)
        self.assertEqual(self.pointers('gMapGroups'), ['NULL', 'gMixed', 'NULL', 'gAfter'])
        self.assertEqual(self.pointers('gMixed'), ['NULL', 'Hoenn', 'NULL', 'Sinnoh', 'NULL'])
        self.assert_includes(['Hoenn', 'Sinnoh', 'Default'])
        constants = self.text('include/constants/map_groups.h')
        for group_index, names in enumerate(groups.values()):
            for index, name in enumerate(names):
                self.assertRegex(constants, rf'MAP_{name.upper()}\s+= \({index} \| \({group_index} << 8\)\)')
        self.assertIn('#define MAP_GROUPS_COUNT 4', constants)
        self.assertEqual(self.text('src/data/map_group_count.h'),
                         'static const u8 MAP_GROUP_COUNT[] = {1, 5, 0, 1, 0};\n')

    def test_firered_still_accepts_only_kanto_and_its_default(self):
        self.map('Hoenn', region='REGION_HOENN')
        self.map('Kanto', region='REGION_KANTO')
        self.map('Sinnoh', region='REGION_SINNOH')
        self.map('Default')
        self.groups('firered', gMixed=['Hoenn', 'Kanto', 'Sinnoh', 'Default'])
        self.assertEqual(self.pointers('gMixed'), ['NULL', 'Kanto', 'NULL', 'Default'])
        self.assert_includes(['Kanto', 'Default'])

    def test_ruby_filter_is_unchanged(self):
        self.map('Hoenn', region='REGION_HOENN')
        self.map('Kanto', region='REGION_KANTO')
        self.map('Sinnoh', region='REGION_SINNOH')
        self.groups('ruby', gAll=['Hoenn', 'Kanto', 'Sinnoh'])
        self.assertEqual(self.pointers('gAll'), ['Hoenn', 'Kanto', 'Sinnoh'])

    def test_missing_group_or_map_json_and_malformed_map_fail(self):
        self.run_tool('groups', 'emerald', 'data/maps/missing.json',
                      'data/maps/missing/map.json', 'data/maps', 'include/constants', success=False)
        self.write('data/maps/map_groups.json', {'group_order': ['gOne'], 'gOne': ['Missing']})
        result = self.run_tool('groups', 'emerald', 'data/maps/map_groups.json',
                               'data/maps/Missing/map.json', 'data/maps', 'include/constants', success=False)
        self.assertIn('Cannot open file', result.stderr)
        (self.root / 'data/maps/Missing').mkdir()
        (self.root / 'data/maps/Missing/map.json').write_text('{broken')
        result = self.run_tool('groups', 'emerald', 'data/maps/map_groups.json',
                               'data/maps/Missing/map.json', 'data/maps', 'include/constants', success=False)
        self.assertIn('Failed to read', result.stderr)

    def test_missing_output_directory_fails_instead_of_claiming_inclusion(self):
        self.map('Sinnoh', region='REGION_SINNOH')
        self.write('data/maps/map_groups.json', {'group_order': ['gOne'], 'gOne': ['Sinnoh']})
        result = self.run_tool('groups', 'emerald', 'data/maps/map_groups.json', *self.map_paths,
                               'missing/output', 'include/constants', success=False)
        self.assertIn('Cannot open file', result.stderr)

    def layout(self, **changes):
        layout = dict(id='LAYOUT_FIXTURE', name='Fixture_Layout', width=1, height=1,
                      primary_tileset='gTileset_General', secondary_tileset='gTileset_Petalburg',
                      border_filepath='data/layouts/fixture/border.bin',
                      blockdata_filepath='data/layouts/fixture/map.bin')
        layout.update(changes)
        return layout

    def test_sinnoh_map_still_requires_unique_layout_and_event_script_linkage(self):
        self.map('Sinnoh', region='REGION_SINNOH')
        self.groups(gSinnoh=['Sinnoh'])
        layouts = {'layouts_table_label': 'gMapLayouts', 'layouts': [self.layout()]}
        self.write('data/layouts/layouts.json', layouts)
        args = ('map', 'emerald', self.map_paths[0], 'data/layouts/layouts.json', 'data/maps/Sinnoh')
        self.run_tool(*args)
        header = self.text('data/maps/Sinnoh/header.inc')
        for symbol in ('Fixture_Layout', 'Sinnoh_MapEvents', 'Sinnoh_MapScripts'):
            self.assertIn('.4byte ' + symbol, header)
        self.assertIn('Sinnoh_MapEvents:', self.text('data/maps/Sinnoh/events.inc'))
        # Map generation references scripts/layouts; groups does not supply them.
        for invalid in ([], [self.layout(), self.layout()]):
            self.write('data/layouts/layouts.json', {**layouts, 'layouts': invalid})
            result = self.run_tool(*args, success=False)
            self.assertIn('Failed to find matching layout', result.stderr)

    def test_emerald_layout_version_filter_and_null_slots_are_unchanged(self):
        layouts = [self.layout(id='LAYOUT_DEFAULT', name='Default_Layout'),
                   self.layout(id='LAYOUT_EMERALD', name='Emerald_Layout', layout_version='emerald'),
                   self.layout(id='LAYOUT_FRLG', name='FRLG_Layout', layout_version='frlg'),
                   self.layout(id='LAYOUT_UNKNOWN', name='Unknown_Layout', layout_version='unknown')]
        border = self.root / layouts[0]['border_filepath']
        border.parent.mkdir(parents=True)
        border.write_bytes(b'\0' * 8)
        (self.root / layouts[0]['blockdata_filepath']).write_bytes(b'\0' * 2)
        self.write('data/layouts/layouts.json', {'layouts_table_label': 'gMapLayouts', 'layouts': layouts})
        self.run_tool('layouts', 'emerald', 'data/layouts/layouts.json', 'data/layouts', 'include/constants')
        pointers = re.findall(r'\.4byte (\w+)', self.text('data/layouts/layouts_table.inc'))
        self.assertEqual(pointers, ['Default_Layout', 'Emerald_Layout', 'NULL', 'NULL'])
        headers = self.text('data/layouts/layouts.inc')
        self.assertIn('Emerald_Layout::', headers)
        self.assertNotIn('FRLG_Layout::', headers)
        self.assertNotIn('Unknown_Layout::', headers)


if __name__ == '__main__':
    unittest.main()
