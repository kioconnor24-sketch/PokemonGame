#include "global.h"
#include "test/test.h"
#include "battle_dynamax.h"
#include "battle_z_move.h"
#include "event_object_movement.h"
#include "item.h"
#include "load_save.h"
#include "pokedex.h"
#include "pokemon.h"
#include "save.h"
#include "gba/flash_internal.h"
#include "constants/event_objects.h"
#include "constants/form_change_types.h"
#include "constants/hold_effects.h"
#include "constants/items.h"

// Runtime integrity checks over every species this build enables. They read
// the compiled data the game itself uses, so a disabled form, a bad table
// entry or a missing sprite shows up here instead of as a crash in the field.
// Each test counts every problem, prints it to the mGBA log, then fails once.

static bool32 IsValidEnabledSpecies(u32 species)
{
    return species > SPECIES_NONE && species < NUM_SPECIES && IsSpeciesEnabled(species);
}

TEST("Averon every evolution of an enabled species leads to an enabled species")
{
    u32 bad = 0, edges = 0;
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct Evolution *evolutions = GetSpeciesEvolutions(species);
        if (evolutions == NULL)
            continue;
        for (u32 i = 0; evolutions[i].method != EVOLUTIONS_END; i++)
        {
            edges++;
            if (!IsValidEnabledSpecies(evolutions[i].targetSpecies))
            {
                DebugPrintf("evolution %S -> %u", GetSpeciesName(species), evolutions[i].targetSpecies);
                bad++;
            }
        }
    }
    DebugPrintf("evolution edges checked: %u", edges);
    EXPECT_GT(edges, 0);
    EXPECT_EQ(bad, 0);
}

// Excluded gimmicks may still list a form the build leaves out: Averon's
// battle rules block those changes (test/averon_battle_rules.c).
static bool32 IsExcludedGimmickFormChange(enum FormChanges method)
{
    switch (method)
    {
    case FORM_CHANGE_BATTLE_PRIMAL_REVERSION:
    case FORM_CHANGE_BATTLE_ULTRA_BURST:
    case FORM_CHANGE_BATTLE_GIGANTAMAX:
    case FORM_CHANGE_BATTLE_TERASTALLIZATION:
        return TRUE;
    default:
        return FALSE;
    }
}

TEST("Averon every allowed form change of an enabled species leads to an enabled species")
{
    u32 bad = 0, changes = 0;
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct FormChange *formChanges = GetSpeciesFormChanges(species);
        if (formChanges == NULL)
            continue;
        for (u32 i = 0; formChanges[i].method != FORM_CHANGE_TERMINATOR; i++)
        {
            changes++;
            // FAINT and END_BATTLE without a target revert to the form saved
            // before the battle change (form_change_types.h).
            if (formChanges[i].targetSpecies == SPECIES_NONE
             && (formChanges[i].method == FORM_CHANGE_FAINT || formChanges[i].method == FORM_CHANGE_END_BATTLE))
                continue;
            if (!IsValidEnabledSpecies(formChanges[i].targetSpecies) && !IsExcludedGimmickFormChange(formChanges[i].method))
            {
                DebugPrintf("form change %S -> %u (method %u)", GetSpeciesName(species), formChanges[i].targetSpecies, formChanges[i].method);
                bad++;
            }
        }
    }
    DebugPrintf("form changes checked: %u", changes);
    EXPECT_GT(changes, 0);
    EXPECT_EQ(bad, 0);
}

// GetSetPokedexFlag subtracts 1 from the number without a bounds check, so a
// species registered with dex number 0 or above NATIONAL_DEX_COUNT would write
// outside dexSeen/dexCaught in the save block.
TEST("Averon every enabled species has a national dex number inside the save's dex flags")
{
    u32 bad = 0;
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        u32 dexNum = SpeciesToNationalPokedexNum(species);
        if (dexNum == 0 || dexNum > NATIONAL_DEX_COUNT)
        {
            DebugPrintf("dex number %S = %u", GetSpeciesName(species), dexNum);
            bad++;
        }
    }
    EXPECT_GE(sizeof(gSaveBlock1Ptr->dexCaught) * 8, NATIONAL_DEX_COUNT);
    EXPECT_GE(sizeof(gSaveBlock1Ptr->dexSeen) * 8, NATIONAL_DEX_COUNT);
    EXPECT_EQ(bad, 0);
}

