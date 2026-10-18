"""Sandgem Town + Pokemon Center 1F acceptance run (real mGBA, controller input,
read-only GDB observation). Modes:
  damage         Averon save -> walk out -> one real wild battle -> SAVE (hurt party)
  town           (DEV continue-warp fixture save) -> Sandgem checklist -> heal -> SAVE inside the Center
  continue-pc    fresh CONTINUE must equal the inside save -> exit -> SAVE outside
  continue-town  fresh CONTINUE must equal the outside save
usage: sandgem_qa.py ENGINE ROM BUILD(normal|release) SCRATCH OUT MODE [EXPECT_SAVED_JSON]
"""
import json, pathlib, shutil, sys, time
sys.dont_write_bytecode = True
engine = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(engine.parent / 'scripts/coordination'))
import codex_cry_gameplay as w
from codex_cry_gameplay import driver, emu, game, mapdata, play

rom_source, build = pathlib.Path(sys.argv[2]).resolve(), sys.argv[3]
scratch, out, mode = pathlib.Path(sys.argv[4]).resolve(), pathlib.Path(sys.argv[5]).resolve(), sys.argv[6]
expect = pathlib.Path(sys.argv[7]).resolve() if len(sys.argv) > 7 else None
if out.exists() and any(out.iterdir()):
    sys.exit('OUT must be new or empty')
out.mkdir(parents=True, exist_ok=True)
rom = scratch / 'game.gba'
shutil.copyfile(rom_source, rom)
flash = rom.with_suffix('.sav')
info = emu.load_build_info(rom_source.with_suffix('.elf'), engine, scratch / 'symbol-cache')
info['symbols'] = w.lto_aliases(info['symbols'])
sizes = w.chunk_sizes(*w.save_struct_sizes(engine, scratch / 'save-sizes', 'off', release=build == 'release'))
result = dict(mode=mode, build=build, rom_sha256=play.sha256(rom), elf_sha256=play.sha256(rom_source.with_suffix('.elf')),
              save_before=play.sha256(flash) if flash.exists() else None, checks=[])
e = emu.Emulator(rom, out, audio=False)
g = game.Game(e, info)
w.use_source_function_names(g)
d = driver.Driver(e, g, mapdata.World(engine), out / 'events.jsonl')
d.moves = game.MoveTable(rom, info)
g.map_names = d.w.by_num
TOWN, PC = 'MAP_SANDGEM_TOWN', 'MAP_SANDGEM_TOWN_POKEMON_CENTER_1F'


def check(name, ok, **detail):
    result['checks'].append(dict(name=name, ok=bool(ok), **detail))
    d.log('sandgem-check', name=name, ok=bool(ok), **detail)


def wait_map(dest, tries=30):
    for _ in range(tries):
        time.sleep(0.25)
        if d.here()[0] == dest and d.field_ready(d.state()):
            return True
    return False


def blocked(target, direction, label):
    d.walk_path(TOWN, {target})
    before = d.here()
    d.e.tap(direction, hold=0.35, after=0.4)
    after = d.here()
    d.shot(label)
    check(f'{label} blocks the player', after == before and before[1] == target, before=before, after=after)


def follower_visible(label):
    obs = play.observe(d, label)
    f = obs.get('follower') or {}
    check(f'follower visible ({label})', bool(f) and not f.get('invisible'), follower=f)


def hp(party):
    return [(m['species'], m['hp'], m['maxhp']) for m in party]


