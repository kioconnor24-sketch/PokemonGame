"""Fixtures for check-averon-native-baseline.py (no compiler needed)."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).with_name('check-averon-native-baseline.py')
spec = importlib.util.spec_from_file_location('averon_native_baseline', SCRIPT)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

RED, GREEN, RESET = '\x1b[31m', '\x1b[32m', '\x1b[0m'
BASELINE = '''# comment
FAIL | gimmick-disabled | Tera thing
INVALID | gimmick-disabled | Z-Move thing
FAIL x2 | gimmick-disabled | Shared name
'''
SHARED = (('Shared name', 'FAIL'), ('Shared name 2/3', 'FAIL'))


def log(*results, finished=True, total=None):
    lines = [f'[{i:02}] {name}: {(RED if status != "PASS" else GREEN)}{status}{RESET}'
             for i, (name, status) in enumerate(results)]
    summary = f'- Tests \x1b[34mTOTAL\x1b[0m:           {len(results) if total is None else total}\n'
    return '\n'.join(lines) + '\n' + (summary if finished else '')


class NativeBaselineTests(unittest.TestCase):
    def test_matching_run_has_no_problems(self):
        text = log(('Tera thing 1/2', 'FAIL'), ('Tera thing 2/2', 'PASS'),
                   ('Z-Move thing (1/?)', 'INVALID'), ('Ordinary test', 'PASS'), *SHARED)
        self.assertEqual(check.compare(text, BASELINE), [])

    def test_new_failure_is_reported(self):
        text = log(('Tera thing', 'FAIL'), ('Z-Move thing', 'INVALID'),
                   ('Ordinary test 1/9 (2/2)', 'FAIL'), ('Crashy', 'CRASH'), *SHARED)
        self.assertEqual(check.compare(text, BASELINE),
                         ['NEW CRASH: Crashy', 'NEW FAIL: Ordinary test'])

    def test_baseline_test_that_now_passes_is_reported(self):
        text = log(('Tera thing', 'PASS'), ('Z-Move thing', 'INVALID'), *SHARED)
        self.assertEqual(check.compare(text, BASELINE),
                         ['NOW PASSES (remove from baseline, was gimmick-disabled): Tera thing'])

    def test_missing_baseline_test_is_reported_unless_partial(self):
        text = log(('Tera thing', 'FAIL'), *SHARED)
        self.assertEqual(check.compare(text, BASELINE),
                         ['NOT RUN (remove or rename in baseline, was gimmick-disabled): Z-Move thing'])
        self.assertEqual(check.compare(text, BASELINE, partial=True), [])

    def test_unfinished_log_is_reported(self):
        text = log(('Tera thing', 'FAIL'), ('Z-Move thing', 'INVALID'), *SHARED, finished=False)
        self.assertEqual(check.compare(text, BASELINE),
                         ['log has no test summary: the run did not finish'])

    def test_skips_todo_and_expected_statuses(self):
        text = log(('Tera thing', 'FAIL'), ('Z-Move thing', 'INVALID'),
                   ('Later', 'TO_DO'), ('Known', 'KNOWN_FAILING'), ('Expected', 'EXPECTED_FAIL'),
                   *SHARED)
        self.assertEqual(check.compare(text, BASELINE), [])

    def test_truncated_output_is_reported(self):
        text = log(('Tera thing', 'FAIL'), ('Z-Move thing', 'INVALID'), *SHARED, total=5)
        self.assertEqual(check.compare(text, BASELINE),
                         ['log has 4 results but TOTAL 5: output is incomplete'])

    def test_changed_status_is_reported(self):
        text = log(('Tera thing', 'FAIL'), ('Z-Move thing', 'FAIL'), *SHARED)
        self.assertEqual(check.compare(text, BASELINE),
                         ['STATUS CHANGED INVALID -> FAIL (was gimmick-disabled): Z-Move thing'])

    def test_extra_failure_under_a_baseline_name_is_reported(self):
        # A second test named like a baseline entry starts failing.
        text = log(('Tera thing', 'FAIL'), ('Tera thing', 'FAIL'),
                   ('Z-Move thing', 'INVALID'), *SHARED)
        self.assertEqual(check.compare(text, BASELINE),
                         ['FAILED 2 times, baseline expects 1 (was gimmick-disabled): Tera thing'])

    def test_one_of_two_shared_name_tests_passing_is_reported(self):
        text = log(('Tera thing', 'FAIL'), ('Z-Move thing', 'INVALID'),
                   ('Shared name', 'FAIL'), ('Shared name', 'PASS'))
        self.assertEqual(check.compare(text, BASELINE),
                         ['FAILED 1 times, baseline expects 2 (was gimmick-disabled): Shared name'])

    def test_malformed_and_duplicate_baseline_lines_are_rejected(self):
        with self.assertRaises(ValueError):
            check.parse_baseline('FAIL | missing name\n')
        with self.assertRaises(ValueError):
            check.parse_baseline('PASS | reason | name\n')
        with self.assertRaises(ValueError):
            check.parse_baseline('FAIL | r | Same 1/2\nFAIL | r | Same 2/2\n')
        for status in ('FAIL x1', 'FAIL x0', 'FAIL x', 'FAILx2', 'PASS x2'):
            with self.assertRaises(ValueError):
                check.parse_baseline(f'{status} | r | name\n')
        self.assertEqual(check.parse_baseline('CRASH x3 | r | name\n'),
                         {'name': (frozenset({'CRASH'}), 3, 'r')})
        with self.assertRaises(ValueError):
            check.parse_baseline('TIMEOUT/PASS | r | name\n')

    def test_either_status_is_accepted_when_listed(self):
        baseline = BASELINE + 'TIMEOUT/FAIL | gimmick-disabled | Flaky\n'
        for status in ('TIMEOUT', 'FAIL'):
            text = log(('Tera thing', 'FAIL'), ('Z-Move thing', 'INVALID'), *SHARED, ('Flaky', status))
            self.assertEqual(check.compare(text, baseline), [])
        text = log(('Tera thing', 'FAIL'), ('Z-Move thing', 'INVALID'), *SHARED, ('Flaky', 'CRASH'))
        self.assertEqual(check.compare(text, baseline),
                         ['STATUS CHANGED FAIL/TIMEOUT -> CRASH (was gimmick-disabled): Flaky'])

    def test_committed_baseline_is_valid_and_explained(self):
        entries = check.parse_baseline(check.BASELINE.read_text())
        self.assertGreater(len(entries), 0)
        reasons = {reason for _, _, reason in entries.values()}
        self.assertEqual(reasons, {'gimmick-disabled', 'level-cap', 'runner-self-test', 'primal-disabled'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
