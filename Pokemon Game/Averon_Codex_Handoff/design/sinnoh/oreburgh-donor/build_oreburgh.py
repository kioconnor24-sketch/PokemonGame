#!/usr/bin/env python3
"""Pinned off-engine Oreburgh preflight and existing-art mine B2 candidate.

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


def prepare(donor, engine, out):
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
    images, palettes = [], {}
    for bank, folder in enumerate(('primary/general', 'secondary/cave')):
        prefix = 'data/tilesets/' + folder + '/'
        images.append(dual.indexed(local(prefix+'tiles.png')))
        for i in (range(6) if bank == 0 else range(6, 16)):
            palettes[i] = base.palette(local(prefix+'palettes/%02d.pal' % i))
    dependencies = dual.closure(raw, [primary, records], images)
    preview = dual.render(raw, [primary, records], images, palettes, 32, 28)
    # Reuse the existing converter's complete-map C/E and identity validation;
    # no competing binary conversion path is introduced here.
    manifest = pilot.draft_manifest(pilot.analyze(donor, name, REVISION))
    manifest.update(target_map_id=header['id'], target_primary_tileset='gTileset_General',
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
                'B1 four-to-one basement warp needs source-grounded reciprocal normalization',
                'No registry, section IDs, source events, story, encounters, engine install or ROM acceptance'])
    out.mkdir(parents=True)
    bank = out / 'banks/cave'
    bank.mkdir(parents=True)
    (bank/'metatiles.bin').write_bytes(records)
    (bank/'metatile_attributes.bin').write_bytes(attrs)
    (out/'staged').mkdir()
    (out/'staged/OreburghMine_B2F.bin').write_bytes(staged)
    preview.save(out/'OreburghMine_B2F-averon.png')
    for file, value in (('source-inspection.json', inspection), ('conversion-receipt.json', receipt)):
        (out/file).write_text(json.dumps(value, indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('donor', 'engine', 'out'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.donor, args.engine, args.out), indent=2))
