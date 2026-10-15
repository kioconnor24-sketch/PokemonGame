"""Require regression tests to reject actual badge/map C mutations.

Mutations are compiled only inside disposable host directories, never in the
engine checkout or the active WSL native build. A compiler/setup error does not
count as detection: the selected unittest must execute and report a failure.
"""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RegionMutationTests(unittest.TestCase):
    def assert_detected(self, before, after, test_name):
        with tempfile.TemporaryDirectory(prefix='averon-region-mutation-') as temporary:
            destination = Path(temporary)
            for relative in ('engine/include/averon_region_fixture.h',
                             'engine/src/averon_region_fixture.c',
                             'scripts/test-averon-region-fixture.py'):
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            source = destination / 'engine/src/averon_region_fixture.c'
            text = source.read_text(encoding='utf-8')
            self.assertEqual(text.count(before), 1, 'Mutation target changed; review the test')
            source.write_text(text.replace(before, after), encoding='utf-8')
            result = subprocess.run([sys.executable, str(destination / 'scripts/test-averon-region-fixture.py'),
                                     f'RegionFixtureTests.{test_name}'],
                                    capture_output=True, text=True, timeout=60)
            output = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0, 'Mutated behavior unexpectedly passed')
            self.assertIn('Ran 1 test', output, output)
            self.assertIn('FAILED (failures=1)', output, output)

    def test_detects_coupled_badge_banks(self):
        self.assert_detected('return badges->sinnoh;', 'return badges->averon;',
                             'test_changing_other_region_never_changes_membership')

    def test_detects_off_by_one_badge_numbers(self):
        self.assert_detected('1u << (badgeNumber - 1)', '1u << badgeNumber',
                             'test_every_mask_and_badge_position')

    def test_detects_ignoring_map_group(self):
        self.assert_detected('bindings[i].mapGroup != mapGroup || bindings[i].mapNum != mapNum',
                             'bindings[i].mapNum != mapNum',
                             'test_map_lookup_checks_every_group_number_pair')

    def test_detects_first_duplicate_wins(self):
        self.assert_detected('found = (enum AveronFixtureRegion) bindings[i].region;', 'return bindings[i].region;',
                             'test_ambiguous_and_unknown_regions_fail_closed')


if __name__ == '__main__':
    unittest.main(verbosity=2)
