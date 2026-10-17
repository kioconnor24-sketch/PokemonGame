"""Source checks for the Averon static-encounter contract (no compiler needed).

The native tests in engine/test/averon_legend.c run the behavior; these
checks keep them complete when the engine changes:
- every B_OUTCOME_ value in include/constants/battle.h is in the test's
  outcome table, so a new upstream outcome cannot slip past the
  "records nothing" test;
- AveronLegend_ClassifyOutcome returns CAUGHT only for B_OUTCOME_CAUGHT and
  DEFEATED only for B_OUTCOME_WON, with everything else falling to default;
- event_scripts.s registers the macros exactly once, and no game script
  uses them yet (no encounter is approved).
"""
from pathlib import Path
import re
import unittest

ENGINE = Path(__file__).resolve().parents[1] / 'engine'


def read(relative):
    return (ENGINE / relative).read_text(encoding='utf-8')


def function_body(source, name):
    start = source.index(name + '(')
    open_brace = source.index('{', start)
    depth = 0
    for index in range(open_brace, len(source)):
        if source[index] == '{':
            depth += 1
        elif source[index] == '}':
            depth -= 1
            if depth == 0:
                return source[open_brace:index + 1]
    raise ValueError(f'unterminated body for {name}')


class AveronLegendSourceTests(unittest.TestCase):
    def test_every_engine_outcome_is_in_the_native_outcome_table(self):
        outcomes = set(re.findall(r'^#define (B_OUTCOME_\w+)', read('include/constants/battle.h'), re.M))
        self.assertGreaterEqual(len(outcomes), 11)
        table = read('test/averon_legend.c')
        table = table[table.index('sAllOutcomes[]'):]
        table = table[:table.index('};')]
        missing = sorted(name for name in outcomes if name not in table)
        self.assertEqual(missing, [], 'add these outcomes to sAllOutcomes')

    def test_only_a_capture_is_caught_and_only_a_knockout_is_defeated(self):
        body = function_body(read('src/averon_legend.c'), 'enum AveronLegendResult AveronLegend_ClassifyOutcome')
        # Every case label, so a fall-through label is caught too.
        self.assertEqual(re.findall(r'case (\w+):', body), ['B_OUTCOME_CAUGHT', 'B_OUTCOME_WON'])
        self.assertEqual(re.findall(r'case (\w+):\s*return (\w+);', body),
                         [('B_OUTCOME_CAUGHT', 'AVERON_LEGEND_CAUGHT'),
                          ('B_OUTCOME_WON', 'AVERON_LEGEND_DEFEATED')])
        self.assertRegex(body, r'default:\s*return AVERON_LEGEND_AVAILABLE;')
        self.assertEqual(body.count('return'), 3)

    def test_macros_are_registered_once(self):
        event = read('data/event_scripts.s')
        includes = re.findall(r'^\s*\.include\s+"data/scripts/averon_legend\.inc"\s*$', event, re.M)
        self.assertEqual(len(includes), 1)
        # Macros must be defined before any script include that could use them.
        self.assertLess(event.index('"data/scripts/averon_legend.inc"'),
                        event.index('"data/averon_optional_sidequests.inc"'))

    def test_no_game_script_uses_the_macros(self):
        users = []
        for path in (ENGINE / 'data').rglob('*'):
            if path.suffix not in ('.inc', '.s', '.pory') or path.name == 'averon_legend.inc':
                continue
            text = path.read_text(encoding='utf-8', errors='replace')
            if re.search(r'^\s*averon_legend_\w+', text, re.M):
                users.append(str(path.relative_to(ENGINE)))
        self.assertEqual(users, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
