#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "battle.h"
#include "battle_controllers.h"
#include "load_save.h"
#include "malloc.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "region_map.h"
#include "regions.h"
#include "save.h"
#include "string_util.h"
#include "gba/flash_internal.h"
#include "constants/characters.h"
#include "constants/heal_locations.h"
#include "constants/maps.h"

// Freeze ALL old identifiers, including upstream/debug locations, not only
// the six naturally reachable Averon values. Nothing here allocates IDs.
#define LEGACY_LOCATION(symbol, value, name) STATIC_ASSERT(symbol == value, symbol##_legacy_value_moved);
#include "data/averon_legacy_location_ids.inc"
#undef LEGACY_LOCATION
STATIC_ASSERT(MAPSEC_NONE == 215, legacy_none_moved);
STATIC_ASSERT(METLOC_SPECIAL_EGG == 0xFD, legacy_egg_moved);
STATIC_ASSERT(METLOC_IN_GAME_TRADE == 0xFE, legacy_trade_moved);
STATIC_ASSERT(METLOC_FATEFUL_ENCOUNTER == 0xFF, legacy_fateful_moved);
STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, box_format_changed);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, party_format_changed);
STATIC_ASSERT(offsetof(struct BoxPokemon, secure) == 32, encrypted_data_offset_changed);
STATIC_ASSERT(sizeof(((struct PokemonSubstruct3 *)0)->metLocation) == 1, met_width_changed);
STATIC_ASSERT(sizeof(((struct MapHeader *)0)->regionMapSectionId) == 1, runtime_header_width_changed);

static const struct {u16 id; const u8 *name;} sLegacySectionNames[] = {
#define LEGACY_LOCATION(symbol, value, name) {symbol, name},
#include "data/averon_legacy_location_ids.inc"
#undef LEGACY_LOCATION
};

TEST("Averon location legacy names and region identities remain unchanged")
{
    for (u32 section = 0; section <= 0xFF; section++)
    {
        bool32 sinnoh = section == MAPSEC_SANDGEM_TOWN || section == MAPSEC_ROUTE_201 || section == MAPSEC_TWINLEAF_TOWN
            || section == MAPSEC_ROUTE_202 || section == MAPSEC_LAKE_VERITY || section == MAPSEC_JUBILIFE_CITY || section == MAPSEC_ROUTE_203 || section == MAPSEC_OREBURGH_GATE || section == MAPSEC_ROUTE_204 || section == MAPSEC_FLOAROMA_TOWN || section == MAPSEC_ROUTE_205;
        EXPECT_EQ(IsRegionMapSectionIdValid(section), section < 215 || sinnoh);
        EXPECT_EQ(GetRegionForSectionId(section), sinnoh ? REGION_SINNOH : section >= KANTO_MAPSEC_START && section < MAPSEC_SPECIAL_AREA
            ? REGION_KANTO : REGION_HOENN);
    }
    EXPECT_EQ(IsRegionMapSectionIdValid(0x100), FALSE);
    EXPECT_EQ(IsRegionMapSectionIdValid(0xFFFF), FALSE);
    EXPECT_EQ(IsRegionMapSectionIdValid(0xFFFFFFFF), FALSE);
    EXPECT_EQ(GetRegionForSectionId(0xFFFFFFFF), REGION_HOENN);
    static const struct {u16 id; const u8 *name;} names[] = {
        {MAPSEC_SALTMERE, COMPOUND_STRING("SALTMERE")},
        {MAPSEC_COASTAL_MEADOW, COMPOUND_STRING("COASTAL MEADOW")},
        {MAPSEC_WINDROW, COMPOUND_STRING("WINDROW HAMLET")},
        {MAPSEC_ORCHARD_LANE, COMPOUND_STRING("ORCHARD LANE")},
        {MAPSEC_ALDERFIELD, COMPOUND_STRING("ALDERFIELD")},
        {MAPSEC_COASTAL_BLUFFS, COMPOUND_STRING("COASTAL BLUFFS")},
    };
    EXPECT_EQ(ARRAY_COUNT(sLegacySectionNames), 215);
    for (u32 i = 0; i < ARRAY_COUNT(sLegacySectionNames); i++)
        EXPECT_EQ(StringCompare(gRegionMapEntries[sLegacySectionNames[i].id].name, sLegacySectionNames[i].name), 0);
    u8 name[64];
    for (u32 i = 0; i < ARRAY_COUNT(names); i++)
    {
        GetMapNameHandleAquaHideout(name, names[i].id);
        EXPECT_EQ(StringCompare(name, names[i].name), 0);
    }
    for (u32 section = MAPSEC_NONE; section <= 0xFF; section++)
    {
        if (section == MAPSEC_SANDGEM_TOWN || section == MAPSEC_ROUTE_201 || section == MAPSEC_TWINLEAF_TOWN
         || section == MAPSEC_ROUTE_202 || section == MAPSEC_LAKE_VERITY || section == MAPSEC_JUBILIFE_CITY || section == MAPSEC_ROUTE_203 || section == MAPSEC_OREBURGH_GATE || section == MAPSEC_ROUTE_204 || section == MAPSEC_FLOAROMA_TOWN || section == MAPSEC_ROUTE_205)
            continue; // the owner-approved ordinary codes (216 Sandgem, 217 Route 201, 218 Twinleaf, 219 Route 202, 220 Lake Verity, 221 Jubilife, 222 Route 203, 223 Oreburgh Gate, 224 Route204/Ravaged Path, 225 Floaroma/Meadow, 226 Route205)
        GetMapName(name, section, 0);
        for (u32 i = 0; i < 18; i++)
            EXPECT_EQ(name[i], CHAR_SPACE);
        EXPECT_EQ(name[18], EOS);
    }
    // The persisted region record is a different namespace, never inferred
    // from section IDs (and never used to relabel a Pokemon's origin).
    AveronRegionSave_InitNewGame();
    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH));
    gMapHeader.regionMapSectionId = MAPSEC_SALTMERE;
    EXPECT_EQ(GetCurrentRegion(), REGION_HOENN);
    EXPECT_EQ(AveronRegion_GetActive(), AVERON_SAVE_REGION_SINNOH);
}

