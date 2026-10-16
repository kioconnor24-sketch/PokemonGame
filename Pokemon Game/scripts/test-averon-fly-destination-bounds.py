#!/usr/bin/env python3
"""Execute the real Fly table/functions under host ASan/UBSan.

Requires generated engine headers (run make first), Python 3 and a host C
compiler. Example: python3 scripts/test-averon-fly-destination-bounds.py
--include-dir engine/include --mutations. The only substitutes are the small
RegionMap/save/flag inputs and observable warp callbacks; no engine is edited.
--source permits an unpatched source file for failed-before evidence.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile


def extract(source, signature):
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for end in range(brace, len(source)):
        depth += (source[end] == "{") - (source[end] == "}")
        if depth == 0:
            return source[start:end + 1]
    raise ValueError(f"Unclosed source definition: {signature}")


PREFIX = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
#include "constants/map_groups.h"
#include "constants/heal_locations.h"
#include "constants/region_map_sections.h"
#define MAP_GROUP(id) ((id) >> 8)
#define MAP_NUM(id) ((id) & 255)
#define WARP_ID_NONE -1
#define MALE 0
#define FEMALE 1
#define FLAG_LANDMARK_POKEMON_LEAGUE 1
#define ARRAY_COUNT(a) (sizeof(a) / sizeof((a)[0]))
#define CHECK(cond) do { if (!(cond)) { fprintf(stderr, "ASSERT line=%d: %s\n", __LINE__, #cond); exit(2); } } while (0)
struct RegionMap { u16 mapSecId; u8 posWithinMapSec; };
static struct { u8 playerGender; } save2, *gSaveBlock2Ptr = &save2;
static unsigned league, healCalls, warpCalls, healArg;
static int groupArg, numberArg, warpArg;
static int FlagGet(unsigned flag) { CHECK(flag == FLAG_LANDMARK_POKEMON_LEAGUE); return league; }
static void SetWarpDestinationToHealLocation(unsigned id) { ++healCalls; healArg = id; }
static void SetWarpDestinationToMapWarp(int group, int number, int warp) {
    ++warpCalls; groupArg = group; numberArg = number; warpArg = warp;
}
'''

DRIVER = r'''
static unsigned checks;
static void exercise(unsigned section, unsigned gender, unsigned flag, unsigned position) {
    struct RegionMap map = {section, position};
    save2.playerGender = gender;
    league = flag;
    healCalls = warpCalls = 0;
    healArg = 0xdead;
    groupArg = numberArg = warpArg = 12345;
    u32 expected;
    switch (section) {
    case MAPSEC_SOUTHERN_ISLAND: expected = HEAL_LOCATION_SOUTHERN_ISLAND_EXTERIOR; break;
    case MAPSEC_BATTLE_FRONTIER: expected = HEAL_LOCATION_BATTLE_FRONTIER_OUTSIDE_EAST; break;
    case MAPSEC_LITTLEROOT_TOWN:
        expected = gender == MALE ? HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F : HEAL_LOCATION_LITTLEROOT_TOWN_MAYS_HOUSE_2F; break;
    case MAPSEC_EVER_GRANDE_CITY:
        expected = flag && position == 0 ? HEAL_LOCATION_EVER_GRANDE_CITY_POKEMON_LEAGUE : HEAL_LOCATION_EVER_GRANDE_CITY; break;
    default:
        expected = section < ARRAY_COUNT(sMapHealLocations) && sMapHealLocations[section][2] != HEAL_LOCATION_NONE
            ? sMapHealLocations[section][2] : (u32)WARP_ID_NONE;
    }
    CHECK(FilterFlyDestination(&map) == expected);
    SetFlyDestination(&map);
    if (expected != (u32)WARP_ID_NONE) {
        CHECK(healCalls == 1 && warpCalls == 0 && healArg == expected);
        CHECK(groupArg == 12345 && numberArg == 12345 && warpArg == 12345);
    } else if (section < ARRAY_COUNT(sMapHealLocations)) {
        CHECK(healCalls == 0 && warpCalls == 1 && healArg == 0xdead);
        CHECK(groupArg == sMapHealLocations[section][0]);
        CHECK(numberArg == sMapHealLocations[section][1]);
        CHECK(warpArg == WARP_ID_NONE);
    } else {
        CHECK(healCalls == 0 && warpCalls == 0 && healArg == 0xdead);
        CHECK(groupArg == 12345 && numberArg == 12345 && warpArg == 12345);
    }
    CHECK(map.mapSecId == section && map.posWithinMapSec == position);
    CHECK(save2.playerGender == gender && league == flag);
    ++checks;
}
int main(int argc, char **argv) {
    CHECK(argc == 2);
    unsigned count = ARRAY_COUNT(sMapHealLocations);
    CHECK(MAPSEC_EMBER_SPA + 1 == count);
    CHECK(MAPSEC_SALTMERE >= count && MAPSEC_ALDERFIELD >= count);
    unsigned id = strtoul(argv[1], NULL, 10);
    if (id == 0) {
        for (unsigned s = 0; s < count; ++s)
            for (unsigned g = 0; g < 2; ++g)
                for (unsigned f = 0; f < 2; ++f)
                    for (unsigned p = 0; p < 2; ++p)
                        exercise(s, g, f, p);
    } else {
        unsigned sections[] = {0, MAPSEC_BATTLE_FRONTIER, MAPSEC_SOUTHERN_ISLAND,
            count - 1, count, MAPSEC_SALTMERE, MAPSEC_ALDERFIELD, 65535};
        CHECK(id < ARRAY_COUNT(sections));
        exercise(sections[id], FEMALE, 1, 0);
    }
    printf("PASS case=%u checks=%u table_rows=%u frontier=%u saltmere=%u alderfield=%u\n",
        id, checks, count, MAPSEC_BATTLE_FRONTIER, MAPSEC_SALTMERE, MAPSEC_ALDERFIELD);
    return 0;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-dir", required=True, type=Path)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1] / "engine/src/region_map.c")
    parser.add_argument("--mutations", action="store_true")
    args = parser.parse_args()
    source = args.source.read_text()
    table = extract(source, "static const u8 sMapHealLocations[][3] =") + ";"
    getter = extract(source, "u32 FilterFlyDestination(struct RegionMap* regionMap)\n{")
    setter = extract(source, "void SetFlyDestination(struct RegionMap* regionMap)\n{")
    print(f"source={args.source} sha256={hashlib.sha256(args.source.read_bytes()).hexdigest()}", flush=True)
    failures = 0
    with tempfile.TemporaryDirectory(prefix="averon-fly-bounds-") as directory:
        directory = Path(directory)

        def compile_probe(name, get, put, high_special=False):
            c_path, executable = directory / f"{name}.c", directory / name
            # Current explicit specials are all below the table bound. Relocate
            # just this symbol in a separate host fixture to exercise the
            # promised special-before-boundary contract without editing enums.
            relocation = "\n#define MAPSEC_BATTLE_FRONTIER 65534\n" if high_special else ""
            c_path.write_text(PREFIX + relocation + table + "\n" + get + "\n" + put + DRIVER)
            subprocess.run([os.environ.get("CC", "cc"), "-std=c11", "-O1", "-g", "-no-pie",
                            "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                            "-I", str(args.include_dir), str(c_path), "-o", str(executable)], check=True)
            return executable

        executable = compile_probe("actual", getter, setter)
        for case in range(8):
            run = subprocess.run([str(executable), str(case)], capture_output=True, text=True)
            print(run.stdout, end="")
            if run.returncode:
                failures += 1
                print(f"FAIL case={case} exit={run.returncode}\n{run.stderr}")
        print(f"actual source cases: {8 - failures}/8 PASS", flush=True)
        if failures:
            return 1
        high = compile_probe("synthetic-high-special", getter, setter, True)
        run = subprocess.run([str(high), "1"], capture_output=True, text=True)
        print("synthetic high-index explicit special: " + run.stdout, end="")
        if run.returncode:
            print(run.stderr)
            return 1
        if args.mutations:
            get_guard = "        if (regionMap->mapSecId >= ARRAY_COUNT(sMapHealLocations))\n            return WARP_ID_NONE;\n"
            put_guard = "else if (regionMap->mapSecId < ARRAY_COUNT(sMapHealLocations))"
            assert get_guard in getter and put_guard in setter, "Guards changed: update reviewed mutations"
            mutations = [
                ("remove-getter-guard", getter.replace(get_guard, ""), setter, 4),
                ("getter-only-still-unsafe", getter, setter.replace(put_guard, "else"), 4),
                ("getter-off-by-one", getter.replace(">= ARRAY_COUNT", "> ARRAY_COUNT"), setter, 4),
                ("setter-off-by-one", getter, setter.replace("< ARRAY_COUNT", "<= ARRAY_COUNT"), 4),
                ("early-setter-breaks-frontier", getter, setter.replace("{", "{\n    if (regionMap->mapSecId >= ARRAY_COUNT(sMapHealLocations)) return;", 1), 1),
                ("wrong-home-gender", getter.replace("playerGender == MALE", "playerGender != MALE"), setter, 0),
            ]
            killed = 0
            for name, get, put, case in mutations:
                mutant = compile_probe(name, get, put, name == "early-setter-breaks-frontier")
                run = subprocess.run([str(mutant), str(case)], capture_output=True, text=True)
                detected = run.returncode != 0 and any(marker in run.stderr for marker in
                    ("runtime error:", "ERROR: AddressSanitizer", "ASSERT line="))
                print(f"mutation {name}: {'KILLED' if detected else 'SURVIVED'} exit={run.returncode}")
                print(run.stderr.splitlines()[0] if run.stderr else run.stdout)
                killed += detected
            print(f"mutations: {killed}/{len(mutations)} KILLED")
            if killed != len(mutations):
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
