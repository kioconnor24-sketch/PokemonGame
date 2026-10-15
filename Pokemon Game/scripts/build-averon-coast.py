"""Authored, bounded R03 preview; no placeholder Breakwater town or warps."""
from pathlib import Path
import runpy, copy
ns=runpy.run_path(str(Path(__file__).with_name('build-averon-first-gym.py')))
globals().update({k:v for k,v in ns.items() if not k.startswith('__')})

# Alderfield's market lane reaches the coastal road only through this gate.
alder,cells=source('Alderfield')
for y in range(0,32,4):tree(cells,38,y)
rect(cells,33,15,7,3,PATH)
layout('Alderfield',cells,alder)
town=read('data/maps/Alderfield/map.json')
town['connections'].append(dict(map='MAP_COASTALBLUFFS',offset=0,direction='right'))
town['coord_events']=[dict(type='trigger',x=38,y=y,elevation=0,var='VAR_TEMP_1',var_value='0',script='CoastalBluffs_BadgeGate') for y in (15,16,17)]
write('data/maps/Alderfield/map.json',town)

# Upper road and lookout, then a broad descent to a sheltered south-facing cove.
coast=field(64,40)
for x in range(0,64,2):tree(coast,x,0)
for y in range(4,24,4):tree(coast,0,y);tree(coast,62,y)
for x,y in [(8,5),(12,8),(18,4),(38,12),(42,15),(52,10),(56,18)]:tree(coast,x,y)
rect(coast,0,15,31,3,PATH)
rect(coast,28,6,3,22,PATH)
rect(coast,28,6,21,3,PATH)
rect(coast,46,3,3,6,PATH)
rect(coast,46,2,3,1,0x3479) # repaired cliff path stays closed until town production
rect(coast,7,10,9,4,TALL);rect(coast,36,17,9,5,TALL)
rect(coast,0,24,64,1,0x3491) # native General rock wall with sand base
rect(coast,4,25,56,5,0x3124) # common full sand tile sampled from Dewford
rect(coast,0,30,64,10,WATER)
for x in range(0,64):coast[30][x]=0x10B1
rect(coast,28,23,3,5,PATH) # walkable three-tile descent, not a hidden ledge jump
objects=[npc(24,14,'OBJ_EVENT_GFX_MAN_2','CoastalBluffs_Trainer',1),
         npc(32,7,'OBJ_EVENT_GFX_HIKER','CoastalBluffs_Lookout',2),
         npc(14,27,'OBJ_EVENT_GFX_FISHERMAN','CoastalBluffs_Beach',3),
         npc(47,4,'OBJ_EVENT_GFX_HIKER','CoastalBluffs_Repairs',4),
         npc(48,27,'OBJ_EVENT_GFX_ITEM_BALL','CoastalBluffs_Item',5)]
objects[-1]['flag']='FLAG_AVERON_COAST_ITEM'
mapfile('CoastalBluffs',layout('CoastalBluffs',coast),'MAPSEC_COASTAL_BLUFFS',objects,
        connections=[dict(map='MAP_ALDERFIELD',offset=0,direction='left')])
route=read('data/maps/CoastalBluffs/map.json');route.update(map_type='MAP_TYPE_ROUTE',music='MUS_ROUTE104');write('data/maps/CoastalBluffs/map.json',route)
write('data/layouts/layouts.json',layoutdata)
groups=read('data/maps/map_groups.json')
if 'CoastalBluffs' not in groups['gMapGroup_AveronOpening']:groups['gMapGroup_AveronOpening'].append('CoastalBluffs')
write('data/maps/map_groups.json',groups)
sections=read('src/data/region_map/region_map_sections.json')
if not any(s['id']=='MAPSEC_COASTAL_BLUFFS' for s in sections['map_sections']):
    sections['map_sections'].append(dict(id='MAPSEC_COASTAL_BLUFFS',name='COASTAL BLUFFS',x=3,y=6,width=1,height=1))
write('src/data/region_map/region_map_sections.json',sections)
replace('include/constants/flags.h','FLAG_UNUSED_0x029','FLAG_AVERON_COAST_ITEM')
replace('include/constants/opponents.h','#define TRAINER_AVERON_FARMER 859',
        '#define TRAINER_AVERON_COAST TRAINER_GRUNT_UNUSED // Reuse unreferenced slot 568; save size unchanged.\n#define TRAINER_AVERON_FARMER 859')
party=ROOT/'src/data/trainers.party';content=party.read_text(encoding='utf-8')
old='=== TRAINER_GRUNT_UNUSED ===';new='=== TRAINER_AVERON_COAST ==='
start=content.index(new if new in content else old);end=content.index('===',start+len(new if new in content else old))
content=content[:start]+'''=== TRAINER_AVERON_COAST ===
Name: JULES
Class: Bird Keeper
Pic: Bird Keeper
Gender: Male
Music: Male
AI: Check Bad Move / Try To Faint

Wingull
Level: 14
IVs: 15 HP / 15 Atk / 15 Def / 15 SpA / 15 SpD / 15 Spe

Rookidee
Level: 15
IVs: 15 HP / 15 Atk / 15 Def / 15 SpA / 15 SpD / 15 Spe

'''+content[end:]
party.write_text(content,encoding='utf-8')
wild=read('src/data/wild_encounters.json')
encounter=copy.deepcopy(next(e for e in wild['wild_encounter_groups'][0]['encounters'] if e['map']=='MAP_ORCHARDLANE'))
encounter.update(map='MAP_COASTALBLUFFS',base_label='gCoastalBluffs')
species=['WINGULL','ROOKIDEE','BUIZEL','FLETCHLING','LECHONK','HOPPIP','WINGULL','ROOKIDEE','BUIZEL','PAWMI','HOPPIP','FLETCHLING']
for i,mon in enumerate(encounter['land_mons']['mons']):mon.update(species='SPECIES_'+species[i],min_level=10,max_level=13)
wild['wild_encounter_groups'][0]['encounters']=[e for e in wild['wild_encounter_groups'][0]['encounters'] if e['map']!='MAP_COASTALBLUFFS']+[encounter]
write('src/data/wild_encounters.json',wild)
events=ROOT/'data/event_scripts.s';content=events.read_text(encoding='utf-8');inc='\t.include "data/maps/CoastalBluffs/scripts.inc"'
if inc not in content:events.write_text(content+'\n'+inc+'\n',encoding='utf-8')
text('data/maps/CoastalBluffs/scripts.inc',Path(__file__).with_name('averon-coast.inc').read_text(encoding='utf-8'))
print('Authored one badge-gated coastal route preview, beach fork and trainer in a reused save-compatible slot. Breakwater is not implemented.')