TEST("Averon location every 8-bit origin survives encryption PC withdrawal and rekeying")
{
    struct BoxPokemon box, deposited;
    struct Pokemon party;
    for (u32 value = 0; value <= 0xFF; value++)
    {
        CreateBoxMon(&box, SPECIES_PIPLUP, 12, value, OTID_STRUCT_PRESET(0x12345678));
        SetBoxMonData(&box, MON_DATA_MET_LOCATION, &value);
        u32 originGame = VERSION_EMERALD;
        SetBoxMonData(&box, MON_DATA_MET_GAME, &originGame);
        deposited = box;
        EXPECT_EQ(GetBoxMonData(&box, MON_DATA_MET_LOCATION), value);
        EXPECT_EQ(memcmp(&box, &deposited, sizeof(box)), 0); // getter re-encrypts
        SetBoxMonAt(0, 0, &box);
        BoxMonToMon(GetBoxedMonPtr(0, 0), &party);
        EXPECT_EQ(GetMonData(&party, MON_DATA_MET_LOCATION), value);
        EXPECT_EQ(GetMonData(&party, MON_DATA_MET_GAME), VERSION_EMERALD);
        EXPECT_EQ(GetMonData(&party, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
        // Actual production helper reshuffles all four encrypted substructs.
        UpdateMonPersonality(&party.box, value + 13);
        EXPECT_EQ(GetMonData(&party, MON_DATA_MET_LOCATION), value);
        EXPECT_EQ(GetMonData(&party, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
        SetBoxMonOtIdKeepingData(&party.box, 0x87654321);
        EXPECT_EQ(GetMonData(&party, MON_DATA_MET_LOCATION), value);
        EXPECT_EQ(GetMonData(&party, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    }
}

// TEST-ONLY option-C experiment. No new MON_DATA field or production encoding
// is adopted. Personality modulo24=0 uses substruct1 at slot1; the deliberate
// restriction prevents claiming full permutation/consumer support.
static void PrototypeCrypt(struct BoxPokemon *box)
{
    for (u32 i = 0; i < ARRAY_COUNT(box->secure.raw); i++)
        box->secure.raw[i] ^= box->personality ^ box->otId;
}

static void PrototypeWrite13(struct BoxPokemon *box, u16 value)
{
    EXPECT_EQ(box->personality % 24, 0);
    EXPECT(value < 8192);
    u32 low = value & 0xFF;
    SetBoxMonData(box, MON_DATA_MET_LOCATION, &low);
    PrototypeCrypt(box);
    box->secure.substructs[1].type1.unused_04 = value >> 8;
    u32 checksum = 0;
    for (u32 i = 0; i < ARRAY_COUNT(box->secure.raw); i++)
        checksum += box->secure.raw[i] + (box->secure.raw[i] >> 16);
    box->checksum = checksum;
    PrototypeCrypt(box);
}

static u16 PrototypeRead13(const struct BoxPokemon *box)
{
    struct BoxPokemon plain = *box;
    EXPECT_EQ(plain.personality % 24, 0);
    PrototypeCrypt(&plain);
    return plain.secure.substructs[3].type3.metLocation
        | (plain.secure.substructs[1].type1.unused_04 << 8);
}

TEST("Averon location 13-bit experiment exposes legacy API truncation and special aliases")
{
    struct BoxPokemon box;
    struct Pokemon party;
    u32 code = 0x1234;
    CreateBoxMon(&box, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PRESET(0x12345678));
    SetBoxMonData(&box, MON_DATA_MET_LOCATION, &code);
    EXPECT_EQ(GetBoxMonData(&box, MON_DATA_MET_LOCATION), 0x34);
    // Setting the old field alone is NOT a 16-bit or 13-bit implementation.
    EXPECT_EQ(PrototypeRead13(&box), 0x34);
    PrototypeWrite13(&box, code);
    EXPECT_EQ(PrototypeRead13(&box), code);
    EXPECT_EQ(GetBoxMonData(&box, MON_DATA_MET_LOCATION), 0x34);
    EXPECT_EQ(GetBoxMonData(&box, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    BoxMonToMon(&box, &party);
    EXPECT_EQ(PrototypeRead13(&party.box), code);
    EXPECT_EQ(GetMonData(&party, MON_DATA_MET_LOCATION), 0x34);
    PrototypeWrite13(&box, 0x1FD);
    EXPECT_EQ(PrototypeRead13(&box), 0x1FD);
    EXPECT_EQ(GetBoxMonData(&box, MON_DATA_MET_LOCATION), METLOC_SPECIAL_EGG);
    for (u32 special = METLOC_SPECIAL_EGG; special <= METLOC_FATEFUL_ENCOUNTER; special++)
    {
        PrototypeWrite13(&box, special);
        EXPECT_EQ(PrototypeRead13(&box), special);
        EXPECT_EQ(GetBoxMonData(&box, MON_DATA_MET_LOCATION), special);
    }
    static const u16 boundaries[] = {0, 215, 216, 252, 255, 256, 511, 8191};
    for (u32 i = 0; i < ARRAY_COUNT(boundaries); i++)
    {
        PrototypeWrite13(&box, boundaries[i]);
        EXPECT_EQ(PrototypeRead13(&box), boundaries[i]);
        EXPECT_EQ(GetBoxMonData(&box, MON_DATA_MET_LOCATION), boundaries[i] & 0xFF);
        EXPECT_EQ(GetBoxMonData(&box, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    }
}

static u32 sControllerCompletions;
static void CompleteLocationController(enum BattlerId battler)
{
    EXPECT_EQ(battler, 0);
    sControllerCompletions++;
}

TEST("Averon location battle controller preserves all legacy bytes but not a new 13-bit identity")
{
    struct BattleResources *previous = gBattleResources;
    gBattleResources = AllocZeroed(sizeof(*gBattleResources));
    EXPECT(gBattleResources != NULL);
    if (gBattleResources == NULL)
    {
        gBattleResources = previous;
        return;
    }
    u32 previousFlags = gBattleTypeFlags;
    void (*previousEnd)(enum BattlerId) = gBattlerControllerEndFuncs[0];
    u32 previousPosition = gBattlerPositions[0], previousPartyIndex = gBattlerPartyIndexes[0];
    gBattleTypeFlags = 0;
    gBattlerPositions[0] = B_POSITION_PLAYER_LEFT;
    gBattlerPartyIndexes[0] = 0;
    gBattlerControllerEndFuncs[0] = CompleteLocationController;
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PRESET(0x12345678));
    for (u32 value = 0; value <= 0xFF; value++)
    {
        SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION, &value);
        memset(gBattleResources->bufferB[0], 0xA5, sizeof(gBattleResources->bufferB[0]));
        sControllerCompletions = 0;
        BtlController_EmitGetMonData(0, B_COMM_TO_CONTROLLER, REQUEST_MET_LOCATION_BATTLE, 0);
        BtlController_HandleGetMonData(0);
        EXPECT_EQ(gBattleResources->bufferB[0][2], 1);
        EXPECT_EQ(gBattleResources->bufferB[0][3], 0);
        EXPECT_EQ(gBattleResources->bufferB[0][4], value);
        EXPECT_EQ(gBattleResources->bufferB[0][5], 0xA5);
        u8 received = gBattleResources->bufferB[0][4];
        u32 other = value ^ 0xFF;
        SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION, &other);
        BtlController_EmitSetMonData(0, B_COMM_TO_CONTROLLER, REQUEST_MET_LOCATION_BATTLE, 0, 1, &received);
        BtlController_HandleSetMonData(0);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION), value);
        EXPECT_EQ(sControllerCompletions, 2);
    }
    PrototypeWrite13(&gParties[B_TRAINER_PLAYER][0].box, 0x1234);
    BtlController_EmitGetMonData(0, B_COMM_TO_CONTROLLER, REQUEST_MET_LOCATION_BATTLE, 0);
    BtlController_HandleGetMonData(0);
    u8 received = gBattleResources->bufferB[0][4];
    EXPECT_EQ(received, 0x34);
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PRESET(0x12345678));
    BtlController_EmitSetMonData(0, B_COMM_TO_CONTROLLER, REQUEST_MET_LOCATION_BATTLE, 0, 1, &received);
    BtlController_HandleSetMonData(0);
    EXPECT_EQ(PrototypeRead13(&gParties[B_TRAINER_PLAYER][0].box), 0x34);
    // Completion callback is a fixture, payload generation/handling is real.
    gBattlerControllerEndFuncs[0] = previousEnd;
    gBattlerPositions[0] = previousPosition;
    gBattlerPartyIndexes[0] = previousPartyIndex;
    gBattleTypeFlags = previousFlags;
    Free(gBattleResources);
    gBattleResources = previous;
}

struct LocationSnapshot
{
    struct PokemonStorage storage;
    struct Pokemon party[PARTY_SIZE];
    TVShow tv[TV_SHOWS_COUNT];
    struct AveronRegionState region;
};

TEST("Averon location flash reload preserves all 256 PC origins party TV specials and region state")
{
    bool32 specialParty = FALSE;
    PARAMETRIZE { specialParty = FALSE; }
    PARAMETRIZE { specialParty = TRUE; }
    static const u8 specials[PARTY_SIZE] = {215, 216, 252, 0xFD, 0xFE, 0xFF};
    CheckForFlashMemory();
    EXPECT(gFlashMemoryPresent);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    ResetPokemonStorageSystem();
    ZeroPlayerPartyMons();
    for (u32 i = 0; i < PARTY_SIZE; i++)
    {
        CreateMon(&gParties[B_TRAINER_PLAYER][i], SPECIES_PIPLUP, 12, i, OTID_STRUCT_PRESET(0x12345678));
        u32 value = specialParty ? specials[i] : 209 + i;
        SetMonData(&gParties[B_TRAINER_PLAYER][i], MON_DATA_MET_LOCATION, &value);
    }
    CalculatePlayerPartyCount();
    for (u32 value = 0; value <= 0xFF; value++)
    {
        struct BoxPokemon *box = GetBoxedMonPtr(value / IN_BOX_COUNT, value % IN_BOX_COUNT);
        CreateBoxMon(box, SPECIES_PIPLUP, 12, value, OTID_STRUCT_PRESET(0x12345678));
        SetBoxMonData(box, MON_DATA_MET_LOCATION, &value);
    }
    // Two isolated candidate-C payloads share the SAME current physical save
    // format; raw survival is tested separately from absent semantic support.
    struct BoxPokemon *extended = GetBoxedMonPtr(256 / IN_BOX_COUNT, 256 % IN_BOX_COUNT);
    CreateBoxMon(extended, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PRESET(0x12345678));
    PrototypeWrite13(extended, 0x1234);
    struct BoxPokemon *alias = GetBoxedMonPtr(257 / IN_BOX_COUNT, 257 % IN_BOX_COUNT);
    CreateBoxMon(alias, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PRESET(0x12345678));
    PrototypeWrite13(alias, 0x1FD);
    memset(gSaveBlock1Ptr->tvShows, 0, sizeof(gSaveBlock1Ptr->tvShows));
    gSaveBlock1Ptr->tvShows[0].smartshopperShow.shopLocation = 209;
    gSaveBlock1Ptr->tvShows[1].pokemonTodayFailed.location = 215;
    gSaveBlock1Ptr->tvShows[2].worldOfMasters.location = 0xFD;
    gSaveBlock1Ptr->tvShows[3].rivalTrainer.location = 0xFE;
    gSaveBlock1Ptr->tvShows[4].treasureInvestigators.location = 0xFF;
    gSaveBlock1Ptr->tvShows[5].breakingNews.location = 214;
    EXPECT(AveronRegion_SetActive(AVERON_SAVE_REGION_SINNOH));
    EXPECT(AveronRegion_SetBadge(AVERON_SAVE_REGION_SINNOH, 3, TRUE));
    struct WarpData warp = {MAP_GROUP(MAP_SALTMERE), MAP_NUM(MAP_SALTMERE), WARP_ID_NONE, 18, 18};
    EXPECT(AveronRegion_SetReturnWarp(AVERON_SAVE_REGION_SINNOH, &warp));
    EXPECT(AveronRegion_SetHealLocation(AVERON_SAVE_REGION_SINNOH, HEAL_LOCATION_ALDERFIELD));
    struct LocationSnapshot *expected = AllocZeroed(sizeof(*expected));
    EXPECT(expected != NULL);
    if (expected == NULL)
        return;
    expected->storage = *gPokemonStoragePtr;
    memcpy(expected->party, gParties[B_TRAINER_PLAYER], sizeof(expected->party));
    memcpy(expected->tv, gSaveBlock1Ptr->tvShows, sizeof(expected->tv));
    EXPECT(AveronRegionSave_GetState(&expected->region));
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    // Genuine flash reload after destroying the corresponding live RAM.
    memset(gPokemonStoragePtr, 0, sizeof(*gPokemonStoragePtr));
    ZeroPlayerPartyMons();
    memset(gSaveBlock1Ptr->tvShows, 0, sizeof(gSaveBlock1Ptr->tvShows));
    AveronRegionSave_InitNewGame();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(gPartiesCount[B_TRAINER_PLAYER], PARTY_SIZE);
    EXPECT_EQ(memcmp(&expected->storage, gPokemonStoragePtr, sizeof(expected->storage)), 0);
    EXPECT_EQ(memcmp(expected->party, gParties[B_TRAINER_PLAYER], sizeof(expected->party)), 0);
    EXPECT_EQ(memcmp(expected->tv, gSaveBlock1Ptr->tvShows, sizeof(expected->tv)), 0);
    struct AveronRegionState observed = {0};
    EXPECT(AveronRegionSave_GetState(&observed));
    EXPECT_EQ(memcmp(&expected->region, &observed, sizeof(observed)), 0);
    for (u32 value = 0; value <= 0xFF; value++)
    {
        struct BoxPokemon *box = GetBoxedMonPtr(value / IN_BOX_COUNT, value % IN_BOX_COUNT);
        EXPECT_EQ(GetBoxMonData(box, MON_DATA_MET_LOCATION), value);
        EXPECT_EQ(GetBoxMonData(box, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    }
    extended = GetBoxedMonPtr(256 / IN_BOX_COUNT, 256 % IN_BOX_COUNT);
    alias = GetBoxedMonPtr(257 / IN_BOX_COUNT, 257 % IN_BOX_COUNT);
    EXPECT_EQ(PrototypeRead13(extended), 0x1234);
    EXPECT_EQ(PrototypeRead13(alias), 0x1FD);
    EXPECT_EQ(GetBoxMonData(alias, MON_DATA_MET_LOCATION), METLOC_SPECIAL_EGG);
    Free(expected);
}
