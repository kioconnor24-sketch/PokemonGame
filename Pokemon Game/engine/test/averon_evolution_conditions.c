#include "global.h"
#include "test/test.h"
#include "battle.h"
#include "event_data.h"
#include "field_weather.h"
#include "item.h"
#include "move.h"
#include "overworld.h"
#include "pokemon.h"
#include "regions.h"
#include "rtc.h"
#include "constants/weather.h"

// Every conditional evolution in the data, set up so its conditions hold,
// run through the game's own GetEvolutionTargetSpecies in the matching mode.
// The first matching evolution wins, so each must produce exactly its own
// target. Left out: conditions Averon cannot meet by design (another region,
// an upstream map; listed by "Averon lists the evolution targets..."), and
// Shedinja's split from Nincada. The run is split into parts so each stays
// inside the runner's per-run time limit.

#define PARTS 4
#define PERSONALITY_TRIES 1000

enum Setup { SETUP_OK, SETUP_UNSUPPORTED };

static bool32 IsEnabled(u32 species)
{
    return species > SPECIES_NONE && species < NUM_SPECIES && IsSpeciesEnabled(species);
}

static enum Move AnyMoveOfType(u32 type)
{
    for (enum Move move = MOVE_NONE + 1; move < MOVES_COUNT; move++)
    {
        if (GetMoveType(move) == type)
            return move;
    }
    return MOVE_NONE;
}

static u32 AnySpeciesOfType(u32 type)
{
    for (u32 species = SPECIES_NONE + 1; species < NUM_SPECIES; species++)
    {
        if (IsEnabled(species) && species != SPECIES_EGG
         && (GetSpeciesType(species, 0) == type || GetSpeciesType(species, 1) == type))
            return species;
    }
    return SPECIES_NONE;
}

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
    return FALSE;
}

// Cheap personality checks, so the full evolution check runs only on
// candidates that can work. Natures are left to the engine.
static bool32 PersonalityMayMeet(u32 species, u32 personality, const struct EvolutionParam *params)
{
    for (u32 i = 0; params[i].condition != CONDITIONS_END; i++)
    {
        u32 upper = (personality >> 16) % 10, lower = personality % 100;
        switch (params[i].condition)
        {
        case IF_GENDER:
            if (GetGenderFromSpeciesAndPersonality(species, personality) != params[i].arg1)
                return FALSE;
            break;
        case IF_PID_UPPER_MODULO_10_GT: if (!(upper > params[i].arg1)) return FALSE; break;
        case IF_PID_UPPER_MODULO_10_EQ: if (!(upper == params[i].arg1)) return FALSE; break;
        case IF_PID_UPPER_MODULO_10_LT: if (!(upper < params[i].arg1)) return FALSE; break;
        case IF_PID_MODULO_100_GT: if (!(lower > params[i].arg1)) return FALSE; break;
        case IF_PID_MODULO_100_EQ: if (!(lower == params[i].arg1)) return FALSE; break;
        case IF_PID_MODULO_100_LT: if (!(lower < params[i].arg1)) return FALSE; break;
        default:
            break;
        }
    }
    return TRUE;
}

