#!/usr/bin/env python3
"""Play an exact cry-profile RELEASE image with the existing read-only driver.

No memory/save writes or cheats. Uses ordinary controller input in graphical
mGBA. New flash saves and captures stay in a scratch directory. Reuses Claude's
driver without editing its files. Human listening and Delta remain separate.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--profile', choices=('on', 'off'), required=True)
    parser.add_argument('--scratch', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--new-game', action='store_true')
    parser.add_argument('--audio', action='store_true')
    parser.add_argument('phases', nargs='*', choices=sorted(play.PHASES))
    args = parser.parse_args()
    engine, scratch, out = args.engine.resolve(), args.scratch.resolve(), args.out.resolve()
    if engine == scratch or engine in scratch.parents:
        parser.error('scratch must be outside the engine tree')
    rom_source = engine/f'pokeemerald-cries-{args.profile}-release.gba'
    elf = rom_source.with_suffix('.elf')
    scratch.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    rom = scratch/'game.gba'
    if rom.exists() and play.sha256(rom) != play.sha256(rom_source):
        parser.error('scratch ROM belongs to a different build; use a new directory')
    if args.new_game and rom.with_suffix('.sav').exists():
        parser.error('new-game refuses to overwrite an existing flash save')
    shutil.copyfile(rom_source, rom)
    info = emu.load_build_info(elf, engine, scratch/'symbol-cache')
    # RELEASE LTO gives shared static globals names such as
    # sLockFieldControls.lto_priv.0; the normal-build driver expects the base.
    info['symbols'] = lto_aliases(info['symbols'])
    record = dict(source_sha=play.git(engine, 'rev-parse', 'HEAD'),
                  engine_tree=play.git(engine, 'rev-parse', 'HEAD:Pokemon Game/engine'),
                  engine_status=play.git(engine, 'status', '--short', '--', '.').splitlines(),
                  driver_sha=play.git(DRIVER, 'rev-parse', 'HEAD'),
                  driver_status=play.git(DRIVER, 'status', '--short', '--', '.').splitlines(),
                  rom_sha256=play.sha256(rom), elf_sha256=play.sha256(elf),
                  cry_profile=args.profile, release=True, phases=args.phases,
                  mgba=subprocess.check_output(['mgba', '--version'], text=True).strip(),
                  acceptance='Supporting real emulator evidence; not human listening or Delta',
                  save_before=play.sha256(rom.with_suffix('.sav')) if rom.with_suffix('.sav').exists() else None)
    if record['engine_status'] or record['driver_status']:
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
        for phase in args.phases:
            play.PHASES[phase](d)
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
        record['save_after'] = play.sha256(rom.with_suffix('.sav')) if rom.with_suffix('.sav').exists() else None
        (out/'provenance-end.json').write_text(json.dumps(record, indent=2)+'\n')
        if args.audio and emulator and emulator.audio_raw and emulator.audio_raw.exists():
            report = emu.audio_report(emulator.audio_raw, out/'audio.wav')
            (out/'audio-report.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
