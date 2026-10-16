#!/usr/bin/env python3
"""Report free bytes in each save block of a built Averon ELF.

check-averon-resource-budget.py covers ROM, EWRAM and IWRAM. This covers the
flash save: SaveBlock1, SaveBlock2, SaveBlock3 and PokemonStorage. Sizes come
from the ELF's symbol table; limits come from the sector constants in
include/save.h, the same ones save.c's STATIC_ASSERTs use. The report is
informational; it never assumes future Sinnoh data fits.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

DEFINE = re.compile(r"^\s*#define\s+(\w+)\s+(\d+)\b", re.M)
ENGINE = Path(__file__).resolve().parents[1] / "engine"


def parse_defines(text):
    return {name: int(value) for name, value in DEFINE.findall(text)}


def limits(save_h, load_save_h):
    """Each block's symbol, its byte limit and the ASLR padding in the symbol."""
    d = parse_defines(save_h)
    pad = parse_defines(load_save_h)["SAVEBLOCK_MOVE_RANGE"]
    sector = d["SECTOR_DATA_SIZE"]

    def sectors(start, end):
        return sector * (d[end] - d[start] + 1)

    return {
        "SaveBlock1": ("gSaveblock1", sectors("SECTOR_ID_SAVEBLOCK1_START", "SECTOR_ID_SAVEBLOCK1_END"), pad),
        "SaveBlock2": ("gSaveblock2", sector, pad),
        "SaveBlock3": ("gSaveblock3", d["SAVE_BLOCK_3_CHUNK_SIZE"] * d["NUM_SECTORS_PER_SLOT"], 0),
        "PokemonStorage": ("gPokemonStorage", sectors("SECTOR_ID_PKMN_STORAGE_START", "SECTOR_ID_PKMN_STORAGE_END"), pad),
    }


def parse_symbol_sizes(nm_text):
    """Sizes from `nm -S` lines: address size type name."""
    sizes = {}
    for line in nm_text.splitlines():
        fields = line.split()
        if len(fields) == 4:
            sizes[fields[3]] = int(fields[1], 16)
    return sizes


def report(sizes, block_limits):
    result = {}
    for block, (symbol, limit, pad) in block_limits.items():
        if symbol not in sizes:
            raise ValueError(f"Missing save symbol {symbol}")
        used = sizes[symbol] - pad
        if used <= 0 or used > limit:
            raise ValueError(f"Out-of-bounds {block}: {used}/{limit}")
        result[block] = {"used_bytes": used, "limit_bytes": limit, "free_bytes": limit - used}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--elf", type=Path, default=ENGINE / "pokeemerald.elf")
    parser.add_argument("--engine", type=Path, default=ENGINE)
    parser.add_argument("--nm", default="arm-none-eabi-nm")
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()

    block_limits = limits((args.engine / "include/save.h").read_text(),
                          (args.engine / "include/load_save.h").read_text())
    nm = subprocess.run([args.nm, "-S", str(args.elf)], capture_output=True, text=True, check=True)
    result = report(parse_symbol_sizes(nm.stdout), block_limits)
    for block, values in result.items():
        print(f"{block}: {values['used_bytes']:,} B of {values['limit_bytes']:,} (free {values['free_bytes']:,} B)")
    if args.json:
        args.json.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
