#ifndef GUARD_REGIONS_H
#define GUARD_REGIONS_H

#include "global.h"
#include "constants/regions.h"

enum KantoSubRegion GetKantoSubregion(u32 mapSecId);

enum Region GetRegionForSectionId(u32 sectionId);

// Only regions with an implemented Town Map/Fly grid may open those UIs.
// Explicit future regions must not inherit another region's destinations.
bool32 IsRegionMapAvailableForSection(u32 sectionId);

static inline enum Region GetCurrentRegion(void)
{
    return GetRegionForSectionId(gMapHeader.regionMapSectionId);
}

#endif // GUARD_REGIONS_H
