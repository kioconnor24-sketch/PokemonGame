#!/usr/bin/env python3
"""Read-only assembly / guarded installation of partial six-floor Temple DEV core."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
HERE=Path(__file__).resolve().parent
BASE='fb83410f6bbded89a9d99537d952698e80af4cf5'
ENGINE='Pokemon Game/engine/'
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
core=load('temple_source',HERE/'build_core.py')
coast=load('temple_existing_base',HERE.parent/'sunyshore-coast/prepare_runtime.py')
base=coast.base;sha=coast.sha;encode=coast.encode
MAPS=tuple(core.NAMES.values())

def assemble(repo):
    repo=Path(repo).resolve()
    if base.git(repo,'rev-parse','HEAD:Pokemon Game/engine').strip()!=base.git(repo,'rev-parse',BASE+':Pokemon Game/engine').strip():
        raise ValueError('exact baseline engine required')
    before=coast.inputs(repo);receipt=json.loads((HERE/'source-receipt.json').read_text())
    for p,h in receipt['input_sha256'].items():
        if sha((HERE/p).read_bytes())!=h:raise ValueError('tested Temple source differs')
    for p,h in receipt['existing_averon_sha256'].items():
        if sha(base.verified_file(repo,Path(ENGINE)/p,'HEAD'))!=h:raise ValueError('tested native art differs')
    expected=core.construct(json.loads((HERE/'shell-recipe.json').read_text()),json.loads((HERE/'portal-reference.json').read_text()))
    groups=json.loads(before['data/maps/map_groups.json']);layouts=json.loads(before['data/layouts/layouts.json'])
    prior=list(groups['gMapGroup_Sinnoh']);g=groups['group_order'].index('gMapGroup_Sinnoh')
    if len(prior)!=19 or len(set(prior))!=19 or set(prior)&set(MAPS):raise ValueError('original19 prefix required')
    slots=before['test/data/averon_map_registry_slots.inc'].decode();marker=f'REGISTRY_GROUP({g}, gMapGroup_Sinnoh, 19, 1)'
    if slots.count(marker)!=1:raise ValueError('registry count differs')
    slots=slots.replace(marker,f'REGISTRY_GROUP({g}, gMapGroup_Sinnoh, 25, 1)');files={};headers={};includes=[]
    layout_ids={d['id'] for d in layouts['layouts']}
    for i,name in enumerate(MAPS,19):
        folder=HERE/'staged'/name;raw=(folder/'map.bin').read_bytes();border=(folder/'border.bin').read_bytes();h=json.loads((folder/'map.json').read_text())
        if (raw,border,h)!=expected[name]:raise ValueError('tested Temple packet differs')
        if h['region_map_section']!='MAPSEC_PENDING_OWNER' or h['layout'] in layout_ids:raise ValueError('unregistered neutral floor required')
        if any(h[k] for k in ('object_events','coord_events','bg_events','connections')):raise ValueError('unexpected content')
        h['region_map_section']='MAPSEC_ROUTE_201';headers[name]=h
        files[f'data/maps/{name}/map.json']=encode(h);files[f'data/maps/{name}/scripts.inc']=(name+'_MapScripts::\n\t.byte 0\n').encode()
        files[f'data/layouts/{name}/map.bin']=raw;files[f'data/layouts/{name}/border.bin']=border
        layouts['layouts'].append(dict(id=h['layout'],name=name+'_Layout',width=20,height=20,primary_tileset='gTileset_General',secondary_tileset='gTileset_Cave',layout_version='emerald',border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin'))
        layout_ids.add(h['layout']);groups['gMapGroup_Sinnoh'].append(name)
        slots+=f'REGISTRY_SLOT({g}, {i}, {h["id"]}, {name}, 1)\n';includes.append(f'\t.include "data/maps/{name}/scripts.inc"')
    files['data/maps/map_groups.json']=encode(groups);files['data/layouts/layouts.json']=encode(layouts)
    files['test/data/averon_map_registry_slots.inc']=slots.encode();files['data/event_scripts.s']=before['data/event_scripts.s']+('\n'+'\n'.join(includes)+'\n').encode()
    files['test/averon_temple_core_runtime.c']=(HERE/'native-runtime.c').read_bytes()
    return files,dict(status='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE',base=BASE,existing_map_names_preserved=prior,temporary_map_slots={n:19+i for i,n in enumerate(MAPS)},source_headers=headers,dev_surrogate='217 DEV only; no production Temple origin approval',files={p:sha(v) for p,v in sorted(files.items())})

def install(repo):
    repo=Path(repo).resolve();engine=repo/ENGINE
    if not base.git(repo,'branch','--show-current').decode().strip().startswith('codex/temple-core-runtime-') or not (engine/'.map_qa_throwaway').is_file():raise ValueError('marked Temple disposable branch required')
    if base.git(repo,'rev-parse','HEAD').decode().strip()!=BASE:raise ValueError('exact base required')
    if base.git(repo,'status','--porcelain','--untracked-files=normal','--',ENGINE).decode().splitlines() not in ([],['?? "Pokemon Game/engine/.map_qa_throwaway"']):raise ValueError('dirty engine refused')
    files,r=assemble(repo)
    for p in files:
        target=(engine/p).resolve()
        if not target.is_relative_to(engine.resolve()):raise ValueError('output escapes engine')
        try:base.git(repo,'cat-file','-e','HEAD:'+ENGINE+p)
        except subprocess.CalledProcessError:
            if target.exists():raise ValueError('untracked output exists')
    for p,data in files.items():
        target=engine/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return r
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True,type=Path);p.add_argument('--install',action='store_true');a=p.parse_args();print(json.dumps(install(a.repo) if a.install else assemble(a.repo)[1],indent=2))
