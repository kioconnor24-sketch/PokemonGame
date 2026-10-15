"""Developer-only obstacle fixture; no final world geography or earning locations."""
from pathlib import Path
from collections import Counter
import re, struct

def apply(ns):
    read,write,text=ns['read'],ns['write'],ns['text']
    root=ns['ROOT']; cells=ns['field'](28,22)
    for x in range(28):cells[0][x]=cells[21][x]=0x3479
    for y in range(22):cells[y][0]=cells[y][27]=0x3479
    ns['rect'](cells,17,5,8,12,ns['WATER'])
    # Reuse actual General tiles from the upstream maps, including elevation.
    behaviors={}; index=-1
    for token in re.finditer(r'^\s*(MB_\w+)(?:\s*=\s*(0x[0-9A-Fa-f]+|\d+))?\s*,',
                            (root/'include/constants/metatile_behaviors.h').read_text(),re.M):
        index=int(token[2],0) if token[2] else index+1
        behaviors[token[1]]=index
    attrs=struct.unpack('<512H',(root/'data/tilesets/primary/general/metatile_attributes.bin').read_bytes())
    def sample(name,behavior):
        _, grid=ns['source'](name)
        matches=[v for row in grid for v in row if (v&1023)<512 and attrs[v&1023]&255==behaviors[behavior]]
        if not matches:raise ValueError(f'No native {behavior} tile in {name}')
        return Counter(matches).most_common(1)[0][0]
    ns['rect'](cells,18,11,6,5,sample('Route124','MB_DEEP_WATER'))
    ns['rect'](cells,20,7,1,3,sample('Route119','MB_WATERFALL'))
    objects=[ns['npc'](5,3,'OBJ_EVENT_GFX_SCIENTIST_1','AveronFieldLab_Grant'),
             ns['npc'](9,3,'OBJ_EVENT_GFX_SCIENTIST_1','AveronFieldLab_Revoke'),
             ns['npc'](13,3,'OBJ_EVENT_GFX_MAN_1','AveronFieldLab_Exit'),
             ns['npc'](5,9,'OBJ_EVENT_GFX_CUTTABLE_TREE','EventScript_CutTree'),
             ns['npc'](9,9,'OBJ_EVENT_GFX_BREAKABLE_ROCK','EventScript_RockSmash'),
             ns['npc'](13,9,'OBJ_EVENT_GFX_PUSHABLE_BOULDER','EventScript_StrengthBoulder')]
    objects[3]['flag']='FLAG_TEMP_11'; objects[4]['flag']='FLAG_TEMP_12'
    objects[5].update(flag='FLAG_TEMP_13',movement_type='MOVEMENT_TYPE_LOOK_AROUND')
    ns['mapfile']('AveronFieldLab',ns['layout']('AveronFieldLab',cells),'MAPSEC_SALTMERE',objects)
    m=read('data/maps/AveronFieldLab/map.json');m['show_map_name']=False
    m['connections']=[dict(map='MAP_AVERONFIELDLABUNDERWATER',direction='dive',offset=0)]
    write('data/maps/AveronFieldLab/map.json',m)
    underwater, native=ns['source']('Underwater_Route124')
    under_attrs=[v[0] for v in struct.iter_unpack('<H',(root/'data/tilesets/secondary/underwater/metatile_attributes.bin').read_bytes())]
    floor=Counter(v for row in native for v in row if ((v>>10)&3)==0
                  and ((attrs if (v&1023)<512 else under_attrs)[(v&1023)%512]&255)==behaviors['MB_NORMAL']).most_common(1)[0][0]
    # Enclose the room exactly below the diveable surface patch, preventing
    # emergence onto land or the waterfall. 0x21E is native underwater rock wall.
    room=[[0x361E]*28 for _ in range(22)]
    ns['rect'](room,18,11,6,5,floor)
    ns['mapfile']('AveronFieldLabUnderwater',ns['layout']('AveronFieldLabUnderwater',room,underwater),'MAPSEC_SALTMERE',[])
    m=read('data/maps/AveronFieldLabUnderwater/map.json')
    m.update(map_type='MAP_TYPE_UNDERWATER',music='MUS_UNDERWATER',weather='WEATHER_UNDERWATER_BUBBLES',
             allow_cycling=False,show_map_name=False,
             connections=[dict(map='MAP_AVERONFIELDLAB',direction='emerge',offset=0)])
    write('data/maps/AveronFieldLabUnderwater/map.json',m)
    write('data/layouts/layouts.json',ns['layoutdata'])
    groups=read('data/maps/map_groups.json')
    if 'AveronFieldLab' not in groups['gMapGroup_AveronOpening']:
        groups['gMapGroup_AveronOpening'].append('AveronFieldLab')
    if 'AveronFieldLabUnderwater' not in groups['gMapGroup_AveronOpening']:
        groups['gMapGroup_AveronOpening'].append('AveronFieldLabUnderwater')
    write('data/maps/map_groups.json',groups)
    lines=['AveronFieldLab_MapScripts::','    .byte 0',
           'AveronFieldLab_Enter::','    warp MAP_AVERONFIELDLAB, 4, 4','    waitstate','    end',
           'AveronFieldLab_Grant::','    lockall',
           '    msgbox AveronFieldLab_TextConfirm, MSGBOX_YESNO',
           '    goto_if_eq VAR_RESULT, NO, AveronFieldLab_Release']
    for name in ('CUT','ROCK_SMASH','STRENGTH','SURF','WATERFALL','DIVE','FLY'):
        lines.append('    setflag FLAG_AVERON_LICENSE_'+name)
    lines+=['    msgbox AveronFieldLab_TextGranted, MSGBOX_DEFAULT','    releaseall','    end',
            'AveronFieldLab_Revoke::','    lockall']
    for name in ('CUT','ROCK_SMASH','STRENGTH','SURF','WATERFALL','DIVE','FLY'):
        lines.append('    clearflag FLAG_AVERON_LICENSE_'+name)
    lines+=['    clearflag FLAG_SYS_USE_STRENGTH','    msgbox AveronFieldLab_TextRevoked, MSGBOX_DEFAULT','    releaseall','    end',
            'AveronFieldLab_Exit::','    lockall','    warp MAP_SALTMERE, 18, 18','    waitstate','    end',
            'AveronFieldLab_TextGranted:','    .string "DEV: All field licenses granted.\\nBack up your save before testing.$"',
            'AveronFieldLab_TextRevoked:','    .string "DEV: Field licenses revoked.$"',
            'AveronFieldLab_Release:','    releaseall','    end',
            'AveronFieldLab_TextConfirm:','    .string "DEV: Grant all field licenses?\\nUse a backed-up test save.$"']
    text('data/maps/AveronFieldLab/scripts.inc','\n'.join(lines)+'\n')
    # No ordinary connections/warps lead here. Release entry and grant/revoke
    # scripts are stubs; debug Script4 is the only entry in developer builds.
    events=root/'data/event_scripts.s'; content=events.read_text(encoding='utf-8')
    marker='@ AVERON FIELD LAB'
    if marker in content:content=content[:content.index(marker)].rstrip()+'\n'
    content+='\n'+marker+'\n\t.include "data/maps/AveronFieldLabUnderwater/scripts.inc"\n#ifndef RELEASE\n\t.include "data/maps/AveronFieldLab/scripts.inc"\n#else\n'
    content+='AveronFieldLab_MapScripts::\n\t.byte 0\n'
    for label in ('Enter','Grant','Revoke','Exit'):
        content+='AveronFieldLab_'+label+'::\n\tend\n'
    content+='#endif\n';events.write_text(content,encoding='utf-8')
    debug=root/'data/scripts/debug.inc'; content=debug.read_text(encoding='utf-8')
    start=content.index('Debug_EventScript_Script_4::');end=content.index('Debug_EventScript_Script_5::',start)
    content=content[:start]+'Debug_EventScript_Script_4::\n\tgoto AveronFieldLab_Enter\n\n'+content[end:]
    debug.write_text(content,encoding='utf-8')
