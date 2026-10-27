#!/usr/bin/env python3
"""Export/install exact-source Battle/Frontier/Stark DEV overlay; no production edits."""
import argparse,copy,importlib.util,json,re,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
ENGINE='Pokemon Game/engine'
BASE='a2698ddf9707140ffd0607646acabeb77bceae7c'   # west packet B's gated head (30 production slots)
ENGINE_TREE='648e92d5a4e69591c81754a5940701336abf4fb6'
PRIOR_SLOTS=41
s=importlib.util.spec_from_file_location('battle_dev_guarded_reuse',HERE.parent/'sunyshore-coast/prepare_runtime.py')
reuse=importlib.util.module_from_spec(s);s.loader.exec_module(reuse)
base=reuse.base
encode=lambda x:(json.dumps(x,indent=2)+chr(10)).encode()
FAMILIES={
 'Battle':('battle-zone-north/outdoor-family','Rustboro'),
 'Fight':('frontier-gate-link/families/FightArea','Rustboro'),
 'Campus':('frontier-gate-link/families/Campus','Rustboro'),
 'Gate':('frontier-gate-link/families/Gate','Cave'),
 'StarkApproach':('stark-approach/cave-family','Cave'),
 'StarkCave':('stark-mountain/cave-family','Cave')}
def inputs(repo):
    # Keep this packet's accepted production pin independent of the older coast scene.
    pins=json.loads((HERE/'runtime-base-input-hashes-main41.json').read_text())   # main22/main30 pins retained as evidence
    data={p:base.verified_file(Path(repo),Path(ENGINE)/p,'HEAD') for p in pins}
    if any(base.sha(data[p])!=h for p,h in pins.items()):raise ValueError('current baseline inputs differ')
    return data
