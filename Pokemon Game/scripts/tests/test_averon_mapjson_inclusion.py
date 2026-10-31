"""Exercise the real C++ generator in temporary roots, never production maps.

Run with unittest discovery. AVERON_MAPJSON may select an already built binary
for RED/mutation checks; by default compile the checked-out tool from source.
"""
import json
import os
from pathlib import Path
import re
import shutil
import struct
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

    def test_arm_link_preserves_slots_and_requires_layout_events_and_scripts(self):
        commands = ('arm-none-eabi-as', 'arm-none-eabi-ld', 'arm-none-eabi-objcopy', 'arm-none-eabi-nm')
        preproc = ENGINE / 'tools/preproc/preproc'
        if not all(shutil.which(command) for command in commands) or not preproc.is_file():
            self.skipTest('ARM binutils and built engine preproc required; run after make all')
        for name, region in (('Before', 'REGION_KANTO'), ('Hoenn', 'REGION_HOENN'),
                             ('Middle', 'REGION_KANTO'), ('Sinnoh', 'REGION_SINNOH'),
                             ('After', 'REGION_KANTO')):
            self.map(name, region=region, music=0, region_map_section=0, weather=0, map_type=0, battle_scene=0)
        self.groups(gMixed=['Before', 'Hoenn', 'Middle', 'Sinnoh', 'After'])
        layout = self.layout(layout_version='emerald')
        self.write('data/layouts/layouts.json', {'layouts_table_label': 'gMapLayouts', 'layouts': [layout]})
        border = self.root / layout['border_filepath']
        border.parent.mkdir(parents=True)
        border.write_bytes(b'\0' * 8)
        (self.root / layout['blockdata_filepath']).write_bytes(b'\0' * 2)
        for name in ('Hoenn', 'Sinnoh'):
            self.run_tool('map', 'emerald', f'data/maps/{name}/map.json',
                          'data/layouts/layouts.json', f'data/maps/{name}')
        self.run_tool('layouts', 'emerald', 'data/layouts/layouts.json', 'data/layouts', 'include/constants')
        base = (f'.include "{ENGINE}/asm/macros/map.inc"\n'
                '.equ NULL,0\n.equ TRUE,1\n.equ FALSE,0\n.equ MUS_NONE,0\n.equ LAYOUT_FIXTURE,1\n')
        includes = ('data/layouts/layouts.inc', 'data/layouts/layouts_table.inc', 'data/maps/groups.inc',
                    'data/maps/headers.inc', 'data/maps/events.inc', 'data/maps/connections.inc')
        stubs = '\ngTileset_General: .4byte 0\ngTileset_Petalburg: .4byte 0\nHoenn_MapScripts: .byte 0\n'
        # Structural link fixtures only: these stubs are not playable content.
        for missing, expected in ((None, None), ('scripts', 'Sinnoh_MapScripts'),
                                  ('data/layouts/layouts.inc', 'Fixture_Layout'),
                                  ('data/maps/events.inc', 'Sinnoh_MapEvents')):
            with self.subTest(missing=missing):
                source = base + ''.join(f'.include "{p}"\n' for p in includes if p != missing) + stubs
                if missing != 'scripts':
                    source += 'Sinnoh_MapScripts: .byte 0\n'
                (self.root / 'fixture.s').write_text(source)
                # Use the production preprocessor for :: global labels/includes.
                processed = subprocess.check_output([str(preproc), '-s', 'fixture.s', str(ENGINE / 'charmap.txt')],
                                                    cwd=self.root, timeout=30)
                (self.root / 'fixture.preprocessed.s').write_bytes(processed)
                subprocess.run(['arm-none-eabi-as', '-mcpu=arm7tdmi', '-o', 'fixture.o', 'fixture.preprocessed.s'],
                               cwd=self.root, check=True, capture_output=True, timeout=30)
                link = subprocess.run(['arm-none-eabi-ld', '-Ttext=0x08000000', '-e', 'Sinnoh',
                                       '-o', 'fixture.elf', 'fixture.o'], cwd=self.root,
                                      capture_output=True, text=True, timeout=30)
                if missing:
                    self.assertNotEqual(link.returncode, 0)
                    self.assertIn('undefined reference', link.stderr)
                    self.assertIn(expected, link.stderr)
                    continue
                self.assertEqual(link.returncode, 0, link.stderr)
                listing = subprocess.check_output(['arm-none-eabi-nm', '-n', 'fixture.elf'],
                                                  cwd=self.root, text=True, timeout=30)
                symbols = {fields[2]: int(fields[0], 16) for line in listing.splitlines()
                           if len(fields := line.split()) == 3 and fields[1] not in ('U', 'u')}
                subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', 'fixture.elf', 'fixture.bin'],
                               cwd=self.root, check=True, timeout=30)
                data = (self.root / 'fixture.bin').read_bytes()
                self.assertEqual(struct.unpack_from('<5I', data, symbols['gMixed'] - 0x08000000),
                                 (0, symbols['Hoenn'], 0, symbols['Sinnoh'], 0))
                self.assertEqual(struct.unpack_from('<3I', data, symbols['Sinnoh'] - 0x08000000),
                                 tuple(symbols[s] for s in ('Fixture_Layout', 'Sinnoh_MapEvents', 'Sinnoh_MapScripts')))

    def test_wide_header_generation_matches_actual_arm_c_layout(self):
        commands = ('arm-none-eabi-gcc', 'arm-none-eabi-as', 'arm-none-eabi-ld',
                    'arm-none-eabi-objcopy', 'arm-none-eabi-nm')
        preproc = ENGINE / 'tools/preproc/preproc'
        if not all(shutil.which(command) for command in commands) or not preproc.is_file():
            self.skipTest('ARM compiler/binutils and built preproc required')
        # Use the actual production C definition. Unrelated fieldmap definitions
        # need the whole generated game include tree; this isolated ABI probe does not.
        source = (ENGINE / 'include/global.fieldmap.h').read_text()
        start = source.index('struct MapHeader\n{')
        definition = source[start:source.index('\n};', start) + 3]
        fields = ('regionMapSectionId', 'weather', 'mapType', 'floorNumber', 'nightMusic', 'battleType')
        probe = self.root / 'abi.c'
        probe.write_text('#include <stddef.h>\n#include "gametypes.h"\n' + definition
                         + '\nconst u32 header_abi[] = { sizeof(struct MapHeader), '
                         + ', '.join(f'offsetof(struct MapHeader, {field})' for field in fields)
                         + ' };\n')
        subprocess.run(['arm-none-eabi-gcc', '-mthumb', '-mthumb-interwork', '-O2',
                        '-mabi=apcs-gnu', '-mtune=arm7tdmi', '-march=armv4t', '-std=gnu17',
                        '-I', str(ENGINE / 'include'), '-c', str(probe), '-o', 'abi.o'],
                       cwd=self.root, check=True, capture_output=True, timeout=30)
        subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', '--only-section=.rodata',
                        'abi.o', 'abi.bin'], cwd=self.root, check=True, timeout=30)
        size, *offsets = struct.unpack('<7I', (self.root / 'abi.bin').read_bytes())
        self.assertEqual((size, *offsets), (32, 20, 22, 23, 24, 26, 29))

        # 0x12FD must remain a wide named-location value rather than aliasing
        # the exact egg special 0xFD. Distinct adjacent fields expose misalignment.
        self.map('Wide', region='REGION_SINNOH', music=0x1234, region_map_section=0x12FD,
                 weather=7, map_type=4, floor_number=-2, night_music=0xABCD,
                 battle_scene=6, allow_cycling=True, allow_escaping=False,
                 allow_running=True, show_map_name=True, requires_flash=False)
        self.groups(gWide=['Wide'])
        self.write('data/layouts/layouts.json', {'layouts_table_label': 'gMapLayouts',
                                              'layouts': [self.layout()]})
        self.run_tool('map', 'emerald', self.map_paths[0], 'data/layouts/layouts.json', 'data/maps/Wide')
        fixture = (f'.include "{ENGINE}/asm/macros/map.inc"\n'
                   '.equ NULL,0\n.equ TRUE,1\n.equ FALSE,0\n.equ LAYOUT_FIXTURE,0x2345\n'
                   '.global Wide\n.include "data/maps/Wide/header.inc"\n'
                   '.global WideEnd\nWideEnd:\n'
                   'Fixture_Layout: .4byte 0\nWide_MapEvents: .4byte 0\nWide_MapScripts: .byte 0\n')
        (self.root / 'fixture.s').write_text(fixture)
        processed = subprocess.check_output([str(preproc), '-s', 'fixture.s', str(ENGINE / 'charmap.txt')],
                                            cwd=self.root, timeout=30)
        (self.root / 'fixture.preprocessed.s').write_bytes(processed)
        subprocess.run(['arm-none-eabi-as', '-mcpu=arm7tdmi', '-o', 'fixture.o', 'fixture.preprocessed.s'],
                       cwd=self.root, check=True, capture_output=True, timeout=30)
        subprocess.run(['arm-none-eabi-ld', '-Ttext=0x08000000', '-e', 'Wide', '-o', 'fixture.elf', 'fixture.o'],
                       cwd=self.root, check=True, capture_output=True, timeout=30)
        listing = subprocess.check_output(['arm-none-eabi-nm', '-n', 'fixture.elf'], cwd=self.root, text=True, timeout=30)
        symbols = {fields[2]: int(fields[0], 16) for line in listing.splitlines()
                   if len(fields := line.split()) == 3 and fields[1] not in ('U', 'u')}
        self.assertEqual(symbols['WideEnd'] - symbols['Wide'], size)
        subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', 'fixture.elf', 'fixture.bin'],
                       cwd=self.root, check=True, timeout=30)
        raw = (self.root / 'fixture.bin').read_bytes()[symbols['Wide'] - 0x08000000:][:size]
        self.assertEqual(struct.unpack_from('<HHHBBb', raw, 16), (0x1234, 0x2345, 0x12FD, 7, 4, -2))
        self.assertEqual(struct.unpack_from('<H', raw, offsets[4])[0], 0xABCD)
        self.assertEqual((raw[28], raw[offsets[5]], raw[30:32]), (13, 6, b'\0\0'))

    def test_numeric_sections_cannot_truncate_or_use_exact_met_specials(self):
        self.map('Numeric', region='REGION_SINNOH', region_map_section=256)
        self.groups(gNumeric=['Numeric'])
        self.write('data/layouts/layouts.json', {'layouts_table_label': 'gMapLayouts',
                                              'layouts': [self.layout()]})
        args = ('map', 'emerald', self.map_paths[0], 'data/layouts/layouts.json', 'data/maps/Numeric')
        self.run_tool(*args)
        self.assertIn('.2byte 256', self.text('data/maps/Numeric/header.inc'))
        original = self.text('data/maps/Numeric/header.inc')
        for invalid in (-1, 253, 254, 255, 8192, 65536, 256.5):
            with self.subTest(invalid=invalid):
                header = json.loads(self.text(self.map_paths[0]))
                header['region_map_section'] = invalid
                self.write(self.map_paths[0], header)
                result = self.run_tool(*args, success=False)
                self.assertIn('Invalid map section', result.stderr)
                self.assertEqual(self.text('data/maps/Numeric/header.inc'), original)


if __name__ == '__main__':
    unittest.main()
