"""Compare a full native `make check` log with Averon's expected-failure baseline.

Under Averon's config some upstream pokeemerald-expansion tests are expected
to fail (disabled gimmicks, hard level caps). This check fails when:
- a test fails that is not in the baseline (a new regression), or
- a baseline test fails with a different status, or more or fewer times
  (some test names are used by two tests; "FAIL x2" expects both to fail), or
- a baseline test now passes or is missing from the log (stale entry), or
- the log has no test summary, or fewer results than its TOTAL (the run did
  not finish).

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
TOTAL = re.compile(r'^- Tests TOTAL:\s+(\d+)')
STATUS_COUNT = re.compile(r'^([A-Z_]+)(?: x(\d+))?$')
PARAM_SUFFIX = re.compile(r'( \d+/\d+)?( \(\d+/[\d?]+\))?$')
ANSI = re.compile(r'\x1b\[[0-9;]*m')


def normalize(name):
    """Drop the per-parameter suffix ("1/2", "(1/?)", "1/9 (2/2)")."""
    return PARAM_SUFFIX.sub('', name.strip())


def parse_log(text):
    """Return ({name: [failing statuses]}, {passing names}, results, total).

    total is the summary's TOTAL, or None if the run did not finish."""
    failing, passing, results, total = {}, set(), 0, None
    for raw in text.splitlines():
        line = ANSI.sub('', raw).strip()
        match = TOTAL.match(line)
        if match:
            total = int(match.group(1))
        match = RESULT.match(line)
        if not match:
            continue
        results += 1
        name, status = normalize(match.group(1)), match.group(2)
        if status in FAILING:
            failing.setdefault(name, []).append(status)
        elif status == 'PASS':
            passing.add(name)
    # Two tests with one name can pass and fail; the failure is what counts.
    return failing, passing - set(failing), results, total


def parse_baseline(text):
    """Return {name: (status, count, reason)} from 'STATUS | reason | name'
    lines. 'STATUS xN' means N tests share the name and all N fail."""
    entries = {}
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        parts = [part.strip() for part in line.split('|', 2)]
        status = STATUS_COUNT.match(parts[0]) if len(parts) == 3 else None
        if (not status or status.group(1) not in FAILING or status.group(2) in ('0', '1')
                or not parts[1] or not parts[2]):
            raise ValueError(f'baseline line {number}: expected "STATUS[ xN] | reason | test name"')
        name = normalize(parts[2])
        if name in entries:
            raise ValueError(f'baseline line {number}: duplicate entry for {name!r}')
        entries[name] = (status.group(1), int(status.group(2) or 1), parts[1])
    return entries


def compare(log_text, baseline_text, partial=False):
    """Return a list of problems; empty means the run matches the baseline.

    partial: the log is a TESTS=... subset, so baseline tests absent from it
    are not reported."""
    failing, passing, results, total = parse_log(log_text)
    baseline = parse_baseline(baseline_text)
    finished = total is not None
    problems = []
    if not finished:
        problems.append('log has no test summary: the run did not finish')
    elif results != total:
        problems.append(f'log has {results} results but TOTAL {total}: output is incomplete')
    for name, statuses in sorted(failing.items()):
        if name not in baseline:
            problems.append(f'NEW {"/".join(sorted(set(statuses)))}: {name}')
            continue
        status, count, reason = baseline[name]
        if set(statuses) != {status}:
            problems.append(f'STATUS CHANGED {status} -> {"/".join(sorted(set(statuses)))} '
                            f'(was {reason}): {name}')
        elif len(statuses) != count:
            problems.append(f'FAILED {len(statuses)} times, baseline expects {count} '
                            f'(was {reason}): {name}')
    for name, (status, count, reason) in sorted(baseline.items()):
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
    failing = parse_log(log_text)[0]
    print(f'failing tests in log: {len(failing)}; baseline entries: '
          f'{len(parse_baseline(args.baseline.read_text()))}')
    for problem in problems:
        print(problem)
    print('OK: matches the Averon baseline' if not problems else f'{len(problems)} problem(s)')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
