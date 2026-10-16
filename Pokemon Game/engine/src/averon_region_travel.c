#include "global.h"
#include "averon_region_save.h"
#include "averon_region_travel.h"
#include "event_data.h"
#include "heal_location.h"
#include "overworld.h"
#include "constants/heal_locations.h"

bool32 AveronRegion_BeginTravel(u32 targetRegion, const struct WarpData *arrival)
{
    u32 current = AveronRegion_GetActive();
    u32 departingHeal, targetHeal;
    struct WarpData here, destination;

    if (targetRegion != AVERON_SAVE_REGION_AVERON && targetRegion != AVERON_SAVE_REGION_SINNOH)
        return FALSE;
    if (current == AVERON_SAVE_REGION_NONE || targetRegion == current)
        return FALSE;
    if (arrival != NULL)
        destination = *arrival;
    else if (!AveronRegion_GetReturnWarp(targetRegion, &destination))
        return FALSE; // never been there: the caller must name an arrival
    if (!AveronRegion_IsWarpShapeValid(&destination))
        return FALSE;
    here.mapGroup = gSaveBlock1Ptr->location.mapGroup;
    here.mapNum = gSaveBlock1Ptr->location.mapNum;
    here.warpId = WARP_ID_NONE;
    here.x = gSaveBlock1Ptr->pos.x;
    here.y = gSaveBlock1Ptr->pos.y;
    if (!AveronRegion_IsWarpShapeValid(&here))
        return FALSE;

    // Everything is valid; nothing has changed yet.
    departingHeal = GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation);
    if (departingHeal >= NUM_HEAL_LOCATIONS)
        departingHeal = HEAL_LOCATION_NONE;
    AveronRegion_SetReturnWarp(current, &here);
    AveronRegion_SetHealLocation(current, departingHeal);
    AveronRegion_SetActive(targetRegion);

    targetHeal = AveronRegion_GetHealLocation(targetRegion);
    if (targetHeal != HEAL_LOCATION_NONE)
        SetLastHealLocationWarp(targetHeal);
    else
        gSaveBlock1Ptr->lastHealLocation = destination;
    gSaveBlock1Ptr->escapeWarp = destination;
    SetWarpDestination(destination.mapGroup, destination.mapNum, destination.warpId, destination.x, destination.y);
    return TRUE;
}

void AveronRegion_BeginTravelSpecial(void)
{
    struct WarpData arrival;
    if (gSpecialVar_0x8005 == 0xFFFF)
    {
        gSpecialVar_Result = AveronRegion_BeginTravel(gSpecialVar_0x8004, NULL);
        return;
    }
    // Reject values that would wrap when narrowed to WarpData's s8 fields.
    if (gSpecialVar_0x8005 > 127 || gSpecialVar_0x8006 > 127
     || ((s16)gSpecialVar_0x8007 < -1 || (s16)gSpecialVar_0x8007 > 127))
    {
        gSpecialVar_Result = FALSE;
        return;
    }
    arrival.mapGroup = gSpecialVar_0x8005;
    arrival.mapNum = gSpecialVar_0x8006;
    arrival.warpId = (s16)gSpecialVar_0x8007;
    arrival.x = (s16)gSpecialVar_0x8008;
    arrival.y = (s16)gSpecialVar_0x8009;
    gSpecialVar_Result = AveronRegion_BeginTravel(gSpecialVar_0x8004, &arrival);
}
