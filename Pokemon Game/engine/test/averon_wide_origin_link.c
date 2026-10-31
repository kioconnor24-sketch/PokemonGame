#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "link.h"
#include "pokemon.h"
#include "constants/region_map_sections.h"

STATIC_ASSERT(sizeof(struct LinkPlayer) == 28, origin_link_player_abi_unchanged);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, origin_link_party_abi_unchanged);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, origin_link_box_abi_unchanged);

static void SetCompatiblePeer(u32 id)
{
    memset(&gLinkPlayers[id], 0, sizeof(gLinkPlayers[id]));
    gLinkPlayers[id].version = VERSION_EMERALD | 0x4000;
    gLinkPlayers[id].lp_field_2 = AVERON_ORIGIN_LINK_SIGNATURE;
    gLinkPlayers[id].neverRead = AVERON_ORIGIN_LINK_REVISION;
}

TEST("Averon origin link requires the exact compatible protocol without changing player ABI")
{
    u32 peer = GetMultiplayerId() ^ 1;
    struct LinkPlayer previous = gLinkPlayers[peer];
    SetCompatiblePeer(peer);
    EXPECT(AveronLink_PeerUsesWideOrigins(peer));
    gLinkPlayers[peer].lp_field_2 = 0x8000;
    EXPECT(!AveronLink_PeerUsesWideOrigins(peer));
    SetCompatiblePeer(peer);
    gLinkPlayers[peer].neverRead ^= 1;
    EXPECT(!AveronLink_PeerUsesWideOrigins(peer));
    SetCompatiblePeer(peer);
    gLinkPlayers[peer].version = VERSION_RUBY;
    EXPECT(!AveronLink_PeerUsesWideOrigins(peer));
    EXPECT(!AveronLink_PeerUsesWideOrigins(MAX_RFU_PLAYERS));
    gLinkPlayers[peer] = previous;
}

TEST("Averon origin link previews sanitize a copy and refuse legacy wide exports")
{
    struct Pokemon original, saved, preview;
    u32 peer = GetMultiplayerId() ^ 1;
    struct LinkPlayer previous = gLinkPlayers[peer];
    u16 wide = 0x2FD; // Its low byte must not become the special egg origin.
    AveronRegionSave_InitNewGame();
    CreateMon(&original, SPECIES_PIPLUP, 12, 7, OTID_STRUCT_PLAYER_ID);
    SetMonData(&original, MON_DATA_MET_LOCATION_EXTENDED, &wide);
    saved = original;
    memset(&gLinkPlayers[peer], 0, sizeof(gLinkPlayers[peer]));
    EXPECT(!AveronLink_CanExportMon(&original, peer));
    AveronLink_CopyPartyPreview(&preview, &original, 1, peer);
    EXPECT_EQ(GetMonData(&preview, MON_DATA_MET_LOCATION_EXTENDED), MAPSEC_NONE);
    EXPECT_EQ(GetMonData(&preview, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    EXPECT_EQ(memcmp(&original, &saved, sizeof(original)), 0);
    SetCompatiblePeer(peer);
    EXPECT(AveronLink_CanExportMon(&original, peer));
    AveronLink_CopyPartyPreview(&preview, &original, 1, peer);
    EXPECT_EQ(memcmp(&preview, &original, sizeof(preview)), 0);
    EXPECT_EQ(GetMonData(&preview, MON_DATA_MET_LOCATION_EXTENDED), wide);
    gLinkPlayers[peer] = previous;
}

TEST("Averon origin link legacy byte origins including exact specials export unchanged")
{
    struct Pokemon original, preview;
    u32 peer = GetMultiplayerId() ^ 1;
    struct LinkPlayer previous = gLinkPlayers[peer];
    AveronRegionSave_InitNewGame();
    memset(&gLinkPlayers[peer], 0, sizeof(gLinkPlayers[peer]));
    CreateMon(&original, SPECIES_PIPLUP, 12, 3, OTID_STRUCT_PLAYER_ID);
    for (u32 value = 0; value <= 0xFF; value++)
    {
        SetMonData(&original, MON_DATA_MET_LOCATION, &value);
        EXPECT(AveronLink_CanExportMon(&original, peer));
        AveronLink_CopyPartyPreview(&preview, &original, 1, peer);
        EXPECT_EQ(GetMonData(&preview, MON_DATA_MET_LOCATION_EXTENDED), value);
        EXPECT_EQ(memcmp(&preview, &original, sizeof(preview)), 0);
    }
    gLinkPlayers[peer] = previous;
}

TEST("Averon origin link normalizes only unknown remote origins and preserves self copies")
{
    struct Pokemon source, received;
    u32 self = GetMultiplayerId(), peer = self ^ 1;
    struct LinkPlayer previous = gLinkPlayers[peer], oldSelf = gLinkPlayers[self];
    u16 wide = 472;
    AveronRegionSave_InitNewGame();
    CreateMon(&source, SPECIES_PIPLUP, 12, 13, OTID_STRUCT_PLAYER_ID);
    SetMonData(&source, MON_DATA_MET_LOCATION_EXTENDED, &wide);
    memset(&gLinkPlayers[peer], 0, sizeof(gLinkPlayers[peer]));
    AveronLink_CopyReceivedParty(&received, &source, 1, peer);
    EXPECT_EQ(GetMonData(&received, MON_DATA_MET_LOCATION_EXTENDED), 216);
    EXPECT_EQ(GetMonData(&received, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    SetCompatiblePeer(peer);
    AveronLink_CopyReceivedParty(&received, &source, 1, peer);
    EXPECT_EQ(memcmp(&received, &source, sizeof(received)), 0);
    EXPECT_EQ(GetMonData(&received, MON_DATA_MET_LOCATION_EXTENDED), wide);
    // Our own send buffer is not an imported legacy mon, even before local
    // peer metadata has been filled in a multiplayer exchange.
    memset(&gLinkPlayers[self], 0, sizeof(gLinkPlayers[self]));
    AveronLink_CopyReceivedParty(&received, &source, 1, self);
    EXPECT_EQ(memcmp(&received, &source, sizeof(received)), 0);
    gLinkPlayers[peer] = previous;
    gLinkPlayers[self] = oldSelf;
}
