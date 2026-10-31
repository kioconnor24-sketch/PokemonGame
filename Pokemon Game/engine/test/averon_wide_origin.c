#include "global.h"
#include "test/test.h"
#include "averon_region_save.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "save.h"
#include "tv.h"
#include "malloc.h"
#include "gba/flash_internal.h"
#include "recorded_battle.h"

STATIC_ASSERT(sizeof(struct BoxPokemon) == 80, wide_origin_box_size);
STATIC_ASSERT(sizeof(struct Pokemon) == 100, wide_origin_party_size);
STATIC_ASSERT(sizeof(((struct PokemonSubstruct3 *)0)->metLocation) == 1, wide_origin_low_byte);

TEST("Averon wide origin keeps all 24 encrypted permutations low-byte specials and PC identities")
{
    static const u16 locations[] = {0,215,216,238,252,253,254,255,256,0x1fd,0x1fe,0x1ff,0x1234,8191};
    AveronRegionSave_InitNewGame();
    for (u32 permutation = 0; permutation < 24; permutation++)
    {
        for (u32 i = 0; i < ARRAY_COUNT(locations); i++)
        {
            struct BoxPokemon box;
            struct Pokemon mon;
            u16 location = locations[i];
            CreateBoxMon(&box, SPECIES_PIPLUP, 12, permutation, OTID_STRUCT_PRESET(0x12345678));
            SetBoxMonData(&box, MON_DATA_MET_LOCATION_EXTENDED, &location);
            EXPECT_EQ(GetBoxMonData(&box, MON_DATA_MET_LOCATION_EXTENDED), location);
            EXPECT_EQ(GetBoxMonData(&box, MON_DATA_MET_LOCATION), location & 0xFF);
            SetBoxMonAt(0, 0, &box);
            BoxMonAtToMon(0, 0, &mon);
            SetBoxMonOtIdKeepingData(&mon.box, 0x87654321);
            UpdateMonPersonality(&mon.box, permutation + 25);
            EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION_EXTENDED), location);
            EXPECT_EQ(GetMonData(&mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
        }
    }
}

TEST("Averon wide origin old byte setters clear extension bits and invalid extended setters preserve data")
{
    struct Pokemon mon;
    u16 location = 0x1FD;
    u8 byte = 216;
    AveronRegionSave_InitNewGame();
    CreateMon(&mon, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    SetMonData(&mon, MON_DATA_MET_LOCATION_EXTENDED, &location);
    EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION_EXTENDED), 0x1FD);
    SetMonData(&mon, MON_DATA_MET_LOCATION, &byte);
    EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION_EXTENDED), 216);
    struct Pokemon prior = mon;
    location = 8192;
    SetMonData(&mon, MON_DATA_MET_LOCATION_EXTENDED, &location);
    EXPECT_EQ(memcmp(&mon, &prior, sizeof(mon)), 0);
}

