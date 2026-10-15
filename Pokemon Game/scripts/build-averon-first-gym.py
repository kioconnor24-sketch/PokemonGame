"""Extend the tested opening toward Alderfield using authored native maps."""
import runpy, copy, json
from pathlib import Path
ns=runpy.run_path(str(Path(__file__).with_name('build-averon-opening.py')))
globals().update({k:v for k,v in ns.items() if not k.startswith('__')})

petalburg,p=source('PetalburgCity')
gymtemplate,g=source('PetalburgCity_Gym')
PATH=p[12][8] # verified broad town footpath

# Open Windrow's north lane. Connection has the same x alignment.
wind=read('data/maps/Windrow/map.json')
wind['connections'].append(dict(map='MAP_ORCHARDLANE',offset=0,direction='up'))
write('data/maps/Windrow/map.json',wind)
wl,wc=source('Windrow');rect(wc,17,0,3,4,PATH);layout('Windrow',wc)

# Orchard Lane: picnic clearing, field path, canal and a catchable eastern fork.
r=field(40,32)
for x in list(range(0,16,2))+list(range(20,40,2)):tree(r,x,0);tree(r,x,28)
for y in range(4,28,4):tree(r,0,y);tree(r,38,y)
rect(r,17,0,3,32,PATH);rect(r,7,14,25,3,PATH)
rect(r,5,5,2,21,WATER)
for y in range(5,26):r[y][4]=0x10B8;r[y][7]=0x10BA
rect(r,4,14,4,3,PATH)
rect(r,25,6,7,5,TALL);rect(r,10,23,5,4,TALL)
for x,y in [(10,4),(14,7),(26,18),(30,23),(8,18)]:tree(r,x,y)
routeNpcs=[npc(16,9,'OBJ_EVENT_GFX_YOUNGSTER','Alderfield_RouteTrainerA',1),npc(21,17,'OBJ_EVENT_GFX_GIRL_1','Alderfield_RouteTrainerB',2),npc(11,16,'OBJ_EVENT_GFX_MAN_1','Alderfield_ExpShare',3),npc(24,12,'OBJ_EVENT_GFX_YOUNGSTER','Alderfield_RouteTrainerC',4)]
mapfile('OrchardLane',layout('OrchardLane',r),'MAPSEC_ORCHARD_LANE',routeNpcs,connections=[dict(map='MAP_WINDROW',offset=0,direction='down'),dict(map='MAP_ALDERFIELD',offset=0,direction='up')])
rm=read('data/maps/OrchardLane/map.json');rm.update(map_type='MAP_TYPE_ROUTE',music='MUS_ROUTE101');write('data/maps/OrchardLane/map.json',rm)

# Alderfield: canal-side market and fields, red roofs, clinic and farm Gym.
a=field(40,32)
for x in range(0,40,2):tree(a,x,0)
for y in range(4,28,4):tree(a,0,y);tree(a,38,y)
rect(a,17,15,3,17,PATH);rect(a,6,15,28,3,PATH);rect(a,7,8,3,10,PATH);rect(a,28,14,3,11,PATH)
rect(a,4,20,10,6,TALL)
rect(a,23,20,2,8,WATER)
for y in range(20,28):a[y][22]=0x10B8;a[y][25]=0x10BA
rect(a,22,23,4,3,PATH)
stamp(a,p,12,3,7,6,5,3) # Gym door source x15,y8 -> x8,y8
stamp(a,oldcells,4,4,4,4,28,9) # supply shop door x29,y12
stamp(a,oldcells,5,13,4,4,16,9) # actual Pokemon Center stamp from Oldale
rect(a,17,13,3,4,PATH)
for x,y in [(13,3),(21,4),(31,3),(3,10),(33,20)]:tree(a,x,y)
mapfile('Alderfield',layout('Alderfield',a),'MAPSEC_ALDERFIELD',[
 npc(16,17,'OBJ_EVENT_GFX_WOMAN_1','Alderfield_Market',1),npc(28,24,'OBJ_EVENT_GFX_OLD_MAN','Alderfield_Canal',2),npc(8,27,'OBJ_EVENT_GFX_LITTLE_BOY','Alderfield_Field',3),
], [warp(8,8,'AlderfieldGym',0),warp(17,12,'AlderfieldClinic',0),warp(29,12,'AlderfieldSupply',0)], [dict(map='MAP_ORCHARDLANE',offset=0,direction='down')])

