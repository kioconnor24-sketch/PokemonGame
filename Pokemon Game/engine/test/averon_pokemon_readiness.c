#include "global.h"
#include "test/battle.h"
#include "battle_dynamax.h"
#include "caps.h"
#include "event_data.h"
#include "battle_z_move.h"
#include "event_object_movement.h"
#include "item.h"
#include "load_save.h"
#include "move.h"
#include "overworld.h"
#include "rtc.h"
#include "pokedex.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "regions.h"
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

// Averon's maps all report REGION_HOENN (GetRegionForSectionId knows only
// Kanto and Hoenn), and its maps are not the upstream Hoenn maps. An
// evolution gated on another region or on an upstream map can never happen.
// This lists every target species reachable ONLY through such evolutions:
// those need another source (gift, wild, trade) chosen by the owner.
static bool32 IsEvolutionPossibleInAveron(const struct Evolution *evolution)
{
    for (u32 i = 0; evolution->params != NULL && evolution->params[i].condition != CONDITIONS_END; i++)
    {
        const struct EvolutionParam *param = &evolution->params[i];
        if (param->condition == IF_REGION && param->arg1 != REGION_HOENN)
            return FALSE;
        if (param->condition == IF_IN_MAP || param->condition == IF_IN_MAPSEC)
            return FALSE;
    }
    return TRUE;
}

// Recorded 2026-10-16. A change here means the data changed: review it, then
// update the list and POKEMON_READINESS.md.
static const u16 sEvolutionOnlyElsewhere[] =
{
    SPECIES_URSALUNA,
    SPECIES_RAICHU_ALOLA,
    SPECIES_EXEGGUTOR_ALOLA,
    SPECIES_MAROWAK_ALOLA,
    SPECIES_WEEZING_GALAR,
    SPECIES_MR_MIME_GALAR,
    SPECIES_TYPHLOSION_HISUI,
    SPECIES_SAMUROTT_HISUI,
    SPECIES_LILLIGANT_HISUI,
    SPECIES_BRAVIARY_HISUI,
    SPECIES_SLIGGOO_HISUI,
    SPECIES_AVALUGG_HISUI,
    SPECIES_DECIDUEYE_HISUI,
};

// Whether any evolution that can happen in Averon leads to target.
static bool32 HasPossibleEvolutionInto(u32 target)
{
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct Evolution *evolutions = GetSpeciesEvolutions(species);
        for (u32 i = 0; evolutions != NULL && evolutions[i].method != EVOLUTIONS_END; i++)
        {
            if (evolutions[i].targetSpecies == target && evolutions[i].method != EVO_NONE
             && IsEvolutionPossibleInAveron(&evolutions[i]))
                return TRUE;
        }
    }
    return FALSE;
}

TEST("Averon lists the evolution targets that only another region or an upstream map can reach")
{
    u32 blocked = 0, listed = 0;
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct Evolution *evolutions = GetSpeciesEvolutions(species);
        for (u32 i = 0; evolutions != NULL && evolutions[i].method != EVOLUTIONS_END; i++)
        {
            u32 target = evolutions[i].targetSpecies;
            bool32 known = FALSE, firstEdge = TRUE;
            // EVO_NONE is not an evolution; count each blocked target once,
            // at its first blocked edge.
            if (evolutions[i].method == EVO_NONE || IsEvolutionPossibleInAveron(&evolutions[i])
             || !IsValidEnabledSpecies(target) || HasPossibleEvolutionInto(target))
                continue;
            for (u32 j = 0; j < i; j++)
                firstEdge = firstEdge && !(evolutions[j].targetSpecies == target && evolutions[j].method != EVO_NONE);
            if (!firstEdge)
                continue;
            for (u32 k = 0; k < ARRAY_COUNT(sEvolutionOnlyElsewhere); k++)
                known = known || sEvolutionOnlyElsewhere[k] == target;
            DebugPrintf("evolution-only-elsewhere: %S (%u)%s", GetSpeciesName(target), target, known ? "" : " NEW");
            blocked++;
            listed += known;
        }
    }
    DebugPrintf("targets reachable only through another region or upstream map: %u", blocked);
    EXPECT_EQ(blocked, ARRAY_COUNT(sEvolutionOnlyElsewhere));
    EXPECT_EQ(listed, ARRAY_COUNT(sEvolutionOnlyElsewhere));
}

