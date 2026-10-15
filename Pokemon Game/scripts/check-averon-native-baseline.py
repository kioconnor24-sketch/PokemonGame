"""Compare a full native `make check` log with Averon's expected-failure baseline.

Under Averon's config some upstream pokeemerald-expansion tests are expected
to fail (disabled gimmicks, hard level caps). This check fails when:
- a test fails that is not in the baseline (a new regression), or
- a baseline test now passes or is missing from the log (stale entry), or
- the log has no test summary (the run did not finish).

Usage, from "Pokemon Game/engine":
    make -j20 -O check > ../native-check.log 2>&1
    python3 ../scripts/check-averon-native-baseline.py ../native-check.log
Add --partial for a TESTS=... subset run.
"""
from pathlib import Path
import argparse
import re
import sys

BASELINE = Path(__file__).with_name('averon-native-test-baseline.txt')
FAILING = ('FAIL', 'INVALID', 'ERROR', 'TIMEOUT', 'CRASH')
RESULT = re.compile(r'^\[\d+\] (.+): ([A-Z_]+)$')
PARAM_SUFFIX = re.compile(r'( \d+/\d+)?( \(\d+/[\d?]+\))?$')
ANSI = re.compile(r'\x1b\[[0-9;]*m')


def normalize(name):
    """Drop the per-parameter suffix ("1/2", "(1/?)", "1/9 (2/2)")."""
    return PARAM_SUFFIX.sub('', name.strip())


def parse_log(text):
    """Return ({name: failing status}, {passing names}, finished?)."""
    failing, passing, finished = {}, set(), False
    for raw in text.splitlines():
        line = ANSI.sub('', raw).strip()
        if line.startswith('- Tests') and 'TOTAL' in line:
            finished = True
        match = RESULT.match(line)
        if not match:
            continue
        name, status = normalize(match.group(1)), match.group(2)
        if status in FAILING:
            failing[name] = status
        elif status == 'PASS':
            passing.add(name)
    # A parametrized test can pass for one parameter and fail for another.
    return failing, passing - set(failing), finished


def parse_baseline(text):
    """Return {name: (status, reason)} from 'STATUS | reason | name' lines."""
    entries = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        parts = [part.strip() for part in line.split('|', 2)]
        if len(parts) != 3 or parts[0] not in FAILING or not parts[1] or not parts[2]:
            raise ValueError(f'baseline line {number}: expected "STATUS | reason | test name"')
        name = normalize(parts[2])
        if name in entries:
            raise ValueError(f'baseline line {number}: duplicate entry for {name!r}')
        entries[name] = (parts[0], parts[1])
    return entries


def compare(log_text, baseline_text, partial=False):
    """Return a list of problems; empty means the run matches the baseline.

    partial: the log is a TESTS=... subset, so baseline tests absent from it
    are not reported."""
    failing, passing, finished = parse_log(log_text)
    baseline = parse_baseline(baseline_text)
    problems = []
    if not finished:
        problems.append('log has no test summary: the run did not finish')
    for name, status in sorted(failing.items()):
        if name not in baseline:
            problems.append(f'NEW {status}: {name}')
    for name, (status, reason) in sorted(baseline.items()):
        if name in failing:
            continue
        if name in passing:
            problems.append(f'NOW PASSES (remove from baseline, was {reason}): {name}')
        elif finished and not partial:
            problems.append(f'NOT RUN (remove or rename in baseline, was {reason}): {name}')
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('log', type=Path)
    parser.add_argument('--baseline', type=Path, default=BASELINE)
    parser.add_argument('--partial', action='store_true',
                        help='log is a TESTS=... subset; skip the not-run check')
    args = parser.parse_args(argv)
    log_text = args.log.read_text(errors='replace')
    problems = compare(log_text, args.baseline.read_text(), args.partial)
    failing, _, _ = parse_log(log_text)
    print(f'failing tests in log: {len(failing)}; baseline entries: '
          f'{len(parse_baseline(args.baseline.read_text()))}')
    for problem in problems:
        print(problem)
    print('OK: matches the Averon baseline' if not problems else f'{len(problems)} problem(s)')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
