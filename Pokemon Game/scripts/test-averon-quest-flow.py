"""Interpret the limited native command subset used by optional quest source.

This is a source-level state machine check, not an engine runtime test.
"""
from pathlib import Path
import re
import unittest

DIR = Path(__file__).resolve().parent
SOURCE = (DIR / 'averon-optional-sidequests.inc').read_text(encoding='utf-8')
LABEL = re.compile(r'^([A-Za-z][A-Za-z0-9_]*):{1,2}$')
FLAG = re.compile(r'\bFLAG_AVERON_[A-Z0-9_]+\b')
JUMP = re.compile(r'^goto(?:_if_(?:set|unset|eq))?\s+(.*)$')


def compile_source(text):
    """Index source labels and instructions; do not evaluate .string escapes."""
    lines = text.splitlines()
    labels = {}
    for i, line in enumerate(lines):
        match = LABEL.fullmatch(line.strip())
        if match:
            if match[1] in labels:
                raise ValueError('Duplicate event label: ' + match[1])
            labels[match[1]] = i + 1
    for line in lines:
        instr = line.strip()
        if not instr or instr.startswith(('@', '.')):
            continue
        found = JUMP.match(instr)
        if found:
            dest = found[1].split(',')[-1].strip()
            if dest not in labels:
                raise ValueError('Missing event branch label: ' + dest)
        if instr.startswith('msgbox '):
            dest = instr.split()[1].rstrip(',')
            if dest not in labels:
                raise ValueError('Missing dialogue text label: ' + dest)
    return lines, labels


class QuestVM:
    def __init__(self, source=SOURCE):
        self.lines, self.labels = compile_source(source)
        self.flags = set()
        self.bag = {}

    def talk(self, speaker, *, accept=True, capacity=True):
        pc = self.labels[speaker]
        result = True
        inventory_change = {}
        stack = []
        for _ in range(100):
            if pc >= len(self.lines):
                raise RuntimeError('Event ran past end of file')
            cmd = self.lines[pc].strip()
            pc += 1
            if not cmd or cmd.startswith(('@', '.')) or LABEL.fullmatch(cmd):
                continue
            parts = cmd.split(maxsplit=1)
            op = parts[0]
            arg = parts[1] if len(parts) == 2 else ''
            if op == 'end':
                return inventory_change
            if op == 'call':
                stack.append(pc)
                pc = self.labels[arg]
                continue
            if op == 'return':
                if not stack:
                    return inventory_change
                pc = stack.pop()
                continue
            if op == 'setvar':
                if arg != 'VAR_RESULT, FALSE':
                    raise RuntimeError('Unsupported variable assignment: ' + arg)
                result = False
                continue
            if op in {'lock', 'faceplayer', 'release', 'playfanfare', 'waitfanfare'}:
                continue
            if op == 'msgbox':
                if 'MSGBOX_YESNO' in arg:
                    result = accept
                continue
            if op == 'setflag':
                self.flags.add(arg)
                continue
            if op == 'additem':
                item, count = (s.strip() for s in arg.split(','))
                result = capacity
                if capacity:
                    self.bag[item] = self.bag.get(item, 0) + int(count)
                    inventory_change[item] = inventory_change.get(item, 0) + int(count)
                continue
            if op == 'goto':
                pc = self.labels[arg]
                continue
            if op in {'goto_if_set', 'goto_if_unset'}:
                flag, dest = (s.strip() for s in arg.split(','))
                flag_set = flag in self.flags
                if (op == 'goto_if_set' and flag_set) or (op == 'goto_if_unset' and not flag_set):
                    pc = self.labels[dest]
                continue
            if op == 'goto_if_eq':
                left, right, dest = (s.strip() for s in arg.split(','))
                if left != 'VAR_RESULT' or right not in {'TRUE', 'FALSE', 'NO'}:
                    raise RuntimeError('Unsupported comparison: ' + arg)
                if result == (right == 'TRUE'):
                    pc = self.labels[dest]
                continue
            raise RuntimeError(f'Unknown event command: {cmd}')
        raise RuntimeError('Quest script exceeded bounded execution steps')


