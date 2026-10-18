"""Scratch verification: boot a RELEASE ROM on the run02 save, heal twice at
the Alderfield clinic with real input, and after each heal check in memory
that the gHeap block list is intact, the text-printer list head is NULL or an
EWRAM pointer, and sUnionRoomPlayerName[0] is EOS. Writes result.json."""
import hashlib, json, pathlib, shutil, struct, subprocess, sys
sys.dont_write_bytecode = True
ROOT = pathlib.Path('/root/claude-dev/wt-cries/Pokemon Game')
sys.path.insert(0, str(ROOT / 'scripts/coordination'))
import codex_cry_gameplay as w
from codex_cry_gameplay import driver, emu, game, mapdata, play

src, engine, scratch, out = (pathlib.Path(a).resolve() for a in sys.argv[1:5])
elf = src.with_suffix('.elf')
nm = subprocess.run(['arm-none-eabi-nm', str(elf)], capture_output=True, text=True, check=True).stdout
syms = {}
for line in nm.splitlines():
    parts = line.split()
    if len(parts) == 3:
        syms.setdefault(w.base_name(parts[2]), int(parts[0], 16))
ADDR = {n: syms[n] for n in ('sHeapStart', 'sFirstTextPrinter', 'sUnionRoomPlayerName', 'gHeap')}
EWRAM = range(0x02000000, 0x02040000)

rom = scratch / 'game.gba'
shutil.copyfile(src, rom)
info = emu.load_build_info(elf, engine, scratch / 'symbol-cache')
info['symbols'] = w.lto_aliases(info['symbols'])
out.mkdir(parents=True, exist_ok=True)
result = dict(rom_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
              elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),
              save_sha256=hashlib.sha256((scratch / 'game.sav').read_bytes()).hexdigest(),
              addresses={k: f'{v:08X}' for k, v in ADDR.items()}, checks=[])
e = emu.Emulator(rom, out)
g = game.Game(e, info)
d = driver.Driver(e, g, mapdata.World(engine), out / 'events.jsonl')
d.moves = game.MoveTable(rom, info)
g.map_names = d.w.by_num


def u32(addr):
    return struct.unpack('<I', g.gdb.read(addr, 4))[0]


def memory_check(label):
    head = u32(ADDR['sHeapStart'])
    blocks, problems, pos = 0, [], head
    for _ in range(512):
        if pos not in EWRAM:
            problems.append(f'block pointer {pos:08X} outside EWRAM')
            break
        w0, magic, w1, prev, nxt = struct.unpack('<HHIII', g.gdb.read(pos, 16))
        blocks += 1
        if magic != 0xA3A3:
            problems.append(f'{pos:08X}: magic {magic:04X}')
            break
        if nxt != head and nxt != pos + 16 + (w1 & 0x3FFFF):
            problems.append(f'{pos:08X}: next {nxt:08X} != end of block')
            break
        pos = nxt
        if pos == head:
            break
    printer = u32(ADDR['sFirstTextPrinter'])
    if printer and printer not in EWRAM:
        problems.append(f'sFirstTextPrinter {printer:08X} outside EWRAM')
    name0 = g.gdb.read(ADDR['sUnionRoomPlayerName'], 1)[0]
    check = dict(label=label, heap_head=f'{head:08X}', heap_blocks=blocks,
                 sFirstTextPrinter=f'{printer:08X}', union_room_name0=f'{name0:02X}', problems=problems)
    result['checks'].append(check)
    d.log('memory-check', **check)
    return check


try:
    play.boot(d, False)
    memory_check('after-continue')
    for n in (1, 2):
        s = d.heal_at_clinic()
        e.capture(f'healed-{n}')
        result[f'heal{n}_party'] = s.party
        memory_check(f'after-heal-{n}')
    result['field_ready'] = d.field_ready(d.state())
    result['alive'] = True
except BaseException as exc:  # record what happened, then re-raise
    result['alive'] = False
    result['error'] = repr(exc)
    raise
finally:
    result['problems'] = [p for c in result['checks'] for p in c['problems']]
    (out / 'result.json').write_text(json.dumps(result, indent=1) + '\n')
    try:
        e.close()
    except Exception:
        pass