static u32 HashBytes(const void *data, u32 size)
{
    const u8 *bytes = data;
    u32 hash = 2166136261u;
    for (u32 i = 0; i < size; i++)
        hash = (hash ^ bytes[i]) * 16777619u;
    return hash;
}

// Hash of SaveBlock1 with the two dex flag arrays left out.
static u32 HashSaveBlock1OutsideDex(void)
{
    const u8 *start = (const u8 *)gSaveBlock1Ptr;
    const u8 *seen = gSaveBlock1Ptr->dexSeen, *caughtEnd = gSaveBlock1Ptr->dexCaught + sizeof(gSaveBlock1Ptr->dexCaught);
    EXPECT(seen + sizeof(gSaveBlock1Ptr->dexSeen) == gSaveBlock1Ptr->dexCaught);
    return HashBytes(start, seen - start) ^ HashBytes(caughtEnd, sizeof(struct SaveBlock1) - (caughtEnd - start));
}

TEST("Averon a complete national dex is counted, stays inside its flags and survives a flash save")
{
    u32 before, after;
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    ClearSaveData();
    Save_ResetSaveCounters();
    memset(gSaveBlock1Ptr->dexSeen, 0, sizeof(gSaveBlock1Ptr->dexSeen));
    memset(gSaveBlock1Ptr->dexCaught, 0, sizeof(gSaveBlock1Ptr->dexCaught));
    before = HashSaveBlock1OutsideDex();
    for (u32 dexNum = 1; dexNum <= NATIONAL_DEX_COUNT; dexNum++)
    {
        GetSetPokedexFlag(dexNum, FLAG_SET_SEEN);
        GetSetPokedexFlag(dexNum, FLAG_SET_CAUGHT);
    }
    after = HashSaveBlock1OutsideDex();
    EXPECT_EQ(before, after);
    EXPECT_EQ(GetNationalPokedexCount(FLAG_GET_SEEN), NATIONAL_DEX_COUNT);
    EXPECT_EQ(GetNationalPokedexCount(FLAG_GET_CAUGHT), NATIONAL_DEX_COUNT);
    EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
    memset(gSaveBlock1Ptr->dexSeen, 0, sizeof(gSaveBlock1Ptr->dexSeen));
    memset(gSaveBlock1Ptr->dexCaught, 0, sizeof(gSaveBlock1Ptr->dexCaught));
    EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
    EXPECT_EQ(GetNationalPokedexCount(FLAG_GET_CAUGHT), NATIONAL_DEX_COUNT);
    EXPECT_EQ(GetNationalPokedexCount(FLAG_GET_SEEN), NATIONAL_DEX_COUNT);
    memset(gSaveBlock1Ptr->dexSeen, 0, sizeof(gSaveBlock1Ptr->dexSeen));
    memset(gSaveBlock1Ptr->dexCaught, 0, sizeof(gSaveBlock1Ptr->dexCaught));
}

static bool32 IsValidLearnableMove(u32 move)
{
    return move > MOVE_NONE && move < MOVES_COUNT && !IsZMove(move) && !IsMaxMove(move);
}

TEST("Averon every enabled species learns only real, non-gimmick moves at valid levels")
{
    u32 bad = 0, moves = 0;
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct LevelUpMove *levelUp = GetSpeciesLevelUpLearnset(species);
        for (u32 i = 0; levelUp != NULL && levelUp[i].move != LEVEL_UP_MOVE_END; i++)
        {
            moves++;
            if (!IsValidLearnableMove(levelUp[i].move) || levelUp[i].level > MAX_LEVEL
             || (i > 0 && levelUp[i].level < levelUp[i - 1].level))
            {
                DebugPrintf("level-up %S: move %u at %u", GetSpeciesName(species), levelUp[i].move, levelUp[i].level);
                bad++;
            }
        }
        const u16 *teachable = GetSpeciesTeachableLearnset(species);
        for (u32 i = 0; teachable != NULL && teachable[i] != MOVE_UNAVAILABLE; i++)
        {
            moves++;
            if (!IsValidLearnableMove(teachable[i]))
            {
                DebugPrintf("teachable %S: move %u", GetSpeciesName(species), teachable[i]);
                bad++;
            }
        }
        const u16 *egg = GetSpeciesEggMoves(species);
        for (u32 i = 0; egg != NULL && egg[i] != MOVE_UNAVAILABLE; i++)
        {
            moves++;
            if (!IsValidLearnableMove(egg[i]))
            {
                DebugPrintf("egg %S: move %u", GetSpeciesName(species), egg[i]);
                bad++;
            }
        }
    }
    DebugPrintf("learnset entries checked: %u", moves);
    EXPECT_GT(moves, 0);
    EXPECT_EQ(bad, 0);
}

