#!/usr/bin/env python3
"""Run real generated healer tables and source under host ASan/UBSan.

All additional IDs live in TemporaryDirectory JSON fixtures, never production.
Requires engine/tools/jsonproc/jsonproc (make tools first), cc, generated map IDs.
--template can point at the pre-fix template to reproduce the rejected append.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile

ENGINE = Path(__file__).resolve().parents[1] / 'engine'


def definition(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 0
    for end in range(brace, len(source)):
        depth += (source[end] == '{') - (source[end] == '}')
        if depth == 0:
            return source[start:end + 1]
    raise ValueError(signature)


PREFIX = r'''
#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
#define ARRAY_COUNT(x) (sizeof(x)/sizeof((x)[0]))
#define LOCALID_NONE 0
#define CHECK(c) do { if (!(c)) { fprintf(stderr,"line %d: %s\n",__LINE__,#c); exit(2); } } while(0)
#include "constants/maps.h"
#include "constants/map_event_ids.h"
#include "fixture_ids.h"
struct HealLocation { u8 mapGroup, mapNum; int16_t x,y; };
struct WarpData { int8_t mapGroup, mapNum, warpId; int16_t x,y; };
static struct { struct WarpData lastHealLocation; } save1, *gSaveBlock1Ptr = &save1;
static u16 gSpecialVar_LastTalked, gSpecialVar_0x800B;
#include "fixture_tables.h"
'''
DRIVER = r'''
int main(void) {
    unsigned checks = 0;
#ifdef EXPECT_TEST_NPC
    CHECK(GetHealNpcLocalId(HEAL_LOCATION_TEST_ONLY) == EXPECT_TEST_NPC);
#endif
    CHECK(GetHealLocation(0) == NULL);
    CHECK(GetHealLocation(NUM_HEAL_LOCATIONS) == NULL);
    CHECK(GetHealNpcLocalId(0) == LOCALID_NONE);
    CHECK(GetHealNpcLocalId(NUM_HEAL_LOCATIONS) == LOCALID_NONE);
    CHECK(GetHealNpcLocalId(0xFFFFFFFF) == LOCALID_NONE);
    for (u32 id=1; id<NUM_HEAL_LOCATIONS; ++id) {
        const struct HealLocation *loc = GetHealLocation(id);
        struct WarpData expected = {loc->mapGroup, loc->mapNum, WARP_ID_NONE, loc->x, loc->y};
        struct WarpData actual;
        gSaveBlock1Ptr->lastHealLocation = expected;
        // Some legacy anchors alias the same coordinates; production uses
        // the first matching row, which must remain the observed behavior.
        u32 matched = GetHealLocationIndexByWarpData(&expected);
        u32 npc = GetHealNpcLocalId(matched);
        gSpecialVar_LastTalked = gSpecialVar_0x800B = 0xBEEF;
        SetWhiteoutRespawnWarpAndHealerNPC(&actual);
        if (!npc) {
            CHECK(memcmp(&actual, &expected, sizeof(actual)) == 0);
            CHECK(gSpecialVar_LastTalked == 0xBEEF && gSpecialVar_0x800B == 0xBEEF);
        } else {
            CHECK(actual.mapGroup == sWhiteoutRespawnHealCenterMapIdxs[matched-1][0]);
            CHECK(actual.mapNum == sWhiteoutRespawnHealCenterMapIdxs[matched-1][1]);
            CHECK(actual.warpId == WARP_ID_NONE);
            CHECK(actual.x == sWhiteoutRespawnHealCenterMapIdxs[matched-1][2]);
            CHECK(actual.y == sWhiteoutRespawnHealCenterMapIdxs[matched-1][3]);
            CHECK(gSpecialVar_LastTalked == npc && gSpecialVar_0x800B == npc);
        }
        CHECK(GetHealNpcLocalId(id) == sWhiteoutRespawnHealerNpcIds[id-1]);
        checks++;
    }
    printf("PASS %u healer rows + invalid-ID boundaries\n", checks);
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', type=Path, default=ENGINE / 'src/data/heal_locations.json.txt')
    args = parser.parse_args()
    source = (ENGINE / 'src/heal_location.c').read_text()
    functions = '\n'.join(definition(source, sig) for sig in (
        'u32 GetHealLocationIndexByWarpData(',
        'const struct HealLocation *GetHealLocation(u32',
        'u32 GetHealNpcLocalId(',
        'void SetWhiteoutRespawnWarpAndHealerNPC('))
    baseline = json.loads((ENGINE / 'src/data/heal_locations.json').read_text())
    with tempfile.TemporaryDirectory(prefix='averon-healer-contract-') as tmp:
        tmp = Path(tmp)
        for mode in ('current', 'append-without-nurse', 'append-with-nurse'):
            data = json.loads(json.dumps(baseline))
            if mode != 'current':
                row = dict(id='HEAL_LOCATION_TEST_ONLY', map='MAP_OLDALE_TOWN', x=123, y=124)
                if mode == 'append-with-nurse':
                    row.update(respawn_map='MAP_OLDALE_TOWN_POKEMON_CENTER_1F', respawn_npc='1')
                data['heal_locations'].append(row)
            fixture = tmp / 'fixture.json'
            fixture.write_text(json.dumps(data))
            for template, output in ((args.template, 'fixture_tables.h'),
                                     (ENGINE / 'src/data/heal_locations.constants.json.txt', 'fixture_ids.h')):
                subprocess.run([str(ENGINE / 'tools/jsonproc/jsonproc'), str(fixture), str(template), str(tmp / output)], check=True)
            expectation = '' if mode == 'current' else f'#define EXPECT_TEST_NPC {int(mode == "append-with-nurse")}\n'
            (tmp / 'probe.c').write_text(PREFIX + functions + '\n' + expectation + DRIVER)
            subprocess.run([os.environ.get('CC', 'cc'), '-std=c11', '-O1', '-g', '-no-pie',
                            '-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                            '-I', str(tmp), '-I', str(ENGINE / 'include'), str(tmp / 'probe.c'),
                            '-o', str(tmp / 'probe')], check=True)
            print(mode, flush=True)
            subprocess.run([str(tmp / 'probe')], check=True)


if __name__ == '__main__':
    main()
