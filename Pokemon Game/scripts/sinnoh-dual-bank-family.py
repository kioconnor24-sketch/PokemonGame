#!/usr/bin/env python3
"""Source-identical General/Petalburg paired-bank and animation scratch adapter.

Generates integration inputs, never edits engine/maps or certifies gameplay.
Unsupported source families fail closed; no donor events/scripts are copied.
"""
import argparse
import importlib.util
import io
import json
from pathlib import Path
import re
import struct
import subprocess
from PIL import Image

spec = importlib.util.spec_from_file_location('static_family', Path(__file__).with_name('sinnoh-isolated-tileset.py'))
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
BANKS = ('primary/general', 'secondary/petalburg')
ANIMS = {'flower': (3, 4), 'water': (8, 30), 'sand_water_edge': (7, 10),
         'waterfall': (4, 6), 'land_water_edge': (4, 10)}


def animation_include(source):
    """Extract only the engine-identical General callback closure, namespace it."""
    names = ['InitTilesetAnim_General', 'TilesetAnim_General'] + [
        'QueueAnimTiles_General_' + x for x in ('Flower', 'Water', 'SandWaterEdge', 'Waterfall', 'LandWaterEdge')]
    functions, prototypes = [], []
    for name in names:
        matches = re.findall(r'^(?:static )?void ' + name + r'\([^;]*?\)\n\{.*?^\}', source, re.M | re.S)
        if len(matches) != 1:
            raise ValueError('unsupported animation function shape: ' + name)
        functions.append(matches[0])
        prototypes.append(matches[0].split('\n{')[0] + ';')
    arrays = re.findall(r'^const u16(?: \*const)? gTilesetAnims_General_\w+\[.*?;', source, re.M | re.S)
    if len(arrays) != 31:  # 26 frames plus five frame-order tables.
        raise ValueError('unsupported General animation data closure')
    text = '\n'.join(prototypes + arrays + functions) + '\n'
    text = re.sub(r'\b(InitTilesetAnim|TilesetAnim|QueueAnimTiles|gTilesetAnims)_General\b', r'\1_SinnohImported', text)
    # Word boundary after General does not include underscores; replace that exact prefix too.
    text = text.replace('_General_', '_SinnohImported_')
    return text.replace('data/tilesets/primary/general/', 'data/tilesets/primary/sinnoh_imported/')


def indexed(raw):
    im = Image.open(io.BytesIO(raw)); im.load()
    if im.mode != 'P' or im.width % 8 or im.height % 8 or max(im.tobytes()) > 15:
        raise ValueError('expected indexed4bpp tile-aligned image')
    return im