TEST("Averon every enabled species has valid types, abilities and nonzero base stats")
{
    u32 bad = 0;
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct SpeciesInfo *info = &gSpeciesInfo[species];
        bool32 ok = info->types[0] < NUMBER_OF_MON_TYPES && info->types[1] < NUMBER_OF_MON_TYPES
                 && info->baseHP > 0 && info->baseAttack > 0 && info->baseDefense > 0
                 && info->baseSpeed > 0 && info->baseSpAttack > 0 && info->baseSpDefense > 0
                 && info->abilities[0] != ABILITY_NONE;
        for (u32 slot = 0; slot < NUM_ABILITY_SLOTS; slot++)
            ok = ok && info->abilities[slot] < ABILITIES_COUNT;
        if (!ok)
        {
            DebugPrintf("species data %S (%u)", GetSpeciesName(species), species);
            bad++;
        }
    }
    EXPECT_EQ(bad, 0);
}

static bool32 IsValidSpriteSize(u32 pixels)
{
    return pixels == 16 || pixels == 32 || pixels == 64;
}

static bool32 IsUsableGraphicsInfo(const struct ObjectEventGraphicsInfo *info)
{
    return info != NULL && info->images != NULL && info->anims != NULL && info->oam != NULL
        && IsValidSpriteSize(info->width) && IsValidSpriteSize(info->height);
}

// Followers pack the species into the low 12 bits of a u16 graphics ID, next
// to the Pokemon, shiny and female bits.
TEST("Averon every species fits in a follower graphics ID")
{
    EXPECT_LE(NUM_SPECIES, OBJ_EVENT_MON_FEMALE);
    EXPECT_EQ(OBJ_EVENT_MON_FEMALE, 1u << 12);
}

// LoadDynamicFollowerPalette uses the overworld palettes only when the other
// one of the pair exists, then loads the one it needs: a species with only
// one of the two would load a NULL palette. Missing sprites fall back to the
// substitute placeholder (OW_SUBSTITUTE_PLACEHOLDER), which is counted.
TEST("Averon every enabled species has usable follower graphics and paired palettes")
{
    u32 bad = 0, placeholders = 0, checked = 0;
    const struct ObjectEventGraphicsInfo *placeholder = &gSpeciesInfo[SPECIES_NONE].overworldData;
    EXPECT(IsUsableGraphicsInfo(placeholder));
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct SpeciesInfo *info = &gSpeciesInfo[species];
        for (u32 female = FALSE; female <= TRUE; female++)
        {
            const struct ObjectEventGraphicsInfo *graphics = SpeciesToGraphicsInfo(species, FALSE, female);
            checked++;
            if (graphics == placeholder)
                placeholders++;
            if (!IsUsableGraphicsInfo(graphics))
            {
                DebugPrintf("follower graphics %S female=%u", GetSpeciesName(species), female);
                bad++;
            }
        }
        if ((info->overworldPalette == NULL) != (info->overworldShinyPalette == NULL))
        {
            DebugPrintf("follower palette pair %S", GetSpeciesName(species));
            bad++;
        }
    #if P_GENDER_DIFFERENCES
        if ((info->overworldPaletteFemale == NULL) != (info->overworldShinyPaletteFemale == NULL))
        {
            DebugPrintf("female follower palette pair %S", GetSpeciesName(species));
            bad++;
        }
    #endif
    }
    DebugPrintf("follower lookups: %u, placeholder: %u", checked, placeholders);
    EXPECT_EQ(bad, 0);
}

