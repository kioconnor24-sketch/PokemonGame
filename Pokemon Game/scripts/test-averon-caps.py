"""Compile the actual cap functions with mocked save flags; no emulator needed.

Run with Python on Linux/WSL with the existing host C compiler. Tests logic,
not the GBA integration or battle UI. Source is extracted, never reimplemented.
"""
from pathlib import Path
import re, subprocess, tempfile

root=Path(__file__).resolve().parents[1]/'engine'
source=(root/'src/caps.c').read_text()
functions=source[source.index('u32 GetCurrentLevelCap(void)'):source.index('u32 GetCurrentEVCap(void)')]
flags=list(dict.fromkeys(re.findall(r'\{(FLAG_\w+),',functions)))
header='''#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
typedef uint32_t u32;
#define TRUE 1
#define FALSE 0
#define MAX_LEVEL 100
#define ARRAY_COUNT(a) (sizeof(a)/sizeof((a)[0]))
'''
header+='\n'.join(f'#define {flag} {i}' for i,flag in enumerate(flags))
header+='''
static unsigned char flags[64];
static int FlagGet(unsigned int flag) { return flags[flag]; }
static unsigned int VarGet(unsigned int id) { (void)id; return 0; }
'''
header+='#include "config/caps.h"\n'
tests='''
static void check(int condition, const char *message) {
    if (!condition) { fprintf(stderr, "FAIL: %s\\n", message); exit(1); }
}
int main(void) {
    const u32 expected[] = {15,23,31,39,47,55,62,69,72,76,100};
    for (u32 i=0; i<ARRAY_COUNT(expected); ++i) {
        const u32 cap=expected[i];
        check(GetCurrentLevelCap()==cap, "progression cap");
        check(GetSoftLevelCapExpValue(cap-1,173)==173, "EXP below cap preserved");
        check(GetSoftLevelCapExpValue(cap,173)==0, "EXP at cap blocked");
        check(GetSoftLevelCapExpValue(cap+1,173)==0, "EXP above cap blocked");
        if (i<ARRAY_COUNT(expected)-1) flags[i]=1;
    }
    check(B_RARE_CANDY_CAP==TRUE, "Rare Candy cap configured");
    puts("PASS: 11 progression caps, below/at/above-cap EXP; Rare Candy cap configured.");
    return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='averon-caps-') as folder:
    src=Path(folder)/'caps-test.c';binary=Path(folder)/'caps-test'
    src.write_text(header+functions+tests)
    subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-I',str(root/'include'),str(src),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