def closure(raw, records, images):
    words = struct.unpack('<' + str(len(raw)//2) + 'H', raw)
    ids, graphics, palettes = sorted({v & 1023 for v in words}), set(), set()
    for mid in ids:
        bank, rel = divmod(mid, 512)
        if (rel+1)*16 > len(records[bank]):
            raise ValueError('absent source metatile')
        for (word,) in struct.iter_unpack('<H', records[bank][rel*16:rel*16+16]):
            tile, pal = word & 1023, word >> 12
            tilebank, local = divmod(tile, 512)
            if local >= images[tilebank].width * images[tilebank].height // 64:
                raise ValueError('absent source graphic')
            graphics.add(tile); palettes.add(pal)
    return {'metatiles': ids, 'graphic_tiles': sorted(graphics), 'palettes': sorted(palettes)}


def render(raw, records, images, palettes, width, height):
    """Flattened static daytime pixels only; object/layer priorities are not modeled."""
    canvas = Image.new('RGB', (width*16, height*16))
    for n, (cell,) in enumerate(struct.iter_unpack('<H', raw)):
        bank, mid = divmod(cell & 1023, 512)
        for i, (word,) in enumerate(struct.iter_unpack('<H', records[bank][mid*16:mid*16+16])):
            tb, tile = divmod(word & 1023, 512); im = images[tb]
            columns = im.width//8
            for y in range(8):
                for x in range(8):
                    ix = im.getpixel(((tile % columns)*8 + (7-x if word & 0x400 else x),
                                      (tile//columns)*8 + (7-y if word & 0x800 else y)))
                    if i < 4 or ix:
                        canvas.putpixel(((n%width)*16+(i%2)*8+x, (n//width)*16+((i%4)//2)*8+y), palettes[word>>12][ix])
    return canvas


def family_source():
    lines = ['#include "global.h"', 'extern void InitTilesetAnim_SinnohImported(void);']
    for bank, suffix in enumerate(('General', 'Petalburg')):
        symbol = 'SinnohImported' + suffix
        path = 'data/tilesets/' + ('primary' if bank == 0 else 'secondary') + '/sinnoh_imported/'
        lines += ['const u32 gTilesetTiles_' + symbol + '[] = INCGFX_U32("' + path + 'tiles.png", ".4bpp.smol");',
                  'const u16 ALIGNED(4) gTilesetPalettes_' + symbol + '[][16] = {']
        lines += ['    INCGFX_U16("' + path + 'palettes/%02d.pal", ".gbapal"),' % i for i in range(16)]
        lines += ['};', 'const u16 gMetatiles_' + symbol + '[] = INCBIN_U16("' + path + 'metatiles.bin");',
                  'const u16 gMetatileAttributes_' + symbol + '[] = INCBIN_U16("' + path + 'metatile_attributes.bin");',
                  'const struct Tileset gTileset_' + symbol + ' = {',
                  ' .isCompressed = TRUE, .isSecondary = ' + ('FALSE' if bank == 0 else 'TRUE') + ',',
                  ' .tiles = gTilesetTiles_' + symbol + ', .palettes = gTilesetPalettes_' + symbol + ',',
                  ' .metatiles = gMetatiles_' + symbol + ', .metatileAttributes = gMetatileAttributes_' + symbol + ',',
                  ' .callback = ' + ('InitTilesetAnim_SinnohImported' if bank == 0 else 'NULL') + ',', '};']
    return '\n'.join(lines) + '\n'


def stage(root, engine, revision, map_name, output):
    root, engine, output = Path(root).resolve(), Path(engine).resolve(), Path(output).resolve()
    if not re.fullmatch('[0-9a-f]{40}', revision) or base.git(root, 'rev-parse', 'HEAD').decode().strip() != revision:
        raise ValueError('donor HEAD mismatch')
    if output.exists() or output.is_relative_to(root) or output.is_relative_to(engine) or 'engine' in output.parts:
        raise ValueError('output must be NEW off-engine/off-donor scratch directory')
    consumed = {}
    def read(rel):
        data = base.verified_file(root, rel, revision); consumed[str(rel)] = base.sha(data)
        return data
    contracts = {}
    for rel in base.CONTRACTS:
        contracts[rel] = read(rel)
        if contracts[rel] != (engine/rel).read_bytes():
            raise ValueError('engine contract mismatch: ' + rel)
    anim_source = animation_include(contracts['src/tileset_anims.c'].decode())
    if not base.pilot.MAP_NAME.fullmatch(map_name):
        raise ValueError('invalid map name')
    header = json.loads(read('data/maps/' + map_name + '/map.json'))
    layouts = json.loads(read('data/layouts/layouts.json'))['layouts']
    matches = [v for v in layouts if v['id'] == header['layout']]
    if len(matches) != 1: raise ValueError('missing/ambiguous layout')
    layout = matches[0]
    if [layout['primary_tileset'], layout['secondary_tileset']] != ['gTileset_General', 'gTileset_Petalburg']:
        raise ValueError('unsupported tileset pair/callback family')
    width, height = layout['width'], layout['height']
    if type(width) is not int or type(height) is not int or width < 1 or height < 1 or (width+15)*(height+14) > 10240:
        raise ValueError('invalid dimensions/field buffer')
    raw, border = read(layout['blockdata_filepath']), read(layout['border_filepath'])
    bw, bh = layout.get('border_width', 2), layout.get('border_height', 2)
    if type(bw) is not int or type(bh) is not int or bw < 1 or bh < 1 or len(border) != bw*bh*2 or len(raw) != width*height*2:
        raise ValueError('invalid map/border length')
    assets, records, images, pals = {}, [], [], []
    for bank, folder in enumerate(BANKS):
        prefix = Path('data/tilesets') / folder
        dest = ('primary' if bank == 0 else 'secondary') + '/sinnoh_imported/'
        record, attr, png = [read(prefix / name) for name in ('metatiles.bin', 'metatile_attributes.bin', 'tiles.png')]
        if not record or len(record) % 16 or len(record) > 8192 or len(attr)*8 != len(record):
            raise ValueError('invalid record/attribute count')
        im = indexed(png)
        if im.width != 128 or im.height > 256 or (bank == 0 and im.height != 256):
            raise ValueError('invalid bank image capacity')
        records.append(record); images.append(im)
        for name, data in [('metatiles.bin', record), ('metatile_attributes.bin', attr), ('tiles.png', png)]:
            assets[dest+name] = data
        bankpals = []
        for i in range(16):
            name = 'palettes/%02d.pal' % i; data = read(prefix/name)
            bankpals.append(base.palette(data)); assets[dest+name] = data
        pals.append(bankpals)
    dependencies = closure(raw+border, records, images)
    for mid in dependencies['metatiles']:
        bank, rel = divmod(mid, 512)
        attr = assets[('primary' if bank == 0 else 'secondary') + '/sinnoh_imported/metatile_attributes.bin']
        if struct.unpack_from('<H', attr, rel*2)[0] >> 12 > 2:
            raise ValueError('unsupported layer type')
    for kind, (count, tiles) in ANIMS.items():
        for frame in range(count):
            rel = 'anim/%s/%d.png' % (kind, frame)
            data = read(Path('data/tilesets/primary/general')/rel)
            im = indexed(data)
            if im.width*im.height != tiles*64:
                raise ValueError('animation frame transfer size mismatch')
            assets['primary/sinnoh_imported/'+rel] = data
    palettes = {i: pals[0 if i < 6 else 1][i] for i in range(16)}
    preview = render(raw, records, images, palettes, width, height)
    receipt = {'status': 'PAIRED_FAMILY_STAGED_NOT_GAMEPLAY_ACCEPTED', 'donor': base.pilot.DONOR_URL,
               'revision': revision, 'map': map_name, 'dimensions': [width, height],
               'map_sha256': base.sha(raw), 'border_sha256': base.sha(border),
               'dependencies': dependencies, 'consumed_source_sha256': consumed,
               'assets': {p: {'sha256': base.sha(v), 'bytes': len(v)} for p,v in assets.items()},
               'animation_frames': 26, 'animation_include_sha256': base.sha(anim_source.encode()),
               'static_rgb_sha256': base.sha(preview.tobytes()),
               'limits': ['General/Petalburg only; secondary callback is static',
                          'animation include must be reviewed/included inside tileset_anims.c',
                          'no registry, connections, events, IDs or scripts imported',
                          'no gameplay, night/field effects/doors or distribution-rights acceptance']}
    output.mkdir(parents=True)
    for rel, data in assets.items():
        p = output/'data/tilesets'/rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
    (output/'map.bin').write_bytes(raw); (output/'border.bin').write_bytes(border)
    (output/'family.c').write_text(family_source())
    (output/'animations.inc').write_text(anim_source)
    preview.save(output/'preview.png')
    (output/'ATTRIBUTION.txt').write_text(base.pilot.DONOR_URL+'\nLiderMorti00\nRevision:'+revision+'\nOwner-reported permission: Issue15/6274520543. Third-party/distribution scope not certified.\n')
    (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ('donor-root', 'engine-root', 'revision', 'map', 'output'): p.add_argument('--'+arg, required=True)
    a = p.parse_args()
    try: print(json.dumps(stage(a.donor_root, a.engine_root, a.revision, a.map, a.output), indent=2))
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as e: p.exit(2, 'ERROR: '+str(e)+'\n')


if __name__ == '__main__': main()
