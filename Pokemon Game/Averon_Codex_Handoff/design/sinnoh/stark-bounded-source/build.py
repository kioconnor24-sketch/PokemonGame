#!/usr/bin/env python3
"""Publish exact bounded Stark source using the tested DEV splitter, no saved IDs."""
import argparse,importlib.util,io,json,struct
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
s=importlib.util.spec_from_file_location('stark_bounded_projection',HERE.parent/'battle-frontier-dev/prepare_scene.py')
scene=importlib.util.module_from_spec(s);s.loader.exec_module(scene)
KEYS=('Route227','StarkOutside','StarkRoom1','StarkRoom2West','StarkRoom2Center','StarkRoom2East','StarkRoom3')
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(scene.base.git(engine,'rev-parse','--show-toplevel').decode().strip())
    files,dev=scene.assemble(repo);pins={}
    def read(p):
        raw=scene.base.verified_file(ROOT,p.relative_to(ROOT),'HEAD');pins[str(p.relative_to(ROOT))]=scene.base.sha(raw);return raw
    definitions={}
    for family,folder in [('Cave',HERE.parent/'stark-approach/cave-family'),('Outdoor',HERE.parent/'battle-zone-north/outdoor-family')]:
        definitions[family]={n:read(folder/n) for n in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin')}
    packets={};dimensions={};seams=[]
    for key in KEYS:
        record=dev['scene'][key];dev_name=record['name'];header=json.loads(files['data/maps/'+dev_name+'/map.json'])
        raw=files['data/layouts/'+dev_name+'/map.bin'];border=files['data/layouts/'+dev_name+'/border.bin']
        family='Outdoor' if key=='Route227' else 'Cave'
        if key.startswith('StarkRoom2'):
            label=key.removeprefix('StarkRoom2')
            folder=HERE.parent/'stark-mountain/staged/Room2'
            original=json.loads(read(folder/'map.json'))
            name=original['name']+label;layout=original['layout']+'_'+label.upper()
            art=Image.open(io.BytesIO(read(folder/'preview.png')));art.load()
            col=('West','Center','East').index(label);art=art.crop((col*512,0,(col+1)*512,1536))
            buf=io.BytesIO();art.save(buf,format='PNG');preview=buf.getvalue()
        else:
            folder=HERE.parent/('stark-mountain/staged/Room3' if key=='StarkRoom3' else 'stark-approach/staged/'+dict(Route227='Route227',StarkOutside='Outside',StarkRoom1='Room1')[key])
            original=json.loads(read(folder/'map.json'));name,layout=original['name'],original['layout']
            preview=read(folder/'preview.png')
            if raw!=read(folder/'map.bin') or border!=read(folder/'border.bin'):raise ValueError('unchanged source geometry differs')
        header.update(name=name,layout=layout,region_map_section='MAPSEC_PENDING_OWNER')
        w,h=record['dimensions'];dimensions[key]=[w,h]
        bank=definitions[family]
        attrs={str(v&1023):struct.unpack_from('<H',bank['primary-attributes.bin' if v&1023<512 else 'secondary-attributes.bin'],2*(v%512))[0] for (v,) in struct.iter_unpack('<H',raw+border)}
        layout=dict(id=layout,name=name+'_Layout',width=w,height=h,primary_tileset='gTileset_General',
            secondary_tileset='gTileset_StarkBounded'+family,layout_version='emerald',
            blockdata_filepath='staged/'+key+'/map.bin',border_filepath='staged/'+key+'/border.bin')
        packets[key]=dict(raw=raw,border=border,header=header,layout=layout,attrs=attrs,preview=preview,family=family)
    for a,b in [('StarkRoom2West','StarkRoom2Center'),('StarkRoom2Center','StarkRoom2East')]:
        first,second=packets[a],packets[b];lanes=[]
        for y in range(96):
            x=struct.unpack_from('<H',first['raw'],2*(y*32+31))[0];z=struct.unpack_from('<H',second['raw'],2*y*32)[0]
            if x&0xc00 or z&0xc00 or first['attrs'][str(x&1023)]&255 or second['attrs'][str(z&1023)]&255:continue
            if x>>12 and z>>12 and x>>12!=z>>12:continue
            lanes.append(y)
        if not lanes:raise ValueError('split source has no ordinary-ground seam')
        seams.append(dict(west=a,east=b,offset=0,ordinary_ground_rows=lanes))
    out.mkdir(parents=True)
    for family,data in definitions.items():
        p=out/'families'/family;p.mkdir(parents=True)
        for name,raw in data.items():(p/name).write_bytes(raw)
    for name,data in packets.items():
        p=out/'staged'/name;p.mkdir(parents=True)
        for filename,raw in [('map.bin',data['raw']),('border.bin',data['border']),('map.json',scene.encode(data['header'])),('layout.json',scene.encode(data['layout'])),('attributes.json',scene.encode(data['attrs'])),('preview.png',data['preview'])]:(p/filename).write_bytes(raw)
    receipt=dict(status='BOUNDED_STARK_SOURCE_ALTERNATIVE_NOT_RUNTIME_OR_PRODUCTION_ACCEPTANCE',source_sha=scene.base.git(ROOT,'rev-parse','HEAD').decode().strip(),
        native_engine_tree=scene.ENGINE_TREE,projection_recipe_files=dev['files'],source_sha256=pins,dimensions=dimensions,
        padded_cells={n:(w+15)*(h+14) for n,(w,h) in dimensions.items()},split_seams=seams,
        bank_for_map={n:p['family'] for n,p in packets.items()},
        limits=['Actual old Room2 96x96 pads12210>10240; three32x96 parts pad5170 each',
                'Exact original cells/metadata/pixels; old source heights/slope proxies/pockets unchanged',
                'Route226 external link retained; no invented return or natural Surf/rail/rock-climb acceptance',
                'Original Room2 proposal must not be registered alongside bounded variant',
                'Pending source section restored; no DEV217 origin surrogate, savedIDs, registry, engine, story or Claude edits',
                'No ROM/native-game/mGBA/Save/Delta acceptance'])
    receipt['output_sha256']={str(p.relative_to(out)):scene.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'receipt.json').write_bytes(scene.encode(receipt));return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(build(a.engine,a.out),indent=2))
