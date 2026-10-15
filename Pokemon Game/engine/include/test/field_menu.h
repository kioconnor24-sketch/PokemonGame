#ifndef GUARD_TEST_FIELD_MENU_H
#define GUARD_TEST_FIELD_MENU_H

#include "constants/field_move.h"

// Native menu integration harness. These entry points are absent from release
// builds. They send keys through the real tasks, windows and fade callbacks.
void Test_FieldMenuBegin(u8 slotId);
void Test_FieldMenuStep(u16 keys);
void Test_FieldMenuEnd(void);
bool32 Test_FieldMenuActionsReady(void);
bool32 Test_FieldMenuChoosingMon(void);
bool32 Test_FieldMenuExited(void);
bool32 Test_FieldMenuAtFieldBoundary(void);
u32 Test_FieldMenuActionCount(void);
s32 Test_FieldMenuToolkitIndex(void);
s32 Test_FieldMenuMoveIndex(enum FieldMove fieldMove);
bool32 Test_FlyMenuReady(void);
struct RegionMap;
const struct RegionMap *Test_FlyMenuState(void);

#endif
