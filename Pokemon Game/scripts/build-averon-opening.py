"""Author the small Averon opening in native Emerald map/event formats.

Coordinates and landmarks are deliberately specified here, never randomized.
Existing tiles are prototype assets; new roofs/greenhouse art remain an art task.
"""
import json, struct, copy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'engine'
def read(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))
def write(p,value):
    path=ROOT/p; path.parent.mkdir(parents=True,exist_ok=True)
    value=json.dumps(value,indent=2)+'\n'
    if not path.exists() or path.read_text(encoding='utf-8')!=value:path.write_text(value,encoding='utf-8')
def text(p,value):
    path=ROOT/p; path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or path.read_text(encoding='utf-8')!=value:path.write_text(value,encoding='utf-8')
def replace(p,old,new):
    path=ROOT/p; s=path.read_text(encoding='utf-8')
    if old not in s:
        assert new in s,(p,old)
        return
    if old in new and new in s:return
    path.write_text(s.replace(old,new,1),encoding='utf-8')

layoutdata=read('data/layouts/layouts.json')
def source(name):
    l=next(x for x in layoutdata['layouts'] if x['name']==name+'_Layout')
    vals=struct.unpack('<'+'H'*(l['width']*l['height']),(ROOT/l['blockdata_filepath']).read_bytes())
    return l,[list(vals[y*l['width']:(y+1)*l['width']]) for y in range(l['height'])]
oldale,oldcells=source('OldaleTown')
route,routecells=source('Route102')
house,housecells=source('House1')
GRASS=0x3001; PATH=oldcells[12][10]; WATER=0x10A1; TALL=0x300D # verified MB_TALL_GRASS, no collision
def field(w,h): return [[GRASS]*w for _ in range(h)]
def rect(a,x,y,w,h,tile):
    for yy in range(y,y+h):
        for xx in range(x,x+w): a[yy][xx]=tile
def stamp(a,src,sx,sy,w,h,x,y):
    for yy in range(h): a[y+yy][x:x+w]=src[sy+yy][sx:sx+w]
def tree(a,x,y): stamp(a,oldcells,0,0,2,4,x,y)
def layout(name,cells,template=oldale):
    entry=copy.deepcopy(template); entry.update(id='LAYOUT_'+name.upper(),name=name+'_Layout',width=len(cells[0]),height=len(cells),border_filepath=f'data/layouts/{name}/border.bin',blockdata_filepath=f'data/layouts/{name}/map.bin')
    found=next((i for i,l in enumerate(layoutdata['layouts']) if l['id']==entry['id']),None)
    if found is None:layoutdata['layouts'].append(entry)
    else:layoutdata['layouts'][found]=entry
    folder=ROOT/f'data/layouts/{name}';folder.mkdir(parents=True,exist_ok=True)
    (folder/'map.bin').write_bytes(struct.pack('<'+'H'*sum(map(len,cells)),*(v for row in cells for v in row)))
    (folder/'border.bin').write_bytes((ROOT/template['border_filepath']).read_bytes())
    return entry['id']
def npc(x,y,gfx,script,local_id=None):
    n=dict(graphics_id=gfx,x=x,y=y,elevation=3,movement_type='MOVEMENT_TYPE_FACE_DOWN',movement_range_x=0,movement_range_y=0,trainer_type='TRAINER_TYPE_NONE',trainer_sight_or_berry_tree_id='0',script=script,flag='0')
    # Numeric local IDs are positional. Only named constants belong in local_id.
    return n
def warp(x,y,dest,index): return dict(x=x,y=y,elevation=0,dest_map='MAP_'+dest.upper(),dest_warp_id=str(index))
def bg(x,y,script):return dict(type='sign',x=x,y=y,elevation=0,player_facing_dir='BG_EVENT_PLAYER_FACING_ANY',script=script)
def mapfile(name,layoutid,section,npcs,warps=[],connections=None,bgs=[],coords=[],indoor=False):
    m=copy.deepcopy(read('data/maps/OldaleTown_House1/map.json' if indoor else 'data/maps/OldaleTown/map.json'))
    m.update(id='MAP_'+name.upper(),name=name,layout=layoutid,region_map_section=section,music='MUS_LITTLEROOT' if name=='Saltmere' else 'MUS_OLDALE',connections=connections,object_events=npcs,warp_events=warps,coord_events=coords,bg_events=bgs,show_map_name=not indoor)
    if name=='CoastalMeadow':m.update(map_type='MAP_TYPE_ROUTE',music='MUS_ROUTE101')
    write(f'data/maps/{name}/map.json',m)
    text(f'data/maps/{name}/scripts.inc',f'{name}_MapScripts::\n\t.byte 0\n')
    return m

