"""Source checks for Averon scripted battles (no compiler needed).

Checks data/scripts/averon_scripted_battle.inc and every engine script that
uses its macros:
- each averon_scripted_battle is immediately followed by a VAR_RESULT branch;
- a win can never fall through into a loss label (the line before every
  label ending in "Lost" is an unconditional goto or end);
- the macro wraps exactly one trainer battle between Begin and Finish;
- every native the macros call is defined in src/averon_scripted_battle.c
  and requests script effects;
- the known boot, soft-reset and in-process reload sequences still reach
  the BIOS EWRAM reset before initialization/load;
- normal-load and Continue references in top-level engine C files stay at
  their reviewed entry points. New dynamic/aliased references fail closed.
These are bounded source guards, not a C preprocessor/control-flow proof
or execution of hardware reset. Indirection introduced in headers needs
separate review. A direct low-level LoadGameSave does not reset special RAM.
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


def c_code(text):
    """Hide comments and strings without changing offsets or line numbers."""
    ignored = r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(ignored, lambda m: re.sub(r'[^\n]', ' ', m.group()), text, flags=re.S)


def function_body(text, name):
    text = c_code(text)
    match = re.search(rf'\b{re.escape(name)}\s*\([^;{{}}]*\)\s*\{{', text)
    if match is None:
        return ''
    start, depth = match.end(), 1
    for end in range(start, len(text)):
        depth += (text[end] == '{') - (text[end] == '}')
        if depth == 0:
            return text[start:end]
    return ''


def asm_instructions(text, label):
    text = '\n'.join(line.split('@', 1)[0] for line in text.splitlines())
    match = re.search(rf'(?m)^{re.escape(label)}::?[ \t]*$', text)
    if match is None:
        return []
    body = re.split(r'(?m)^(?:[A-Za-z_]\w*::?(?=\s|$)|[ \t]*thumb_func_end\b)',
                    text[match.end():], maxsplit=1)[0]
    return [re.sub(r'\s+', '', line).lower() for line in body.splitlines()
            if line.strip() and not line.lstrip().startswith('.')]


def reset_sources():
    names = ('src/crt0.s', 'libagbsyscall/libagbsyscall.s', 'include/gba/syscall.h')
    sources = {name: (ENGINE / name).read_text() for name in names}
    sources.update((str(p.relative_to(ENGINE)), p.read_text()) for p in (ENGINE / 'src').glob('*.c'))
    return sources


def reset_problems(sources):
    """Pin the reviewed reset instructions and ordering, not arbitrary C flow."""
    problems = []
    header = c_code(sources['include/gba/syscall.h'])
    values = {}
    for name in ('RESET_EWRAM', 'RESET_ALL'):
        match = re.search(rf'(?m)^\s*#\s*define\s+{name}\s+(0[xX][0-9a-fA-F]+|[0-9]+)\s*$', header)
        values[name] = int(match.group(1), 0) if match else 0
    if values['RESET_EWRAM'] != 1 or values['RESET_ALL'] != 0xFF or not values['RESET_ALL'] & values['RESET_EWRAM']:
        problems.append('RESET_ALL must include the BIOS EWRAM bit (RESET_EWRAM = 1)')
    boot = asm_instructions(sources['src/crt0.s'], 'Init')
    boot_reset = ('movr0,#255', 'svc#1<<16', 'blinitializeworkingmemory')
    # Init is ARM code: BIOS RegisterRamReset (1) occupies bits 16..23.
    modes = re.findall(r'(?m)^\s*\.(arm|thumb)\b', sources['src/crt0.s'].split('Init::', 1)[0])
    if (not modes or modes[-1] != 'arm' or boot.count('blinitializeworkingmemory') != 1
            or not any(tuple(boot[i:i + 3]) == boot_reset for i in range(len(boot)))):
        problems.append('ARM boot must reset all RAM via BIOS 1 immediately before InitializeWorkingMemory')
    wrappers = sources['libagbsyscall/libagbsyscall.s']
    if asm_instructions(wrappers, 'RegisterRamReset') != ['svc#1', 'bxlr']:
        problems.append('RegisterRamReset must call BIOS 1')
    soft = asm_instructions(wrappers, 'SoftReset')
    if [line for line in soft if line.startswith('svc')] != ['svc#1', 'svc#0']:
        problems.append('SoftReset must call RegisterRamReset BIOS 1 before restarting with BIOS 0')
    if any('r0' in line for line in soft):
        problems.append('SoftReset must preserve its reset-mask argument in r0')
    main = function_body(sources['src/main.c'], 'DoSoftReset')
    if [arg.strip() for arg in re.findall(r'\bSoftReset\s*\(([^)]*)\)', main)] != ['RESET_ALL']:
        problems.append('DoSoftReset must request RESET_ALL')
    reload = function_body(sources['src/reload_save.c'], 'ReloadSave')
    sequence = [re.search(pattern, reload) for pattern in (
        r'\bRegisterRamReset\s*\(\s*RESET_EWRAM\s*\)\s*;',
        r'\bReInitializeEWRAM\s*\(\s*\)\s*;',
        r'\bLoadGameSave\s*\(\s*SAVE_NORMAL\s*\)\s*;',
    )]
    if not all(sequence) or [m.start() for m in sequence] != sorted(m.start() for m in sequence):
        problems.append('ReloadSave must reset EWRAM, initialize it, then load SAVE_NORMAL')
    return problems


def loader_problems(sources):
    """Reject unreviewed visible loader/callback references, including aliases."""
    problems, loads, continues = [], [], []
    for path, raw in sources.items():
        if not path.startswith('src/') or not path.endswith('.c'):
            continue
        source = c_code(raw)
        for match in re.finditer(r'\bLoadGameSave\b', source):
            tail = source[match.end():]
            if path == 'src/save.c' and re.match(r'\s*\(\s*u8\s+saveType\s*\)\s*\{', tail):
                continue  # The actual function definition, not a loader call.
            call = re.match(r'\s*\(\s*(SAVE_NORMAL|SAVE_HALL_OF_FAME)\s*\)', tail)
            if call is None:
                problems.append(f'{path}: dynamic/aliased LoadGameSave reference requires review')
            elif call.group(1) == 'SAVE_NORMAL':
                loads.append(path)
        for match in re.finditer(r'\bCB2_ContinueSavedGame\b', source):
            tail = source[match.end():]
            if path == 'src/overworld.c' and re.match(r'\s*\(\s*void\s*\)\s*\{', tail):
                continue
            if (re.search(r'\bSetMainCallback2\s*\(\s*$', source[:match.start()])
                    and re.match(r'\s*\)', tail)):
                continues.append(path)
            else:
                problems.append(f'{path}: aliased/direct Continue reference requires review')
    if sorted(loads) != ['src/intro.c', 'src/reload_save.c']:
        problems.append(f'unreviewed normal-save call sites: {sorted(loads)}')
    if sorted(continues) != ['src/main_menu.c', 'src/reload_save.c']:
        problems.append(f'unreviewed Continue call sites: {sorted(continues)}')
    return problems


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
        sources = reset_sources()
        self.assertRegex(c_code(sources['src/event_data.c']), r'\bEWRAM_DATA\s+static\s+u8\s+sSpecialFlags\[')
        self.assertEqual(loader_problems(sources), [])
        self.assertEqual(reset_problems(sources), [])

    def test_reset_guard_rejects_boot_mask_and_reload_mutations(self):
        sources = reset_sources()
        self.assertEqual(reset_problems(sources), [], 'valid reset control must pass before mutations')
        mutations = (
            ('src/crt0.s', 'svc #1 << 16', 'svc #0 << 16'),
            ('src/crt0.s', 'mov r0, #255', 'mov r0, #254'),
            ('src/crt0.s', 'svc #1 << 16', '@ svc #1 << 16'),
            ('src/crt0.s', 'bl InitializeWorkingMemory', '@ bl InitializeWorkingMemory'),
            ('src/crt0.s', 'mov r0, #255', 'bl InitializeWorkingMemory\n\tmov r0, #255'),
            ('src/crt0.s', '\t.arm', '\t.thumb'),
            ('include/gba/syscall.h', '#define RESET_EWRAM      0x01', '#define RESET_EWRAM      0x02'),
            ('include/gba/syscall.h', '#define RESET_ALL        0xFF', '#define RESET_ALL        0xFE'),
            ('libagbsyscall/libagbsyscall.s', 'RegisterRamReset:\n\tsvc #1', 'RegisterRamReset:\n\tsvc #0'),
            ('libagbsyscall/libagbsyscall.s', '\tsvc #1\n\tsvc #0\n\t.pool\n\tthumb_func_end SoftReset\n',
             '\tsvc #0\n\tsvc #1\n\t.pool\n\tthumb_func_end SoftReset\n'),
            ('libagbsyscall/libagbsyscall.s', 'SoftReset:\n', 'SoftReset:\n\tsvc #0\n'),
            ('libagbsyscall/libagbsyscall.s', 'SoftReset:\n', 'SoftReset:\n\tmovs r0, #0\n'),
            ('src/main.c', 'SoftReset(RESET_ALL);', 'SoftReset(RESET_IWRAM);'),
            ('src/main.c', 'SoftReset(RESET_ALL);', 'SoftReset(RESET_IWRAM); SoftReset(RESET_ALL);'),
            ('src/reload_save.c', 'RegisterRamReset(RESET_EWRAM);', 'RegisterRamReset(RESET_IWRAM);'),
            ('src/reload_save.c', 'RegisterRamReset(RESET_EWRAM);', '/* RegisterRamReset(RESET_EWRAM); */'),
            ('src/reload_save.c', 'ReInitializeEWRAM();', '/* ReInitializeEWRAM(); */'),
            ('src/reload_save.c', 'RegisterRamReset(RESET_EWRAM);', 'LoadGameSave(SAVE_NORMAL);\n    RegisterRamReset(RESET_EWRAM);'),
        )
        rejected = 0
        for path, old, new in mutations:
            with self.subTest(path=path, mutation=new):
                self.assertIn(old, sources[path], 'mutation target no longer exists')
                changed = dict(sources)
                changed[path] = sources[path].replace(old, new, 1)
                errors = reset_problems(changed)
                rejected += bool(errors)
                self.assertTrue(errors, 'unsafe reset mutation survived')
        print(f'reset mutations rejected: {rejected}/{len(mutations)}')

    def test_loader_guard_accepts_whitespace_and_ignores_comments(self):
        sources = reset_sources()
        changed = {path: text.replace('LoadGameSave(SAVE_NORMAL)', 'LoadGameSave /* load */ (\n SAVE_NORMAL \n)')
                   .replace('SetMainCallback2(CB2_ContinueSavedGame)', 'SetMainCallback2 ( /* callback */ CB2_ContinueSavedGame )')
                   for path, text in sources.items()}
        changed['src/new_non_loader.c'] = ('// LoadGameSave(SAVE_NORMAL);\n'
            '/* SetMainCallback2(CB2_ContinueSavedGame); */\n'
            'const char *note = "LoadGameSave(SAVE_NORMAL)";\n')
        self.assertEqual(loader_problems(changed), [])
        self.assertEqual(reset_problems(changed), [])

    def test_loader_guard_rejects_new_dynamic_and_aliased_entrypoints(self):
        sources = reset_sources()
        self.assertEqual(loader_problems(sources), [], 'valid loader control must pass before mutations')
        mutations = (
            'void NewLoad(void) { LoadGameSave ( SAVE_NORMAL ); }',
            'void NewLoad(u8 kind) { LoadGameSave(kind); }',
            'u8 (*load)(u8) = LoadGameSave;',
            '#define load SaveAlias\n#define SaveAlias LoadGameSave',
            'void NewContinue(void) { SetMainCallback2 ( CB2_ContinueSavedGame ); }',
            'void (*next)(void) = CB2_ContinueSavedGame;',
            'void NewContinue(void) { CB2_ContinueSavedGame(); }',
        )
        rejected = 0
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                changed = dict(sources, **{'src/new_entrypoint.c': mutation})
                errors = loader_problems(changed)
                rejected += bool(errors)
                self.assertTrue(errors, 'unreviewed loader mutation survived')
        print(f'loader mutations rejected: {rejected}/{len(mutations)}')

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