// Builds the party and world state for one evolution. The evolving Pokemon is
// party slot 0 (overworld steps need the first live Pokemon).
static enum Setup SetUp(u32 species, const struct Evolution *evo, u32 personality,
                        enum EvolutionMode *mode, u32 *item, struct Pokemon *partner, bool32 *usePartner)
{
    const struct EvolutionParam *params = evo->params;
    struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][0];
    u32 level = 50, helperSlot = 1, value;

    *item = ITEM_NONE;
    *usePartner = FALSE;
    switch (evo->method)
    {
    case EVO_LEVEL:             *mode = EVO_MODE_NORMAL; level = evo->param ? evo->param : 50; break;
    case EVO_LEVEL_BATTLE_ONLY: *mode = EVO_MODE_BATTLE_ONLY; level = evo->param ? evo->param : 50; break;
    case EVO_ITEM:              *mode = EVO_MODE_ITEM_USE; *item = evo->param; break;
    case EVO_TRADE:             *mode = EVO_MODE_TRADE; break;
    case EVO_SPIN:              *mode = EVO_MODE_OVERWORLD_SPECIAL; gSpecialVar_0x8000 = evo->param; break;
    case EVO_SCRIPT_TRIGGER:    *mode = EVO_MODE_SCRIPT_TRIGGER; *item = evo->param; break;
    case EVO_BATTLE_END:        *mode = EVO_MODE_BATTLE_SPECIAL; *item = 0; break; // party slot 0
    default:
        return SETUP_UNSUPPORTED;
    }

    ZeroPlayerPartyMons();
    CreateMon(mon, species, level, personality, OTID_STRUCT_PLAYER_ID);
    CalculateMonStats(mon); // CreateMon leaves HP at 0; the first live Pokemon needs HP
    SetTimeOfDay(0);
    for (u32 i = 0; params[i].condition != CONDITIONS_END; i++)
    {
        const struct EvolutionParam *param = &params[i];
        switch (param->condition)
        {
        case IF_GENDER:
        case IF_NATURE:
        case IF_AMPED_NATURE:
        case IF_LOW_KEY_NATURE:
        case IF_PID_UPPER_MODULO_10_GT:
        case IF_PID_UPPER_MODULO_10_EQ:
        case IF_PID_UPPER_MODULO_10_LT:
        case IF_PID_MODULO_100_GT:
        case IF_PID_MODULO_100_EQ:
        case IF_PID_MODULO_100_LT:
            break; // chosen by personality
        case IF_MIN_FRIENDSHIP:
            value = MAX_FRIENDSHIP;
            SetMonData(mon, MON_DATA_FRIENDSHIP, &value);
            break;
        case IF_KNOWS_MOVE:
            value = param->arg1;
            SetMonData(mon, MON_DATA_MOVE1, &value);
            break;
        case IF_KNOWS_MOVE_TYPE:
            value = AnyMoveOfType(param->arg1);
            SetMonData(mon, MON_DATA_MOVE2, &value);
            break;
        case IF_HOLD_ITEM:
            value = param->arg1;
            SetMonData(mon, MON_DATA_HELD_ITEM, &value);
            break;
        case IF_TIME:
        case IF_NOT_TIME:
            if (!SetHourForTimeConditions(params))
                return SETUP_UNSUPPORTED;
            break;
        case IF_NOT_REGION:
            if (param->arg1 == REGION_HOENN)
                return SETUP_UNSUPPORTED;
            break;
        case IF_REGION:
            if (param->arg1 != REGION_HOENN)
                return SETUP_UNSUPPORTED;
            break;
        case IF_ATK_GT_DEF:
        case IF_ATK_EQ_DEF:
        case IF_ATK_LT_DEF:
        {
            u32 attack = param->condition == IF_ATK_LT_DEF ? 50 : 100;
            u32 defense = param->condition == IF_ATK_GT_DEF ? 50 : 100;
            if (param->condition == IF_ATK_EQ_DEF)
                attack = defense = 80;
            SetMonData(mon, MON_DATA_ATK, &attack);
            SetMonData(mon, MON_DATA_DEF, &defense);
            break;
        }
        case IF_MIN_BEAUTY:
            value = 255;
            SetMonData(mon, MON_DATA_BEAUTY, &value);
            break;
        case IF_MIN_COOLNESS:
            value = 255;
            SetMonData(mon, MON_DATA_COOL, &value);
            break;
        case IF_MIN_SMARTNESS:
            value = 255;
            SetMonData(mon, MON_DATA_SMART, &value);
            break;
        case IF_MIN_TOUGHNESS:
            value = 255;
            SetMonData(mon, MON_DATA_TOUGH, &value);
            break;
        case IF_MIN_CUTENESS:
            value = 255;
            SetMonData(mon, MON_DATA_CUTE, &value);
            break;
        case IF_SPECIES_IN_PARTY:
            CreateMon(&gParties[B_TRAINER_PLAYER][helperSlot], param->arg1, 5, 0, OTID_STRUCT_PLAYER_ID);
            CalculateMonStats(&gParties[B_TRAINER_PLAYER][helperSlot++]);
            break;
        case IF_TYPE_IN_PARTY:
            value = AnySpeciesOfType(param->arg1);
            if (value == SPECIES_NONE)
                return SETUP_UNSUPPORTED;
            CreateMon(&gParties[B_TRAINER_PLAYER][helperSlot], value, 5, 0, OTID_STRUCT_PLAYER_ID);
            CalculateMonStats(&gParties[B_TRAINER_PLAYER][helperSlot++]);
            break;
        case IF_WEATHER:
            if (param->arg1 == WEATHER_FOG)
                SetCurrentAndNextWeatherNoDelay(WEATHER_FOG_HORIZONTAL);
            else
                SetCurrentAndNextWeatherNoDelay(param->arg1);
            break;
        case IF_BAG_ITEM_COUNT:
            if (!AddBagItem(param->arg1, param->arg2))
                return SETUP_UNSUPPORTED;
            break;
        case IF_MIN_OVERWORLD_STEPS:
            gFollowerSteps = param->arg1;
            break;
        case IF_RECOIL_DAMAGE_GE:
        case IF_USED_MOVE_X_TIMES:
        case IF_DEFEAT_X_WITH_ITEMS:
            value = max(param->arg1, max(param->arg2, param->arg3));
            SetMonData(mon, MON_DATA_EVOLUTION_TRACKER, &value);
            break;
        case IF_CURRENT_DAMAGE_GE:
            value = GetMonData(mon, MON_DATA_MAX_HP);
            if (value <= param->arg1)
                return SETUP_UNSUPPORTED;
            value -= param->arg1;
            SetMonData(mon, MON_DATA_HP, &value);
            break;
        case IF_CRITICAL_HITS_GE:
            gPartyCriticalHits[0] = param->arg1;
            break;
        case IF_TRADE_PARTNER_SPECIES:
            CreateMon(partner, param->arg1, 50, 0, OTID_STRUCT_PLAYER_ID);
            *usePartner = TRUE;
            break;
        default: // IF_IN_MAP, IF_IN_MAPSEC and anything new
            return SETUP_UNSUPPORTED;
        }
    }
    CalculatePlayerPartyCount();
    return SETUP_OK;
}

