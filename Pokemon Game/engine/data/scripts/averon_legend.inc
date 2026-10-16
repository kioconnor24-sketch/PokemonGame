@ Averon static-encounter macros: legendaries, mythicals and other
@ one-of-a-kind Pokemon. Natives live in src/averon_legend.c.
@
@ NOT YET REGISTERED: data/event_scripts.s (a protected file) does not
@ include this file, so no game script can use it yet. test/averon_legend.c
@ includes it directly. Registering it needs a handoff in issue #15.
@
@ Rules:
@ - Only a real capture marks the encounter caught. A knockout marks it
@   defeated. Running, either side teleporting or fleeing (Roar, Whirlwind,
@   Teleport, Emergency Exit) and any unknown outcome record nothing.
@ - A whiteout ends the script before averon_legend_battle records anything,
@   so the encounter stays available.
@ - Each encounter owns two saved flags chosen by its approved design.
@   Nothing here allocates flags or places an encounter.
@
@ Example (names are placeholders, not an approved encounter):
@ Encounter_Example::
@     averon_legend_check_available FLAG_..._CAUGHT, FLAG_..._DEFEATED, TRUE
@     goto_if_eq VAR_RESULT, FALSE, Encounter_ExampleGone
@     averon_legend_battle SPECIES_..., 50, FLAG_..._CAUGHT, FLAG_..._DEFEATED
@     goto_if_eq VAR_RESULT, AVERON_LEGEND_CAUGHT, Encounter_ExampleCaught
@     @ defeated or still available: keep the object, try again later
@     end

	@ Fights the encounter. Afterwards VAR_RESULT is an AveronLegendResult:
	@ AVAILABLE (0), CAUGHT (1) or DEFEATED (2).
	.macro averon_legend_battle species:req, level:req, caught_flag:req, defeated_flag:req, item=ITEM_NONE
	callnative AveronLegend_Begin, requests_effects=1
	setwildbattle \species, \level, \item
	dowildbattle
	setvar VAR_0x8004, \caught_flag
	setvar VAR_0x8005, \defeated_flag
	callnative AveronLegend_Record, requests_effects=1
	.endm

	@ VAR_RESULT is TRUE if the encounter can be fought now. A defeated
	@ encounter counts as available only if retry_after_defeat is TRUE.
	.macro averon_legend_check_available caught_flag:req, defeated_flag:req, retry_after_defeat:req
	setvar VAR_0x8004, \caught_flag
	setvar VAR_0x8005, \defeated_flag
	setvar VAR_0x8006, \retry_after_defeat
	callnative AveronLegend_CheckAvailable, requests_effects=1
	.endm

	@ Makes a defeated encounter available again. Never undoes a capture.
	.macro averon_legend_allow_retry caught_flag:req, defeated_flag:req
	setvar VAR_0x8004, \caught_flag
	setvar VAR_0x8005, \defeated_flag
	callnative AveronLegend_Retry, requests_effects=1
	.endm
