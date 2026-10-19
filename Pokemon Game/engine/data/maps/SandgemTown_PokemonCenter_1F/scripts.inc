SandgemTown_PokemonCenter_1F_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, SandgemTown_PokemonCenter_1F_OnTransition
	.byte 0

SandgemTown_PokemonCenter_1F_OnTransition:
	setrespawn HEAL_LOCATION_SANDGEM_TOWN
	end

SandgemTown_PokemonCenter_1F_EventScript_Nurse::
	setvar VAR_0x800B, 1
	call Common_EventScript_PkmnCenterNurse
	waitmessage
	waitbuttonpress
	release
	end

SandgemTown_PokemonCenter_1F_EventScript_PokefanF::
	msgbox SandgemTown_PokemonCenter_1F_Text_PokefanF, MSGBOX_NPC
	end

SandgemTown_PokemonCenter_1F_EventScript_Girl::
	msgbox SandgemTown_PokemonCenter_1F_Text_Girl, MSGBOX_NPC
	end

SandgemTown_PokemonCenter_1F_Text_PokefanF:
	.string "Whenever my POKéMON get tired from\n"
	.string "playing on the beach, I bring them\l"
	.string "straight here for a rest.$"

SandgemTown_PokemonCenter_1F_Text_Girl:
	.string "The NURSE says healing is always\n"
	.string "free. I think that's wonderful!$"
