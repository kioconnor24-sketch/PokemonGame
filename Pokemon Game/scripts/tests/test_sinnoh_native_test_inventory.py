"""Temporary ELF fixtures: inventory is not an execution/expected-failure gate."""
import importlib.util
from pathlib import Path
import struct
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'list-averon-native-tests.py'
spec = importlib.util.spec_from_file_location('native_identity_inventory', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
BASE = 0x08000000


def fixture(names=('Averon one', 'Other test', 'Averon two')):
    payload = bytearray(); pointers = []
    for i, name in enumerate(names):
        name_at = BASE + len(payload); payload += name.encode() + b'\0'
        file_at = BASE + len(payload); payload += f'test/source{i}.c'.encode() + b'\0'
        pointers.append((name_at, file_at))
    while len(payload) % 4:
        payload.append(0)
    start = BASE + len(payload)
    for i, (name_at, file_at) in enumerate(pointers):
        payload += struct.pack('<IIIIH2x', name_at, file_at, 0, 0, 100 + i)
    stop = BASE + len(payload)
    strings = b'\0__start_tests\0__stop_tests\0'
    symbols = bytes(16) + struct.pack('<IIIBBH', 1, start, 0, 0, 0, 1) + struct.pack('<IIIBBH', 15, stop, 0, 0, 0, 1)
    blob = bytearray(52); data_at = len(blob); blob += payload
    strings_at = len(blob); blob += strings
    symbols_at = len(blob); blob += symbols
    table_at = len(blob)
    for row in [(0,) * 10, (0, 1, 0, BASE, data_at, len(payload), 0, 0, 4, 0),
                (0, 3, 0, 0, strings_at, len(strings), 0, 0, 1, 0),
                (0, 2, 0, 0, symbols_at, len(symbols), 2, 0, 4, 16)]:
        blob += struct.pack('<10I', *row)
    ident = b'\x7fELF\x01\x01\x01' + bytes(9)
    struct.pack_into('<16sHHIIIIIHHHHHH', blob, 0, ident, 2, 40, 1, BASE, 0, table_at, 0, 52, 0, 0, 40, 4, 0)
    return blob, dict(table=table_at, symbols=symbols_at, records=data_at + start - BASE)


class NativeInventoryTests(unittest.TestCase):
    def test_compiled_prefix_names_filenames_lines_and_hash(self):
        blob, _ = fixture(); result = m.inventory(blob)
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['tests'], [dict(name='Averon one', filename='test/source0.c', line=100),
                                          dict(name='Averon two', filename='test/source2.c', line=102)])
        self.assertIn('no execution', result['scope'])
        self.assertEqual(len(result['elf_sha256']), 64)

    def test_explicit_prefix_and_no_matches(self):
        blob, _ = fixture(); self.assertEqual(m.inventory(blob, 'Other')['count'], 1)
        with self.assertRaisesRegex(ValueError, 'no compiled tests'):
            m.inventory(blob, 'Missing')

    def test_truncated_and_wrong_class_machine_endian_fail(self):
        blob, _ = fixture()
        for length in (0, 16, 51, len(blob) - 1):
            with self.subTest(length=length), self.assertRaises(ValueError):
                m.inventory(blob[:length])
        for offset, value in [(4, 2), (5, 2), (18, 3)]:
            changed = bytearray(blob); changed[offset] = value
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                m.inventory(changed)

    def test_missing_and_duplicate_boundary_symbols_fail(self):
        blob, offsets = fixture(); changed = bytearray(blob)
        struct.pack_into('<I', changed, offsets['symbols'] + 16, 0)
        with self.assertRaisesRegex(ValueError, 'missing compiled'):
            m.inventory(changed)
        changed = bytearray(blob); struct.pack_into('<I', changed, offsets['symbols'] + 32, 1)
        with self.assertRaisesRegex(ValueError, 'duplicate test boundary'):
            m.inventory(changed)

    def test_unknown_descriptor_stride_and_span_fail(self):
        blob, offsets = fixture(); pointer_at = offsets['symbols'] + 36
        stop = struct.unpack_from('<I', blob, pointer_at)[0]
        for value in (BASE, stop - 1, stop + 20):
            changed = bytearray(blob); struct.pack_into('<I', changed, pointer_at, value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                m.inventory(changed)

    def test_bad_symbol_links_and_truncated_regions_fail(self):
        blob, offsets = fixture()
        for relative, value in [(24, 90), (16, len(blob)), (36, 8)]:
            changed = bytearray(blob); struct.pack_into('<I', changed, offsets['table'] + 3 * 40 + relative, value)
            with self.subTest(relative=relative), self.assertRaises(ValueError):
                m.inventory(changed)

    def test_unmapped_name_and_filename_fail(self):
        blob, offsets = fixture()
        for field in (0, 4):
            changed = bytearray(blob); struct.pack_into('<I', changed, offsets['records'] + field, 0xFFFFFFFF)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'unmapped'):
                m.inventory(changed)

    def test_unterminated_symbol_name_is_rejected(self):
        blob, offsets = fixture()
        string_row = offsets['table'] + 2 * 40
        start, size = struct.unpack_from('<II', blob, string_row + 16)
        changed = bytearray(blob); changed[start + size - 1] = 65
        with self.assertRaisesRegex(ValueError, 'unterminated'):
            m.inventory(changed)

    def test_overlapping_file_backed_test_addresses_are_rejected(self):
        blob, offsets = fixture(); changed = bytearray(blob)
        changed[offsets['table']:offsets['table'] + 40] = blob[offsets['table'] + 40:offsets['table'] + 80]
        with self.assertRaisesRegex(ValueError, 'ambiguous test pointer'):
            m.inventory(changed)

    def test_duplicate_names_keep_both_source_identities(self):
        blob, _ = fixture(('Averon same', 'Averon same'))
        result = m.inventory(blob)
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['ambiguous_log_names'], ['Averon same'])
        self.assertNotEqual(result['tests'][0]['filename'], result['tests'][1]['filename'])


if __name__ == '__main__':
    unittest.main()