TEST("Averon wide origin legacy normalization preserves byte meanings and never repairs a corrupt checksum")
{
    struct Pokemon mon;
    u16 ambiguous = 216 + 256;
    AveronRegionSave_InitNewGame();
    CreateMon(&mon, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    SetMonData(&mon, MON_DATA_MET_LOCATION_EXTENDED, &ambiguous);
    NormalizeMonLegacyOrigin(&mon);
    EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION_EXTENDED), 216);
    EXPECT_EQ(GetMonData(&mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    SetMonData(&mon, MON_DATA_MET_LOCATION_EXTENDED, &ambiguous);
    mon.box.checksum ^= 1;
    struct Pokemon corrupt = mon;
    NormalizeMonLegacyOrigin(&mon);
    EXPECT_EQ(memcmp(&mon, &corrupt, sizeof(mon)), 0);
}

TEST("Averon wide origin upgrade normalizes every persisted legacy container before format 2 reads")
{
    struct Pokemon mon;
    u16 ambiguous = 216 + 256;
    AveronRegionSave_InitNewGame();
    CreateMon(&mon, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    SetMonData(&mon, MON_DATA_MET_LOCATION_EXTENDED, &ambiguous);
    gSaveBlock1Ptr->playerParty[PARTY_SIZE - 1] = mon;
    gPokemonStoragePtr->boxes[TOTAL_BOXES_COUNT - 1][IN_BOX_COUNT - 1] = mon.box;
    gSaveBlock1Ptr->daycare.mons[DAYCARE_MON_COUNT - 1].mon = mon.box;
#if IS_FRLG
    gSaveBlock1Ptr->route5DayCareMon.mon = mon.box;
#endif
    gPokemonStoragePtr->fusions[MAX_FUSION_STORAGE - 1] = mon;
    // A validated format-1 load has arbitrary checksum-valid old unused bits.
    // This fixture calls the real RAM migration boundary; flash validation and
    // interrupted-save behavior remain covered by the region-save fixtures.
    gSaveBlock3Ptr->averonRegionRecord[4] = 1;
    gSaveBlock3Ptr->averonRegionRecord[5] = 0;
    memcpy(gSaveBlock2Ptr->averonRegionAnchor, "AVRS", 4);
    gSaveBlock2Ptr->averonRegionAnchor[4] = 1;
    gSaveBlock2Ptr->averonRegionAnchor[5] = 0;
    gSaveBlock2Ptr->averonRegionAnchor[6] = 0xFE;
    gSaveBlock2Ptr->averonRegionAnchor[7] = 0xFF;
    AveronRegionSave_BeginLoad();
    EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION_EXTENDED), 216);
    AveronRegionSave_FinishLoad(SAVE_STATUS_OK);
    EXPECT(AveronRegionSave_UsesWideOrigins());
    EXPECT_EQ(GetMonData(&gSaveBlock1Ptr->playerParty[PARTY_SIZE - 1], MON_DATA_MET_LOCATION_EXTENDED), 216);
    EXPECT_EQ(GetBoxMonData(&gPokemonStoragePtr->boxes[TOTAL_BOXES_COUNT - 1][IN_BOX_COUNT - 1], MON_DATA_MET_LOCATION_EXTENDED), 216);
    EXPECT_EQ(GetBoxMonData(&gSaveBlock1Ptr->daycare.mons[DAYCARE_MON_COUNT - 1].mon, MON_DATA_MET_LOCATION_EXTENDED), 216);
#if IS_FRLG
    EXPECT_EQ(GetBoxMonData(&gSaveBlock1Ptr->route5DayCareMon.mon, MON_DATA_MET_LOCATION_EXTENDED), 216);
#endif
    EXPECT_EQ(GetMonData(&gPokemonStoragePtr->fusions[MAX_FUSION_STORAGE - 1], MON_DATA_MET_LOCATION_EXTENDED), 216);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_LEGACY_MIGRATED);
}

TEST("Averon wide origin TV policy refuses a byte-truncated location without changing saved ABI")
{
    u16 prior = gMapHeader.regionMapSectionId;
    gMapHeader.regionMapSectionId = 0x1FD;
    gSaveBlock1Ptr->gabbyAndTyData.mapnum = 216;
    gSaveBlock1Ptr->gabbyAndTyData.onAir = TRUE;
    GabbyAndTyAfterInterview();
    EXPECT_EQ(gSaveBlock1Ptr->gabbyAndTyData.mapnum, 216);
    EXPECT_EQ(gSaveBlock1Ptr->gabbyAndTyData.onAir, FALSE);
    gMapHeader.regionMapSectionId = prior;
}

static struct SaveSector *PrepareLegacyOriginFlash(void)
{
    CheckForFlashMemory();
    EXPECT(gFlashMemoryPresent);
    ClearSaveData();
    Save_ResetSaveCounters();
    AveronRegionSave_InitNewGame();
    ZeroPlayerPartyMons();
    CreateMon(&gParties[B_TRAINER_PLAYER][0], SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    u16 ambiguous = 216 + 256;
    SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION_EXTENDED, &ambiguous);
    gPokemonStoragePtr->boxes[0][0] = gParties[B_TRAINER_PLAYER][0].box;
    CalculatePlayerPartyCount();
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    struct SaveSector *sector = Alloc(sizeof(*sector));
    u32 physical;
    for (physical = (gSaveCounter % NUM_SAVE_SLOTS) * NUM_SECTORS_PER_SLOT;
         physical < ((gSaveCounter % NUM_SAVE_SLOTS) + 1) * NUM_SECTORS_PER_SLOT; physical++)
    {
        ReadFlash(physical, 0, (u8 *)sector, sizeof(*sector));
        if (sector->id == SECTOR_ID_SAVEBLOCK2)
            break;
    }
    EXPECT_EQ(sector->id, SECTOR_ID_SAVEBLOCK2);
    u8 *anchor = &sector->data[offsetof(struct SaveBlock2, averonRegionAnchor)];
    u8 *record = &sector->saveBlock3Chunk[offsetof(struct SaveBlock3, averonRegionRecord)];
    anchor[4] = record[4] = 1;
    anchor[5] = record[5] = 0;
    anchor[6] = 0xFE;
    anchor[7] = 0xFF;
    u32 crc = AveronRegionSave_RecordCrc(record);
    for (u32 i = 0; i < 4; i++)
        record[12 + i] = crc >> (8 * i);
    u32 checksum = 0;
    for (u32 i = 0; i < sizeof(struct SaveBlock2) / 4; i++)
        checksum += ((u32 *)sector->data)[i];
    sector->checksum = (checksum >> 16) + checksum;
    EraseFlashSector(physical);
    ProgramFlashSector(physical, (u8 *)sector);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_LEGACY_MIGRATED);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION_EXTENDED), 216);
    EXPECT_EQ(gSaveBlock3Ptr->averonRegionRecord[4], 2);
    return sector;
}

