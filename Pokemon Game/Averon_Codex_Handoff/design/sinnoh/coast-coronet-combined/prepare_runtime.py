#!/usr/bin/env python3
"""Combine existing verified DEV recipes; no new world seams or saved origins."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
SOURCE_ROOT=Path(__file__).resolve().parents[5]
PREFIX='Pokemon Game/Averon_Codex_Handoff/design/sinnoh/'
ENGINE='Pokemon Game/engine/'
BASE='9c195964938b5a9c5db37bd114ca6dbcfc1965a3'
REPAIR='0fa671e3717b57b6f1409a3cee866950eca6a5d9'
ENGINE_BASE_TREE='c2e26cce0a00af43251e0672fef708c796b7a918'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,SOURCE_ROOT/PREFIX/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def assemble(repo):
 repo=Path(repo).resolve()
 league=load('combined_league','victory-road-shell/prepare_league_runtime.py')
 ascent=load('combined_ascent','coronet-ascent/prepare_runtime.py')
 if ascent.base.git(repo,'rev-parse','HEAD:'+ENGINE.rstrip('/'))!=(ENGINE_BASE_TREE+'\n').encode():raise ValueError('exact current-main engine baseline required')
 a,ar=league.assemble(repo);b,br=ascent.assemble(repo)
 common={'data/maps/map_groups.json','data/layouts/layouts.json','test/data/averon_map_registry_slots.inc','data/event_scripts.s'}
 if set(a)&set(b)!=common:raise ValueError('unexpected scene collision')
 out={**{p:v for p,v in a.items() if p not in common},**{p:v for p,v in b.items() if p not in common}}
 groups=json.loads(a['data/maps/map_groups.json']);prior=ar['existing_map_names_preserved']
 if len(prior)!=19 or groups['gMapGroup_Sinnoh'][:19]!=prior or prior!=br['existing_map_names_preserved'] or len(groups['gMapGroup_Sinnoh'])!=27:raise ValueError('original prefix differs')
 if set(groups['gMapGroup_Sinnoh'])&set(ascent.MAPS):raise ValueError('ascent already included')
 groups['gMapGroup_Sinnoh']+=list(ascent.MAPS)
 layouts=json.loads(a['data/layouts/layouts.json']);extra=json.loads(b['data/layouts/layouts.json'])['layouts'][-6:]
 if {v['name'] for v in extra}!={n+'_Layout' for n in ascent.MAPS}:raise ValueError('six exact ascent layouts required')
 if {v['id'] for v in extra}&{v['id'] for v in layouts['layouts']}:raise ValueError('layout collision')
 layouts['layouts']+=extra;group=groups['group_order'].index('gMapGroup_Sinnoh')
 slots=league.replace_once(a['test/data/averon_map_registry_slots.inc'],f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 27, 1)',f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 33, 1)')
 for i,name in enumerate(ascent.MAPS,27):
  h=br['source_headers'][name];slots+=f'REGISTRY_SLOT({group}, {i}, {h["id"]}, {name}, 1)\n'.encode()
 original=ascent.coast.inputs(repo)['data/event_scripts.s']
 if not b['data/event_scripts.s'].startswith(original):raise ValueError('event prefix differs')
 out['data/event_scripts.s']=a['data/event_scripts.s']+b['data/event_scripts.s'][len(original):]
 out['data/maps/map_groups.json']=ascent.encode(groups);out['data/layouts/layouts.json']=ascent.encode(layouts);out['test/data/averon_map_registry_slots.inc']=slots
 p='test/averon_coronet_ascent_runtime.c'
 for old,new in [('19+i','27+i'),('p->mapNum>=19 && p->mapNum<=24','p->mapNum>=27 && p->mapNum<=32')]:out[p]=league.replace_once(out[p],old,new)
 # Reuse the exact published correction, never apply it to an unknown baseline.
 path=PREFIX+'route222-safety/corrected/averon-map.bin'
 fixed=(SOURCE_ROOT/path).read_bytes()
 if ascent.sha(fixed)!='d72e2575f7503746f8ba2e404696b217ee9f66e60d1995dc6a26e22fc22d7d36':raise ValueError('published repair hash differs')
 raw=out['data/layouts/Route222/map.bin']
 if len(raw)!=len(fixed):raise ValueError('repair length differs')
 cells=[i//2 for i in range(0,len(raw),2) if raw[i:i+2]!=fixed[i:i+2]]
 if cells!=[16*92+36,16*92+37]:raise ValueError('exact two published ledge cells required')
 for cell in cells:
  if raw[cell*2:cell*2+2]!=bytes.fromhex('8704') or fixed[cell*2:cell*2+2]!=bytes.fromhex('9104'):raise ValueError('published cliff semantics differ')
 out['data/layouts/Route222/map.bin']=fixed
 fixture=SOURCE_ROOT/(PREFIX+'route222-safety/native-runtime.c')
 out['test/averon_route222_safety.c']=fixture.read_bytes()
 return out,dict(status='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE',disconnected_coronet=True,base=BASE,repair_commit=REPAIR,repair_changed_cells=cells,existing_map_names_preserved=prior,temporary_map_slots={n:i for i,n in enumerate(groups['gMapGroup_Sinnoh'][19:],19)},source_league_files=ar['files'],source_ascent_files=br['files'],files={p:ascent.sha(v) for p,v in sorted(out.items())})
def install(repo):
 repo=Path(repo).resolve();ascent=load('combined_guard','coronet-ascent/prepare_runtime.py');engine=repo/ENGINE;base=ascent.base
 if not base.git(repo,'branch','--show-current').decode().strip().startswith('codex/coast-coronet-runtime-scratch-') or not (engine/'.map_qa_throwaway').is_file():raise ValueError('marked disposable combined branch required')
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
 p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--install',action='store_true');a=p.parse_args();print(json.dumps(install(a.repo) if a.install else assemble(a.repo)[1],indent=2))
