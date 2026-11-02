"""Offline DEV save fixture for the cable-session check (same encoding as scripts/claude_play/wide_origin_qa.py).

  link_fixture.py inspect --engine E --rom R SAVE
  link_fixture.py make --engine E --rom R IN OUT --origins 1021,238 [--pokedex]

make clones the save's first party Pokemon into len(origins) party slots with those exact met locations
(marker 2 above 255, as the wide codec writes), optionally sets FLAG_SYS_POKEDEX_GET (the Direct Corner's
precondition), and rewrites the sector checksums of the newest valid slot. Position is set separately
with map_qa.py fixture-save.
"""
import argparse
import json
import pathlib
import re
import struct
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument('cmd', choices=['inspect', 'make'])
ap.add_argument('--engine', type=pathlib.Path, required=True)
ap.add_argument('--rom', type=pathlib.Path, required=True)
ap.add_argument('src', type=pathlib.Path)
ap.add_argument('dst', type=pathlib.Path, nargs='?')
ap.add_argument('--origins')
ap.add_argument('--pokedex', action='store_true')
ap.add_argument('--work', type=pathlib.Path, default=pathlib.Path('/root/claude-dev/link-qa/work'))
a = ap.parse_args()
a.work.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(a.engine.parent / 'scripts/coordination'))
import codex_cry_gameplay as w  # noqa: E402

engine = a.engine.resolve()
exprs = {
    'party': 'offsetof(struct SaveBlock1, playerParty)',
    'party_count': 'offsetof(struct SaveBlock1, playerPartyCount)',
    'flags': 'offsetof(struct SaveBlock1, flags)',
    'pokedex_flag': 'FLAG_SYS_POKEDEX_GET',
    'checksum': 'offsetof(struct BoxPokemon, checksum)',
    'secure': 'offsetof(struct BoxPokemon, secure)',
    'location': 'offsetof(struct SaveBlock1, location)',
    'pos': 'offsetof(struct SaveBlock1, pos)',
}
has_record = 'averonRegionRecord' in (engine / 'include/global.h').read_text()
if has_record:
    exprs['record'] = 'offsetof(struct SaveBlock3, averonRegionRecord)'
probe = a.work / ('probe-%s.c' % engine.parent.parent.name)
probe.write_text('#include "global.h"\n#include "constants/flags.h"\nvoid LinkQaOffsets(void) {\n'
    + '\n'.join('asm volatile(".global LQ_%s\\n.equ LQ_%s, %%c0" :: "i"(%s));' % (n, n, e)
                for n, e in exprs.items()) + '\n}\n')
obj = probe.with_suffix('.o')
subprocess.run(['arm-none-eabi-gcc', '-mthumb', '-mthumb-interwork', '-O2', '-mabi=apcs-gnu', '-mtune=arm7tdmi',
    '-march=armv4t', '-std=gnu17', '-iquote', 'include', '-I', 'tools/agbcc/include', '-DMODERN=1', '-DTESTING=0',
    '-DEMERALD', '-c', str(probe.resolve()), '-o', str(obj.resolve())], cwd=engine, check=True)
off = {}
for line in subprocess.check_output(['arm-none-eabi-nm', str(obj)], text=True).splitlines():
    m = re.fullmatch(r'([0-9a-f]+) A LQ_(\w+)', line)
    if m:
        off[m[2]] = int(m[1], 16)
assert set(off) == set(exprs), off
syms = {}
for line in subprocess.check_output(['arm-none-eabi-nm', str(a.rom.with_suffix('.elf'))], text=True).splitlines():
    parts = line.split()
    if len(parts) == 3:
        syms[parts[2]] = int(parts[0], 16)
rom = a.rom.read_bytes()
table = syms['sSubstructOffsets'] - 0x08000000
orders = [rom[table + n * 24:table + (n + 1) * 24] for n in range(4)]
sizes = w.chunk_sizes(*w.save_struct_sizes(engine, a.work / ('sizes-' + engine.parent.parent.name), 'off', release=False))
SECURE = off['secure']


def parts(raw):
    personality, ot = struct.unpack_from('<II', raw)
    key = personality ^ ot
    clear = bytearray(struct.pack('<12I', *(v ^ key for v in struct.unpack_from('<12I', raw, SECURE))))
    logical = [bytearray(clear[orders[n][personality % 24] * 12:orders[n][personality % 24] * 12 + 12]) for n in range(4)]
    return personality, key, clear, logical


