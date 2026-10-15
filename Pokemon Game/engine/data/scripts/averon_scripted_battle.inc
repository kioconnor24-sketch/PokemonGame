@ Averon scripted-battle macros: story losses, the operative chain and the
@ Gym ambush. Natives live in src/averon_scripted_battle.c.
@
@ NOT YET REGISTERED: nothing in event_scripts.s includes this file, and
@ B_FLAG_NO_WHITEOUT is still 0 in include/config/battle.h, so in the ROM a
@ loss still whites out. Registration waits for QUEST #14 to merge and for an
@ explicit flag handoff with Codex (Issue #15). Native tests include this
@ file directly.
@
@ Rules every caller follows:
@ - Keep each sequence inside one locked script so the game cannot be saved
@   while the no-whiteout flag is set.
@ - Every averon_scripted_battle is followed, on every path, by the result
@   check. The macro clears the flag itself, win or lose.
@
@ Example: ten-battle operative chain, allied heal afterwards
@     averon_scripted_battle TRAINER_..._1, Text_..._Defeat1
@     goto_if_eq VAR_RESULT, TRUE, Scene_ChainLost
@     ... (one per operative; party damage carries over)
@     special HealPlayerParty
@ Scene_ChainLost:
@     averon_respawn
@
@ Example: Gym ambush after the official badge battle
@     setflag FLAG_BADGE0x_GET            @ badge first, as the normal Gym script does
@     averon_scripted_battle TRAINER_..._AMBUSH, Text_..._Defeat
@     goto_if_eq VAR_RESULT, TRUE, Scene_AmbushLost  @ no heal before this battle
@ Scene_AmbushLost:
@     averon_respawn                      @ badge flag is kept

	@ Starts a trainer battle the player is allowed to lose. Afterwards
	@ VAR_RESULT is TRUE if the player lost. Never heals.
	.macro averon_scripted_battle trainer:req, lose_text:req
	callnative AveronScriptedBattle_Begin, requests_effects=1
	trainerbattle_no_intro \trainer, \lose_text
	callnative AveronScriptedBattle_Finish, requests_effects=1
	.endm

	@ After a lost story battle: heals the party and lets the scene continue
	@ where it is. No money is taken.
	.macro averon_recover_in_place
	callnative AveronScriptedBattle_RecoverInPlace, requests_effects=1
	.endm

	@ After a lost battle: heals the party and returns the player to the last
	@ heal location, like a whiteout but without the money loss. Ends the
	@ script.
	.macro averon_respawn
	callnative AveronScriptedBattle_PrepareRespawn, requests_effects=1
	callnative AveronScriptedBattle_DoRespawnWarp, requests_effects=1
	waitstate
	end
	.endm
