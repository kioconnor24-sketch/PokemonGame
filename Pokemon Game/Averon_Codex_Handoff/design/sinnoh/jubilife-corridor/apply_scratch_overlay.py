#!/usr/bin/env python3
"""Apply existing candidates ONLY to an explicitly marked disposable worktree.

Not a production registrar or authorization. Begin from current main merged with
exact Route202 below. Preserve Claude's branches. The section220 dependency is
copied from exact existing Verity source, not newly allocated here.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
ROUTE202='b4c1d39f0476b004f772506abd1b378e055ad03e'
VERITY='4ed99916f0aeb6bee81e9aedf51f40fb6d66730e'
SECTION='Pokemon Game/engine/src/data/region_map/region_map_sections.json'
def update_fixture_expectations(engine):
 """Extend approved namespace expectations without changing legacy goldens."""
 e=Path(engine)
 p=e/'test/averon_sandgem_location.c';s=p.read_text()
 s=s.replace('MAPSEC_COUNT == 220','MAPSEC_COUNT == 224').replace('i = 220;','i = 224;').replace('{215, 220, 252, 253, 254, 255}','{215, 224, 252, 253, 254, 255}')
 p.write_text(s)
 p=e/'test/averon_location_compatibility.c';s=p.read_text()
 s=s.replace('section == MAPSEC_ROUTE_202;', 'section == MAPSEC_ROUTE_202 || section == MAPSEC_LAKE_VERITY || section == MAPSEC_JUBILIFE_CITY || section == MAPSEC_ROUTE_203 || section == MAPSEC_OREBURGH_GATE;')
 s=s.replace('section == MAPSEC_ROUTE_202)', 'section == MAPSEC_ROUTE_202 || section == MAPSEC_LAKE_VERITY || section == MAPSEC_JUBILIFE_CITY || section == MAPSEC_ROUTE_203 || section == MAPSEC_OREBURGH_GATE)')
 p.write_text(s)
 p=e/'test/data/averon_map_registry_slots.inc';s=p.read_text().replace('REGISTRY_GROUP(76, gMapGroup_Sinnoh, 5, 1)','REGISTRY_GROUP(76, gMapGroup_Sinnoh, 11, 1)')
 names=['JubilifeCity','Route203','OreburghGate_1F','JubilifeCity_PokemonCenter_1F','JubilifeCity_Mart','JubilifeCity_PokemonSchool']
 for n,name in enumerate(names,5):
  symbol=json.loads((e/'data/maps'/name/'map.json').read_text())['id']
  s+='REGISTRY_SLOT(76, %d, %s, %s, 1)\n'%(n,symbol,name)
 p.write_text(s)

def apply(repo,overlay):
 repo,overlay=Path(repo).resolve(),Path(overlay).resolve();e=repo/'Pokemon Game/engine'
 def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
 if not (e/'.map_qa_throwaway').exists():raise ValueError('explicit disposable-engine marker required')
 if not git('branch','--show-current').decode().strip().startswith('codex/corridor-scratch-'):raise ValueError('scratch branch required')
 git('merge-base','--is-ancestor',ROUTE202,'HEAD')
 original=git('show',ROUTE202+':Pokemon Game/engine/data/maps/Route202/map.json')
 if (e/'data/maps/Route202/map.json').read_bytes()!=original:raise ValueError('Route202 source changed')
 f=json.loads((overlay/'registration-fragments.json').read_text())
 if f['route202_header_patch']['expected_source_head']!=ROUTE202:raise ValueError('stale overlay source pin')
 groups=json.loads((e/'data/maps/map_groups.json').read_text())
 if any(n in groups['gMapGroup_Sinnoh'] for n in f['append_map_names']):raise ValueError('already applied')
 source=json.loads(git('show',VERITY+':'+SECTION))
 section=next(s for s in source['map_sections'] if s.get('value')==220)
 current=json.loads((e/'src/data/region_map/region_map_sections.json').read_text())
 if any(s.get('value',0)>=220 for s in current['map_sections']):raise ValueError('unexpected section namespace')
 # All preconditions precede writes. Reuse files, do not reconvert geography.
 for rel in ('data/maps','data/layouts','data/tilesets','test'):shutil.copytree(overlay/rel,e/rel,dirs_exist_ok=True)
 def edit(rel,fn):
  p=e/rel;v=json.loads(p.read_text());fn(v);p.write_text(json.dumps(v,indent=2)+'\n')
 edit('data/maps/map_groups.json',lambda v:v['gMapGroup_Sinnoh'].extend(f['append_map_names']))
 edit('data/layouts/layouts.json',lambda v:v['layouts'].extend(f['append_layouts']))
 edit('src/data/region_map/region_map_sections.json',lambda v:v['map_sections'].extend([section]+f['append_sections']))
 edit('data/maps/Route202/map.json',lambda v:v['connections'].append(f['route202_header_patch']['append_connection']))
 with (e/'data/event_scripts.s').open('a') as p:p.write('\n'+'\n'.join(f['append_event_includes'])+'\n')
 s=(overlay/'averon_corridor_tileset.c').read_text()
 constants=s[s.index('const u16'):s.index('const struct Tileset')]
 header=s[s.index('const struct Tileset'):].replace('.metatileAttributes=','.metatileAttributes = ').replace(' = {',' =\n{')
 with (e/'src/data/tilesets/metatiles.h').open('a') as p:p.write('\n'+constants)
 with (e/'src/data/tilesets/headers.h').open('a') as p:p.write('\n'+header)
 with (e/'include/tilesets.h').open('a') as p:p.write('\nextern const struct Tileset gTileset_AveronCorridorRustboro;\n')
 update_fixture_expectations(e)
 return {'status':'SCRATCH_SOURCE_ONLY','base':git('rev-parse','HEAD').decode().strip(),'route202':ROUTE202,'verity_section_source':VERITY,'production_authorization':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True);p.add_argument('--overlay',required=True);a=p.parse_args()
 print(json.dumps(apply(a.repo,a.overlay),indent=2))
