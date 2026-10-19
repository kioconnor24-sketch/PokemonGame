#!/usr/bin/env python3
"""Execute release/development configuration and extracted production guards.

No engine files are modified. Requires generated engine headers, ARM GCC for
preprocessing, and a host C compiler. These are host tests of production code;
they do not claim a linked release ROM, full EXP routing, or graphical QA.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

MACROS = {
    'I_EXP_SHARE_ITEM': 'GEN_5',
    'I_EXP_SHARE_FLAG': '0',
    'B_SPLIT_EXP': 'GEN_5',
    'B_EXP_CAP_TYPE': 'EXP_CAP_HARD',
    'B_RARE_CANDY_CAP': 'TRUE',
    'MAX_LEVEL': '100',
    'P_MEGA_EVOLUTIONS': 'TRUE',
    'P_PRIMAL_REVERSIONS': 'FALSE',
    'P_ULTRA_BURST_FORMS': 'FALSE',
    'P_REGIONAL_FORMS': 'TRUE',
    'P_CRIES_ENABLED': 'FALSE',
    **{f'P_GEN_{i}_POKEMON': 'TRUE' for i in range(1, 10)},
}
INCLUDES = '''#include "global.h"
#include "config/caps.h"
#include "config/debug.h"
'''

def definition(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth = 0
    for end in range(brace, len(source)):
        depth += (source[end] == '{') - (source[end] == '}')
        if not depth:
            return source[start:end + 1]
    raise ValueError(f'Unclosed definition: {signature}')


def cpp(engine, compiler, mode, content):
    flags = ['-mcpu=arm7tdmi', '-mthumb', '-DMODERN=1', '-DEMERALD', '-DTESTING=0']
    if mode == 'release':
        flags.append('-DRELEASE')
    command = [*compiler, '-E', '-P', '-std=gnu17', '-iquote', str(engine / 'include'), *flags, '-x', 'c', '-']
    result = subprocess.run(command, input=INCLUDES + content, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


PREFIX = r'''
#include <stdio.h>
#include <string.h>
#include <stdint.h>
typedef unsigned bool32;
typedef unsigned u32;
#define CHECK(x) do { ++checks; if (!(x)) { fprintf(stderr,"FAIL line %d: %s\n", __LINE__, #x); return 1; } } while (0)
static unsigned checks, flagCalls, callbackCalls;
static bool32 flagValue, callbackValue;
static unsigned lastBattler;
static bool32 FlagGet(unsigned id) { ++flagCalls; (void)id; return flagValue; }
enum BattlerId { BATTLER_ZERO, BATTLER_ONE, BATTLER_TWO, BATTLER_THREE };
static bool32 MegaCallback(enum BattlerId battler) { ++callbackCalls; lastBattler=battler; return callbackValue; }
struct GimmickInfo { bool32 (*CanActivate)(enum BattlerId); };
static struct { u32 windowsType, battleStyle, expOnCatch, specialTrainerBattleType; } gBattleScripting;
#define GetConfig(x) (x)
'''

FIXTURE = r'''
static struct GimmickInfo gGimmicksInfo[GIMMICKS_COUNT];
struct BattleFixture { struct { enum Gimmick usableGimmick[4]; } gimmick; };
static struct BattleFixture battleStruct, *gBattleStruct = &battleStruct;
static unsigned gBattlersCount;
'''

DRIVER = r'''
int main(void) {
    PARITY_CONFIG_ASSERTS
    for (unsigned v=0;v<2;++v) {
        flagValue=v;flagCalls=0;
        CHECK(IsGen6ExpShareEnabled()==0);
        CHECK(flagCalls==0);
    }
    for (unsigned battler=0;battler<4;++battler) {
        for (unsigned allowed=0;allowed<2;++allowed) {
            callbackValue=allowed;
            for (unsigned gimmick=0;gimmick<GIMMICKS_COUNT;++gimmick) {
                for (unsigned i=0;i<GIMMICKS_COUNT;++i) gGimmicksInfo[i].CanActivate=MegaCallback;
                callbackCalls=0;
                CHECK(CanActivateGimmick(battler,gimmick)==(gimmick==GIMMICK_MEGA ? allowed : 0));
                CHECK(callbackCalls==(gimmick==GIMMICK_MEGA));
                if (callbackCalls) CHECK(lastBattler==battler);
            }
        }
    }
    gGimmicksInfo[GIMMICK_MEGA].CanActivate=0;
    callbackCalls=0;
    CHECK(CanActivateGimmick(0,GIMMICK_MEGA)==0);
    CHECK(callbackCalls==0);
    const unsigned invalidGimmicks[] = {GIMMICKS_COUNT, 255, UINT32_MAX};
    for (unsigned battler=0;battler<4;++battler) {
        for (unsigned i=0;i<sizeof(invalidGimmicks)/sizeof(invalidGimmicks[0]);++i) {
            callbackCalls=0;
            CHECK(CanActivateGimmick(battler,invalidGimmicks[i])==0);
            CHECK(callbackCalls==0);
        }
    }
    for (gBattlersCount=0;gBattlersCount<=4;++gBattlersCount) {
        for (unsigned allowed=0;allowed<2;++allowed) {
            for (unsigned i=0;i<GIMMICKS_COUNT;++i) gGimmicksInfo[i].CanActivate=MegaCallback;
            for (unsigned i=0;i<4;++i) gBattleStruct->gimmick.usableGimmick[i]=GIMMICK_TERA;
            callbackValue=allowed;callbackCalls=0;
            AssignUsableGimmicks();
            for (unsigned i=0;i<4;++i) {
                CHECK(gBattleStruct->gimmick.usableGimmick[i]==
                      (i>=gBattlersCount ? GIMMICK_TERA : allowed ? GIMMICK_MEGA : GIMMICK_NONE));
            }
            CHECK(callbackCalls==gBattlersCount);
        }
    }
    for (unsigned oldStyle=0;oldStyle<3;++oldStyle) {
        gBattleScripting.windowsType=7;
        gBattleScripting.specialTrainerBattleType=13;
        gBattleScripting.battleStyle=oldStyle;
        ClearSetBScriptingStruct();
        CHECK(gBattleScripting.battleStyle==1);
        CHECK(gBattleScripting.windowsType==7);
        CHECK(gBattleScripting.specialTrainerBattleType==13);
    }
    printf("PASS: %u production/config checks\n", checks);
    return 0;
}
'''


def probe(engine, compiler, host, mode, overrides='', function_mutation=None):
    functions = '\n'.join(definition((engine / name).read_text(), signature) for name, signature in [
        ('src/battle_util.c', 'bool32 IsGen6ExpShareEnabled(void)'),
        ('src/battle_gimmick.c', 'bool32 CanActivateGimmick('),
        ('src/battle_gimmick.c', 'void AssignUsableGimmicks(void)'),
        ('src/battle_main.c', 'static void ClearSetBScriptingStruct(void)'),
    ])
    if function_mutation:
        before, after = function_mutation
        if functions.count(before) != 1:
            raise ValueError('Mutation target must match exactly once')
        functions = functions.replace(before, after)
    assertions = '\n'.join(f'CHECK(({name}) == ({expected}));' for name, expected in MACROS.items())
    for macro in ('DEBUG_OVERWORLD_MENU', 'DEBUG_BATTLE_MENU', 'DEBUG_POKEMON_SPRITE_VISUALIZER'):
        assertions += f'\nCHECK({macro} == {0 if mode == "release" else 1});'
    assertions += '\nCHECK(B_PHYSICAL_SPECIAL_SPLIT >= GEN_4);'
    # Only the marked code is compiled by the host. Every macro is expanded by
    # the ARM compiler against real production include order with TESTING=0.
    marked = '\nPARITY_BEGIN\n' + functions + '\n' + DRIVER.replace('PARITY_CONFIG_ASSERTS', assertions) + '\nPARITY_END\n'
    preprocessed = cpp(engine, compiler, mode, overrides + marked)
    body = preprocessed.split('PARITY_BEGIN\n', 1)[1].split('PARITY_END', 1)[0]
    enum = definition((engine / 'include/battle_gimmick.h').read_text(), 'enum Gimmick\n') + ';\n'
    with tempfile.TemporaryDirectory(prefix='averon-release-parity-') as directory:
        source = Path(directory) / 'probe.c'
        binary = Path(directory) / 'probe'
        source.write_text(PREFIX + enum + FIXTURE + body)
        compiled = subprocess.run([*host, '-std=c17', '-Wall', '-Wextra', '-fsanitize=address,undefined',
                                   '-fno-sanitize-recover=all', str(source), '-o', str(binary)],
                                  capture_output=True, text=True)
        if compiled.returncode:
            raise RuntimeError(f'Host compilation failed:\n{compiled.stderr}')
        return subprocess.run([str(binary)], text=True, capture_output=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--mutations', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    engine = args.engine.resolve()
    # Exercise ordinary Make defaults as well as explicit profile restoration.
    # Auditing the header alone would miss a future Make default of CRIES=on.
    subprocess.run([sys.executable, str(Path(__file__).parent / 'coordination/test_codex_cry_default.py'), '-v'],
                   env={**os.environ, 'AVERON_CRY_TEST_ENGINE': str(engine), 'PYTHONDONTWRITEBYTECODE': '1'},
                   check=True)
    compiler = shlex.split(os.environ.get('ARM_CC', 'arm-none-eabi-gcc'))
    host = shlex.split(os.environ.get('CC', 'cc'))
    report = {'engine': str(engine), 'testing': 0, 'modes': {}, 'mutations': {},
              'probe_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'arm_compiler': subprocess.run([*compiler, '--version'], check=True, capture_output=True, text=True).stdout.splitlines()[0],
              'host_compiler': subprocess.run([*host, '--version'], check=True, capture_output=True, text=True).stdout.splitlines()[0],
              'asan_options': os.environ.get('ASAN_OPTIONS', ''),
              'source_sha256': {str(p.relative_to(engine)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [*(engine/'include/config').glob('*.h'),
                                          engine/'include/global.h', engine/'include/constants/global.h',
                                          engine/'include/constants/pokemon.h', engine/'include/battle_gimmick.h',
                                          engine/'src/battle_util.c', engine/'src/battle_gimmick.c', engine/'src/battle_main.c']}}
    for mode in ('development', 'release'):
        result = probe(engine, compiler, host, mode)
        print(mode + ': ' + result.stdout.strip())
        if result.returncode:
            raise RuntimeError(result.stderr)
        report['modes'][mode] = result.stdout.strip()
    if args.mutations:
        for macro, replacement in {
            'I_EXP_SHARE_ITEM': 'GEN_6',
            'I_EXP_SHARE_FLAG': '100',
            'B_SPLIT_EXP': 'GEN_6',
            'B_EXP_CAP_TYPE': 'EXP_CAP_NONE',
            'B_RARE_CANDY_CAP': 'FALSE',
            'MAX_LEVEL': '101',
            'P_MEGA_EVOLUTIONS': 'FALSE',
            'P_PRIMAL_REVERSIONS': 'TRUE',
            'P_ULTRA_BURST_FORMS': 'TRUE',
            'P_REGIONAL_FORMS': 'FALSE',
            'P_CRIES_ENABLED': 'TRUE',
            'P_GEN_9_POKEMON': 'FALSE',
            'DEBUG_OVERWORLD_MENU': 'TRUE',
            'DEBUG_BATTLE_MENU': 'TRUE',
            'DEBUG_POKEMON_SPRITE_VISUALIZER': 'TRUE',
            'B_PHYSICAL_SPECIAL_SPLIT': 'GEN_3',
        }.items():
            result = probe(engine, compiler, host, 'release', f'\n#undef {macro}\n#define {macro} {replacement}\n')
            if result.returncode == 0 or 'FAIL line' not in result.stderr:
                raise RuntimeError(f'Undetected or invalid mutation {macro}: {result.stderr}')
            report['mutations'][macro] = 'DETECTED'
            print(f'mutation {macro}: DETECTED')
        for name, change in {
            'gimmick-release-guard-removed': ('if (gimmick != GIMMICK_MEGA)', 'if (FALSE)'),
            'gimmick-guard-test-only': ('if (gimmick != GIMMICK_MEGA)\n        return FALSE;', '#if TESTING\n    if (gimmick != GIMMICK_MEGA)\n        return FALSE;\n#endif'),
            'mega-legality-callback-bypassed': ('return gGimmicksInfo[gimmick].CanActivate != NULL && gGimmicksInfo[gimmick].CanActivate(battler);', 'return TRUE;'),
            'shift-restored': ('gBattleScripting.battleStyle = OPTIONS_BATTLE_STYLE_SET;', 'gBattleScripting.battleStyle = OPTIONS_BATTLE_STYLE_SHIFT;'),
            'team-share-enabled': ('if (I_EXP_SHARE_FLAG <= TEMP_FLAGS_END)', 'if (FALSE)'),
            'stale-gimmick-retained': ('gBattleStruct->gimmick.usableGimmick[battler] = GIMMICK_NONE;', 'gBattleStruct->gimmick.usableGimmick[battler] = GIMMICK_TERA;'),
            'last-battler-not-assigned': ('battler < gBattlersCount;', 'battler + 1 < gBattlersCount;'),
            'assigned-gimmick-substituted': ('gBattleStruct->gimmick.usableGimmick[battler] = gimmick;', 'gBattleStruct->gimmick.usableGimmick[battler] = GIMMICK_Z_MOVE;'),
        }.items():
            result = probe(engine, compiler, host, 'release', function_mutation=change)
            if result.returncode == 0 or 'FAIL line' not in result.stderr:
                raise RuntimeError(f'Undetected or invalid mutation {name}: {result.stderr}')
            report['mutations'][name] = 'DETECTED'
            print(f'mutation {name}: DETECTED')
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(f'PASS: {len(report["modes"])} production modes; {len(report["mutations"])} mutations detected')

if __name__ == '__main__':
    main()
