#!/usr/bin/env python3
"""Isolated Route207 art candidate made exclusively from existing Averon art.

This is an explicit style adaptation, not donor visual equivalence. No tile or
palette pixels are copied from donor. Source behavior/layer attributes are kept.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('oreburgh_source',HERE/'build_oreburgh.py')
source=importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)

# Source-index -> reviewed existing Averon General art record. These are
# MAP-LOCAL GRAPHICS indices, never permanent saved-location identities.
PRIMARY={147:175,148:175,155:175,156:175,163:175,164:175}
SECONDARY={515:123,516:121,517:125,521:289,523:112,524:114,
           536:225,850:None,852:145,853:None,855:None,859:123,
           860:145,861:13,868:145}


def record(raw,index):
    if len(raw)%16 or not 0 <= index < len(raw)//16:
        raise ValueError('missing/misaligned existing art record')
    return list(struct.unpack_from('<8H',raw,index*16))


def banks(raw, border, general, general_attrs, rustboro, source_attrs):
    if (len(raw)!=64*32*2 or len(border)!=8 or len(general)!=512*16
            or len(general_attrs)!=512*2 or len(rustboro)%16
            or len(source_attrs)!=2 or len(source_attrs[0])!=1024
            or len(source_attrs[1])%2):
        raise ValueError('Route207 bank/dimension contract changed')
    used={x[0]&1023 for x in struct.iter_unpack('<H',raw+border)}
    expected=set(json.loads((HERE/'source-inspection.json').read_text())['Route207']['used_primary'])
    # The actual pinned border also uses478/479 (tree pieces), absent from map cells.
    if (border != bytes.fromhex('d601d701de01df01')
            or not used.issubset(expected|{478,479}|set(SECONDARY))
            or not set(SECONDARY).issubset(used)):
        raise ValueError('unreviewed Route207 used-metatile dependency')
    primary,pa=bytearray(general),bytearray(general_attrs)
    count=max(SECONDARY)-512+1
    secondary,sa=bytearray(count*16),bytearray(count*2)
    wood=record(rustboro,528-512)
    for mid in sorted(used):
        bank,index=divmod(mid,512)
        if (index+1)*2>len(source_attrs[bank]):
            raise ValueError('missing source behavior/layer word')
        if bank==0:
            words=record(general,PRIMARY.get(mid,mid))
        elif SECONDARY[mid] is not None:
            words=record(general,SECONDARY[mid])
            if mid==521:
                # Existing sand texture with existing brown palette3 instead
                # of palette5: brown mine-country soil, no donor palette.
                words=[(w&0xFFF)|0x3000 for w in words]
            if mid in (523,524):
                words[:4]=[(w&0xFFF)|0x3000 for w in record(general,289)[:4]]
        elif mid==853:
            words=wood
        elif mid==855:
            words=[wood[i]^0x400 for i in (1,0,3,2,5,4,7,6)]
        else:  #850: central planks, without either edge post.
            words=[wood[i] for i in (1,1,3,3,5,5,7,7)]
        # All chosen records use existing General pixels and palettes0–5.
        # No secondary animation/callback or replacement pixel bank required.
        if any((w&1023)>=512 or (w>>12)>=6 for w in words):
            raise ValueError('unreviewed graphics/palette dependency')
        records,attrs=(primary,pa) if bank==0 else (secondary,sa)
        struct.pack_into('<8H',records,index*16,*words)
        attrs[index*2:index*2+2]=source_attrs[bank][index*2:index*2+2]
    return bytes(primary),bytes(pa),bytes(secondary),bytes(sa)


def build(donor, engine, out):
    donor,engine,out=map(lambda p:Path(p).resolve(),(donor,engine,out))
    if out.exists() or 'engine' in out.parts or out.is_relative_to(donor):
        raise ValueError('new off-engine/off-donor output required')
    if source.base.git(donor,'rev-parse','HEAD').decode().strip()!=source.REVISION:
        raise ValueError('wrong donor revision')
    root=Path(source.base.git(engine,'rev-parse','--show-toplevel').decode().strip())
    revision=source.base.git(engine,'rev-parse','HEAD').decode().strip()
    consumed={}
    def existing(rel):
        value=source.base.verified_file(root,engine.relative_to(root)/rel,revision)
        consumed[rel]=source.base.sha(value)
        return value
    donor_hashes={}
    def donor_data(rel):
        value=source.base.verified_file(donor,rel,source.REVISION)
        donor_hashes[rel]=source.base.sha(value)
        return value
    for contract in ('include/fieldmap.h','include/constants/metatile_behaviors.h'):
        if donor_data(contract)!=existing(contract):
            raise ValueError('runtime metadata contract mismatch: '+contract)
    raw=(HERE/'corridor/Route207/map.bin').read_bytes()
    border=(HERE/'corridor/Route207/border.bin').read_bytes()
    original=(HERE/'corridor/Route207/source.bin').read_bytes()
    if source.base.sha(original)!='fe265553a2d3983dd2e007aef1c1b73547bc93028fc35239c3913830d0127fab':
        raise ValueError('wrong staged source geometry')
    if source.base.sha(raw)!='b21dff39fc3f721a48f654d934c5eeecd952458032f95010ca9c1e4482a474e6':
        raise ValueError('wrong reviewed closed-edge geometry')
    expected=json.loads((HERE/'corridor/Route207/map.json').read_text())
    closures={c['y']*64+c['x']:c for c in expected['collision_closures']}
    for i,(old,new) in enumerate(zip(struct.iter_unpack('<H',original),struct.iter_unpack('<H',raw))):
        if old!=new and (i not in closures or closures[i]['before']!=old[0]
                        or closures[i]['after']!=new[0]):
            raise ValueError('undisclosed geometry change')
    general='data/tilesets/primary/general/'
    source_attributes=[donor_data('data/tilesets/'+f+'/metatile_attributes.bin')
                       for f in ('primary/general','secondary/jubilife')]
    p,pa,s,sa=banks(raw,border,existing(general+'metatiles.bin'),
        existing(general+'metatile_attributes.bin'),
        existing('data/tilesets/secondary/rustboro/metatiles.bin'),
        source_attributes)
    im=source.dual.indexed(existing(general+'tiles.png'))
    palettes={i:source.base.palette(existing(general+'palettes/%02d.pal'%i)) for i in range(6)}
    dependencies=source.dual.closure(raw+border,[p,s],[im,im])
    preview=source.dual.render(raw,[p,s],[im,im],palettes,64,32)
    out.mkdir(parents=True)
    for bank,records,attrs in (('primary',p,pa),('secondary',s,sa)):
        folder=out/'banks'/bank;folder.mkdir(parents=True)
        (folder/'metatiles.bin').write_bytes(records)
        (folder/'metatile_attributes.bin').write_bytes(attrs)
    preview.save(out/'averon.png')
    receipt=dict(status='OFF_ENGINE_ROUTE207_ART_CANDIDATE_NOT_ROM_TESTED',
        donor_revision=source.REVISION,engine_revision=revision,
        geometry_sha256=source.base.sha(raw),used_graphics=dependencies,
        existing_averon_sha256=consumed,consumed_donor_metadata_sha256=donor_hashes,
        primary_art_remap=PRIMARY,secondary_art_remap=SECONDARY,
        source_attribute_words={str(mid):struct.unpack_from('<H',source_attributes[mid//512],(mid%512)*2)[0]
                                for mid in dependencies['metatiles']},
        exact_source_behavior_layer_words=True,geometry_changed=False,
        all_graphics_in_existing_general_bank=True,secondary_callback_required=False,
        secondary_records=len(s)//16,secondary_records_remaining=512-len(s)//16,
        limits=['Existing Averon style adaptation; donor visual equality NOT claimed',
                'Gray flat stair art replaces sideways gray flights; donor diagonal movement/elevations retained',
                'Simplified grass/rock/wood transitions; graphical/runtime acceptance pending',
                'City graphics still unfinished; no coherent corridor ROM or saved IDs'])
    (out/'art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ('donor','engine','out'):parser.add_argument('--'+n,required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(build(args.donor,args.engine,args.out),indent=2))
