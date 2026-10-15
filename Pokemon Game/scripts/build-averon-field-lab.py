"""Developer-only obstacle fixture; no final world geography or earning locations."""
from pathlib import Path

def apply(ns):
    read,write,text=ns['read'],ns['write'],ns['text']
    root=ns['ROOT']; cells=ns['field'](28,22)
    for x in range(28):cells[0][x]=cells[21][x]=0x3479
    for y in range(22):cells[y][0]=cells[y][27]=0x3479
    ns['rect'](cells,17,5,8,12,ns['WATER'])
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
    write('data/maps/AveronFieldLab/map.json',m)
    write('data/layouts/layouts.json',ns['layoutdata'])
    groups=read('data/maps/map_groups.json')
    if 'AveronFieldLab' not in groups['gMapGroup_AveronOpening']:
        groups['gMapGroup_AveronOpening'].append('AveronFieldLab')
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
    content+='\n'+marker+'\n#ifndef RELEASE\n\t.include "data/maps/AveronFieldLab/scripts.inc"\n#else\n'
    content+='AveronFieldLab_MapScripts::\n\t.byte 0\n'
    for label in ('Enter','Grant','Revoke','Exit'):
        content+='AveronFieldLab_'+label+'::\n\tend\n'
    content+='#endif\n';events.write_text(content,encoding='utf-8')
    debug=root/'data/scripts/debug.inc'; content=debug.read_text(encoding='utf-8')
    start=content.index('Debug_EventScript_Script_4::');end=content.index('Debug_EventScript_Script_5::',start)
    content=content[:start]+'Debug_EventScript_Script_4::\n\tgoto AveronFieldLab_Enter\n\n'+content[end:]
    debug.write_text(content,encoding='utf-8')
