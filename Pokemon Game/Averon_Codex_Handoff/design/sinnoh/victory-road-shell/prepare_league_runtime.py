#!/usr/bin/env python3
"""Reuse the two guarded scene assemblers for coast+connected Victory Road DEV.

No production identities or art are authored. Only explicit new geometry doors
and exact temporary map/test expectations differ from the two source scenes.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

PREFIX='Pokemon Game/Averon_Codex_Handoff/design/sinnoh/'
ENGINE='Pokemon Game/engine/'
BASE='d96ae4041cb955918801eea5dfb300f517000474'
sha=lambda raw:hashlib.sha256(raw).hexdigest()
encode=lambda value:(json.dumps(value,indent=2)+'\n').encode()


def load(repo,name,path):
    spec=importlib.util.spec_from_file_location(name,Path(repo)/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def replace_once(raw,before,after):
    before,after=before.encode(),after.encode()
    if raw.count(before)!=1:raise ValueError('native fixture contract differs')
    return raw.replace(before,after)


def assemble(repo):
    repo=Path(repo).resolve();coast=load(repo,'combined_coast_source',PREFIX+'sunyshore-coast/prepare_runtime.py')
    core=load(repo,'combined_core_source',PREFIX+'victory-road-shell/prepare_runtime.py')
    if coast.BASE!=BASE or core.BASE!=BASE:raise ValueError('scene baseline differs')
    a,ar=coast.assemble(repo);b,br=core.assemble(repo)
    common={'data/maps/map_groups.json','data/layouts/layouts.json','test/data/averon_map_registry_slots.inc','data/event_scripts.s'}
    if set(a)&set(b)!=common:raise ValueError('unexpected scene file collision')
    out={**{p:v for p,v in a.items() if p not in common},**{p:v for p,v in b.items() if p not in common}}
    groups=json.loads(a['data/maps/map_groups.json']);before=groups['gMapGroup_Sinnoh']
    if before[:19]!=ar['existing_map_names_preserved'] or br['existing_map_names_preserved']!=before[:19] or len(before)!=24:raise ValueError('production/coast prefix differs')
    if set(before)&set(core.MAPS):raise ValueError('core name already installed')
    groups['gMapGroup_Sinnoh']+=list(core.MAPS)
    layouts=json.loads(a['data/layouts/layouts.json']);extra=json.loads(b['data/layouts/layouts.json'])['layouts'][-3:]
    if {v['name'] for v in extra}!={n+'_Layout' for n in core.MAPS}:raise ValueError('three exact core layouts required')
    layouts['layouts']+=extra
    group=groups['group_order'].index('gMapGroup_Sinnoh')
    slots=replace_once(a['test/data/averon_map_registry_slots.inc'],f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 24, 1)',f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 27, 1)')
    for i,name in enumerate(core.MAPS,24):
        h=br['source_headers'][name];slots+=f'REGISTRY_SLOT({group}, {i}, {h["id"]}, {name}, 1)\n'.encode()
    out['data/maps/map_groups.json']=encode(groups);out['data/layouts/layouts.json']=encode(layouts);out['test/data/averon_map_registry_slots.inc']=slots
    original=coast.inputs(repo)['data/event_scripts.s']
    if not b['data/event_scripts.s'].startswith(original):raise ValueError('event script prefix differs')
    out['data/event_scripts.s']=a['data/event_scripts.s']+b['data/event_scripts.s'][len(original):]
    here=repo/(PREFIX+'victory-road-shell');receipt=json.loads((here/'connected-receipt.json').read_text())
    expected={n+'/'+f for n in ('PokmonLeague',*core.MAPS) for f in ('map.bin','border.bin','map.json','attributes.json','averon.png')}
    if set(receipt['output_sha256'])!=expected:raise ValueError('exact connected packet set required')
    data={p:(here/'connected'/p).read_bytes() for p in expected}
    if any(sha(v)!=receipt['output_sha256'][p] for p,v in data.items()):raise ValueError('connected packet hash differs')
    for name in ('PokmonLeague',*core.MAPS):
        h=json.loads(data[name+'/map.json'])
        if h['region_map_section']!='MAPSEC_PENDING_OWNER' or any(h[k] for k in ('object_events','coord_events','bg_events')):raise ValueError('neutral source packet required')
        h['region_map_section']='MAPSEC_ROUTE_201';out['data/maps/'+name+'/map.json']=encode(h)
        for f in ('map.bin','border.bin'):out['data/layouts/'+name+'/'+f]=data[name+'/'+f]
    # Own DEV fixture expectations follow the actual appended indices/doors;
    # no production source, strict golden or expected-failure baseline changes.
    p='test/averon_sunyshore_runtime.c';out[p]=replace_once(out[p],'warps[]={1,1,0,0,2}','warps[]={1,1,0,2,2}')
    p='test/averon_victory_runtime.c'
    for old,new in [('counts[]={6,3,3}','counts[]={8,3,3}'),('19+i','24+i'),('p->mapNum>=19 && p->mapNum<=21','(p->mapNum>=24 && p->mapNum<=26) || p->mapNum==MAP_NUM(MAP_POKMON_LEAGUE)'),('EXPECT_EQ(total,12)','EXPECT_EQ(total,14)'),('all twelve stairs have reciprocal core-only destinations','all fourteen core events have reciprocal core-or-League destinations')]:out[p]=replace_once(out[p],old,new)
    return out,dict(status='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE',base=BASE,
        existing_map_names_preserved=before[:19],temporary_map_slots={n:i for i,n in enumerate(groups['gMapGroup_Sinnoh'][19:],19)},
        dev_surrogate='existing217 only in disposable eight-map scene; no natural Surf/Waterfall or production origin approval',
        source_coast_recipe=ar['files'],source_core_recipe=br['files'],connected_receipt_sha256=sha((here/'connected-receipt.json').read_bytes()),
        files={p:sha(v) for p,v in sorted(out.items())})


def install(repo):
    repo=Path(repo).resolve();coast=load(repo,'combined_install_guard',PREFIX+'sunyshore-coast/prepare_runtime.py');base=coast.base;engine=repo/ENGINE
    if not base.git(repo,'branch','--show-current').decode().strip().startswith('codex/victory-league-runtime-scratch-') or not (engine/'.map_qa_throwaway').is_file():raise ValueError('marked disposable combined branch required')
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
    for path,raw in files.items():
        target=engine/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',type=Path,required=True);p.add_argument('--install',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.repo) if a.install else assemble(a.repo)[1],indent=2))
