#!/usr/bin/env python3
"""Read-only Emerald map preflight; does not generate maps or certify gameplay.

Checks selected maps against the current Averon source format. Run the existing
check-averon-map-registry.py separately for saved-ID pins. C declarations are
inspected, not preprocessed: a real build must prove conditional symbol linkage.
"""
import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import zlib


def positive_int(value):
    return type(value) is int and value > 0


def layout_errors(layout, blocks, border, counts, limits):
    """Validate raw geometry and referenced metatiles, with no filesystem writes."""
    errors = []
    width, height = layout.get('width'), layout.get('height')
    if not positive_int(width) or not positive_int(height):
        return ['layout dimensions must be positive integers']
    if (width + limits['pad_w']) * (height + limits['pad_h']) > limits['cells']:
        errors.append('padded layout exceeds MAX_MAP_DATA_SIZE')
    if len(blocks) != 2 * width * height:
        errors.append(f'block byte count {len(blocks)} != {2 * width * height}')
    version = layout.get('layout_version', 'emerald')
    bw, bh = (layout.get('border_width'), layout.get('border_height')) if version == 'frlg' else (2, 2)
    if not positive_int(bw) or not positive_int(bh) or len(border) != 2 * bw * bh:
        errors.append('border byte count does not match its dimensions')
    split = limits['primary_frlg'] if version == 'frlg' else limits['primary']
    capacities = (split, limits['total'] - split)
    for slot, (metatiles, attributes) in enumerate(counts):
        if metatiles <= 0 or metatiles > capacities[slot] or attributes != metatiles:
            errors.append(f'tileset {slot} metatile/attribute counts {metatiles}/{attributes} '
                          f'do not fit capacity {capacities[slot]}')
    for label, data in (('blocks', blocks), ('border', border)):
        if len(data) % 2:
            errors.append(f'{label} has an incomplete u16 cell')
            continue
        used = {v[0] & limits['mask'] for v in struct.iter_unpack('<H', data)}
        missing = sorted(v for v in used
                         if v >= limits['total'] or (v if v < split else v - split)
                         >= min(counts[int(v >= split)]))
        if missing:
            errors.append(f'{label} references undefined metatiles: {missing[:16]}')
    return errors


def source_limits(fieldmap, global_fieldmap):
    def constant(text, name):
        found = re.search(r'^#define\s+' + name + r'\s+(0x[0-9A-Fa-f]+|\d+)\b', text, re.M)
        if not found:
            raise ValueError(f'Cannot read source contract {name}')
        return int(found[1], 0)
    # Fail closed if the padded-buffer formula changes rather than guessing.
    compact = re.sub(r'\s+', '', fieldmap)
    if '#defineMAP_OFFSET_W(MAP_OFFSET*2+1)' not in compact or '#defineMAP_OFFSET_H(MAP_OFFSET*2)' not in compact:
        raise ValueError('Map buffer padding contract changed; review preflight')
    offset = constant(fieldmap, 'MAP_OFFSET')
    if constant(fieldmap, 'NUM_TILES_PER_METATILE') != 8:
        raise ValueError('Metatile record format changed; review preflight')
    return {'cells': constant(fieldmap, 'MAX_MAP_DATA_SIZE'),
            'pad_w': offset * 2 + 1, 'pad_h': offset * 2,
            'primary': constant(fieldmap, 'NUM_METATILES_IN_PRIMARY'),
            'primary_frlg': constant(fieldmap, 'NUM_METATILES_IN_PRIMARY_FRLG'),
            'total': constant(fieldmap, 'NUM_METATILES_TOTAL'),
            'tile_primary': constant(fieldmap, 'NUM_TILES_IN_PRIMARY'),
            'tile_primary_frlg': constant(fieldmap, 'NUM_TILES_IN_PRIMARY_FRLG'),
            'tile_total': constant(fieldmap, 'NUM_TILES_TOTAL'),
            'mask': constant(global_fieldmap, 'MAPGRID_METATILE_ID_MASK')}


