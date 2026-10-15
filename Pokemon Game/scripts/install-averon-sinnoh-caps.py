#!/usr/bin/env python3
"""Install or verify Sinnoh/postgame hard-cap flags in native Emerald source.

Run AFTER the Codex Averon map/content generator. Safe to run more than once.
This does not grant Sinnoh badges: native Gym/quest scripts must set the flags.
"""
import argparse
import re
from pathlib import Path

# 0x2A-0x2F are reserved by the two early-game quest chains (PR #3).
CAP_STAGES = [
    (0x30, "FLAG_AVERON_SINNOH_BADGE01", 79),
    (0x31, "FLAG_AVERON_SINNOH_BADGE02", 81),
    (0x32, "FLAG_AVERON_SINNOH_BADGE03", 83),
    (0x33, "FLAG_AVERON_SINNOH_BADGE04", 85),
    (0x34, "FLAG_AVERON_SINNOH_BADGE05", 87),
    (0x35, "FLAG_AVERON_SINNOH_BADGE06", 89),
    (0x36, "FLAG_AVERON_SINNOH_BADGE07", 91),
    (0x37, "FLAG_AVERON_SINNOH_BADGE08", 93),
    (0x38, "FLAG_AVERON_SINNOH_CHAMPION", 95),
    (0x39, "FLAG_AVERON_POSTGAME_EPILOGUE", 97),
    (0x3A, "FLAG_AVERON_RED_ACCESS", 99),
]

ANCHOR = "        {FLAG_IS_CHAMPION, 76},"
CAPS_END = "    };"
EXPECTED_LINES = [f"        {{{name}, {level}}}," for _, name, level in CAP_STAGES]


def flags_edit(source):
    """Reserve exact unused flag slots, refuse to clobber other contributors."""
    result = source
    for number, name, _ in CAP_STAGES:
        old = re.compile(
            rf"^#define[ \t]+FLAG_UNUSED_0x{number:03X}[ \t]+0x{number:02X}\b[^\n]*$",
            re.M)
        new = f"#define {name:<38} 0x{number:02X} // Averon Sinnoh / endgame persistent progress"
        defined = re.search(rf"^#define[ \t]+{name}[ \t]+0x([0-9A-Fa-f]+)\b", result, re.M)
        if defined:
            if int(defined.group(1), 16) != number:
                raise ValueError(f"Conflicting existing {name} value: {defined.group(1)}")
            continue
        result, count = old.subn(new, result)
        if count != 1:
            raise ValueError(f"Unused flag slot 0x{number:02X} is occupied or unavailable")
    return result


def caps_edit(source):
    """Extend existing Averon first-unset-flag cap map after League cap."""
    if source.count(ANCHOR) != 1:
        raise ValueError("Expected one Averon Champion level-cap anchor")
    if all(line in source for line in EXPECTED_LINES):
        anchor_pos = source.index(ANCHOR)
        slice_pos = source.index(CAPS_END, anchor_pos)
        rows = source[anchor_pos:slice_pos]
        observed = re.findall(r"\{(FLAG_AVERON_(?:SINNOH|POSTGAME|RED)[A-Z0-9_]+),\s*(\d+)\}", rows)
        expected = [(name, str(level)) for _, name, level in CAP_STAGES]
        if observed != expected:
            raise ValueError("Sinnoh cap entries are present but unexpected or misordered")
        return source
    if any(name in source for _, name, _ in CAP_STAGES):
        raise ValueError("Partial Sinnoh level-cap state; requires manual review")
    additions = "\n".join(EXPECTED_LINES)
    return source.replace(ANCHOR, ANCHOR + "\n" + additions, 1)


def verify_caps(source):
    source = caps_edit(source)
    return all(source.count(line) == 1 for line in EXPECTED_LINES)


def stage_cap(set_flags):
    """Documentation/test model of the first-unset-flag design, not engine code."""
    base_stages = [
        ("FLAG_BADGE01_GET", 15), ("FLAG_BADGE02_GET", 23),
        ("FLAG_BADGE03_GET", 31), ("FLAG_BADGE04_GET", 39),
        ("FLAG_BADGE05_GET", 47), ("FLAG_BADGE06_GET", 55),
        ("FLAG_BADGE07_GET", 62), ("FLAG_BADGE08_GET", 69),
        ("FLAG_AVERON_ASSAULT_COMPLETE", 72), ("FLAG_IS_CHAMPION", 76),
    ]
    for flag, cap in base_stages + [(n, cap) for _, n, cap in CAP_STAGES]:
        if flag not in set_flags:
            return cap
    return 100


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--install", action="store_true",
                        help="Write guarded changes; default verifies only")
    args = parser.parse_args()
    flags_path = args.engine / "include/constants/flags.h"
    caps_path = args.engine / "src/caps.c"
    old_flags = flags_path.read_text(encoding="utf-8")
    old_caps = caps_path.read_text(encoding="utf-8")
    revised_flags = flags_edit(old_flags)
    revised_caps = caps_edit(old_caps)
    if not args.install and (old_flags != revised_flags or old_caps != revised_caps):
        parser.error("Sinnoh cap definitions are not fully installed; run with --install")
    if args.install:
        if revised_flags != old_flags:
            flags_path.write_text(revised_flags, encoding="utf-8")
        if revised_caps != old_caps:
            caps_path.write_text(revised_caps, encoding="utf-8")
    print("Sinnoh and postgame cap stages validated (11 persistent flags). "
          "Native compilation and event flag setting must be tested separately.")


if __name__ == "__main__":
    main()
