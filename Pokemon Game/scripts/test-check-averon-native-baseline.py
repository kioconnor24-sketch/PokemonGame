"""Fixtures for check-averon-native-baseline.py (no compiler needed)."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).with_name('check-averon-native-baseline.py')
spec = importlib.util.spec_from_file_location('averon_native_baseline', SCRIPT)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)

RED, GREEN, RESET = '\x1b[31m', '\x1b[32m', '\x1b[0m'
SUMMARY = '- Tests \x1b[34mTOTAL\x1b[0m:           4\n'
BASELINE = '''# comment
FAIL | gimmick-disabled | Tera thing
INVALID | gimmick-disabled | Z-Move thing
'''


def log(*results, finished=True):
    lines = [f'[{i:02}] {name}: {(RED if status != "PASS" else GREEN)}{status}{RESET}'
             for i, (name, status) in enumerate(results)]
    return '\n'.join(lines) + '\n' + (SUMMARY if finished else '')


class NativeBaselineTests(unittest.TestCase):
    def test_matching_run_has_no_problems(self):
        text = log(('Tera thing 1/2', 'FAIL'), ('Tera thing 2/2', 'PASS'),
                   ('Z-Move thing (1/?)', 'INVALID'), ('Ordinary test', 'PASS'))
        self.assertEqual(check.compare(text, BASELINE), [])

    def test_new_failure_is_reported(self):
        text = log(('Tera thing', 'FAIL'), ('Z-Move thing', 'INVALID'),
                   ('Ordinary test 1/9 (2/2)', 'FAIL'), ('Crashy', 'CRASH'))
        self.assertEqual(check.compare(text, BASELINE),
                         ['NEW CRASH: Crashy', 'NEW FAIL: Ordinary test'])

    def test_baseline_test_that_now_passes_is_reported(self):
        text = log(('Tera thing', 'PASS'), ('Z-Move thing', 'INVALID'))
        self.assertEqual(check.compare(text, BASELINE),
                         ['NOW PASSES (remove from baseline, was gimmick-disabled): Tera thing'])

    def test_missing_baseline_test_is_reported_unless_partial(self):
        text = log(('Tera thing', 'FAIL'))
        self.assertEqual(check.compare(text, BASELINE),
                         ['NOT RUN (remove or rename in baseline, was gimmick-disabled): Z-Move thing'])
        self.assertEqual(check.compare(text, BASELINE, partial=True), [])

    def test_unfinished_log_is_reported(self):
        text = log(('Tera thing', 'FAIL'), ('Z-Move thing', 'INVALID'), finished=False)
        self.assertEqual(check.compare(text, BASELINE),
                         ['log has no test summary: the run did not finish'])

    def test_skips_todo_and_expected_statuses(self):
        text = log(('Tera thing', 'FAIL'), ('Z-Move thing', 'INVALID'),
                   ('Later', 'TO_DO'), ('Known', 'KNOWN_FAILING'), ('Expected', 'EXPECTED_FAIL'))
        self.assertEqual(check.compare(text, BASELINE), [])

    def test_malformed_and_duplicate_baseline_lines_are_rejected(self):
        with self.assertRaises(ValueError):
            check.parse_baseline('FAIL | missing name\n')
        with self.assertRaises(ValueError):
            check.parse_baseline('PASS | reason | name\n')
        with self.assertRaises(ValueError):
            check.parse_baseline('FAIL | r | Same 1/2\nFAIL | r | Same 2/2\n')

    def test_committed_baseline_is_valid_and_explained(self):
        entries = check.parse_baseline(check.BASELINE.read_text())
        self.assertGreater(len(entries), 0)
        reasons = {reason for _, reason in entries.values()}
        self.assertEqual(reasons, {'gimmick-disabled', 'level-cap', 'runner-self-test'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