# Saltmere: west/south water, a sheltered pier, clustered homes and a north exit.
s=field(40,34)
rect(s,0,0,6,34,WATER);rect(s,0,28,40,6,WATER)
for y in range(0,28): s[y][6]=0x10BA # east shoreline
for x in range(7,40): s[28][x]=0x10B1 # north shoreline
rect(s,7,24,10,3,PATH) # pier approach
rect(s,3,25,14,2,PATH) # short pier; walkable above the water
rect(s,8,12,27,3,PATH);rect(s,17,12,3,15,PATH)
rect(s,33,0,3,15,PATH)
for x,y in [(10,6),(25,5),(24,19),(10,16)]:
    stamp(s,oldcells,4,4,4,4,x,y)
    rect(s,x+1,y+4,2,3,PATH)
for x in list(range(8,34,2))+[36,38]: tree(s,x,0)
for x,y in [(37,5),(37,18),(8,21)]: tree(s,x,y)
saltlayout=layout('Saltmere',s)
warps=[warp(11,9,'SaltmereGreenhouse',0),warp(26,8,'SaltmereWorkshop',0),warp(25,22,'SaltmereHarbor',0),warp(11,19,'SaltmereHome',0)]
coords=[dict(type='trigger',x=x,y=1,elevation=0,var='VAR_TEMP_1',var_value='0',script='Saltmere_ExitGate') for x in (33,34,35)]
mapfile('Saltmere',saltlayout,'MAPSEC_SALTMERE',[
 npc(18,16,'OBJ_EVENT_GFX_PROF_BIRCH','Saltmere_Fenwick',1),
 npc(10,25,'OBJ_EVENT_GFX_BOY_2','Saltmere_Pip',2),
 npc(28,25,'OBJ_EVENT_GFX_FISHERMAN','Saltmere_Dockhand',3),
 npc(32,7,'OBJ_EVENT_GFX_RIVAL_BRENDAN_NORMAL','Saltmere_Renn',4),
 npc(20,14,'OBJ_EVENT_GFX_RIVAL_MAY_NORMAL','Saltmere_Mira',5),
],warps,[dict(map='MAP_COASTALMEADOW',offset=0,direction='up')],coords=coords)

# Household rooms remain small and readable. Each has its own event data.
for name,index,keeper,gfx in [('SaltmereGreenhouse',0,'Saltmere_GreenhouseKeeper','OBJ_EVENT_GFX_WOMAN_1'),('SaltmereWorkshop',1,'Saltmere_WorkshopKeeper','OBJ_EVENT_GFX_MAN_1'),('SaltmereHarbor',2,'Saltmere_HarborKeeper','OBJ_EVENT_GFX_FISHERMAN'),('SaltmereHome',3,'Saltmere_HomeHeal','OBJ_EVENT_GFX_MOM')]:
    cells=copy.deepcopy(housecells)
    if name=='SaltmereHome':cells[1][0]=(cells[1][0]&0xFC00)|0x004
    lid=layout(name,cells,house)
    bgs=[bg(2,1,'Saltmere_Tray')] if index==0 else [bg(1,1,'Saltmere_WorkshopScrew')] if index==1 else []
    mapfile(name,lid,'MAPSEC_SALTMERE',[npc(6,4,gfx,keeper,1)],[warp(3,8,'Saltmere',index),warp(4,8,'Saltmere',index)],bgs=bgs,indoor=True)

# Route 01: one crossing, two grassy pockets, an optional coast lookout.
r=field(40,32)
for x in range(0,40,2):
    if x not in (16,18): tree(r,x,0)
for y in range(4,28,4): tree(r,0,y);tree(r,38,y)
for x in list(range(0,32,2))+[36,38]:tree(r,x,28)
rect(r,17,0,3,18,PATH);rect(r,17,16,18,3,PATH);rect(r,33,18,3,14,PATH)
rect(r,20,7,2,18,WATER)
for y in range(7,25):r[y][19]=0x10B8;r[y][22]=0x10BA
rect(r,19,16,4,3,PATH) # safe stepping-stone crossing, prototype tiles
rect(r,6,8,8,5,TALL);rect(r,26,22,6,5,TALL)
rect(r,5,21,8,3,PATH)
for x,y in [(4,4),(12,4),(24,4),(30,8),(8,16),(12,25),(26,12)]:tree(r,x,y)
mapfile('CoastalMeadow',layout('CoastalMeadow',r),'MAPSEC_COASTAL_MEADOW',[
 npc(16,12,'OBJ_EVENT_GFX_YOUNGSTER','Averon_MeadowTrainer',1),
 npc(6,22,'OBJ_EVENT_GFX_LITTLE_BOY','Averon_Lookout',2),
],[ ],[dict(map='MAP_SALTMERE',offset=0,direction='down'),dict(map='MAP_WINDROW',offset=0,direction='up')])

