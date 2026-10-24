Route202_MapScripts::
	.byte 0

Route202_EventScript_NorthSign::
	msgbox Route202_Text_NorthSign, MSGBOX_SIGN
	end

Route202_EventScript_RouteSign::
	msgbox Route202_Text_RouteSign, MSGBOX_SIGN
	end

Route202_Text_NorthSign:
	.string "ROUTE 202\n"
	.string "SOUTH: SANDGEM TOWN$"

Route202_Text_RouteSign:
	.string "ROUTE 202$"
