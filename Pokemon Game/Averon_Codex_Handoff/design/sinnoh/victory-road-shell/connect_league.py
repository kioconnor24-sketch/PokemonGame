#!/usr/bin/env python3
"""Couple existing League cave doors to original core floors, off-engine only."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

COAST='3e00eab223722dda747f2ac3f748682a33c47026'
CORE='064433efeb35a7e171149e3a1f950c76ccf24a84'
PREFIX='Pokemon Game/Averon_Codex_Handoff/design/sinnoh/'
NAMES=('PokmonLeague','SinnohVictoryRoad_1F','SinnohVictoryRoad_2F','SinnohVictoryRoad_B1F')
PORTS=((21,58,15,78,7),(23,41,34,5,8))
encode=lambda value:(json.dumps(value,indent=2)+'\n').encode()


def read_packet(repo):
    files={}
    for name in NAMES:
        coast=name=='PokmonLeague';rev=COAST if coast else CORE
        folder=PREFIX+('sunyshore-coast' if coast else 'victory-road-shell')+'/staged/'+name+'/'
        for suffix in ('map.bin','border.bin','map.json','attributes.json','averon.png'):
            filename='averon-map.bin' if coast and suffix=='map.bin' else 'averon-border.bin' if coast and suffix=='border.bin' else suffix
            files[name+'/'+suffix]=subprocess.check_output(['git','-C',str(repo),'show',rev+':'+folder+filename],stderr=subprocess.PIPE)
    for bank in ('primary','secondary'):
        path=PREFIX+'sunyshore-coast/outdoor-family/'+bank+'-attributes.bin'
        files['league-'+bank+'-attributes.bin']=subprocess.check_output(['git','-C',str(repo),'show',COAST+':'+path],stderr=subprocess.PIPE)
    return files


def couple(files,cave_attrs,general_attrs):
    result=dict(files);first='SinnohVictoryRoad_1F';league='PokmonLeague'
    outside=json.loads(files[league+'/map.json']);inside=json.loads(files[first+'/map.json'])
    if outside['warp_events'] or len(inside['warp_events'])!=6:raise ValueError('exact unconnected portal baseline required')
    raw=bytearray(files[first+'/map.bin']);sea=files[league+'/map.bin'];changes=[]
    for i,(x,y,ix,iy,ds_index) in enumerate(PORTS):
        v=struct.unpack_from('<H',sea,2*(y*33+x))[0];b,mid=divmod(v&1023,512)
        attrs=files['league-'+('primary' if b==0 else 'secondary')+'-attributes.bin']
        if v&0xC00 or struct.unpack_from('<H',attrs,mid*2)[0]&511!=0x60:raise ValueError('existing League cave behavior/collision differs')
        pos=2*(iy*52+ix);old=struct.unpack_from('<H',raw,pos)[0]
        if old!=(0xC00|521):raise ValueError('original sealed core anchor differs')
        # Existing native Cave record532 is a real nonanimated door. Stand
        # below/facing up on departure; existing floor neighbours stay intact.
        if struct.unpack_from('<H',cave_attrs,20*2)[0]&511!=0x60:raise ValueError('native Cave door behavior differs')
        new=532;struct.pack_into('<H',raw,pos,new)
        outside['warp_events'].append(dict(x=x,y=y,elevation=0,dest_map=inside['id'],dest_warp_id=str(6+i)))
        inside['warp_events'].append(dict(x=ix,y=iy,elevation=0,dest_map=outside['id'],dest_warp_id=str(i)))
        changes.append(dict(core_tile=[ix,iy],before=old,after=new,league_tile=[x,y],ds_1f_canonical_index=ds_index,core_index=6+i,league_index=i))
    result[first+'/map.bin']=bytes(raw);result[first+'/map.json']=encode(inside);result[league+'/map.json']=encode(outside)
    for name in (first,league):
        attrs=(general_attrs,cave_attrs) if name==first else (files['league-primary-attributes.bin'],files['league-secondary-attributes.bin'])
        used={v[0]&1023 for v in struct.iter_unpack('<H',result[name+'/map.bin']+result[name+'/border.bin'])}
        words={str(mid):struct.unpack_from('<H',attrs[mid//512],(mid%512)*2)[0] for mid in sorted(used)}
        result[name+'/attributes.json']=encode(dict(used_source_attribute_words=words,source_tilesets=['gTileset_General','gTileset_Cave' if name==first else 'gTileset_SunyshoreDevOutdoorSecondary']))
    return {k:v for k,v in result.items() if not k.startswith('league-')},changes


def build(repo,engine,out):
    repo,engine,out=Path(repo).resolve(),Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    sp=importlib.util.spec_from_file_location('connected_existing_renderer',repo/(PREFIX+'victory-road-shell/build_shell.py'))
    a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
    inputs=read_packet(repo);assets={}
    def read(path):
        raw=a.base.verified_file(repo,engine.relative_to(repo)/path,'HEAD');assets[path]=a.sha(raw);return raw
    paths=['data/tilesets/primary/general/','data/tilesets/secondary/cave/']
    banks=[read(p+'metatiles.bin') for p in paths];attrs=[read(p+'metatile_attributes.bin') for p in paths]
    result,changes=couple(inputs,attrs[1],attrs[0]);images=[a.dual.indexed(read(p+'tiles.png')) for p in paths]
    name='SinnohVictoryRoad_1F';raw=result[name+'/map.bin'];deps=a.dual.closure(raw,banks,images)
    pals={i:a.base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
    preview=a.dual.render(raw,banks,images,pals,52,84)
    import io
    stream=io.BytesIO();preview.save(stream,format='PNG');result[name+'/averon.png']=stream.getvalue()
    out.mkdir(parents=True)
    for p,data in result.items():
        target=out/'connected'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    receipt=dict(status='SOURCE_COUPLING_ONLY_NOT_ROM_OR_NATURAL_TRAVEL_ACCEPTANCE',coast_revision=COAST,core_revision=CORE,
        input_sha256={p:a.sha(v) for p,v in inputs.items()},existing_averon_sha256=assets,
        core_changes=changes,league_binary_and_border_unchanged=True,original_six_core_stairs_unchanged=True,
        full_fields_preserved_except_two_original_sealed_core_doors=True,
        output_sha256={p:a.sha(v) for p,v in result.items()},
        limits=['Existing League cave anchors are source facts21,58 and23,41, not guessed coordinates',
                'Canonical DS pairs League2/3 to1F7/8 become two explicit GBA paired doors; wider DS warp aliases not copied',
                'Source coast terrain/elevation/behaviors/art unchanged; only two original authored core door cells open',
                'League Route223 metadata still requires the existing coast batch in a combined DEV/production registry',
                'No natural Surf/Waterfall arrival, side rooms, story, saved IDs, ROM/native/mGBA or production acceptance'])
    (out/'connected-receipt.json').write_bytes(encode(receipt));return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('repo','engine','out'):p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.repo,a.engine,a.out)['core_changes'],indent=2))
