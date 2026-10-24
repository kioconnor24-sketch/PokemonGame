#!/usr/bin/env python3
"""Guarded current-main nine-map Coronet upper floors DEV installation; external anchors stay closed."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('victory_existing_guard',HERE.parent/'sunyshore-coast/prepare_runtime.py')
coast=importlib.util.module_from_spec(sp);sp.loader.exec_module(coast)
base=coast.base;BASE='9c195964938b5a9c5db37bd114ca6dbcfc1965a3';ENGINE=coast.ENGINE;sha=coast.sha;encode=coast.encode
MAPS={'SinnohMtCoronet_2F': (34, 64), 'SinnohMtCoronet_3F': (28, 34), 'SinnohMtCoronet_OutsideSouth': (46, 40), 'SinnohMtCoronet_OutsideNorth': (50, 46), 'SinnohMtCoronet_4F_Rooms1And2': (64, 30), 'SinnohMtCoronet_4F_Room3': (24, 14), 'SinnohMtCoronet_5F': (26, 28), 'SinnohMtCoronet_6F': (14, 28), 'SinnohMtCoronet_1F_Tunnel_Room': (20, 62)}
source_spec=importlib.util.spec_from_file_location('victory_original_source',HERE.parent/'victory-road-shell/build_shell.py')
source=importlib.util.module_from_spec(source_spec);source_spec.loader.exec_module(source)


def assemble(repo):
    repo=Path(repo).resolve();before=coast.inputs(repo)
    # Native graphics, including every referenced palette and full attributes,
    # must be exactly the source/art candidate inputs. No new bank is installed.
    receipt=json.loads((HERE/'source-receipt.json').read_text())
    for path,h in receipt['source_inputs_sha256'].items():
        if sha((HERE/path).read_bytes())!=h:raise ValueError('tested shell input differs')
    cs=importlib.util.spec_from_file_location('ascent_source_config',HERE/'build_upper_floors.py')
    config=importlib.util.module_from_spec(cs);cs.loader.exec_module(config)
    expected=source.construct(json.loads((HERE/'shell-recipe.json').read_text()),json.loads((HERE/'portal-reference.json').read_text()),config.NAMES,config.IDS,'MAP_HEADER_MT_CORONET_')
    for name in ('SinnohMtCoronet_OutsideSouth','SinnohMtCoronet_OutsideNorth'):
        expected[name][2]['map_type']='MAP_TYPE_ROUTE'
    for path,h in receipt['existing_averon_sha256'].items():
        if sha(base.verified_file(repo,Path(ENGINE)/path,'HEAD'))!=h:raise ValueError('native cave asset differs')
    groups=json.loads(before['data/maps/map_groups.json']);layouts=json.loads(before['data/layouts/layouts.json'])
    prior=list(groups['gMapGroup_Sinnoh']);group=groups['group_order'].index('gMapGroup_Sinnoh')
    if len(prior)!=19 or len(set(prior))!=19 or set(prior)&set(MAPS):raise ValueError('exact original19 prefix required')
    slots=before['test/data/averon_map_registry_slots.inc'].decode();marker=f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 19, 1)'
    if slots.count(marker)!=1:raise ValueError('registry count differs')
    slots=slots.replace(marker,f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 28, 1)')
    layout_ids={v['id'] for v in layouts['layouts']};files={};headers={};includes=[]
    for slot,(name,(w,h)) in enumerate(MAPS.items(),19):
        f=HERE/'staged'/name;header=json.loads((f/'map.json').read_text());headers[name]=copy.deepcopy(header)
        if header['region_map_section']!='MAPSEC_PENDING_OWNER' or header['layout'] in layout_ids or any(header[k] for k in ('object_events','coord_events','bg_events','connections')):
            raise ValueError('neutral unregistered core floor required')
        raw=(f/'map.bin').read_bytes();border=(f/'border.bin').read_bytes()
        if (raw,border,header)!=expected[name]:raise ValueError('tested original packet differs')
        if len(raw)!=w*h*2 or len(border)!=8 or (w+15)*(h+14)>10240:raise ValueError('floor dimensions/buffer differ')
        if sha(raw)!=receipt['maps'][name]['map_sha256']:raise ValueError('tested original floor differs')
        header['region_map_section']='MAPSEC_ROUTE_201'
        files[f'data/maps/{name}/map.json']=encode(header);files[f'data/maps/{name}/scripts.inc']=(name+'_MapScripts::\n\t.byte 0\n').encode()
        files[f'data/layouts/{name}/map.bin']=raw;files[f'data/layouts/{name}/border.bin']=border
        layouts['layouts'].append(dict(id=header['layout'],name=name+'_Layout',width=w,height=h,primary_tileset='gTileset_General',secondary_tileset='gTileset_Cave',layout_version='emerald',border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin'))
        layout_ids.add(header['layout']);groups['gMapGroup_Sinnoh'].append(name)
        slots+=f'REGISTRY_SLOT({group}, {slot}, {header["id"]}, {name}, 1)\n';includes.append(f'\t.include "data/maps/{name}/scripts.inc"')
    byid={v['id']:v for v in headers.values()}
    for h in headers.values():
        for i,p in enumerate(h['warp_events']):
            if p['dest_map'] not in byid or not 0<=int(p['dest_warp_id'])<len(byid[p['dest_map']]['warp_events']):raise ValueError('foreign or absent stair')
            other=byid[p['dest_map']]['warp_events'][int(p['dest_warp_id'])]
            if other['dest_map']!=h['id'] or int(other['dest_warp_id'])!=i:raise ValueError('nonreciprocal stair')
    files['data/maps/map_groups.json']=encode(groups);files['data/layouts/layouts.json']=encode(layouts)
    files['test/data/averon_map_registry_slots.inc']=slots.encode();files['data/event_scripts.s']=before['data/event_scripts.s']+('\n'+'\n'.join(includes)+'\n').encode()
    files['test/averon_coronet_upper_floors_runtime.c']=(HERE/'native-runtime.c').read_bytes()
    return files,dict(status='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE',base=BASE,existing_map_names_preserved=prior,
        temporary_map_slots={n:19+i for i,n in enumerate(MAPS)},source_headers=headers,dev_surrogate='MAPSEC_ROUTE_201217 only in disposable nine-map Coronet upper floors ROM; unbuilt four exterior anchors closed, never production',files={p:sha(v) for p,v in sorted(files.items())})


def install(repo):
    repo=Path(repo).resolve();engine=repo/ENGINE
    if not base.git(repo,'branch','--show-current').decode().strip().startswith('codex/coronet-upper-floors-runtime-scratch-') or not (engine/'.map_qa_throwaway').is_file():raise ValueError('marked disposable Coronet branch required')
    if base.git(repo,'rev-parse','HEAD').decode().strip()!=BASE:raise ValueError('exact production baseline required')
    status=base.git(repo,'status','--porcelain','--untracked-files=normal','--',ENGINE).decode().splitlines()
    if status not in ([],['?? "Pokemon Game/engine/.map_qa_throwaway"']):raise ValueError('refusing dirty runtime source')
    files,receipt=assemble(repo)
    for path in files:
        target=(engine/path).resolve()
        if not target.is_relative_to(engine.resolve()):raise ValueError('output escapes engine')
        try:base.git(repo,'cat-file','-e','HEAD:'+ENGINE+path)
        except subprocess.CalledProcessError:
            if target.exists():raise ValueError('untracked output exists')
    for path,data in files.items():
        target=engine/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True,type=Path);p.add_argument('--install',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.repo) if a.install else assemble(a.repo)[1],indent=2))
