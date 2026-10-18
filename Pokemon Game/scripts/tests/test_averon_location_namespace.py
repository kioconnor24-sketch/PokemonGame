"""Isolated namespace proposals using real jsonproc templates/runtime C bodies.

Candidate constants are rendered ONLY in TemporaryDirectory. The production
constants template, section JSON, IDs and save format are never changed.
"""
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unittest


ENGINE = Path(__file__).resolve().parents[2] / 'engine'


def c_function(source, signature):
    start = source.index(signature + '\n{')
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


class LocationNamespaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.jsonproc = ENGINE / 'tools/jsonproc/jsonproc'
        if not cls.jsonproc.is_file():
            subprocess.run(['make', '-C', str(cls.jsonproc.parent)], check=True, timeout=120)
        cls.sections = json.loads((ENGINE / 'src/data/region_map/region_map_sections.json').read_text())['map_sections']
        source = (ENGINE / 'src/region_map.c').read_text()
        cls.runtime = '\n'.join(c_function(source, signature) for signature in (
            'bool32 IsRegionMapSectionIdValid(u32 sectionId)',
            'enum Region GetRegionForSectionId(u32 sectionId)'))
        summary = (ENGINE / 'src/pokemon_summary_screen.c').read_text()
        predicate = re.search(r'bool32 knownMetLocation\s*=\s*(.*?);', summary, re.S)[1]
        cls.met_predicate = predicate.replace('sum->metLocation', 'location')
        cls.template = (ENGINE / 'src/data/region_map/region_map_sections.constants.json.txt').read_text()
        cls.entries_template = (ENGINE / 'src/data/region_map/region_map_sections.json.txt').read_text()

    def run_fixture(self, additions=(), *, stable=False, body='', compile_error=None):
        with TemporaryDirectory(prefix='averon-location-namespace-') as temp:
            root = Path(temp)
            sections = deepcopy(self.sections) + list(additions)
            data = {'map_sections': sections}
            constants = self.template
            if stable:
                # EXPERIMENTAL proposal, not a production template/policy.
                # Preserve all old assignments and the old NONE hole, then
                # append test-only values216+ (or sparse/u16 boundary cases).
                for index, entry in enumerate(sections):
                    entry['fixture_value'] = entry.get('fixture_value', index if index < 215 else index + 1)
                data['fixture_count'] = max(e['fixture_value'] for e in sections) + 1
                constants = constants.replace('{{ map_section.id }},',
                    '{{ map_section.id }} = {{ map_section.fixture_value }},')
                constants = constants.replace('MAPSEC_NONE,\n    MAPSEC_COUNT',
                    'MAPSEC_NONE = 215,\n    MAPSEC_COUNT = {{ fixture_count }}')
            for name, text in (('fixture.json', json.dumps(data)), ('constants.txt', constants),
                               ('entries.txt', self.entries_template)):
                (root / name).write_text(text)
            for template, output in (('constants.txt', 'constants.h'), ('entries.txt', 'entries.h')):
                subprocess.run([str(self.jsonproc), str(root / 'fixture.json'), str(root / template), str(root / output)],
                               cwd=root, check=True, capture_output=True, timeout=30)
            (root / 'fixture.c').write_text('''
#include <assert.h>
#include <stdint.h>
#include <string.h>
typedef uint8_t u8;
typedef uint32_t u32;
typedef uint32_t bool32;
#define NULL ((void *)0)
#define ARRAY_COUNT(a) (sizeof(a) / sizeof((a)[0]))
#define COMPOUND_STRING(s) ((const u8 *)(s))
#define _(s) {0} // empty encoded-string literal; host tests do not render font data
struct RegionMapLocation {u8 x, y, width, height; const u8 *name;};
''' + f'#include "{ENGINE / "include/constants/regions.h"}"\n'
                + '#include "constants.h"\n#include "entries.h"\n'
                + '#define LEGACY_LOCATION(symbol, value, name) _Static_assert(symbol == value, "Legacy ID moved");\n'
                + f'#include "{ENGINE / "test/data/averon_legacy_location_ids.inc"}"\n'
                + '#undef LEGACY_LOCATION\n' + self.runtime
                + '\nstatic bool32 KnownMet(u32 location) {return ' + self.met_predicate + ';}\n'
                + '\nint main(void) {\n(void)KnownMet(215);\n' + body + '\nreturn 0;\n}\n')
            result = subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                                     'fixture.c', '-o', 'fixture'], cwd=root, capture_output=True, text=True, timeout=30)
            if compile_error:
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(compile_error, result.stderr)
                return
            self.assertEqual(result.returncode, 0, result.stderr)
            run = subprocess.run([str(root / 'fixture')], cwd=root, capture_output=True, text=True, timeout=30)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_baseline_all_legacy_ids_sentinel_specials_and_regions(self):
        self.run_fixture(body='''
_Static_assert(MAPSEC_NONE == 215, "legacy sentinel moved");
_Static_assert(METLOC_SPECIAL_EGG == 253 && METLOC_IN_GAME_TRADE == 254 && METLOC_FATEFUL_ENCOUNTER == 255, "specials moved");
for (u32 id = 0; id < 256; id++) {
    assert(IsRegionMapSectionIdValid(id) == (id < 215));
    assert(KnownMet(id) == (id < 215));
    assert(GetRegionForSectionId(id) == (id >= KANTO_MAPSEC_START && id < MAPSEC_SPECIAL_AREA ? REGION_KANTO : REGION_HOENN));
}
assert(!IsRegionMapSectionIdValid(UINT32_MAX));
''')

    def test_naive_append_breaks_preserved_none_even_with_all_old_pins_unchanged(self):
        self.run_fixture([{'id': 'MAPSEC_FIXTURE_A', 'name': 'Fixture'}],
            body='_Static_assert(MAPSEC_NONE == 215, "legacy sentinel moved");',
            compile_error='legacy sentinel moved')

    def test_stable_none_candidate_supports_one_named_section_and_explicit_sinnoh(self):
        self.run_fixture([{'id': 'MAPSEC_FIXTURE_A', 'name': 'Fixture', 'region': 'REGION_SINNOH'}],
            stable=True, body='''
assert(MAPSEC_NONE == 215 && MAPSEC_FIXTURE_A == 216);
assert(!IsRegionMapSectionIdValid(215) && !KnownMet(215));
assert(IsRegionMapSectionIdValid(216) && KnownMet(216));
assert(GetRegionForSectionId(216) == REGION_SINNOH);
assert(!strcmp((const char *)gRegionMapEntries[216].name, "Fixture"));
for (u32 id = 0; id < 215; id++)
    assert(GetRegionForSectionId(id) == (id >= KANTO_MAPSEC_START && id < MAPSEC_SPECIAL_AREA ? REGION_KANTO : REGION_HOENN));
''')

    def test_stable_none_candidate_has_exactly_37_spare_named_met_codes(self):
        additions = [{'id': f'MAPSEC_FIXTURE_{i}', 'name': 'Fixture'} for i in range(37)]
        self.run_fixture(additions, stable=True, body='''
assert(MAPSEC_NONE == 215 && MAPSEC_FIXTURE_36 == 252);
for (u32 id = 216; id <= 252; id++) assert(KnownMet(id));
for (u32 id = 253; id <= 255; id++) assert(!KnownMet(id));
''')

    def test_38th_append_collides_with_special_and_fails_candidate_gate(self):
        additions = [{'id': f'MAPSEC_FIXTURE_{i}', 'name': 'Fixture'} for i in range(38)]
        self.run_fixture(additions, stable=True,
            body='_Static_assert(MAPSEC_FIXTURE_37 < METLOC_SPECIAL_EGG, "reserved met collision");',
            compile_error='reserved met collision')

    def test_sparse_slots_do_not_become_names_or_regions(self):
        self.run_fixture([{'id': 'MAPSEC_FIXTURE_A', 'name': 'Fixture',
                           'fixture_value': 252, 'region': 'REGION_SINNOH'}], stable=True, body='''
assert(!IsRegionMapSectionIdValid(216) && !KnownMet(216));
assert(GetRegionForSectionId(216) == REGION_HOENN);
assert(KnownMet(252) && GetRegionForSectionId(252) == REGION_SINNOH);
''')

    def test_none_remains_invalid_even_if_bad_fixture_defines_a_row(self):
        self.run_fixture([{'id': 'MAPSEC_FIXTURE_BAD', 'name': 'Fixture',
                           'fixture_value': 215, 'region': 'REGION_SINNOH'}], stable=True, body='''
assert(!IsRegionMapSectionIdValid(215) && !KnownMet(215));
assert(GetRegionForSectionId(215) == REGION_HOENN);
''')

    def test_region_none_and_invalid_metadata_preserve_legacy_fallback(self):
        for region in ('REGION_NONE', 'REGIONS_COUNT', '255'):
            with self.subTest(region=region):
                self.run_fixture([{'id': 'MAPSEC_FIXTURE_A', 'name': 'Fixture', 'region': region}],
                    stable=True, body='assert(GetRegionForSectionId(216) == REGION_HOENN);')

    def test_typo_in_region_metadata_cannot_compile(self):
        self.run_fixture([{'id': 'MAPSEC_FIXTURE_A', 'name': 'Fixture', 'region': 'REGION_TYPO'}],
            stable=True, compile_error='REGION_TYPO')

    def test_u16_runtime_lookup_works_but_current_saved_width_needs_mapping(self):
        self.run_fixture([{'id': 'MAPSEC_FIXTURE_A', 'name': 'Fixture',
                           'fixture_value': 0x1234, 'region': 'REGION_SINNOH'}], stable=True, body='''
assert(IsRegionMapSectionIdValid(0x1234));
assert(GetRegionForSectionId(0x1234) == REGION_SINNOH);
assert(!KnownMet(0x1234));
// Option-B example only: runtime sections can alias a durable 8-bit name.
const uint16_t runtime_ids[] = {0x1234, 0x1235};
const u8 met_codes[] = {216, 216};
assert(runtime_ids[0] != runtime_ids[1] && met_codes[0] == met_codes[1]);
assert((u8)runtime_ids[0] == 0x34); // direct writes are lossy, not a solution
''')


if __name__ == '__main__':
    unittest.main()