# Windrow: compact orchard hamlet and a growers' cooperative.
w=field(40,26);rect(w,17,0,3,26,PATH);rect(w,8,13,25,3,PATH)
for x in range(0,40,2):tree(w,x,0)
for x in (4,8,12,24,28,32):
    for y in (5,9):tree(w,x,y)
stamp(w,oldcells,4,4,4,4,25,17);rect(w,26,21,2,3,PATH)
for y in range(4,22,4):tree(w,0,y);tree(w,38,y)
mapfile('Windrow',layout('Windrow',w),'MAPSEC_WINDROW',[
 npc(15,14,'OBJ_EVENT_GFX_WOMAN_1','Windrow_Berries',1),
 npc(22,14,'OBJ_EVENT_GFX_OLD_MAN','Windrow_RoadAhead',2),
], [warp(26,20,'WindrowCooperative',0)], [dict(map='MAP_COASTALMEADOW',offset=0,direction='down')])
coopcells=copy.deepcopy(housecells);coopcells[1][0]=(coopcells[1][0]&0xFC00)|0x004
mapfile('WindrowCooperative',layout('WindrowCooperative',coopcells,house),'MAPSEC_WINDROW',[npc(6,4,'OBJ_EVENT_GFX_WOMAN_1','Saltmere_HomeHeal',1)],[warp(3,8,'Windrow',0),warp(4,8,'Windrow',0)],indoor=True)

write('data/layouts/layouts.json',layoutdata)
groups=read('data/maps/map_groups.json'); group='gMapGroup_AveronOpening'
if group not in groups['group_order']:groups['group_order'].append(group)
names=['Saltmere','SaltmereGreenhouse','SaltmereWorkshop','SaltmereHarbor','SaltmereHome','CoastalMeadow','Windrow','WindrowCooperative']
groups[group]=names+[n for n in groups.get(group,[]) if n not in names];write('data/maps/map_groups.json',groups)
sections=read('src/data/region_map/region_map_sections.json')
for section in sections['map_sections']:
    if 'Ã' in section.get('name',''):
        section['name']=section['name'].encode('cp1252').decode('utf-8')
for id,name,x,y in [('MAPSEC_SALTMERE','SALTMERE',3,11),('MAPSEC_COASTAL_MEADOW','COASTAL MEADOW',3,10),('MAPSEC_WINDROW','WINDROW HAMLET',3,9)]:
    if not any(e['id']==id for e in sections['map_sections']):sections['map_sections'].append(dict(id=id,name=name,x=x,y=y,width=1,height=1))
write('src/data/region_map/region_map_sections.json',sections)

for old,new in [('VAR_UNUSED_0x404E','VAR_AVERON_FIRST_HOUSE'),('VAR_UNUSED_0x4083','VAR_AVERON_GREENHOUSE'),('VAR_UNUSED_0x408B','VAR_AVERON_WORKSHOP'),('VAR_UNUSED_0x4091','VAR_AVERON_HARBOR'),('VAR_UNUSED_0x409B','VAR_AVERON_RENN'),('VAR_UNUSED_0x409D','VAR_AVERON_MIRA_STARTER'),('VAR_UNUSED_0x40A1','VAR_AVERON_INTRO')]:replace('include/constants/vars.h',old,new)
for old,new in [('FLAG_UNUSED_0x020','FLAG_AVERON_STARTER'),('FLAG_UNUSED_0x021','FLAG_AVERON_PIP_SCREW'),('FLAG_UNUSED_0x022','FLAG_AVERON_BERRIES')]:replace('include/constants/flags.h',old,new)
replace('include/constants/flags.h','FLAG_UNUSED_0x023','FLAG_AVERON_SUPPLIES')

replace('src/new_game.c','SetWarpDestination(MAP_GROUP(MAP_INSIDE_OF_TRUCK), MAP_NUM(MAP_INSIDE_OF_TRUCK), WARP_ID_NONE, -1, -1);','SetWarpDestination(MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18);')
replace('src/new_game.c','OPTIONS_TEXT_SPEED_MID;','OPTIONS_TEXT_SPEED_FAST;')
replace('include/config/overworld.h','OW_FOLLOWERS_ENABLED           FALSE','OW_FOLLOWERS_ENABLED           TRUE')
replace('src/battle_setup.c','TRAINER_BATTLE_PARAM.earlyRival && GetRivalBattleFlags() & RIVAL_BATTLE_TUTORIAL',
        'TRAINER_BATTLE_PARAM.earlyRival && (GetRivalBattleFlags() & RIVAL_BATTLE_TUTORIAL) == RIVAL_BATTLE_TUTORIAL')
