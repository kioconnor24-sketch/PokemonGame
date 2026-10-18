#!/usr/bin/env python3
"""Play an exact cry-profile build (RELEASE or normal) with the existing read-only driver.

No memory/save writes or cheats. Uses ordinary controller input in graphical
mGBA. New flash saves and captures stay in a scratch directory. Reuses Claude's
driver without editing its files. Human listening and Delta remain separate.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode = True
DRIVER = Path(__file__).resolve().parents[1]/'claude_play'
sys.path.insert(0, str(DRIVER))
import driver
import emu
import game
import mapdata
import run as play


def lto_aliases(symbols):
    """Use only unambiguous ELF-provided names, never guessed addresses."""
    result = dict(symbols)
    candidates = {}
    for name, address in symbols.items():
        match = re.fullmatch(r'(.+)\.lto_priv\.[0-9]+', name)
        if match:
            candidates.setdefault(match[1], set()).add(address)
    for name, addresses in candidates.items():
        if name not in result and len(addresses) == 1:
            result[name] = addresses.pop()
    return result


# --- RELEASE-safe save verification ------------------------------------------
# RELEASE/LTO drops stores to gSaveAttemptStatus (production never reads it), so
# the normal driver's status check reads 0 after a good save. Instead require all
# of: the game's own success dialog callback (SaveDoSaveCallback only selects it
# when TrySavingData returned SAVE_STATUS_OK, start_menu.c), a complete flash
# slot newer than before, and a fresh-process CONTINUE that restores the state.
SECTOR_SIZE = 0x1000
SECTOR_DATA_SIZE = 3968
SECTORS_PER_SLOT = 14
SECTOR_SIGNATURE = 0x08012025
SAVE_SIZE_TYPES = ('SaveBlock2', 'SaveBlock1', 'PokemonStorage')
RESTORED_KEYS = ('map', 'mapGroup', 'mapNum', 'x', 'y', 'party', 'flags', 'money',
                 'pokeBalls', 'berries')


def base_name(name):
    """SaveSuccessCallback.lto_priv.0 / .constprop.0 / .isra.0 -> SaveSuccessCallback."""
    return re.sub(r'(\.(lto_priv|constprop|isra|part|cold)\.[0-9]+)+$', '', name)


def save_struct_sizes(engine, workdir, profile, release=True):
    """sizeof() of each saved block, from the game's own compiler and headers."""
    workdir.mkdir(parents=True, exist_ok=True)
    src, obj = workdir/'save_sizes.c', workdir/'save_sizes.o'
    src.write_text('\n'.join(['#include "global.h"', '#include "pokemon_storage_system.h"',
                              '#define P(n, v) asm volatile(".globl AVSIZE_" #n "\\n.equ AVSIZE_" #n ", %c0" :: "i"(v))',
                              'void AvSizes(void)', '{']
                             + [f'    P({name}, sizeof(struct {name}));' for name in SAVE_SIZE_TYPES]
                             + ['}', '']))
    subprocess.run(['arm-none-eabi-gcc', '-mthumb', '-mthumb-interwork', '-O2', '-mabi=apcs-gnu',
                    '-mtune=arm7tdmi', '-march=armv4t', '-std=gnu17', '-iquote', 'include',
                    '-I', 'tools/agbcc/include', '-DMODERN=1', '-DTESTING=0', '-DEMERALD']
                   + (['-DRELEASE'] if release else [])  # as the build under test was compiled
                   + [f"-DP_CRIES_ENABLED={'TRUE' if profile == 'on' else 'FALSE'}",
                      '-c', str(src), '-o', str(obj)], cwd=engine, check=True)
    found = {}
    for line in subprocess.check_output(['arm-none-eabi-nm', str(obj)], text=True).splitlines():
        match = re.fullmatch(r'([0-9a-f]+) A AVSIZE_(\w+)', line)
        if match:
            found[match[2]] = int(match[1], 16)
    return [found[name] for name in SAVE_SIZE_TYPES]


def chunk_sizes(sb2, sb1, storage):
    """Bytes checksummed in each sector id (save.c SAVEBLOCK_CHUNK)."""
    def chunks(size, count):
        return [min(size - n*SECTOR_DATA_SIZE, SECTOR_DATA_SIZE) if size >= n*SECTOR_DATA_SIZE else 0
                for n in range(count)]
    return chunks(sb2, 1) + chunks(sb1, 4) + chunks(storage, 9)


def sector_checksum(data, size):
    total = sum(struct.unpack_from(f'<{size // 4}I', data)) & 0xFFFFFFFF
    return ((total >> 16) + total) & 0xFFFF