def assemble(repo):
    repo=Path(repo).resolve();engine=repo/ENGINE
    if base.git(repo,'rev-parse','HEAD:'+ENGINE).decode().strip()!=ENGINE_TREE:raise ValueError('exact engine tree required')
    before=inputs(repo);source_pins={};native_inputs={}
    def read(path):
        raw=base.verified_file(ROOT,path.relative_to(ROOT),'HEAD');source_pins[str(path.relative_to(ROOT))]=base.sha(raw);return raw
    def eng(path):
        raw=base.verified_file(repo,Path(ENGINE)/path,'HEAD');native_inputs[path]=base.sha(raw);return raw
    packets={}
    def add(key,folder,family=None,stock_layout=None,rawname='map.bin',bordername='border.bin',header_folder=None):
        header=json.loads(read((header_folder or folder)/'map.json'))
        raw,border=read(folder/rawname),read(folder/bordername)
        if family:
            if key.startswith('Campus'):dims=(32,96)
            elif key=='Gate':dims=(32,32)
            elif key=='FightArea':dims=(70,37)
            else:dims=DIMS[key]
            layout=dict(width=dims[0],height=dims[1],primary_tileset='gTileset_General')
        else:
            layout=json.loads(read(stock_layout));dims=(layout['width'],layout['height'])
        expected=None
        if (folder/'attributes.json').is_file():
            expected=json.loads(read(folder/'attributes.json'))
            expected=expected.get('used_source_attribute_words',expected)
        packets[key]=dict(header=header,raw=raw,border=border,layout=layout,family=family,dims=dims,expected_attributes=expected)
    # Source selection is explicit: no glob precedence/last-writer overrides.
    DIMS={'Route225':(32,94),'Route226':(100,32),'Route227':(48,60),'Route229':(64,30),'Route230':(96,34),
          'SurvivalArea':(32,32),'ResortArea':(36,30),'Route228':(32,94),
          'StarkOutside':(32,32),'StarkRoom1':(64,32),'StarkRoom2':(96,96),'StarkRoom3':(32,32)}
    bounded=HERE.parent/'frontier-bounded-campus'
    for key in ('CampusWest','CampusCenter','CampusEast','Gate','FightArea'):
        family='Campus' if key.startswith('Campus') else 'Gate' if key=='Gate' else 'Fight'
        add(key,bounded/'staged'/key,family)
    for key in ('Tower1','Tower2','Tower3','Hall1','Hall2','Factory1','Factory2','Castle','Arcade1','Arcade2'):
        add(key,bounded/'staged'/key,stock_layout=bounded/'staged'/key/'layout.json')
    towns=HERE.parent/'battle-zone-center-shells'
    for key in ('SurvivalArea','ResortArea','Route228'):add(key,towns/'staged'/key,'Battle')
    for area in ('FightArea','SurvivalArea','ResortArea'):
        for floor in (1,2):
            key=area+'Center'+str(floor);add(key,towns/'staged'/key,stock_layout=towns/'staged'/key/'layout.json')
    for area,count in [('FightArea',2),('SurvivalArea',3),('ResortArea',2),('Route228',2)]:
        for i in range(1,count+1):
            key=area+'House'+str(i);add(key,towns/'staged'/key,stock_layout=towns/'staged'/key/'layout.json')
    for key in ('Route225','Route226'):add(key,HERE.parent/'battle-zone-links/staged'/key,'Battle')
    for key in ('Route229','Route230'):
        add(key,HERE.parent/'battle-zone-north/staged'/key,'Battle',rawname='averon-map.bin',bordername='averon-border.bin',header_folder=HERE.parent/'remaining-donor/staged'/key)
    for key,source in [('Route227','Route227'),('StarkOutside','Outside'),('StarkRoom1','Room1')]:
        add(key,HERE.parent/'stark-approach/staged'/source,'Battle' if key=='Route227' else 'StarkApproach')
    for key,source in [('StarkRoom2','Room2'),('StarkRoom3','Room3')]:add(key,HERE.parent/'stark-mountain/staged'/source,'StarkCave')
    if len(packets)!=42:raise ValueError('exact42-map source set required')
    original_room2=packets.pop('StarkRoom2');original_header=original_room2['header'];translation={}
    if original_header['connections'] or len(original_header['warp_events'])!=2:raise ValueError('source Room2 contract differs')
    for col,label in enumerate(('West','Center','East')):
        key='StarkRoom2'+label;h=copy.deepcopy(original_header)
        h.update(id=original_header['id']+'_'+label.upper(),name=original_header['name']+label,warp_events=[],connections=[])
        for index,e in enumerate(original_header['warp_events']):
            if e['x']//32!=col:continue
            translation[str(index)]=dict(map=h['id'],index=len(h['warp_events']))
            h['warp_events'].append(dict(e,x=e['x']%32))
        for dc,direction in ((-1,'left'),(1,'right')):
            if 0<=col+dc<3:h['connections'].append(dict(map=original_header['id']+'_'+('West','Center','East')[col+dc].upper(),direction=direction,offset=0))
        raw=b''.join(original_room2['raw'][(y*96+col*32)*2:(y*96+(col+1)*32)*2] for y in range(96))
        packets[key]=dict(original_room2,header=h,raw=raw,dims=(32,96),layout=dict(original_room2['layout'],width=32,height=96))
    for p in packets.values():
        for e in p['header']['warp_events']:
            if e['dest_map']==original_header['id']:
                target=translation[e['dest_warp_id']];e.update(dest_map=target['map'],dest_warp_id=str(target['index']))
    if len(packets)!=44:raise ValueError('exact bounded44-map scene required')
    ids={p['header']['id']:p for p in packets.values()}
    if len(ids)!=44:raise ValueError('source ID collision')
    for key,p in packets.items():
        h=p['header'];w,height=p['dims']
        if h['region_map_section']!='MAPSEC_PENDING_OWNER' or any(h[x] for x in ('object_events','coord_events','bg_events')):raise ValueError('neutral pending source required')
        if len(p['raw'])!=2*w*height or len(p['border'])!=8 or (w+15)*(height+14)>10240:raise ValueError('map capacity/bounds exceeded')
        for e in h['warp_events']:
            if e['dest_map'] not in ids or not 0<=int(e['dest_warp_id'])<len(ids[e['dest_map']]['header']['warp_events']):raise ValueError('foreign/invalid warp')
            if not 0<=e['x']<w or not 0<=e['y']<height:raise ValueError('warp coordinates outside map')
        for e in h['connections'] or []:
            other=ids.get(e['map']);reverse=dict(up='down',down='up',left='right',right='left')[e['direction']]
            if other is None or dict(map=h['id'],direction=reverse,offset=-e['offset']) not in (other['header']['connections'] or []):raise ValueError('nonreciprocal/foreign source connection')
    families={}
    for name,(folder,graphics) in FAMILIES.items():
        raw={n:read(HERE.parent/folder/n) for n in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin')}
        if raw['primary-metatiles.bin']!=before['data/tilesets/primary/general/metatiles.bin'] or raw['primary-attributes.bin']!=before['data/tilesets/primary/general/metatile_attributes.bin']:raise ValueError('shared primary metadata differs')
        sec,attrs=raw['secondary-metatiles.bin'],raw['secondary-attributes.bin']
        if not sec or len(sec)%16 or len(sec)>8192 or len(attrs)*8!=len(sec):raise ValueError('invalid secondary bank')
        families[name]=dict(raw,graphics=graphics)
    verified_cells=0
    for p in packets.values():
        if p['family']:
            fam=families[p['family']]
            banks=[fam['primary-metatiles.bin'],fam['secondary-metatiles.bin']]
            attrs=[fam['primary-attributes.bin'],fam['secondary-attributes.bin']]
        else:
            symbols=[p['layout']['primary_tileset'],p['layout']['secondary_tileset']]
            paths=['data/tilesets/'+kind+'/'+re.sub(r'(?<!^)(?=[A-Z])','_',symbol.removeprefix('gTileset_')).lower()+'/' for kind,symbol in zip(('primary','secondary'),symbols)]
            banks=[eng(path+'metatiles.bin') for path in paths]
            attrs=[eng(path+'metatile_attributes.bin') for path in paths]
        for (v,) in struct.iter_unpack('<H',p['raw']+p['border']):
            bank,index=divmod(v&1023,512)
            if 16*(index+1)>len(banks[bank]) or 2*(index+1)>len(attrs[bank]):raise ValueError('metatile outside native bank')
            word=struct.unpack_from('<H',attrs[bank],2*index)[0]
            if p['expected_attributes'] is not None and p['expected_attributes'].get(str(v&1023))!=word:raise ValueError('source full attribute differs')
            verified_cells+=1
    # Sharing is allowed only when every old record/attribute and graphics binding survive.
    aliases={}
    for name,fam in families.items():
        options=[n for n,v in families.items() if v['graphics']==fam['graphics'] and v['secondary-metatiles.bin'].startswith(fam['secondary-metatiles.bin']) and v['secondary-attributes.bin'].startswith(fam['secondary-attributes.bin'])]
        aliases[name]=sorted(options,key=lambda n:(-len(families[n]['secondary-metatiles.bin']),n))[0]
    canonical=sorted(set(aliases.values()));out={};decl=[];heads=[];meta=[]
    for name in canonical:
        fam=families[name];symbol='BattleFrontierDev'+name;path='data/tilesets/secondary/battle_frontier_dev_'+name.lower()+'/'
        bindings=reuse.asset_bindings(before['src/data/tilesets/headers.h'].decode(),fam['graphics'])
        out[path+'metatiles.bin']=fam['secondary-metatiles.bin'];out[path+'metatile_attributes.bin']=fam['secondary-attributes.bin']
        decl.append('extern const struct Tileset gTileset_'+symbol+';')
        meta.append('const u16 gMetatiles_'+symbol+'[] = INCBIN_U16("'+path+'metatiles.bin");'+chr(10)+'const u16 gMetatileAttributes_'+symbol+'[] = INCBIN_U16("'+path+'metatile_attributes.bin");')
        heads.append('const struct Tileset gTileset_'+symbol+' = { .isCompressed=TRUE, .isSecondary=TRUE, .tiles='+bindings['tiles']+', .palettes='+bindings['palettes']+', .metatiles=gMetatiles_'+symbol+', .metatileAttributes = gMetatileAttributes_'+symbol+', .callback='+bindings['callback']+' };')
    groups=json.loads(before['data/maps/map_groups.json']);layouts=json.loads(before['data/layouts/layouts.json'])
    prior=list(groups['gMapGroup_Sinnoh']);group=groups['group_order'].index('gMapGroup_Sinnoh')
    if len(prior)!=PRIOR_SLOTS:raise ValueError(f'exact{PRIOR_SLOTS}-map prefix required')
    slots=before['test/data/averon_map_registry_slots.inc'].decode();marker=f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, {PRIOR_SLOTS}, 1)'
    if slots.count(marker)!=1:raise ValueError('registry group pin differs')
    slots=slots.replace(marker,f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, {PRIOR_SLOTS+len(packets)}, 1)')
    includes=[];scene={}
    for i,(key,p) in enumerate(packets.items(),PRIOR_SLOTS):
        name='DevBattleFrontier_'+key;h=copy.deepcopy(p['header']);h.update(name=name,layout='LAYOUT_DEV_BATTLE_FRONTIER_'+key.upper(),region_map_section='MAPSEC_ROUTE_201')
        if name in prior or (engine/'data/maps'/name).exists():raise ValueError('refusing existing scene map')
        l=dict(p['layout']);l.update(id=h['layout'],name=name+'_Layout',blockdata_filepath='data/layouts/'+name+'/map.bin',border_filepath='data/layouts/'+name+'/border.bin',layout_version='emerald')
        if p['family']:l['secondary_tileset']='gTileset_BattleFrontierDev'+aliases[p['family']]
        layouts['layouts'].append(l);groups['gMapGroup_Sinnoh'].append(name)
        for path,raw in [('data/maps/'+name+'/map.json',encode(h)),('data/maps/'+name+'/scripts.inc',(name+'_MapScripts::'+chr(10)+'\t.byte 0'+chr(10)).encode()),('data/layouts/'+name+'/map.bin',p['raw']),('data/layouts/'+name+'/border.bin',p['border'])]:out[path]=raw
        includes.append('\t.include "data/maps/'+name+'/scripts.inc"')
        slots+=f'REGISTRY_SLOT({group}, {i}, {h["id"]}, {name}, 1)'+chr(10)
        scene[key]=dict(group=group,num=i,id=h['id'],name=name,dimensions=list(p['dims']),source_section='MAPSEC_PENDING_OWNER',dev_only_section='MAPSEC_ROUTE_201')
    for path,lines in [('include/tilesets.h',decl),('src/data/tilesets/headers.h',heads),('src/data/tilesets/metatiles.h',meta),('data/event_scripts.s',includes)]:out[path]=before[path]+(chr(10)+chr(10).join(lines)+chr(10)).encode()
    out['data/maps/map_groups.json']=encode(groups);out['data/layouts/layouts.json']=encode(layouts);out['test/data/averon_map_registry_slots.inc']=slots.encode()
    receipt=dict(status='DEV_OVERLAY_ONLY_NOT_ROM_OR_PRODUCTION_ACCEPTANCE',base=BASE,base_engine_tree=ENGINE_TREE,source_sha=base.git(ROOT,'rev-parse','HEAD').decode().strip(),existing_map_names_preserved=prior,
        dev_surrogate='Existing217 only in disposable scene; no permanent origin or save compatibility acceptance',scene=scene,source_sha256=source_pins,
        base_input_sha256={p:base.sha(v) for p,v in before.items()},native_input_sha256=native_inputs,family_aliases=aliases,stark_room2_dev_split=translation,verified_native_attribute_cells=verified_cells,
        secondary_metadata_bytes_before=sum(len(v['secondary-metatiles.bin'])+len(v['secondary-attributes.bin']) for v in families.values()),
        secondary_metadata_bytes_after=sum(len(families[n]['secondary-metatiles.bin'])+len(families[n]['secondary-attributes.bin']) for n in canonical),
        files={p:base.sha(v) for p,v in sorted(out.items())})
    return out,receipt
