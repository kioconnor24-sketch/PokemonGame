#!/usr/bin/env python3
"""Compile & exercise the REAL engine's level-cap functions with host C compiler.

Reads native src/caps.c and include/config/caps.h; no duplicated Python EXP
implementation. Checks cap behavior, not whether the *numbers* are well balanced.
"""
import argparse
import re
import subprocess
import tempfile
from pathlib import Path

BEGIN = "u32 GetCurrentLevelCap(void)"
END = "u32 GetCurrentEVCap(void)"
ROW = re.compile(r"\{\s*(FLAG_[A-Z0-9_]+)\s*,\s*(\d+)\s*\}")


def extract_functions(source):
    if source.count(BEGIN) != 1 or source.count(END) != 1:
        raise ValueError("Unexpected caps.c function structure")
    section = source[source.index(BEGIN):source.index(END)]
    return section


def inspect_stages(section):
    start = section.index("sLevelCapFlagMap")
    opening = section.index("{", start)
    closing = section.index("};", opening)
    rows = ROW.findall(section[opening:closing])
    if not rows:
        raise ValueError("No level-cap flag rows")
    flags = [name for name, _ in rows]
    caps = [int(level) for _, level in rows]
    if len(flags) != len(set(flags)):
        raise ValueError("Duplicate level-cap flag")
    if any(cap <= 1 or cap >= 100 for cap in caps):
        raise ValueError("Level cap must remain within 2..99 until final MAX_LEVEL")
    if any(b <= a for a, b in zip(caps, caps[1:])):
        raise ValueError("Level caps must increase strictly")
    return list(zip(flags, caps))


def build_harness(source, stages):
    preamble = """#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
typedef uint32_t u32;
#define TRUE 1
#define FALSE 0
#define MAX_LEVEL 100
#define ARRAY_COUNT(a) (sizeof(a) / sizeof((a)[0]))
"""
    preamble += "\n".join(f"#define {name} {i}" for i, (name, _) in enumerate(stages))
    preamble += """
static unsigned char gTestFlags[256];
static int FlagGet(unsigned int flag) { return gTestFlags[flag]; }
static unsigned int VarGet(unsigned int id) { (void)id; return 0; }
#include "config/caps.h"
static void require_true(int condition, const char *reason) {
    if (!condition) { fprintf(stderr, "FAIL: %s\\n", reason); exit(1); }
}
"""
    expected = ", ".join(str(cap) for _, cap in stages) + ", 100"
    testcase = f"""
int main(void) {{
    const u32 expected[] = {{{expected}}};
    require_true(ARRAY_COUNT(expected) == {len(stages) + 1}, "expected table length");
    for (u32 i = 0; i < ARRAY_COUNT(expected); i++) {{
        u32 actual = GetCurrentLevelCap();
        require_true(actual == expected[i], "first unset flag determines level cap");
        require_true(GetSoftLevelCapExpValue(actual - 1, 190) == 190,
                     "EXP below cap preserved");
        require_true(GetSoftLevelCapExpValue(actual, 190) == 0,
                     "EXP at cap is blocked");
        require_true(GetSoftLevelCapExpValue(actual + 1, 190) == 0,
                     "EXP above cap is blocked");
        if (i + 1 < ARRAY_COUNT(expected))
            gTestFlags[i] = 1;
    }}
    require_true(B_RARE_CANDY_CAP == TRUE, "Rare Candy cap configured");
    puts("PASS: native level-cap functions + EXP behavior for {len(stages)} flag stages and MAX_LEVEL.");
    return 0;
}}
"""
    return preamble + source + testcase


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--engine", required=True, type=Path)
    ap.add_argument("--cc", default="cc")
    args = ap.parse_args()
    source = extract_functions((args.engine / "src/caps.c").read_text(encoding="utf-8"))
    stages = inspect_stages(source)
    with tempfile.TemporaryDirectory(prefix="averon-real-caps-") as folder:
        code = Path(folder) / "caps_test.c"
        binary = Path(folder) / "caps_test"
        code.write_text(build_harness(source, stages), encoding="utf-8")
        subprocess.run([args.cc, "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-I", str(args.engine / "include"),
                        str(code), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True)


if __name__ == "__main__":
    main()