def verify_generator(source):
    # This checker models these exact filters, not arbitrary mapjson forks.
    compact = re.sub(r'\s+', '', source)
    for pattern in ('version=="emerald"&&region!="REGION_HOENN"',
                    'version=="emerald"&&layout_version!="emerald"',
                    'if(!std::filesystem::exists(json_to_string(layout,"border_filepath")))continue;'):
        if pattern not in compact:
            raise ValueError('mapjson inclusion contract changed; review preflight')


def tileset_body(headers, symbol):
    bodies = re.findall(r'const\s+struct\s+Tileset\s+' + re.escape(symbol) + r'\s*=\s*\{(.*?)\};', headers, re.S)
    if len(bodies) != 1:
        raise ValueError(f'{symbol}: expected one Tileset declaration, got {len(bodies)}')
    return bodies[0]


def visual_sources(headers, graphics, symbol):
    body = tileset_body(headers, symbol)
    refs = {}
    for field in ('tiles', 'palettes'):
        match = re.search(r'\.' + field + r'\s*=\s*(\w+)', body)
        if not match:
            raise ValueError(f'{symbol}: unresolved {field} symbol')
        refs[field] = match[1]
    tiles = re.findall(r'\b' + re.escape(refs['tiles']) +
                       r'\s*\[\s*\]\s*=\s*INCGFX_U32\("([^"]+)",\s*"([^"]+)"(?:,\s*"([^"]*)")?\)', graphics)
    palettes = re.findall(r'\b' + re.escape(refs['palettes']) +
                          r'\s*\[\s*\]\s*\[\s*16\s*\]\s*=\s*\{(.*?)\};', graphics, re.S)
    if len(tiles) != 1 or len(palettes) != 1 or not tiles[0][1].startswith('.4bpp'):
        raise ValueError(f'{symbol}: unresolved/unsupported graphics or palette declaration')
    paths = re.findall(r'INCGFX_U16\("([^"]+)",\s*"\.gbapal"\)', palettes[0])
    if len(paths) != 16:
        raise ValueError(f'{symbol}: expected 16 declared palette banks, got {len(paths)}')
    return tiles[0], paths


