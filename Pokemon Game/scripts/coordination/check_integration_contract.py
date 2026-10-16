#!/usr/bin/env python3
"""Read-only source integration contract for disposable Averon merge rehearsals.

This is a limited, positive source check. It NEVER builds a ROM, checks actual
runtime/save behavior, or grants any file handoff or merge authority.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

QUEST = 'data/averon_optional_sidequests.inc'
BATTLE = 'data/scripts/averon_scripted_battle.inc'
EVENT = 'data/event_scripts.s'
FLAG = 'include/config/battle.h'
CONST_FLAGS = 'include/constants/flags.h'
BATTLE_C = 'src/averon_scripted_battle.c'


def read(engine: Path, name: str) -> str:
    path = engine / name
    return path.read_text(encoding='utf-8', errors='replace') if path.is_file() else ''


def active_includes(event: str, target: str) -> int:
    """Ignore comments, match only actual assembler include statements."""
    pattern = r'^\s*\.include\s+"' + re.escape(target) + r'"\s*(?:@.*)?$'
    return len(re.findall(pattern, event, re.M))


def examine(engine: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    report: list[str] = []
    event = read(engine, EVENT)
    if not event:
        return [f'Missing engine/{EVENT}'], []
    quest = read(engine, QUEST)
    battle = read(engine, BATTLE)
    src = read(engine, BATTLE_C)
    battle_cfg = read(engine, FLAG)
    const_flags = read(engine, CONST_FLAGS)
    quest_n = active_includes(event, QUEST)
    battle_n = active_includes(event, BATTLE)
    has_quest = bool(quest) or bool(quest_n)
    has_battle = bool(battle) or bool(battle_n) or bool(src)

    if not has_quest and not has_battle:
        return [], ['SKIP: neither QUEST nor SCRIPTED-BATTLE integration present']

    if has_quest:
        if quest_n != 1:
            errors.append(f'QUEST registry: expected one active include of {QUEST}, got {quest_n}')
        if not quest:
            errors.append('QUEST: registered source file absent')
        for symbol in ('Averon_FieldNotes_Researcher::',
                       'Averon_BerrySketch_Artist::',
                       'Averon_BerrySketch_Tree::'):
            if symbol not in quest:
                errors.append(f'QUEST: missing established script entry {symbol}')
        if 'FLAG_AVERON_NOTES_STARTED' not in const_flags:
            errors.append('QUEST: source flag contract missing in constants/flags.h')
        report.append('QUEST source event registration and known entry points inspected')

    if has_battle:
        if battle_n != 1:
            errors.append(f'SCRIPTED-BATTLE registry: expected one active include of {BATTLE}, got {battle_n}')
        if not battle:
            errors.append('SCRIPTED-BATTLE: registered macro file absent')
        for macro in ('averon_scripted_battle', 'averon_recover_in_place', 'averon_respawn'):
            if not re.search(r'^\s*\.macro\s+' + macro + r'\b', battle, re.M):
                errors.append(f'SCRIPTED-BATTLE: missing macro {macro}')
        for native in ('AveronScriptedBattle_Begin', 'AveronScriptedBattle_Finish',
                       'AveronScriptedBattle_PrepareRespawn', 'AveronScriptedBattle_DoRespawnWarp'):
            if not re.search(r'^void\s+' + native + r'\s*\(', src, re.M):
                errors.append(f'SCRIPTED-BATTLE: missing native implementation {native}')
        binding = re.search(r'^\s*#define\s+B_FLAG_NO_WHITEOUT\s+(\S+)', battle_cfg, re.M)
        if not binding or binding.group(1) != 'FLAG_SPECIAL_FLAG_UNUSED_0x4003':
            errors.append('SCRIPTED-BATTLE: B_FLAG_NO_WHITEOUT not bound to approved RAM-only 0x4003')
        if not re.search(r'^\s*#define\s+FLAG_SPECIAL_FLAG_UNUSED_0x4003\b', const_flags, re.M):
            errors.append('SCRIPTED-BATTLE: approved special flag constant not declared')
        report.append('SCRIPTED-BATTLE source registry, macros, native definitions and flag contract inspected')

    if has_quest and has_battle:
        # Macro definitions need to precede downstream script source includes.
        if event.find(f'"{BATTLE}"') > event.find(f'"{QUEST}"'):
            errors.append('Combined registry: battle macro include follows QUEST script include')
        report.append('Both feature sources detected in combined checkout')
    return errors, report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--engine', type=Path, default=Path('Pokemon Game/engine'))
    args = parser.parse_args()
    errors, notes = examine(args.engine)
    for note in notes:
        print(note)
    for error in errors:
        print('FAIL:', error)
    if errors:
        print(f'FAIL: {len(errors)} limited source-contract defect(s)')
        return 1
    print('PASS: limited source integration contract; NOT a build, save, gameplay or merge approval')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
