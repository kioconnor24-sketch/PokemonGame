"""Scratch debugging only: walk to the Alderfield nurse on a RELEASE ROM, talk,
and read CPU registers + stack when the core stops on the crash."""
import json, pathlib, shutil, socket, struct, sys, time
sys.dont_write_bytecode = True
ROOT = pathlib.Path('/root/claude-dev/wt-cries/Pokemon Game')
sys.path.insert(0, str(ROOT/'scripts/coordination'))
import codex_cry_gameplay as w
from codex_cry_gameplay import driver, emu, game, mapdata, play

profile, scratch, out = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
bps = [b for b in sys.argv[4:] if b not in ('poll', 'w')]
engine = ROOT/'engine'
src = engine/f'pokeemerald-cries-{profile}-release.gba' if not profile.endswith('.gba') else None
if profile.endswith('.gba'):
    src = pathlib.Path(profile)
    engine = src.parent
elif profile == 'main':
    engine = pathlib.Path('/root/claude-dev/wt-mainrel/Pokemon Game/engine')
    src = engine/'pokeemerald-release.gba'
rom = scratch/'game.gba'
shutil.copyfile(src, rom)
info = emu.load_build_info(src.with_suffix('.elf'), engine, scratch/'symbol-cache')
info['symbols'] = w.lto_aliases(info['symbols'])
out.mkdir(parents=True, exist_ok=True)
e = emu.Emulator(rom, out)
g = game.Game(e, info)
d = driver.Driver(e, g, mapdata.World(engine), out/'events.jsonl')
d.moves = game.MoveTable(rom, info)
g.map_names = d.w.by_num
by_addr = {}
for a, n in info['all_symbols']:
    by_addr.setdefault(a & ~1, n)
def near(addr):
    a0 = addr & ~1
    tag = ''
    if 0x0A000000 <= a0 < 0x0C000000:
        a0 -= 0x2000000; tag = '[mirror]'
    best = max((a for a in by_addr if a <= a0), default=None)
    return f'{tag}{by_addr[best]}+0x{a0 - best:x}' if best is not None and a0 - best < 0x4000 else '?'
try:
    play.boot(d, False)
    d.travel_to('MAP_ALDERFIELD')
    d.walk_path('MAP_ALDERFIELD', {(17, 13)})
    d.settle()
    e.capture('at-door')
    def key(k, hold, after):
        d.e.key(k, True); time.sleep(hold); d.e.key(k, False); time.sleep(after)
    key('UP', 6.0, 0.5)
    e.capture('at-counter')
    gdb = g.gdb
    gdb.halt()
    early = [b for b in bps if not b.startswith('late:')]
    late = [b[5:] for b in bps if b.startswith('late:')]
    def arm(names):
        for name in names:
            if name.startswith('watch:'):
                a = int(name[6:], 16)
                for kind in (('Z2',) if 'w' in sys.argv[-1] else ('Z3', 'Z4')):
                    print('watch', kind, hex(a), gdb._cmd(f'{kind},{a:x},4'), flush=True)
                continue
            addr = int(name, 16) if name.startswith('0x') else info['symbols'][name] & ~1
            for a in (addr, addr + 0x2000000):
                print('bp', name, hex(a), gdb._cmd(f'Z1,{a:x},2'), flush=True)
    arm(early)
    armed_late = False
    gdb.resume()
    hits = []
    t_end = time.monotonic() + 60
    gdb.sock.settimeout(0.4)
    presses = 0
    while time.monotonic() < t_end and len(hits) < 80:
        if presses < 30:
            d.e.key('A', True); time.sleep(0.1); d.e.key('A', False)
            presses += 1
        try:
            stop = gdb._packet()
        except socket.timeout:
            continue
        except Exception as exc:
            print('socket', repr(exc), flush=True); break
        gdb.running = False
        gdb.sock.settimeout(10)
        try:
            regs = gdb._cmd('g')
        except Exception as exc:
            print('regs failed', repr(exc), stop, flush=True); break
        r = [struct.unpack('<I', bytes.fromhex(regs[k*8:(k+1)*8]))[0] for k in range(16)]
        cpsr = regs[16*8+ 0: 16*8+8]
        try:
            words = struct.unpack('<64I', gdb.read(r[13], 0x100))
        except Exception as exc:
            words = ()
        rec = dict(n=len(hits), stop=stop, pc=hex(r[15]), pc_sym=near(r[15]), lr=hex(r[14]), lr_sym=near(r[14]),
                   regs=[hex(x) for x in r], tail=regs[128:],
                   stack=[(hex(x), near(x)) for x in words if 0x08000000 <= x < 0x0A000000 or 0x03000000 <= x < 0x03008000])
        print(json.dumps(rec), flush=True)
        hits.append(rec)
        if r[15] < 0x02000000 or r[15] >= 0x0C000000 or not rec['pc_sym'] or rec['pc_sym'] == '?':
            break
        if rec['pc_sym'].startswith('HealPlayerParty') and 'poll' in sys.argv[-1]:
            gdb.resume()
            gdb.sock.settimeout(5)
            t_stop = time.monotonic() + 40
            while time.monotonic() < t_stop:
                try:
                    hw = g.stack_high_water()
                except Exception as exc:
                    print('poll stopped', repr(exc), flush=True)
                    break
                print('STACK', round(time.monotonic(), 2), hw, flush=True)
                d.e.key('A', True); time.sleep(0.1); d.e.key('A', False); time.sleep(0.2)
            break
        if r[15] == 0x823e92e:
            # Fanfare over, BGM about to continue: single-step to the crash.
            import collections
            ring = collections.deque(maxlen=400)
            gdb.sock.settimeout(5)
            t_stop = time.monotonic() + 240
            steps = 0
            last_ok = None
            while time.monotonic() < t_stop:
                try:
                    st = gdb._cmd('s')
                    rg = gdb._cmd('p0f')
                except Exception as exc:
                    print('step failed', repr(exc), steps, flush=True)
                    break
                pc = struct.unpack('<I', bytes.fromhex(rg[:8]))[0]
                ring.append(pc)
                steps += 1
                if pc < 0x02000000 or pc >= 0x0C000000 or (0x03008000 <= pc < 0x08000000):
                    print('BAD PC', hex(pc), 'after', steps, flush=True)
                    break
            print('steps', steps, flush=True)
            uniq = []
            for pc in ring:
                if not uniq or uniq[-1][0] != near(pc).split('+')[0]:
                    uniq.append([near(pc).split('+')[0], pc])
            print('TRACE', json.dumps([(n, hex(p), near(p)) for n, p in uniq[-60:]]), flush=True)
            print('LAST', json.dumps([(hex(p), near(p)) for p in list(ring)[-40:]]), flush=True)
            break
        if not armed_late and rec['pc_sym'].startswith('HealPlayerParty'):
            arm(late)
            armed_late = True
        gdb.resume()
        gdb.sock.settimeout(0.4)
    (out/'stops.json').write_text(json.dumps(hits, indent=1))
finally:
    e.close()
