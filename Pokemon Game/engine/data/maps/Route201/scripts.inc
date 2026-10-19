Route201_MapScripts::
	.byte 0

Route201_EventScript_WestSign::
	msgbox Route201_Text_RouteSign, MSGBOX_SIGN
	end

Route201_EventScript_MiddleSign::
	msgbox Route201_Text_RouteSign, MSGBOX_SIGN
	end

Route201_EventScript_SandgemSign::
	msgbox Route201_Text_SandgemSign, MSGBOX_SIGN
	end

Route201_Text_RouteSign:
	.string "ROUTE 201$"

Route201_Text_SandgemSign:
	.string "ROUTE 201\n"
	.string "EAST: SANDGEM TOWN$"
