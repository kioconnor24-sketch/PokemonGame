FloaromaTown_MapScripts::
	.byte 0

FloaromaTown_EventScript_ToMeadow0::
	warp MAP_FLOAROMA_MEADOW, 0
	waitstate
	end

FloaromaTown_EventScript_ToMeadow1::
	warp MAP_FLOAROMA_MEADOW, 1
	waitstate
	end

FloaromaTown_EventScript_Sign::
	msgbox FloaromaTown_Text_Sign, MSGBOX_SIGN
	end

FloaromaTown_Text_Sign:
	.string "FLOAROMA TOWN$"
