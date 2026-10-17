"""Negative fixtures for linked occupancy and forecast accounting."""
import struct
import unittest
import codex_rom_capacity as c


def fixture(end=c.ROM_BASE+100):
    z = bytes([0])
    names = z.join([b'', b'.shstrtab', b'.strtab', b'.symtab', b'.text', b''])
    strings = z.join([b'', b'__rom_end', b'sample', b'alias', b''])
    symbols = bytes(16)
    symbols += struct.pack('<IIIBBH', 1, end, 0, 16, 0, 65521)
    symbols += struct.pack('<IIIBBH', 11, c.ROM_BASE, 4, 17, 0, 4)
    symbols += struct.pack('<IIIBBH', 18, c.ROM_BASE, 4, 17, 0, 4)
    blobs = [b'', names, strings, symbols, b'ABCD']
    offsets, cursor = [], 52
    for blob in blobs:
        offsets.append(cursor)
        cursor += len(blob)
    ident = bytes([127])+b'ELF'+bytes([1, 1, 1])+bytes(9)
    header = struct.pack('<16sHHIIIIIHHHHHH', ident, 2, 40, 1, 0, 0, cursor, 0, 52, 0, 0, 40, 5, 1)
    sections = bytes(40)
    for i, name in enumerate((1, 11, 19, 27), 1):
        sections += struct.pack('<IIIIIIIIII', name, 2 if i == 3 else 1,
                                2 if i == 4 else 0, c.ROM_BASE if i == 4 else 0,
                                offsets[i], len(blobs[i]), 2 if i == 3 else 0,
                                0, 1, 16 if i == 3 else 0)
    return header+b''.join(blobs)+sections


class Budget(unittest.TestCase):
    def test_linked_not_padded(self):
        self.assertEqual(c.Elf(fixture()).occupancy(), {'linked_used_bytes': 100, 'free_bytes': c.ROM_LIMIT-100})

    def test_boundary_and_overflow(self):
        self.assertEqual(c.Elf(fixture(c.ROM_BASE+c.ROM_LIMIT)).occupancy()['free_bytes'], 0)
        for end in (c.ROM_BASE, c.ROM_BASE-1, c.ROM_BASE+c.ROM_LIMIT+1):
            with self.assertRaises(ValueError):
                c.Elf(fixture(end)).occupancy()

    def test_alias_and_bounds(self):
        elf = c.Elf(fixture())
        self.assertEqual(elf.at_symbol('sample', 4), elf.at_symbol('alias', 4))
        with self.assertRaises(ValueError):
            elf.at_symbol('sample', 5)

    def test_malformed_elf(self):
        for data in (b'', b'not elf', fixture()[:-1]):
            with self.assertRaises(ValueError):
                c.Elf(data)

    def test_input_not_output_or_discarded(self):
        text = chr(10).join(['.rodata 0x08000000 0x300', ' .rodata 0x08000000 0x100 data/maps.o', ' .rodata 0x00000000 0x200 data/unused.o'])
        self.assertEqual(c.input_sections(text), [{'object': 'data/maps.o', 'bytes': 256}])

    def test_forecast_charges_increment_once(self):
        result = c.forecast([{'count': 2, 'width': 20, 'height': 20}], {'species': 0, 'events': 400, 'reserve': 1000}, 10000)
        self.assertEqual(result, {'layout_bytes': 1616, 'growth_including_reserve_bytes': 3016, 'headroom_after_reserve_bytes': 6984})

    def test_preserve_deficit(self):
        self.assertEqual(c.forecast([], {'assets': 200}, 100)['headroom_after_reserve_bytes'], -100)

    def test_reject_invalid_scenario(self):
        for row in ({'count': 1, 'width': 100, 'height': 76}, {'count': -1, 'width': 20, 'height': 20}):
            with self.assertRaises(ValueError):
                c.forecast([row], {}, 0)
        with self.assertRaises(ValueError):
            c.forecast([], {'reserve': -1}, 0)


if __name__ == '__main__':
    unittest.main()
