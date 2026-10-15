"""Attach controlled QA fixtures to upstream's developer-only Script 1/2/3.

Never select these during a natural balance playthrough. Back up the native
save first; restore it afterward. Release builds disable the debug menu.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'engine'
p=root/'data/scripts/debug.inc';s=p.read_text(encoding='utf-8')
def replace_block(label,nextlabel,body):
    global s
    a=s.index(label+'::');b=s.index(nextlabel+'::',a)
    s=s[:a]+label+'::\n'+body+'\n\n'+s[b:]
cap=''
for i,(species,level,item) in enumerate([('SNIVY',15,'ORAN_BERRY'),('BUNNELBY',14,'EXP_SHARE'),('PAWMI',14,'NONE'),('FLETCHLING',14,'NONE'),('SMOLIV',14,'NONE'),('FENNEKIN',14,'NONE')]):
    cap+=f'\tcreatemon 0, {i}, SPECIES_{species}, {level}, ITEM_{item}\n'
cap+='\tspecial CalculatePlayerPartyCount\n\tspecial HealPlayerParty\n\tspecial UpdateFollowingPokemon\n\tgiveitem ITEM_RARE_CANDY, 6\n\tmsgbox Averon_DebugCapText, MSGBOX_DEFAULT\n\treleaseall\n\tend'
replace_block('Debug_EventScript_Script_1','Debug_EventScript_Script_2',cap)
replace_block('Debug_EventScript_Script_2','Debug_EventScript_Script_3','''\tcreatemon 0, 0, SPECIES_CHARIZARD, 15, ITEM_CHARIZARDITE_X, move1=MOVE_EMBER, move2=MOVE_SCRATCH, move3=MOVE_GROWL, move4=MOVE_DRAGON_BREATH
\tspecial CalculatePlayerPartyCount
\tspecial HealPlayerParty
\tspecial UpdateFollowingPokemon
\tgiveitem ITEM_MEGA_RING
\tmsgbox Averon_DebugMegaText, MSGBOX_DEFAULT
\treleaseall
\tend''')
exp=''
for i,(species,level,item) in enumerate([('SNIVY',10,'NONE'),('BUNNELBY',5,'EXP_SHARE'),('PAWMI',5,'NONE'),('FLETCHLING',5,'NONE'),('SMOLIV',5,'NONE'),('FENNEKIN',5,'NONE')]):
    exp+=f'\tcreatemon 0, {i}, SPECIES_{species}, {level}, ITEM_{item}\n'
exp+='\tspecial CalculatePlayerPartyCount\n\tspecial HealPlayerParty\n\tspecial UpdateFollowingPokemon\n\tmsgbox Averon_DebugExpText, MSGBOX_DEFAULT\n\treleaseall\n\tend'
replace_block('Debug_EventScript_Script_3','Debug_EventScript_Script_4',exp)
marker='@ AVERON QA FIXTURE TEXT'
if marker in s:s=s[:s.index(marker)]
s+='''\n@ AVERON QA FIXTURE TEXT
Averon_DebugCapText:
    .string "QA party ready: lead Lv. 15.\\nTest candy and battle EXP at cap.$"
Averon_DebugMegaText:
    .string "QA Mega Charizard ready.\\nTest SELECT on its move screen.$"
Averon_DebugExpText:
    .string "QA EXP party ready.\\nOnly Bunnelby holds Exp. Share.$"
'''
p.write_text(s,encoding='utf-8')
print('Developer-only fixtures installed in Script 1 (cap), 2 (Mega), 3 (held EXP).')
