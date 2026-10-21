#!/usr/bin/env python3
"""Stage pinned City/207 geography; no graphics, production IDs or installer.

Uses the existing donor converter for source identity validation. Changes to
collision are limited to explicitly closed unbuilt doors/edges. Sparse source
warp IDs are retained as DATA, not silently packed into an engine event array.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('accepted_oreburgh', HERE / 'build_oreburgh.py')
accepted = importlib.util.module_from_spec(spec)
spec.loader.exec_module(accepted)
base, pilot = accepted.base, accepted.pilot
KEEP = {'OreburghCity': (0, 11, 12, 13, 14), 'Route207': ()}
CONNECTIONS = {
    'OreburghCity': [dict(map='MAP_ROUTE207', offset=35, direction='up')],
    'Route207': [dict(map='MAP_OREBURGH_CITY', offset=-35, direction='down')],
}


def cells(raw, width, height):
    if width <= 0 or height <= 0 or len(raw) != width * height * 2:
        raise ValueError('invalid dimensions/cell count')
    return list(struct.unpack('<%dH' % (width * height), raw))


def stage_map(name, header, raw, width, height):
    """Pure staging, retaining elevations and source metatile/warp identities."""
    if name not in KEEP:
        raise ValueError('unreviewed map')
    before = cells(raw, width, height)
    result, reasons = list(before), {}
    warps = header['warp_events']
    anchors = set()
    for warp in warps:
        x, y = warp['x'], warp['y']
        if (not isinstance(x, int) or not isinstance(y, int)
                or not 0 <= x < width or not 0 <= y < height
                or not isinstance(warp['elevation'], int)
                or not 0 <= warp['elevation'] <= 15):
            raise ValueError('invalid warp coordinate/elevation')
        if (x, y) in anchors:
            raise ValueError('duplicate warp anchor')
        anchors.add((x, y))
    if any(index >= len(warps) for index in KEEP[name]):
        raise ValueError('missing retained source warp')
    retained = { (warps[i]['x'], warps[i]['y']) for i in KEEP[name] }

    def close(x, y, why):
        if (x, y) in retained:
            raise ValueError('closure collides with retained warp')
        index = y * width + x
        result[index] = (result[index] & ~0xC00) | 0x400
        reasons[index] = why

    for index, warp in enumerate(warps):
        if index not in KEEP[name]:
            close(warp['x'], warp['y'], 'unbuilt source destination')
    for y in range(height):
        close(0, y, 'unbuilt west edge')
        close(width - 1, y, 'unbuilt east edge')
    # Source offset +35/-35 leaves only these overlapping spans. All other
    # exterior cells are explicitly closed, even if already solid in source.
    for x in range(width):
        if name != 'OreburghCity' or x < 35:
            close(x, 0, 'unbuilt north edge')
        if name != 'Route207' or x >= 35:
            close(x, height - 1, 'unbuilt south edge')
    closures = [dict(x=i % width, y=i // width, before=before[i], after=result[i], reason=reasons[i])
                for i in sorted(reasons) if before[i] != result[i]]
    if any((old ^ new) & ~0xC00 for old, new in zip(before, result)):
        raise ValueError('metatile or elevation changed')
    staged_warps = [dict(source_warp_id=i, **warps[i]) for i in KEEP[name]]
    return struct.pack('<%dH' % len(result), *result), staged_warps, closures


def validate_links(headers, gate):
    """Fail on a source identity/offset change; never guess a destination."""
    city, route = headers['OreburghCity'], headers['Route207']
    if (city['connections'] != CONNECTIONS['OreburghCity']
            or route['connections'] != [
                dict(map='MAP_ROUTE206', offset=2, direction='up'),
                *CONNECTIONS['Route207']]):
        raise ValueError('source reciprocal connection changed')
    expected = [(6, 12, 0, 'MAP_OREBURGH_GATE_1F', '1'),
                (50, 57, 0, 'MAP_OREBURGH_MINE_B1F', '0'),
                (51, 57, 0, 'MAP_OREBURGH_MINE_B1F', '0'),
                (52, 57, 0, 'MAP_OREBURGH_MINE_B1F', '1'),
                (53, 57, 0, 'MAP_OREBURGH_MINE_B1F', '1')]
    shape = lambda w: (w['x'], w['y'], w['elevation'], w['dest_map'], str(w['dest_warp_id']))
    if ([shape(city['warp_events'][i]) for i in KEEP['OreburghCity']] != expected
            or shape(gate['warp_events'][1]) != (25, 20, 0, 'MAP_OREBURGH_CITY', '0')
            or [shape(w) for w in route['warp_events']] != [
                (52, 5, 0, 'MAP_MT_CORONET_1F_SOUTH', '0')]):
        raise ValueError('source corridor warp identity changed')
    b1 = json.loads((HERE/'staged/OreburghMine_B1F/map.json').read_text())
    b2 = json.loads((HERE/'staged/OreburghMine_B2F/map.json').read_text())
    accepted.mine_warps(b1['warp_events'], b2['warp_events'])
    for warp in b1['warp_events'][:2]:
        target = city['warp_events'][int(warp['dest_warp_id'])]
        if target['dest_map'] != b1['id'] or int(target['dest_warp_id']) not in (0, 1):
            raise ValueError('city/mine reciprocal warp changed')


def build(donor, out):
    donor, out = Path(donor).resolve(), Path(out).resolve()
    if out.exists() or 'engine' in out.parts or out.is_relative_to(donor):
        raise ValueError('new off-engine/off-donor output required')
    if base.git(donor, 'rev-parse', 'HEAD').decode().strip() != accepted.REVISION:
        raise ValueError('wrong donor revision')
    consumed = {}

    def read(rel):
        raw = base.verified_file(donor, rel, accepted.REVISION)
        consumed[rel] = base.sha(raw)
        return raw

    layouts = json.loads(read('data/layouts/layouts.json'))['layouts']
    headers, inputs = {}, {}
    for name in KEEP:
        header = json.loads(read('data/maps/'+name+'/map.json'))
        layout = next(x for x in layouts if x['id'] == header['layout'])
        raw = read(layout['blockdata_filepath'])
        width, height, blob = accepted.MAPS[name]
        if (layout['width'], layout['height']) != (width, height):
            raise ValueError('source layout dimensions changed')
        if hashlib.sha1(b'blob %d\0' % len(raw) + raw).hexdigest() != blob:
            raise ValueError('source geometry blob changed')
        border = read(layout['border_filepath'])
        if len(border) != 8:
            raise ValueError('invalid source border')
        headers[name], inputs[name] = header, (raw, border)
    gate = json.loads(read('data/maps/OreburghGate_1F/map.json'))
    validate_links(headers, gate)
    receipt = dict(status='OFF_ENGINE_GEOMETRY_ONLY_GRAPHICS_PENDING',
                   donor_revision=accepted.REVISION, maps={}, consumed_donor_sha256=consumed,
                   gate_dependency=dict(source_warp_id=1, x=25, y=20,
                       destination='MAP_OREBURGH_CITY', destination_source_warp_id=0,
                       status='CLOSED_IN_PR194_OPEN_ONLY_IN_COHERENT_TEST_TREE'),
                   mine_dependency='reuse merged198; retain source City11/14 and all6 B1 warps',
                   limits=['No donor pixels/palettes/music or gameplay copied',
                           'Graphics remapping and callback/bridge validation NOT COMPLETED',
                           'Sparse source warp IDs are not an engine event array',
                           'No permanent sections, production install, ROM or mGBA acceptance'])
    pending = []
    for name in KEEP:
        raw, border = inputs[name]
        width, height, blob = accepted.MAPS[name]
        manifest = pilot.draft_manifest(pilot.analyze(donor, name, accepted.REVISION))
        manifest.update(target_map_id='SOURCE_ONLY_'+name,
                        target_primary_tileset='DONOR_ONLY_General',
                        target_secondary_tileset='DONOR_ONLY_Jubilife')
        for key, record in manifest['metatiles'].items():
            record.update(target=int(key), behavior_verified=True, graphics_verified=True)
        # SAME donor bank on both sides: proves converter identity only, never
        # Averon visual compatibility. No bank pixels are read or written here.
        with tempfile.TemporaryDirectory(prefix='oreburgh-source-identity-') as tmp:
            target = Path(tmp)/'source.bin'
            pilot.convert(donor, name, manifest, target)
            if target.read_bytes() != raw:
                raise ValueError('converter changed source geometry')
        staged, warps, closures = stage_map(name, headers[name], raw, width, height)
        info = dict(name=name, status=receipt['status'], dimensions=[width, height],
                    section=None, source_warp_events=warps,
                    source_connection_events=CONNECTIONS[name], collision_closures=closures,
                    object_events=[], coord_events=[], bg_events=[], scripts=[], encounters=[])
        used = {x & 1023 for x in cells(raw, width, height)}
        receipt['maps'][name] = dict(git_blob=blob, source_sha256=base.sha(raw),
            staged_sha256=base.sha(staged), dimensions=[width,height],
            used_primary=sum(x < 512 for x in used), used_secondary=sum(x >= 512 for x in used),
            closed_collision_cells=len(closures), all_elevation_and_metatile_bits_preserved=True,
            excluded_event_counts={k:len(headers[name].get(k, []))
                                   for k in ('object_events','coord_events','bg_events')})
        pending.append((name, raw, border, staged, info))
    out.mkdir(parents=True)
    for name, raw, border, staged, info in pending:
        target = out/name
        target.mkdir()
        for filename, data in (('source.bin',raw),('map.bin',staged),('border.bin',border)):
            (target/filename).write_bytes(data)
        (target/'map.json').write_text(json.dumps(info,indent=2)+'\n')
        width, height = info['dimensions']
        image = Image.new('RGB',(width*6,height*6))
        draw = ImageDraw.Draw(image)
        colors = [(183,216,170),(48,56,62),(164,115,64),(190,124,165)]
        for i, cell in enumerate(cells(staged,width,height)):
            x,y=i%width*6,i//width*6
            draw.rectangle((x,y,x+5,y+5),fill=colors[(cell>>10)&3])
        for warp in info['source_warp_events']:
            x,y=warp['x']*6,warp['y']*6
            draw.rectangle((x,y,x+5,y+5),fill=(50,100,255))
        image.save(target/'collision.png')
    (out/'corridor-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--donor',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.donor,args.out),indent=2))
