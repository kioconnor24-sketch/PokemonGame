#!/usr/bin/env python3
"""Stage a connected five-map Eterna/Cycling geography cluster, no donor art.

Uses the merged donor converter for identity round trips. Only layout cells,
collision/elevation schematics and sanitized technical headers are published.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import re
from pathlib import Path
import struct
import subprocess
import tempfile
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
SCRIPTS=HERE.parents[3]/'scripts'
spec=importlib.util.spec_from_file_location('eterna_pilot',SCRIPTS/'sinnoh-donor-map-pilot.py')
pilot=importlib.util.module_from_spec(spec);spec.loader.exec_module(pilot)
REVISION='38228bb574a3557345852b758d5f1a65eb01bb22'
MAPS={
 'EternaCity':(60,55,'97a89e5859ba1eadce5edd3933113f1e5ad854b7'),
 'Route206_North':(9,11,'38af8d53086c00edfee9778c2b17a9d5a12c1872'),
 'Route206':(28,120,'be22592888868f46afd1c6270a103aa0c5ad791d'),
 'Route206_South':(9,11,'38af8d53086c00edfee9778c2b17a9d5a12c1872'),
 'Route211_West':(36,28,'3e9730a4a2bc44fd0334f00bbdfc894db4439db5')}


def sha(data):return hashlib.sha256(data).hexdigest()
def encode(value):return (json.dumps(value,indent=2)+'\n').encode()


def cells(raw,width,height):
 if type(width) is not int or type(height) is not int or width<1 or height<1 or len(raw)!=width*height*2:
  raise ValueError('invalid source dimensions')
 return list(struct.unpack('<%dH'%(width*height),raw))


def destination(point,direction,offset,width,height):
 x,y=point
 if direction=='up':return x-offset,height-1
 if direction=='down':return x-offset,0
 if direction=='left':return width-1,y-offset
 if direction=='right':return 0,y-offset
 raise ValueError('invalid connection direction')


def sanitize(headers,layouts,raws):
 """Pure whole-cluster warp compaction, reciprocal seams and explicit closures."""
 ids={h['id']:name for name,h in headers.items()}
 if len(ids)!=len(headers):raise ValueError('duplicate source map ID')
 keep={name:[i for i,w in enumerate(h['warp_events']) if w['dest_map'] in ids] for name,h in headers.items()}
 translations={name:{old:new for new,old in enumerate(indices)} for name,indices in keep.items()}
 data={name:cells(raws[name],layouts[name]['width'],layouts[name]['height']) for name in headers}
 out={};closures={};inverse={'up':'down','down':'up','left':'right','right':'left'}
 for name,h in headers.items():
  w,height=layouts[name]['width'],layouts[name]['height'];result=list(data[name]);changes={}
  events=h['warp_events'];anchors=set()
  for event in events:
   x,y=event['x'],event['y']
   if type(x) is not int or type(y) is not int or not 0<=x<w or not 0<=y<height or (x,y) in anchors or type(event['elevation']) is not int or not 0<=event['elevation']<16:
    raise ValueError('invalid source warp anchor')
   anchors.add((x,y))
  retained={(events[i]['x'],events[i]['y']) for i in keep[name]}
  def close(x,y,reason):
   if (x,y) in retained:raise ValueError('closure collides with retained warp')
   i=y*w+x;before=result[i];result[i]=(before&~0xC00)|0x400
   if before!=result[i]:changes[i]=dict(x=x,y=y,before=before,after=result[i],reason=reason)
  for i,e in enumerate(events):
   if i not in keep[name]:close(e['x'],e['y'],'unbuilt source destination')
  warps=[]
  for i in keep[name]:
   e=copy.deepcopy(events[i]);target=ids[e['dest_map']];old=int(e['dest_warp_id'])
   if old not in translations[target]:raise ValueError('return warp removed or invalid')
   e['dest_warp_id']=str(translations[target][old]);warps.append(e)
  connections=[copy.deepcopy(c) for c in h.get('connections') or [] if c['map'] in ids]
  if len({c['direction'] for c in connections})!=len(connections):raise ValueError('duplicate connection direction')
  for c in connections:
   target=ids[c['map']]
   reverse=[x for x in headers[target].get('connections') or [] if x['map']==h['id'] and x['direction']==inverse[c['direction']] and x['offset']==-c['offset']]
   if len(reverse)!=1:raise ValueError('nonreciprocal source offset')
  edges={'up':[(x,0) for x in range(w)],'down':[(x,height-1) for x in range(w)],'left':[(0,y) for y in range(height)],'right':[(w-1,y) for y in range(height)]}
  for direction,points in edges.items():
   connection=next((c for c in connections if c['direction']==direction),None)
   for x,y in points:
    if (x,y) in retained:continue # An approved paired warp is a real boundary exit.
    reason='unbuilt external edge'
    if connection:
     target=ids[connection['map']];tw,th=layouts[target]['width'],layouts[target]['height'];tx,ty=destination((x,y),direction,connection['offset'],tw,th)
     if 0<=tx<tw and 0<=ty<th and not ((data[target][ty*tw+tx]>>10)&3):continue
     reason='nonoverlap or blocked source seam endpoint'
    close(x,y,reason)
  if any((old^new)&~0xC00 for old,new in zip(data[name],result)):raise ValueError('identity or elevation changed')
  new={k:copy.deepcopy(h[k]) for k in ('id','name','layout','map_type','requires_flash','allow_cycling','allow_escaping','allow_running','battle_scene') if k in h}
  new.update(region='REGION_SINNOH',region_map_section='MAPSEC_PENDING_OWNER',music='MUS_RUSTBORO' if name=='EternaCity' else 'MUS_ROUTE110',weather='WEATHER_NONE',show_map_name=True,
             connections=connections,warp_events=warps,object_events=[],coord_events=[],bg_events=[])
  out[name]=(struct.pack('<%dH'%len(result),*result),new);closures[name]=list(changes.values())
 # A target corner can have been walkable in the original source but closed
 # above because its other edge has no constructed neighbour. Seal against
 # FINAL candidate cells, to a fixed point; never retain a dangling seam just
 # because its destination was open before cluster sanitization.
 final={name:cells(raw,layouts[name]['width'],layouts[name]['height']) for name,(raw,_) in out.items()}
 while True:
  pending={}
  for name,(_,header) in out.items():
   w,height=layouts[name]['width'],layouts[name]['height']
   retained={(e['x'],e['y']) for e in header['warp_events']}
   for connection in header['connections']:
    direction=connection['direction'];target=ids[connection['map']]
    tw,th=layouts[target]['width'],layouts[target]['height']
    points=([(x,0 if direction=='up' else height-1) for x in range(w)] if direction in ('up','down')
            else [(0 if direction=='left' else w-1,y) for y in range(height)])
    for x,y in points:
     index=y*w+x
     if (x,y) in retained or final[name][index]&0xC00:continue
     tx,ty=destination((x,y),direction,connection['offset'],tw,th)
     if not (0<=tx<tw and 0<=ty<th) or final[target][ty*tw+tx]&0xC00:
      pending[name,index]=dict(x=x,y=y,before=final[name][index],after=(final[name][index]&~0xC00)|0x400,
                               reason='destination closed by final cluster sanitization')
  if not pending:break
  for (name,index),change in pending.items():
   final[name][index]=change['after'];closures[name].append(change)
 for name,values in final.items():
  out[name]=(struct.pack('<%dH'%len(values),*values),out[name][1])
 return out,closures,translations


def schematic(raw,width,height):
 values=cells(raw,width,height);im=Image.new('RGB',(width,height))
 for i,v in enumerate(values):
  level=v>>12;blocked=(v>>10)&3
  im.putpixel((i%width,i//width),(40,40,45) if blocked else (225,170,45) if level==15 else (35+level*11,150,80+level*5))
 return im.resize((width*4,height*4),Image.Resampling.NEAREST)


def repair_border(original,spec,replacement):
 if sha(original)!=spec['expected_sha256'] or not original or len(original)%2 or len(replacement)!=len(original):
  raise ValueError('border repair precondition changed')
 return replacement


def build(donor,out,maps=MAPS,border_overrides=None):
 donor,out=Path(donor).resolve(),Path(out).resolve()
 if out.exists() or out.is_relative_to(donor) or 'engine' in out.parts:raise ValueError('new off-engine output required')
 def read(path):
  value=subprocess.check_output(['git','-C',str(donor),'show',REVISION+':'+path],stderr=subprocess.PIPE)
  consumed[path]=sha(value);return value
 if subprocess.check_output(['git','-C',str(donor),'rev-parse','HEAD'],text=True).strip()!=REVISION:raise ValueError('wrong donor revision')
 border_overrides=border_overrides or {}
 consumed={};table=json.loads(read('data/layouts/layouts.json'))['layouts'];headers={};layouts={};raws={};borders={};identities={}
 with tempfile.TemporaryDirectory() as temp:
  source=Path(temp)/'donor-identity';converted=Path(temp)/'converted';source.mkdir();converted.mkdir()
  for name,(w,h,expected_blob) in maps.items():
   header=read('data/maps/'+name+'/map.json');headers[name]=json.loads(header)
   entries=[x for x in table if x['id']==headers[name]['layout']]
   if len(entries)!=1:raise ValueError('source layout not unique')
   layout=entries[0];layouts[name]=layout
   if (layout['width'],layout['height'])!=(w,h):raise ValueError('source dimension pin changed')
   raw=read(layout['blockdata_filepath']);raws[name]=raw
   actual=subprocess.check_output(['git','-C',str(donor),'rev-parse',REVISION+':'+layout['blockdata_filepath']],text=True).strip()
   if actual!=expected_blob:raise ValueError('source map blob pin changed')
   borders[name]=read(layout['border_filepath'])
   if name in border_overrides:
    spec=border_overrides[name]
    borders[name]=repair_border(borders[name],spec,read(spec['replacement_source_path']))
   for path,value in [('data/maps/'+name+'/map.json',header),(layout['blockdata_filepath'],raw)]:
    dest=source/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(value)
  p=source/'data/layouts/layouts.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(encode({'layouts':list(layouts.values())}))
  # Donor-only identity round trip: NOT a claim of Averon art compatibility.
  for name in maps:
   analysis=pilot.analyze(source,name,REVISION);manifest=pilot.draft_manifest(analysis)
   manifest.update(target_map_id=headers[name]['id'],target_primary_tileset=layouts[name]['primary_tileset'],target_secondary_tileset=layouts[name]['secondary_tileset'])
   for mid,v in manifest['metatiles'].items():v.update(target=int(mid),behavior_verified=True,graphics_verified=True)
   identities[name]=pilot.convert(source,name,manifest,converted/(name+'.bin'))
   if (converted/(name+'.bin')).read_bytes()!=raws[name]:raise ValueError('existing converter identity mismatch')
  staged,closures,translations=sanitize(headers,layouts,raws)
  receipt=dict(status='OFF_ENGINE_GEOGRAPHY_ONLY_AVERON_GRAPHICS_PENDING',donor_revision=REVISION,donor_sha256=consumed,identity_roundtrips=identities,source_geometry_headers={name:{k:copy.deepcopy(h[k]) for k in ('id','name','layout','map_type','requires_flash','allow_cycling','allow_escaping','allow_running','battle_scene','warp_events','connections') if k in h} for name,h in headers.items()},warp_index_translation=translations,closure_changes=closures,maps={},limits=['No donor pixels/palettes/scripts/objects/trainers/encounters copied','No production registry, saved ID, ROM or mGBA acceptance','Yellow collision preview means elevation15, not actual art'])
  if border_overrides:receipt['border_substitutions']=border_overrides
  out.mkdir(parents=True)
  for name,(raw,h) in staged.items():
   folder=out/'staged'/name;folder.mkdir(parents=True);(folder/'map.bin').write_bytes(raw);(folder/'border.bin').write_bytes(borders[name]);(folder/'map.json').write_bytes(encode(h))
   w,height=maps[name][:2];schematic(raw,w,height).save(folder/'collision.png')
   attrs={}
   for secondary,key in ((False,'primary_tileset'),(True,'secondary_tileset')):
    symbol=re.sub(r'(?<=[a-z0-9])(?=[A-Z])','_',layouts[name][key].removeprefix('gTileset_')).lower();path='data/tilesets/'+('secondary/' if secondary else 'primary/')+symbol+'/metatile_attributes.bin'
    bank=read(path)
    for (cell,) in struct.iter_unpack('<H',raw+borders[name]):
     mid=cell&1023
     if (mid>=512)!=secondary:continue
     i=mid%512
     if len(bank)<(i+1)*2:raise ValueError(f'{name} source metatile {mid} outside {path} ({len(bank)//2} records)')
     attrs[str(mid)]=struct.unpack_from('<H',bank,i*2)[0]
   (folder/'attributes.json').write_bytes(encode(dict(source_tilesets=[layouts[name]['primary_tileset'],layouts[name]['secondary_tileset']],used_source_attribute_words=attrs,averon_art_compatibility='UNVERIFIED')))
   receipt['maps'][name]=dict(dimensions=[w,height],source_blob=maps[name][2],source_sha256=sha(raws[name]),staged_sha256=sha(raw),border_sha256=sha(borders[name]),closed_cells=len(closures[name]),warp_count=len(h['warp_events']),connections=h['connections'],elevation15_cells=sum(v[0]>>12==15 for v in struct.iter_unpack('<H',raw)))
  (out/'source-receipt.json').write_bytes(encode(receipt))
 return receipt


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--donor',required=True,type=Path);p.add_argument('--out',required=True,type=Path);args=p.parse_args();print(json.dumps(build(args.donor,args.out),indent=2))
