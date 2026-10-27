#!/usr/bin/env python3
"""Neutral native facility interiors and source-ground Frontier doorway copies.

Original GBA interior geometry is reused; these are explicit neutral adaptations,
not donor Sinnoh interiors or implemented competitive facilities.
"""
import argparse,importlib.util,json,re,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('facility_existing',HERE.parent/'frontier-campus/build_source.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
BASE=HERE.parent/'frontier-campus'
TEMPLATES={
'Tower1':'RustboroCity_DevonCorp_1F','Tower2':'RustboroCity_DevonCorp_2F','Tower3':'RustboroCity_DevonCorp_3F',
'Hall1':'SlateportCity_OceanicMuseum_1F','Hall2':'SlateportCity_OceanicMuseum_2F',
'Factory1':'SlateportCity_SternsShipyard_1F','Factory2':'SlateportCity_SternsShipyard_2F',
'Castle':'BattleFrontier_BattlePalaceLobby',
'Arcade1':'LilycoveCity_LilycoveMuseum_1F','Arcade2':'LilycoveCity_LilycoveMuseum_2F'}
PORTS={'Factory1':(77,34),'Hall1':(19,34),'Castle':(33,62),'Arcade1':(64,62),'Tower1':(48,18)}
def folder(symbol):
    name=symbol.removeprefix('gTileset_')
    return re.sub(r'(?<!^)(?=[A-Z])','_',name).lower()
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(m.base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(path):
        raw=m.base.verified_file(repo,path,'HEAD');pins[str(path)]=m.base.sha(raw);return raw
    def eng(path):return read(engine.relative_to(repo)/path)
    layouts={v['id']:v for v in json.loads(eng('data/layouts/layouts.json'))['layouts']}
    source={n:json.loads(eng('data/maps/'+v+'/map.json')) for n,v in TEMPLATES.items()}
    ids={v['id']:'MAP_SINNOH_FRONTIER_'+n.upper() for n,v in source.items()}
    dims={};packets={};previews={};closures=[]
    for name,h in source.items():
        l=layouts[h['layout']];w,height=l['width'],l['height'];dims[name]=[w,height]
        raw=bytearray(eng(l['blockdata_filepath']));border=eng(l['border_filepath'])
        header=json.loads(json.dumps(h));header.update(id=ids[h['id']],name='SinnohFrontier'+name,layout='LAYOUT_SINNOH_FRONTIER_'+name.upper(),
            region='REGION_SINNOH',region_map_section='MAPSEC_PENDING_OWNER',music='MUS_ROUTE110',allow_running=True,
            connections=[],object_events=[],coord_events=[],bg_events=[])
        warps=[]
        for i,event in enumerate(h['warp_events']):
            event=dict(event)
            if event['dest_map'] in ids:event['dest_map']=ids[event['dest_map']]
            elif event['dest_map'] in ('MAP_RUSTBORO_CITY','MAP_SLATEPORT_CITY','MAP_LILYCOVE_CITY','MAP_BATTLE_FRONTIER_OUTSIDE_EAST'):
                # Facility root exits retained as reversible proposed-campus returns.
                if name in PORTS:
                    event['dest_map']='MAP_SINNOH_FRONTIER_CAMPUS';event['dest_warp_id']=str(list(PORTS).index(name))
                else:
                    offset=2*(event['y']*w+event['x']);v=struct.unpack_from('<H',raw,offset)[0]
                    struct.pack_into('<H',raw,offset,v|0xc00);event['dest_map']=header['id'];event['dest_warp_id']=str(i)
                    closures.append(dict(map=name,cell=[event['x'],event['y']],reason='unsupported Tower access sealed',index=i))
            else:
                # Seal the unused final corridor and omit only its trailing warp;
                # all retained source indices stay unchanged.
                x,y=event['x'],event['y'];offset=2*(y*w+x);v=struct.unpack_from('<H',raw,offset)[0]
                struct.pack_into('<H',raw,offset,v|0xc00);event['dest_map']=header['id'];event['dest_warp_id']=str(i)
                closures.append(dict(map=name,cell=[x,y],reason='unbuilt competitive corridor sealed',source_index=i))
                if i!=len(h['warp_events'])-1:raise ValueError('cannot remove non-tail unbuilt warp')
                continue
            warps.append(event)
        header['warp_events']=warps
        prefixes=['data/tilesets/primary/'+folder(l['primary_tileset'])+'/','data/tilesets/secondary/'+folder(l['secondary_tileset'])+'/']
        banks=[eng(p+'metatiles.bin') for p in prefixes];images=[m.dual.indexed(eng(p+'tiles.png')) for p in prefixes]
        attrs=[eng(p+'metatile_attributes.bin') for p in prefixes];deps=m.dual.closure(raw,banks,images)
        palettes={i:m.base.palette(eng(prefixes[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
        previews[name]=m.dual.render(raw,banks,images,palettes,w,height)
        words={str(v&1023):m.packer.attribute(attrs[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)}
        layout=dict(l);layout.update(id=header['layout'],name=header['name']+'_Layout',blockdata_filepath='staged/'+name+'/map.bin',border_filepath='staged/'+name+'/border.bin')
        packets[name]=(bytes(raw),border,header,layout,words)
    # Campus copy: only four genuinely supported source doorway cells reopened.
    raw=bytearray(read((BASE/'civic-candidate/map.bin').relative_to(repo)))
    header=json.loads(read((BASE/'staged/Campus/map.json').relative_to(repo)));header['warp_events']=[]
    geometry=json.loads(read((BASE/'geometry.json').relative_to(repo)))['Campus']['surfaces']
    supports={tuple(p['tile']):p for p in geometry};zmap={str(v):i+3 for i,v in enumerate(sorted({m.Fraction(p['height']) for p in geometry if p['flat']}))}
    changes=[]
    for index,(name,(x,y)) in enumerate(PORTS.items()):
        if (x,y) not in supports:raise ValueError('unsupported facility door')
        z=zmap[supports[x,y]['height']];old=struct.unpack_from('<H',raw,2*(y*96+x))[0]
        # Use native primary ladder-free normal ground for source-stage portal.
        # Actual warp-trigger art/behavior stays an explicit runtime integration gate.
        new=z<<12|265;struct.pack_into('<H',raw,2*(y*96+x),new)
        header['warp_events'].append(dict(x=x,y=y,elevation=z,dest_map=packets[name][2]['id'],dest_warp_id='0'))
        changes.append(dict(cell=[x,y],before=old,after=new,source_height=supports[x,y]['height']))
    # Append one isolated ladder-behavior portal record; never mutate primary
    # attributes or reinterpret normal grass elsewhere.
    prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
    pa=read((BASE/'civic-candidate/primary-attributes.bin').relative_to(repo))
    primary=read((BASE/'civic-candidate/primary-metatiles.bin').relative_to(repo))
    sec=read((BASE/'civic-candidate/secondary-metatiles.bin').relative_to(repo))
    sa=read((BASE/'civic-candidate/secondary-attributes.bin').relative_to(repo))
    source_attrs=[pa,sa+struct.pack('<H',0x1061)];placeholder=512+len(sec)//16
    for x,y in PORTS.values():
        off=2*(y*96+x);v=struct.unpack_from('<H',raw,off)[0];struct.pack_into('<H',raw,off,(v&0xfc00)|placeholder)
    border=read((BASE/'civic-candidate/border.bin').relative_to(repo))
    desired=[]
    for (v,) in struct.iter_unpack('<H',raw+border):
        mid=v&1023
        desired.append(m.packer.words(primary,265) if mid==placeholder else m.packer.words((primary,sec)[mid//512],mid%512))
    converted,sec,sa=m.packer.pack_art(raw+border,desired,source_attrs,primary,pa,sec,sa)
    raw=bytearray(converted[:len(raw)])
    for c in changes:c['after']=struct.unpack_from('<H',raw,2*(c['cell'][1]*96+c['cell'][0]))[0]
    campus_images=[m.dual.indexed(eng(p+'tiles.png')) for p in prefixes]
    dependencies=m.dual.closure(raw,[primary,sec],campus_images)
    palettes={i:m.base.palette(eng(prefixes[i>=6]+'palettes/%02d.pal'%i)) for i in dependencies['palettes']}
    campus_preview=m.dual.render(raw,[primary,sec],campus_images,palettes,96,96)
    # Tower portal is explicitly moved one tile south to supported doorstep48,18.
    # Original unsupported source door48,17 stays closed.
    out.mkdir(parents=True)
    for name,(raw_,border,h,l,attrs) in packets.items():
        p=out/'staged'/name;p.mkdir(parents=True)
        (p/'map.bin').write_bytes(raw_);(p/'border.bin').write_bytes(border)
        (p/'map.json').write_text(json.dumps(h,indent=2)+'\n');(p/'layout.json').write_text(json.dumps(l,indent=2)+'\n')
        (p/'attributes.json').write_text(json.dumps(attrs,indent=2)+'\n');previews[name].save(p/'preview.png')
    family=out/'campus-family';family.mkdir()
    for n,v in [('primary-metatiles',primary),('primary-attributes',pa),('secondary-metatiles',sec),('secondary-attributes',sa)]:
        (family/(n+'.bin')).write_bytes(v)
    p=out/'staged/Campus';p.mkdir(parents=True);(p/'map.bin').write_bytes(raw);(p/'border.bin').write_bytes(converted[len(raw):]);campus_preview.save(p/'preview.png');(p/'map.json').write_text(json.dumps(header,indent=2)+'\n')
    receipt=dict(status='NEUTRAL_NATIVE_INTERIOR_SOURCE_CANDIDATES_NOT_RUNTIME_ACCEPTANCE',maps=dims,source_sha256=pins,
        campus_door_changes=changes,sealed_corridors=closures,limits=['Physical templates only; all original NPCs/signs/scripts removed',
        'No minigames, rewards, trainers, encounters or services','Tower portal moved from unsupported48,17 to supported doorstep48,18; original tile stays closed',
        'Five explicit neutral portal cells use native ladder trigger; ordinary gameplay acceptance pending',
        'No production IDs/registry/save changes or runtime acceptance'])
    receipt['output_sha256']={str(p.relative_to(out)):m.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();print(json.dumps(build(a.engine,a.out),indent=2))
