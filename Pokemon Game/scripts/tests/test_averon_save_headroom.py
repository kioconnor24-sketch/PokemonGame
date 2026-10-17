"""Checks the save-block headroom report against fixture headers and symbols."""
import importlib.util
import unittest
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "report-averon-save-headroom.py"
spec = importlib.util.spec_from_file_location("averon_save_headroom", FILE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

SAVE_H = """#define SECTOR_DATA_SIZE 3968
#define SAVE_BLOCK_3_CHUNK_SIZE 116
#define SECTOR_ID_SAVEBLOCK2          0
#define SECTOR_ID_SAVEBLOCK1_START    1
#define SECTOR_ID_SAVEBLOCK1_END      4
#define SECTOR_ID_PKMN_STORAGE_START  5
#define SECTOR_ID_PKMN_STORAGE_END   13
#define NUM_SECTORS_PER_SLOT         14
"""
LOAD_SAVE_H = "#define SAVEBLOCK_MOVE_RANGE    128\n"
NM = """02007908 000085e0 B gPokemonStorage
0200fee8 00003d50 B gSaveblock1
02013c38 00000fac B gSaveblock2
02007398 00000044 B gSaveblock3
08000000 T Start
"""

class SaveHeadroomTests(unittest.TestCase):
    def test_limits_follow_the_sector_layout(self):
        limits = tool.limits(SAVE_H, LOAD_SAVE_H)
        self.assertEqual(limits["SaveBlock1"], ("gSaveblock1", 15872, 128))
        self.assertEqual(limits["SaveBlock2"], ("gSaveblock2", 3968, 128))
        self.assertEqual(limits["SaveBlock3"], ("gSaveblock3", 1624, 0))
        self.assertEqual(limits["PokemonStorage"], ("gPokemonStorage", 35712, 128))

    def test_report_subtracts_padding(self):
        result = tool.report(tool.parse_symbol_sizes(NM), tool.limits(SAVE_H, LOAD_SAVE_H))
        self.assertEqual(result["SaveBlock1"]["free_bytes"], 304)
        self.assertEqual(result["SaveBlock2"]["free_bytes"], 84)
        self.assertEqual(result["SaveBlock3"]["used_bytes"], 68)
        self.assertEqual(result["PokemonStorage"]["free_bytes"], 1568)

    def test_missing_or_oversized_block_fails(self):
        limits = tool.limits(SAVE_H, LOAD_SAVE_H)
        with self.assertRaisesRegex(ValueError, "Missing save symbol gSaveblock3"):
            tool.report(tool.parse_symbol_sizes(NM.replace("gSaveblock3", "other")), limits)
        with self.assertRaisesRegex(ValueError, "Out-of-bounds SaveBlock2"):
            tool.report(tool.parse_symbol_sizes(NM.replace("00000fac", "00001010")), limits)
        with self.assertRaisesRegex(ValueError, "Out-of-bounds SaveBlock3"):
            tool.report(tool.parse_symbol_sizes(NM.replace("00000044", "00000000")), limits)

    def test_a_block_exactly_at_its_limit_has_zero_free(self):
        # SaveBlock2 limit 3968 + 128 padding = 0x1000; one byte more is over.
        limits = tool.limits(SAVE_H, LOAD_SAVE_H)
        at_limit = NM.replace("00000fac", "%08x" % (3968 + 128))
        self.assertEqual(tool.report(tool.parse_symbol_sizes(at_limit), limits)["SaveBlock2"]["free_bytes"], 0)
        over = NM.replace("00000fac", "%08x" % (3968 + 128 + 1))
        with self.assertRaisesRegex(ValueError, "Out-of-bounds SaveBlock2: 3969/3968"):
            tool.report(tool.parse_symbol_sizes(over), limits)

    def test_ambiguous_or_malformed_symbols_fail(self):
        limits = tool.limits(SAVE_H, LOAD_SAVE_H)
        duplicate = NM + "02020000 00000fac b gSaveblock2\n"
        with self.assertRaisesRegex(ValueError, "Ambiguous save symbol gSaveblock2: 2"):
            tool.report(tool.parse_symbol_sizes(duplicate), limits)
        with self.assertRaisesRegex(ValueError, "Malformed nm line"):
            tool.parse_symbol_sizes("0200fee8 zz B gSaveblock1\n")

    def test_missing_or_invalid_header_constants_fail(self):
        with self.assertRaisesRegex(ValueError, "Missing define SAVEBLOCK_MOVE_RANGE"):
            tool.limits(SAVE_H, "")
        with self.assertRaisesRegex(ValueError, "Missing define SECTOR_ID_PKMN_STORAGE_END"):
            tool.limits(SAVE_H.replace("SECTOR_ID_PKMN_STORAGE_END", "UNRELATED"), LOAD_SAVE_H)
        with self.assertRaisesRegex(ValueError, "Non-positive limit for SaveBlock1"):
            tool.limits(SAVE_H.replace("SAVEBLOCK1_END      4", "SAVEBLOCK1_END      0"), LOAD_SAVE_H)

if __name__ == "__main__":
    unittest.main()
