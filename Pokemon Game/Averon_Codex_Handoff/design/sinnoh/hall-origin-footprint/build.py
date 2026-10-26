#!/usr/bin/env python3
"""Bounded authentic Hall footprint, no flute/Arceus/story or summit unlock."""
import argparse,importlib.util,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('hall_source_projection',HERE.parent/'frontier-campus/build_source.py')
existing=importlib.util.module_from_spec(s);s.loader.exec_module(existing)
existing.HERE=HERE;existing.DIMS={'Hall':(64,64)}
existing.SOURCE_BEHAVIORS=existing.SOURCE_BEHAVIORS+(0x6f,)
original_construct=existing.construct
def construct(geometry):
    result=original_construct(geometry)
    raw,h,audit=result['Hall']
    h.update(id='MAP_SINNOH_HALL_ORIGIN_PROTOTYPE',name='SinnohHallOriginPrototype',layout='LAYOUT_SINNOH_HALL_ORIGIN_PROTOTYPE',map_type='MAP_TYPE_UNDERGROUND',music='MUS_PETALBURG_WOODS')
    result['Hall']=(raw,h,audit)
    return result
existing.construct=construct
def build(engine,out):
    result=existing.build(engine,out)
    result.update(status='BOUNDED_HALL_FOOTPRINT_ONLY_NOT_STORY_OR_RUNTIME_ACCEPTANCE',
       limits=['Authentic technical footprint/native cave and step proxies, not DS sky/platform architecture or camera',
               'Source exit and summit transition closed; no flute, legendary, conditional routing or story unlock',
               'No DS pixels/models/music, production IDs/registry/save edits, ROM/native/mGBA/Save acceptance'])
    (Path(out)/'receipt.json').write_text(json.dumps(result,indent=2)+'
')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--private-inputs',type=Path);a=p.parse_args()
    if a.private_inputs:
        g=existing.extract(a.private_inputs);(HERE/'geometry.json').write_text(json.dumps(g,indent=2)+'
')
        print({n:dict(supported=len(v['surfaces']),rejected=v['rejected_permission_clear']) for n,v in g.items()})
    else:print(json.dumps(build(a.engine,a.out),indent=2))
