#!/usr/bin/env python3
"""Bound an immutable already-converted coast cluster with the merged sanitizer.

No donor conversion, new geography, graphics authoring or production install.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
SOURCE_REV='e3663c8b86999f23442d366eb2379e22291d7332'
GATE_REV='9d21973f94a5ffe6e4d77fad4a4ba69d682f76f4'
SOURCE='Pokemon Game/Averon_Codex_Handoff/design/sinnoh/remaining-donor/'
MAPS={'SunyshoreCity':(70,64),'Route222':(92,32),'Route223':(34,124),'PokmonLeague':(33,69),'Route222_Access':(13,9)}
spec=importlib.util.spec_from_file_location('coast_existing_sanitizer',HERE.parent/'eterna-cycle/stage_batch.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
encode=lambda doc:(json.dumps(doc,indent=2)+'\n').encode()


def git_read(repo,revision,path):
    return subprocess.check_output(['git','-C',str(repo),'show',revision+':'+path],stderr=subprocess.PIPE)


def source_paths():
    return [SOURCE+'staged/'+name+'/'+file for name in MAPS for file in ('map.bin','border.bin','map.json','attributes.json')]


def bound(files,pins):
    if set(files)!=set(source_paths()) or set(files)!=set(pins):
        raise ValueError('exact five-map source file set required')
    if any(sha(raw)!=pins[path] for path,raw in files.items()):
        raise ValueError('immutable source-stage hash changed')
    headers={};layouts={};raws={};borders={};attrs={}
    for name,(w,h) in MAPS.items():
        def read(file):return files[SOURCE+'staged/'+name+'/'+file]
        headers[name]=json.loads(read('map.json'));raws[name]=read('map.bin');borders[name]=read('border.bin');attrs[name]=json.loads(read('attributes.json'))
        if len(raws[name])!=w*h*2 or len(borders[name])!=8 or (w+15)*(h+14)>10240:
            raise ValueError('source dimensions/buffer invalid')
        if headers[name]['region_map_section']!='MAPSEC_PENDING_OWNER' or any(headers[name][k] for k in ('object_events','coord_events','bg_events')):
            raise ValueError('neutral source stage required')
        layouts[name]=dict(width=w,height=h)
    staged,closures,translations=base.sanitize(headers,layouts,raws)
    if staged['Route222_Access'][0]!=raws['Route222_Access'] or staged['Route222_Access'][1]!=headers['Route222_Access']:
        raise ValueError('reuse gate geometry/headers must stay unchanged')
    receipt=dict(status='BOUNDED_IMMUTABLE_SOURCE_ONLY_NOT_RUNTIME_OR_PRODUCTION',source_parent=SOURCE_REV,
        donor_revision=base.REVISION,source_sha256=pins,original_headers=headers,warp_index_translation=translations,
        closure_changes=closures,maps={name:dict(dimensions=MAPS[name],source_sha256=sha(raws[name]),
            staged_sha256=sha(staged[name][0]),border_sha256=sha(borders[name]),
            elevation15_cells=sum(v[0]>>12==15 for v in struct.iter_unpack('<H',raws[name])),
            connections=staged[name][1]['connections'],warp_count=len(staged[name][1]['warp_events'])) for name in MAPS},
        limits=['Reuses already converted source, never donor reconversion or production registry',
                'Route224 and all external entries remain closed; sea/Surf/final visuals unaccepted',
                'Literal PokmonLeague and all original source/save identities remain unchanged'])
    return staged,borders,attrs,receipt


def build(repo,out):
    repo,out=Path(repo).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(repo/'Pokemon Game/engine') or 'engine' in out.parts:
        raise ValueError('new off-engine output required')
    pins=json.loads((HERE/'source-input-hashes.json').read_text())
    files={path:git_read(repo,SOURCE_REV,path) for path in source_paths()}
    staged,borders,attrs,receipt=bound(files,pins)
    # Reuse the already tested #238 gate; do not regenerate stock art.
    gate_files={}
    for name in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin'):
        path=SOURCE+'interior-art/'+name;gate_files['gate-art/'+name]=git_read(repo,GATE_REV,path)
    for name in ('averon-map.bin','averon.png'):
        path=SOURCE+'staged/Route222_Access/'+name;gate_files['staged/Route222_Access/'+name]=git_read(repo,GATE_REV,path)
    old_gate=git_read(repo,GATE_REV,SOURCE+'staged/Route222_Access/map.bin')
    if old_gate!=staged['Route222_Access'][0]:raise ValueError('gate art source differs from bounded gate')
    out.mkdir(parents=True)
    for name,(raw,header) in staged.items():
        folder=out/'staged'/name;folder.mkdir(parents=True)
        (folder/'map.bin').write_bytes(raw);(folder/'border.bin').write_bytes(borders[name]);(folder/'map.json').write_bytes(encode(header));(folder/'attributes.json').write_bytes(encode(attrs[name]))
        base.schematic(raw,*MAPS[name]).save(folder/'collision.png')
    for path,raw in gate_files.items():
        target=out/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    (out/'source-receipt.json').write_bytes(encode(receipt))
    (out/'gate-art-reuse.json').write_bytes(encode(dict(source_revision=GATE_REV,
        source_receipt_path=SOURCE+'interior-art/gate-art-receipt.json',
        source_receipt_sha256=sha(git_read(repo,GATE_REV,SOURCE+'interior-art/gate-art-receipt.json')),
        copied_sha256={path:sha(raw) for path,raw in gate_files.items()},status='EXACT_REUSE_NOT_NEW_ART_OR_RUNTIME_ACCEPTANCE')))
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();r=build(a.repo,a.out);print(json.dumps({n:len(c) for n,c in r['closure_changes'].items()},indent=2))
