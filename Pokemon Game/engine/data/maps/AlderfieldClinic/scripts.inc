AlderfieldClinic_MapScripts::
	map_script MAP_SCRIPT_ON_TRANSITION, AlderfieldClinic_OnTransition
	.byte 0
AlderfieldClinic_OnTransition:
	setrespawn HEAL_LOCATION_ALDERFIELD
	end