TEST("Averon wide origin validated format 1 flash save upgrades to 2 without reinterpreting old unused bits")
{
    struct SaveSector *sector = PrepareLegacyOriginFlash();
    EXPECT_EQ(GetBoxMonData(&gPokemonStoragePtr->boxes[0][0], MON_DATA_MET_LOCATION_EXTENDED), 216);
    EXPECT(AveronRegionSave_RequiresFullOriginSave());
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT(!AveronRegionSave_RequiresFullOriginSave());
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(AveronRegionSave_GetLoadIssue(), AVERON_REGION_LOAD_OK);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION_EXTENDED), 216);
    EXPECT_EQ(GetBoxMonData(&gPokemonStoragePtr->boxes[0][0], MON_DATA_MET_LOCATION_EXTENDED), 216);
    Free(sector);
}

TEST("Averon wide origin partial link and ereader saves commit migrated PC data with format 2")
{
    const u8 modes[] = {SAVE_LINK, SAVE_EREADER};
    for (u32 i = 0; i < ARRAY_COUNT(modes); i++)
    {
        struct SaveSector *sector = PrepareLegacyOriginFlash();
        EXPECT(AveronRegionSave_RequiresFullOriginSave());
        EXPECT_EQ(TrySavingData(modes[i]), SAVE_STATUS_OK);
        EXPECT(!AveronRegionSave_RequiresFullOriginSave());
        EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
        EXPECT_EQ(GetBoxMonData(&gPokemonStoragePtr->boxes[0][0], MON_DATA_MET_LOCATION_EXTENDED), 216);
        Free(sector);
    }
}

TEST("Averon wide origin direct incremental save cannot seal an unmigrated PC slot")
{
    struct SaveSector *sector = PrepareLegacyOriginFlash();
    EXPECT(WriteSaveBlock1Sector());
    EXPECT_EQ(gSaveAttemptStatus, SAVE_STATUS_ERROR);
    EXPECT(AveronRegionSave_RequiresFullOriginSave());
    EXPECT(!WriteSaveBlock2());
    EXPECT(!AveronRegionSave_RequiresFullOriginSave());
    bool32 finished = FALSE;
    for (u32 i = 0; i < 8 && !finished; i++)
        finished = WriteSaveBlock1Sector();
    EXPECT(finished);
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(GetBoxMonData(&gPokemonStoragePtr->boxes[0][0], MON_DATA_MET_LOCATION_EXTENDED), 216);
    Free(sector);
}

TEST("Averon wide origin recorded legacy copies normalize without changing the recording")
{
    AveronRegionSave_InitNewGame();
    struct RecordedBattleSave *record = AllocZeroed(sizeof(*record));
    struct Pokemon mon;
    CreateMon(&mon, SPECIES_PIPLUP, 12, 0, OTID_STRUCT_PLAYER_ID);
    u16 ambiguous = 216 + 256;
    SetMonData(&mon, MON_DATA_MET_LOCATION_EXTENDED, &ambiguous);
    record->parties[B_TRAINER_PLAYER][0] = mon;
    SetPartiesFromRecordedSave(record);
    EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_MET_LOCATION_EXTENDED), 216);
    EXPECT_EQ(memcmp(&record->parties[B_TRAINER_PLAYER][0], &mon, sizeof(mon)), 0);
    EXPECT(RecordedBattle_CanPersistOrigins());
    gParties[B_TRAINER_PLAYER][0] = mon;
    EXPECT(!RecordedBattle_CanPersistOrigins());
    EXPECT(!MoveRecordedBattleToSaveData());
    Free(record);
}