def flash_slots(image, sizes):
    """Each save slot as the loader would judge it: empty, valid or invalid."""
    slots = []
    for slot in range(2):
        seen, problems, counters, signed = {}, [], set(), False
        for index in range(SECTORS_PER_SLOT):
            offset = (slot*SECTORS_PER_SLOT + index)*SECTOR_SIZE
            sector = image[offset:offset + SECTOR_SIZE]
            if len(sector) < SECTOR_SIZE:
                problems.append(f'sector {index} missing from image')
                continue
            sid, check, signature, counter = struct.unpack_from('<HHII', sector, SECTOR_SIZE - 12)
            if signature != SECTOR_SIGNATURE:
                continue
            signed = True
            if sid >= SECTORS_PER_SLOT:
                problems.append(f'sector {index} has id {sid}')
            elif sid in seen:
                problems.append(f'id {sid} appears twice')
            elif sector_checksum(sector, sizes[sid]) != check:
                problems.append(f'id {sid} checksum mismatch')
            else:
                seen[sid] = counter
                counters.add(counter)
        if not signed and not problems:
            slots.append(dict(status='empty'))
            continue
        missing = sorted(set(range(SECTORS_PER_SLOT)) - set(seen))
        if missing:
            problems.append(f'missing ids {missing}')
        if len(counters) > 1:
            problems.append(f'mixed counters {sorted(counters)}')
        slots.append(dict(status='invalid' if problems else 'valid', problems=problems,
                          counter=max(counters) if counters else None))
    return slots


def newest_valid_counter(slots):
    counters = [slot['counter'] for slot in slots if slot['status'] == 'valid']
    return max(counters) if counters else None


def flash_verdict(before, after, saves=1):
    """After `saves` saves, the newest valid slot must be at least that many
    counters newer than the newest valid slot before the first of them."""
    problems = [f'slot {i}: {"; ".join(slot["problems"])}' for i, slot in enumerate(after)
                if slot['status'] == 'invalid']
    new, old = newest_valid_counter(after), newest_valid_counter(before)
    if new is None:
        problems.append('no valid save slot')
    elif old is not None and new < old + saves:
        problems.append(f'newest valid counter {new} is not {saves} newer than {old}')
    return problems


def save_dialog_verdict(callbacks):
    """Problems with the observed sSaveDialogCallback sequence (base names)."""
    names = {base_name(name) for name in callbacks}
    problems = []
    if names & {'SaveErrorCallback', 'SaveReturnErrorCallback'}:
        problems.append('the game showed its save error dialog')
    if not names & {'SaveSuccessCallback', 'SaveReturnSuccessCallback'}:
        problems.append('the save success dialog was never observed')
    return problems


def restored_problems(saved, restored):
    """Fields of a fresh CONTINUE that differ from the state at SAVE."""
    # Compare as stored: the saved side went through JSON (tuples became lists).
    restored = json.loads(json.dumps(restored))
    problems = [] if restored.get('cb2') == 'CB2_Overworld' else [f"not in the overworld ({restored.get('cb2')})"]
    for key in RESTORED_KEYS:
        if saved.get(key) != restored.get(key):
            problems.append(f'{key}: saved {saved.get(key)!r}, continued {restored.get(key)!r}')
    return problems


def read_flash(path):
    return path.read_bytes() if path.exists() else b''


def release_save(d, label, sizes, flash_path):
    """Start -> SAVE -> YES with ordinary input; verify without gSaveAttemptStatus."""
    g, gd, sym = d.g, d.g.gdb, d.g.sym
    d.settle()
    saved = g.observation()
    before = flash_slots(read_flash(flash_path), sizes)
    d.e.tap('START', after=0.8)
    for _ in range(12):
        count = gd.read(sym['sNumStartMenuActions'], 1)[0]
        cursor = gd.read(sym['sStartMenuCursorPos'], 1)[0]
        actions = list(gd.read(sym['sCurrentStartMenuActions'], 9))[:count]
        if count and actions[cursor] == 5:  # MENU_ACTION_SAVE
            break
        d.e.tap('DOWN', after=0.25)
    else:
        raise driver.Stuck(f'no SAVE entry in start menu {actions}')
    d.e.tap('A', after=2.5)
    d.shot(f'save-confirm-{label}')
    callbacks = []
    for step in range(40):
        # Poll between presses: the success callback lasts only while its text prints.
        for _ in range(12):
            name = g.func_name(struct.unpack('<I', gd.read(sym['sSaveDialogCallback'], 4))[0])
            if not callbacks or callbacks[-1] != name:
                callbacks.append(name)
            time.sleep(0.05)
        if d.field_ready(d.state()):
            break
        d.e.tap('A', after=0.1)
        if step < 8:
            d.shot(f'save-step-{label}-{step + 1:02d}')
    d.shot(f'saved-{label}')
    problems = save_dialog_verdict(callbacks)
    d.log('release-save', label=label, callbacks=callbacks, problems=problems)
    (d.e.outdir/f'saved-{label}.json').write_text(json.dumps(
        dict(label=label, state=saved, callbacks=callbacks, flash_before=before), indent=1)+'\n')
    if problems:
        raise driver.Stuck(f'save {label}: {problems}')
    return saved


