#!/usr/bin/env python3
"""Author a bounded city-art alternative from already present Averon templates.

This is a PROVISIONAL map draft. Explicit regional edits are geography adaptations,
not an identity conversion or complete source-behavior/graphical acceptance.
"""
import argparse
import importlib.util
import json
import re
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('existing_assets',HERE/'adapt_existing_assets.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a)

def patch_rectangle(cells,width,source,source_width,rectangle,destination,reason,edits):
 x,y,w,h=rectangle;dx,dy=destination
 if min(x,y,dx,dy)<0 or x+w>source_width or (y+h)*source_width>len(source) or dx+w>width or (dy+h)*width>len(cells):raise ValueError('template rectangle out of bounds')
 saved=[source[(y+row)*source_width+x+col] for row in range(h) for col in range(w)]
 for row in range(h):
  for col in range(w):
   i=(dy+row)*width+dx+col;new=saved[row*w+col]
   if cells[i]!=new:edits.append({'x':dx+col,'y':dy+row,'before':cells[i],'after':new,'reason':reason});cells[i]=new

def build(engine,staged,output):
 engine,staged,output=map(Path,(engine,staged,output))
 if output.exists() or 'engine' in output.resolve().parts:raise ValueError('new off-engine output required')
 raw=(staged/'JubilifeCity/map.bin').read_bytes();cells=list(struct.unpack('<4480H',raw));original=list(cells)
 stock=(engine/'data/layouts/RustboroCity/map.bin').read_bytes();stock=list(struct.unpack('<2400H',stock));edits=[]
 # Clear only the two incompatible landmark envelopes using existing adjacent paving.
 # Roof/height changes are deliberate disclosed adaptations, no invented services.
 paving=original[15*70+35]
 for x,y,w,h in ((15,4,9,11),(36,0,9,14)):
  patch_rectangle(cells,70,[paving]*(w*h),w,(0,0,w,h),(x,y),'neutral landmark envelope adapted to existing art',edits)
 # Devon's artwork is reused as a NEUTRAL facade, no company/NPC/script imported.
 patch_rectangle(cells,70,stock,40,(6,7,12,9),(14,5),'existing Averon neutral landmark facade west',edits)
 patch_rectangle(cells,70,stock,40,(6,7,12,9),(35,5),'existing Averon neutral landmark facade north',edits)
 # Preserve active door anchors by translating the existing Rustboro templates.
 patch_rectangle(cells,70,stock,40,(13,34,7,5),(52,32),'existing Averon Center facade; door55,36 retained',edits)
 patch_rectangle(cells,70,stock,40,(14,42,5,4),(52,23),'existing Averon Mart facade; door54,26 retained',edits)
 # The nine source fountain records are absent from Averon Rustboro. Reuse the
 # already rendering lower city fountain footprint, preserving the central park.
 patch_rectangle(cells,70,original,70,(20,46,3,3),(41,23),'central fountain uses existing Averon lower-fountain art',edits)
 patch_rectangle(cells,70,original,70,(4,0,12,5),(35,0),'existing tree screen closes unbuilt northern road',edits)
 patch_rectangle(cells,70,original,70,(0,0,4,9),(0,16),'existing tree screen closes unbuilt western road',edits)
 header=json.loads((staged/'JubilifeCity/map.json').read_text())
 # Never accidentally reopen discarded external edges or non-integrated doors.
 for warp in header['warp_events']:
  i=warp['y']*70+warp['x']
  if (cells[i]>>10)&3!=warp['source_collision']:raise ValueError('active door collision/anchor changed')
 # Original closed source doors and all newly introduced landmark door tiles stay
 # closed; only three explicitly active neutral interior anchors may transition.
 active={(w['x'],w['y']) for w in header['warp_events']}
 banks=[a.read_target(engine,f) for f in ('primary/general','secondary/rustboro')]
 names=re.findall(r'^\s*(MB_\w+)\s*[,=]',(engine/'include/constants/metatile_behaviors.h').read_text(),re.M)
 for i,c in enumerate(cells):
  bank,mid=divmod(c&1023,512)
  if (mid+1)*16>len(banks[bank][0]):raise ValueError('unresolved target metatile')
  behavior=struct.unpack_from('<H',banks[bank][1],mid*2)[0]&255
  # Existing animated/nonanimated door behaviors, identified from current enums.
  if 'DOOR' in names[behavior] and (i%70,i//70) not in active:
   new=(c&~0xC00)|0x400
   if c!=new:edits.append({'x':i%70,'y':i//70,'before':c,'after':new,'reason':'closed neutral/unbuilt door'});cells[i]=new
 # City north/west remain closed until their actual areas exist.
 for x,y in [(x,0) for x in range(70)]+[(0,y) for y in range(64)]:
  i=y*70+x;new=(cells[i]&~0xC00)|0x400
  if cells[i]!=new:edits.append({'x':x,'y':y,'before':cells[i],'after':new,'reason':'preserve unbuilt boundary closure'});cells[i]=new
 final=struct.pack('<4480H',*cells);pals={i:banks[0 if i<6 else 1][3][i] for i in range(16)}
 preview=a.b.dual.render(final,[b[0] for b in banks],[b[2] for b in banks],pals,70,64)
 output.mkdir(parents=True);(output/'map.bin').write_bytes(final);preview.save(output/'averon-city-art-draft.png')
 report={'status':'PROVISIONAL_AVERON_ART_DRAFT_NOT_INTEGRATED_OR_GAMEPLAY_ACCEPTED','dimensions':[70,64],
 'input_sha256':a.b.digest(raw),'output_sha256':a.b.digest(final),'edits':edits,'active_doors':header['warp_events'],
 'assets':'existing Averon General/Rustboro; no donor graphics',
 'limitations':['not yet source-behavior/layer verified outside adapted regions','landmark silhouettes differ from donor: reused neutral existing facades',
 'source city source road/park/residential layout retained outside recorded changes','Route202/203 streamed seams not yet accepted','door animation and follower/SaveContinue not tested']}
 a.b.dump(output/'receipt.json',report);return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('engine','staged','output'):p.add_argument('--'+n,required=True)
 v=p.parse_args();print(json.dumps(build(v.engine,v.staged,v.output),indent=2))
