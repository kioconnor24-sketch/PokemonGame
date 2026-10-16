#!/usr/bin/env python3
"""Source contract and mutation checks for the Averon two-region save.

Default mode is read-only: it checks that the region-save hooks are present
in every slot-sector writer and in slot validation, that the anchor replaced
filler_90 in place, and that the record is the last SaveBlock3 member.

With --mutations it removes one guard at a time from a scratch copy of each
source, rebuilds the native tests and requires `make check TESTS="Averon
region save"` to fail (the mutation is "killed"). Sources are restored after
every mutation, even on error. Run from the repository's "Pokemon Game"
directory or pass --engine.
"""
import argparse
import pathlib
import subprocess
import sys

MUTATIONS = [
    ("no-counter-coherence", "src/save.c",
     "== (1 << NUM_SECTORS_PER_SLOT) - 1 && !counterMixed)\n            saveSlot2Status",
     "== (1 << NUM_SECTORS_PER_SLOT) - 1)\n            saveSlot2Status"),
    ("no-region-classify", "src/save.c",
     "enum AveronRegionSlotClass slotClass = AveronRegionSave_ClassifySlot(slot, counter);",
     "enum AveronRegionSlotClass slotClass = AVERON_REGION_SLOT_CURRENT;"),
    ("no-seal", "src/save.c",
     "    if (sectorId == SECTOR_ID_SAVEBLOCK2)\n        AveronRegionSave_Seal(gSaveCounter);\n\n    // Get current save data\n    data = locations[sectorId].data;\n    size = locations[sectorId].size;\n\n    // Clear temp save sector\n",
     "\n    // Get current save data\n    data = locations[sectorId].data;\n    size = locations[sectorId].size;\n\n    // Clear temp save sector\n"),
    ("no-unsupported-refusal", "src/save.c",
     "    if (unsupported)\n    {",
     "    if (FALSE)\n    {"),
    ("no-write-block", "src/save.c",
     "    if (AveronRegionSave_IsWriteBlocked())\n    {\n        SetDamagedSectorBits(ENABLE, sector);\n        return SAVE_STATUS_ERROR;\n    }\n    // Averon: stamp the region anchor and record with this write's counter\n    if (sectorId == SECTOR_ID_SAVEBLOCK2)\n        AveronRegionSave_Seal(gSaveCounter);\n\n    // Get current save data\n    data = locations[sectorId].data;\n    size = locations[sectorId].size;\n\n    // Clear temp save sector\n",
     "    if (sectorId == SECTOR_ID_SAVEBLOCK2)\n        AveronRegionSave_Seal(gSaveCounter);\n\n    // Get current save data\n    data = locations[sectorId].data;\n    size = locations[sectorId].size;\n\n    // Clear temp save sector\n"),
    ("no-crc-check", "src/averon_region_save.c",
     "     || ReadU32(&record[REC_CRC]) != AveronRegionSave_RecordCrc(record)\n", ""),
    ("no-counter-binding", "src/averon_region_save.c",
     "     || ReadU32(&record[REC_COUNTER]) != sectorCounter\n", ""),
    ("no-trainer-binding", "src/averon_region_save.c",
     "     || memcmp(&record[REC_TRAINER_ID], trainerId, sizeof(trainerId)) != 0\n", ""),
    ("no-badge-mirror", "src/averon_region_save.c",
     "|| averonMask != record[REC_AVERON_MASK])", ")"),
    ("no-region-range", "src/averon_region_save.c",
     "     || !IsValidRegion(record[REC_ACTIVE])\n", ""),
    ("no-warp-validation", "src/averon_region_save.c",
     "     || !IsEncodedWarpValid(&record[REC_RETURN])\n", ""),
    ("no-reserved-check", "src/averon_region_save.c",
     "     || !IsZero(&record[REC_RESERVED], AVERON_REGION_RECORD_SIZE - REC_RESERVED)\n", ""),
    ("record-missing-is-legacy", "src/averon_region_save.c",
     "    if (!IsRecordInitialized(record)\n     ||",
     "    if (!IsRecordInitialized(record))\n        return AVERON_REGION_SLOT_LEGACY;\n    if ("),
    ("anchor-garbage-is-legacy", "src/averon_region_save.c",
     "     || format == 0)\n        return AVERON_REGION_SLOT_CORRUPT;",
     "     || format == 0)\n        return AVERON_REGION_SLOT_LEGACY;"),
    ("legacy-keeps-tail", "src/averon_region_save.c",
     "        // Legacy save: derive the defaults in RAM. Flash is untouched until\n        // the player's next ordinary save writes the anchor and record.\n        InitRecordDefaults();",
     "        // mutated"),
]

CONTRACT = [
    ("include/global.h", "/*0x90*/ u8 averonRegionAnchor[0x8];", 1),
    ("include/global.h", "u8 filler_90[", 0),
    ("include/global.h", "ALIGNED(4) u8 averonRegionRecord[64];\n}; /* max size 1624 bytes */", 1),
    ("src/save.c", "AveronRegionSave_Seal(gSaveCounter);", 2),
    ("src/save.c", "if (AveronRegionSave_IsWriteBlocked())", 2),
    ("src/save.c", "CheckRegionSlot(0, saveSlot1Counter, &unsupported)", 1),
    ("src/save.c", "CheckRegionSlot(1, saveSlot2Counter, &unsupported)", 1),
    ("src/save.c", "AveronRegionSave_BeginLoad();", 1),
    ("src/save.c", "AveronRegionSave_FinishLoad(status);", 1),
    ("src/new_game.c", "    ClearSav3();\n    AveronRegionSave_InitNewGame();", 1),
]


def check_contract(engine):
    problems = 0
    for rel, needle, expected in CONTRACT:
        count = (engine / rel).read_text().count(needle)
        if count != expected:
            print(f"CONTRACT FAIL {rel}: {needle!r} found {count}, expected {expected}")
            problems += 1
    print(f"contract: {len(CONTRACT) - problems}/{len(CONTRACT)} OK")
    return problems


def run_tests(engine, jobs):
    cmd = ["make", f"-j{jobs}", "-O", "check", "TESTS=Averon region save"]
    try:
        result = subprocess.run(cmd, cwd=engine, capture_output=True, text=True, timeout=2400)
    except subprocess.TimeoutExpired:
        return False, "timeout"
    finally:
        subprocess.run(["pkill", "-x", "mgba-rom-test"], capture_output=True)
    return result.returncode == 0, result.stdout[-400:]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--engine", default="engine", type=pathlib.Path)
    parser.add_argument("--mutations", action="store_true")
    parser.add_argument("--only", help="run a single named mutation")
    parser.add_argument("-j", "--jobs", default=8, type=int)
    args = parser.parse_args()
    engine = args.engine.resolve()
    if check_contract(engine):
        return 1
    if not args.mutations:
        return 0
    survived = 0
    selected = [m for m in MUTATIONS if not args.only or m[0] == args.only]
    for name, rel, old, new in selected:
        path = engine / rel
        original = path.read_text()
        if original.count(old) != 1:
            print(f"mutation {name}: pattern found {original.count(old)} times; fix the script")
            return 1
        try:
            path.write_text(original.replace(old, new))
            passed, tail = run_tests(engine, args.jobs)
        finally:
            path.write_text(original)
        if passed:
            survived += 1
            print(f"mutation {name}: SURVIVED")
        else:
            print(f"mutation {name}: KILLED")
    print(f"mutations: {len(selected) - survived}/{len(selected)} KILLED")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
