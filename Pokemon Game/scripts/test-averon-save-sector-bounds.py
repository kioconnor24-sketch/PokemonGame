#!/usr/bin/env python3
"""Execute actual save.c validator/copy functions with host ASan + UBSan.

Flash and SaveBlock3 are host fixtures, not emulated hardware. Native flash
coverage lives in engine/test/averon_save_sector_bounds.c. No source is edited.
"""
import argparse
from pathlib import Path
import os
import shlex
import subprocess
import tempfile
import unittest

ENGINE = Path(__file__).resolve().parents[1] / "engine"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", type=Path, default=ENGINE / "src/save.c")
args, unittest_args = parser.parse_known_args()


def extract(source, signature):
    start = source.index(signature + "\n{")
    brace = source.index("{", start)
    depth = 0
    for end in range(brace, len(source)):
        depth += (source[end] == "{") - (source[end] == "}")
        if depth == 0:
            return source[start:end + 1]
    raise ValueError("Unterminated production function: " + signature)


PREFIX = r'''
#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
typedef uint8_t u8;
typedef uint8_t bool8;
typedef uint16_t u16;
typedef uint32_t u32;
#define TRUE 1
#define FALSE 0
#define NUM_SECTORS_PER_SLOT 14
#define NUM_SAVE_SLOTS 2
#define SECTOR_SIGNATURE 0x8012025
#define SAVE_STATUS_EMPTY 0
#define SAVE_STATUS_OK 1
#define SAVE_STATUS_CORRUPT 2
#define SAVE_STATUS_ERROR 255
#define FULL_SAVE_SLOT 0xFFFF
struct SaveSector { u8 data[3968]; u8 sb3[116]; u16 id, checksum; u32 signature, counter; };
struct SaveSectorLocation { void *data; u16 size; };
_Static_assert(sizeof(struct SaveSector) == 4096, "host flash fixture layout");
static struct SaveSector flash[28], buffer, *gReadWriteSector = &buffer;
static u32 gSaveCounter;
static u16 gLastWrittenSector;
static unsigned copied;
static bool8 ReadFlashSector(u8 sector, struct SaveSector *out) { *out = flash[sector]; return TRUE; }
static void CopyToSaveBlock3(u16 id, struct SaveSector *sector) { ++copied; }
'''

MAIN = r'''
int main(int argc, char **argv) {
    if (argc != 5) return 3;
    unsigned operation = atoi(argv[1]), badId = atoi(argv[2]), bank = atoi(argv[3]), signature = atoi(argv[4]);
    struct SaveSectorLocation *locations = calloc(NUM_SECTORS_PER_SLOT, sizeof(*locations));
    u8 destinations[NUM_SECTORS_PER_SLOT][4] = {{0}};
    if (!locations) return 4;
    for (unsigned i = 0; i < NUM_SECTORS_PER_SLOT; ++i) {
        locations[i].size = 4;
        locations[i].data = destinations[i];
        for (unsigned slot = 0; slot < 2; ++slot) {
            struct SaveSector *s = &flash[slot * NUM_SECTORS_PER_SLOT + i];
            s->id = i;
            s->signature = SECTOR_SIGNATURE;
            s->counter = slot + 1;
        }
    }
    if (operation == 3) memset(flash, 0xFF, sizeof(flash));
    else if (badId) {
        flash[bank * NUM_SECTORS_PER_SLOT].id = badId;
        flash[bank * NUM_SECTORS_PER_SLOT].signature = signature ? SECTOR_SIGNATURE : 0;
    }
    if (operation == 2) {
        // A signed invalid-ID slot and an empty other slot must be CORRUPT,
        // not silently EMPTY. Keep signatureValid before range rejection.
        for (unsigned i = 0; i < NUM_SECTORS_PER_SLOT; ++i) {
            flash[bank * NUM_SECTORS_PER_SLOT + i].id = badId;
            flash[(1 - bank) * NUM_SECTORS_PER_SLOT + i].signature = 0;
        }
    }
    gSaveCounter = bank;
    u8 status = operation == 1 || operation == 3
        ? CopySaveSlotData(FULL_SAVE_SLOT, locations) : GetSaveValidStatus(locations);
    printf("%u %u %u\n", status, gSaveCounter, copied);
    free(locations);
    return 0;
}
'''


class SaveSectorBounds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="averon-save-bounds-")
        cls.addClassCleanup(cls.tmp.cleanup)
        root = Path(cls.tmp.name)
        source = args.source.read_text()
        signatures = ["static u16 CalculateChecksum(void *data, u16 size)",
                      "static u8 CopySaveSlotData(u16 sectorId, struct SaveSectorLocation *locations)",
                      "static u8 GetSaveValidStatus(const struct SaveSectorLocation *locations)"]
        code = PREFIX + "\n".join(extract(source, signature) for signature in signatures) + MAIN
        (root / "probe.c").write_text(code)
        cls.binary = root / "probe"
        subprocess.run([*shlex.split(os.environ.get("CC", "cc")), "-g", "-O1",
                        "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                        str(root / "probe.c"), "-o", str(cls.binary)], check=True)

    def run_probe(self, operation, sector_id=0, bank=0, signature=1):
        result = subprocess.run([str(self.binary), str(operation), str(sector_id), str(bank), str(signature)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "", result.stderr)
        return tuple(map(int, result.stdout.split()))

    def test_healthy_slot_selection(self):
        self.assertEqual(self.run_probe(0), (1, 2, 0))

    def test_healthy_sector_copy(self):
        for bank in (0, 1):
            with self.subTest(bank=bank):
                self.assertEqual(self.run_probe(1, bank=bank), (1, bank, 14))

    def test_invalid_id_recovers_other_valid_slot(self):
        for bank in (0, 1):
            for sector_id in (14, 65535):
                with self.subTest(bank=bank, sector_id=sector_id):
                    self.assertEqual(self.run_probe(0, sector_id, bank), (255, 2 - bank, 0))

    def test_invalid_signature_recovers_other_valid_slot(self):
        for bank in (0, 1):
            with self.subTest(bank=bank):
                self.assertEqual(self.run_probe(0, 65535, bank, 0), (255, 2 - bank, 0))

    def test_corrupt_ids_are_not_copied(self):
        for bank in (0, 1):
            for sector_id in (14, 65535):
                with self.subTest(bank=bank, sector_id=sector_id):
                    self.assertEqual(self.run_probe(1, sector_id, bank), (1, bank, 13))

    def test_invalid_signature_copy_skips_before_lookup(self):
        for bank in (0, 1):
            with self.subTest(bank=bank):
                self.assertEqual(self.run_probe(1, 65535, bank, 0), (1, bank, 13))

    def test_signed_invalid_ids_do_not_become_empty(self):
        for bank in (0, 1):
            with self.subTest(bank=bank):
                self.assertEqual(self.run_probe(2, 14, bank), (2, 0, 0))

    def test_empty_flash_copy_never_looks_up_erased_id(self):
        self.assertEqual(self.run_probe(3), (1, 0, 0))


if __name__ == "__main__":
    unittest.main(argv=[__file__, *unittest_args], verbosity=2)
