#!/usr/bin/env python3
"""Assemble accepted source data into a strictly disposable Oreburgh test ROM.

No production IDs or art are created. Pinned git blobs are copied, not rebuilt.
Only a marked codex/oreburgh-runtime-scratch-* checkout can receive the overlay.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import zipfile
import io

HERE = Path(__file__).resolve().parent
BASE = 'f0a8bcaa10b410245d240b6014779ba69eb31c74'
ART = '0005ba56711ba5c73e4d1b31402b62b1a7863800'
SOURCE = 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/oreburgh-donor/'
ENGINE = 'Pokemon Game/engine/'
BASE_CACHE_SHA256 = '79c53813a74f979875e1f9c5e4a163659001e5fc0f14cbabad94eccd8fbf121a'
ART_CACHE_SHA256 = '73ed064f3570c31a1eb6cf09bddf474e20fe547d9de972bf004fe071e9b42409'
MAPS = {'OreburghCity': (70,59), 'Route207': (64,32),
        'OreburghMine_B1F': (24,26), 'OreburghMine_B2F': (32,28)}
IDS = dict(zip(MAPS, ('MAP_OREBURGH_CITY','MAP_ROUTE207','MAP_OREBURGH_MINE_B1F','MAP_OREBURGH_MINE_B2F')))


def git(repo, *args):
    return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.PIPE)


def blob(repo, revision, path):
    if revision==ART:
        data=(HERE/'city-art-inputs.zip').read_bytes()
        if sha(data)!=ART_CACHE_SHA256:raise ValueError('pinned art cache changed')
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            return archive.read(path.removeprefix(SOURCE+'city-family/'))
    # Shallow read-only CI need not fetch unmerged sibling PRs or historical commits.
    # Existing tracked base files may substitute only if every byte matches its pin.
    pins=json.loads((HERE/'base-input-hashes.json').read_text())
    if revision==BASE and path in pins:
        local=Path(repo)/path
        if local.is_file() and sha(local.read_bytes())==pins[path]:return local.read_bytes()
        cache=(HERE/'base-inputs.zip').read_bytes()
        if sha(cache)!=BASE_CACHE_SHA256:raise ValueError('pinned base cache changed')
        with zipfile.ZipFile(io.BytesIO(cache)) as archive:
            data=archive.read(path)
        if sha(data)!=pins[path]:raise ValueError('base input does not match its pin')
        return data
    return git(repo,'show',revision+':'+path)


def encode(data):
    return (json.dumps(data,indent=2)+'\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def open_gate(raw):
    """Restore only four source-pinned east doorway cells, not its closed ladder."""
    if len(raw)!=29*27*2: raise ValueError('Gate dimensions changed')
    changes=((25,20,0x3201,0x3207),(24,21,0x609,0x658),
             (25,21,0x609,0x659),(26,21,0x609,0x65A))
    result=bytearray(raw)
    for x,y,old,new in changes:
        offset=(y*29+x)*2
        if struct.unpack_from('<H',raw,offset)[0]!=old:
            raise ValueError('Gate closed east source changed')
        struct.pack_into('<H',result,offset,new)
    return bytes(result)


def close_unmatched_seam(raw):
    # Source Route207 (13,31) faces solid City (48,0); retain the other six spans.
    if len(raw)!=64*32*2 or struct.unpack_from('<H',raw,(31*64+13)*2)[0]!=0x310C:
        raise ValueError('Route207 unmatched edge precondition changed')
    out=bytearray(raw);struct.pack_into('<H',out,(31*64+13)*2,0x350C)
    return bytes(out)


def validate_links(headers, gate):
    """Whole-cluster validation including sparse City indices and all mine events."""
    city,route,b1,b2=(headers[n] for n in MAPS)
    if city['connections']!=[dict(map=IDS['Route207'],offset=35,direction='up')] or route['connections']!=[dict(map=IDS['OreburghCity'],offset=-35,direction='down')]:
        raise ValueError('City/Route207 reciprocal offset changed')
    maps={h['id']:h for h in [*headers.values(),gate]}
    for h in maps.values():
        if any(h.get(k) for k in ('object_events','coord_events','bg_events')):
            raise ValueError('unexpected gameplay events')
        for w in h['warp_events']:
            if w['dest_map'] not in maps:
                if h['id']==gate['id'] and w==gate['warp_events'][0] and w['dest_map']=='MAP_ROUTE203': continue
                raise ValueError('unbuilt or foreign warp destination')
            if not 0<=int(w['dest_warp_id'])<len(maps[w['dest_map']]['warp_events']):
                raise ValueError('destination warp outside event array')
    shape=lambda events:[(w['x'],w['y'],w['elevation'],w['dest_map'],str(w['dest_warp_id'])) for w in events]
    if shape(city['warp_events'])!=[(6,12,0,gate['id'],'1'),(50,57,0,b1['id'],'0'),(51,57,0,b1['id'],'0'),(52,57,0,b1['id'],'1'),(53,57,0,b1['id'],'1')]:
        raise ValueError('City source anchors/compact mine returns changed')
    if shape(b1['warp_events'])!=[(11,1,0,city['id'],'1'),(12,1,0,city['id'],'4'),(11,21,0,b2['id'],'0'),(12,21,0,b2['id'],'0'),(10,21,0,b2['id'],'0'),(13,21,0,b2['id'],'0')]:
        raise ValueError('all six individual B1 events must survive')
    if shape(b2['warp_events'])!=[(15,1,0,b1['id'],'2')]:raise ValueError('B2 canonical return changed')
    if len(gate['warp_events'])!=2 or shape(gate['warp_events'])[1]!=(25,20,0,city['id'],'0'):
        raise ValueError('Gate reciprocal east return changed')
    if route['warp_events']:raise ValueError('Coronet must stay closed')


def assemble(repo):
    """Pure overlay plan: all reads and validation precede scratch-engine writes."""
    repo=Path(repo).resolve()
    read=lambda p:blob(repo,BASE,ENGINE+p)
    source=lambda p:blob(repo,BASE,SOURCE+p)
    prior=lambda p:blob(repo,ART,SOURCE+'city-family/'+p)
    groups=json.loads(read('data/maps/map_groups.json'))
    layouts=json.loads(read('data/layouts/layouts.json'))
    names=groups['gMapGroup_Sinnoh'];old_names=list(names)
    if not {'Route203','OreburghGate_1F'}<=set(names) or set(MAPS)&set(names):
        raise ValueError('base corridor absent or target already registered')
    plan=json.loads(prior('warp-plan.json'))
    headers={}
    for name in MAPS:
        if name.startswith('OreburghMine'):
            h=json.loads(source('staged/'+name+'/map.json'))
        else:
            h=dict(id=IDS[name],name=name,layout='LAYOUT_'+('OREBURGH_CITY' if name=='OreburghCity' else 'ROUTE207'),
                   music='MUS_RUSTBORO' if name=='OreburghCity' else 'MUS_ROUTE110',region='REGION_SINNOH',
                   region_map_section='MAPSEC_PENDING_OWNER',weather='WEATHER_SUNNY',map_type='MAP_TYPE_TOWN' if name=='OreburghCity' else 'MAP_TYPE_ROUTE',
                   requires_flash=False,allow_cycling=True,allow_escaping=False,allow_running=True,show_map_name=True,
                   battle_scene='MAP_BATTLE_SCENE_NORMAL',connections=json.loads(source('corridor/'+name+'/map.json'))['source_connection_events'],
                   object_events=[],warp_events=[],coord_events=[],bg_events=[])
        h['warp_events']=copy.deepcopy(plan['events'].get(h['id'],[]))
        headers[name]=h
    gate=json.loads(read('data/maps/OreburghGate_1F/map.json'))
    original_gate=copy.deepcopy(gate)
    if len(gate['warp_events'])!=1:raise ValueError('Gate source event array changed')
    gate['warp_events'].append(copy.deepcopy(plan['events'][gate['id']][1]))
    songs=read('include/constants/songs.h').decode()
    for h in headers.values():
        if not re.search(r'^#define\s+'+re.escape(h['music'])+r'\s+',songs,re.M):raise ValueError('undefined existing music symbol')
    validate_links(headers,gate)
    if gate['warp_events'][0]!=original_gate['warp_events'][0]:raise ValueError('west route changed')
    files={'test/averon_oreburgh_candidate.c':(HERE/'native-candidate.c').read_bytes()};bank_symbols={}
    def bank(kind,secondary,graphics,callback,records,attrs):
        path='data/tilesets/'+('secondary/' if secondary else 'primary/')+'oreburgh_candidate_'+kind+'/'
        if len(records)%16 or len(attrs)*8!=len(records) or len(records)>8192:raise ValueError('bank capacity/dimensions')
        files[path+'metatiles.bin']=records;files[path+'metatile_attributes.bin']=attrs
        symbol='OreburghCandidate'+kind.title()
        bank_symbols[kind]='gTileset_'+symbol
        return symbol,path,secondary,graphics,callback
    banks=[bank('cityprimary',False,'General','General',prior('banks/primary/metatiles.bin'),prior('banks/primary/metatile_attributes.bin')),
           bank('citysecondary',True,'Rustboro','Rustboro',prior('banks/secondary/metatiles.bin'),prior('banks/secondary/metatile_attributes.bin')),
           bank('mineprimary',False,'General','General',source('banks/primary/metatiles.bin'),source('banks/primary/metatile_attributes.bin')),
           bank('minesecondary',True,'Cave','Cave',source('banks/cave/metatiles.bin'),source('banks/cave/metatile_attributes.bin'))]
    declarations='\n// DEV-only isolated metadata; all pixels/palettes reuse existing Averon assets.\n'
    metatiles='\n';tilesets='\n'
    for symbol,path,secondary,graphics,callback in banks:
        declarations+=f'extern const struct Tileset gTileset_{symbol};\n'
        metatiles+=f'const u16 gMetatiles_{symbol}[] = INCBIN_U16("{path}metatiles.bin");\nconst u16 gMetatileAttributes_{symbol}[] = INCBIN_U16("{path}metatile_attributes.bin");\n'
        tilesets+=f'const struct Tileset gTileset_{symbol} = {{ .isCompressed=TRUE, .isSecondary={"TRUE" if secondary else "FALSE"}, .tiles=gTilesetTiles_{graphics}, .palettes=gTilesetPalettes_{graphics}, .metatiles=gMetatiles_{symbol}, .metatileAttributes = gMetatileAttributes_{symbol}, .callback=InitTilesetAnim_{callback} }};\n'
    for path,extra in [('include/tilesets.h',declarations),('src/data/tilesets/metatiles.h',metatiles),('src/data/tilesets/headers.h',tilesets)]:files[path]=read(path)+extra.encode()
    group=groups['group_order'].index('gMapGroup_Sinnoh');pins=read('test/data/averon_map_registry_slots.inc').decode()
    old=f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, {len(names)}, 1)'
    if pins.count(old)!=1:raise ValueError('registry source golden changed')
    pins=pins.replace(old,f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, {len(names)+len(MAPS)}, 1)')
    includes=[]
    for name,(width,height) in MAPS.items():
        h=copy.deepcopy(headers[name]);h['region_map_section']='MAPSEC_ROUTE_201' # DEV surrogate only, not a new origin.
        data=prior(name+'/map.bin') if not name.startswith('OreburghMine') else source('staged/'+name+'.bin')
        if name=='Route207':data=close_unmatched_seam(data)
        border=source(('staged/' if name.startswith('OreburghMine') else 'corridor/')+name+'/border.bin')
        if len(data)!=width*height*2:raise ValueError('map dimensions changed')
        files['data/layouts/'+name+'/map.bin']=data;files['data/layouts/'+name+'/border.bin']=border
        files['data/maps/'+name+'/map.json']=encode(h)
        files['data/maps/'+name+'/scripts.inc']=(name+'_MapScripts::\n\t.byte 0\n').encode()
        prefix='mine' if name.startswith('OreburghMine') else 'city'
        layouts['layouts'].append(dict(id=h['layout'],name=name+'_Layout',width=width,height=height,
            primary_tileset=bank_symbols[prefix+'primary'],secondary_tileset=bank_symbols[prefix+'secondary'],
            layout_version='emerald',border_filepath='data/layouts/'+name+'/border.bin',blockdata_filepath='data/layouts/'+name+'/map.bin'))
        pins+=f'REGISTRY_SLOT({group}, {len(names)}, {h["id"]}, {name}, 1)\n';names.append(name)
        includes.append(f'\t.include "data/maps/{name}/scripts.inc"')
    files['data/event_scripts.s']=read('data/event_scripts.s')+('\n'+'\n'.join(includes)+'\n').encode()
    files['data/layouts/layouts.json']=encode(layouts);files['data/maps/map_groups.json']=encode(groups)
    files['test/data/averon_map_registry_slots.inc']=pins.encode()
    files['data/maps/OreburghGate_1F/map.json']=encode(gate)
    files['data/layouts/OreburghGate_1F/map.bin']=open_gate(read('data/layouts/OreburghGate_1F/map.bin'))
    return files,dict(status='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE',base=BASE,art_source=ART,
        donor_revision='38228bb574a3557345852b758d5f1a65eb01bb22',maps=MAPS,source_headers=headers,
        existing_map_names_preserved=old_names,group_index=group,dev_surrogate='MAPSEC_ROUTE_201=217; never reuse generated save as production',
        protected_registries_unchanged=True,seam_closure=dict(map='Route207',x=13,y=31,before=0x310C,after=0x350C,reason='source edge faces blocked City48,0'),files={p:sha(v) for p,v in sorted(files.items())})


def install(repo):
    repo=Path(repo).resolve();engine=repo/ENGINE
    branch=git(repo,'branch','--show-current').decode().strip()
    if not branch.startswith('codex/oreburgh-runtime-scratch-') or not (engine/'.map_qa_throwaway').is_file():
        raise ValueError('explicit disposable branch and marker required')
    if git(repo,'rev-parse','HEAD').decode().strip()!=BASE:raise ValueError('scratch must start at exact current pinned base')
    if git(repo,'diff','--name-only','HEAD','--',ENGINE).strip():raise ValueError('refusing dirty tracked engine')
    files,receipt=assemble(repo)
    for path in files:
        f=engine/path
        try:original=blob(repo,BASE,ENGINE+path)
        except subprocess.CalledProcessError:
            if f.exists():raise ValueError('untracked target exists: '+path)
        else:
            if not f.is_file() or f.read_bytes()!=original:raise ValueError('unexpected base file: '+path)
    identities=['src/data/region_map/region_map_sections.json','../scripts/averon-mapsec-pins.json','include/pokemon.h','include/global.h']
    before={p:sha((engine/p).read_bytes()) for p in identities}
    for p,data in files.items():
        f=engine/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(data)
    if before!={p:sha((engine/p).read_bytes()) for p in identities}:raise ValueError('identity/save source changed')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',required=True,type=Path);parser.add_argument('--install',action='store_true')
    args=parser.parse_args();print(json.dumps(install(args.repo) if args.install else assemble(args.repo)[1],indent=2)+'\n')