# Retain naming/gender intro in the production flow. Dev tests can use debug
# warp on an existing save; no fake save data or party injected by this script.

heals=read('src/data/heal_locations.json')
for h in heals['heal_locations'][:2]:
    h.update(map='MAP_SALTMERE',x=18,y=18,respawn_map='MAP_SALTMEREHOME',respawn_npc='1',respawn_x=6,respawn_y=5)
write('src/data/heal_locations.json',heals)

wild=read('src/data/wild_encounters.json'); encounter=copy.deepcopy(wild['wild_encounter_groups'][0]['encounters'][0])
encounter.update(map='MAP_COASTALMEADOW',base_label='gCoastalMeadow')
species=['FLETCHLING','LECHONK','BUNNELBY','SMOLIV','PAWMI','SENTRET','HOPPIP','FLETCHLING','LECHONK','SMOLIV','PAWMI','HOPPIP']
for i,mon in enumerate(encounter['land_mons']['mons']):mon.update(species='SPECIES_'+species[i],min_level=2,max_level=4)
wild['wild_encounter_groups'][0]['encounters']=[e for e in wild['wild_encounter_groups'][0]['encounters'] if e['map']!='MAP_COASTALMEADOW']+[encounter]
write('src/data/wild_encounters.json',wild)

events=ROOT/'data/event_scripts.s';content=events.read_text(encoding='utf-8')
for name in names:
    inc=f'\t.include "data/maps/{name}/scripts.inc"'
    if inc not in content:content+='\n'+inc+'\n'
events.write_text(content,encoding='utf-8')
specials=ROOT/'data/specials.inc'; specialtext=specials.read_text(encoding='utf-8')
if '\tdef_special UpdateFollowingPokemon' not in specialtext:
    # Append before the table terminator, keeping all existing special IDs stable.
    position=specialtext.rfind('gSpecialsEnd')
    if position < 0:
        specialtext+='\n\tdef_special UpdateFollowingPokemon\n'
    else:
        specialtext=specialtext[:position]+'\tdef_special UpdateFollowingPokemon\n'+specialtext[position:]
    specials.write_text(specialtext,encoding='utf-8')
# Authored dialogue and state machine stay in a reviewable source file.
text('data/maps/Saltmere/scripts.inc',(Path(__file__).with_name('averon-opening.inc')).read_text(encoding='utf-8'))
saltmap=read('data/maps/Saltmere/map.json')
saltmap['object_events'].append(npc(14,26,'OBJ_EVENT_GFX_ITEM_BALL','Saltmere_PipScrew',6))
saltmap['object_events'][-1]['flag']='FLAG_AVERON_PIP_SCREW'
write('data/maps/Saltmere/map.json',saltmap)
trainers=ROOT/'src/data/trainers.party'; trainertext=trainers.read_text(encoding='utf-8')
marker='/* AVERON OPENING TEAMS */'
if marker in trainertext: trainertext=trainertext[:trainertext.index(marker)]
trainertext+='\n'+marker+'\n'
for species,moves in [('FENNEKIN',['Scratch','Tail Whip']),('PIPLUP',['Pound','Growl']),('SNIVY',['Tackle','Leer'])]:
    trainertext+=f'\n=== TRAINER_AVERON_RENN_{species} ===\nName: RENN\nClass: Pkmn Trainer 1\nPic: Brendan\nGender: Male\nMusic: Male\nAI: Check Bad Move\n\n{species.title()}\nLevel: 5\nIVs: 10 HP / 10 Atk / 10 Def / 10 SpA / 10 SpD / 10 Spe\n'+''.join('- '+m+'\n' for m in moves)
trainertext+='\n=== TRAINER_AVERON_MEADOW ===\nName: FINN\nClass: Youngster\nPic: Youngster\nGender: Male\nMusic: Male\nAI: Check Bad Move\n\nLechonk\nLevel: 4\n- Tackle\n- Tail Whip\n'
trainers.write_text(trainertext,encoding='utf-8')
if 'TRAINER_AVERON_RENN_FENNEKIN' not in (ROOT/'include/constants/opponents.h').read_text():
    replace('include/constants/opponents.h','#define TRAINERS_COUNT_EMERALD     855',
'''#define TRAINER_AVERON_RENN_FENNEKIN 855
#define TRAINER_AVERON_RENN_PIPLUP 856
#define TRAINER_AVERON_RENN_SNIVY 857
#define TRAINER_AVERON_MEADOW 858
#define TRAINERS_COUNT_EMERALD     859''')
print('Authored 8 native maps, 3 map sections, opening state IDs, encounters and new-game spawn.')