// Conditional evolutions whose conditions depend only on the Pokemon itself
// (gender, friendship, a known move or move type, a held item), on the time of
// day (set with SetTimeOfDay), or are already true in Averon (not in another
// region). Weather, party, map, step and battle-record conditions are left out
// and counted.
static bool32 CanSatisfyFromMonData(const struct EvolutionParam *params)
{
    for (u32 i = 0; params[i].condition != CONDITIONS_END; i++)
    {
        switch (params[i].condition)
        {
        case IF_GENDER:
        case IF_MIN_FRIENDSHIP:
        case IF_KNOWS_MOVE:
        case IF_KNOWS_MOVE_TYPE:
        case IF_HOLD_ITEM:
        case IF_TIME:
        case IF_NOT_TIME:
            break;
        case IF_NOT_REGION:
            if (params[i].arg1 == REGION_HOENN)
                return FALSE;
            break;
        default:
            return FALSE;
        }
    }
    return TRUE;
}

// Sets an hour (1-23; 0 turns the override off) that meets every time
// condition. Returns FALSE if none does.
static bool32 SetHourForTimeConditions(const struct EvolutionParam *params)
{
    for (u32 hour = 1; hour < HOURS_PER_DAY; hour++)
    {
        bool32 ok = TRUE;
        SetTimeOfDay(hour);
        for (u32 i = 0; params[i].condition != CONDITIONS_END; i++)
        {
            if (params[i].condition == IF_TIME)
                ok = ok && GetTimeOfDay() == params[i].arg1;
            else if (params[i].condition == IF_NOT_TIME)
                ok = ok && GetTimeOfDay() != params[i].arg1;
        }
        if (ok)
            return TRUE;
    }
    SetTimeOfDay(0);
    return FALSE;
}

static u32 PersonalityForGender(u32 species, u32 gender)
{
    for (u32 personality = 0; personality < 256; personality++)
    {
        if (GetGenderFromSpeciesAndPersonality(species, personality) == gender)
            return personality;
    }
    return 0;
}

static enum Move AnyMoveOfType(u32 type)
{
    for (enum Move move = MOVE_NONE + 1; move < MOVES_COUNT; move++)
    {
        if (GetMoveType(move) == type && IsValidLearnableMove(move))
            return move;
    }
    return MOVE_NONE;
}

