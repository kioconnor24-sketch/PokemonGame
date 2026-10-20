VerityLakefront_MapScripts::
	.byte 0

VerityLakefront_EventScript_ToWarp0::
	warp MAP_LAKE_VERITY, 0
	end

VerityLakefront_EventScript_ToWarp1::
	warp MAP_LAKE_VERITY, 1
	end

VerityLakefront_EventScript_Sign::
	msgbox VerityLakefront_Text_Sign, MSGBOX_SIGN
	end

VerityLakefront_Text_Sign:
	.string "LAKE VERITY$"
