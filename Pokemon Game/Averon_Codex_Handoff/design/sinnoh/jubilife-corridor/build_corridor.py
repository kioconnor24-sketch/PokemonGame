#!/usr/bin/env python3
"""Build six real donor-derived OFF-ENGINE geographic candidates, never registries.

Geometry reuse is owner-authorized. Donor-art render previews remain private;
only authored collision schematics and donor geometry are published. This is NOT
Averon graphics conversion, section registration, gameplay or rights acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
GAME=HERE.parents[3]
SCRIPTS=GAME/'scripts'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
static=load('family_static',SCRIPTS/'sinnoh-isolated-tileset.py')
dual=load('family_dual',SCRIPTS/'sinnoh-dual-bank-family.py')
pilot=static.pilot

def digest(raw):return hashlib.sha256(raw).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def bank(root,folder,revision):
 prefix=Path('data/tilesets')/folder
 record=static.verified_file(root,prefix/'metatiles.bin',revision)
 attr=static.verified_file(root,prefix/'metatile_attributes.bin',revision)
 if len(record)%16 or len(attr)*8!=len(record):raise ValueError('invalid metatile bank')
 import io
 im=dual.indexed(static.verified_file(root,prefix/'tiles.png',revision))
 pals=[static.palette(static.verified_file(root,prefix/('palettes/%02d.pal'%i),revision)) for i in range(16)]
 return record,attr,im,pals

def build(donor,output,private_previews=None):
 donor,output=Path(donor).resolve(),Path(output).resolve()
 spec=json.loads((HERE/'corridor-spec.json').read_text());revision=spec['donor_revision']
 if static.git(donor,'rev-parse','HEAD').decode().strip()!=revision:raise ValueError('wrong donor HEAD')
 if output.exists() or 'engine' in output.parts or output.is_relative_to(donor):raise ValueError('new off-engine output required')
 if private_previews:
  private_previews=Path(private_previews).resolve()
  if private_previews.is_relative_to(GAME.parent):raise ValueError('donor art previews must stay outside repository')
  private_previews.mkdir(parents=True,exist_ok=True)
 layouts=json.loads(static.verified_file(donor,'data/layouts/layouts.json',revision))['layouts']
 tables={};headers={};receipt={'status':spec['status'],'donor_revision':revision,'maps':{},'connections':spec['connections'],'external_connection':spec['external_connection']}
 for name,config in spec['maps'].items():
  header=json.loads(static.verified_file(donor,'data/maps/'+name+'/map.json',revision));headers[name]=header
  layout=next(x for x in layouts if x['id']==header['layout'])
  raw=static.verified_file(donor,layout['blockdata_filepath'],revision)
  if static.git(donor,'hash-object',str(donor/layout['blockdata_filepath'])).decode().strip()!=config['blob']:raise ValueError('wrong source blob')
  w,h=config['dimensions']
  if [layout['width'],layout['height']]!=[w,h] or len(raw)!=w*h*2 or (w+15)*(h+14)>10240:raise ValueError('dimension/buffer mismatch')
  tables[name]=[(layout,raw),None]
 # Preserve raw warp coordinates, sanitize graph, and renumber ONLY local candidate warp slots.
 ids={headers[n]['id']:n for n in headers}
 indexes={n:{old:new for new,old in enumerate(c['retain_warps'])} for n,c in spec['maps'].items()}
 for name,config in spec['maps'].items():
  (layout,raw),_=tables[name];header=headers[name];w,h=config['dimensions'];cells=list(struct.unpack('<'+str(w*h)+'H',raw));before=list(cells)
  warps=[];retained={}
  for old in config['retain_warps']:
   source=header['warp_events'][old];target=ids.get(source['dest_map'])
   if target is None:raise ValueError('unexpected unbuilt retained warp')
   dest_old=int(source['dest_warp_id'])
   if dest_old not in indexes[target]:raise ValueError('destination warp was dropped')
   warps.append({'x':source['x'],'y':source['y'],'elevation':source['elevation'],'dest_map':target,'dest_warp_id':indexes[target][dest_old],'source_collision':(before[source['y']*w+source['x']]>>10)&3})
   retained[(source['x'],source['y'])]=True
  closures={}
  def close(x,y,reason):
   if (x,y) in retained:return
   i=y*w+x;cells[i]=(cells[i]&~0xC00)|0x400;closures[str(i)]=reason
  for i,source in enumerate(header['warp_events']):
   if i not in config['retain_warps']:close(source['x'],source['y'],'unbuilt door/exit')
  for direction in config['close_edges']:
   coords=([(x,0 if direction=='up' else h-1) for x in range(w)] if direction in ('up','down') else [(0 if direction=='left' else w-1,y) for y in range(h)])
   for x,y in coords:close(x,y,'unbuilt boundary '+direction)
  closed=[{'x':i%w,'y':i//w,'before':before[i],'after':cells[i],'reason':closures[str(i)]} for i in range(w*h) if cells[i]!=before[i]]
  out=output/name;out.mkdir(parents=True)
  (out/'source.bin').write_bytes(raw);candidate=struct.pack('<'+str(len(cells))+'H',*cells);(out/'map.bin').write_bytes(candidate)
  border=static.verified_file(donor,layout['border_filepath'],revision);(out/'border.bin').write_bytes(border)
  # Empty event families are deliberate: no NPCs, music, hidden rewards, services or flags.
  sanitized={'name':name,'status':'UNREGISTERED_CANDIDATE','dimensions':[w,h],'section':None,'section_parent':config['parent'],
             'source_tilesets':[layout['primary_tileset'],layout['secondary_tileset']],
             'connections':[c for c in spec['connections'] if c['from']==name], 'warp_events':warps,
             'object_events':[],'coord_events':[],'bg_events':[],'scripts':[],'encounters':[],
             'services':[],'collision_closures':closed}
  dump(out/'map.json',sanitized)
  colors={0:(202,226,180),1:(50,60,60),2:(150,100,70),3:(190,130,150)}
  im=Image.new('RGB',(w*8,h*8));draw=ImageDraw.Draw(im)
  for i,c in enumerate(cells):draw.rectangle((i%w*8,i//w*8,i%w*8+7,i//w*8+7),fill=colors[(c>>10)&3])
  for warp in warps:draw.rectangle((warp['x']*8,warp['y']*8,warp['x']*8+7,warp['y']*8+7),fill=(50,100,255))
  im.save(out/'collision.png')
  symbols=(layout['primary_tileset'],layout['secondary_tileset'])
  folders={'gTileset_General':'primary/general','gTileset_Building':'primary/building','gTileset_Rustboro':'secondary/rustboro','gTileset_Cave':'secondary/cave','gTileset_PokemonCenter':'secondary/pokemon_center','gTileset_Shop':'secondary/shop','gTileset_PokemonSchool':'secondary/pokemon_school'}
  banks=[bank(donor,folders[s],revision) for s in symbols];records=[b[0] for b in banks];images=[b[2] for b in banks];pals={i:banks[0 if i<6 else 1][3][i] for i in range(16)}
  dep=dual.closure(raw+border,records,images)
  # A donor-only identity manifest is legitimate here because the SAME exact donor
  # assets define source and destination. It does NOT attest Averon compatibility.
  analysis=pilot.analyze(donor,name,revision);manifest=pilot.draft_manifest(analysis)
  manifest.update(target_map_id='CANDIDATE_'+name,target_primary_tileset='DONOR_ONLY_'+symbols[0],target_secondary_tileset='DONOR_ONLY_'+symbols[1])
  for key,v in manifest['metatiles'].items():v.update(target=int(key),graphics_verified=True,behavior_verified=True)
  # Run the existing converter, no competing binary remapper.
  pilot.convert(donor,name,manifest,out/'donor-identity.bin');dump(out/'identity-remap.json',manifest)
  if (out/'donor-identity.bin').read_bytes()!=raw:raise ValueError('existing converter changed identity geometry')
  if private_previews:
   dual.render(candidate,records,images,pals,w,h).save(private_previews/(name+'.png'))
  receipt['maps'][name]={'blob':config['blob'],'source_sha256':digest(raw),'candidate_sha256':digest(candidate),'dimensions':[w,h],
                         'source_cells':w*h,'closures':len(closed),'dependencies':dep,'tilesets':list(symbols),'geometry_identity_except_documented_collision_closures':True,
                         'source_graphics_scope':'PRIVATE_DONOR_ONLY_PREVIEW_NOT_DISTRIBUTION_OR_AVERON_COMPATIBILITY',
                         'dropped_events':{k:len(header.get(k,[])) for k in ('object_events','coord_events','bg_events')}}
 dump(output/'receipt.json',receipt)
 return receipt

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--donor-root',required=True);p.add_argument('--output',required=True);p.add_argument('--private-previews')
 a=p.parse_args();print(json.dumps(build(a.donor_root,a.output,a.private_previews),indent=2))
