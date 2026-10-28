"""Extend the reviewed W25 DEV scene with the existing Coronet South passage.

Source preparation only: no installer, production origins, new converter or art.
The five packet-D maps remain in their existing W25 context (50 DEV maps total).
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent
NAME = 'MtCoronet_1F_South'
MAP_ID = 'MAP_MT_CORONET_1F_SOUTH'
INPUTS = {'source-map.bin', 'source-border.bin', 'source-header.json', 'source-attributes.json',
          'averon-map.bin', 'averon-border.bin', 'primary-metatiles.bin', 'primary-attributes.bin',
          'secondary-metatiles.bin', 'secondary-attributes.bin', 'cave-art-receipt.json'}
sha = lambda b: hashlib.sha256(b).hexdigest()
encode = lambda x: (json.dumps(x, indent=2) + '\n').encode()
words = lambda b: struct.unpack('<%dH' % (len(b) // 2), b)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def south_inputs(repo):
    pins = json.loads((HERE / 'source-pins.json').read_text())
    if set(pins['files']) != INPUTS:
        raise ValueError('exact reused South inventory required')
    data = {n: (HERE / 'inputs' / n).read_bytes() for n in INPUTS}
    if any(sha(data[n]) != pins['files'][n]['sha256'] for n in INPUTS):
        raise ValueError('reused South source differs')
    receipt = json.loads(data['cave-art-receipt.json'])
    for path, expected in receipt['existing_averon_sha256'].items():
        raw = (Path(repo) / 'Pokemon Game/engine' / path).read_bytes()
        canonical = subprocess.check_output(['git', 'show', 'HEAD:Pokemon Game/engine/' + path], cwd=repo)
        # Git's declared *.pal eol=crlf checkout preserves the same RGB values.
        if sha(canonical) != expected or not (raw == canonical or
                path.endswith('.pal') and raw.replace(b'\r\n', b'\n') == canonical):
            raise ValueError('existing graphics dependency differs: ' + path)
    if any(len(data[n]) != size for n, size in [('source-map.bin',2688), ('averon-map.bin',2688), ('source-border.bin',8), ('averon-border.bin',8)]):
        raise ValueError('exact South block and border sizes required')
    original = words(data['source-map.bin'] + data['source-border.bin'])
    remapped = words(data['averon-map.bin'] + data['averon-border.bin'])
    if len(original) != 1348 or len(remapped) != 1348:
        raise ValueError('South42x32 plus four border cells required')
    attrs = json.loads(data['source-attributes.json'])['used_source_attribute_words']
    banks = [words(data[b + '-attributes.bin']) for b in ('primary', 'secondary')]
    for bank in ('primary', 'secondary'):
        records, attributes = data[bank + '-metatiles.bin'], data[bank + '-attributes.bin']
        if not records or len(records) > 8192 or len(records) % 16 or len(attributes) * 8 != len(records):
            raise ValueError('invalid reused metatile bank')
    for before, after in zip(original, remapped):
        idx = after & 1023
        if before & 0xFC00 != after & 0xFC00 or banks[idx >= 512][idx % 512] != attrs[str(before & 1023)]:
            raise ValueError('South collision/elevation/full behavior changed')
    if (remapped[170] != 0x0604 or banks[1][4] != 0x1000):
        raise ValueError('existing native cave wall role differs')
    if (original[299], original[876], original[113]) != (0x3607, 0x3607, 0x33A5):
        raise ValueError('quarantined source ports changed')
    donor = list(original[:1344])
    donor[299] = donor[876] = 0x3207
    if sha(struct.pack('<1344H', *donor)) != pins['original_donor_map_sha256']:
        raise ValueError('original donor collision reconstruction differs')
    return data, pins


def extend(files, data, pins, bindings):
    """Pure bounded join; existing 49 slots/layouts/native fixtures stay intact."""
    result = dict(files)
    group_path = 'data/maps/map_groups.json'
    groups = json.loads(files[group_path])
    names = groups['gMapGroup_Sinnoh']
    if len(names) != 49 or NAME in names or names[-3:] != ['Route207', 'OreburghMine_B1F', 'OreburghMine_B2F']:
        raise ValueError('exact post-C49 source required')
    route_path = 'data/maps/Route207/map.json'
    route = json.loads(files[route_path])
    if route['warp_events']:
        raise ValueError('Route207 already has a passage')
    route['warp_events'] = pins['donor_headers']['data/maps/Route207/map.json']['warp_events']
    expected = [dict(x=52, y=5, elevation=0, dest_map=MAP_ID, dest_warp_id='0')]
    if route['warp_events'] != expected:
        raise ValueError('donor Route207 reciprocal anchor differs')
    route_block = 'data/layouts/Route207/map.bin'
    raw = bytearray(files[route_block])
    if len(raw) != 4096 or struct.unpack_from('<H', raw, 2 * (5 * 64 + 52))[0] != 0x04A7:
        raise ValueError('closed Route207 doorway changed')
    struct.pack_into('<H', raw, 2 * (5 * 64 + 52), 0x00A7)  # original donor C/E, existing native door art
    result[route_block], result[route_path] = bytes(raw), encode(route)
    header = json.loads(data['source-header.json'])
    if header['warp_events'] or any(header[k] for k in ('connections', 'object_events', 'coord_events', 'bg_events')):
        raise ValueError('neutral South header required')
    events = pins['donor_headers']['data/maps/MtCoronet_1F_South/map.json']['warp_events']
    if events != [dict(x=5, y=7, elevation=0, dest_map='MAP_ROUTE207', dest_warp_id='0'),
                  dict(x=36, y=20, elevation=0, dest_map='MAP_ROUTE208', dest_warp_id='0')]:
        raise ValueError('donor South ports differ')
    header.update(warp_events=events[:1], region_map_section='MAPSEC_ROUTE_201', music='MUS_PETALBURG_WOODS')
    south = bytearray(data['averon-map.bin'])
    if [struct.unpack_from('<H', south, 2*i)[0] for i in (299, 876, 113)] != [0x361A, 0x361A, 0x3222]:
        raise ValueError('converted South ports differ')
    struct.pack_into('<H', south, 2*299, 0x321A)  # restore original west arrow collision, not flat terrain
    struct.pack_into('<H', south, 2*876, 0x3604)  # native cave wall closes unbuilt Route208
    struct.pack_into('<H', south, 2*113, 0x3604)  # native cave wall closes unbuilt 2F ladder
    prefix = 'data/layouts/' + NAME + '/'
    result[prefix+'map.bin'], result[prefix+'border.bin'] = bytes(south), data['averon-border.bin']
    result['data/maps/'+NAME+'/map.json'] = encode(header)
    result['data/maps/'+NAME+'/scripts.inc'] = (NAME+'_MapScripts:\n\t.byte 0\n').encode()
    groups['gMapGroup_Sinnoh'] = names + [NAME]
    result[group_path] = encode(groups)
    layouts_path = 'data/layouts/layouts.json'
    layouts = json.loads(files[layouts_path])
    if any(x['id'] == header['layout'] for x in layouts['layouts']):
        raise ValueError('South layout already registered')
    layouts['layouts'].append(dict(id=header['layout'], name=NAME+'_Layout', width=42, height=32,
        primary_tileset='gTileset_PacketDSouthPrimary', secondary_tileset='gTileset_PacketDSouthSecondary',
        layout_version='emerald', border_filepath=prefix+'border.bin', blockdata_filepath=prefix+'map.bin'))
    result[layouts_path] = encode(layouts)
    registry = 'test/data/averon_map_registry_slots.inc'
    g = groups['group_order'].index('gMapGroup_Sinnoh')
    marker = f'REGISTRY_GROUP({g}, gMapGroup_Sinnoh, 49, 1)'
    text = files[registry].decode()
    if text.count(marker) != 1:
        raise ValueError('post-C49 registry pin differs')
    result[registry] = (text.replace(marker, f'REGISTRY_GROUP({g}, gMapGroup_Sinnoh, 50, 1)')+
                        f'REGISTRY_SLOT({g}, 49, {MAP_ID}, {NAME}, 1)\n').encode()
    extras = dict.fromkeys(('include/tilesets.h', 'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h'), '')
    for bank, label in [('primary', 'Primary'), ('secondary', 'Secondary')]:
        symbol = 'PacketDSouth'+label; folder = f'data/tilesets/{bank}/packet_d_south/'
        result[folder+'metatiles.bin'], result[folder+'metatile_attributes.bin'] = data[bank+'-metatiles.bin'], data[bank+'-attributes.bin']
        b = bindings[bank]
        extras['include/tilesets.h'] += f'extern const struct Tileset gTileset_{symbol};\n'
        extras['src/data/tilesets/metatiles.h'] += f'const u16 gMetatiles_{symbol}[] = INCBIN_U16("{folder}metatiles.bin");\nconst u16 gMetatileAttributes_{symbol}[] = INCBIN_U16("{folder}metatile_attributes.bin");\n'
        extras['src/data/tilesets/headers.h'] += f'const struct Tileset gTileset_{symbol} = {{ .isCompressed=TRUE, .isSecondary={"TRUE" if bank == "secondary" else "FALSE"}, .tiles={b["tiles"]}, .palettes={b["palettes"]}, .metatiles=gMetatiles_{symbol}, .metatileAttributes = gMetatileAttributes_{symbol}, .callback={b["callback"]} }};\n'
    for path, extra in extras.items():
        if ('gTileset_PacketDSouth' in files[path].decode()):
            raise ValueError('South tileset symbol already exists')
        result[path] = files[path] + extra.encode()
    result['data/event_scripts.s'] = files['data/event_scripts.s'] + f'\n\t.include "data/maps/{NAME}/scripts.inc"\n'.encode()
    result['test/averon_packet_d.c'] = NATIVE.encode()
    return result


NATIVE = '''// Generated DEV fixture only: no production saved identity.
#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "pokemon.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
STATIC_ASSERT(MAPSEC_NONE == 215, packet_d_none_fixed);
STATIC_ASSERT(MAPSEC_OREBURGH_CITY == 227, packet_d_city_fixed);
STATIC_ASSERT(MAPSEC_COUNT == 228, packet_d_no_new_origin);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, packet_d_box_fixed);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, packet_d_party_fixed);
#define HEADER(id) Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(id), MAP_NUM(id))
TEST("Averon DEV packet D preserves reciprocal Route207 and Coronet South anchors")
{
    const struct MapHeader *south = HEADER(MAP_MT_CORONET_1F_SOUTH);
    const struct MapEvents *route = HEADER(MAP_ROUTE207)->events;
    const struct WarpEvent *a = &route->warps[0], *b = &south->events->warps[0];
    EXPECT_EQ(route->warpCount, 1); EXPECT_EQ(south->events->warpCount, 1);
    EXPECT_EQ(a->x, 52); EXPECT_EQ(a->y, 5);
    EXPECT_EQ(b->x, 5); EXPECT_EQ(b->y, 7);
    EXPECT_EQ(a->mapGroup, MAP_GROUP(MAP_MT_CORONET_1F_SOUTH));
    EXPECT_EQ(a->mapNum, MAP_NUM(MAP_MT_CORONET_1F_SOUTH)); EXPECT_EQ(a->warpId, 0);
    EXPECT_EQ(b->mapGroup, MAP_GROUP(MAP_ROUTE207));
    EXPECT_EQ(b->mapNum, MAP_NUM(MAP_ROUTE207)); EXPECT_EQ(b->warpId, 0);
    EXPECT_EQ(MAP_NUM(MAP_MT_CORONET_1F_SOUTH), 49);
    EXPECT_EQ(south->regionMapSectionId, MAPSEC_ROUTE_201);
    EXPECT_EQ(south->mapLayout->width, 42); EXPECT_EQ(south->mapLayout->height, 32);
}
TEST("Averon DEV packet D opens only the original west port and visibly closes unbuilt dependencies")
{
    const struct MapLayout *south = HEADER(MAP_MT_CORONET_1F_SOUTH)->mapLayout;
    const struct MapLayout *route = HEADER(MAP_ROUTE207)->mapLayout;
    EXPECT_EQ(route->map[5*64+52], 0x00A7);
    EXPECT_EQ(south->map[7*42+5], 0x321A);
    EXPECT_EQ(south->map[20*42+36], 0x3604);
    EXPECT_EQ(south->map[2*42+29], 0x3604);
    EXPECT((south->width+15)*(south->height+14) <= 10240);
}
'''


def assemble(repo):
    w25 = module('packet_d_existing_w25', DESIGN/'cycling-road-join/prepare_current_runtime.py')
    files, receipt = w25.compose(repo)
    data, pins = south_inputs(repo)
    existing = module('packet_d_existing_bindings', DESIGN/'eterna-cycle/prepare_runtime.py')
    headers = (Path(repo)/'Pokemon Game/engine/src/data/tilesets/headers.h').read_text()
    result = extend(files, data, pins, {k: existing.asset_bindings(headers, name)
        for k, name in [('primary', 'General'), ('secondary', 'Cave')]})
    return result, dict(status='50_MAP_DEV_SOURCE_ONLY_NOT_PRODUCTION_OR_RUNTIME_ACCEPTANCE',
        production_engine_tree='b06114f532e98f331dcdf64481fd01e726073fdf', reused_south_commit=pins['reused_commit'],
        packet_d=['Route206_North','Route206','Route206_South','Route207',NAME],
        original_49_maps_preserved=True, closed_dependencies=['Route208','MtCoronet2F'],
        dev_origin='217 surrogate only; no production allocation or saved-format change',
        files={p:sha(b) for p,b in sorted(result.items())})
