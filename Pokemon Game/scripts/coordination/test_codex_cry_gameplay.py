import struct
import unittest
from codex_cry_gameplay import (SECTOR_SIGNATURE, SECTOR_SIZE, chunk_sizes, flash_slots,
                                flash_verdict, lto_aliases, restored_problems,
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
                self.assertTrue(flash_verdict(flash_slots(image(good_slot(7)), SIZES), slots))

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

    def test_any_lost_field_fails(self):
        for key, value in (('party', []), ('x', 4), ('flags', {'FLAG_AVERON_STARTER': False}),
                           ('money', 0), ('map', 'MAP_ALDERFIELD'), ('cb2', 'CB2_InitTitleScreen')):
            with self.subTest(key):
                self.assertTrue(restored_problems(self.SAVED, dict(self.SAVED, **{key: value})))


if __name__ == '__main__':
    unittest.main()
