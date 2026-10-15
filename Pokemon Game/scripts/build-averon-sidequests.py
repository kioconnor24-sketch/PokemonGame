#!/usr/bin/env python3
"""Install two optional early-Averon sidequests after build-averon-coast.py.

Never call the base map generators *after* this overlay, or they will reset
those maps. This script is intentionally conservative: it rejects conflicting
flag slots, scripted NPC placements, missing maps and blocked tiles.

Does not modify battle rules, trainers, saves, or the core storyline.
"""
import argparse
import copy
import json
import struct
from pathlib import Path

# Positions are selected from the authored walking paths in the map builders.
# The layout collision bits must also be checked against the current output.
ACTORS = (
    ('Alderfield', 12, 16, 'OBJ_EVENT_GFX_WOMAN_1', 'Averon_FieldNotes_Researcher'),
    ('CoastalBluffs', 35, 7, 'OBJ_EVENT_GFX_HIKER', 'Averon_FieldNotes_Observer'),
    ('Windrow', 20, 14, 'OBJ_EVENT_GFX_GIRL_1', 'Averon_BerrySketch_Artist'),
    ('CoastalMeadow', 10, 22, 'OBJ_EVENT_GFX_LITTLE_BOY', 'Averon_BerrySketch_Observer'),
)
FLAG_SLOTS = {
    'FLAG_UNUSED_0x02A': 'FLAG_AVERON_NOTES_STARTED',
    'FLAG_UNUSED_0x02B': 'FLAG_AVERON_NOTES_RECORDED',
    'FLAG_UNUSED_0x02C': 'FLAG_AVERON_NOTES_REWARDED',
    'FLAG_UNUSED_0x02D': 'FLAG_AVERON_SKETCH_STARTED',
    'FLAG_UNUSED_0x02E': 'FLAG_AVERON_SKETCH_FOUND',
    'FLAG_UNUSED_0x02F': 'FLAG_AVERON_SKETCH_REWARDED',
}
INCLUDE = '\t.include "data/averon_optional_sidequests.inc"'


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_if_changed(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text(encoding='utf-8') != content:
        path.write_text(content, encoding='utf-8')


def walking_tiles(engine, map_data):
    layouts = load_json(engine / 'data/layouts/layouts.json')['layouts']
    by_id = {layout['id']: layout for layout in layouts}
    layout_id = map_data['layout']
    if layout_id not in by_id:
        raise ValueError(f'Missing layout: {layout_id}')
    layout = by_id[layout_id]
    width, height = layout['width'], layout['height']
    data = (engine / layout['blockdata_filepath']).read_bytes()
    if len(data) != 2 * width * height:
        raise ValueError(f'Unexpected map binary size: {layout_id}')
    return width, height, struct.unpack('<' + 'H' * (width * height), data)


def validate_actor(engine, map_data, x, y):
    width, height, tiles = walking_tiles(engine, map_data)
    if not (1 <= x < width-1 and 1 <= y < height-1):
        raise ValueError(f'Actor position out of bounds: {map_data["id"]} {x},{y}')
    if ((tiles[y * width + x] >> 10) & 3) != 0:
        raise ValueError(f'Actor on blocked tile: {map_data["id"]} {x},{y}')
    for key in ('warp_events', 'object_events', 'bg_events', 'coord_events'):
        for entry in map_data.get(key) or []:
            if entry.get('x') == x and entry.get('y') == y:
                raise ValueError(f'Actor collides with {key}: {map_data["id"]} {x},{y}')


def new_actor(map_data, x, y, graphics, script):
    events = map_data['object_events']
    if not events:
        raise ValueError(f'No existing NPC schema in map: {map_data["id"]}')
    npc = copy.deepcopy(events[0])
    npc.update(graphics_id=graphics, x=x, y=y, elevation=3,
               movement_type='MOVEMENT_TYPE_FACE_DOWN',
               movement_range_x=0, movement_range_y=0,
               trainer_type='TRAINER_TYPE_NONE', trainer_sight_or_berry_tree_id='0',
               script=script, flag='0')
    return npc


def patch_flags(source):
    result = source
    for original, replacement in FLAG_SLOTS.items():
        if replacement in result:
            # Reject a second definition of the new symbol at a different address.
            if result.count('#define ' + replacement + ' ') != 1:
                raise ValueError(f'Duplicate or malformed allocated flag: {replacement}')
            continue
        old = '#define ' + original + ' '
        if result.count(old) != 1:
            raise ValueError(f'Reserved slot unavailable: {original}')
        result = result.replace(old, '#define ' + replacement + ' ', 1)
    return result


def apply(engine, source_script):
    """Validate all prerequisites before writing any modified engine file."""
    source = source_script.read_text(encoding='utf-8')
    if 'Averon_FieldNotes_Researcher::' not in source or 'Averon_BerrySketch_Artist::' not in source:
        raise ValueError('Expected optional quest scripts are absent')
    flags_path = engine / 'include/constants/flags.h'
    event_path = engine / 'data/event_scripts.s'
    flags = patch_flags(flags_path.read_text(encoding='utf-8'))
    events = event_path.read_text(encoding='utf-8')
    # Validate every actor and map before touching any files.
    target_maps = {}
    for name, x, y, graphics, script in ACTORS:
        path = engine / 'data/maps' / name / 'map.json'
        map_data = target_maps.get(name)
        if map_data is None:
            map_data = load_json(path)
            target_maps[name] = map_data
        existing = [e for e in map_data['object_events'] if e.get('script') == script]
        if existing:
            if len(existing) != 1 or (existing[0]['x'], existing[0]['y']) != (x, y):
                raise ValueError(f'Conflicting existing quest NPC: {name}/{script}')
            continue
        validate_actor(engine, map_data, x, y)
        map_data['object_events'].append(new_actor(map_data, x, y, graphics, script))
    write_if_changed(flags_path, flags)
    write_if_changed(event_path, events if INCLUDE in events else events.rstrip() + '\n' + INCLUDE + '\n')
    write_if_changed(engine / 'data/averon_optional_sidequests.inc', source)
    for name, data in target_maps.items():
        write_if_changed(engine / 'data/maps' / name / 'map.json', json.dumps(data, indent=2) + '\n')
    return len(ACTORS)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, default=Path(__file__).resolve().parents[1] / 'engine')
    parser.add_argument('--scripts', type=Path, default=Path(__file__).with_name('averon-optional-sidequests.inc'))
    args = parser.parse_args(argv)
    try:
        n = apply(args.engine.resolve(), args.scripts.resolve())
    except (OSError, KeyError, ValueError, struct.error) as exc:
        parser.exit(2, f'Cannot install sidequests: {exc}\n')
    print(f'Installed/verified {n} optional quest NPCs and two native event chains. Build and runtime testing required.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
