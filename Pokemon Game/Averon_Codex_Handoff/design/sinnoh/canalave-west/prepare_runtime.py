#!/usr/bin/env python3
"""Install four already converted Canalave/Route218 maps/art in an exact-base DEV checkout.

No production identifiers or source art are authored here. Production nineteen-map prefix and saved identities remain unchanged.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
BASE='d855ff86785a744264788ff39815cc70581e4c94'
ENGINE='Pokemon Game/engine/'
MAPS={'Route218_East':(13,9),'Route218':(64,32),'Route218_West':(13,9),'CanalaveCity':(38,64)}
spec=importlib.util.spec_from_file_location('canalave_runtime_pack',HERE/'adapt_gate_art.py')
art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
base=art.shared.pack.accepted.base
sha=lambda data:hashlib.sha256(data).hexdigest()
encode=lambda data:(json.dumps(data,indent=2)+'\n').encode()


def asset_bindings(headers,name):
    block=re.search(r'const struct Tileset gTileset_'+re.escape(name)+r' =\s*\{(.*?)\};',headers,re.S)
    if not block:raise ValueError('existing tileset declaration missing: '+name)
    result={}
    for field in ('tiles','palettes','callback'):
        value=re.search(r'\.'+field+r'\s*=\s*(\w+)\s*,',block[1])
        if not value:raise ValueError('existing asset binding missing: '+name+'/'+field)
        result[field]=value[1]
    return result


def inputs(repo):
    pins=json.loads((HERE/'runtime-base-input-hashes.json').read_text())
    engine=Path(repo)/ENGINE
    data={p:base.verified_file(Path(repo),Path(ENGINE)/p,'HEAD') for p in pins}
    if any(sha(data[p])!=h for p,h in pins.items()):raise ValueError('current baseline inputs differ')
    return data


def assemble(repo):
    repo=Path(repo).resolve();before=inputs(repo)
    groups=json.loads(before['data/maps/map_groups.json']);layouts=json.loads(before['data/layouts/layouts.json'])
    names=groups['gMapGroup_Sinnoh'];prior=list(names);group=groups['group_order'].index('gMapGroup_Sinnoh')
    if len(names)!=19 or len(set(names))!=19 or set(MAPS)&set(names):raise ValueError('exact current19-slot prefix required')
    pins=before['test/data/averon_map_registry_slots.inc'].decode();marker=f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 19, 1)'
    if pins.count(marker)!=1:raise ValueError('registry count mismatch')
    pins=pins.replace(marker,f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 23, 1)')
    files={};symbols={};declarations='\n';headers='\n';metatiles='\n';includes=[]
    for folder,graphics in [('outdoor-family','General'),('gate-art','Building')]:
        prefix='data/tilesets/primary/'+graphics.lower()+'/'
        for name in ('metatiles.bin','metatile_attributes.bin'):
            suffix='primary-metatiles.bin' if name=='metatiles.bin' else 'primary-attributes.bin'
            if (HERE/folder/suffix).read_bytes()!=before[prefix+name]:
                raise ValueError('native '+graphics+' metadata prefix differs from candidate')
    for family,secondary,graphics,folder in [('OutdoorSecondary',True,'Rustboro','outdoor-family'),('GateSecondary',True,'Shop','gate-art')]:
        bank='secondary';symbol='CanalaveDev'+family;path='data/tilesets/secondary/canalave_dev_'+family.lower()+'/'
        records=(HERE/folder/'secondary-metatiles.bin').read_bytes()
        attrs=(HERE/folder/'secondary-attributes.bin').read_bytes()
        if not records or len(records)%16 or len(records)>8192 or len(attrs)*8!=len(records):raise ValueError('invalid metadata bank')
        files[path+'metatiles.bin']=records;files[path+'metatile_attributes.bin']=attrs
        symbols[family]='gTileset_'+symbol
        bindings=asset_bindings(before['src/data/tilesets/headers.h'].decode(),graphics)
        declarations+=f'extern const struct Tileset gTileset_{symbol};\n'
        metatiles+=f'const u16 gMetatiles_{symbol}[] = INCBIN_U16("{path}metatiles.bin");\nconst u16 gMetatileAttributes_{symbol}[] = INCBIN_U16("{path}metatile_attributes.bin");\n'
        headers+=f'const struct Tileset gTileset_{symbol} = {{ .isCompressed=TRUE, .isSecondary={"TRUE" if secondary else "FALSE"}, .tiles={bindings["tiles"]}, .palettes={bindings["palettes"]}, .metatiles=gMetatiles_{symbol}, .metatileAttributes = gMetatileAttributes_{symbol}, .callback={bindings["callback"]} }};\n'
    source_headers={};layout_ids={d['id'] for d in layouts['layouts']}
    for slot,(name,(w,h)) in enumerate(MAPS.items(),19):
        folder=HERE/'staged'/name;header=json.loads((folder/'map.json').read_text());source_headers[name]=copy.deepcopy(header)
        if header['region_map_section']!='MAPSEC_PENDING_OWNER' or header['layout'] in layout_ids:
            raise ValueError('not an unregistered pending source map')
        if any(header[k] for k in ('object_events','coord_events','bg_events')):raise ValueError('unexpected gameplay events')
        raw=(folder/'averon-map.bin').read_bytes();border=(folder/'border.bin').read_bytes()
        if len(raw)!=w*h*2 or (w+15)*(h+14)>10240:raise ValueError('map footprint/buffer exceeded')
        header['region_map_section']='MAPSEC_ROUTE_201'
        files[f'data/maps/{name}/map.json']=encode(header);files[f'data/maps/{name}/scripts.inc']=(name+'_MapScripts::\n\t.byte 0\n').encode()
        files[f'data/layouts/{name}/map.bin']=raw;files[f'data/layouts/{name}/border.bin']=border
        layouts['layouts'].append(dict(id=header['layout'],name=name+'_Layout',width=w,height=h,primary_tileset='gTileset_Building' if name.endswith(('_East','_West')) else 'gTileset_General',
            secondary_tileset=symbols['GateSecondary' if name.endswith(('_East','_West')) else 'OutdoorSecondary'],layout_version='emerald',border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin'))
        layout_ids.add(header['layout']);names.append(name)
        pins+=f'REGISTRY_SLOT({group}, {slot}, {header["id"]}, {name}, 1)\n';includes.append(f'\t.include "data/maps/{name}/scripts.inc"')
    by_id={h['id']:h for h in source_headers.values()}
    for header in source_headers.values():
        for warp in header['warp_events']:
            if warp['dest_map'] not in by_id or not 0<=int(warp['dest_warp_id'])<len(by_id[warp['dest_map']]['warp_events']):
                raise ValueError('foreign or out-of-bounds warp')
        for connection in header['connections']:
            other=by_id.get(connection['map']);opposite={'up':'down','down':'up','left':'right','right':'left'}[connection['direction']]
            if other is None or dict(map=header['id'],direction=opposite,offset=-connection['offset']) not in other['connections']:
                raise ValueError('nonreciprocal connection')
    for path,extra in [('include/tilesets.h',declarations),('src/data/tilesets/headers.h',headers),('src/data/tilesets/metatiles.h',metatiles),
                       ('data/event_scripts.s','\n'+'\n'.join(includes)+'\n')]:files[path]=before[path]+extra.encode()
    files['data/maps/map_groups.json']=encode(groups);files['data/layouts/layouts.json']=encode(layouts)
    files['test/data/averon_map_registry_slots.inc']=pins.encode();files['test/averon_canalave_runtime.c']=(HERE/'native-runtime.c').read_bytes()
    return files,dict(status='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE',base=BASE,existing_map_names_preserved=prior,
        temporary_map_slots={n:19+i for i,n in enumerate(MAPS)},source_headers=source_headers,
        dev_surrogate='MAPSEC_ROUTE_201217 only in disposable ROM; never production met-origin acceptance',files={p:sha(d) for p,d in sorted(files.items())})


def install(repo):
    repo=Path(repo).resolve();engine=repo/ENGINE
    if not base.git(repo,'branch','--show-current').decode().strip().startswith('codex/canalave-runtime-scratch-') or not (engine/'.map_qa_throwaway').is_file():
        raise ValueError('explicit disposable Canalave branch and marker required')
    if base.git(repo,'rev-parse','HEAD').decode().strip()!=BASE:raise ValueError('exact production baseline required')
    status=base.git(repo,'status','--porcelain','--untracked-files=normal','--',ENGINE).decode().splitlines()
    if status not in ([],['?? "Pokemon Game/engine/.map_qa_throwaway"']):raise ValueError('refusing dirty runtime source')
    files,receipt=assemble(repo)
    for path in files:
        target=(engine/path).resolve()
        if not target.is_relative_to(engine.resolve()):raise ValueError('output path escapes engine')
        try:base.git(repo,'cat-file','-e','HEAD:'+ENGINE+path)
        except subprocess.CalledProcessError:
            if target.exists():raise ValueError('untracked output exists')
    for path,data in files.items():
        target=engine/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--install',action='store_true');args=p.parse_args()
    print(json.dumps(install(args.repo) if args.install else assemble(args.repo)[1],indent=2))
