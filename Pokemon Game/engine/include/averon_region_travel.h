#ifndef GUARD_AVERON_REGION_TRAVEL_H
#define GUARD_AVERON_REGION_TRAVEL_H

// Moving the player between Averon and Sinnoh. Uses the region record in
// averon_region_save.c; no maps, flags or vars of its own.
//
// AveronRegion_BeginTravel validates everything first and changes nothing on
// failure. On success it:
//   - stores where the player stands as the departing region's return warp,
//     and the departing region's last heal location;
//   - makes the target region active;
//   - points the whiteout/Teleport heal warp at the target's stored heal
//     location, or at the arrival point if the player hasn't healed there;
//   - points the Escape Rope/Dig warp at the arrival point;
//   - sets the warp destination. The caller performs the warp (WarpIntoMap
//     or a script warp with a fade).
// arrival NULL means "go back to where the player left the target region".

bool32 AveronRegion_BeginTravel(u32 targetRegion, const struct WarpData *arrival);

// Script special. Reads VAR_0x8004 = target region (1 Averon, 2 Sinnoh) and,
// when VAR_0x8005 != 0xFFFF, the arrival VAR_0x8005 group, VAR_0x8006 map,
// VAR_0x8007 warp, VAR_0x8008 x, VAR_0x8009 y. Sets VAR_RESULT TRUE/FALSE.
void AveronRegion_BeginTravelSpecial(void);

#endif // GUARD_AVERON_REGION_TRAVEL_H
