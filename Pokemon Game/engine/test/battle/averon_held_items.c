#include "global.h"
#include "test/battle.h"

// Averon uses B_RESTORE_HELD_BATTLE_ITEMS = GEN_LATEST: a party Pokemon's
// non-Berry held item is put back after battle, however it was lost, and a
// Berry it ate stays eaten. Upstream marks this config "TODO: use in tests".
// Each test ends the battle with a win so THEN sees the post-battle party.

static enum Item PartyItem(u32 slot)
{
    return GetMonData(&gParties[B_TRAINER_PLAYER][slot], MON_DATA_HELD_ITEM);
}

AI_SINGLE_BATTLE_TEST("Averon held items: a non-Berry item lost to a trainer is back after the battle")
{
    enum Item item = ITEM_NONE;
    enum Move move = MOVE_KNOCK_OFF;
    PARAMETRIZE { item = ITEM_LEFTOVERS;   move = MOVE_KNOCK_OFF; }
    PARAMETRIZE { item = ITEM_LEFTOVERS;   move = MOVE_THIEF; }
    PARAMETRIZE { item = ITEM_FOCUS_SASH;  move = MOVE_SEISMIC_TOSS; }
    PARAMETRIZE { item = ITEM_AIR_BALLOON; move = MOVE_TACKLE; }
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(item); Level(100); MaxHP(100); HP(100); Speed(100); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_WOBBUFFET) { Level(100); HP(1); Speed(200); Moves(move); }
    } WHEN {
        TURN { EXPECT_MOVE(opponent, move); MOVE(player, MOVE_TACKLE); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, move, opponent);
        if (move == MOVE_KNOCK_OFF)
            MESSAGE("The opposing Wobbuffet knocked off Wobbuffet's Leftovers!");
        else if (move == MOVE_THIEF)
            MESSAGE("The opposing Wobbuffet stole Wobbuffet's Leftovers!");
        else if (item == ITEM_FOCUS_SASH)
            MESSAGE("Wobbuffet hung on using its Focus Sash!");
        else
            MESSAGE("Wobbuffet's Air Balloon popped!");
        MESSAGE("The opposing Wobbuffet fainted!");
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), item);
    }
}

AI_SINGLE_BATTLE_TEST("Averon held items: a Berry eaten in battle stays eaten")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_SITRUS_BERRY); Level(100); MaxHP(100); HP(100); Speed(100); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_WOBBUFFET) { Level(60); HP(1); Speed(200); Moves(MOVE_SEISMIC_TOSS); }
    } WHEN {
        TURN { EXPECT_MOVE(opponent, MOVE_SEISMIC_TOSS); MOVE(player, MOVE_TACKLE); }
    } SCENE {
        MESSAGE("The opposing Wobbuffet fainted!");
    } THEN {
        // 100 - 60 = 40 HP, then Sitrus Berry heals a quarter of 100.
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(GetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HP), 65);
        EXPECT_EQ(PartyItem(0), ITEM_NONE);
    }
}

AI_SINGLE_BATTLE_TEST("Averon held items: Trick returns each side's own item after the battle")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_CHOICE_SCARF); Speed(200); Moves(MOVE_TRICK, MOVE_TACKLE); }
        OPPONENT(SPECIES_WOBBUFFET) { Item(ITEM_LEFTOVERS); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TRICK); EXPECT_MOVE(opponent, MOVE_CELEBRATE); }
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_TRICK, player);
        MESSAGE("The opposing Wobbuffet fainted!");
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_CHOICE_SCARF);
    }
}

// Gen 5+ (B_RETURN_STOLEN_NPC_ITEMS): Thief does not permanently take a
// trainer's item, so beating trainers cannot be used to farm their items.
AI_SINGLE_BATTLE_TEST("Averon held items: an item the player steals from a trainer is not kept", u32 outcome)
{
    u32 win = FALSE;
    PARAMETRIZE { win = TRUE; }
    PARAMETRIZE { win = FALSE; }
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { HP(win ? 100 : 1); Speed(200); Moves(MOVE_THIEF); }
        OPPONENT(SPECIES_WOBBUFFET) { Item(ITEM_LEFTOVERS); HP(win ? 1 : 400); MaxHP(400); Speed(1); Moves(MOVE_SEISMIC_TOSS); }
    } WHEN {
        TURN { MOVE(player, MOVE_THIEF); EXPECT_MOVE(opponent, MOVE_SEISMIC_TOSS); }
    } SCENE {
        MESSAGE("Wobbuffet stole the opposing Wobbuffet's Leftovers!");
    } THEN {
        EXPECT_EQ(gBattleOutcome, win ? B_OUTCOME_WON : B_OUTCOME_LOST);
        EXPECT_EQ(PartyItem(0), ITEM_NONE);
    }
}

// An item given to a partner with Bestow must not exist twice after battle:
// the giver gets its own item back, so the receiver must not keep a copy.
AI_DOUBLE_BATTLE_TEST("Averon held items: Bestow to a partner does not duplicate the item")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_LEFTOVERS); Speed(200); Moves(MOVE_BESTOW, MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Speed(150); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_WOBBUFFET) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_WOBBUFFET) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(playerLeft, MOVE_BESTOW, target: playerRight); MOVE(playerRight, MOVE_TACKLE, target: opponentLeft); }
        TURN { MOVE(playerLeft, MOVE_TACKLE, target: opponentRight); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_BESTOW, playerLeft);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_LEFTOVERS);
        EXPECT_EQ(PartyItem(1), ITEM_NONE);
    }
}

// A Berry is not restored to its holder after battle, so one handed to a
// partner must go back to the giver rather than vanish.
AI_DOUBLE_BATTLE_TEST("Averon held items: a Berry given to a partner with Bestow goes back to the giver")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_ORAN_BERRY); Speed(200); Moves(MOVE_BESTOW, MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Speed(150); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_WOBBUFFET) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_WOBBUFFET) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(playerLeft, MOVE_BESTOW, target: playerRight); MOVE(playerRight, MOVE_TACKLE, target: opponentLeft); }
        TURN { MOVE(playerLeft, MOVE_TACKLE, target: opponentRight); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_BESTOW, playerLeft);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_ORAN_BERRY);
        EXPECT_EQ(PartyItem(1), ITEM_NONE);
    }
}

// The fix must not take away an item legitimately won from a wild Pokemon.
WILD_BATTLE_TEST("Averon held items: an item taken from a wild Pokemon with Magician is kept")
{
    GIVEN {
        PLAYER(SPECIES_KLEFKI) { Ability(ABILITY_MAGICIAN); Speed(200); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_WOBBUFFET) { Item(ITEM_LEFTOVERS); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        ABILITY_POPUP(player, ABILITY_MAGICIAN);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_LEFTOVERS);
    }
}