def check_continue(d, expected_path):
    """After a CONTINUE boot, the overworld must match the state at SAVE."""
    saved = json.loads(expected_path.read_text())['state']
    restored = d.g.observation()
    d.shot('continued')
    problems = restored_problems(saved, restored)
    (d.e.outdir/'continue-check.json').write_text(json.dumps(
        dict(expected=str(expected_path), restored=restored, problems=problems), indent=1)+'\n')
    d.log('continue-check', problems=problems)
    if problems:
        raise driver.Stuck(f'continue did not restore the saved state: {problems}')


# --- Silent-cry gameplay paths -------------------------------------------------
OPPOSITE = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}


def active_tasks(g):
    """Base names of the active task functions (read-only)."""
    size, flag = g.off['task.size'], g.off['task.isActive']
    raw = g.gdb.read(g.sym['gTasks'], 16*size)
    return [base_name(g.func_name(struct.unpack_from('<I', raw, i*size)[0]))
            for i in range(16) if raw[i*size + flag]]


def wait_task(d, names, timeout=8.0):
    """Wait until one of `names` is an active task; returns it or None."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        found = set(active_tasks(d.g)) & set(names)
        if found:
            return found.pop()
        time.sleep(0.1)
    return None


def talk_follower(d):
    """Face the follower and press A: EventScript_Follower runs playfirstmoncry
    (and waitmoncry for some reactions), the silent-cry script path."""
    d.settle()
    mid, pos = d.here()
    m = d.w.map(mid)
    for _ in range(3):
        # One step puts the follower on the tile just left (and shows it after a warp).
        for direction, (dx, dy) in mapdata.DIRS.items():
            if m.walkable(pos[0] + dx, pos[1] + dy):
                break
        else:
            raise driver.Stuck(f'no free tile next to {pos} on {mid}')
        d.step(direction)
        d.settle()
        follower = d.g.follower()
        d.log('follower-before-talk', follower=follower, pos=d.here()[1])
        back = OPPOSITE[direction]
        for attempt in range(4):
            here = d.here()
            d.e.tap(driver.KEY[back], hold=0.03 + 0.03*attempt, after=0.3)
            if d.here() != here:
                break  # walked instead of turning; step again and retry
            d.e.tap('A', after=0.4)
            s = d.state()
            if s.locked or s.cb2 != 'CB2_Overworld':
                d.shot('follower-talk')
                tasks = active_tasks(d.g)
                s = d.clear_text(capture='follower-talk')
                d.log('follower-talked', tasks=tasks, field_ready=d.field_ready(s), follower=d.g.follower())
                if not d.field_ready(d.state()):
                    raise driver.Stuck('follower script did not return control')
                return
        mid, pos = d.here()
    raise driver.Stuck('talking to the follower started no script')


def pokedex_cry(d):
    """Pokedex entry (opening it waits on IsCryPlayingOrClearCrySongs), the CRY
    page and its replay button, then back out to the field."""
    play.open_start_menu_action(d, 0)  # MENU_ACTION_POKEDEX
    listed = wait_task(d, ['Task_HandlePokedexInput'])
    time.sleep(1.0)
    d.shot('dex-list')
    d.log('dex', step='list', tasks=active_tasks(d.g))
    if not listed:
        raise driver.Stuck(f'Pokedex list never took input: {active_tasks(d.g)}')
    for attempt in range(40):
        d.e.tap('A', after=0.3)
        info = wait_task(d, ['Task_HandleInfoScreenInput'], timeout=6.0)
        if info:
            break
        d.e.tap('DOWN', after=0.3)  # unseen entries do not open
    else:
        raise driver.Stuck('no Pokedex entry opened')
    time.sleep(0.8)
    d.shot('dex-entry')
    d.log('dex', step='entry', tasks=active_tasks(d.g), attempts=attempt)
    # The page menu opens on AREA (pokedex.c selectedScreen); CRY is next.
    pages = ['Task_HandleCryScreenInput', 'Task_HandleSizeScreenInput', 'Task_HandleAreaScreenInput']
    cry = None
    for key in ('RIGHT', 'LEFT', 'LEFT'):
        d.e.tap(key, after=0.4)
        d.e.tap('A', after=0.4)
        page = wait_task(d, pages, timeout=8.0)
        d.log('dex', step='page', key=key, page=page)
        if page == 'Task_HandleCryScreenInput':
            cry = page
            break
        if page:  # another page opened: back to the entry and move again
            d.e.tap('B', after=0.4)
            wait_task(d, ['Task_HandleInfoScreenInput'], timeout=8.0)
    time.sleep(0.8)
    d.shot('dex-cry-page')
    d.log('dex', step='cry-page', tasks=active_tasks(d.g))
    if not cry:
        raise driver.Stuck(f'CRY page never took input: {active_tasks(d.g)}')
    for n in range(3):  # replay; each press is PlayCry_NormalNoDucking
        d.e.tap('A', after=1.2)
        d.shot(f'dex-cry-replay-{n + 1}')
        if 'Task_HandleCryScreenInput' not in active_tasks(d.g):
            raise driver.Stuck(f'CRY page lost input after replay {n + 1}: {active_tasks(d.g)}')
    for _ in range(12):
        if d.field_ready(d.state()):
            break
        d.e.tap('B', after=1.0)
    else:
        raise driver.Stuck(f'Pokedex did not close: {active_tasks(d.g)}')
    d.shot('dex-closed')
    d.log('dex', step='closed')


def evolve_lead(d):
    """Wild battles until the lead gains a level; the lead must then have
    evolved through the real evolution scene (which plays the old and new
    species' cries). The driver presses A through post-battle screens; B
    would cancel the evolution. Frames of the scene are kept."""
    before = play.lead(d)
    frames = []
    snapshot = d.state

    def watched(*args, **kwargs):
        s = snapshot(*args, **kwargs)
        if 'Evolution' in (s.cb2 or '') and len(frames) < 6 and (
                not frames or time.monotonic() - frames[-1] > 1.5):
            frames.append(time.monotonic())
            d.shot(f'evolution-{len(frames)}')
        return s

    d.state = watched
    try:
        battles = play.grind_until(d, lambda d, s: play.lead(d, s)['level'] > before['level'])
    finally:
        d.state = snapshot
    after = play.lead(d)
    d.log('evolution', before=[before['species'], before['level']], after=[after['species'], after['level']],
          battles=battles, frames=len(frames))
    d.shot('evolved')
    if after['species'] == before['species'] or not frames:
        raise driver.Stuck(f'no evolution scene: {before["species"]} -> {after["species"]}, {len(frames)} frames')


EXTRA_PHASES = {'talk_follower': talk_follower, 'pokedex_cry': pokedex_cry, 'evolve_lead': evolve_lead}


def rom_name(profile, build):
    """Output of make [RELEASE=1] CRIES=<profile> (engine Makefile suffixes)."""
    return f"pokeemerald-cries-{profile}{'-release' if build == 'release' else ''}.gba"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--profile', choices=('on', 'off'), required=True)
    parser.add_argument('--build', choices=('release', 'normal'), default='release',
                        help='normal = make CRIES=<profile> (no RELEASE/LTO), same cry source')
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--new-game', action='store_true')
    parser.add_argument('--audio', action='store_true')
    parser.add_argument('--expect-saved', type=Path,
                        help='saved-<label>.json from an earlier run; CONTINUE must restore it')
    parser.add_argument('phases', nargs='*', choices=sorted(set(play.PHASES) | set(EXTRA_PHASES)))
    args = parser.parse_args()
    engine, scratch, out = args.engine.resolve(), args.scratch.resolve(), args.out.resolve()
    if engine == scratch or engine in scratch.parents:
        parser.error('scratch must be outside the engine tree')
    rom_source = engine/rom_name(args.profile, args.build)
    elf = rom_source.with_suffix('.elf')
    scratch.mkdir(parents=True, exist_ok=True)
    if out.exists() and any(out.iterdir()):
        # Driver logs append and the flash check trusts saved-checkpoint-*.json here.
        parser.error('--out must be a new or empty directory')
    out.mkdir(parents=True, exist_ok=True)
    rom = scratch/'game.gba'
    if rom.exists() and play.sha256(rom) != play.sha256(rom_source):
        parser.error('scratch ROM belongs to a different build; use a new directory')
    if args.new_game and rom.with_suffix('.sav').exists():
        parser.error('new-game refuses to overwrite an existing flash save')
    shutil.copyfile(rom_source, rom)
    info = emu.load_build_info(elf, engine, scratch/'symbol-cache')
    # Sector checksum sizes come from the game's own struct layout.
    sizes = chunk_sizes(*save_struct_sizes(engine, scratch/'save-sizes', args.profile, args.build == 'release'))
    flash_path = rom.with_suffix('.sav')
    if args.expect_saved and args.new_game:
        parser.error('--expect-saved checks a CONTINUE boot, not a new game')
    # RELEASE LTO gives shared static globals names such as
    # sLockFieldControls.lto_priv.0; the normal-build driver expects the base.
    info['symbols'] = lto_aliases(info['symbols'])
    record = dict(source_sha=play.git(engine, 'rev-parse', 'HEAD'),
                  engine_tree=play.git(engine, 'rev-parse', 'HEAD:Pokemon Game/engine'),
                  engine_status=play.git(engine, 'status', '--short', '--', '.').splitlines(),
                  driver_sha=play.git(DRIVER, 'rev-parse', 'HEAD'),
                  driver_status=play.git(DRIVER, 'status', '--short', '--', '.').splitlines(),
                  wrapper_status=play.git(Path(__file__).resolve().parent, 'status', '--short', '--',
                                          Path(__file__).name).splitlines(),
                  rom_sha256=play.sha256(rom), elf_sha256=play.sha256(elf),
                  cry_profile=args.profile, release=args.build == 'release', build=args.build,
                  phases=args.phases,
                  mgba=subprocess.check_output(['mgba', '--version'], text=True).strip(),
                  acceptance='Supporting real emulator evidence; not human listening or Delta',
                  save_before=play.sha256(flash_path) if flash_path.exists() else None,
                  save_check='success dialog callback + valid newer flash slot + fresh-process CONTINUE '
                             '(gSaveAttemptStatus is not used: RELEASE LTO removes its stores)')
    if record['engine_status'] or record['driver_status'] or record['wrapper_status']:
        parser.error('commit source before collecting publishable gameplay evidence')
    (out/'provenance-start.json').write_text(json.dumps(record, indent=2)+'\n')
    world = mapdata.World(engine)
    emulator = None
    try:
        emulator = emu.Emulator(rom, out, audio=args.audio)
        observed = game.Game(emulator, info)
        d = driver.Driver(emulator, observed, world, out/'events.jsonl')
        d.moves = game.MoveTable(rom, info)
        observed.map_names = world.by_num
        emulator.start_trace(out/'inputs.jsonl', info['symbols']['gMain']+info['offsets']['main.vblankCounter1'])
        play.boot(d, args.new_game)
        if args.expect_saved:
            check_continue(d, args.expect_saved.resolve())
            record['continue_restored'] = True
        saves = 0
        for phase in args.phases:
            if phase == 'save':
                saves += 1
                release_save(d, f'checkpoint-{saves}', sizes, flash_path)
            else:
                EXTRA_PHASES.get(phase, play.PHASES.get(phase))(d)
        record['saves'] = saves
        play.observe(d, 'end')
        record['completed'] = True
    except Exception as error:
        record['completed'] = False
        record['error'] = f'{type(error).__name__}: {error}'
        if emulator:
            try:
                emulator.capture('error')
            except Exception:
                pass
        raise
    finally:
        if emulator:
            emulator.close()
        record['source_sha_end'] = play.git(engine, 'rev-parse', 'HEAD')
        record['engine_status_end'] = play.git(engine, 'status', '--short', '--', '.').splitlines()
        record['source_unchanged'] = record['source_sha_end'] == record['source_sha'] and not record['engine_status_end']
        record['save_after'] = play.sha256(flash_path) if flash_path.exists() else None
        # The emulator has closed, so its flash file is complete.
        before = json.loads((out/'saved-checkpoint-1.json').read_text())['flash_before'] \
            if (out/'saved-checkpoint-1.json').exists() else None
        if before is not None:
            record['flash_slots'] = flash_slots(read_flash(flash_path), sizes)
            record['flash_problems'] = flash_verdict(before, record['flash_slots'],
                                                     len(list(out.glob('saved-checkpoint-*.json'))))
            if record['flash_problems']:
                record['completed'] = False
        (out/'provenance-end.json').write_text(json.dumps(record, indent=2)+'\n')
        if record.get('flash_problems'):
            raise SystemExit(f"flash check failed: {record['flash_problems']}")
        if args.audio and emulator and emulator.audio_raw and emulator.audio_raw.exists():
            report = emu.audio_report(emulator.audio_raw, out/'audio.wav')
            (out/'audio-report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
