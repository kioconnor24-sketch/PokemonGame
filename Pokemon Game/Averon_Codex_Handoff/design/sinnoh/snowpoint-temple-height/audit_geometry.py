#!/usr/bin/env python3
"""Audit pinned private Temple height surfaces; emit metadata, never model assets."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
from parse_bdhc import decode, candidates, tile_candidates, FX, TILE

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'snowpoint-temple-core'
s=importlib.util.spec_from_file_location('temple_permission_source',SOURCE/'read_source_terrain.py')
terrain=importlib.util.module_from_spec(s);s.loader.exec_module(terrain)


def audit(inputs,manifest):
    # Independently validate whole-file SHA256/Git blob/section/permission pins.
    verified=terrain.audit(inputs,manifest);floors={};root=Path(inputs).resolve()
    for floor,pin in manifest['floors'].items():
        raw=(root/pin['private_input_name']).read_bytes()
        sizes=struct.unpack_from('<4I',raw);offset=16+sum(sizes[:3])
        section=raw[offset:];data=decode(section)
        words,_=terrain.decode(raw)
        covered=[];outside_clear=[];ambiguous=[];ramps=[];ice=[];heights=Counter();walkable=[];corner_missing=[];corner_nonflat=[];corner_count=0
        for i,word in enumerate(words):
            x,y=i%32,i//32;values=tile_candidates(data,x,y)
            if values:
                covered.append([x,y])
                if not word&0x8000:
                    walkable.append(dict(tile=[x,y],source_behavior=word&255,height_candidates=[str(h/FX) for _,h in values]))
                    for dx,dz in ((-8,-8),(-8,8),(8,-8),(8,8)):
                        edge=candidates(data,(x-16)*TILE+TILE//2+dx*FX,(y-16)*TILE+TILE//2+dz*FX)
                        corner_count+=1
                        if not any(h==16*FX for _,h in edge):corner_missing.append([x,y,dx,dz])
                        if any(h!=16*FX for _,h in edge):
                            corner_nonflat.append(dict(tile=[x,y],offset=[dx,dz],height_candidates=[str(h/FX) for _,h in edge]))
                for _,height in values:heights[str(height/FX)]+=1
                if len(values)>1:ambiguous.append([x,y])
                if any(data['normals'][data['plates'][plate][2]]!=(0,FX,0) for plate,_ in values):ramps.append([x,y])
            elif not word&0x8000:outside_clear.append([x,y])
            if word&255==32:
                ice.append(dict(tile=[x,y],collision_bit=bool(word&0x8000),height_candidates=[str(h/FX) for _,h in values]))
        floors[floor]=dict(source_identity=pin,bdhc_sha256=hashlib.sha256(section).hexdigest(),
            table_counts={k:len(v) for k,v in data.items()},surface_center_tiles=len(covered),walkable_center_samples=walkable,
            permission_clear_without_surface=outside_clear,multiple_height_tiles=ambiguous,
            sampled_walkable_corners=corner_count,corners_without_flat16=corner_missing,nonflat_edge_candidates=corner_nonflat,
            ramp_center_tiles=ramps,height_histogram=dict(heights),ice=ice,
            full_collision_or_puzzle_accepted=False)
    return dict(status='SOURCE_HEIGHT_SURFACES_ONLY_NOT_CONVERTED_OR_RUNTIME_ACCEPTED',revision=verified['revision'],
        total_terrain_words=verified['total_terrain_words'],total_ice_tiles=verified['total_ice_tiles'],floors=floors,
        limitations=['Rational center-plane samples are not DS fixed-point runtime parity or movement proof',
                    'Permission-clear cells without BDHC surface must not be converted into safe floor',
                    'Multiple/ramped heights, tile-edge transitions, dynamic terrain and model obstacles need separate verification',
                    'No canonical map, ice solution, source model/texture/props, saved IDs or production edits emitted'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',required=True,type=Path)
    p.add_argument('--manifest',type=Path,default=SOURCE/'terrain-source-identities.json')
    a=p.parse_args();print(json.dumps(audit(a.inputs,json.loads(a.manifest.read_text())),indent=2))