def export(repo,out):
    out=Path(out).resolve();engine=(Path(repo)/ENGINE).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine export required')
    files,receipt=assemble(repo)
    out.mkdir(parents=True)
    for path,raw in files.items():
        target=out/'overlay'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    (out/'receipt.json').write_bytes(encode(receipt));return receipt
def install(repo):
    repo=Path(repo).resolve();engine=repo/ENGINE
    if not base.git(repo,'branch','--show-current').decode().strip().startswith('codex/battle-frontier-runtime-scratch-') or not (engine/'.map_qa_throwaway').is_file():raise ValueError('marked disposable scene branch required')
    if base.git(repo,'rev-parse','HEAD').decode().strip()!=BASE:raise ValueError('exact production baseline required')
    status=base.git(repo,'status','--porcelain','--untracked-files=normal','--',ENGINE).decode().splitlines()
    if status not in ([],['?? "Pokemon Game/engine/.map_qa_throwaway"']):raise ValueError('refusing dirty runtime engine')
    files,receipt=assemble(repo)
    for path in files:
        target=(engine/path).resolve()
        if not target.is_relative_to(engine.resolve()):raise ValueError('output escapes engine')
        if path not in receipt['base_input_sha256'] and target.exists():raise ValueError('refusing existing untracked target')
    for path,raw in files.items():
        target=engine/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True)
    g=p.add_mutually_exclusive_group();g.add_argument('--out',type=Path);g.add_argument('--install',action='store_true');a=p.parse_args()
    r=install(a.repo) if a.install else export(a.repo,a.out) if a.out else assemble(a.repo)[1]
    print(json.dumps(r,indent=2))