# Gym: two sluices unlock a central farm gate. Flags survive save/reentry.
gc=copy.deepcopy(g[:9])+[copy.deepcopy(g[6]) for _ in range(7)]
gc[8]=copy.deepcopy(g[6]) # replace the original room separator with walkable floor
gc[15]=copy.deepcopy(g[111]);floor=g[6][4];wall=g[1][0]
for x in range(9):gc[9][x]=wall
gc[9][4]=0x3624 # existing Petalburg Gym door, elevation 3 + collision
mapfile('AlderfieldGym',layout('AlderfieldGym',gc,gymtemplate),'MAPSEC_ALDERFIELD',[
 npc(4,4,'OBJ_EVENT_GFX_MAN_1','Alderfield_Elio',1),npc(2,12,'OBJ_EVENT_GFX_MAN_1','Alderfield_WestSluice',2),npc(6,12,'OBJ_EVENT_GFX_WOMAN_1','Alderfield_EastSluice',3),npc(7,6,'OBJ_EVENT_GFX_YOUNGSTER','Alderfield_GymTrainer',4),
], [warp(4,15,'Alderfield',0),warp(5,15,'Alderfield',0)],indoor=True)
gm=read('data/maps/AlderfieldGym/map.json');gm['music']='MUS_GYM';write('data/maps/AlderfieldGym/map.json',gm)
gm['bg_events']=[bg(1,13,'Alderfield_GymRules')];write('data/maps/AlderfieldGym/map.json',gm)
clinic=read('data/maps/OldaleTown_PokemonCenter_1F/map.json')
clinic.update(id='MAP_ALDERFIELDCLINIC',name='AlderfieldClinic',region_map_section='MAPSEC_ALDERFIELD',connections=None,object_events=[npc(7,2,'OBJ_EVENT_GFX_NURSE','Saltmere_HomeHeal',1)],warp_events=[warp(7,8,'Alderfield',1),warp(6,8,'Alderfield',1)],coord_events=[],bg_events=[])
write('data/maps/AlderfieldClinic/map.json',clinic)
text('data/maps/AlderfieldClinic/scripts.inc','AlderfieldClinic_MapScripts::\n\tmap_script MAP_SCRIPT_ON_TRANSITION, AlderfieldClinic_OnTransition\n\t.byte 0\nAlderfieldClinic_OnTransition:\n\tsetrespawn HEAL_LOCATION_ALDERFIELD\n\tend\n')
mapfile('AlderfieldSupply',layout('AlderfieldSupply',copy.deepcopy(housecells),house),'MAPSEC_ALDERFIELD',[npc(6,4,'OBJ_EVENT_GFX_MAN_1','Alderfield_Shop',1)],[warp(3,8,'Alderfield',2),warp(4,8,'Alderfield',2)],indoor=True)
write('data/layouts/layouts.json',layoutdata)
groups=read('data/maps/map_groups.json');newnames=['OrchardLane','Alderfield','AlderfieldGym','AlderfieldClinic','AlderfieldSupply']
for n in newnames:
    if n not in groups['gMapGroup_AveronOpening']:groups['gMapGroup_AveronOpening'].append(n)
write('data/maps/map_groups.json',groups)
sections=read('src/data/region_map/region_map_sections.json')
for id,name,x,y in [('MAPSEC_ORCHARD_LANE','ORCHARD LANE',3,8),('MAPSEC_ALDERFIELD','ALDERFIELD',3,7)]:
    if not any(s['id']==id for s in sections['map_sections']):sections['map_sections'].append(dict(id=id,name=name,x=x,y=y,width=1,height=1))
