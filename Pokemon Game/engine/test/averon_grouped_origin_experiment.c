#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "load_save.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "pokemon_summary_screen.h"
#include "save.h"
#include "string_util.h"
#include "constants/region_map_sections.h"

// TEST-only proposal, not a production codebook or allocation. These wide
// runtime identities do not name or register maps. Sharing the approved216
// byte is an isolated example of loss of detail, not an approved grouping.
#define TEST_DETAIL_A 0x1234
#define TEST_DETAIL_B 0x1235

static bool32 CandidateGroupedOrigin(u32 detail, u8 *origin)
{
    if (detail <= 0xFF) // never reinterpret any saved legacy/special byte
        *origin = detail;
    else if (detail == TEST_DETAIL_A || detail == TEST_DETAIL_B)
        *origin = MAPSEC_SANDGEM_TOWN;
    else
        return FALSE;
    return TRUE;
}

TEST("Averon grouped origin experiment preserves all legacy bytes without modifying encryption")
{
    struct Pokemon seed, mon, restored;
    u8 origin = 0xA5;
    CreateMon(&seed, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    for (u32 detail = 0; detail <= 255; ++detail)
    {
        mon = seed;
        EXPECT(CandidateGroupedOrigin(detail, &origin));
        EXPECT_EQ(origin, detail);
        u32 value = origin;
        SetMonData(&mon, MON_DATA_MET_LOCATION, &value);
        BoxMonToMon(&mon.box, &restored);
        EXPECT_EQ(GetMonData(&restored, MON_DATA_MET_LOCATION), detail);
        EXPECT_EQ(GetMonData(&restored, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
        EXPECT_EQ(memcmp(&mon.box, &restored.box, sizeof(mon.box)), 0);
    }
    origin = 0xA5;
    EXPECT(!CandidateGroupedOrigin(256, &origin));
    EXPECT(!CandidateGroupedOrigin(0xFFFF, &origin));
    EXPECT(!CandidateGroupedOrigin(0x10000, &origin));
    EXPECT_EQ(origin, 0xA5); // failed lookup cannot silently assign a default
}

TEST("Averon grouped origin experiment loses distinct runtime detail across real PC flash and summary")
{
    struct Pokemon seed;
    struct BoxPokemon expected;
    u8 a, b, text[1024];
    u32 value, memoCrc;
    CheckForFlashMemory();
    EXPECT(gFlashMemoryPresent);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
    AveronRegionSave_InitNewGame();
    StringCopy(gSaveBlock2Ptr->playerName, COMPOUND_STRING("CODEX"));
    gSaveBlock2Ptr->playerGender = MALE;
    CreateMon(&seed, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    EXPECT(TEST_DETAIL_A != TEST_DETAIL_B);
    EXPECT(CandidateGroupedOrigin(TEST_DETAIL_A, &a));
    EXPECT(CandidateGroupedOrigin(TEST_DETAIL_B, &b));
    EXPECT_EQ(a, b);
    value = a;
    SetMonData(&seed, MON_DATA_MET_LOCATION, &value);
    value = VERSION_EMERALD;
    SetMonData(&seed, MON_DATA_MET_GAME, &value);
    ZeroPlayerPartyMons();
    gParties[B_TRAINER_PLAYER][0] = seed;
    gParties[B_TRAINER_PLAYER][1] = seed;
    value = b;
    SetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_MET_LOCATION, &value);
    CalculatePlayerPartyCount();
    expected = seed.box;
    gPokemonStoragePtr->boxes[0][0] = gParties[B_TRAINER_PLAYER][0].box;
    gPokemonStoragePtr->boxes[0][1] = gParties[B_TRAINER_PLAYER][1].box;
    EXPECT_EQ(memcmp(&gPokemonStoragePtr->boxes[0][0], &gPokemonStoragePtr->boxes[0][1], sizeof(expected)), 0);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    ZeroPlayerPartyMons();
    memset(&gPokemonStoragePtr->boxes[0][0], 0, 2 * sizeof(expected));
    Save_ResetSaveCounters();
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(gPartiesCount[B_TRAINER_PLAYER], 2);
    for (u32 slot = 0; slot < 2; ++slot)
    {
        EXPECT_EQ(memcmp(&gPokemonStoragePtr->boxes[0][slot], &expected, sizeof(expected)), 0);
        EXPECT_EQ(GetBoxMonData(&gPokemonStoragePtr->boxes[0][slot], MON_DATA_MET_LOCATION), MAPSEC_SANDGEM_TOWN);
        EXPECT_EQ(GetBoxMonData(&gPokemonStoragePtr->boxes[0][slot], MON_DATA_SANITY_IS_BAD_EGG), FALSE);
        EXPECT(TestSummaryBufferTrainerMemo(&gParties[B_TRAINER_PLAYER][slot], text));
        u32 crc = AveronRegionSave_Crc32(text, StringLength(text));
        if (slot == 0)
            memoCrc = crc;
        else
            EXPECT_EQ(crc, memoCrc);
    }
    // Both complete encrypted boxes and their actual summary text are
    // identical: no decoder can recover which original detail was used.
    // This is the proposed grouping's deliberate precision cost, not a bug
    // in the current byte format. #134 separately proves 13-bit hazards.
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_BeginLoad();
}
