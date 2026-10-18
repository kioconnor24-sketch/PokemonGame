from pathlib import Path
import shutil
import struct
import subprocess
import unittest
import unittest.mock
from codex_cry_gameplay import (use_source_function_names, SECTOR_SIGNATURE, SECTOR_SIZE, chunk_sizes, flash_slots,
                                flash_verdict, lto_aliases, restored_problems, rom_name,
                                save_dialog_verdict, sector_checksum)

SIZES = chunk_sizes(3800, 15000, 33744)


def sector(sid, counter, data=b'', bad_sum=False, signature=SECTOR_SIGNATURE):
    raw = bytearray(SECTOR_SIZE)
    raw[:len(data)] = data
    check = sector_checksum(raw, SIZES[sid]) ^ (1 if bad_sum else 0)
    struct.pack_into('<HHII', raw, SECTOR_SIZE - 12, sid, check, signature, counter)
    return bytes(raw)


def image(slot0, slot1=None):
    empty = bytes([0xFF])*SECTOR_SIZE
    return b''.join(slot0) + b''.join(slot1 or [empty]*14)


def good_slot(counter, rotate=0):
    ids = [(i + rotate) % 14 for i in range(14)]
    return [sector(sid, counter, bytes([sid + 1])*64) for sid in ids]


class Symbols(unittest.TestCase):
    def test_exact_elf_alias_only_and_no_input_mutation(self):
        original = {'sLockFieldControls.lto_priv.0': 123, 'unrelated': 456}
        result = lto_aliases(original)
        self.assertEqual(result['sLockFieldControls'], 123)
        self.assertNotIn('sLockFieldControls', original)

    def test_ambiguous_static_names_fail_closed(self):
        result = lto_aliases({'same.lto_priv.0': 1, 'same.lto_priv.1': 2})
        self.assertNotIn('same', result)

    def test_preserve_real_symbol_and_ignore_other_suffixes(self):
        original = {'same': 3, 'same.lto_priv.0': 1, 'other.constprop.0': 5}
        result = lto_aliases(original)
        self.assertEqual(result['same'], 3)
        self.assertNotIn('other', result)



class FunctionNames(unittest.TestCase):
    def test_lto_statics_report_their_source_names(self):
        class Observed:
            by_addr = {0x0806DFD4: 'HandleInputChooseAction', 0x08069184: 'HandleInputChooseAction.lto_priv.0',
                       0x08069598: 'HandleInputChooseAction.lto_priv.1', 0x08001000: 'CB2_MainMenu.lto_priv.0',
                       0x08002000: 'Task_Foo.constprop.0.isra.0', 0x08003000: 'CB2_Overworld'}
        observed = Observed()
        use_source_function_names(observed)
        self.assertEqual(observed.by_addr[0x08069598], 'HandleInputChooseAction')
        self.assertEqual(observed.by_addr[0x08001000], 'CB2_MainMenu')
        self.assertEqual(observed.by_addr[0x08002000], 'Task_Foo')
        self.assertEqual(observed.by_addr[0x08003000], 'CB2_Overworld')
        self.assertEqual(len(observed.by_addr), 6)  # addresses are kept, only names change


class Builds(unittest.TestCase):
    def test_rom_names_follow_the_makefile_suffixes(self):
        self.assertEqual(rom_name('off', 'release'), 'pokeemerald-cries-off-release.gba')
        self.assertEqual(rom_name('on', 'release'), 'pokeemerald-cries-on-release.gba')
        self.assertEqual(rom_name('off', 'normal'), 'pokeemerald-cries-off.gba')


class MakefileProfiles(unittest.TestCase):
    @unittest.skipUnless(shutil.which('make'), 'make not installed')
    def test_cries_value_is_stripped_then_validated(self):
        """A padded CRIES must build the named profile; anything else must fail."""
        engine = Path(__file__).resolve().parents[2]/'engine'

        def probe(value):
            return subprocess.run(['make', '--no-print-directory', 'SETUP_PREREQS=0', 'NODEP=1', 'RELEASE=1',
                                   f'CRIES={value}', '--eval', 'print-vars: ; @echo $(FILE_NAME) $(CRY_CPPFLAGS)',
                                   'print-vars'], cwd=engine, capture_output=True, text=True)
        for value, words in (('on ', ['pokeemerald-cries-on-release', '-DP_CRIES_ENABLED=TRUE']),
                             (' off', ['pokeemerald-cries-off-release', '-DP_CRIES_ENABLED=FALSE']),
                             ('default ', ['pokeemerald-release'])):
            with self.subTest(value=value):
                result = probe(value)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.split(), words)
        for value in ('on off', 'bogus', '', 'o%', '%', '%n', '%f'):  # % would act as a filter pattern
            with self.subTest(value=value):
                self.assertNotEqual(probe(value).returncode, 0)