write('src/data/region_map/region_map_sections.json',sections)
heals=read('src/data/heal_locations.json')
if not any(h['id']=='HEAL_LOCATION_ALDERFIELD' for h in heals['heal_locations']):
    heals['heal_locations'].append(dict(id='HEAL_LOCATION_ALDERFIELD',map='MAP_ALDERFIELD',x=17,y=13,respawn_map='MAP_ALDERFIELDCLINIC',respawn_npc='1',respawn_x=7,respawn_y=4))
write('src/data/heal_locations.json',heals)
for number,name in [('024','ASSAULT_COMPLETE'),('025','WEST_SLUICE'),('026','EAST_SLUICE'),('027','EXP_SHARE'),('028','GYM1_TM')]:replace('include/constants/flags.h','FLAG_UNUSED_0x'+number,'FLAG_AVERON_'+name)

wild=read('src/data/wild_encounters.json');e=copy.deepcopy(next(e for e in wild['wild_encounter_groups'][0]['encounters'] if e['map']=='MAP_COASTALMEADOW'));e.update(map='MAP_ORCHARDLANE',base_label='gOrchardLane')
for mon in e['land_mons']['mons']:mon.update(min_level=5,max_level=7)
wild['wild_encounter_groups'][0]['encounters']=[x for x in wild['wild_encounter_groups'][0]['encounters'] if x['map']!='MAP_ORCHARDLANE']+[e];write('src/data/wild_encounters.json',wild)

teams=[('FARMER','SAM','Youngster','Youngster',[('Sentret',7),('Bunnelby',8)]),('PICNIC','LINA','Picnicker','Picnicker',[('Hoppip',8),('Smoliv',9)]),('GYM1','NICO','Youngster','Youngster',[('Bunnelby',10),('Lillipup',11)]),('ELIO','ELIO','Leader','Leader Norman',[('Bunnelby',12),('Lechonk',13),('Lillipup',15)]),('ORCHARD','MILO','Youngster','Youngster',[('Pawmi',9),('Lechonk',10)])]
tp=ROOT/'src/data/trainers.party';t=tp.read_text(encoding='utf-8');marker='/* AVERON ALDERFIELD TEAMS */'
if marker in t:t=t[:t.index(marker)]
t+='\n'+marker+'\n'
for id,name,cl,pic,mons in teams:
    t+=f'\n=== TRAINER_AVERON_{id} ===\nName: {name}\nClass: {cl}\nPic: {pic}\nGender: Male\nMusic: Male\nAI: Check Bad Move / Try To Faint\n'
    if id=='GYM1':t+='Double Battle: Yes\n'
    for mon,level in mons:t+=f'\n{mon}\nLevel: {level}\nIVs: 15 HP / 15 Atk / 15 Def / 15 SpA / 15 SpD / 15 Spe\n'
tp.write_text(t,encoding='utf-8')
replace('include/constants/opponents.h','#define TRAINERS_COUNT_EMERALD     859','''#define TRAINER_AVERON_FARMER 859
#define TRAINER_AVERON_PICNIC 860
#define TRAINER_AVERON_GYM1 861
#define TRAINER_AVERON_ELIO 862
#define TRAINER_AVERON_ORCHARD 863
#define TRAINERS_COUNT_EMERALD     864''')

