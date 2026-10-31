#include "global.h"
#include "test/test.h"
#include "daycare.h"
#include "egg_hatch.h"
#include "event_data.h"
#include "region_map.h"
#include "pokemon.h"
#include "pokemon_storage_system.h"
#include "pokemon_summary_screen.h"
#include "string_util.h"
#include "constants/maps.h"

// TEST-ONLY candidate C. No production accessor, format, tag or ID is added.
// Normalize a COPY/read or temporary write to permutation0 using the existing
// production reshuffler, then restore the original personality/identity.
static void Crypt(struct BoxPokemon *box)
{
    for (u32 i = 0; i < ARRAY_COUNT(box->secure.raw); i++)
        box->secure.raw[i] ^= box->personality ^ box->otId;
}

static void WriteCandidate(struct BoxPokemon *box, u16 code)
{
    EXPECT(code < 8192);
    u32 personality = box->personality;
    UpdateMonPersonality(box, 0);
    u32 low = code & 0xFF;
    SetBoxMonData(box, MON_DATA_MET_LOCATION, &low);
    Crypt(box);
    box->secure.substructs[1].type1.unused_04 = code >> 8;
    u32 checksum = 0;
    for (u32 i = 0; i < ARRAY_COUNT(box->secure.raw); i++)
        checksum += box->secure.raw[i] + (box->secure.raw[i] >> 16);
    box->checksum = checksum;
    Crypt(box);
    UpdateMonPersonality(box, personality);
}

static u16 ReadCandidate(const struct BoxPokemon *box)
{
    struct BoxPokemon copy = *box;
    UpdateMonPersonality(&copy, 0);
    Crypt(&copy);
    return copy.secure.substructs[3].type3.metLocation
        | (copy.secure.substructs[1].type1.unused_04 << 8);
}

static bool32 Contains(const u8 *text, const u8 *needle)
{
    u32 length = StringLength(text), n = StringLength(needle);
    for (u32 i = 0; i + n <= length; i++)
        if (memcmp(text + i, needle, n) == 0)
            return TRUE;
    return FALSE;
}

TEST("Averon extended location experiment preserves candidate bits across all 24 permutations PC and OT rekey")
{
    static const u16 values[] = {0, 215, 216, 252, 255, 256, 0x1234, 8191};
    struct BoxPokemon box;
    struct Pokemon party;
    ResetPokemonStorageSystem();
    for (u32 permutation = 0; permutation < 24; permutation++)
    {
        for (u32 i = 0; i < ARRAY_COUNT(values); i++)
        {
            CreateBoxMon(&box, SPECIES_PIPLUP, 12, permutation, OTID_STRUCT_PRESET(0x12345678));
            WriteCandidate(&box, values[i]);
            EXPECT_EQ(box.personality, permutation);
            EXPECT_EQ(ReadCandidate(&box), values[i]);
            EXPECT_EQ(GetBoxMonData(&box, MON_DATA_MET_LOCATION), values[i] & 0xFF);
            EXPECT_EQ(GetBoxMonData(&box, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
            SetBoxMonAt(0, 0, &box);
            BoxMonToMon(GetBoxedMonPtr(0, 0), &party);
            SetBoxMonOtIdKeepingData(&party.box, 0x87654321);
            UpdateMonPersonality(&party.box, permutation + 25);
            EXPECT_EQ(ReadCandidate(&party.box), values[i]);
            EXPECT_EQ(GetMonData(&party, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
        }
    }
}

TEST("Averon extended location experiment cannot infer a version from checksum-valid legacy unused bits")
{
    StringCopy(gSaveBlock2Ptr->playerName, COMPOUND_STRING("CODEX"));
    struct Pokemon mon;
    u8 text[1024];
    for (u32 permutation = 0; permutation < 24; permutation++)
    {
        CreateMon(&mon, SPECIES_PIPLUP, 12, permutation, OTID_STRUCT_PLAYER_ID);
        // An untagged import fixture with nonzero formerly-unused bits is
        // checksum-valid. Old accessors/formatter see Sandgem216; an unconditional
        // C decoder would reinterpret it as472. This is ambiguity, not migration.
        WriteCandidate(&mon.box, 216 | (1 << 8));
        EXPECT_EQ(GetMonData(&mon, MON_DATA_MET_LOCATION), 216);
        EXPECT_EQ(ReadCandidate(&mon.box), 472);
        EXPECT_EQ(GetMonData(&mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
        EXPECT(TestSummaryBufferTrainerMemo(&mon, text));
        EXPECT(Contains(text, COMPOUND_STRING("SANDGEM TOWN")));
    }
}

TEST("Averon extended location production egg hatch clears stale candidate high bits")
{
    StringCopy(gSaveBlock2Ptr->playerName, COMPOUND_STRING("CODEX"));
    ZeroPlayerPartyMons();
    struct Pokemon *mon = &gParties[B_TRAINER_PLAYER][0];
    CreateEgg(mon, SPECIES_PIPLUP, TRUE);
    EXPECT_EQ(GetMonData(mon, MON_DATA_IS_EGG), TRUE);
    EXPECT_EQ(GetMonData(mon, MON_DATA_MET_LOCATION), METLOC_SPECIAL_EGG);
    WriteCandidate(&mon->box, 0x1FD);
    EXPECT_EQ(GetMonData(mon, MON_DATA_MET_LOCATION), METLOC_SPECIAL_EGG);
    gSaveBlock1Ptr->location.mapGroup = MAP_GROUP(MAP_SALTMERE);
    gSaveBlock1Ptr->location.mapNum = MAP_NUM(MAP_SALTMERE);
    CalculatePlayerPartyCount();
    gSpecialVar_0x8004 = 0;
    ScriptHatchMon(); // real production core on an unchanged existing map
    EXPECT_EQ(GetMonData(mon, MON_DATA_IS_EGG), FALSE);
    EXPECT_EQ(GetMonData(mon, MON_DATA_MET_LEVEL), 0);
    EXPECT_EQ(GetMonData(mon, MON_DATA_MET_LOCATION), MAPSEC_SALTMERE);
    EXPECT_EQ(ReadCandidate(&mon->box), MAPSEC_SALTMERE);
    EXPECT_EQ(GetMonData(mon, MON_DATA_SANITY_IS_BAD_EGG), FALSE);
    u8 text[1024];
    EXPECT(TestSummaryBufferTrainerMemo(mon, text));
    EXPECT(Contains(text, COMPOUND_STRING("SALTMERE")));
    EXPECT(Contains(text, COMPOUND_STRING("hatched at")));
    // Production hatch now replaces the complete origin, including any stale
    // candidate bits; original failing research evidence remains in history.
}