TEST("Averon every conditional evolution satisfiable from the Pokemon's own data triggers")
{
    u32 bad = 0, tested = 0, skipped = 0;
    struct Pokemon mon;
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct Evolution *evolutions = GetSpeciesEvolutions(species);
        for (u32 i = 0; evolutions != NULL && evolutions[i].method != EVOLUTIONS_END; i++)
        {
            const struct Evolution *evo = &evolutions[i];
            const struct EvolutionParam *params = evo->params;
            enum EvolutionMode mode;
            u32 level = 50, personality = 0, item = ITEM_NONE;
            bool32 canStopEvo = TRUE;
            if (params == NULL)
                continue;
            if (!CanSatisfyFromMonData(params)
             || (evo->method != EVO_LEVEL && evo->method != EVO_ITEM && evo->method != EVO_TRADE)
             || !SetHourForTimeConditions(params))
            {
                skipped++;
                continue;
            }
            if (evo->method == EVO_LEVEL)
            {
                mode = EVO_MODE_NORMAL;
                level = evo->param == 0 ? 50 : evo->param;
            }
            else if (evo->method == EVO_ITEM)
            {
                mode = EVO_MODE_ITEM_USE;
                item = evo->param;
            }
            else
            {
                mode = EVO_MODE_TRADE;
            }
            for (u32 j = 0; params[j].condition != CONDITIONS_END; j++)
            {
                if (params[j].condition == IF_GENDER)
                    personality = PersonalityForGender(species, params[j].arg1);
            }
            CreateMon(&mon, species, level, personality, OTID_STRUCT_PLAYER_ID);
            for (u32 j = 0; params[j].condition != CONDITIONS_END; j++)
            {
                u32 value = params[j].arg1;
                switch (params[j].condition)
                {
                case IF_MIN_FRIENDSHIP:
                    value = MAX_FRIENDSHIP;
                    SetMonData(&mon, MON_DATA_FRIENDSHIP, &value);
                    break;
                case IF_KNOWS_MOVE:
                    SetMonData(&mon, MON_DATA_MOVE1, &value);
                    break;
                case IF_KNOWS_MOVE_TYPE:
                    value = AnyMoveOfType(value);
                    SetMonData(&mon, MON_DATA_MOVE1, &value);
                    break;
                case IF_HOLD_ITEM:
                    SetMonData(&mon, MON_DATA_HELD_ITEM, &value);
                    break;
                default:
                    break;
                }
            }
            tested++;
            enum Species result = GetEvolutionTargetSpecies(&mon, mode, item, NULL, &canStopEvo, CHECK_EVO);
            SetTimeOfDay(0);
            if (!IsValidEnabledSpecies(result))
            {
                DebugPrintf("conditional evolution did not trigger %S -> %S (method %u)", GetSpeciesName(species), GetSpeciesName(evo->targetSpecies), evo->method);
                bad++;
            }
        }
    }
    DebugPrintf("conditional evolutions run: %u, left out: %u", tested, skipped);
    EXPECT_GT(tested, 0);
    EXPECT_EQ(bad, 0);
}

// Every species and form, packed into PC boxes, written to flash, cleared,
// read back. Values are derived from the species ID, so nothing is stored.
static u32 TestPersonality(u32 species) { return species * 2654435761u; }
static u32 TestHeldItem(u32 species)    { return 1 + species % (ITEMS_COUNT - 1); }
static u32 TestLevel(u32 species)       { return 1 + species % MAX_LEVEL; }
static u32 TestMove(u32 species)        { return 1 + species % (MOVES_COUNT - 1); }

static u32 NextEnabledSpecies(u32 species)
{
    do
        species++;
    while (species < NUM_SPECIES && (!IsSpeciesEnabled(species) || species == SPECIES_EGG));
    return species;
}

TEST("Averon every enabled species survives the PC boxes and a flash save and load")
{
    u32 bad = 0, stored = 0, rounds = 0;
    u32 first = NextEnabledSpecies(SPECIES_NONE);
    struct BoxPokemon boxMon;
    CheckForFlashMemory();
    EXPECT_EQ(gFlashMemoryPresent, TRUE);
    if (!gFlashMemoryPresent)
        return;
    while (first < NUM_SPECIES)
    {
        u32 species = first, slot;
        ClearSaveData();
        Save_ResetSaveCounters();
        for (slot = 0; slot < TOTAL_BOXES_COUNT * IN_BOX_COUNT && species < NUM_SPECIES; slot++, species = NextEnabledSpecies(species))
        {
            u32 item = TestHeldItem(species), move = TestMove(species);
            CreateBoxMon(&boxMon, species, TestLevel(species), TestPersonality(species), OTID_STRUCT_PLAYER_ID);
            SetBoxMonData(&boxMon, MON_DATA_HELD_ITEM, &item);
            SetBoxMonData(&boxMon, MON_DATA_MOVE1, &move);
            SetBoxMonAt(slot / IN_BOX_COUNT, slot % IN_BOX_COUNT, &boxMon);
        }
        EXPECT_EQ(TrySavingData(SAVE_NORMAL), SAVE_STATUS_OK);
        for (u32 i = 0; i < slot; i++)
            ZeroBoxMonAt(i / IN_BOX_COUNT, i % IN_BOX_COUNT);
        EXPECT_EQ(LoadGameSave(SAVE_NORMAL), SAVE_STATUS_OK);
        species = first;
        for (u32 i = 0; i < slot; i++, species = NextEnabledSpecies(species))
        {
            struct BoxPokemon *loaded = GetBoxedMonPtr(i / IN_BOX_COUNT, i % IN_BOX_COUNT);
            CreateBoxMon(&boxMon, species, TestLevel(species), TestPersonality(species), OTID_STRUCT_PLAYER_ID);
            if (GetBoxMonData(loaded, MON_DATA_SANITY_IS_BAD_EGG)
             || GetBoxMonData(loaded, MON_DATA_SPECIES) != species
             || GetBoxMonData(loaded, MON_DATA_PERSONALITY) != TestPersonality(species)
             || GetBoxMonData(loaded, MON_DATA_HELD_ITEM) != TestHeldItem(species)
             || GetBoxMonData(loaded, MON_DATA_MOVE1) != TestMove(species)
             || GetBoxMonData(loaded, MON_DATA_EXP) != GetBoxMonData(&boxMon, MON_DATA_EXP)
             || GetBoxMonData(loaded, MON_DATA_ABILITY_NUM) != GetBoxMonData(&boxMon, MON_DATA_ABILITY_NUM))
            {
                DebugPrintf("box round trip %S (%u)", GetSpeciesName(species), species);
                bad++;
            }
            stored++;
        }
        first = species;
        rounds++;
    }
    for (u32 i = 0; i < TOTAL_BOXES_COUNT * IN_BOX_COUNT; i++)
        ZeroBoxMonAt(i / IN_BOX_COUNT, i % IN_BOX_COUNT);
    DebugPrintf("species stored and reloaded: %u in %u saves", stored, rounds);
    EXPECT_GT(rounds, 1);
    EXPECT_EQ(bad, 0);
}

