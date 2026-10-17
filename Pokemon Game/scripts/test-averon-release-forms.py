"""Source checks for forms the release build leaves out (no compiler needed).

Native tests build with include/config/test.h, which turns every species
and form on. The release build differs only where test.h forces a flag that
species_enabled.h turns off. Those forms exist in native tests but not in the
release ROM, so a reference to them in a data table must sit under the same
#if, or the release ROM would point at an empty species entry. These checks
find the flags, the species they guard, and every table reference to them.
"""
from pathlib import Path
import re
import unittest

ENGINE = Path(__file__).resolve().parents[1] / 'engine'
DATA = ENGINE / 'src' / 'data' / 'pokemon'
TABLES = [DATA / 'form_change_tables.h', DATA / 'form_species_tables.h',
          *sorted((DATA / 'species_info').glob('gen_*_families.h'))]
DEFINE = re.compile(r'^#define (P_\w+)\s+(\S+)', re.M)
SPECIES_ENTRY = re.compile(r'^\s*\[(SPECIES_\w+)\]\s*=')


def read(path):
    return path.read_text(encoding='utf-8')


def release_only_disabled_flags():
    """Flags test.h forces TRUE that species_enabled.h sets to FALSE."""
    test = dict(DEFINE.findall(read(ENGINE / 'include' / 'config' / 'test.h')))
    release = dict(DEFINE.findall(read(ENGINE / 'include' / 'config' / 'species_enabled.h')))
    return sorted(flag for flag, value in test.items()
                  if value == 'TRUE' and release.get(flag) == 'FALSE')


def walk(path):
    """Yield (line number, text, active #if conditions) for each line."""
    stack = []
    for number, line in enumerate(read(path).splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith(('#if', '#ifdef', '#ifndef')):
            stack.append(stripped)
        elif stripped.startswith('#endif'):
            if stack:
                stack.pop()
        elif stripped.startswith(('#else', '#elif')):
            if stack:
                stack[-1] = '!(' + stack[-1] + ')' + stripped
        yield number, line, list(stack)


def guarded_species(flags):
    """Species whose gSpeciesInfo entry is inside an #if on one of the flags."""
    result = {}
    for path in sorted((DATA / 'species_info').glob('gen_*_families.h')):
        for _, line, stack in walk(path):
            match = SPECIES_ENTRY.match(line)
            if not match:
                continue
            for flag in flags:
                if any(flag in condition and not condition.startswith('!(') for condition in stack):
                    result[match.group(1)] = flag
    return result


class AveronReleaseFormTests(unittest.TestCase):
    def test_release_only_flags_are_the_known_gimmick_forms(self):
        self.assertEqual(release_only_disabled_flags(), ['P_PRIMAL_REVERSIONS', 'P_ULTRA_BURST_FORMS'])

    def test_every_table_reference_to_a_release_disabled_form_is_guarded(self):
        species = guarded_species(release_only_disabled_flags())
        self.assertEqual(sorted(species), ['SPECIES_GROUDON_PRIMAL', 'SPECIES_KYOGRE_PRIMAL',
                                           'SPECIES_NECROZMA_ULTRA'])
        unguarded = []
        for path in TABLES:
            for number, line, stack in walk(path):
                for name, flag in species.items():
                    if re.search(r'\b' + name + r'\b', line) and not any(
                            flag in condition and not condition.startswith('!(') for condition in stack):
                        unguarded.append(f'{path.relative_to(ENGINE)}:{number}: {name}')
        self.assertEqual(unguarded, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
