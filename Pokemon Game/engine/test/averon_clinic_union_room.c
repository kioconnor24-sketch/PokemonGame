#include "global.h"
#include "test/test.h"
#include "test/overworld_script.h"
#include "event_data.h"
#include "string_util.h"

// The shared nurse script asks BufferUnionRoomPlayerName whether a Union Room
// player is waiting after every heal. Averon's clinics never run
// CableClub_OnResume (special InitUnionRoom), so the buffered name keeps its
// boot value. A zero-filled buffer was copied into gStringVar1 until the next
// 0xFF byte in EWRAM: on RELEASE builds that wiped the heap and crashed the
// first clinic heal after power-on. This file must not call InitUnionRoom.
TEST("Averon clinic union-room check without InitUnionRoom copies nothing")
{
    StringCopy(gStringVar1, COMPOUND_STRING("SENTINEL"));
    StringCopy(gStringVar2, COMPOUND_STRING("CANARY"));
    gSpecialVar_Result = 0xFFFF;

    RUN_OVERWORLD_SCRIPT(
        specialvar VAR_RESULT, BufferUnionRoomPlayerName;
    );

    EXPECT_EQ(gSpecialVar_Result, FALSE);
    EXPECT_EQ(StringCompare(gStringVar1, COMPOUND_STRING("SENTINEL")), 0);
    EXPECT_EQ(StringCompare(gStringVar2, COMPOUND_STRING("CANARY")), 0);
}
