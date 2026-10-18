SandgemTown_MapScripts::
	.byte 0

SandgemTown_EventScript_Woman::
	msgbox SandgemTown_Text_Woman, MSGBOX_NPC
	end

SandgemTown_EventScript_Boy::
	msgbox SandgemTown_Text_Boy, MSGBOX_NPC
	end

SandgemTown_EventScript_Fisherman::
	msgbox SandgemTown_Text_Fisherman, MSGBOX_NPC
	end

SandgemTown_EventScript_Man::
	msgbox SandgemTown_Text_Man, MSGBOX_NPC
	end

SandgemTown_EventScript_TownSign::
	msgbox SandgemTown_Text_TownSign, MSGBOX_SIGN
	end

SandgemTown_EventScript_Route202Sign::
	msgbox SandgemTown_Text_Route202Sign, MSGBOX_SIGN
	end

SandgemTown_EventScript_HouseSign::
	msgbox SandgemTown_Text_HouseSign, MSGBOX_SIGN
	end

SandgemTown_EventScript_BeachSign::
	msgbox SandgemTown_Text_BeachSign, MSGBOX_SIGN
	end

SandgemTown_Text_Woman:
	.string "The sea breeze reaches every street\n"
	.string "in Sandgem. On sunny days the whole\l"
	.string "town wanders down to the beach.$"

SandgemTown_Text_Boy:
	.string "I'm going to be a TRAINER someday!\p"
	.string "Until then I watch the POKéMON\n"
	.string "playing in the grass by the road.$"

SandgemTown_Text_Fisherman:
	.string "This beach runs on south toward\n"
	.string "the sea.\p"
	.string "Without a POKéMON that can SURF,\n"
	.string "you'll only get your shoes wet!$"

SandgemTown_Text_Man:
	.string "New TRAINERS always stop by the\n"
	.string "POKé MART before heading north.$"

SandgemTown_Text_TownSign:
	.string "SANDGEM TOWN\n"
	.string "Sand, sea air and a warm welcome.$"

SandgemTown_Text_Route202Sign:
	.string "NORTH: ROUTE 202$"

SandgemTown_Text_HouseSign:
	.string "A neat little house with a sea view.$"

SandgemTown_Text_BeachSign:
	.string "SANDGEM BEACH\n"
	.string "Please take your litter home.$"