def mon(raw):
    _, _, clear, logical = parts(raw)
    marker = struct.unpack_from('<H', logical[0], 10)[0] >> 14
    high = struct.unpack_from('<H', logical[1], 4)[0] >> 11
    low = logical[3][1]
    return dict(species=struct.unpack_from('<H', logical[0])[0] & 0x7ff, personality=struct.unpack_from('<I', raw)[0],
                location=low | ((high << 8) if marker == 2 else 0), low=low, high=high, marker=marker,
                checksum_valid=sum(struct.unpack('<24H', clear)) & 0xffff == struct.unpack_from('<H', raw, off['checksum'])[0])


def reencode(template, location, personality):
    """The template mon with this origin, re-encrypted under a distinct personality (to tell slots apart)."""
    _, _, clear, logical = parts(template)
    v = struct.unpack_from('<H', logical[0], 10)[0]
    struct.pack_into('<H', logical[0], 10, (v & 0x3fff) | ((2 if location > 255 else 0) << 14))
    v = struct.unpack_from('<H', logical[1], 4)[0]
    struct.pack_into('<H', logical[1], 4, (v & 0x7ff) | ((location >> 8 if location > 255 else 0) << 11))
    logical[3][1] = location & 255
    raw = bytearray(template)
    struct.pack_into('<I', raw, 0, personality)
    ot = struct.unpack_from('<I', raw, 4)[0]
    key = personality ^ ot
    clear = bytearray(48)
    for n, data in enumerate(logical):
        start = orders[n][personality % 24] * 12
        clear[start:start + 12] = data
    struct.pack_into('<12I', raw, SECURE, *(v ^ key for v in struct.unpack('<12I', clear)))
    struct.pack_into('<H', raw, off['checksum'], sum(struct.unpack('<24H', clear)) & 0xffff)
    assert mon(bytes(raw))['checksum_valid'] and mon(bytes(raw))['location'] == location
    return raw


data = bytearray(a.src.read_bytes())
slots = w.flash_slots(bytes(data), sizes)
slot = max((i for i, s in enumerate(slots) if s['status'] == 'valid'), key=lambda i: slots[i]['counter'])
physical = {}
for i in range(w.SECTORS_PER_SLOT):
    o = (slot * w.SECTORS_PER_SLOT + i) * w.SECTOR_SIZE
    physical[struct.unpack_from('<H', data, o + 0xff4)[0]] = o
sb1 = bytearray().join(bytes(data[physical[i]:physical[i] + sizes[i]]) for i in range(1, 5))
count = sb1[off['party_count']]
party = [mon(bytes(sb1[off['party'] + i * 100:off['party'] + i * 100 + 100])) for i in range(count)]
flag = off['pokedex_flag']
state = dict(slot=slot, counter=slots[slot]['counter'], party_count=count, party=party,
             pokedex=bool(sb1[off['flags'] + flag // 8] >> (flag % 8) & 1),
             location=list(sb1[off['location']:off['location'] + 4]), pos=struct.unpack_from('<hh', sb1, off['pos']))
if a.cmd == 'inspect':
    print(json.dumps(state, indent=1))
    raise SystemExit
origins = [int(v) for v in a.origins.split(',')]
template = bytes(sb1[off['party']:off['party'] + 100])
assert party and party[0]['checksum_valid']
for i, value in enumerate(origins):
    at = off['party'] + i * 100
    sb1[at:at + 100] = reencode(template, value, (party[0]['personality'] + 0x101 * i) & 0xffffffff)
for i in range(len(origins), 6):
    at = off['party'] + i * 100
    sb1[at:at + 100] = bytes(100)
sb1[off['party_count']] = len(origins)
if a.pokedex:
    sb1[off['flags'] + flag // 8] |= 1 << (flag % 8)
used = 0
for sid in range(1, 5):
    o, n = physical[sid], sizes[sid]
    data[o:o + n] = sb1[used:used + n]
    used += n
    struct.pack_into('<H', data, o + 0xff6, w.sector_checksum(bytes(data[o:o + w.SECTOR_DATA_SIZE]), n))
assert w.flash_slots(bytes(data), sizes)[slot]['status'] == 'valid'
a.dst.write_bytes(data)
print(json.dumps(dict(made=str(a.dst), origins=origins, pokedex=a.pokedex), indent=1))
