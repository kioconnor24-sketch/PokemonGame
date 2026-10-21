"""Isolated existing-art Cave adaptation; no production maps or saved IDs."""
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('oreburgh', ROOT /
    'Averon_Codex_Handoff/design/sinnoh/oreburgh-donor/build_oreburgh.py')
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


class CaveAdapterTest(unittest.TestCase):
    def setUp(self):
        self.records = b''.join(struct.pack('<8H', *([i] * 8)) for i in range(414))
        self.attrs = bytes(414 * 2)
        self.donor_records = self.records + bytes(26 * 16)
        self.donor_attrs = bytes(440 * 2)
        self.raw = struct.pack('<7H', 529 | 0x3000, *[i | 0x1400 for i in adapter.ENTRANCE])

    def adapt(self, **kw):
        args = dict(raw=self.raw, donor_records=self.donor_records,
                    donor_attrs=self.donor_attrs, records=self.records, attrs=self.attrs)
        args.update(kw)
        return adapter.adapt_cave(**args)

    def test_six_appended_records_preserve_complete_existing_prefix(self):
        result, attrs, used = self.adapt()
        self.assertEqual(result[:len(self.records)], self.records)
        self.assertEqual(attrs[:len(self.attrs)], self.attrs)
        self.assertEqual(len(result), 420 * 16)
        for mid, source in adapter.ENTRANCE.items():
            self.assertEqual(result[(mid-512)*16:(mid-511)*16],
                             self.records[(source-512)*16:(source-511)*16])
        self.assertEqual(used, [529, *adapter.ENTRANCE])

    def test_changed_existing_cave_record_is_rejected(self):
        changed = bytearray(self.donor_records)
        changed[(529-512)*16] ^= 1
        with self.assertRaisesRegex(ValueError, 'structural difference'):
            self.adapt(donor_records=bytes(changed))

    def test_existing_behavior_and_layer_changes_are_rejected(self):
        for value in (0x60, 0x1000):
            changed = bytearray(self.donor_attrs)
            struct.pack_into('<H', changed, (529-512)*2, value)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'behavior/layer'):
                self.adapt(donor_attrs=bytes(changed))

    def test_entrance_behavior_and_layer_changes_are_rejected(self):
        for mid in adapter.ENTRANCE:
            changed = bytearray(self.donor_attrs)
            struct.pack_into('<H', changed, (mid-512)*2, 0x60)
            with self.subTest(mid=mid), self.assertRaisesRegex(ValueError, 'replacement changes'):
                self.adapt(donor_attrs=bytes(changed))

    def test_unknown_or_missing_entrance_dependency_is_rejected(self):
        for cells in ([*adapter.ENTRANCE, 932], list(adapter.ENTRANCE)[:-1]):
            with self.subTest(cells=cells), self.assertRaisesRegex(ValueError, 'entrance dependency'):
                self.adapt(raw=struct.pack('<%dH' % len(cells), *cells))

    def test_primary_or_empty_geometry_is_rejected(self):
        for raw in (b'', self.raw + b'\x01\x00'):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, 'secondary-only'):
                self.adapt(raw=raw)

    def test_changed_prefix_size_and_truncated_donor_are_rejected(self):
        for kwargs in (dict(records=self.records[:-16]), dict(attrs=self.attrs[:-2]),
                       dict(raw=self.raw[:-1]), dict(donor_attrs=self.donor_attrs[:-1])):
            with self.subTest(kwargs=list(kwargs)), self.assertRaises(ValueError):
                self.adapt(**kwargs)

    def test_missing_source_entrance_record_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'absent donor'):
            self.adapt(donor_records=self.donor_records[:418*16], donor_attrs=self.donor_attrs[:418*2])


if __name__ == '__main__':
    unittest.main()
