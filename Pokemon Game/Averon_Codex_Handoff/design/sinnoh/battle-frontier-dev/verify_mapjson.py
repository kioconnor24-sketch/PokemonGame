#!/usr/bin/env python3
"""Run the real native map generator against a readonly overlay view, not a ROM."""
import argparse,importlib.util,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('battle_scene_export',HERE/'prepare_scene.py')
scene=importlib.util.module_from_spec(s);s.loader.exec_module(scene)
def verify(repo,bundle,tool,out):
    repo,bundle,tool,out=[Path(p).resolve() for p in (repo,bundle,tool,out)]
    engine=repo/scene.ENGINE
    if out.exists() or out.is_relative_to(engine) or out.is_relative_to(bundle) or 'engine' in out.parts:raise ValueError('new independent verification directory required')
    if not tool.is_file():raise ValueError('real mapjson executable required')
    recipe=json.loads((bundle/'receipt.json').read_text());overlay=bundle/'overlay'
    for p,h in recipe['files'].items():
        if scene.base.sha((overlay/p).read_bytes())!=h:raise ValueError('overlay hash differs')
    source_hashes={}
    for name in ('mapjson.cpp','json11.cpp','mapjson.h'):
        current=scene.base.verified_file(repo,Path(scene.ENGINE)/'tools/mapjson'/name,'HEAD')
        if (tool.parent/name).read_bytes()!=current:raise ValueError('mapjson tool source provenance differs')
        source_hashes[name]=scene.base.sha(current)
    view=out/'view';maps=view/'data/maps';const=view/'include/constants';generated=out/'generated'
    maps.mkdir(parents=True);const.mkdir(parents=True);(generated/'maps').mkdir(parents=True);(generated/'layouts').mkdir();(view/'src/data').mkdir(parents=True)
    # A short source alias limits symlink metadata overhead on the constrained host.
    alias=out/'source-maps';alias.symlink_to(engine/'data/maps',target_is_directory=True)
    for p in (engine/'data/maps').iterdir():
        if p.is_dir():(maps/p.name).symlink_to(alias/p.name,target_is_directory=True)
    new=[]
    for item in recipe['scene'].values():
        p=overlay/'data/maps'/item['name'];target=maps/item['name']
        if target.exists():raise ValueError('scene name shadows baseline map')
        target.symlink_to(p,target_is_directory=True);new.append(p/'map.json')
    (maps/'map_groups.json').write_bytes((overlay/'data/maps/map_groups.json').read_bytes())
    required=view/'tools/mapjson';required.mkdir(parents=True)
    defines=scene.base.verified_file(repo,Path(scene.ENGINE)/'tools/mapjson/required_map_defines.json','HEAD')
    (required/'required_map_defines.json').write_bytes(defines)
    oldfiles=list((engine/'data/maps').glob('*/map.json'))
    heals=scene.base.verified_file(repo,Path(scene.ENGINE)/'src/data/heal_locations.json','HEAD')
    (view/'src/data/heal_locations.json').write_bytes(heals)
    source_groups=scene.base.verified_file(repo,Path(scene.ENGINE)/'data/maps/map_groups.json','HEAD')
    (maps/'map_groups.json').write_bytes(source_groups)
    baseline_asm=generated/'baseline-maps';baseline_const=generated/'baseline-constants'
    baseline_asm.mkdir();baseline_const.mkdir()
    control=subprocess.run([str(tool),'groups','emerald',str(maps/'map_groups.json'),*[str(p) for p in oldfiles],str(baseline_asm),str(baseline_const)],cwd=view,capture_output=True,text=True)
    if control.returncode:raise ValueError('mapjson baseline failed: '+control.stderr[-1500:])
    baseline_heals=(view/'src/data/heal_locations.json').read_bytes()
    (view/'src/data/heal_locations.json').write_bytes(heals)
    (maps/'map_groups.json').write_bytes((overlay/'data/maps/map_groups.json').read_bytes())
    files=oldfiles+new
    commands=[[str(tool),'groups','emerald',str(maps/'map_groups.json'),*[str(p) for p in files],str(generated/'maps'),str(const)],
              [str(tool),'layouts','emerald',str(overlay/'data/layouts/layouts.json'),str(generated/'layouts'),str(const)]]
    for p in new:
        dest=generated/'maps'/p.parent.name;dest.mkdir()
        commands.append([str(tool),'map','emerald',str(p),str(overlay/'data/layouts/layouts.json'),str(dest)])
    for cmd in commands:
        result=subprocess.run(cmd,cwd=view,capture_output=True,text=True)
        if result.returncode:raise ValueError('mapjson '+cmd[1]+' failed: '+result.stderr[-1500:])
    if json.loads(baseline_heals)!=json.loads((view/'src/data/heal_locations.json').read_bytes()):raise ValueError('overlay changes baseline healer records')
    import re
    expression=r'(MAP_\w+)\s*=\s*\((\d+)\s*\|\s*\((\d+)\s*<<\s*8\)\)'
    old_ids={k:int(n)|(int(g)<<8) for k,n,g in re.findall(expression,(baseline_const/'map_groups.h').read_text())}
    new_ids={k:int(n)|(int(g)<<8) for k,n,g in re.findall(expression,(const/'map_groups.h').read_text())}
    if not old_ids or any(new_ids.get(k)!=v for k,v in old_ids.items()):raise ValueError('legacy numeric map identity changed')
    receipt=dict(legacy_enum_values_preserved=len(old_ids),baseline_healers_unchanged=True,status='REAL_HOST_MAPJSON_GENERATION_NOT_ROM_NATIVE_GAME_OR_RUNTIME_ACCEPTANCE',
        source_sha=recipe['source_sha'],tool_sha256=scene.base.sha(tool.read_bytes()),matched_tool_source_sha256=source_hashes,
        required_defines_sha256=scene.base.sha(defines),generated_maps=len(new),successful_commands=len(commands)+1,
        generated_sha256={str(p.relative_to(out)):scene.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file() and not p.is_symlink() and 'view' not in p.relative_to(out).parts and p.name!='receipt.json'})
    (out/'receipt.json').write_bytes(scene.encode(receipt));return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);p.add_argument('--tool',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(verify(a.repo,a.bundle,a.tool,a.out),indent=2))
