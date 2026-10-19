#!/usr/bin/env python3
"""Stage a source-identical static Sinnoh General family outside the engine.

No scripts, events, connections, registries, saved IDs or production files are
imported. Only primary-only General maps are supported by this first adapter.
Animated tiles and cross-bank graphic/palette dependencies fail closed.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import subprocess

from PIL import Image

_spec = importlib.util.spec_from_file_location('donor_pilot', Path(__file__).with_name('sinnoh-donor-map-pilot.py'))
pilot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pilot)
FAMILY = Path('data/tilesets/primary/general')
# Verified against the pinned donor's and Averon's identical tileset_anims.c.
ANIMATION_START = 432
CONTRACTS = ('include/fieldmap.h', 'include/constants/metatile_behaviors.h', 'src/tileset_anims.c')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE)


def verified_file(root, relative, revision):
    """Bind every consumed byte to a tracked non-symlink blob, not a caller label."""
    path = pilot._inside(root, relative)
    entry = git(root, 'ls-tree', revision, '--', str(relative)).decode().split()
    if len(entry) < 3 or entry[0] not in ('100644', '100755') or entry[1] != 'blob':
        raise ValueError('missing regular tracked donor file: ' + str(relative))
    committed = git(root, 'cat-file', 'blob', entry[2])
    working = path.read_bytes()
    if working != committed:
        # Git's declared text eol=crlf checkout is not an asset modification.
        # Accept only that exact normalization, never custom clean filters.
        eol = git(root, 'check-attr', 'eol', '--', str(relative)).decode().strip()
        if not (eol.endswith(': crlf') and b'\r' not in committed
                and working.replace(b'\r\n', b'\n') == committed):
            raise ValueError('dirty donor dependency: ' + str(relative))
    return committed


def validate_assets(raw, records, attributes, image, palettes):
    if not records or len(records) % 16 or len(records) > 512 * 16:
        raise ValueError('invalid primary metatile records')
    if len(attributes) * 8 != len(records):
        raise ValueError('attribute count mismatch')
    if image.mode != 'P' or image.width != 128 or image.height % 8 or image.height > 256:
        raise ValueError('expected indexed 128-wide primary image with at most512 tiles')
    if max(image.tobytes()) > 15:
        raise ValueError('graphics exceed 4bpp indices')
    cells = struct.unpack('<' + str(len(raw) // 2) + 'H', raw)
    ids = sorted({x & 1023 for x in cells})
    tiles, pals = set(), set()
    for metatile in ids:
        if metatile >= 512:
            raise ValueError('secondary metatiles require a separately verified family adapter')
        if (metatile + 1) * 16 > len(records):
            raise ValueError('absent source metatile')
        for (word,) in struct.iter_unpack('<H', records[metatile * 16:(metatile + 1) * 16]):
            tile, pal = word & 1023, word >> 12
            if tile >= ANIMATION_START:
                raise ValueError('animated or secondary graphic dependency requires callback adapter')
            if tile >= image.width * image.height // 64:
                raise ValueError('absent source graphic tile')
            if pal >= 6 or pal not in palettes:
                raise ValueError('secondary or missing palette dependency')
            tiles.add(tile)
            pals.add(pal)
    return {'metatiles': ids, 'graphic_tiles': sorted(tiles), 'palettes': sorted(pals)}


def palette(raw):
    lines = raw.decode('ascii').splitlines()
    if lines[:3] != ['JASC-PAL', '0100', '16'] or len(lines) != 19:
        raise ValueError('invalid16-color JASC palette')
    colors = [tuple(map(int, x.split())) for x in lines[3:]]
    if any(len(x) != 3 or any(c < 0 or c > 255 for c in x) for x in colors):
        raise ValueError('invalid palette color')
    # GBA color quantization; avoid claiming PNG embedded palettes are runtime colors.
    return [tuple((c >> 3) << 3 for c in x) for x in colors]


def render(raw, records, image, palettes, width, height):
    """Daytime static two-layer rendering, palette-index0 transparent on top layer."""
    canvas = Image.new('RGB', (width * 16, height * 16))
    for n, (cell,) in enumerate(struct.iter_unpack('<H', raw)):
        for i, (word,) in enumerate(struct.iter_unpack('<H', records[(cell & 1023)*16:(cell & 1023)*16+16])):
            tile, pal = word & 1023, word >> 12
            tx, ty = (tile % 16) * 8, (tile // 16) * 8
            for y in range(8):
                for x in range(8):
                    sx = 7-x if word & 0x400 else x
                    sy = 7-y if word & 0x800 else y
                    index = image.getpixel((tx+sx, ty+sy))
                    if i < 4 or index:
                        canvas.putpixel(((n % width)*16+(i % 2)*8+x,
                                         (n // width)*16+((i % 4)//2)*8+y), palettes[pal][index])
    return canvas


def stage(root, engine, revision, map_name, output):
    root, engine, output = Path(root).resolve(), Path(engine).resolve(), Path(output).resolve()
    if not re.fullmatch('[0-9a-f]{40}', revision) or git(root, 'rev-parse', 'HEAD').decode().strip() != revision:
        raise ValueError('donor HEAD does not match pinned revision')
    if output.exists() or output.is_relative_to(root) or output.is_relative_to(engine) or 'engine' in output.parts:
        raise ValueError('output must be a NEW off-engine, off-donor scratch directory')
    # Contracts are compared in full. New behavior enum or animation semantics require review.
    blobs = {}
    for rel in CONTRACTS:
        donor = verified_file(root, rel, revision)
        if donor != (engine / rel).read_bytes():
            raise ValueError('engine contract mismatch: ' + rel)
        blobs[rel] = donor
    header, layout, raw, _ = pilot.read_donor_map(root, map_name)
    if layout['primary_tileset'] != 'gTileset_General':
        raise ValueError('unsupported primary family')
    if (layout['width'] + 15) * (layout['height'] + 14) > 10240:
        raise ValueError('layout exceeds padded field buffer')
    for rel in ('data/maps/' + map_name + '/map.json', 'data/layouts/layouts.json', layout['blockdata_filepath']):
        blobs[rel] = verified_file(root, rel, revision)
    border = verified_file(root, layout['border_filepath'], revision)
    border_width, border_height = layout.get('border_width', 2), layout.get('border_height', 2)
    if type(border_width) is not int or type(border_height) is not int or border_width < 1 or border_height < 1 or len(border) != border_width * border_height * 2:
        raise ValueError('invalid border dimensions/length')
    records = verified_file(root, FAMILY / 'metatiles.bin', revision)
    attributes = verified_file(root, FAMILY / 'metatile_attributes.bin', revision)
    png = verified_file(root, FAMILY / 'tiles.png', revision)
    # Include all16 palette source files for ordinary/night palette integration, but
    # this renderer and static adapter only certify referenced daytime slots0..5.
    assets = {'metatiles.bin': records, 'metatile_attributes.bin': attributes, 'tiles.png': png}
    pals = {}
    for i in range(16):
        rel = 'palettes/%02d.pal' % i
        assets[rel] = verified_file(root, FAMILY / rel, revision)
        pals[i] = palette(assets[rel])
    import io
    image = Image.open(io.BytesIO(png)); image.load()
    closure = validate_assets(raw + border, records, attributes, image, pals)
    # This first renderer supports normal/covered two-layer attributes only.
    if any(struct.unpack_from('<H', attributes, i * 2)[0] >> 12 not in (0, 1) for i in closure['metatiles']):
        raise ValueError('unsupported layer type')
    preview = render(raw, records, image, pals, layout['width'], layout['height'])
    receipt = {
        'status': 'STATIC_FAMILY_STAGED_NOT_PLAYTESTED', 'source_url': pilot.DONOR_URL,
        'donor_revision': revision, 'source_map': map_name,
        'dimensions': [layout['width'], layout['height']], 'source_map_sha256': sha(raw),
        'border_sha256': sha(border), 'border_dimensions': [border_width, border_height],
        'source_metadata': {p: sha(v) for p, v in blobs.items() if p not in CONTRACTS},
        'family': 'SinnohGeneralStatic', 'callback': 'NULL (referenced tiles exclude animation ranges)',
        'dependencies': closure, 'source_contracts': {p: sha(blobs[p]) for p in CONTRACTS},
        'assets': {p: {'sha256': sha(v), 'bytes': len(v)} for p, v in assets.items()},
        'decoded_graphics_bytes': image.width * image.height // 2,
        'metatile_and_attribute_bytes': len(records) + len(attributes),
        'palette_runtime_bytes': 16 * 32,
        'preview_rgb_sha256': sha(preview.tobytes()),
        'limits': ['static daytime preview only', 'no collision gameplay or scene rendering acceptance',
                   'no secondary metatiles/graphics/palettes', 'no map registration or connections imported',
                   'no permission/distribution determination', 'night and field-effect visuals need graphical QA'],
    }
    # Validate everything before creating output; never copy arbitrary donor directories.
    output.mkdir(parents=True)
    for rel, data in assets.items():
        path = output / 'SinnohGeneralStatic' / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (output / 'map.bin').write_bytes(raw)
    (output / 'border.bin').write_bytes(border)
    preview.save(output / 'preview.png')
    (output / 'sinnoh_general_static.c').write_text(family_include())
    (output / 'ATTRIBUTION.txt').write_text('Source: ' + pilot.DONOR_URL + '\nRevision: ' + revision + '\nOriginal Sinnoh map work: LiderMorti00. Owner reports permission in Issue15 comment6274520543; third-party asset/distribution terms remain to be documented.\n')
    # Reopen written dependencies and prove staging retained the actual indexed pixels,
    # palettes, flips, records and high collision/elevation bits; no lossy art remapping.
    staged_image = Image.open(output / 'SinnohGeneralStatic/tiles.png'); staged_image.load()
    staged_pals = {i: palette((output / ('SinnohGeneralStatic/palettes/%02d.pal' % i)).read_bytes()) for i in range(16)}
    actual = render((output / 'map.bin').read_bytes(), (output / 'SinnohGeneralStatic/metatiles.bin').read_bytes(),
                    staged_image, staged_pals, layout['width'], layout['height'])
    if actual.tobytes() != preview.tobytes():
        raise ValueError('staged pixels differ')
    receipt['staged_pixels_equal_source'] = True
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt



def family_include():
    """Standalone generated source; a reviewed adapter must register its symbol."""
    prefix = 'data/tilesets/primary/sinnoh_general_static/'
    lines = ['// Generated isolated static family. Never replace gTileset_General.',
             '#include "global.h"',
             'const u32 gTilesetTiles_SinnohGeneralStatic[] = INCGFX_U32("' + prefix + 'tiles.png", ".4bpp.smol");',
             'const u16 ALIGNED(4) gTilesetPalettes_SinnohGeneralStatic[][16] = {']
    lines += ['    INCGFX_U16("' + prefix + 'palettes/%02d.pal", ".gbapal"),' % i for i in range(16)]
    lines += ['};',
              'const u16 gMetatiles_SinnohGeneralStatic[] = INCBIN_U16("' + prefix + 'metatiles.bin");',
              'const u16 gMetatileAttributes_SinnohGeneralStatic[] = INCBIN_U16("' + prefix + 'metatile_attributes.bin");',
              'const struct Tileset gTileset_SinnohGeneralStatic = {',
              '    .isCompressed = TRUE, .isSecondary = FALSE,',
              '    .tiles = gTilesetTiles_SinnohGeneralStatic,',
              '    .palettes = gTilesetPalettes_SinnohGeneralStatic,',
              '    .metatiles = gMetatiles_SinnohGeneralStatic,',
              '    .metatileAttributes = gMetatileAttributes_SinnohGeneralStatic,',
              '    .callback = NULL,', '};', '']
    return '\n'.join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--donor-root', type=Path, required=True)
    p.add_argument('--engine-root', type=Path, required=True)
    p.add_argument('--revision', required=True)
    p.add_argument('--map', required=True, dest='map_name')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    try:
        print(json.dumps(stage(a.donor_root, a.engine_root, a.revision, a.map_name, a.output), indent=2))
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        p.exit(2, 'ERROR: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
