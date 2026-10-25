#!/usr/bin/env python3
"""Native civic-art candidate over immutable conservative campus physics."""
import importlib.util,json,struct,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('civic_frontier',HERE/'build_source.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
FACADES=[(46,13),(75,30),(17,30),(31,58),(62,58),(46,48)]
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(m.base.git(engine,'rev-parse','--show-toplevel').decode().strip());assets={}
    def read(p):
        raw=m.base.verified_file(repo,engine.relative_to(repo)/p,'HEAD');assets[p]=m.base.sha(raw);return raw
    raw=m.base.verified_file(repo,HERE.relative_to(repo)/'staged/Campus/map.bin','HEAD')
    border=m.base.verified_file(repo,HERE.relative_to(repo)/'staged/Campus/border.bin','HEAD')
    oldattrs=[m.base.verified_file(repo,HERE.relative_to(repo)/('native-family/'+p),'HEAD') for p in ('primary-attributes.bin','secondary-attributes.bin')]
    prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
    banks=[read(p+'metatiles.bin') for p in prefixes];pa=read(prefixes[0]+'metatile_attributes.bin')
    stock=struct.unpack('<2400H',read('data/layouts/RustboroCity/map.bin'))
    words=list(struct.iter_unpack('<H',raw+border));desired=[]
    for i,(v,) in enumerate(words):
        tile=1 if v&0xc00 else 103 if v>>12==0 else 148
        art=m.packer.words(banks[0],tile)
        if i<len(raw)//2:
            x,y=i%96,i//96
            for fx,fy in FACADES:
                if fx<=x<fx+5 and fy<=y<fy+5 and v&0xc00:
                    native=stock[(15+y-fy)*40+31+x-fx]&1023
                    art=m.packer.words(banks[native//512],native%512)
        desired.append(art)
    converted,sec,sa=m.packer.pack_art(raw+border,desired,oldattrs,banks[0],pa,b'',b'')
    for (a,),(b,) in zip(words,struct.iter_unpack('<H',converted)):
        if a&0xfc00!=b&0xfc00:raise ValueError('civic art changed source physics')
        if m.packer.attribute((pa,sa)[(b&1023)//512],b%512)!=m.packer.attribute(oldattrs[(a&1023)//512],a%512):raise ValueError('civic art changed behavior')
    images=[m.dual.indexed(read(p+'tiles.png')) for p in prefixes];deps=m.dual.closure(converted,[banks[0],sec],images)
    palettes={i:m.base.palette(read(prefixes[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
    preview=m.dual.render(converted[:len(raw)],[banks[0],sec],images,palettes,96,96)
    out.mkdir(parents=True);preview.save(out/'preview.png');(out/'map.bin').write_bytes(converted[:len(raw)]);(out/'border.bin').write_bytes(converted[len(raw):])
    for n,data in [('primary-metatiles',banks[0]),('primary-attributes',pa),('secondary-metatiles',sec),('secondary-attributes',sa)]:(out/(n+'.bin')).write_bytes(data)
    receipt=dict(status='CIVIC_NATIVE_ART_CANDIDATE_NOT_RUNTIME_ACCEPTANCE',source_sha256=m.base.sha(raw),source_cells=len(words),secondary_records=len(sec)//16,native_assets=assets,facade_origins=FACADES,limits=['Native neutral houses mark six physical source facility positions, not finished architecture or services','All source collision/elevation/full attributes unchanged, all doors remain closed','No DS artwork or permanent IDs/engine changes'])
    receipt['output_sha256']={str(p.relative_to(out)):m.base.sha(p.read_bytes()) for p in out.iterdir() if p.is_file()};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();print(json.dumps(build(a.engine,a.out),indent=2))