try:
    play.boot(d, False)
    if expect:
        w.check_continue(d, expect)
        check('fresh CONTINUE restores the saved state', True, at=d.here())
    if mode == 'damage':
        d.walk_path(d.here()[0], {(7, 8)})
        d.e.tap('DOWN', hold=0.25, after=1.5)
        wait_map('MAP_ALDERFIELD')
        play.grind_until(d, lambda d, s: any(m['hp'] < m['maxhp'] for m in s.party))
        check('party hurt in a real wild battle', any(m['hp'] < m['maxhp'] for m in d.state().party), party=hp(d.state().party))
        w.release_save(d, 'hurt', sizes, flash)
    elif mode == 'town':
        ok = wait_map(TOWN)
        d.shot('arrived-sandgem')
        check('DEV continue-warp lands in Sandgem', ok and d.here()[0] == TOWN, at=d.here())
        hurt = hp(d.state().party)
        check('party still hurt on arrival (so healing is meaningful)', any(h < m for _, h, m in hurt), party=hurt)
        d.e.tap('DOWN', hold=0.2, after=0.5)
        d.e.tap('UP', hold=0.2, after=0.8)
        follower_visible('arrival')
        # Walk the original roads end to end; every exit stays closed until its route exists.
        blocked((0, 11), 'LEFT', 'west-edge-route-201')
        blocked((21, 0), 'UP', 'north-edge-route-202')
        d.walk_path(TOWN, {(10, 20)})
        d.shot('south-road')
        blocked((21, 27), 'DOWN', 'south-edge-route-219')
        blocked((4, 16), 'LEFT', 'forest-wall')
        blocked((7, 19), 'UP', 'house-wall')
        blocked((25, 10), 'UP', 'mart-door-without-interior')
        check('still in the field after the closed Mart door', d.field_ready(d.state()) and d.here()[0] == TOWN, at=d.here())
        d.walk_path(TOWN, {(23, 17)})
        d.e.tap('UP', hold=0.15, after=0.3)
        d.e.tap('A', after=0.6)
        d.shot('talk-fisherman')
        s = d.clear_text()
        check('talking to a townsperson returns control', d.field_ready(s))
        d.walk_path(TOWN, {(19, 10)})
        d.e.tap('UP', hold=0.15, after=0.3)
        d.e.tap('A', after=0.6)
        d.shot('town-sign')
        s = d.clear_text()
        check('reading the town sign returns control', d.field_ready(s))
        # Pokemon Center: door in, heal, save inside.
        d.walk_path(TOWN, {(15, 10)})
        d.e.tap('UP', hold=0.3, after=1.5)
        ok = wait_map(PC)
        d.shot('inside-pokemon-center')
        check('Pokemon Center door warp in', ok, at=d.here())
        d.walk_path(PC, {(7, 4)})
        for attempt in range(4):
            d.e.tap('UP', hold=0.15 + 0.05 * attempt, after=0.4)
            d.e.tap('A', after=0.6)
            s = d.state()
            if s.locked or not d.field_ready(s):
                break
            d.log('nurse-retry', attempt=attempt)
        check('nurse conversation starts', s.locked or not d.field_ready(s), attempts=attempt + 1)
        s = d.clear_text()
        d.shot('healed')
        check('nurse heals the hurt party', all(h == m for _, h, m in hp(s.party)), before=hurt, after=hp(s.party))
        d.e.tap('START', after=0.8)
        d.shot('start-menu')
        d.e.tap('B', after=0.6)
        check('Start menu opens and returns to the field', d.field_ready(d.state()))
        w.release_save(d, 'inside-pc', sizes, flash)
        check('SAVE inside the Pokemon Center', True, at=d.here())
    elif mode == 'continue-pc':
        check('CONTINUE resumes inside the Pokemon Center', d.here()[0] == PC, at=d.here())
        d.walk_path(PC, {(7, 8)})
        for _ in range(4):
            d.e.tap('DOWN', hold=0.25, after=0.8)
            if wait_map(TOWN, 10):
                break
        check('exit mat back out to the Pokemon Center door', d.here() == (TOWN, (15, 10)), at=d.here())
        d.e.tap('DOWN', hold=0.2, after=0.5)
        d.e.tap('DOWN', hold=0.2, after=0.8)
        follower_visible('after-door-round-trip')
        d.walk_path(TOWN, {(11, 15)})
        d.shot('outside-before-save')
        w.release_save(d, 'outside', sizes, flash)
        check('SAVE outside in Sandgem', True, at=d.here())
    elif mode == 'continue-town':
        check('CONTINUE resumes outside in Sandgem', d.here()[0] == TOWN, at=d.here())
        follower_visible('continued')
    result['alive'] = True
except BaseException as exc:
    result['alive'] = False
    result['error'] = repr(exc)
    try:
        e.capture('error')
    except Exception:
        pass
    raise
finally:
    try:
        e.close()
    except Exception:
        pass
    saves = sorted(out.glob('saved-*.json'))
    if saves:
        before = json.loads(saves[0].read_text())['flash_before']
        result['flash_problems'] = w.flash_verdict(before, w.flash_slots(w.read_flash(flash), sizes), len(saves))
    result['save_after'] = play.sha256(flash) if flash.exists() else None
    (out / 'result.json').write_text(json.dumps(result, indent=1) + '\n')
