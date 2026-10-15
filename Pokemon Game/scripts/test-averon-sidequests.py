"""Transactional/idempotent sidequest installer fixtures (no compiler needed)."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('build-averon-sidequests.py')
spec = importlib.util.spec_from_file_location('averon_quests', SCRIPT)
quest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(quest)


class SideQuestInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.engine = Path(self.temp.name)
        self.layout = self.engine / 'data/layouts/Test/map.bin'
        self.layout.parent.mkdir(parents=True)
        cells = [0x3001] * (60 * 40)
        cells[27 * 60 + 12] = 0x05D4
        self.layout.write_bytes(struct.pack('<' + 'H' * len(cells), *cells))
        self.put_json('data/layouts/layouts.json', {'layouts': [
            {'id': f'LAYOUT_{name.upper()}', 'width': 60, 'height': 40,
             'blockdata_filepath': 'data/layouts/Test/map.bin'}
            for name, *_ in quest.ACTORS]})
        for name, *_ in quest.ACTORS:
            self.put_json(f'data/maps/{name}/map.json', {
                'id': f'MAP_{name.upper()}', 'layout': f'LAYOUT_{name.upper()}',
                'object_events': [{'x': 5, 'y': 5, 'script': 'Existing',
                                   'graphics_id': 'OBJ_EVENT_GFX_BOY_1'}],
                'warp_events': [], 'coord_events': [], 'bg_events': [],
            })
        self.flags = self.engine / 'include/constants/flags.h'
        self.flags.parent.mkdir(parents=True)
        self.flags.write_text('\n'.join(f'#define {old} 0x{0x2a + i:03X} // Unused Flag'
                                         for i, old in enumerate(quest.FLAG_SLOTS)) + '\n')
        self.events = self.engine / 'data/event_scripts.s'
        self.events.parent.mkdir(parents=True, exist_ok=True)
        self.events.write_text('\t.include "data/maps/Existing/scripts.inc"\n')
        self.script = Path(__file__).with_name('averon-optional-sidequests.inc')

    def put_json(self, rel, data):
        path = self.engine / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))

    def test_install_adds_four_npcs_unique_scripts_and_six_flags(self):
        self.assertEqual(quest.apply(self.engine, self.script), 4)
        for name, x, y, graphics, script in quest.ACTORS:
            data = quest.load_json(self.engine / 'data/maps' / name / 'map.json')
            found = [o for o in data['object_events'] if o['script'] == script]
            self.assertEqual(len(found), 1)
            self.assertEqual((found[0]['x'], found[0]['y']), (x, y))
            self.assertEqual(found[0]['graphics_id'], graphics)
        flags = self.flags.read_text()
        for old, new in quest.FLAG_SLOTS.items():
            self.assertNotIn('#define ' + old + ' ', flags)
            self.assertEqual(flags.count('#define ' + new + ' '), 1)
        self.assertEqual(self.events.read_text().count(quest.INCLUDE), 1)

    def test_repeated_install_byte_identical(self):
        quest.apply(self.engine, self.script)
        paths = [self.flags, self.events, self.engine / 'data/averon_optional_sidequests.inc'] + [
            self.engine / 'data/maps' / name / 'map.json' for name, *_ in quest.ACTORS]
        saved = [path.read_bytes() for path in paths]
        quest.apply(self.engine, self.script)
        self.assertEqual(saved, [path.read_bytes() for path in paths])

    def test_flag_conflict_leaves_maps_untouched(self):
        self.flags.write_text(self.flags.read_text().replace('FLAG_UNUSED_0x02A', 'FLAG_OTHER_OWNER'))
        before = (self.engine / 'data/maps/Alderfield/map.json').read_bytes()
        with self.assertRaisesRegex(ValueError, 'Reserved slot unavailable'):
            quest.apply(self.engine, self.script)
        self.assertEqual((self.engine / 'data/maps/Alderfield/map.json').read_bytes(), before)
        self.assertNotIn(quest.INCLUDE, self.events.read_text())

    def test_blocked_tile_rejected_without_partial_writes(self):
        cells = [0x3001] * (60 * 40)
        cells[16 * 60 + 12] = 0x3401
        self.layout.write_bytes(struct.pack('<' + 'H' * len(cells), *cells))
        with self.assertRaisesRegex(ValueError, 'blocked tile'):
            quest.apply(self.engine, self.script)
        self.assertNotIn('FLAG_AVERON_NOTES_STARTED', self.flags.read_text())

    def test_npc_overlap_rejected(self):
        data = quest.load_json(self.engine / 'data/maps/Alderfield/map.json')
        data['object_events'][0]['x'], data['object_events'][0]['y'] = (12, 16)
        self.put_json('data/maps/Alderfield/map.json', data)
        with self.assertRaisesRegex(ValueError, 'collides with object_events'):
            quest.apply(self.engine, self.script)

    def test_missing_target_map_rejected(self):
        (self.engine / 'data/maps/Alderfield/map.json').unlink()
        with self.assertRaises(FileNotFoundError):
            quest.apply(self.engine, self.script)

    def test_tree_requires_unchanged_landmark_and_walkable_approach(self):
        cells = list(struct.unpack('<2400H', self.layout.read_bytes()))
        cells[27 * 60 + 11] = 0x3401
        self.layout.write_bytes(struct.pack('<2400H', *cells))
        with self.assertRaisesRegex(ValueError, 'west approach changed'):
            quest.apply(self.engine, self.script)
        self.assertNotIn(quest.INCLUDE, self.events.read_text())

    def test_tree_event_is_installed_once(self):
        quest.apply(self.engine, self.script)
        quest.apply(self.engine, self.script)
        meadow = quest.load_json(self.engine / 'data/maps/CoastalMeadow/map.json')
        self.assertEqual(meadow['bg_events'], [quest.SKETCH_TREE])

    def test_existing_flag_cannot_silently_move_to_another_save_bit(self):
        quest.apply(self.engine, self.script)
        content = self.flags.read_text().replace('FLAG_AVERON_NOTES_STARTED 0x02A',
                                                'FLAG_AVERON_NOTES_STARTED 0x080')
        self.flags.write_text(content)
        with self.assertRaisesRegex(ValueError, 'saved slot'):
            quest.apply(self.engine, self.script)

    def test_reward_flags_set_only_after_success_and_have_retry(self):
        content = self.script.read_text()
        for command, reward_flag, full_label in [
            ('additem ITEM_GREAT_BALL, 2', 'FLAG_AVERON_NOTES_REWARDED', 'Averon_NotesBagFull'),
            ('additem ITEM_ORAN_BERRY, 3', 'FLAG_AVERON_SKETCH_REWARDED', 'Averon_SketchBagFull'),
        ]:
            segment = content.split(command, 1)[1].split('return', 1)[0]
            self.assertLess(segment.index('goto_if_eq VAR_RESULT, FALSE, Averon_EventRewardReturn'),
                            segment.index('setflag ' + reward_flag))
            self.assertIn(full_label + ':', content)
            self.assertIn('goto_if_set ' + reward_flag, content)


if __name__ == '__main__':
    unittest.main()
