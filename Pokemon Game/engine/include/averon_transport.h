#ifndef GUARD_AVERON_TRANSPORT_H
#define GUARD_AVERON_TRANSPORT_H

#include "global.h"

// ROM/caller data only: no saved point IDs, flags, vehicle or story policy.
// region uses AVERON_SAVE_REGION_*, not the engine's enum Region.
struct AveronTransportPoint
{
    u32 region;
    struct WarpData warp;
};

bool32 AveronTransport_IsPointValid(const struct AveronTransportPoint *point);

// Departure is an exact coordinate activation point (warpId == WARP_ID_NONE).
// Arrival may use valid coordinates or an indexed map warp. The caller chooses
// first arrival (FALSE) versus the target's stored last departure (TRUE).
// Reject wrong-region endpoints, source position/active-region mismatches,
// missing/invalid saved returns and mismatched target healers before invoking
// the existing atomic region-travel transaction. Caller performs the fade/warp.
// Does not check collision, unlock a route, run a story script or certify that
// an arbitrary point is safe for a player; those are content/graphical gates.
bool32 AveronTransport_Begin(const struct AveronTransportPoint *departure,
                            const struct AveronTransportPoint *arrival,
                            bool32 useSavedReturn);

#endif