static bool32 IsBattleOnlyFormChange(enum FormChanges method)
{
    switch (method)
    {
    case FORM_CHANGE_BEGIN_BATTLE:
    case FORM_CHANGE_BATTLE_SWITCH_IN:
    case FORM_CHANGE_BATTLE_HP_PERCENT_TURN_END:
    case FORM_CHANGE_BATTLE_HP_PERCENT_SEND_OUT:
    case FORM_CHANGE_BATTLE_HP_PERCENT_DURING_MOVE:
    case FORM_CHANGE_BATTLE_MEGA_EVOLUTION_ITEM:
    case FORM_CHANGE_BATTLE_MEGA_EVOLUTION_MOVE:
    case FORM_CHANGE_BATTLE_PRIMAL_REVERSION:
    case FORM_CHANGE_BATTLE_WEATHER:
    case FORM_CHANGE_BATTLE_TURN_END:
    case FORM_CHANGE_BATTLE_ULTRA_BURST:
    case FORM_CHANGE_BATTLE_GIGANTAMAX:
    case FORM_CHANGE_BATTLE_HIT_BY_MOVE_CATEGORY:
    case FORM_CHANGE_BATTLE_HIT_BY_CONFUSION_SELF_DMG:
    case FORM_CHANGE_BATTLE_TERASTALLIZATION:
    case FORM_CHANGE_BATTLE_BEFORE_MOVE:
    case FORM_CHANGE_BATTLE_AFTER_MOVE:
    case FORM_CHANGE_BATTLE_BOND:
    case FORM_CHANGE_BATTLE_BEFORE_MOVE_CATEGORY:
        return TRUE;
    default:
        return FALSE;
    }
}

static bool32 HasEndBattleRevert(u32 species)
{
    const struct FormChange *formChanges = GetSpeciesFormChanges(species);
    for (u32 i = 0; formChanges != NULL && formChanges[i].method != FORM_CHANGE_TERMINATOR; i++)
    {
        if (formChanges[i].method == FORM_CHANGE_END_BATTLE)
            return TRUE;
    }
    return FALSE;
}

