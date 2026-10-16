"""Source checks for Averon scripted battles (no compiler needed).

Checks data/scripts/averon_scripted_battle.inc and every engine script that
uses its macros:
- each averon_scripted_battle is immediately followed by a VAR_RESULT branch;
- a win can never fall through into a loss label (the line before every
  label ending in "Lost" is an unconditional goto or end);
- the macro wraps exactly one trainer battle between Begin and Finish;
- every native the macros call is defined in src/averon_scripted_battle.c
  and requests script effects;
- every in-process load of the normal save still resets EWRAM first, so the
  RAM-only no-whiteout special flag cannot survive a load (a native test
  cannot do the hardware reset).
Example scripts in the .inc header comments are checked like real scripts.
"""
from pathlib import Path
import re
import unittest

ENGINE = Path(__file__).resolve().parent.parent / 'engine'
INC = ENGINE / 'data/scripts/averon_scripted_battle.inc'
SOURCE = ENGINE / 'src/averon_scripted_battle.c'

LABEL = re.compile(r'^([A-Za-z_][A-Za-z0-9_]*)::?$')
UNCONDITIONAL = re.compile(r'^(goto|end|return|averon_respawn)\b')


def example_lines(text):
    """Script lines from the leading '@' comment block, comment marker removed."""
    lines = []
    for raw in text.splitlines():
        if not raw.startswith('@'):
            break
        lines.append(raw[1:].split(' @ ')[0].strip())
    return lines


def code_lines(text):
    return [raw.split('@')[0].strip() for raw in text.splitlines()]


def find_problems(lines, where):
    """Return control-flow problems in a list of script lines."""
    problems = []
    body = [(n, line) for n, line in enumerate(lines, 1) if line]
    for i, (n, line) in enumerate(body):
        if line.startswith('averon_scripted_battle '):
            nxt = body[i + 1][1] if i + 1 < len(body) else ''
            if not nxt.startswith('goto_if_eq VAR_RESULT,'):
                problems.append(f'{where}:{n}: averon_scripted_battle not followed by a VAR_RESULT branch')
        label = LABEL.match(line)
        if label and label.group(1).endswith('Lost') and i > 0:
            prev = body[i - 1][1]
            if not UNCONDITIONAL.match(prev):
                problems.append(f'{where}:{n}: {label.group(1)} can be reached by falling through from "{prev}"')
    return problems


def macro_body(text, name):
    match = re.search(rf'\.macro {name}\b[^\n]*\n(.*?)\n\s*\.endm', text, re.S)
    return [line.strip() for line in match.group(1).splitlines() if line.strip() and not line.strip().startswith('@')] if match else None


class ScriptedBattleSourceTests(unittest.TestCase):
    def test_examples_have_no_win_fallthrough(self):
        lines = example_lines(INC.read_text())
        self.assertGreater(sum(l.startswith('averon_scripted_battle ') for l in lines), 0)
        self.assertEqual(find_problems(lines, INC.name), [])

    def test_engine_scripts_using_the_macros_have_no_win_fallthrough(self):
        problems, users = [], 0
        for path in sorted((ENGINE / 'data').rglob('*.inc')):
            if path == INC:
                continue
            text = path.read_text(errors='replace')
            if 'averon_scripted_battle ' in text:
                users += 1
                problems += find_problems(code_lines(text), str(path.relative_to(ENGINE)))
        self.assertEqual(problems, [])
        print(f'scripts using averon_scripted_battle: {users}')

    def test_macro_wraps_one_battle_between_begin_and_finish(self):
        body = macro_body(INC.read_text(), 'averon_scripted_battle')
        self.assertEqual(body, [
            'callnative AveronScriptedBattle_Begin, requests_effects=1',
            'trainerbattle_no_intro \\trainer, \\lose_text',
            'callnative AveronScriptedBattle_Finish, requests_effects=1',
        ])

    def test_natives_exist_and_request_effects(self):
        inc, src = INC.read_text(), SOURCE.read_text()
        calls = re.findall(r'^\s*callnative (AveronScriptedBattle_\w+)(.*)$', inc, re.M)
        self.assertGreaterEqual(len(calls), 5)
        for name, rest in calls:
            self.assertIn('requests_effects=1', rest, name)
            match = re.search(rf'^void {name}\(struct ScriptContext \*ctx\)\n\{{\n(.*?)\n\}}', src, re.M | re.S)
            self.assertIsNotNone(match, f'{name} not defined in {SOURCE.name}')
            self.assertIn('Script_RequestEffects(', match.group(1), name)

    def test_every_normal_save_load_resets_ewram_first(self):
        src = lambda name: (ENGINE / 'src' / name).read_text()
        self.assertRegex(src('event_data.c'), r'\bEWRAM_DATA static u8 sSpecialFlags\[')
        # Exactly these callers load the normal save or continue a saved game.
        callers = sorted(str(p.relative_to(ENGINE)) for p in (ENGINE / 'src').glob('*.c')
                         if re.search(r'LoadGameSave\(SAVE_NORMAL\)|SetMainCallback2\(CB2_ContinueSavedGame\)', p.read_text()))
        self.assertEqual(callers, ['src/intro.c', 'src/main_menu.c', 'src/reload_save.c'])
        # Boot: crt0 zeroes EWRAM. Main menu: reached from boot or DoSoftReset.
        self.assertRegex(src('main.c'), r'void DoSoftReset\(void\)\n\{[^}]*SoftReset\(RESET_ALL\);\n\}')
        # Link-error reload: resets EWRAM before loading.
        reload = src('reload_save.c')
        self.assertLess(reload.index('RegisterRamReset(RESET_EWRAM);'), reload.index('LoadGameSave(SAVE_NORMAL);'))

    def test_checker_detects_fallthrough_and_missing_branch(self):
        bad = [
            'averon_scripted_battle TRAINER_A, Text_A',
            'goto_if_eq VAR_RESULT, TRUE, Scene_Lost',
            'special HealPlayerParty',
            'Scene_Lost:',
            'averon_respawn',
            'averon_scripted_battle TRAINER_B, Text_B',
            'msgbox Text_B',
        ]
        problems = find_problems(bad, 'fixture')
        self.assertEqual(len(problems), 2, problems)
        self.assertIn('Scene_Lost can be reached by falling through', problems[0])
        self.assertIn('not followed by a VAR_RESULT branch', problems[1])


if __name__ == '__main__':
    unittest.main(verbosity=2)