class Flash(unittest.TestCase):
    def test_chunk_sizes_match_save_c_layout(self):
        self.assertEqual(SIZES[0], 3800)
        self.assertEqual(SIZES[1:5], [3968, 3968, 3968, 15000 - 3*3968])
        self.assertEqual(SIZES[5:14], [3968]*8 + [33744 - 8*3968])

    def test_complete_rotated_slot_is_valid_and_empty_slot_is_empty(self):
        slots = flash_slots(image(good_slot(7, rotate=5)), SIZES)
        self.assertEqual(slots[0], dict(status='valid', problems=[], counter=7))
        self.assertEqual(slots[1], dict(status='empty'))

    def test_new_save_must_be_valid_and_newer(self):
        before = flash_slots(image(good_slot(7)), SIZES)
        after = flash_slots(image(good_slot(7), good_slot(8)), SIZES)
        self.assertEqual(flash_verdict(before, after), [])
        self.assertTrue(flash_verdict(before, before))  # nothing new written
        self.assertEqual(flash_verdict(flash_slots(b'', SIZES), after), [])

    def test_each_save_must_advance_the_counter(self):
        before = flash_slots(image(good_slot(7)), SIZES)
        one = flash_slots(image(good_slot(7), good_slot(8)), SIZES)
        two = flash_slots(image(good_slot(9), good_slot(8)), SIZES)
        self.assertEqual(flash_verdict(before, two, saves=2), [])
        self.assertIn('not 2 newer', flash_verdict(before, one, saves=2)[0])

    def test_corrupt_slots_are_refused(self):
        bad_sum = good_slot(8)
        bad_sum[3] = sector(3, 8, b'x', bad_sum=True)
        mixed = good_slot(8)
        mixed[0] = sector(0, 9, b'\x01'*64)
        missing = good_slot(8)
        missing[13] = bytes([0xFF])*SECTOR_SIZE
        duplicate = good_slot(8)
        duplicate[13] = duplicate[12]
        for name, slot in (('checksum', bad_sum), ('counter', mixed),
                           ('missing', missing), ('twice', duplicate)):
            with self.subTest(name):
                slots = flash_slots(image(good_slot(7), slot), SIZES)
                self.assertEqual(slots[1]['status'], 'invalid')
                # Slot 0 is newer than before, so only the invalid slot can be reported.
                newer = flash_slots(image(good_slot(9), slot), SIZES)
                before = flash_slots(image(good_slot(7)), SIZES)
                problems = flash_verdict(before, newer)
                self.assertTrue(problems)
                self.assertTrue(all(p.startswith('slot 1:') for p in problems), problems)

    def test_truncated_image_is_not_valid(self):
        slots = flash_slots(image(good_slot(7))[:5*SECTOR_SIZE], SIZES)
        self.assertEqual(slots[0]['status'], 'invalid')
        self.assertIn('no valid save slot', flash_verdict([], slots))


class Dialog(unittest.TestCase):
    def test_success_needs_the_success_callback(self):
        self.assertEqual(save_dialog_verdict(['SaveYesNoCallback', 'SaveDoSaveCallback',
                                              'SaveSuccessCallback.lto_priv.0']), [])
        self.assertEqual(save_dialog_verdict(['SaveReturnSuccessCallback']), [])

    def test_error_or_missing_success_fails(self):
        self.assertTrue(save_dialog_verdict(['SaveDoSaveCallback', 'SaveErrorCallback']))
        self.assertTrue(save_dialog_verdict(['SaveSuccessCallback', 'SaveReturnErrorCallback.constprop.0']))
        self.assertTrue(save_dialog_verdict(['SaveYesNoCallback', '0x00000000']))
        self.assertTrue(save_dialog_verdict([]))


class Continue(unittest.TestCase):
    SAVED = dict(cb2='CB2_Overworld', map='MAP_SALTMERE', mapGroup=0, mapNum=1, x=5, y=6,
                 party=[dict(species=393, level=5)], flags={'FLAG_AVERON_STARTER': True},
                 money=3000, pokeBalls=[], berries=[], frame=100)

    def test_identical_state_passes_and_frame_is_ignored(self):
        self.assertEqual(restored_problems(self.SAVED, dict(self.SAVED, frame=9)), [])

    def test_json_round_trip_is_not_a_difference(self):
        saved = dict(self.SAVED, pokeBalls=[[1, 5]])
        self.assertEqual(restored_problems(saved, dict(saved, pokeBalls=[(1, 5)])), [])
        self.assertTrue(restored_problems(saved, dict(saved, pokeBalls=[(1, 4)])))

    def test_any_lost_field_fails(self):
        for key, value in (('party', []), ('x', 4), ('flags', {'FLAG_AVERON_STARTER': False}),
                           ('money', 0), ('map', 'MAP_ALDERFIELD'), ('cb2', 'CB2_InitTitleScreen')):
            with self.subTest(key):
                self.assertTrue(restored_problems(self.SAVED, dict(self.SAVED, **{key: value})))



class Arguments(unittest.TestCase):
    def test_reused_output_folder_is_refused(self):
        import contextlib, io, sys, tempfile
        from pathlib import Path
        import codex_cry_gameplay
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)/'out'
            out.mkdir()
            (out/'events.jsonl').write_text('{}\n')
            argv = ['codex_cry_gameplay.py', '--engine', str(Path(tmp)/'engine'), '--profile', 'off',
                    '--scratch', str(Path(tmp)/'scratch'), '--out', str(out)]
            with unittest.mock.patch.object(sys, 'argv', argv), \
                    contextlib.redirect_stderr(io.StringIO()) as err, self.assertRaises(SystemExit):
                codex_cry_gameplay.main()
            self.assertIn('new or empty directory', err.getvalue())

if __name__ == '__main__':
    unittest.main()
