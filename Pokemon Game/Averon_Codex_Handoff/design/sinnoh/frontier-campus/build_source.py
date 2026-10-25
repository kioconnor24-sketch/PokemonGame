#!/usr/bin/env python3
"""Conservative physical Frontier campus/gate projection; no DS art or mechanics."""
import importlib.util,json,struct,argparse
from fractions import Fraction
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('frontier_reuse',HERE.parent/'stark-mountain/build_source.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
base=m.base;dual=m.dual;packer=m.a.a
DIMS={'Gate':(32,32),'Campus':(96,96)}

def extract(inputs):
    pins=json.loads((HERE/'source-pins.json').read_text());raws={}
    for key,pin in pins['files'].items():
        raw=(Path(inputs)/pin['private_input_name']).read_bytes()
        import hashlib
        if base.sha(raw)!=pin['sha256'] or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=pin['git_blob']:raise ValueError('source pin differs')
        raws[key]=raw
    result={}
    for name,(w,h) in DIMS.items():
        matrix=json.loads(raws[name])['maps'];points=[];rejected={}
        for yy,row in enumerate(matrix):
            for xx,land in enumerate(row):
                raw=raws[land];sizes=struct.unpack_from('<4I',raw)
                if sizes[0]!=2048 or 16+sum(sizes)!=len(raw):raise ValueError('section bounds differ')
                data=m.b.decode(raw[16+sum(sizes[:3]):])
                for i,(word,) in enumerate(struct.iter_unpack('<H',raw[16:2064])):
                    if word&0x8000:continue
                    x,y=i%32,i//32;heights={v for _,v in m.b.tile_candidates(data,x,y)}
                    reason=None
                    if len(heights)!=1:reason='missing_or_ambiguous_center'
                    elif word&255 not in (0,0x15,0x65,0x6c,0x6d,0x6e):reason='unsupported_behavior'
                    else:
                        height=next(iter(heights));flat=True
                        for dx,dz in ((-8,-8),(-8,8),(8,-8),(8,8)):
                            values={v for _,v in m.b.candidates(data,(x-16)*m.b.TILE+m.b.TILE//2+dx*m.b.FX,(y-16)*m.b.TILE+m.b.TILE//2+dz*m.b.FX)}
                            if not values:reason='unsupported_footprint';break
                            flat &= height in values
                    if reason:rejected[reason]=rejected.get(reason,0)+1;continue
                    points.append(dict(tile=[xx*32+x,yy*32+y],permission=word,height=str(height/m.b.FX),flat=flat))
        result[name]=dict(dimensions=[w,h],surfaces=points,rejected_permission_clear=rejected)
    return result

def construct(geometry):
    result={}
    for name,(w,h) in DIMS.items():
        g=geometry[name]
        if g['dimensions']!=[w,h]:raise ValueError('bounds differ')
        heights=sorted({Fraction(p['height']) for p in g['surfaces'] if p['flat']})
        if len(heights)>12:raise ValueError('height capacity')
        zmap={v:i+3 for i,v in enumerate(heights)};cells=[0xc00|513]*(w*h);seen=set();sealed=0
        for p in g['surfaces']:
            x,y=p['tile']
            if not 0<=x<w or not 0<=y<h or (x,y) in seen:raise ValueError('invalid/duplicate surface')
            seen.add((x,y))
            # External/capability doors remain sealed until supported shells and links.
            if x in (0,w-1) or y in (0,h-1) or p['permission']&255 not in (0,0x15):sealed+=1;continue
            z=zmap[Fraction(p['height'])] if p['flat'] else 0
            cells[y*w+x]=z<<12|(529 if p['flat'] else 516)
        shape=list(cells)
        for y in range(1,h-1):
            for x in range(1,w-1):
                i=y*w+x
                if shape[i]&0xc00:cells[i]=0xc00|(521 if not shape[i+w]&0xc00 else 530 if not shape[i+1]&0xc00 else 528 if not shape[i-1]&0xc00 else 513)
        header=dict(id='MAP_SINNOH_FRONTIER_'+name.upper(),name='SinnohFrontier'+name,layout='LAYOUT_SINNOH_FRONTIER_'+name.upper(),region='REGION_SINNOH',region_map_section='MAPSEC_PENDING_OWNER',map_type='MAP_TYPE_INDOOR' if name=='Gate' else 'MAP_TYPE_TOWN',music='MUS_ROUTE110',weather='WEATHER_NONE',requires_flash=False,allow_cycling=False,allow_running=True,allow_escaping=False,show_map_name=True,battle_scene='MAP_BATTLE_SCENE_NORMAL',connections=[],warp_events=[],object_events=[],coord_events=[],bg_events=[])
        result[name]=(struct.pack('<%dH'%(w*h),*cells),header,dict(supported=len(seen),sealed_doors_boundaries=sealed,static_components=m.height_components(cells,w,h)))
    return result

def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip())
    geometry=json.loads(base.verified_file(repo,HERE.relative_to(repo)/'geometry.json','HEAD'));result=construct(geometry);assets={}
    def read(p):
        raw=base.verified_file(repo,engine.relative_to(repo)/p,'HEAD');assets[p]=base.sha(raw);return raw
    prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/cave/']
    banks=[read(p+'metatiles.bin') for p in prefixes];pa=read(prefixes[0]+'metatile_attributes.bin');attrs=[bytearray(pa),bytearray(read(prefixes[1]+'metatile_attributes.bin'))]
    for mid in (513,516,521,528,529,530):struct.pack_into('<H',attrs[mid//512],2*(mid%512),0x1000)
    sec=sa=b'';packets={}
    for name,(raw,header,audit) in result.items():
        border=struct.pack('<4H',*[0xc00|513]*4);desired=[packer.words(banks[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)]
        data,sec,sa=packer.pack_art(raw+border,desired,attrs,banks[0],pa,sec,sa);packets[name]=(data[:len(raw)],data[len(raw):],header,audit)
    images=[dual.indexed(read(p+'tiles.png')) for p in prefixes];previews={}
    for name,(raw,border,h,audit) in packets.items():
        deps=dual.closure(raw,[banks[0],sec],images);palettes={i:base.palette(read(prefixes[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
        previews[name]=dual.render(raw,[banks[0],sec],images,palettes,*DIMS[name])
    out.mkdir(parents=True);family=out/'native-family';family.mkdir()
    for n,v in [('primary-metatiles',banks[0]),('primary-attributes',pa),('secondary-metatiles',sec),('secondary-attributes',sa)]:(family/(n+'.bin')).write_bytes(v)
    for name,(raw,border,header,audit) in packets.items():
        p=out/'staged'/name;p.mkdir(parents=True);(p/'map.bin').write_bytes(raw);(p/'border.bin').write_bytes(border);(p/'map.json').write_text(json.dumps(header,indent=2)+'\n');previews[name].save(p/'preview.png')
    receipt=dict(status='CONSERVATIVE_SOURCE_HEIGHT_PROJECTION_NOT_RUNTIME_ACCEPTANCE',maps={n:v[3] for n,v in packets.items()},native_assets=assets,geometry_sha256=base.sha((HERE/'geometry.json').read_bytes()),secondary_records=len(sec)//16,limits=['Native cave proxies, not final campus architecture','Missing/overlapping source surfaces sealed, not guessed','All doors sealed; no Fight Area arrival or facility gameplay','No DS art/props/story/IDs/registry/save changes or runtime proof'])
    receipt['output_sha256']={str(p.relative_to(out)):base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();print(json.dumps(build(a.engine,a.out),indent=2))
