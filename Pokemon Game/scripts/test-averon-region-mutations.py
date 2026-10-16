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

    def test_detects_partial_snapshot_commit_on_read_failure(self):
        self.assert_detected('if (value != 0 && value != 1)\n                return 0;',
                             'if (value != 0 && value != 1) { *badges = snapshot; return 0; }',
                             'test_capture_failure_is_atomic_at_every_read_boundary')

    def test_detects_reading_the_wrong_region_bank(self):
        self.assert_detected('reader(regions[i], number, context)',
                             'reader(AVERON_FIXTURE_AVERON, number, context)',
                             'test_capture_reads_both_banks_once_and_allows_aliasing')

    def test_detects_ignoring_destination_discovery(self):
        self.assert_detected('if (destinationVisited != 1)', 'if (destinationVisited < 0)',
                             'test_fly_destination_policy_truth_table_and_immutable_inputs')

    def test_detects_cross_region_fly_leak(self):
        self.assert_detected('return currentRegion == destinationRegion;', 'return 1;',
                             'test_fly_destination_policy_truth_table_and_immutable_inputs')

    def test_detects_cross_region_healer_leak(self):
        original = 'return AveronRegionFixture_ResolveMap(bindings, bindingCount, mapGroup, mapNum) == region;'
        self.assert_detected(original, original.replace('== region;', '== region || region != AVERON_FIXTURE_UNKNOWN;'),
                             'test_heal_selection_prefers_valid_current_region_then_validates_fallback')

    def test_detects_reversed_healer_candidate_priority(self):
        self.assert_detected('uint32_t candidates[] = {preferredHealId, fallbackHealId};',
                             'uint32_t candidates[] = {fallbackHealId, preferredHealId};',
                             'test_heal_selection_prefers_valid_current_region_then_validates_fallback')

    def test_detects_accepting_non_boolean_positive_healer_reader_result(self):
        self.assert_detected('reader(healId, context, &mapGroup, &mapNum) != 1',
                             'reader(healId, context, &mapGroup, &mapNum) < 1',
                             'test_heal_selection_refuses_invalid_or_unwritten_metadata')

    def test_detects_healer_output_mutation_on_failure(self):
        original = 'if (!reader || !selectedHealId)\n        return 0;'
        self.assert_detected(original, original + '\n    *selectedHealId = 0;',
                             'test_heal_selection_validates_arguments_and_source_region_before_reading')

    def test_detects_retrying_a_failed_healer_identifier(self):
        self.assert_detected('if (i != 0 && candidates[i] == candidates[0])',
                             'if (i > 2 && candidates[i] == candidates[0])',
                             'test_heal_selection_does_not_retry_an_identical_failed_identifier')

    def test_detects_ignoring_map_group(self):
        self.assert_detected('bindings[i].mapGroup != mapGroup || bindings[i].mapNum != mapNum',
                             'bindings[i].mapNum != mapNum',
                             'test_map_lookup_checks_every_group_number_pair')

    def test_detects_first_duplicate_wins(self):
        self.assert_detected('found = (enum AveronFixtureRegion) bindings[i].region;', 'return bindings[i].region;',
                             'test_ambiguous_and_unknown_regions_fail_closed')

    def test_detects_warp_event_count_off_by_one(self):
        self.assert_detected('return (uint32_t)warpId < metadata.warpCount;',
                             'return (uint32_t)warpId <= metadata.warpCount;',
                             'test_warp_indexed_requests_enforce_event_count_and_signed_byte_limit')

    def test_detects_ignoring_warp_coordinate_dimensions(self):
        self.assert_detected('return (uint32_t)x < metadata.width && (uint32_t)y < metadata.height;',
                             'return 1;',
                             'test_warp_coordinate_requests_enforce_dimensions_and_signed_byte_limit')

    def test_detects_accepting_warp_index_signed_byte_overflow(self):
        self.assert_detected('warpId > INT8_MAX', 'warpId > UINT8_MAX',
                             'test_warp_indexed_requests_enforce_event_count_and_signed_byte_limit')

    def test_detects_accepting_map_id_signed_byte_overflow(self):
        self.assert_detected('mapGroup > INT8_MAX || mapNum > INT8_MAX',
                             'mapGroup > UINT8_MAX || mapNum > UINT8_MAX',
                             'test_warp_known_map_ids_must_fit_engine_signed_bytes')

    def test_detects_accepting_warp_coordinate_signed_byte_overflow(self):
        self.assert_detected('x > INT8_MAX || y > INT8_MAX', 'x > UINT8_MAX || y > UINT8_MAX',
                             'test_warp_coordinate_requests_enforce_dimensions_and_signed_byte_limit')

    def test_detects_accepting_non_boolean_positive_warp_reader_result(self):
        self.assert_detected('reader(mapGroup, mapNum, context, &metadata) != 1',
                             'reader(mapGroup, mapNum, context, &metadata) < 1',
                             'test_warp_reader_requires_exact_success_and_preserves_context')


if __name__ == '__main__':
    unittest.main(verbosity=2)
