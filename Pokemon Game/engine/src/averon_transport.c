#include "global.h"
#include "averon_transport.h"
#include "averon_region_save.h"
#include "averon_region_travel.h"
#include "heal_location.h"
#include "overworld.h"
#include "region_map.h"
#include "regions.h"
#include "constants/heal_locations.h"

bool32 AveronTransport_IsPointValid(const struct AveronTransportPoint *point)
{
    if (point == NULL
        || (point->region != AVERON_SAVE_REGION_AVERON && point->region != AVERON_SAVE_REGION_SINNOH)
        || !AveronRegion_IsWarpShapeValid(&point->warp))
        return FALSE;
    const struct MapHeader *header = Overworld_GetMapHeaderByGroupAndId(point->warp.mapGroup, point->warp.mapNum);
    // GetRegionForSectionId deliberately falls back to Hoenn for unknown IDs.
    // A display fallback must not authorize a configured transport endpoint.
    if (!IsRegionMapSectionIdValid(header->regionMapSectionId))
        return FALSE;
    u32 expected = point->region == AVERON_SAVE_REGION_AVERON ? REGION_HOENN : REGION_SINNOH;
    return GetRegionForSectionId(header->regionMapSectionId) == expected;
}

bool32 AveronTransport_Begin(const struct AveronTransportPoint *departure,
                            const struct AveronTransportPoint *arrival,
                            bool32 useSavedReturn)
{
    if (!AveronTransport_IsPointValid(departure) || !AveronTransport_IsPointValid(arrival)
        || departure->region == arrival->region || departure->warp.warpId != WARP_ID_NONE
        || AveronRegion_GetActive() != departure->region
        || gSaveBlock1Ptr->location.mapGroup != departure->warp.mapGroup
        || gSaveBlock1Ptr->location.mapNum != departure->warp.mapNum
        || gSaveBlock1Ptr->pos.x != departure->warp.x || gSaveBlock1Ptr->pos.y != departure->warp.y)
        return FALSE;

    struct AveronTransportPoint destination = *arrival;
    if (useSavedReturn
        && (!AveronRegion_GetReturnWarp(arrival->region, &destination.warp)
            || !AveronTransport_IsPointValid(&destination)))
        return FALSE;

    // BeginTravel caches a recognized departing healer. Refuse an inconsistent
    // source now, rather than storing a wrong-region healer that blocks return.
    if (GetHealLocationIndexByWarpData(&gSaveBlock1Ptr->lastHealLocation) != HEAL_LOCATION_NONE)
    {
        struct AveronTransportPoint healer = {departure->region, gSaveBlock1Ptr->lastHealLocation};
        if (!AveronTransport_IsPointValid(&healer))
            return FALSE;
    }

    u32 healIndex = AveronRegion_GetHealLocation(arrival->region);
    if (healIndex != HEAL_LOCATION_NONE)
    {
        const struct HealLocation *heal = GetHealLocation(healIndex);
        if (heal == NULL)
            return FALSE;
        struct AveronTransportPoint healer = {
            .region = arrival->region,
            .warp = {heal->mapGroup, heal->mapNum, WARP_ID_NONE, heal->x, heal->y},
        };
        if (!AveronTransport_IsPointValid(&healer))
            return FALSE;
    }
    return AveronRegion_BeginTravel(arrival->region, &destination.warp);
}
