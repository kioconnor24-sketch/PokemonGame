#!/usr/bin/env python3
"""Pack map-local semantic adaptations using only existing Averon graphic records.

General is NEVER changed. Extra secondary records duplicate existing Averon tile
words with explicit donor behavior/layer attributes for unchanged donor terrain.
This authors the two corridor candidates; it is not a generic donor converter.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('city_art',HERE/'build_city_art_draft.py');city=importlib.util.module_from_spec(s);s.loader.exec_module(city)
a=city.a

def pack(engine,donor,staged,city_art,output):
 engine,donor,staged,city_art,output=map(Path,(engine,donor,staged,city_art,output))
 if output.exists() or 'engine' in output.resolve().parts:raise ValueError('new off-engine output required')
 revision=json.loads((HERE/'corridor-spec.json').read_text())['donor_revision']
 if a.b.static.git(donor,'rev-parse','HEAD').decode().strip()!=revision:raise ValueError('wrong pinned donor')
 banks=[a.read_target(engine,f) for f in ('primary/general','secondary/rustboro')]
 original_secondary=banks[1][0];original_attributes=banks[1][1]
 source_attr=[a.b.static.verified_file(donor,'data/tilesets/'+f+'/metatile_attributes.bin',revision) for f in ('primary/general','secondary/rustboro')]
 altered={(v['x'],v['y']) for v in json.loads((city_art/'receipt.json').read_text())['edits']}
 raw_inputs={'JubilifeCity':(city_art/'map.bin').read_bytes(),'Route203':(staged/'Route203/map.bin').read_bytes()}
 plans={};needed=set()
 for name,raw in raw_inputs.items():
  width=70 if name=='JubilifeCity' else 64
  before=struct.unpack('<'+str(len(raw)//2)+'H',raw)
  source=struct.unpack('<'+str(len(raw)//2)+'H',(staged/name/'source.bin').read_bytes())
  changes=[]
  for i,(cell,src) in enumerate(zip(before,source)):
   if name=='JubilifeCity' and (i%width,i//width) in altered:continue
   sb,sm=divmod(src&1023,512);tb,tm=divmod(cell&1023,512)
   desired=struct.unpack_from('<H',source_attr[sb],sm*2)[0]
   actual=struct.unpack_from('<H',banks[tb][1],tm*2)[0]
   if actual!=desired:
    key=(cell&1023,desired);needed.add(key);changes.append((i,key))
  plans[name]=(before,changes)
 count=len(original_secondary)//16
 if count+len(needed)>512:raise ValueError('secondary bank capacity exceeded')
 allocation={key:512+count+n for n,key in enumerate(sorted(needed))}
 records=bytearray(original_secondary);attrs=bytearray(original_attributes)
 for base,desired in sorted(needed):
  bank,mid=divmod(base,512);records.extend(banks[bank][0][mid*16:(mid+1)*16]);attrs.extend(struct.pack('<H',desired))
 output.mkdir(parents=True);(output/'metatiles.bin').write_bytes(records);(output/'metatile_attributes.bin').write_bytes(attrs)
 receipt={'status':'PROVISIONAL_CORRIDOR_CANDIDATES_NOT_INTEGRATED_OR_PLAYTESTED','donor_revision':revision,
 'primary':'existing gTileset_General unchanged','secondary':'gTileset_AveronCorridorRustboro',
 'existing_secondary_records':count,'appended_records':len(needed),'final_secondary_records':count+len(needed),
 'allocation':[{'base_existing_id':k[0],'attribute_u16':k[1],'target_id':v} for k,v in sorted(allocation.items())],
 'metatiles_sha256':a.b.digest(bytes(records)),'attributes_sha256':a.b.digest(bytes(attrs)),
 'maps':{},'limits':['original Averon style adaptation; source art equality not claimed','sideways stairs behavior retained but in-game appearance/traversal pending','new bank-local metatile IDs are not saved location IDs','full runtime/map/SaveContinue acceptance pending']}
 custom=[banks[0],(bytes(records),bytes(attrs),banks[1][2],banks[1][3])]
 pals={i:custom[0 if i<6 else 1][3][i] for i in range(16)}
 for name,(before,changes) in plans.items():
  cells=list(before)
  for i,key in changes:cells[i]=(cells[i]&0xFC00)|allocation[key]
  if any((x&0xFC00)!=(y&0xFC00) for x,y in zip(before,cells)):raise ValueError('collision/elevation changed during semantic packing')
  raw=struct.pack('<'+str(len(cells))+'H',*cells);p=output/name;p.mkdir();(p/'map.bin').write_bytes(raw)
  w,h=(70,64) if name=='JubilifeCity' else (64,30)
  a.b.dual.render(raw,[b[0] for b in custom],[b[2] for b in custom],pals,w,h).save(p/'averon-render.png')
  receipt['maps'][name]={'dimensions':[w,h],'input_sha256':a.b.digest(raw_inputs[name]),'output_sha256':a.b.digest(raw),'semantic_cells_reassigned':len(changes),'upper_six_bits_preserved':True}
 # Route202 sees exactly this last-seven-row strip via FillNorthConnection.
 city_cells=struct.unpack('<4480H',(output/'JubilifeCity/map.bin').read_bytes())
 strip=city_cells[57*70:64*70]
 if any((v&1023)>=512 for v in strip):raise ValueError('Route202-facing strip requires incompatible secondary bank')
 receipt['route202_seam_primary_bank_only']={'rows':[57,63],'cells':len(strip),'all_primary':True,'scope':'bank compatibility only; actual offsets/collision traversal still require integrated Route202 checks'}
 a.b.dump(output/'receipt.json',receipt)
 definition='''#include "global.h"
#include "tileset_anims.h"
extern const u32 gTilesetTiles_Rustboro[];
extern const u16 gTilesetPalettes_Rustboro[][16];
const u16 gMetatiles_AveronCorridorRustboro[] = INCBIN_U16("data/tilesets/secondary/averon_corridor_rustboro/metatiles.bin");
const u16 gMetatileAttributes_AveronCorridorRustboro[] = INCBIN_U16("data/tilesets/secondary/averon_corridor_rustboro/metatile_attributes.bin");
const struct Tileset gTileset_AveronCorridorRustboro = {
 .isCompressed=TRUE, .isSecondary=TRUE,
 .tiles=gTilesetTiles_Rustboro, .palettes=gTilesetPalettes_Rustboro,
 .metatiles=gMetatiles_AveronCorridorRustboro,
 .metatileAttributes=gMetatileAttributes_AveronCorridorRustboro,
 .callback=InitTilesetAnim_Rustboro,
};
'''
 (output/'tileset.c').write_text(definition)
 return receipt

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('engine','donor','staged','city-art','output'):p.add_argument('--'+n,required=True)
 v=p.parse_args();print(json.dumps(pack(v.engine,v.donor,v.staged,v.city_art,v.output),indent=2))