class NativeQuestFlowTests(unittest.TestCase):
    def test_every_go_to_and_msgbox_target_exists(self):
        lines, labels = compile_source(SOURCE)
        self.assertGreaterEqual(len(labels), 30)

    def test_field_notes_decline_accept_and_observation(self):
        game = QuestVM()
        self.assertEqual(game.talk('Averon_FieldNotes_Observer'), {})
        self.assertNotIn('FLAG_AVERON_NOTES_RECORDED', game.flags)
        game.talk('Averon_FieldNotes_Researcher', accept=False)
        self.assertEqual(game.flags, set())
        game.talk('Averon_FieldNotes_Researcher', accept=True)
        self.assertIn('FLAG_AVERON_NOTES_STARTED', game.flags)
        game.talk('Averon_FieldNotes_Observer')
        self.assertIn('FLAG_AVERON_NOTES_RECORDED', game.flags)

    def test_field_notes_full_bag_then_one_time_reward(self):
        game = QuestVM()
        game.talk('Averon_FieldNotes_Researcher')
        game.talk('Averon_FieldNotes_Observer')
        self.assertEqual(game.talk('Averon_FieldNotes_Researcher', capacity=False), {})
        self.assertNotIn('FLAG_AVERON_NOTES_REWARDED', game.flags)
        self.assertEqual(game.talk('Averon_FieldNotes_Researcher'), {'ITEM_GREAT_BALL': 2})
        self.assertIn('FLAG_AVERON_NOTES_REWARDED', game.flags)
        self.assertEqual(game.talk('Averon_FieldNotes_Researcher'), {})
        self.assertEqual(game.bag['ITEM_GREAT_BALL'], 2)

    def test_berry_sketch_full_bag_then_one_time_reward(self):
        game = QuestVM()
        game.talk('Averon_BerrySketch_Observer')
        self.assertNotIn('FLAG_AVERON_SKETCH_FOUND', game.flags)
        game.talk('Averon_BerrySketch_Artist')
        game.talk('Averon_BerrySketch_Observer')
        self.assertIn('FLAG_AVERON_SKETCH_FOUND', game.flags)
        game.talk('Averon_BerrySketch_Artist', capacity=False)
        self.assertNotIn('FLAG_AVERON_SKETCH_REWARDED', game.flags)
        self.assertEqual(game.talk('Averon_BerrySketch_Artist'), {'ITEM_ORAN_BERRY': 3})
        self.assertEqual(game.talk('Averon_BerrySketch_Artist'), {})
        self.assertEqual(game.bag['ITEM_ORAN_BERRY'], 3)

    def test_quest_flags_are_disjoint(self):
        game = QuestVM()
        game.talk('Averon_FieldNotes_Researcher')
        game.talk('Averon_FieldNotes_Observer')
        game.talk('Averon_FieldNotes_Researcher')
        self.assertFalse(any(f.startswith('FLAG_AVERON_SKETCH_') for f in game.flags))
        game.talk('Averon_BerrySketch_Artist')
        game.talk('Averon_BerrySketch_Observer')
        game.talk('Averon_BerrySketch_Artist')
        self.assertEqual(game.bag, {'ITEM_GREAT_BALL': 2, 'ITEM_ORAN_BERRY': 3})

    def test_source_uses_only_six_reserved_persistent_flags(self):
        self.assertEqual(set(FLAG.findall(SOURCE)), {
            'FLAG_AVERON_NOTES_STARTED', 'FLAG_AVERON_NOTES_RECORDED', 'FLAG_AVERON_NOTES_REWARDED',
            'FLAG_AVERON_SKETCH_STARTED', 'FLAG_AVERON_SKETCH_FOUND', 'FLAG_AVERON_SKETCH_REWARDED'
        })


if __name__ == '__main__':
    unittest.main()
