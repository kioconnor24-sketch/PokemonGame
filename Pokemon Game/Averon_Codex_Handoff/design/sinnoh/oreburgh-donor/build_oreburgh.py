#!/usr/bin/env python3
"""Pinned off-engine Oreburgh preflight and existing-art mine candidates.

This is partial geography preparation, not a production installer. No donor
art, events, scripts, connections, saved IDs or engine files are copied.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[3] / 'scripts'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


dual = module('oreburgh_dual', SCRIPTS / 'sinnoh-dual-bank-family.py')
base, pilot = dual.base, dual.base.pilot
REVISION = '38228bb574a3557345852b758d5f1a65eb01bb22'
MAPS = {
    'OreburghCity': (70, 59, 'e475d8891ee8e50160679d05b9095c72b05e1f38'),
    'Route207': (64, 32, '08fb2516a753dbb621316d13703e564be9a94619'),
    'OreburghMine_B1F': (24, 26, '224045753ff73e41b03c8c62dc11a1170e72686d'),
    'OreburghMine_B2F': (32, 28, '6873b27f8a6663a9fcf4f403303f3b1526313ba6'),
}
# Original Averon stone-door geometry, not donor General artwork. These are
# metatile records in an isolated bank, NOT permanent saved-location IDs.
ENTRANCE = {926: 562, 927: 564, 928: 554, 929: 555, 930: 556, 931: 563}
B1_SECONDARY = (687, 711, 869, 870, 871, 880, 881, 882, 883, 884, 885,
                888, 889, 890, 891, 892, 893, 894, 895, 896, 899, 900)
# Donor blue railing quadrants become existing Averon wooden support graphics.
# Every word references current General pixels/palettes, never donor art.
SUPPORT_WORDS = {674: 0x314E, 675: 0x314F, 676: 0x354E, 677: 0x354E,
                 690: 0x314E, 691: 0x314F, 692: 0x354E, 693: 0x354E}


def mine_banks(raw, primary, primary_attrs, source_primary_attrs,
               cave, cave_attrs, jubilife, jubilife_attrs):
    """Map-local metadata only; never change shared General graphics or behavior."""
    if (len(raw) != 24 * 26 * 2 or len(primary) != 512 * 16
            or len(primary_attrs) != 512 * 2 or len(source_primary_attrs) != 512 * 2
            or len(cave) != 420 * 16 or len(cave_attrs) != 420 * 2
            or len(jubilife) % 16 or len(jubilife_attrs) * 8 != len(jubilife)):
        raise ValueError('unexpected mine bank/dimension contract')
    used = {v[0] & 1023 for v in struct.iter_unpack('<H', raw)}
    if {v for v in used if v >= 512} != set(B1_SECONDARY):
        raise ValueError('unreviewed B1 secondary dependency')
    if struct.unpack_from('<H', source_primary_attrs, 484*2)[0] != 0x64:
        raise ValueError('City doorway is no longer a north-arrow warp')
    p, pa, c, ca = map(bytearray, (primary, primary_attrs, cave, cave_attrs))
    for mid in sorted(v for v in used if v < 512):
        if mid != 484 and pa[mid*2:mid*2+2] != source_primary_attrs[mid*2:mid*2+2]:
            raise ValueError('unreviewed primary behavior/layer change: ' + str(mid))
    # The source's top City exits are north-arrow warps; Averon's same numeric
    # General entries are plants. Use existing stairs and supports locally.
    for mid in (483, 484, 485):
        words = list(struct.unpack_from('<8H', primary, (207 if mid == 484 else 113)*16))
        if mid != 484:
            words[4:] = ([0x314E, 0x314F]*2 if mid == 483 else [0x314F, 0x354E]*2)
        struct.pack_into('<8H', p, mid*16, *words)
        pa[mid*2:mid*2+2] = source_primary_attrs[mid*2:mid*2+2]
    remap = {}
    for mid in B1_SECONDARY:
        i = mid - 512
        if (i + 1) * 16 > len(jubilife):
            raise ValueError('absent Jubilife source record')
        if struct.unpack_from('<H', jubilife_attrs, i*2)[0] != (0x65 if mid in (896, 899, 900) else 0):
            raise ValueError('unreviewed B1 secondary behavior/layer change')
        words = list(struct.unpack_from('<8H', jubilife, i*16))
        # Replace the donor's primary-bank entrance fascia with Averon's
        # gray building fascia/stairs, not its unrelated palette-5 artwork.
        if mid in (880, 881, 882, 892, 893, 894, 895):
            local = 101 if mid in (881, 892) else 103 if mid in (882, 895) else 102
            words = list(struct.unpack_from('<8H', primary, local*16))
        elif mid in (888, 889, 890, 891):
            overlay = words[4:]
            words = list(struct.unpack_from('<8H', primary, 207*16))
            words[4:] = overlay
        mapped = []
        for word in words:
            tile = word & 1023
            if tile >= 512:
                if tile not in SUPPORT_WORDS:
                    raise ValueError('unmapped donor support graphic: ' + str(tile))
                mapped.append(SUPPORT_WORDS[tile] ^ (word & 0xC00))
            else:
                mapped.append(word)
        remap[mid] = 512 + len(c)//16
        c.extend(struct.pack('<8H', *mapped))
        ca.extend(jubilife_attrs[i*2:i*2+2])
    return bytes(p), bytes(pa), bytes(c), bytes(ca), remap


def mine_warps(b1, b2):
    """Retain the wide entrance and its valid canonical return, like Emerald doors."""
    def shape(events):
        return [(v['x'], v['y'], v['elevation'], v['dest_map'], str(v['dest_warp_id'])) for v in events]
    city, bottom = 'MAP_OREBURGH_CITY', 'MAP_OREBURGH_MINE_B2F'
    expected = [(11, 1, 0, city, '11'), (12, 1, 0, city, '14'),
                (11, 21, 0, bottom, '0'), (12, 21, 0, bottom, '0'),
                (10, 21, 0, bottom, '0'), (13, 21, 0, bottom, '0')]
    if shape(b1) != expected or shape(b2) != [(15, 1, 0, 'MAP_OREBURGH_MINE_B1F', '2')]:
        raise ValueError('changed source mine warp contract')
    return [dict(v) for v in b1], [dict(v) for v in b2]



def adapt_cave(raw, donor_records, donor_attrs, records, attrs):
    """Preserve the complete Averon Cave prefix; append six behavior-equal records."""
    if len(raw) % 2 or len(records) != 414 * 16 or len(attrs) != 414 * 2:
        raise ValueError('expected the pinned 414-record Averon Cave prefix')
    if len(donor_records) % 16 or len(donor_attrs) * 8 != len(donor_records):
        raise ValueError('invalid donor Cave records/attributes')
    used = sorted({v[0] & 1023 for v in struct.iter_unpack('<H', raw)})
    if not used or any(mid < 512 for mid in used):
        raise ValueError('basement adapter requires secondary-only geometry')
    if set(mid for mid in used if mid >= 926) != set(ENTRANCE):
        raise ValueError('unknown or incomplete six-record entrance dependency')
    extended, extended_attrs = bytearray(records), bytearray(attrs)
    for mid, original in ENTRANCE.items():
        i, j = mid - 512, original - 512
        if (i + 1) * 16 > len(donor_records):
            raise ValueError('absent donor entrance record')
        if donor_attrs[i*2:i*2+2] != attrs[j*2:j*2+2]:
            raise ValueError('entrance replacement changes behavior/layer attributes')
        extended.extend(records[j*16:j*16+16])
        extended_attrs.extend(attrs[j*2:j*2+2])
    for mid in used:
        i = mid - 512
        if mid not in ENTRANCE and donor_records[i*16:i*16+16] != records[i*16:i*16+16]:
            raise ValueError('unreviewed Cave structural difference: ' + str(mid))
        if donor_attrs[i*2:i*2+2] != extended_attrs[i*2:i*2+2]:
            raise ValueError('Cave behavior/layer mismatch: ' + str(mid))
    return bytes(extended), bytes(extended_attrs), used


def prepare(donor, engine, out, mine_pair=False):
    donor, engine, out = Path(donor).resolve(), Path(engine).resolve(), Path(out).resolve()
    if out.exists() or 'engine' in out.parts or out.is_relative_to(donor) or out.is_relative_to(engine):
        raise ValueError('output must be a NEW off-engine, off-donor directory')
    if base.git(donor, 'rev-parse', 'HEAD').decode().strip() != REVISION:
        raise ValueError('donor HEAD mismatch')
    consumed, destination = {}, {}

    def read(rel):
        value = base.verified_file(donor, rel, REVISION)
        consumed[str(rel)] = base.sha(value)
        return value

    def local(rel):
        # Bind current Averon bytes to its own tracked source, including assets.
        revision = base.git(engine, 'rev-parse', 'HEAD').decode().strip()
        root = Path(base.git(engine, 'rev-parse', '--show-toplevel').decode().strip())
        value = base.verified_file(root, engine.relative_to(root) / rel, revision)
        destination[str(rel)] = base.sha(value)
        return value

    for rel in ('include/fieldmap.h', 'include/constants/metatile_behaviors.h'):
        if read(rel) != local(rel):
            raise ValueError('engine contract mismatch: ' + rel)
    layouts = json.loads(read('data/layouts/layouts.json'))['layouts']
    inspection, sources = {}, {}
    for name, (width, height, blob) in MAPS.items():
        header = json.loads(read('data/maps/' + name + '/map.json'))
        matching = [v for v in layouts if v['id'] == header['layout']]
        if len(matching) != 1:
            raise ValueError('ambiguous layout: ' + name)
        layout = matching[0]
        raw = read(layout['blockdata_filepath'])
        if ((layout['width'], layout['height']) != (width, height)
                or len(raw) != width * height * 2):
            raise ValueError('invalid dimensions')
        if hashlib.sha1(b'blob %d\0' % len(raw) + raw).hexdigest() != blob:
            raise ValueError('unexpected source geometry: ' + name)
        header2, layout2, raw2, cells = pilot.read_donor_map(donor, name)
        if header2 != header or layout2 != layout or raw2 != raw:
            raise ValueError('reader source mismatch')
        sources[name] = (header, layout, raw)
        used = sorted({v & 1023 for v in cells})
        inspection[name] = dict(dimensions=[width, height], git_blob=blob,
            sha256=base.sha(raw), tilesets=[layout['primary_tileset'], layout['secondary_tileset']],
            used_primary=[v for v in used if v < 512], used_secondary=[v for v in used if v >= 512],
            warp_geometry=header.get('warp_events', []), connections=header.get('connections'),
            excluded_object_count=len(header.get('object_events', [])))
    name = 'OreburghMine_B2F'
    header, layout, raw = sources[name]
    if [layout['primary_tileset'], layout['secondary_tileset']] != ['gTileset_General', 'gTileset_Cave']:
        raise ValueError('unsupported basement pair')
    cave = 'data/tilesets/secondary/cave/'
    records, attrs, used = adapt_cave(raw, read(cave+'metatiles.bin'), read(cave+'metatile_attributes.bin'),
                                    local(cave+'metatiles.bin'), local(cave+'metatile_attributes.bin'))
    primary = local('data/tilesets/primary/general/metatiles.bin')
    extras, pair_info = {}, None
    if mine_pair:
        h1, l1, raw1 = sources['OreburghMine_B1F']
        if [l1['primary_tileset'], l1['secondary_tileset']] != ['gTileset_General', 'gTileset_Jubilife']:
            raise ValueError('unsupported B1 pair')
        old_cave = records, attrs
        primary, primary_attrs, records, attrs, remap = mine_banks(raw1, primary,
            local('data/tilesets/primary/general/metatile_attributes.bin'),
            read('data/tilesets/primary/general/metatile_attributes.bin'), records, attrs,
            read('data/tilesets/secondary/jubilife/metatiles.bin'),
            read('data/tilesets/secondary/jubilife/metatile_attributes.bin'))
        if records[:len(old_cave[0])] != old_cave[0] or attrs[:len(old_cave[1])] != old_cave[1]:
            raise ValueError('accepted B2 prefix changed')
        warps = mine_warps(h1['warp_events'], header['warp_events'])
        manifest1 = pilot.draft_manifest(pilot.analyze(donor, 'OreburghMine_B1F', REVISION))
        manifest1.update(target_map_id=h1['id'], target_primary_tileset='gTileset_AveronOreburghGeneral',
                         target_secondary_tileset='gTileset_AveronOreburghCave')
        manifest1['metatiles'] = {mid: dict(target=remap.get(int(mid), int(mid)),
            behavior_verified=True, graphics_verified=True) for mid in manifest1['metatiles']}
        with tempfile.TemporaryDirectory(prefix='averon-mine-pair-') as tmp:
            candidate = Path(tmp)/'candidate.bin'
            conversion1 = pilot.convert(donor, 'OreburghMine_B1F', manifest1, candidate)
            raw1_fixed = candidate.read_bytes()
        extras['staged/OreburghMine_B1F.bin'] = raw1_fixed
        extras['banks/primary/metatiles.bin'] = primary
        extras['banks/primary/metatile_attributes.bin'] = primary_attrs
        for n, h, l, events in (('OreburghMine_B1F', h1, l1, warps[0]),
                                 ('OreburghMine_B2F', header, layout, warps[1])):
            border = read(l['border_filepath'])
            if len(border) != 8:
                raise ValueError('unexpected 2x2 mine border')
            extras['staged/'+n+'/border.bin'] = border
            info = dict(id=h['id'], name=n, layout=l['id'], music='MUS_CAVE_OF_ORIGIN',
                region='REGION_SINNOH', region_map_section='MAPSEC_PENDING_OWNER', weather='WEATHER_NONE',
                map_type='MAP_TYPE_UNDERGROUND', requires_flash=False, allow_cycling=h['allow_cycling'],
                allow_escaping=h['allow_escaping'], allow_running=h['allow_running'], show_map_name=True,
                battle_scene='MAP_BATTLE_SCENE_NORMAL', connections=None, object_events=[],
                warp_events=events, coord_events=[], bg_events=[])
            extras['staged/'+n+'/map.json'] = (json.dumps(info, indent=2)+'\n').encode()
            extras['staged/'+n+'/scripts.inc'] = (n+'_MapScripts::\n\t.byte 0\n').encode()
        pair_info = dict(conversion=conversion1, remap=remap,
            primary_metatile_changes=[483, 484, 485], source_warp_events_preserved=[6, 1],
            canonical_return=[11, 21], entrance_cells=[[11, 21], [12, 21], [10, 21], [13, 21]],
            primary_bank='isolated512-record metadata; existing General graphics/palettes unchanged',
            cave_records=len(records)//16, external_dependency='B1 City warps0/1 -> future City11/14',
            adaptation='blue industrial supports -> existing Averon wooden supports and gray stairs/fascia')
        old_cells, new_cells = struct.unpack('<624H', raw1), struct.unpack('<624H', raw1_fixed)
        source_attrs = (read('data/tilesets/primary/general/metatile_attributes.bin'),
                        read('data/tilesets/secondary/jubilife/metatile_attributes.bin'))
        altered = []
        for index, (old, new) in enumerate(zip(old_cells, new_cells)):
            bank, rel = divmod(old & 1023, 512)
            old_attr = struct.unpack_from('<H', source_attrs[bank], rel*2)[0]
            bank, rel = divmod(new & 1023, 512)
            new_attr = struct.unpack_from('<H', (primary_attrs, attrs)[bank], rel*2)[0]
            if old_attr != new_attr:
                altered.append((index%24, index//24, old_attr, new_attr))
        if altered:
            raise ValueError('unexpected mine behavior/layer change')
        pair_info.update(behavior_layer_comparisons=624, exact_attribute_changes=altered,
                         collision_elevation_unchanged_cells=624)
    images, palettes = [], {}
    for bank, folder in enumerate(('primary/general', 'secondary/cave')):
        prefix = 'data/tilesets/' + folder + '/'
        images.append(dual.indexed(local(prefix+'tiles.png')))
        for i in (range(6) if bank == 0 else range(6, 16)):
            palettes[i] = base.palette(local(prefix+'palettes/%02d.pal' % i))
    dependencies = dual.closure(raw, [primary, records], images)
    preview = dual.render(raw, [primary, records], images, palettes, 32, 28)
    if mine_pair:
        # Check every map and border graphics/palette dependency, not just B2.
        closure1 = dual.closure(raw1_fixed + extras['staged/OreburghMine_B1F/border.bin'],
                               [primary, records], images)
        closure2 = dual.closure(raw + extras['staged/OreburghMine_B2F/border.bin'],
                               [primary, records], images)
        pair_info.update(dependencies_b1=closure1, dependencies_b2_with_border=closure2)
        preview1 = dual.render(raw1_fixed, [primary, records], images, palettes, 24, 26)
    # Reuse the existing converter's complete-map C/E and identity validation;
    # no competing binary conversion path is introduced here.
    manifest = pilot.draft_manifest(pilot.analyze(donor, name, REVISION))
    manifest.update(target_map_id=header['id'], target_primary_tileset=(
                        'gTileset_AveronOreburghGeneral' if mine_pair else 'gTileset_General'),
                    target_secondary_tileset='gTileset_AveronOreburghCave')
    manifest['metatiles'] = {str(mid): dict(target=mid, behavior_verified=True, graphics_verified=True)
                             for mid in used}
    with tempfile.TemporaryDirectory(prefix='averon-oreburgh-') as tmp:
        candidate = Path(tmp) / 'candidate.bin'
        conversion = pilot.convert(donor, name, manifest, candidate)
        staged = candidate.read_bytes()
    if staged != raw:
        raise ValueError('basement cell geometry changed')
    receipt = dict(status='PARTIAL_OFF_ENGINE_B2_CANDIDATE_NOT_PLAYTESTED', donor_revision=REVISION,
        engine_revision=base.git(engine, 'rev-parse', 'HEAD').decode().strip(),
        source_sha256=base.sha(raw), staged_sha256=base.sha(staged), conversion=conversion,
        cave_prefix_preserved=True, cave_records=420, appended_existing_art=ENTRANCE,
        attributes_equal_for_every_used_metatile=True, dependencies=dependencies,
        consumed_donor_sha256=consumed, existing_averon_sha256=destination,
        limits=['Existing Averon art adaptation, not donor visual equivalence or art redistribution',
                'Only B2 geometry staged; border/header/warps/B1/City/Route207 integration still blocked',
                'B1 wide entrance uses a valid canonical return; preserve all source warp events',
                'No registry, section IDs, source events, story, encounters, engine install or ROM acceptance'])
    if mine_pair:
        receipt.update(status='OFF_ENGINE_MINE_PAIR_NOT_ROM_TESTED', cave_records=len(records)//16,
            mine_pair=pair_info, limits=[
                'Existing Averon art adaptation, not donor visual equivalence; no art redistributed',
                'Both headers retain MAPSEC_PENDING_OWNER; no production maps or saved IDs',
                'City exits require future City11/14 integration; no stand-alone story access',
                'No source objects/items/scripts/encounters; no ROM/warp/runtime acceptance'])
    out.mkdir(parents=True)
    bank = out / 'banks/cave'
    bank.mkdir(parents=True)
    (bank/'metatiles.bin').write_bytes(records)
    (bank/'metatile_attributes.bin').write_bytes(attrs)
    (out/'staged').mkdir()
    (out/'staged/OreburghMine_B2F.bin').write_bytes(staged)
    preview.save(out/'OreburghMine_B2F-averon.png')
    for relative, data in extras.items():
        target = out/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    if mine_pair:
        preview1.save(out/'OreburghMine_B1F-averon.png')
    for file, value in (('source-inspection.json', inspection), ('conversion-receipt.json', receipt)):
        (out/file).write_text(json.dumps(value, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('donor', 'engine', 'out'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--mine-pair', action='store_true')
    args = parser.parse_args()
    print(json.dumps(prepare(args.donor, args.engine, args.out, args.mine_pair), indent=2))