def png_geometry(data):
    """Check the PNG container/CRC and tile geometry; not a pixel decoder."""
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('invalid PNG signature')
    position, header, image, ended, palette = 8, None, False, False, False
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError('truncated PNG chunk')
        size, kind = struct.unpack_from('>I4s', data, position)
        end = position + 12 + size
        if end > len(data):
            raise ValueError('PNG chunk extends beyond file')
        payload = data[position+8:position+8+size]
        crc = struct.unpack_from('>I', data, end-4)[0]
        if zlib.crc32(kind+payload) & 0xffffffff != crc:
            raise ValueError('PNG chunk CRC mismatch')
        if header is None and kind != b'IHDR':
            raise ValueError('PNG must start with IHDR')
        if kind == b'IHDR':
            if header is not None or size != 13:
                raise ValueError('invalid/duplicate PNG IHDR')
            width, height, depth, color, comp, filtering, interlace = struct.unpack('>IIBBBBB', payload)
            valid_depths = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
            if depth not in valid_depths.get(color, ()):
                raise ValueError('invalid PNG bit depth/color type')
            if not width or not height or width % 8 or height % 8 or comp or filtering or interlace not in (0, 1):
                raise ValueError('PNG must have positive 8-pixel tile dimensions and supported header')
            header = {'width': width, 'height': height, 'bit_depth': depth,
                      'color_type': color, 'raw_tiles': width*height//64}
        if kind == b'PLTE':
            if palette or image or not size or size % 3 or size > 768:
                raise ValueError('invalid PNG palette chunk')
            if header['color_type'] == 3 and size // 3 > 2 ** header['bit_depth']:
                raise ValueError('PNG palette exceeds bit-depth capacity')
            palette = True
        if kind == b'IDAT' and header['color_type'] == 3 and not palette:
            raise ValueError('indexed PNG needs a palette before IDAT')
        image |= kind == b'IDAT'
        if kind == b'IEND':
            if size or end != len(data):
                raise ValueError('invalid PNG IEND/trailing bytes')
            ended = True
            break
        position = end
    if not ended or not image:
        raise ValueError('PNG needs IDAT and IEND')
    return header


def palette_errors(data):
    try:
        lines = data.decode('ascii').splitlines()
        valid = lines[:3] == ['JASC-PAL', '0100', '16'] and len(lines) == 19
        colors = [list(map(int, line.split())) for line in lines[3:]]
        valid &= all(len(c) == 3 and all(0 <= n <= 255 for n in c) for c in colors)
    except (UnicodeError, ValueError):
        valid = False
    if not valid:
        raise ValueError('palette must be JASC-PAL 0100 with exactly 16 RGB colors')


def namespace_contract(engine, document):
    """Reuse merged #123's section definitions, saved pins and region mapping."""
    path = Path(__file__).with_name('audit-averon-mapsec-namespace.py')
    spec = importlib.util.spec_from_file_location('averon_namespace', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Same audit input reader records hashes and supports in-memory negatives.
    module.read_json = lambda p: document(p.relative_to(engine).as_posix())
    pin_path = path.with_name('averon-mapsec-pins.json')
    pins = json.loads(pin_path.read_text())['pins']
    entries = module.sections(engine)
    values = {entry['id']: value for value, entry in enumerate(entries)}
    return module, values, {'saved_pin_errors': module.check_pins(engine, pins),
                            'saved_pins_checked': len(pins), 'mapsec_none': len(entries),
                            'audit_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'pins_sha256': hashlib.sha256(pin_path.read_bytes()).hexdigest(),
                            'scope': 'Existing #123 checks reused; no identifier allocation approved'}


def tileset_dependencies(headers, metatiles, symbol, secondary):
    """Resolve actual C references, including aliases, without folder-name guesses."""
    body = tileset_body(headers, symbol)
    role = re.search(r'\.isSecondary\s*=\s*(TRUE|FALSE)', body)
    if not role or (role[1] == 'TRUE') != secondary:
        raise ValueError(f'{symbol}: incorrect or unresolved primary/secondary role')
    paths = []
    for field in ('metatiles', 'metatileAttributes'):
        ref = re.search(r'\.' + field + r'\s*=\s*(\w+)', body)
        matches = re.findall(r'\b' + re.escape(ref[1]) + r'\s*\[\s*\]\s*=\s*INCBIN_U(16|32)\("([^"]+)"\)', metatiles) if ref else []
        if len(matches) != 1:
            raise ValueError(f'{symbol}.{field}: cannot resolve one raw source')
        paths.append((matches[0][1], int(matches[0][0]) // 8))
    return paths


def audit(engine, names):
    engine = Path(engine).resolve()
    hashes, dependencies, errors, warnings, rows = {}, {}, [], [], []

    def read(path):
        if not isinstance(path, str):
            raise ValueError('Expected engine-relative source path')
        target = (engine / path).resolve()
        if not target.is_relative_to(engine):
            raise ValueError(f'Source path escapes engine: {path}')
        data = target.read_bytes()
        hashes[target.relative_to(engine).as_posix()] = hashlib.sha256(data).hexdigest()
        return data

    def document(path):
        return json.loads(read(path).decode('utf-8-sig'))

    groups = document('data/maps/map_groups.json')
    layouts = document('data/layouts/layouts.json')['layouts']
    maps = {p.parent.name: document(p.relative_to(engine).as_posix())
            for p in sorted((engine / 'data/maps').glob('*/map.json'))}
    by_id = defaultdict(list)
    slots = defaultdict(list)
    for name, data in maps.items():
        by_id[data.get('id')].append(name)
    for group_index, group in enumerate(groups['group_order']):
        for index, name in enumerate(groups[group]):
            slots[name].append((group_index, index, group))
    limits = source_limits(read('include/fieldmap.h').decode(), read('include/global.fieldmap.h').decode())
    verify_generator(read('tools/mapjson/mapjson.cpp').decode())
    rules = read('map_data_rules.mk').decode()
    read('Makefile')  # Record the build-version default/override provenance.
    if '$(MAPJSON) groups $(MAP_VERSION)' not in rules:
        raise ValueError('Map build invocation changed; review preflight')
    headers = read('src/data/tilesets/headers.h').decode()
    metatiles = read('src/data/tilesets/metatiles.h').decode()
    graphics = read('src/data/tilesets/graphics.h').decode() + '\n' + read('src/graphics.c').decode()
    namespace, section_values, section_contract = namespace_contract(engine, document)

    def enabled(name):
        return (maps[name].get('region') or 'REGION_HOENN') == 'REGION_HOENN'

    def problem(name, code, detail, warning=False):
        (warnings if warning else errors).append({'map': name, 'code': code, 'detail': detail})

    def target_layout(name):
        matches = [l for l in layouts if l.get('id') == maps[name].get('layout')]
        if len(matches) != 1 or (matches[0].get('layout_version') or 'emerald') != 'emerald':
            raise ValueError(f'{name}: missing/ambiguous/excluded destination layout')
        # A missing border silently removes a table slot; this is a source check.
        read(matches[0]['border_filepath'])
        return matches[0]

    for detail in section_contract['saved_pin_errors']:
        problem('*', 'saved-section-pin', detail)
    if len(groups['group_order']) > 128:
        problem('*', 'group-capacity', 'Map groups exceed signed-byte capacity')

    for name in sorted(set(names)):
        if name not in maps:
            problem(name, 'missing-map', 'No map.json found')
            continue
        data = maps[name]
        row = {'name': name, 'id': data.get('id'), 'layout': data.get('layout'),
               'header_eligible': enabled(name), 'registry_slots': slots[name]}
        rows.append(row)
        section = data.get('region_map_section')
        row['section'] = section
        if section != 'MAPSEC_NONE' and section not in section_values:
            problem(name, 'section-reference', f'Unknown map-section {section!r}')
        elif section == 'MAPSEC_NONE':
            problem(name, 'section-none', 'Sentinel is not a named met-location; review intent', True)
        else:
            row['section_value'] = section_values[section]
            row['section_engine_region'] = namespace.engine_region(section_values[section], section_values)
            if data.get('region') == 'REGION_SINNOH':
                problem(name, 'section-region-mismatch', 'Saved section currently resolves to ' + row['section_engine_region'] + '; Sinnoh routing requires an approved policy', True)
        if len(slots[name]) == 1 and (slots[name][0][1] >= 128 or len(groups[slots[name][0][2]]) > 128):
            problem(name, 'map-capacity', 'Map index/group size exceeds signed-byte capacity')
        if any(slot[:2] == (127, 127) for slot in slots[name]):
            problem(name, 'reserved-map-id', 'Selected slot collides with MAP_DYNAMIC')
        if data.get('name') != name or len(by_id[data.get('id')]) != 1:
            problem(name, 'map-identity', 'Directory/name mismatch or duplicate map constant')
        if len(slots[name]) != 1:
            problem(name, 'map-registration', f'Expected one registry slot, got {len(slots[name])}')
        elif any(enabled(other) != enabled(name) for other in groups[slots[name][0][2]]):
            problem(name, 'mixed-build-group', 'mapjson compacts filtered slots; constants keep source indices')
        if not enabled(name):
            problem(name, 'map-excluded', 'Current Emerald mapjson excludes non-REGION_HOENN headers')
        matched = [l for l in layouts if l.get('id') == data.get('layout')]
        if len(matched) != 1:
            problem(name, 'layout-identity', f'Expected one layout, got {len(matched)}')
            continue
        layout = matched[0]
        row['dimensions'] = [layout.get('width'), layout.get('height')]
        row['layout_eligible'] = (layout.get('layout_version') or 'emerald') == 'emerald'
        if not row['layout_eligible']:
            problem(name, 'layout-excluded', 'Current Emerald mapjson emits NULL for this layout version')
        try:
            blocks = read(layout['blockdata_filepath'])
            border = read(layout['border_filepath'])
            counts = []
            for field, secondary in (('primary_tileset', False), ('secondary_tileset', True)):
                paths = tileset_dependencies(headers, metatiles, layout[field], secondary)
                raw = [read(path) for path, _ in paths]
                strides = [16, 4 if layout.get('layout_version') == 'frlg' else 2]
                if paths[0][1] != 2 or paths[1][1] != strides[1] or any(len(blob) % stride for blob, stride in zip(raw, strides)):
                    raise ValueError(f'{layout[field]}: invalid metatile/attribute record format')
                counts.append(tuple(len(blob) // stride for blob, stride in zip(raw, strides)))
                (tile_path, encoding, options), palette_paths = visual_sources(headers, graphics, layout[field])
                tile_data = read(tile_path)
                info = png_geometry(tile_data)
                trim = re.search(r'(?:^|\s)-num_tiles\s+(\d+)(?:\s|$)', options)
                tile_count = int(trim[1]) if trim else info['raw_tiles']
                primary_tiles = limits['tile_primary_frlg'] if layout.get('layout_version') == 'frlg' else limits['tile_primary']
                tile_limit = primary_tiles if not secondary else limits['tile_total'] - primary_tiles
                if not 0 < tile_count <= min(info['raw_tiles'], tile_limit):
                    raise ValueError(f'{layout[field]}: converted tile count {tile_count} exceeds source/VRAM capacity')
                row.setdefault('graphics', []).append(dict(symbol=layout[field], path=tile_path, encoding=encoding,
                                                          converted_tiles=tile_count, palette_banks=len(palette_paths), **info))
                dependencies[tile_path] = dict(path=tile_path, kind='tiles_png', bytes=len(tile_data), sha256=hashes[tile_path])
                for palette_path in palette_paths:
                    palette_data = read(palette_path)
                    palette_errors(palette_data)
                    dependencies[palette_path] = dict(path=palette_path, kind='palette', bytes=len(palette_data), sha256=hashes[palette_path])
                for (path, _), blob, kind in zip(paths, raw, ('metatiles', 'attributes')):
                    dependencies[path] = {'path': path, 'kind': kind, 'bytes': len(blob), 'sha256': hashes[path]}
            for key, kind in (('blockdata_filepath', 'blocks'), ('border_filepath', 'border')):
                path = layout[key]
                dependencies[path] = {'path': path, 'kind': kind, 'bytes': len(read(path)), 'sha256': hashes[path]}
            row['metatile_counts'] = counts
            for detail in layout_errors(layout, blocks, border, counts, limits):
                problem(name, 'layout-data', detail)
        except (OSError, KeyError, ValueError) as exc:
            problem(name, 'asset-dependency', str(exc))

        if 'shared_events_map' in data:
            shared = data['shared_events_map']
            if not isinstance(shared, str) or shared not in maps:
                problem(name, 'shared-events-reference', 'Missing/invalid shared_events_map source')
            else:
                problem(name, 'shared-events', 'Events come from shared_events_map; manual event review required', True)
        source_warps = [] if 'shared_events_map' in data else data.get('warp_events') or []
        if not isinstance(source_warps, list):
            problem(name, 'warp-format', 'warp_events must be an array')
            source_warps = []
        for i, warp in enumerate(source_warps):
            if not isinstance(warp, dict):
                problem(name, 'warp-format', f'Warp {i} must be an object')
                continue
            width, height = layout.get('width'), layout.get('height')
            if not all(type(warp.get(k)) is int for k in ('x', 'y')) or not positive_int(width) or not positive_int(height) or not (0 <= warp['x'] < width and 0 <= warp['y'] < height):
                problem(name, 'warp-coordinates', f'Warp {i} lies outside its layout')
            target_id = warp.get('dest_map')
            if target_id == 'MAP_DYNAMIC':
                problem(name, 'dynamic-warp', f'Warp {i} needs runtime/script review', True)
                continue
            targets = by_id.get(target_id, [])
            if len(targets) != 1 or len(slots[targets[0]]) != 1:
                problem(name, 'warp-target', f'Warp {i}: missing/ambiguous registered target {target_id}')
                continue
            target = maps[targets[0]]
            if not enabled(targets[0]):
                problem(name, 'warp-excluded', f'Warp {i} targets an excluded header')
            try:
                destination = target_layout(targets[0])
            except (OSError, KeyError, ValueError) as exc:
                problem(name, 'warp-layout', str(exc))
                continue
            if 'shared_events_map' in target:
                shared = target['shared_events_map']
                if not isinstance(shared, str) or shared not in maps:
                    problem(name, 'shared-events-reference', f'Warp {i}: invalid shared target event source')
                else:
                    problem(name, 'shared-target-events', f'Warp {i}: target uses shared events; manual review required', True)
                continue
            warps = target.get('warp_events') or []
            if not isinstance(warps, list) or any(not isinstance(w, dict) for w in warps):
                problem(name, 'warp-target-format', f'Warp {i}: target warp_events is not an object array')
                continue
            raw_index = warp.get('dest_warp_id')
            if type(raw_index) not in (int, str) or not re.fullmatch(r'-?\d+|[A-Za-z_]\w*', str(raw_index), re.ASCII):
                problem(name, 'warp-index', f'Warp {i}: malformed destination index {raw_index!r}')
                continue
            index = str(raw_index)
            if re.fullmatch(r'-?\d+', index, re.ASCII):
                if str(int(index)) != index:
                    problem(name, 'warp-index', f'Warp {i}: use canonical decimal indices, not {index}')
                    continue
                index = int(index)
                if index == -1:
                    problem(name, 'dynamic-warp', f'Warp {i}: WARP_ID_NONE requires runtime/script review', True)
                    continue
            else:
                matches = [j for j, w in enumerate(warps) if w.get('warp_id') == index]
                if len(matches) != 1:
                    problem(name, 'symbolic-warp', f'Warp {i}: unresolved {index}; needs manual review', True)
                    continue
                index = matches[0]
            if not 0 <= index < min(len(warps), 128):
                problem(name, 'warp-index', f'Warp {i}: destination index {index} is invalid')
            else:
                point = warps[index]
                if not all(type(point.get(k)) is int for k in ('x', 'y')) or not positive_int(destination.get('width')) or not positive_int(destination.get('height')) or not (0 <= point['x'] < destination['width'] and 0 <= point['y'] < destination['height']):
                    problem(name, 'warp-arrival', f'Warp {i}: destination warp lies outside its layout')
                if point.get('dest_map') != data.get('id'):
                    problem(name, 'warp-return', f'Warp {i} has no direct return; check intentional one-way/script behavior', True)
                else:
                    back = point.get('dest_warp_id')
                    if type(back) in (str, int) and re.fullmatch(r'-?\d+', str(back), re.ASCII):
                        if str(int(back)) != str(back) or not -1 <= int(back) < min(len(source_warps), 128):
                            problem(name, 'warp-return-index', f'Warp {i}: return index {back!r} is invalid')
                        elif int(back) == -1:
                            problem(name, 'dynamic-return-warp', f'Warp {i}: return uses WARP_ID_NONE; script review required', True)
                    elif not isinstance(back, str) or len([w for w in source_warps if isinstance(w, dict) and w.get('warp_id') == back]) != 1:
                        problem(name, 'warp-return-index', f'Warp {i}: return index {back!r} is unresolved')
        connections = data.get('connections') or []
        if not isinstance(connections, list):
            problem(name, 'connection-format', 'connections must be an array')
            connections = []
        for connection in connections:
            if not isinstance(connection, dict):
                problem(name, 'connection-format', 'connection must be an object')
                continue
            offset = connection.get('offset')
            if connection.get('direction') not in ('up', 'down', 'left', 'right', 'dive', 'emerge') or type(offset) not in (int, str) or not re.fullmatch(r'-?\d+', str(offset), re.ASCII) or str(int(offset)) != str(offset) or not -(2**31) <= int(offset) < 2**31:
                problem(name, 'connection-format', 'Expected known direction and signed 32-bit numeric offset')
                continue
            targets = by_id.get(connection.get('map'), [])
            if len(targets) != 1 or len(slots[targets[0]]) != 1 or not enabled(targets[0]):
                problem(name, 'connection-target', f'Missing/ambiguous/excluded connection {connection.get("map")}')
            else:
                try:
                    dest_layout = target_layout(targets[0])
                    direction = connection['direction']
                    if direction in ('up', 'down', 'left', 'right'):
                        axis = 'width' if direction in ('up', 'down') else 'height'
                        a, b = layout.get(axis), dest_layout.get(axis)
                        if not positive_int(a) or not positive_int(b) or max(0, int(offset)) >= min(a, int(offset) + b):
                            problem(name, 'connection-overlap', 'Connected map edges have no overlapping coordinates')
                        reverse = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}[direction]
                        returns = maps[targets[0]].get('connections') or []
                        back = [c for c in returns if isinstance(c, dict) and c.get('map') == data.get('id')
                                and c.get('direction') == reverse] if isinstance(returns, list) else []
                        if not back:
                            problem(name, 'connection-return', 'No reciprocal edge; review intentional one-way behavior', True)
                        elif not any(str(c.get('offset')) == str(-int(offset)) for c in back):
                            problem(name, 'connection-offset-return', 'Reciprocal edge offset does not undo this connection')
                except (OSError, KeyError, ValueError) as exc:
                    problem(name, 'connection-layout', str(exc))

    duplicates = defaultdict(list)
    for dep in dependencies.values():
        duplicates[(dep['kind'], dep['sha256'])].append(dep['path'])
    return {'scope': 'SOURCE preflight only: PNG container/palette sources checked, not pixel conversion/animation; no generated output, linkage, '
                     'collision/pathfinding, script semantics, licensing or emulator certification',
            'format': 'Current Averon Emerald mapjson; conditional C linkage requires a real build',
            'target_scope': 'Targets checked for registration, layout inclusion and arrival bounds; '
                            'select each target with --map for full geometry/dependency checks',
            'limits': limits, 'namespace_contract': section_contract, 'maps': rows, 'errors': errors, 'warnings': warnings,
            'geometry_dependencies': sorted(dependencies.values(), key=lambda d: d['path']),
            'duplicate_byte_candidates': [paths for paths in duplicates.values() if len(paths) > 1],
            'input_sha256': dict(sorted(hashes.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--map', dest='maps', action='append', required=True, help='Map directory name; repeat for a batch')
    parser.add_argument('--json', type=Path)
    args = parser.parse_args()
    if args.json and args.json.resolve().is_relative_to(args.engine.resolve()):
        parser.error('Write the report outside the read-only engine tree')
    try:
        result = audit(args.engine, args.maps)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        parser.exit(2, f'Preflight input error: {exc}\n')
    if args.json:
        try:
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        except OSError as exc:
            parser.exit(2, f'Cannot write report: {exc}\n')
    for entry in result['errors'] + result['warnings']:
        print(f'{entry["code"]}: {entry["map"]}: {entry["detail"]}')
    print(f'SOURCE: {len(result["maps"])} maps; {len(result["geometry_dependencies"])} geometry dependencies; '
          f'{len(result["errors"])} errors; {len(result["warnings"])} review warnings')
    raise SystemExit(bool(result['errors']))


if __name__ == '__main__':
    main()
