#!/usr/bin/env python3
"""Explicit two-cell safety deviation; retain pristine donor/art source packets."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

PINS={'map.bin':'e9545d4a1ad3a71c6dbacccba7a1eff13f758f1e0c16edaf6864c7c8870a8ee3','averon-map.bin':'752711b563612d52def985c5d66018f496cbf6323f8e9344cff8714ed28a8b75'}
sha=lambda b:hashlib.sha256(b).hexdigest()

def build(repo,out):
    repo,out=Path(repo).resolve(),Path(out).resolve();engine=repo/'Pokemon Game/engine'
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    root=repo/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/sunyshore-coast';source=root/'staged/Route222'
    original={n:(source/n).read_bytes() for n in PINS}
    if any(sha(original[n])!=v for n,v in PINS.items()):raise ValueError('original Route222 packet changed')
    attrs=(engine/'data/tilesets/primary/general/metatile_attributes.bin').read_bytes()
    if struct.unpack_from('<H',attrs,2*135)[0]!=0x103b or struct.unpack_from('<H',attrs,2*145)[0]!=0:raise ValueError('native ledge/cliff behavior changed')
    changed={}
    for name,raw in original.items():
        result=bytearray(raw)
        for x in (36,37):
            at=2*(16*92+x)
            if struct.unpack_from('<H',raw,at)[0]!=0x487:raise ValueError('exact original hazardous ledge required')
            # Same collision/elevation bits. Only these two south-jump behaviors
            # become stock nonjumping sand-base cliff, preserving all boulders.
            struct.pack_into('<H',result,at,0x491)
        changed[name]=bytes(result)
    p=root/'adapt_art.py';sp=importlib.util.spec_from_file_location('route222_existing_renderer',p);s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
    banks=[(root/'outdoor-family'/p).read_bytes() for p in ('primary-metatiles.bin','secondary-metatiles.bin')]
    if [sha(b) for b in banks]!=['17974b0ba1bb9d105d5ba255c69a3b80d8484a26ea0b8ff22c6c6567c6c22910','4c512158566d2d929427645981cf55bc0ab05c95b11c61868561abf6793cc1bb']:raise ValueError('original permitted banks changed')
    paths=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/'];images=[s.pack.accepted.dual.indexed((engine/(p+'tiles.png')).read_bytes()) for p in paths]
    raw=changed['averon-map.bin'];border=(source/'averon-border.bin').read_bytes();deps=s.pack.accepted.dual.closure(raw+border,banks,images)
    palettes={i:s.pack.accepted.base.palette((engine/(paths[i>=6]+'palettes/%02d.pal'%i)).read_bytes()) for i in deps['palettes']}
    preview=s.pack.accepted.dual.render(raw,banks,images,palettes,92,32)
    receipt=dict(status='DOCUMENTED_TWO_CELL_GEOGRAPHY_SAFETY_DEVIATION_NOT_RUNTIME_ACCEPTANCE',original_sha256=PINS,
      cells=[dict(x=x,y=16,before=0x487,after=0x491,old_behavior='MB_JUMP_SOUTH',new_behavior='MB_NORMAL',collision_before=1,collision_after=1,elevation_before=0,elevation_after=0) for x in (36,37)],
      reason='Previously reproduced ledge jumps land inside unchanged solid boulders36/37,17. Replace only those two jump faces with existing impassable sand-base cliff; retain adjacent legal jumps and all four boulder cells. Owner visual review remains.',
      output_sha256={n:sha(v) for n,v in changed.items()},limits=['Original source packets remain byte-identical','No bank or global graphics edit, saved ID, warp, story, encounter or production install','Source-tested only; original negative fixtures must be rerun against a newly compiled corrected scene'])
    out.mkdir(parents=True)
    for n,v in changed.items():(out/n).write_bytes(v)
    preview.save(out/'averon.png');(out/'repair-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();print(json.dumps(build(a.repo,a.out),indent=2))
