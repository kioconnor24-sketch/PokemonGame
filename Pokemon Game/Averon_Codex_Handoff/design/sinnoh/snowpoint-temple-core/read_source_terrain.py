#!/usr/bin/env python3
"""Read pinned Temple permission metadata; never import models or assume full collision.

The DS also uses BDHC/model geometry. Collision-bit/ice extraction is SOURCE
EVIDENCE ONLY, not a complete walkability map or ice-puzzle implementation.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

BEHAVIORS={0:'NONE',8:'CAVE_FLOOR',0x20:'ICE',0x5e:'WARP_STAIRS_EAST',0x5f:'WARP_STAIRS_WEST',0x65:'WARP_ENTRANCE_SOUTH',0x6f:'WARP_SOUTH'}

def decode(raw):
    if len(raw)<16:raise ValueError('truncated section header')
    terrain,props,model,bdhc=struct.unpack_from('<4I',raw)
    if terrain!=2048:raise ValueError('expected32x32 little-endian terrain words')
    if 16+terrain+props+model+bdhc!=len(raw):raise ValueError('section lengths/trailing bytes differ')
    if not model or not bdhc:raise ValueError('required opaque model/BDHC section absent')
    data=raw[16:16+terrain];words=struct.unpack('<1024H',data)
    if any(w&0x7f00 for w in words):raise ValueError('unsupported terrain flag bits')
    if any((w&255) not in BEHAVIORS for w in words):raise ValueError('unreviewed Temple behavior')
    counts=Counter(w&255 for w in words)
    return words,dict(scope='SOURCE_METADATA_NOT_FULL_BDHC_COLLISION_OR_GAMEPLAY',dimensions=[32,32],
        terrain_sha256=hashlib.sha256(data).hexdigest(),terrain_words=1024,
        collision_bit_tiles=sum(bool(w&0x8000) for w in words),
        ice_coordinates=[[i%32,i//32] for i,w in enumerate(words) if w&255==0x20],
        behaviors={BEHAVIORS[k]:v for k,v in sorted(counts.items())},
        opaque_section_bytes=dict(props=props,model=model,bdhc=bdhc),
        models_or_textures_emitted=False,full_walkability_accepted=False)

def audit(inputs,manifest):
    inputs=Path(inputs).resolve();floors={}
    for floor,identity in manifest['floors'].items():
        relative=Path(identity['private_input_name']);p=(inputs/relative).resolve()
        if relative.is_absolute() or not p.is_relative_to(inputs):raise ValueError('input path escapes root')
        raw=p.read_bytes()
        if len(raw)!=identity['bytes'] or hashlib.sha256(raw).hexdigest()!=identity['sha256']:
            raise ValueError('source data identity differs: '+floor)
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob!=identity['git_blob']:raise ValueError('source Git blob differs: '+floor)
        _,d=decode(raw);d['source_identity']=identity;floors[floor]=d
    return dict(status='PINNED_SOURCE_TERRAIN_AUDIT_ONLY_NOT_CONVERTED_MAPS',revision=manifest['revision'],
                total_terrain_words=sum(d['terrain_words'] for d in floors.values()),
                total_ice_tiles=sum(len(d['ice_coordinates']) for d in floors.values()),floors=floors,
                limitations=['DS BDHC/model collision and height remain unparsed; do not treat outside zero-valued tiles as safe floor',
                             'No native map, ice route, story, encounter, ID, graphics or gameplay acceptance emitted',
                             'Current neutral-core test ROM is unchanged; these facts belong to a later geometry pass'])

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--inputs',required=True,type=Path)
    p.add_argument('--manifest',type=Path,default=Path(__file__).with_name('terrain-source-identities.json'))
    args=p.parse_args();print(json.dumps(audit(args.inputs,json.loads(args.manifest.read_text())),indent=2))