// After battle, TryRevertPartyMonFormChange applies FORM_CHANGE_END_BATTLE to
// each party Pokemon. A form reached only in battle without that entry would
// stay in the party, and as the follower, after the battle.
TEST("Averon every form reached in battle has an end-of-battle revert")
{
    u32 bad = 0, battleForms = 0;
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (!IsSpeciesEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct FormChange *formChanges = GetSpeciesFormChanges(species);
        for (u32 i = 0; formChanges != NULL && formChanges[i].method != FORM_CHANGE_TERMINATOR; i++)
        {
            u32 target = formChanges[i].targetSpecies;
            if (!IsBattleOnlyFormChange(formChanges[i].method) || target == species || !IsValidEnabledSpecies(target))
                continue;
            // A change back to the base form (first in the form table) is
            // itself the revert, e.g. Gulping Cramorant to Cramorant.
            if (GetSpeciesFormTable(target) != NULL && GetSpeciesFormTable(target)[0] == target)
                continue;
            battleForms++;
            if (!HasEndBattleRevert(target))
            {
                DebugPrintf("no end-of-battle revert: %S (%u) from %S, method %u", GetSpeciesName(target), target, GetSpeciesName(species), formChanges[i].method);
                bad++;
            }
        }
    }
    DebugPrintf("battle form changes checked: %u", battleForms);
    EXPECT_GT(battleForms, 0);
    EXPECT_EQ(bad, 0);
}

SINGLE_BATTLE_TEST("Averon a Mega Evolved Pokemon is back in its base form in the party after battle")
{
    GIVEN {
        PLAYER(SPECIES_VENUSAUR) { Item(ITEM_VENUSAURITE); Speed(100); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_WOBBUFFET) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE, gimmick: GIMMICK_MEGA); }
    } SCENE {
        ANIMATION(ANIM_TYPE_GENERAL, B_ANIM_MEGA_EVOLUTION, player);
        MESSAGE("The opposing Wobbuffet fainted!");
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_SPECIES), SPECIES_VENUSAUR);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HELD_ITEM), ITEM_VENUSAURITE);
    }
}

// The last cap lifts with FLAG_IS_CHAMPION; after that only MAX_LEVEL limits
// growth. The cap values themselves are a design decision and not tested.
static const u16 sCapFlags[] =
{
    FLAG_BADGE01_GET, FLAG_BADGE02_GET, FLAG_BADGE03_GET, FLAG_BADGE04_GET,
    FLAG_BADGE05_GET, FLAG_BADGE06_GET, FLAG_BADGE07_GET, FLAG_BADGE08_GET,
    FLAG_AVERON_ASSAULT_COMPLETE, FLAG_IS_CHAMPION,
};

WILD_BATTLE_TEST("Averon with every level cap lifted a Pokemon grows to level 100 and no further")
{
    u32 level, champion;
    PARAMETRIZE { level = MAX_LEVEL - 1; champion = TRUE; }
    PARAMETRIZE { level = MAX_LEVEL - 1; champion = FALSE; }
    PARAMETRIZE { level = MAX_LEVEL; champion = TRUE; }
    GIVEN {
        for (u32 j = 0; j < ARRAY_COUNT(sCapFlags); j++)
            FlagSet(sCapFlags[j]);
        if (!champion)
            FlagClear(FLAG_IS_CHAMPION);
        PLAYER(SPECIES_WOBBUFFET) { Level(level); }
        OPPONENT(SPECIES_BLISSEY) { Level(50); HP(1); }
    } WHEN {
        TURN { MOVE(player, MOVE_SCRATCH); }
    } SCENE {
        MESSAGE("The wild Blissey fainted!");
    } THEN {
        u32 start = gExperienceTables[gSpeciesInfo[SPECIES_WOBBUFFET].growthRate][level];
        if (champion)
            EXPECT_EQ(GetCurrentLevelCap(), MAX_LEVEL);
        else
            EXPECT_LT(GetCurrentLevelCap(), MAX_LEVEL);
        if (champion && level < MAX_LEVEL)
            EXPECT_GT(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP), start);
        else
            EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_EXP), start);
        EXPECT_LE(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_LEVEL), MAX_LEVEL);
        for (u32 j = 0; j < ARRAY_COUNT(sCapFlags); j++)
            FlagClear(sCapFlags[j]);
    }
}

