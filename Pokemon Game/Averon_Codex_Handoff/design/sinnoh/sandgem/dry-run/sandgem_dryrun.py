"""Scratch DRY RUN (not committed): play the #128 Sandgem candidate built in a
local scratch tree. DEV entry: Averon's Alderfield clinic exit was redirected
to Sandgem's door in that scratch tree only. Real controller input; read-only
GDB observation. Writes evidence to OUT. Second invocation with --continue
checks a fresh-process CONTINUE against the saved state."""
import json, pathlib, shutil, sys, time
sys.dont_write_bytecode = True
ROOT = pathlib.Path('/root/claude-dev/wt-sandgem-dry/Pokemon Game')
sys.path.insert(0, str(ROOT / 'scripts/coordination'))
import codex_cry_gameplay as w
from codex_cry_gameplay import driver, emu, game, mapdata, play

engine, scratch, out = ROOT / 'engine', pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
continue_from = pathlib.Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else None
rom_source = engine / 'pokeemerald.gba'
rom = scratch / 'game.gba'
shutil.copyfile(rom_source, rom)
info = emu.load_build_info(rom_source.with_suffix('.elf'), engine, scratch / 'symbol-cache')
info['symbols'] = w.lto_aliases(info['symbols'])
sizes = w.chunk_sizes(*w.save_struct_sizes(engine, scratch / 'save-sizes', 'on', release=False))
out.mkdir(parents=True, exist_ok=True)
result = dict(rom_sha256=play.sha256(rom), checks=[], dev_fixture='Alderfield clinic exit redirected to MAP_SANDGEM_TOWN (scratch only)')
e = emu.Emulator(rom, out)
g = game.Game(e, info)
w.use_source_function_names(g)
d = driver.Driver(e, g, mapdata.World(engine), out / 'events.jsonl')
d.moves = game.MoveTable(rom, info)
g.map_names = d.w.by_num


def check(name, ok, **detail):
    result['checks'].append(dict(name=name, ok=bool(ok), **detail))
    d.log('dry-check', name=name, ok=bool(ok), **detail)


def try_step(direction, label):
    """Hold a direction from the current tile; report whether the player moved."""
    before = d.here()
    d.e.tap(direction, hold=0.35, after=0.4)
    after = d.here()
    d.shot(label)
    return before, after


def exit_by_mat(dest):
    """Exit mats (MB_SOUTH_ARROW_WARP) warp when DOWN is pressed while standing on them."""
    d.walk_path(d.here()[0], {(7, 8)})
    for _ in range(4):
        d.e.tap('DOWN', hold=0.25, after=0.8)
        for _ in range(15):
            time.sleep(0.2)
            if d.here()[0] == dest and d.field_ready(d.state()):
                return
    raise driver.Stuck(f'exit mat did not lead to {dest}: {d.here()}')


try:
    play.boot(d, False)
    if continue_from:
        w.check_continue(d, continue_from)
        mid, pos = d.here()
        check('fresh CONTINUE restores the Sandgem save', mid == 'MAP_SANDGEM_TOWN', map=mid, pos=pos)
        result['alive'] = True
        raise SystemExit(0)
    # Leave the Averon clinic: its exit is redirected to Sandgem's door.
    exit_by_mat('MAP_SANDGEM_TOWN')
    mid, pos = d.here()
    d.shot('arrived-sandgem')
    check('door warp into Sandgem', mid == 'MAP_SANDGEM_TOWN', map=mid, pos=pos)
    # Collision and edges: west exit edge, north exit edge, sea at the corridor, a house wall.
    d.walk_path('MAP_SANDGEM_TOWN', {(0, 13)})
    before, after = try_step('LEFT', 'west-edge')
    check('west edge closed (no Route 201 yet)', after == before, before=before, after=after)
    d.walk_path('MAP_SANDGEM_TOWN', {(15, 0)})
    before, after = try_step('UP', 'north-edge')
    check('north edge closed (no Route 202 yet)', after == before, before=before, after=after)
    d.walk_path('MAP_SANDGEM_TOWN', {(13, 28)})
    before, after = try_step('LEFT', 'sea-shore')
    check('sea blocks walking without Surf', after == before, before=before, after=after)
    d.walk_path('MAP_SANDGEM_TOWN', {(24, 16)})
    before, after = try_step('UP', 'house-wall')
    check('house A wall is solid', after == before, before=before, after=after)
    # Pokemon Center: door in, heal, door out.
    d.walk_path('MAP_SANDGEM_TOWN', {(6, 12)})
    d.e.tap('UP', hold=0.3, after=1.5)
    for _ in range(20):
        time.sleep(0.3)
        mid, pos = d.here()
        if mid == 'MAP_SANDGEM_TOWN_POKEMON_CENTER_1F' and d.field_ready(d.state()):
            break
    mid, pos = d.here()
    d.shot('inside-pokemon-center')
    check('Pokemon Center door warp in', mid == 'MAP_SANDGEM_TOWN_POKEMON_CENTER_1F', map=mid, pos=pos)
    d.walk_path(mid, {(7, 4)})
    d.e.tap('UP', hold=0.05, after=0.3)
    d.e.tap('A', after=0.6)
    s = d.clear_text()
    party = s.party
    check('nurse heals the party', all(m['hp'] == m['maxhp'] for m in party), party=[(m['species'], m['hp'], m['maxhp']) for m in party])
    d.shot('healed')
    exit_by_mat('MAP_SANDGEM_TOWN')
    mid, pos = d.here()
    d.shot('back-outside')
    check('Pokemon Center exit back to Sandgem door', mid == 'MAP_SANDGEM_TOWN' and pos == (6, 12), map=mid, pos=pos)
    d.e.tap('DOWN', hold=0.25, after=0.5)
    d.e.tap('DOWN', hold=0.25, after=0.8)
    obs = play.observe(d, 'sandgem-outside')
    follower = obs.get('follower') or {}
    check('follower visible after the door round trip and two steps',
          bool(follower) and not follower.get('invisible'), follower=follower, pos=d.here()[1])
    # Start menu opens and closes.
    d.e.tap('START', after=0.8)
    d.shot('start-menu')
    d.e.tap('B', after=0.6)
    check('start menu returns to field', d.field_ready(d.state()))
    w.release_save(d, 'sandgem', sizes, rom.with_suffix('.sav'))
    check('save success dialog in Sandgem', True)
    result['alive'] = True
except SystemExit:
    pass
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
    if not continue_from:
        before = json.loads((out / 'saved-sandgem.json').read_text())['flash_before'] if (out / 'saved-sandgem.json').exists() else None
        if before is not None:
            result['flash'] = w.flash_verdict(before, w.flash_slots(w.read_flash(rom.with_suffix('.sav')), sizes))
    (out / 'result.json').write_text(json.dumps(result, indent=1) + '\n')
