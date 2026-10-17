#!/usr/bin/env python3
"""Execute actual Mystery Gift Client_Init and its init script with host ASan + UBSan.

Client_Init used to copy MG_LINK_BUFFER_SIZE (1024) bytes out of the 16-byte
gMysteryGiftClientScript_Init. The probe compiles the production function and
the production script definition, so ASan reports any copy past the script.
The client's link, allocator and other callers are host fixtures. No source is
edited.
"""
import argparse
from pathlib import Path
import os
import re
import shlex
import subprocess
import tempfile
import unittest

ENGINE = Path(__file__).resolve().parents[1] / "engine"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--client", type=Path, default=ENGINE / "src/mystery_gift_client.c")
parser.add_argument("--scripts", type=Path, default=ENGINE / "src/mystery_gift_scripts.c")
parser.add_argument("--header", type=Path, default=ENGINE / "include/mystery_gift_client.h")
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


def extract_init_script(source):
    """The init script array plus, when present, the definitions that follow it."""
    start = source.index("const struct MysteryGiftClientCmd gMysteryGiftClientScript_Init[] = {")
    end = source.index("};", start) + 2
    tail = re.findall(r"^(?:const u32 gMysteryGiftClientScript_InitSize\b.*|STATIC_ASSERT\(.*)$",
                      source[end:source.index("static const", end)], re.M)
    return source[start:end] + "\n" + "\n".join(tail)


def enum_block(header, first):
    start = header.index("enum {\n    " + first)
    return header[start:header.index("};", start) + 2]


PREFIX = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
#define MG_LINK_BUFFER_SIZE 0x400
#define MG_LINKID_CLIENT_SCRIPT 16
#define STATIC_ASSERT(expr, id) typedef char id[(expr) ? 1 : -1];
#define AGB_ASSERT(exp) assert(exp)
enum { FUNC_INIT, FUNC_DONE, FUNC_RECV, FUNC_SEND, FUNC_RUN };
struct MysteryGiftClientCmd { u32 instr; u32 parameter; };
struct MysteryGiftClient { u32 funcId, funcState, cmdidx; struct MysteryGiftClientCmd *script; };
'''

MAIN = r'''
int main(void) {
    struct MysteryGiftClient client = {FUNC_INIT, 7, 9, calloc(1, MG_LINK_BUFFER_SIZE)};
    const u8 *bytes = (const u8 *)client.script;
    unsigned nonzero = 0;
    if (!client.script) return 4;
    u32 ret = Client_Init(&client);
    for (unsigned i = sizeof(gMysteryGiftClientScript_Init); i < MG_LINK_BUFFER_SIZE; ++i)
        nonzero += bytes[i] != 0;
    printf("%u %u %u %u %u %u %u %u %u %u\n", ret, client.funcId, client.funcState, client.cmdidx,
           client.script[0].instr, client.script[0].parameter, client.script[1].instr,
           client.script[1].parameter, (unsigned)sizeof(gMysteryGiftClientScript_Init), nonzero);
    free(client.script);
    return 0;
}
'''


class MysteryGiftInitCopy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="averon-mg-init-")
        cls.addClassCleanup(cls.tmp.cleanup)
        root = Path(cls.tmp.name)
        header = args.header.read_text()
        cls.header = header
        code = "\n".join([PREFIX, enum_block(header, "CLI_RET_INIT"), enum_block(header, "CLI_NONE"),
                          extract_init_script(args.scripts.read_text()),
                          extract(args.client.read_text(), "static u32 Client_Init(struct MysteryGiftClient *client)"),
                          MAIN])
        (root / "probe.c").write_text(code)
        cls.binary = root / "probe"
        subprocess.run([*shlex.split(os.environ.get("CC", "cc")), "-g", "-O0",
                        "-fsanitize=address,undefined", "-fno-sanitize-recover=all",
                        str(root / "probe.c"), "-o", str(cls.binary)], check=True)

    def test_init_copies_only_the_init_script(self):
        result = subprocess.run([str(self.binary)], capture_output=True, text=True,
                                env={**os.environ, "ASAN_OPTIONS": "detect_leaks=0"})
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "", result.stderr)
        # CLI_RET_INIT, FUNC_RUN, state 0, cmdidx 0, {CLI_RECV, 16}, {CLI_COPY_RECV, 0},
        # a 16-byte script, and every byte after it left as allocated (zero).
        self.assertEqual(tuple(map(int, result.stdout.split())), (0, 4, 0, 0, 2, 16, 4, 0, 16, 0))

    def test_header_owns_the_init_script_declarations(self):
        for declaration in ("extern const struct MysteryGiftClientCmd gMysteryGiftClientScript_Init[];",
                            "extern const u32 gMysteryGiftClientScript_InitSize;"):
            self.assertTrue(declaration in self.header, "header lacks " + declaration)
        self.assertFalse("extern const struct MysteryGiftClientCmd gMysteryGiftClientScript_Init"
                         in args.client.read_text(), "client.c keeps a local init-script extern")


if __name__ == "__main__":
    unittest.main(argv=[__file__, *unittest_args], verbosity=2)
