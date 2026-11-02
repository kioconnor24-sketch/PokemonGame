"""Real graphical legacy/wide Save/Continue checks using disclosed save fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument('--engine', type=Path, required=True)
p.add_argument('--rom', type=Path, required=True)
p.add_argument('--save', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--framework', type=Path, required=True)
p.add_argument('--profile', choices=['normal', 'release'], required=True)
p.add_argument('--mode', choices=['legacy', 'wide', 'continue'], required=True)
p.add_argument('--expect', type=Path)
a = p.parse_args()
if a.out.exists() and any(a.out.iterdir()):
    raise SystemExit('Output must be new/empty')
a.out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(a.framework.parent / 'coordination'))
import codex_cry_gameplay as w
from codex_cry_gameplay import emu, game, driver, mapdata, play

info = emu.load_build_info(a.rom.with_suffix('.elf'), a.engine, a.out / 'symbol-cache')
info['symbols'] = w.lto_aliases(info['symbols'])
source = (a.engine / 'src/pokemon_summary_screen.c').read_text()
end = source.index('} *sMonSummaryScreen = NULL;') + len('} *sMonSummaryScreen = NULL;')
exprs = {
    'party': 'offsetof(struct SaveBlock1, playerParty)',
    'party_count': 'offsetof(struct SaveBlock1, playerPartyCount)',
    'daycare': 'offsetof(struct SaveBlock1, daycare.mons[0].mon)',
    'boxes': 'offsetof(struct PokemonStorage, boxes)',
    'checksum': 'offsetof(struct BoxPokemon, checksum)',
    'anchor': 'offsetof(struct SaveBlock2, averonRegionAnchor)',
    'record': 'offsetof(struct SaveBlock3, averonRegionRecord)',
    'summary': 'offsetof(struct PokemonSummaryScreenData, summary.metLocation)',
}
probe = a.out / 'offset-probe.c'
probe.write_text(source[:end] + '\n#include "pokemon_storage_system.h"\n'
    + 'void WideQaOffsets(void) {\n'
    + '\n'.join('asm volatile(".global WIDE_QA_%s\\n.equ WIDE_QA_%s, %%c0" :: "i"(%s));'
                % (name, name, expr) for name, expr in exprs.items()) + '\n}\n')
obj = probe.with_suffix('.o')
subprocess.run(['arm-none-eabi-gcc', '-mthumb', '-mthumb-interwork', '-O2', '-mabi=apcs-gnu',
    '-mtune=arm7tdmi', '-march=armv4t', '-std=gnu17', '-iquote', 'include',
    '-I', 'tools/agbcc/include', '-DMODERN=1', '-DTESTING=0', '-DEMERALD',
    '-c', str(probe.resolve()), '-o', str(obj.resolve())], cwd=a.engine, check=True)
offsets = {}
for line in subprocess.check_output(['arm-none-eabi-nm', str(obj)], text=True).splitlines():
    match = re.fullmatch(r'([0-9a-f]+) A WIDE_QA_(\w+)', line)
    if match:
        offsets[match[2]] = int(match[1], 16)
assert set(offsets) == set(exprs)
sizes = w.chunk_sizes(*w.save_struct_sizes(a.engine, a.out / 'save-sizes', 'off',
                                          release=a.profile == 'release'))
rom_bytes = a.rom.read_bytes()
table = info['symbols']['sSubstructOffsets'] - 0x08000000
orders = [rom_bytes[table + n * 24:table + (n + 1) * 24] for n in range(4)]
secure = info['offsets']['box.secure']

def parts(raw):
    personality, ot = struct.unpack_from('<II', raw)
    key = personality ^ ot
    clear = bytearray(struct.pack('<12I', *(v ^ key for v in struct.unpack_from('<12I', raw, secure))))
    logical = [bytearray(clear[orders[n][personality % 24] * 12:orders[n][personality % 24] * 12 + 12]) for n in range(4)]
    return personality, key, clear, logical

def mon(raw):
    _, _, clear, logical = parts(raw)
    marker = struct.unpack_from('<H', logical[0], 10)[0] >> 14
    high = struct.unpack_from('<H', logical[1], 4)[0] >> 11
    low = logical[3][1]
    return dict(species=struct.unpack_from('<H', logical[0])[0] & 0x7ff,
        location=low | ((high << 8) if marker == 2 else 0), low=low, high=high, marker=marker,
        checksum_valid=sum(struct.unpack('<24H', clear)) & 0xffff == struct.unpack_from('<H', raw, offsets['checksum'])[0])

def set_origin(raw, location, noise=False):
    raw = bytearray(raw)
    personality, key, clear, logical = parts(raw)
    v = struct.unpack_from('<H', logical[0], 10)[0]
    struct.pack_into('<H', logical[0], 10, (v & 0x3fff) | ((2 if noise or location > 255 else 0) << 14))
    v = struct.unpack_from('<H', logical[1], 4)[0]
    struct.pack_into('<H', logical[1], 4, (v & 0x7ff) | ((5 if noise else location >> 8) << 11))
    logical[3][1] = location & 255
    for n, data in enumerate(logical):
        start = orders[n][personality % 24] * 12
        clear[start:start + 12] = data
    struct.pack_into('<12I', raw, secure, *(v ^ key for v in struct.unpack('<12I', clear)))
    struct.pack_into('<H', raw, offsets['checksum'], sum(struct.unpack('<24H', clear)) & 0xffff)
    assert mon(raw)['checksum_valid']
    return raw

rom = a.out / 'game.gba'
flash = rom.with_suffix('.sav')
shutil.copyfile(a.rom, rom)
data = bytearray(a.save.read_bytes())
expected = json.loads(a.expect.read_text())['expected'] if a.mode == 'continue' else (
    dict(party=[238, 253, 216], pc=238, daycare=216) if a.mode == 'legacy'
    else dict(party=[1021, 8191, 238], pc=1021, daycare=8191))
if a.mode != 'continue':
    slots = w.flash_slots(bytes(data), sizes)
    slot = max((i for i, s in enumerate(slots) if s['status'] == 'valid'), key=lambda i: slots[i]['counter'])
    physical = {}
    for i in range(w.SECTORS_PER_SLOT):
        off = (slot * w.SECTORS_PER_SLOT + i) * w.SECTOR_SIZE
        sid = struct.unpack_from('<H', data, off + 0xff4)[0]
        physical[sid] = off
    blocks = {sid: bytearray(data[off:off + sizes[sid]]) for sid, off in physical.items()}
    sb1 = bytearray().join(blocks[i] for i in range(1, 5))
    storage = bytearray().join(blocks[i] for i in range(5, 14))
    template = sb1[offsets['party']:offsets['party'] + 100]
    assert mon(template)['species'] and mon(template)['checksum_valid']
    for i, value in enumerate(expected['party']):
        at = offsets['party'] + i * 100
        sb1[at:at + 100] = set_origin(template, value, noise=a.mode == 'legacy')
    sb1[offsets['party_count']] = 3
    at = offsets['daycare']
    sb1[at:at + 80] = set_origin(template[:80], expected['daycare'], noise=a.mode == 'legacy')
    at = offsets['boxes']
    storage[at:at + 80] = set_origin(template[:80], expected['pc'], noise=a.mode == 'legacy')
    for start, end, joined in ((1, 5, sb1), (5, 14, storage)):
        used = 0
        for sid in range(start, end):
            off, count = physical[sid], sizes[sid]
            data[off:off + count] = joined[used:used + count]
            used += count
            struct.pack_into('<H', data, off + 0xff6,
                             w.sector_checksum(bytes(data[off:off + w.SECTOR_DATA_SIZE]), count))
    assert w.flash_slots(bytes(data), sizes)[slot]['status'] == 'valid'
flash.write_bytes(data)
result = dict(profile=a.profile, mode=a.mode, expected=expected, checks=[],
    fixture='OFFLINE DEV SAVE FIXTURE: cloned existing valid mon into party/PC/daycare; modified encrypted origin bits and sector checksums; no memory writes or production IDs/maps allocated',
    source_save_sha256=hashlib.sha256(a.save.read_bytes()).hexdigest(),
    fixture_save_sha256=hashlib.sha256(data).hexdigest(), rom_sha256=hashlib.sha256(rom_bytes).hexdigest(),
    elf_sha256=info['elf_sha256'], offsets=offsets,
    harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    framework_emu_sha256=hashlib.sha256((a.framework / 'emu.py').read_bytes()).hexdigest())

def check(name, good, **detail):
    result['checks'].append(dict(name=name, ok=bool(good), **detail))
    if not good:
        raise AssertionError(name + ': ' + repr(detail))

e = None
try:
    e = emu.Emulator(rom, a.out, display=250 + (a.profile == 'release'), audio=False)
    g = game.Game(e, info)
    w.use_source_function_names(g)
    d = driver.Driver(e, g, mapdata.World(a.engine), a.out / 'events.jsonl')
    g.map_names = d.w.by_num
    e.start_trace(a.out / 'keys.jsonl', g.sym['gMain'] + g.off['main.vblankCounter1'])
    play.boot(d, False)
    d.settle()
    ptr = lambda name: struct.unpack('<I', g.gdb.read(g.sym[name], 4))[0]
    version = struct.unpack('<H', g.gdb.read(ptr('gSaveBlock3Ptr') + offsets['record'] + 4, 2))[0]
    check('loaded/migrated format2', version == 2, version=version)
    party = [mon(g.gdb.read(g.sym['gParties'] + i * 100, 100)) for i in range(3)]
    pc = mon(g.gdb.read(ptr('gPokemonStoragePtr') + offsets['boxes'], 80))
    daycare = mon(g.gdb.read(ptr('gSaveBlock1Ptr') + offsets['daycare'], 80))
    result['loaded'] = dict(party=party, pc=pc, daycare=daycare, field=d.here())
    check('party exact origins', [m['location'] for m in party] == expected['party'])
    check('PC exact origin', pc['location'] == expected['pc'])
    check('daycare exact origin', daycare['location'] == expected['daycare'])
    check('all observed mon checksums valid', all(m['checksum_valid'] for m in party + [pc, daycare]))
    play.open_start_menu_action(d, 1)
    e.tap('A', after=.8)
    e.tap('A', after=2)
    summary = ptr('sMonSummaryScreen')
    check('real summary opened', 0x02000000 <= summary < 0x02040000, pointer=summary)
    shown = struct.unpack('<H', g.gdb.read(summary + offsets['summary'], 2))[0]
    check('summary cache retains full origin', shown == expected['party'][0], shown=shown)
    d.shot('actual-summary')
    result['summary_text_hex'] = g.gdb.read(g.sym['gStringVar4'], 256).hex()
    if expected['party'][0] == 238:
        encoded = bytes(0 if c == ' ' else 0xbb + ord(c) - ord('A') for c in 'AMITY SQUARE')
        check('trainer memo renders exact place name', encoded in bytes.fromhex(result['summary_text_hex']))
    play.back_to_field(d)
    d.settle()
    if a.mode != 'continue':
        w.release_save(d, 'wide-origin', sizes, flash)
        result['flash_after'] = w.flash_slots(w.read_flash(flash), sizes)
        check('ordinary save writes valid newer flash', not w.flash_verdict(w.flash_slots(bytes(data), sizes), result['flash_after']))
    d.shot('field-after')
    result['status'] = 'PASS'
except BaseException as exc:
    result['status'], result['error'] = 'FAIL', repr(exc)
    raise
finally:
    if e:
        e.close()
    (a.out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'checks': len(result['checks']), 'out': str(a.out)}))
