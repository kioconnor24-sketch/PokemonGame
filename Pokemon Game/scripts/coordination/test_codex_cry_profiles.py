import copy
import unittest
import codex_cry_profiles as c


class Profiles(unittest.TestCase):
    def setUp(self):
        self.on = {'samples': {'totals': {'cries': {'count': 1}}, 'blobs': [
            {'label': 'instrument', 'category': 'instruments_other', 'bytes': 4, 'sha256': 'abc'}]},
            'song_names_sha256': 'songs', 'linked_used_bytes': 200}
        self.off = copy.deepcopy(self.on)
        self.off['samples']['totals'] = {}
        self.off['linked_used_bytes'] = 100
        self.songs = {'sound/songs/mus_title.o': '123', 'sound/songs/se_select.o': '456'}

    def test_valid_pair(self):
        result = c.compare(self.on, self.off, self.songs, self.songs)
        self.assertEqual(result['linked_saving_bytes'], 100)
        self.assertEqual(result['identical_song_objects'], 2)

    def test_swapped_or_missing_banks(self):
        for on, off in ((self.off, self.on), (self.off, self.off), (self.on, self.on)):
            with self.assertRaises(ValueError):
                c.compare(on, off, self.songs, self.songs)

    def test_reject_missing_or_changed_song(self):
        for changed in ({}, {**self.songs, 'sound/songs/se_select.o': 'wrong'}):
            with self.assertRaises(ValueError):
                c.compare(self.on, self.off, self.songs, changed)

    def test_reject_instrument_removal_or_mutation(self):
        for rows in ([], [{**self.off['samples']['blobs'][0], 'sha256': 'wrong'}]):
            changed = copy.deepcopy(self.off)
            changed['samples']['blobs'] = rows
            with self.assertRaises(ValueError):
                c.compare(self.on, changed, self.songs, self.songs)

    def test_reject_linked_song_loss_and_non_saving(self):
        for field, value in (('song_names_sha256', 'missing'), ('linked_used_bytes', 201)):
            changed = copy.deepcopy(self.off)
            changed[field] = value
            with self.assertRaises(ValueError):
                c.compare(self.on, changed, self.songs, self.songs)


if __name__ == '__main__':
    unittest.main()