# Enforce the user-selected battle rules at the engine boundary.
replace('include/config/battle.h','B_SPLIT_EXP                 GEN_LATEST','B_SPLIT_EXP                 GEN_5')
replace('src/new_game.c','optionsBattleStyle = OPTIONS_BATTLE_STYLE_SHIFT;','optionsBattleStyle = OPTIONS_BATTLE_STYLE_SET;')
replace('src/battle_main.c','gBattleScripting.battleStyle = gSaveBlock2Ptr->optionsBattleStyle;','gBattleScripting.battleStyle = OPTIONS_BATTLE_STYLE_SET;')
replace('src/battle_main.c','''    #if TESTING
    gBattleScripting.battleStyle = OPTIONS_BATTLE_STYLE_SET;
    #endif
''','')
replace('src/option_menu.c','gTasks[taskId].tBattleStyle = gSaveBlock2Ptr->optionsBattleStyle;','gTasks[taskId].tBattleStyle = OPTIONS_BATTLE_STYLE_SET;')
replace('src/option_menu.c','''    if (JOY_NEW(DPAD_LEFT | DPAD_RIGHT))
    {
        selection ^= 1;
        sArrowPressed = TRUE;
    }

    return selection;
}

static void BattleStyle_DrawChoices''','''    return OPTIONS_BATTLE_STYLE_SET;
}

static void BattleStyle_DrawChoices''')
replace('include/config/caps.h','B_EXP_CAP_TYPE                  EXP_CAP_NONE','B_EXP_CAP_TYPE                  EXP_CAP_HARD')
replace('include/config/caps.h','B_LEVEL_CAP_TYPE                LEVEL_CAP_NONE','B_LEVEL_CAP_TYPE                LEVEL_CAP_FLAG_LIST')
replace('include/config/caps.h','B_RARE_CANDY_CAP                FALSE','B_RARE_CANDY_CAP                TRUE')
for flag,old,new in [(2,19,23),(3,24,31),(4,29,39),(5,31,47),(6,33,55),(7,42,62),(8,46,69)]:replace('src/caps.c',f'{{FLAG_BADGE0{flag}_GET, {old}}}',f'{{FLAG_BADGE0{flag}_GET, {new}}}')
replace('src/caps.c','{FLAG_IS_CHAMPION, 58}', '{FLAG_AVERON_ASSAULT_COMPLETE, 72},\n        {FLAG_IS_CHAMPION, 76}')
replace('src/battle_gimmick.c','return gGimmicksInfo[gimmick].CanActivate != NULL', 'if (gimmick != GIMMICK_MEGA)\n        return FALSE;\n    return gGimmicksInfo[gimmick].CanActivate != NULL')
replace('include/config/species_enabled.h','P_PRIMAL_REVERSIONS              TRUE','P_PRIMAL_REVERSIONS              FALSE')
replace('include/config/species_enabled.h','P_ULTRA_BURST_FORMS              TRUE','P_ULTRA_BURST_FORMS              FALSE')
replace('include/constants/tms_hms.h','F(FOCUS_PUNCH)', 'F(WORK_UP)')
replace('include/constants/tms_hms.h','#endif','// Legacy Hoenn pickup references retain the TM01 slot.\n#define ITEM_TM_FOCUS_PUNCH ITEM_TM_WORK_UP\n\n#endif')
replace('src/data/items.h','''    [ITEM_TM_FOCUS_PUNCH] =
    {
        .name = ITEM_NAME("TM01"),
        .price = 3000,
        .description = COMPOUND_STRING(
            "Powerful, but fails\\n"
            "if the user is\\n"
            "hit by the foe."),''','''    [ITEM_TM_WORK_UP] =
    {
        .name = ITEM_NAME("TM01"),
        .price = 3000,
        .description = COMPOUND_STRING(
            "Raises the user's\\n"
            "Attack and Sp. Atk\\n"
            "at the same time."),''')
es=ROOT/'data/event_scripts.s';content=es.read_text(encoding='utf-8')
for n in newnames:
    inc=f'\t.include "data/maps/{n}/scripts.inc"'
    if inc not in content:content+='\n'+inc+'\n'
es.write_text(content,encoding='utf-8')
script=Path(__file__).with_name('averon-first-gym.inc').read_text(encoding='utf-8').replace('AV_GYM_FLOOR',str(floor&1023))
text('data/maps/AlderfieldGym/scripts.inc',script)
sp=ROOT/'data/specials.inc';value=sp.read_text(encoding='utf-8')
if '\tdef_special GetCurrentLevelCap' not in value:sp.write_text(value+'\n\tdef_special GetCurrentLevelCap\n',encoding='utf-8')
print('Authored Orchard Lane/Alderfield/Gym/clinic/shop; configured Set, hard caps, held EXP Share defaults, and Mega-only gimmick activation.')
