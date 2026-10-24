#!/usr/bin/env python3
"""Original Coronet upper core, reusing the existing room painter and renderer."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

NAMES={'2f':'SinnohMtCoronet_2F','3f':'SinnohMtCoronet_3F'}
IDS={n:'MAP_SINNOH_MT_CORONET_'+k.upper() for k,n in NAMES.items()}


def build(repo,inputs,out):
    repo,inputs,out=Path(repo).resolve(),Path(inputs).resolve(),Path(out).resolve();engine=repo/'Pokemon Game/engine'
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    p=repo/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/victory-road-shell/build_shell.py'
    sp=importlib.util.spec_from_file_location('upper_existing_painter',p);s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
    recipe=json.loads((inputs/'shell-recipe.json').read_text());reference=json.loads((inputs/'portal-reference.json').read_text())
    result=s.construct(recipe,reference,NAMES,IDS,'MAP_HEADER_MT_CORONET_')
    assets={}
    def read(path):
        data=s.base.verified_file(repo,Path('Pokemon Game/engine')/path,'HEAD');assets[path]=s.sha(data);return data
    paths=['data/tilesets/primary/general/','data/tilesets/secondary/cave/'];banks=[read(p+'metatiles.bin') for p in paths];attrs=[read(p+'metatile_attributes.bin') for p in paths];images=[s.dual.indexed(read(p+'tiles.png')) for p in paths]
    output={};facts={}
    for name,(raw,border,header) in result.items():
        deps=s.dual.closure(raw+border,banks,images);pals={i:s.base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
        used={v[0]&1023 for v in struct.iter_unpack('<H',raw+border)};words={str(i):s.art.attribute(attrs[i//512],i%512) for i in sorted(used)}
        plan=recipe['maps'][name];preview=s.dual.render(raw,banks,images,pals,plan['width'],plan['height'])
        output[name]=(raw,border,header,words,preview);facts[name]=dict(dimensions=[plan['width'],plan['height']],cells=len(raw)//2,warps=len(header['warp_events']),source_warp_indices=plan['interior_warp_indices'],sealed_external_ports=plan['sealed_external_ports'],dependencies=deps,map_sha256=s.sha(raw))
    out.mkdir(parents=True)
    for name,(raw,border,header,words,preview) in output.items():
        f=out/'staged'/name;f.mkdir(parents=True);(f/'map.bin').write_bytes(raw);(f/'border.bin').write_bytes(border);(f/'map.json').write_bytes(s.encode(header));(f/'attributes.json').write_bytes(s.encode(dict(used_source_attribute_words=words,source_tilesets=['gTileset_General','gTileset_Cave'])));preview.save(f/'averon.png')
    receipt=dict(status='ORIGINAL_UPPER_CORE_SOURCE_ART_ONLY_NOT_ROM_OR_PRODUCTION',reference_revision=reference['revision'],source_inputs_sha256={n:s.sha((inputs/n).read_bytes()) for n in ('shell-recipe.json','portal-reference.json')},existing_averon_sha256=assets,maps=facts,limits=recipe['limits'])
    (out/'source-receipt.json').write_bytes(s.encode(receipt));return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('repo','inputs','out'):p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.repo,a.inputs,a.out)['maps'],indent=2))