static void CleanUp(const struct EvolutionParam *params)
{
    for (u32 i = 0; params[i].condition != CONDITIONS_END; i++)
    {
        if (params[i].condition == IF_BAG_ITEM_COUNT)
            RemoveBagItem(params[i].arg1, CountTotalItemQuantityInBag(params[i].arg1));
    }
    SetTimeOfDay(0);
    gFollowerSteps = 0;
    gPartyCriticalHits[0] = 0;
    gSpecialVar_0x8000 = 0;
    ZeroPlayerPartyMons();
}

TEST("Averon every conditional evolution Averon can meet produces exactly its own form")
{
    u32 part = 0, run = 0, shadowed = 0, bad = 0, unsupported = 0;
    struct Pokemon partner;
    for (u32 p = 0; p < PARTS; p++)
        PARAMETRIZE { part = p; }
    for (u32 species = SPECIES_NONE + 1 + part; species < NUM_SPECIES; species += PARTS)
    {
        if (!IsEnabled(species) || species == SPECIES_EGG)
            continue;
        const struct Evolution *evolutions = GetSpeciesEvolutions(species);
        for (u32 i = 0; evolutions != NULL && evolutions[i].method != EVOLUTIONS_END; i++)
        {
            const struct Evolution *evo = &evolutions[i];
            enum Species result = SPECIES_NONE;
            bool32 supported = FALSE;
            if (evo->params == NULL || !IsEnabled(evo->targetSpecies))
                continue;
            for (u32 try = 0; try < PERSONALITY_TRIES && result != evo->targetSpecies; try++)
            {
                u32 personality = ((try / 100) << 16) | (try % 100), item;
                enum EvolutionMode mode;
                bool32 usePartner, canStopEvo = TRUE;
                if (!PersonalityMayMeet(species, personality, evo->params))
                    continue;
                if (SetUp(species, evo, personality, &mode, &item, &partner, &usePartner) != SETUP_OK)
                    break;
                supported = TRUE;
                result = GetEvolutionTargetSpecies(&gParties[B_TRAINER_PLAYER][0], mode, item,
                                                   usePartner ? &partner : NULL, &canStopEvo, CHECK_EVO);
                CleanUp(evo->params);
            }
            CleanUp(evo->params);
            if (!supported)
            {
                unsupported++;
                continue;
            }
            run++;
            if (result == evo->targetSpecies)
                continue;
            if (IsEnabled(result))
            {
                DebugPrintf("shadowed: %S -> %S, got %S (method %u)", GetSpeciesName(species), GetSpeciesName(evo->targetSpecies), GetSpeciesName(result), evo->method);
                shadowed++;
            }
            else
            {
                DebugPrintf("did not trigger: %S -> %S (method %u)", GetSpeciesName(species), GetSpeciesName(evo->targetSpecies), evo->method);
                bad++;
            }
        }
    }
    DebugPrintf("part %u: run %u, shadowed %u, not supported %u", part, run, shadowed, unsupported);
    EXPECT_GT(run, 0);
    EXPECT_EQ(bad, 0);
    EXPECT_EQ(shadowed, 0);
}
