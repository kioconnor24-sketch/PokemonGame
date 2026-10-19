#include "global.h"
#include "test/test.h"
#include "averon_transport.h"
#include "averon_region_save.h"
#include "averon_region_travel.h"
#include "heal_location.h"
#include "overworld.h"
#include "region_map.h"
#include "regions.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"

// Compile the exact production body under test-only names, substituting only
// its metadata lookup. Shared warp validation still checks the real linked
// map. This exercises invalid section metadata without creating a map, writing
// cartridge data, or adding a production dependency-injection interface.
static struct MapHeader sMetadataHeader;
static const struct MapHeader *const MetadataHeader(u16 group, u16 map)
{
    return &sMetadataHeader;
}

static bool32 MetadataPointValid(const struct AveronTransportPoint *point);
static bool32 MetadataBegin(const struct AveronTransportPoint *from,
                            const struct AveronTransportPoint *to, bool32 useSavedReturn);
#define Overworld_GetMapHeaderByGroupAndId MetadataHeader
#define AveronTransport_IsPointValid MetadataPointValid
#define AveronTransport_Begin MetadataBegin
#include "../src/averon_transport.c"
#undef AveronTransport_Begin
#undef AveronTransport_IsPointValid
#undef Overworld_GetMapHeaderByGroupAndId

TEST("Averon transport rejects invalid section metadata before Hoenn display fallback")
{
    const struct AveronTransportPoint point = {
        AVERON_SAVE_REGION_AVERON,
        {MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18},
    };
    u32 section = MAPSEC_NONE;
    PARAMETRIZE { section = MAPSEC_NONE; }
    PARAMETRIZE { section = MAPSEC_COUNT; } // first entry outside the current table
    PARAMETRIZE { section = 0xFD; }
    PARAMETRIZE { section = 0xFE; }
    PARAMETRIZE { section = 0xFF; }
    sMetadataHeader = *Overworld_GetMapHeaderByGroupAndId(point.warp.mapGroup, point.warp.mapNum);
    EXPECT(AveronRegion_IsWarpShapeValid(&point.warp));
    EXPECT(MetadataPointValid(&point));
    sMetadataHeader.regionMapSectionId = section;
    EXPECT_EQ(GetRegionForSectionId(section), REGION_HOENN);
    EXPECT(!MetadataPointValid(&point));
    EXPECT(!MetadataBegin(&point, &point, FALSE));
}
