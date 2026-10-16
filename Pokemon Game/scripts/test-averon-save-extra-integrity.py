#!/usr/bin/env python3
"""Measure ARM save offsets and demonstrate existing extra-chunk checksum exclusion.

Read-only diagnostic, NOT a proposed format implementation or a flash runtime
test. Requires the configured/generated engine headers, ARM GCC/binutils and
a host C compiler. No allocations or persistent identifiers are introduced.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile


def definition(source, signature):
    start = source.index(signature + "\n{")
    depth = 0
    for end in range(source.index("{", start), len(source)):
        depth += (source[end] == "{") - (source[end] == "}")
        if depth == 0:
            return source[start:end + 1]
    raise ValueError(signature)


ARM_PROBE = r'''
#include "global.h"
#include "save.h"
#include "pokemon_storage_system.h"
const u32 measured[] __attribute__((section(".averon_layout_probe"))) = {
    sizeof(struct SaveBlock1), sizeof(struct SaveBlock2), sizeof(struct SaveBlock3),
    sizeof(struct PokemonStorage), offsetof(struct SaveBlock3, dexNavChain),
    offsetof(struct SaveBlock2, filler_90), sizeof(((struct SaveBlock2 *)0)->filler_90),
    offsetof(struct SaveSector, saveBlock3Chunk), offsetof(struct SaveSector, id),
    offsetof(struct SaveSector, checksum), offsetof(struct SaveSector, signature),
    offsetof(struct SaveSector, counter), sizeof(struct SaveSector)
};
'''

HOST_PROBE = r'''
int main(void) {
    struct SaveSector sector = {0};
    for (unsigned i = 0; i < SECTOR_DATA_SIZE; ++i) sector.data[i] = i * 37 + 11;
    unsigned lengths[] = {3884, SECTOR_DATA_SIZE};
    unsigned primaryDetected = 0, extraUndetected = 0;
    for (unsigned n = 0; n < 2; ++n) {
        unsigned length = lengths[n];
        u16 checksum = CalculateChecksum(sector.data, length);
        for (unsigned i = 0; i < length; ++i) {
            for (unsigned bit = 0; bit < 8; ++bit) {
                sector.data[i] ^= 1 << bit;
                if (CalculateChecksum(sector.data, length) == checksum) return 2;
                sector.data[i] ^= 1 << bit;
                ++primaryDetected;
            }
        }
        for (unsigned i = 0; i < SAVE_BLOCK_3_CHUNK_SIZE; ++i) {
            for (unsigned bit = 0; bit < 8; ++bit) {
                sector.saveBlock3Chunk[i] ^= 1 << bit;
                if (CalculateChecksum(sector.data, length) != checksum) return 3;
                sector.saveBlock3Chunk[i] ^= 1 << bit;
                ++extraUndetected;
            }
        }
    }
    printf("primary_single_bits_detected=%u extra_single_bits_NOT_detected=%u\n",
        primaryDetected, extraUndetected);
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True, type=Path)
    args = parser.parse_args()
    engine = args.engine.resolve()
    save = (engine / "src/save.c").read_text()
    header = (engine / "include/save.h").read_text()
    # Follow the real call sites, not just a hand-written checksum model.
    for function in ("static u8 CopySaveSlotData(u16 sectorId, struct SaveSectorLocation *locations)",
                     "static u8 GetSaveValidStatus(const struct SaveSectorLocation *locations)"):
        body = definition(save, function)
        assert "CalculateChecksum(gReadWriteSector->data, locations[" in body
        assert "saveBlock3Chunk" not in body
    copy = definition(save, "static void CopyToSaveBlock3(u32 sectorId, struct SaveSector *sector)")
    assert "sector->saveBlock3Chunk, size" in copy
    checksum = definition(save, "static u16 CalculateChecksum(void *data, u16 size)")
    sector = definition(header, "struct SaveSector") + ";"
    defines = "\n".join(re.findall(r"^#define (?:SECTOR_DATA_SIZE|SAVE_BLOCK_3_CHUNK_SIZE|SECTOR_FOOTER_SIZE|SECTOR_SIZE) .*$", header, re.M))
    names = ["save_block1_size", "save_block2_size", "save_block3_size", "storage_size",
             "dexnav_chain_offset", "candidate_anchor_offset", "candidate_anchor_bytes",
             "sector_extra_offset", "sector_id_offset", "sector_checksum_offset",
             "sector_signature_offset", "sector_counter_offset", "sector_size"]
    with tempfile.TemporaryDirectory(prefix="averon-save-extra-") as folder:
        folder = Path(folder)
        arm = folder / "layout.c"
        arm.write_text(ARM_PROBE)
        subprocess.run(["arm-none-eabi-gcc", "-c", "-O2", "-mthumb", "-march=armv4t", "-mabi=apcs-gnu",
                        "-DMODERN=1", "-DTESTING=0", "-DEMERALD", "-iquote", str(engine / "include"),
                        str(arm), "-o", str(folder / "layout.o")], check=True)
        subprocess.run(["arm-none-eabi-objcopy", "--only-section=.averon_layout_probe", "-O", "binary",
                        str(folder / "layout.o"), str(folder / "layout.bin")], check=True)
        values = struct.unpack("<" + "I" * len(names), (folder / "layout.bin").read_bytes())
        layout = dict(zip(names, values))
        assert values == (15568, 3884, 4, 34144, 0, 144, 8, 3968, 4084, 4086, 4088, 4092, 4096), layout
        print(json.dumps({"ARM_APCS_layout": layout, "source_sha256": {
            path: hashlib.sha256((engine / path).read_bytes()).hexdigest()
            for path in ("src/save.c", "include/save.h", "include/global.h")}}, indent=2), flush=True)
        host = folder / "coverage.c"
        host.write_text("#include <stdint.h>\n#include <stdio.h>\n"
                        "typedef uint8_t u8; typedef uint16_t u16; typedef uint32_t u32;\n"
                        + defines + "\n" + sector + "\n" + checksum + HOST_PROBE)
        subprocess.run([os.environ.get("CC", "cc"), "-O2", "-g", "-no-pie", "-fsanitize=address,undefined",
                        "-fno-sanitize-recover=all", str(host), "-o", str(folder / "coverage")], check=True)
        subprocess.run([str(folder / "coverage")], check=True)
    print("PASS: measured layout and checksum-exclusion diagnostic; extension remains UNIMPLEMENTED")


if __name__ == "__main__":
    main()
