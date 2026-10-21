"""Run the production section generator, audits and runtime C on off-tree fixtures."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

ENGINE = Path(__file__).resolve().parents[2] / 'engine'
SOURCE = ENGINE / 'src/data/region_map'
SPEC = importlib.util.spec_from_file_location('namespace_audit', ENGINE.parent / 'scripts/audit-averon-mapsec-namespace.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def c_function(source, signature):
    start = source.index(signature + '\n{')
    opening = source.index('{', start)
    depth, end = 1, opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


class LocationNamespaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jsonproc = ENGINE / 'tools/jsonproc/jsonproc'
        subprocess.run(['make', '-C', str(cls.jsonproc.parent)], check=True, capture_output=True, timeout=120)
        cls.production = json.loads((SOURCE / 'region_map_sections.json').read_text())
        cls.legacy = json.loads((SOURCE / 'region_map_sections.legacy.json').read_text())
        source = (ENGINE / 'src/region_map.c').read_text()
        cls.runtime = '\n'.join(c_function(source, signature) for signature in (
            'bool32 IsRegionMapSectionIdValid(u32 sectionId)',
            'enum Region GetRegionForSectionId(u32 sectionId)'))

    def fixture(self, data=None, *, body='', rejected=False, manifest=True):
        data = deepcopy(self.production if data is None else data)
        with TemporaryDirectory(prefix='averon-section-') as temp:
            root = Path(temp)
            region_dir = root / 'src/data/region_map'
            region_dir.mkdir(parents=True)
            source = region_dir / 'region_map_sections.json'
            source.write_text(json.dumps(data))
            original = source.read_bytes()
            if manifest:
                (region_dir / 'region_map_sections.legacy.json').write_text(json.dumps(self.legacy))
            for template, output in (('region_map_sections.constants.json.txt', 'constants.h'),
                                     ('region_map_sections.json.txt', 'entries.h')):
                target = root / output
                target.write_text('existing-output-canary')
                command = [str(self.jsonproc), str(source), str(SOURCE / template), str(target)]
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                if rejected:
                    self.assertNotEqual(result.returncode, 0, data)
                    self.assertIn('map sections:', result.stderr)
                    self.assertEqual(target.read_text(), 'existing-output-canary')
                    continue
                self.assertEqual(result.returncode, 0, result.stderr)
                content = target.read_bytes()
                subprocess.run(command, capture_output=True, check=True, timeout=30)
                self.assertEqual(target.read_bytes(), content)
            self.assertEqual(source.read_bytes(), original)
            if rejected:
                with self.assertRaises((ValueError, KeyError)):
                    audit.sections(root)
                return
            entries = audit.sections(root)
            values = {e['id']: e['value'] for e in entries}
            self.assertEqual(audit.section_none(root, entries), 215)
            self.assertEqual(values['MAPSEC_COASTAL_BLUFFS'], 214)
            (root / 'fixture.c').write_text('''
#include <assert.h>
#include <stdint.h>
#include <string.h>
typedef uint8_t u8;
typedef uint32_t u32;
typedef uint32_t bool32;
#define ARRAY_COUNT(a) (sizeof(a) / sizeof((a)[0]))
#define COMPOUND_STRING(s) ((const u8 *)(s))
#define _(s) {0}
struct RegionMapLocation {u8 x, y, width, height; const u8 *name;};
''' + f'#include "{ENGINE / "include/constants/regions.h"}"\n'
                + '#include "constants.h"\n#include "entries.h"\n'
                + '#define LEGACY_LOCATION(symbol, value, name) _Static_assert(symbol == value, "legacy ID moved");\n'
                + f'#include "{ENGINE / "test/data/averon_legacy_location_ids.inc"}"\n'
                + '#undef LEGACY_LOCATION\n' + self.runtime
                + '\nint main(void) {\n_Static_assert(MAPSEC_NONE == 215, "sentinel moved");\n'
                + '_Static_assert(METLOC_SPECIAL_EGG == 253 && METLOC_IN_GAME_TRADE == 254 && METLOC_FATEFUL_ENCOUNTER == 255, "specials moved");\n'
                + body + '\nreturn 0;\n}\n')
            result = subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', 'fixture.c', '-o', 'fixture'],
                                    cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            run = subprocess.run([str(root / 'fixture')], capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_production_sinnoh_sections_and_all_legacy_runtime_values(self):
        self.fixture(body='''
assert(MAPSEC_SANDGEM_TOWN == 216 && MAPSEC_ROUTE_201 == 217 && MAPSEC_TWINLEAF_TOWN == 218 && MAPSEC_ROUTE_202 == 219 && MAPSEC_LAKE_VERITY == 220 && MAPSEC_JUBILIFE_CITY == 221 && MAPSEC_ROUTE_203 == 222 && MAPSEC_OREBURGH_GATE == 223 && MAPSEC_COUNT == 224);
assert(!strcmp((const char *)gRegionMapEntries[216].name, "SANDGEM TOWN"));
assert(!strcmp((const char *)gRegionMapEntries[217].name, "ROUTE 201"));
assert(!strcmp((const char *)gRegionMapEntries[218].name, "TWINLEAF TOWN"));
assert(!strcmp((const char *)gRegionMapEntries[219].name, "ROUTE 202"));
assert(!strcmp((const char *)gRegionMapEntries[220].name, "LAKE VERITY"));
assert(!strcmp((const char *)gRegionMapEntries[221].name, "JUBILIFE CITY"));
assert(!strcmp((const char *)gRegionMapEntries[222].name, "ROUTE 203"));
assert(!strcmp((const char *)gRegionMapEntries[223].name, "OREBURGH GATE"));
for (u32 id = 0; id < 256; id++) {
 assert(IsRegionMapSectionIdValid(id) == (id < 215 || id == 216 || id == 217 || id == 218 || id == 219 || id == 220 || id == 221 || id == 222 || id == 223));
 assert(GetRegionForSectionId(id) == (id == 216 || id == 217 || id == 218 || id == 219 || id == 220 || id == 221 || id == 222 || id == 223 ? REGION_SINNOH : id >= KANTO_MAPSEC_START && id < MAPSEC_SPECIAL_AREA ? REGION_KANTO : REGION_HOENN));
}
assert(!IsRegionMapSectionIdValid(UINT32_MAX));
''')

    def test_legacy_only_generation_preserves_the_empty_sentinel(self):
        data = deepcopy(self.production); data['map_sections'] = data['map_sections'][:215]
        self.fixture(data, body='assert(MAPSEC_COUNT == 216 && !IsRegionMapSectionIdValid(215));')

    def test_next_explicit_allocation_works_without_generated_file_edits(self):
        data = deepcopy(self.production)
        data['map_sections'].append(dict(id='MAPSEC_FIXTURE', name='Fixture', value=224, region='REGION_SINNOH'))
        self.fixture(data, body='assert(MAPSEC_FIXTURE == 224 && GetRegionForSectionId(224) == REGION_SINNOH && !IsRegionMapSectionIdValid(215));')

    def test_37th_code_works_and_38th_is_rejected(self):
        data = deepcopy(self.production)
        for value in range(224, 253):
            data['map_sections'].append(dict(id=f'MAPSEC_FIXTURE_{value}', name='Fixture', value=value, region='REGION_SINNOH'))
        self.fixture(data, body='assert(MAPSEC_COUNT == 253 && MAPSEC_FIXTURE_252 == 252); assert(!IsRegionMapSectionIdValid(253));')
        data['map_sections'].append(dict(id='MAPSEC_BAD', name='Bad', value=253, region='REGION_SINNOH'))
        self.fixture(data, rejected=True)

    def test_legacy_ids_names_regions_and_order_cannot_be_changed(self):
        for key, value in [('id', 'MAPSEC_CHANGED'), ('name', 'CHANGED'), ('value', 1), ('region', 'REGION_SINNOH')]:
            data = deepcopy(self.production); data['map_sections'][0][key] = value
            with self.subTest(key=key): self.fixture(data, rejected=True)
        data = deepcopy(self.production)
        data['map_sections'][0], data['map_sections'][1] = data['map_sections'][1], data['map_sections'][0]
        self.fixture(data, rejected=True)

    def test_duplicate_identifiers_and_reserved_symbols_are_rejected(self):
        for ident in ('MAPSEC_SALTMERE', 'MAPSEC_NONE', 'MAPSEC_COUNT', 'MAPSEC_BAD; INJECT'):
            data = deepcopy(self.production); data['map_sections'][-1]['id'] = ident
            with self.subTest(ident=ident): self.fixture(data, rejected=True)

    def test_invalid_duplicate_sparse_special_and_wide_values_are_rejected(self):
        # The last production entry is Oreburgh Gate (223): its value can't be moved, duplicated or widened.
        for value in (None, True, '223', 223.0, -1, 0, 214, 215, 222, 224, 252, 253, 255, 0x1234):
            data = deepcopy(self.production); data['map_sections'][-1]['value'] = value
            with self.subTest(value=value): self.fixture(data, rejected=True)

    def test_new_sections_require_explicit_value_name_and_region(self):
        for key in ('value', 'name', 'region'):
            data = deepcopy(self.production); del data['map_sections'][-1][key]
            with self.subTest(key=key): self.fixture(data, rejected=True)

    def test_region_tags_are_declared_engine_enums(self):
        for region in (None, False, 4, '4', 'REGIONS_COUNT', 'REGION_TYPO', 'REGION_NONE'):
            data = deepcopy(self.production); data['map_sections'][-1]['region'] = region
            with self.subTest(region=region): self.fixture(data, rejected=True)

    def test_missing_manifest_fails_before_replacing_generated_outputs(self):
        self.fixture(rejected=True, manifest=False)

    def test_frozen_manifest_matches_every_legacy_source_entry(self):
        self.assertEqual(len(self.legacy), 215)
        for index, old in enumerate(self.legacy):
            entry = self.production['map_sections'][index]
            self.assertEqual(old, dict(id=entry['id'], name=entry.get('name'), value=index))

    def test_real_assembly_enum_preprocessor_accepts_generated_values(self):
        preproc = ENGINE / 'tools/preproc/preproc'
        subprocess.run(['make', '-C', str(preproc.parent)], capture_output=True, check=True, timeout=120)
        with TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run([str(self.jsonproc), str(SOURCE/'region_map_sections.json'),
                str(SOURCE/'region_map_sections.constants.json.txt'), str(root/'constants.h')], check=True, timeout=30)
            fixture = root/'fixture.s'
            fixture.write_text('#include "constants.h"\n.section .rodata\n.byte MAPSEC_SANDGEM_TOWN, MAPSEC_NONE, METLOC_SPECIAL_EGG, METLOC_FATEFUL_ENCOUNTER\n')
            text = subprocess.run(['cc', '-E', '-x', 'assembler-with-cpp', str(fixture)],
                check=True, capture_output=True, timeout=30).stdout
            translated = subprocess.run([str(preproc), '-ie', str(fixture), str(ENGINE/'charmap.txt')],
                input=text, capture_output=True, timeout=30)
            self.assertEqual(translated.returncode, 0, translated.stderr)
            subprocess.run(['cc', '-c', '-x', 'assembler', '-o', str(root/'out.o'), '-'],
                input=translated.stdout, capture_output=True, check=True, timeout=30)
            # Real native build caught this: C alone accepts the missing comma.
            h = root/'constants.h'
            self.assertIn('MAPSEC_COUNT = 224,', h.read_text())  # the mutation below must really apply
            h.write_text(h.read_text().replace('MAPSEC_COUNT = 224,', 'MAPSEC_COUNT = 224'))
            text = subprocess.run(['cc', '-E', '-x', 'assembler-with-cpp', str(fixture)],
                check=True, capture_output=True, timeout=30).stdout
            bad = subprocess.run([str(preproc), '-ie', str(fixture), str(ENGINE/'charmap.txt')],
                input=text, capture_output=True, timeout=30)
            self.assertNotEqual(bad.returncode, 0)

    def test_unrelated_jsonproc_templates_keep_working(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'in.json').write_text('{"hello": "world"}')
            (root / 'in.txt').write_text('{{ hello }}')
            subprocess.run([str(self.jsonproc), str(root/'in.json'), str(root/'in.txt'), str(root/'out.txt')], check=True, timeout=30)
            self.assertEqual((root/'out.txt').read_text(), 'world')


if __name__ == '__main__':
    unittest.main()
