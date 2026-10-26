CanalaveCity_Harbor_MapScripts::
	.byte 0

CanalaveCity_Harbor_EventScript_ToIronIsland::
	warp MAP_IRON_ISLAND, 2
	waitstate
	end

CanalaveCity_Harbor_EventScript_ToFullmoonIsland::
	warp MAP_FULLMOON_ISLAND, 0
	waitstate
	end

CanalaveCity_Harbor_EventScript_ToNewmoonIsland::
	warp MAP_NEWMOON_ISLAND, 0
	waitstate
	end