// Runs the game's own evolution check for every evolution that has no extra
// condition (gender, time, friendship, move, ...): a level evolution at its
// level, and an item evolution with its item.
TEST("Averon every unconditional level and item evolution actually triggers")
{
    u32 bad = 0, tested = 0, conditional = 0;
    struct Pokemon mon;
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct Evolution *evolutions = GetSpeciesEvolutions(species);
        if (evolutions == NULL)
            continue;
        for (u32 i = 0; evolutions[i].method != EVOLUTIONS_END; i++)
        {
            bool32 canStopEvo = TRUE;
            enum Species result;
            if (evolutions[i].params != NULL)
            {
                conditional++;
                continue;
            }
            if (evolutions[i].method == EVO_LEVEL)
            {
                if (evolutions[i].param < 1 || evolutions[i].param > MAX_LEVEL)
                {
                    DebugPrintf("evolution level %S: %u", GetSpeciesName(species), evolutions[i].param);
                    bad++;
                    continue;
                }
                CreateMon(&mon, species, evolutions[i].param, 0, OTID_STRUCT_PLAYER_ID);
                result = GetEvolutionTargetSpecies(&mon, EVO_MODE_NORMAL, ITEM_NONE, NULL, &canStopEvo, CHECK_EVO);
            }
            else if (evolutions[i].method == EVO_ITEM)
            {
                if (evolutions[i].param == ITEM_NONE || evolutions[i].param >= ITEMS_COUNT)
                {
                    DebugPrintf("evolution item %S: %u", GetSpeciesName(species), evolutions[i].param);
                    bad++;
                    continue;
                }
                CreateMon(&mon, species, 50, 0, OTID_STRUCT_PLAYER_ID);
                result = GetEvolutionTargetSpecies(&mon, EVO_MODE_ITEM_USE, evolutions[i].param, NULL, &canStopEvo, CHECK_EVO);
            }
            else
            {
                continue;
            }
            tested++;
            // Another, earlier evolution may win; it must still be a real one.
            if (!IsValidEnabledSpecies(result))
            {
                DebugPrintf("evolution did not trigger %S -> %u (method %u)", GetSpeciesName(species), evolutions[i].targetSpecies, evolutions[i].method);
                bad++;
            }
        }
    }
    DebugPrintf("evolutions run: %u, with extra conditions (not run): %u", tested, conditional);
    EXPECT_GT(tested, 0);
    EXPECT_EQ(bad, 0);
}

TEST("Averon every Mega Evolution by held stone uses a real Mega Stone")
{
    u32 bad = 0, megas = 0;
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct FormChange *formChanges = GetSpeciesFormChanges(species);
        for (u32 i = 0; formChanges != NULL && formChanges[i].method != FORM_CHANGE_TERMINATOR; i++)
        {
            if (formChanges[i].method != FORM_CHANGE_BATTLE_MEGA_EVOLUTION_ITEM)
                continue;
            megas++;
            if (formChanges[i].param1 == ITEM_NONE || formChanges[i].param1 >= ITEMS_COUNT
             || GetItemHoldEffect(formChanges[i].param1) != HOLD_EFFECT_MEGA_STONE
             || !IsValidEnabledSpecies(formChanges[i].targetSpecies))
            {
                DebugPrintf("mega %S item %u -> %u", GetSpeciesName(species), formChanges[i].param1, formChanges[i].targetSpecies);
                bad++;
            }
        }
    }
    DebugPrintf("mega stone form changes: %u", megas);
    EXPECT_GT(megas, 0);
    EXPECT_EQ(bad, 0);
}

// Level 100 is the maximum: the EXP tables must rise to it, fit the 21-bit
// box field, and extra EXP must not push a Pokemon past it.
TEST("Averon every growth rate reaches level 100 and stops there")
{
    struct Pokemon mon;
    for (u32 growth = GROWTH_MEDIUM_FAST; growth <= GROWTH_SLOW; growth++)
    {
        u32 species = SPECIES_NONE, exp;
        for (u32 candidate = SPECIES_NONE + 1; candidate < NUM_SPECIES && species == SPECIES_NONE; candidate++)
        {
            if (IsSpeciesEnabled(candidate) && candidate != SPECIES_EGG && gSpeciesInfo[candidate].growthRate == growth)
                species = candidate;
        }
        EXPECT_NE(species, SPECIES_NONE);
        for (u32 level = 2; level <= MAX_LEVEL; level++)
            EXPECT_GT(gExperienceTables[growth][level], gExperienceTables[growth][level - 1]);
        EXPECT_LT(gExperienceTables[growth][MAX_LEVEL], 1u << 21);
        CreateMon(&mon, species, MAX_LEVEL, 0, OTID_STRUCT_PLAYER_ID);
        EXPECT_EQ(GetMonData(&mon, MON_DATA_LEVEL), MAX_LEVEL);
        exp = gExperienceTables[growth][MAX_LEVEL] + 100000;
        SetMonData(&mon, MON_DATA_EXP, &exp);
        CalculateMonStats(&mon);
        EXPECT_EQ(GetMonData(&mon, MON_DATA_LEVEL), MAX_LEVEL);
    }
}
