#include "global.h"
#include "test/battle.h"
#include "battle_util.h"
#include "item.h"

// Averon uses B_RESTORE_HELD_BATTLE_ITEMS = GEN_LATEST: a party Pokemon's
// non-Berry held item is put back after battle, however it was lost, and a
// Berry it ate stays eaten. Upstream marks this config "TODO: use in tests".
// Tests finish the battle so THEN sees the post-battle party.

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

// The receiver did not start empty: Stuff Cheeks consumes its original
// Berry, then Symbiosis gives it the partner's non-Berry item. Restoring
// the giver must not also leave a second copy on the Berry's former holder.
AI_DOUBLE_BATTLE_TEST("Averon held items: Symbiosis after eating an original Berry does not duplicate its gift")
{
    GIVEN {
        PLAYER(SPECIES_SKWOVET) { Item(ITEM_LIECHI_BERRY); Speed(200); Moves(MOVE_STUFF_CHEEKS, MOVE_TACKLE); }
        PLAYER(SPECIES_ORANGURU) { Ability(ABILITY_SYMBIOSIS); Item(ITEM_LEFTOVERS); Speed(150); Moves(MOVE_CELEBRATE, MOVE_TACKLE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(playerLeft, MOVE_STUFF_CHEEKS); MOVE(playerRight, MOVE_CELEBRATE); }
        TURN { MOVE(playerLeft, MOVE_TACKLE, target: opponentLeft); MOVE(playerRight, MOVE_TACKLE, target: opponentRight); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_STUFF_CHEEKS, playerLeft);
        ABILITY_POPUP(playerRight, ABILITY_SYMBIOSIS);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_NONE);
        EXPECT_EQ(PartyItem(1), ITEM_LEFTOVERS);
    }
}

AI_DOUBLE_BATTLE_TEST("Averon held items: Bestow after eating an original Berry does not duplicate its gift")
{
    GIVEN {
        PLAYER(SPECIES_SKWOVET) { Item(ITEM_LIECHI_BERRY); Speed(200); Moves(MOVE_STUFF_CHEEKS, MOVE_CELEBRATE, MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_LEFTOVERS); Speed(150); Moves(MOVE_CELEBRATE, MOVE_BESTOW, MOVE_TACKLE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(playerLeft, MOVE_STUFF_CHEEKS); MOVE(playerRight, MOVE_CELEBRATE); }
        TURN { MOVE(playerLeft, MOVE_CELEBRATE); MOVE(playerRight, MOVE_BESTOW, target: playerLeft); }
        TURN { MOVE(playerLeft, MOVE_TACKLE, target: opponentLeft); MOVE(playerRight, MOVE_TACKLE, target: opponentRight); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_STUFF_CHEEKS, playerLeft);
        ANIMATION(ANIM_TYPE_MOVE, MOVE_BESTOW, playerRight);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_NONE);
        EXPECT_EQ(PartyItem(1), ITEM_LEFTOVERS);
    }
}

// A gives its Berry to B, then C gives a different Berry to A. At cleanup
// B is visited first: returning its Berry over A's new one would destroy
// C's item. Return C's item first, then revisit A's newly emptied slot.
AI_DOUBLE_BATTLE_TEST("Averon held items: returning a donated Berry never overwrites a different held Berry")
{
    bool32 opponentHasMatchingBerry = FALSE;
    PARAMETRIZE { opponentHasMatchingBerry = FALSE; }
    PARAMETRIZE { opponentHasMatchingBerry = TRUE; }
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Speed(200); Moves(MOVE_CELEBRATE, MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_ORAN_BERRY); Speed(150); Moves(MOVE_BESTOW, MOVE_CELEBRATE, MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_SITRUS_BERRY); Speed(200); Moves(MOVE_BESTOW, MOVE_CELEBRATE); }
        OPPONENT(SPECIES_MAGIKARP) { Item(opponentHasMatchingBerry ? ITEM_ORAN_BERRY : ITEM_NONE); MaxHP(1); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(playerLeft, MOVE_CELEBRATE); MOVE(playerRight, MOVE_BESTOW, target: playerLeft); }
        TURN { SWITCH(playerLeft, 2); MOVE(playerRight, MOVE_CELEBRATE); }
        TURN { MOVE(playerLeft, MOVE_BESTOW, target: playerRight); MOVE(playerRight, MOVE_CELEBRATE); }
        TURN { SWITCH(playerLeft, 0); MOVE(playerRight, MOVE_CELEBRATE); }
        TURN { MOVE(playerLeft, MOVE_TACKLE, target: opponentLeft); MOVE(playerRight, MOVE_TACKLE, target: opponentRight); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_BESTOW, playerRight);
        ANIMATION(ANIM_TYPE_MOVE, MOVE_BESTOW, playerLeft);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_NONE);
        EXPECT_EQ(PartyItem(1), ITEM_ORAN_BERRY);
        EXPECT_EQ(PartyItem(2), ITEM_SITRUS_BERRY);
    }
}

AI_DOUBLE_BATTLE_TEST("Averon held items: allied Trick preserves a Berry and restores a non-Berry in either slot order")
{
    enum Item left = ITEM_LEFTOVERS, right = ITEM_ORAN_BERRY;
    PARAMETRIZE { left = ITEM_LEFTOVERS; right = ITEM_ORAN_BERRY; }
    PARAMETRIZE { left = ITEM_ORAN_BERRY; right = ITEM_LEFTOVERS; }
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(left); Speed(200); Moves(MOVE_TRICK, MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Item(right); Speed(150); Moves(MOVE_CELEBRATE, MOVE_TACKLE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(playerLeft, MOVE_TRICK, target: playerRight); MOVE(playerRight, MOVE_CELEBRATE); }
        TURN { MOVE(playerLeft, MOVE_TACKLE, target: opponentLeft); MOVE(playerRight, MOVE_TACKLE, target: opponentRight); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_TRICK, playerLeft);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), left);
        EXPECT_EQ(PartyItem(1), right);
    }
}

// These are two distinct Leftovers: a used player item is restored while a
// different Pokemon legitimately takes the wild opponent's item.
WILD_BATTLE_TEST("Averon held items: wild Magician loot is kept when a teammate started with the same item")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_LEFTOVERS); Level(1); Attack(1); Speed(200); Moves(MOVE_FLING); }
        PLAYER(SPECIES_KLEFKI) { Ability(ABILITY_MAGICIAN); Level(100); Attack(500); Speed(200); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_MAGIKARP) { Item(ITEM_LEFTOVERS); Level(100); MaxHP(100); HP(100); Defense(100); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_FLING); }
        TURN { SWITCH(player, 1); }
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_FLING, player);
        ABILITY_POPUP(player, ABILITY_MAGICIAN);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_LEFTOVERS);
        EXPECT_EQ(PartyItem(1), ITEM_LEFTOVERS);
    }
}

AI_DOUBLE_BATTLE_TEST("Averon held items: Recycle remembers the donor of a consumed Berry")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_ORAN_BERRY); Speed(200); Moves(MOVE_BESTOW, MOVE_CELEBRATE, MOVE_TACKLE); }
        PLAYER(SPECIES_SKWOVET) { Speed(150); Moves(MOVE_STUFF_CHEEKS, MOVE_RECYCLE, MOVE_TACKLE, MOVE_CELEBRATE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        // Gen 9 cannot select Stuff Cheeks before holding a Berry. Receive
        // the gift first, then consume it on the following ordinary turn.
        TURN { MOVE(playerLeft, MOVE_BESTOW, target: playerRight); MOVE(playerRight, MOVE_CELEBRATE); }
        TURN { MOVE(playerLeft, MOVE_CELEBRATE); MOVE(playerRight, MOVE_STUFF_CHEEKS); }
        TURN { MOVE(playerLeft, MOVE_CELEBRATE); MOVE(playerRight, MOVE_RECYCLE); }
        TURN { MOVE(playerLeft, MOVE_TACKLE, target: opponentLeft); MOVE(playerRight, MOVE_TACKLE, target: opponentRight); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_STUFF_CHEEKS, playerRight);
        ANIMATION(ANIM_TYPE_MOVE, MOVE_RECYCLE, playerRight);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_ORAN_BERRY);
        EXPECT_EQ(PartyItem(1), ITEM_NONE);
    }
}

AI_DOUBLE_BATTLE_TEST("Averon held items: Harvest remembers the donor of a consumed Berry")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_ORAN_BERRY); Speed(200); Moves(MOVE_SUNNY_DAY, MOVE_BESTOW, MOVE_TACKLE, MOVE_CELEBRATE); }
        PLAYER(SPECIES_TREVENANT) { Ability(ABILITY_HARVEST); Speed(150); Moves(MOVE_CELEBRATE, MOVE_STUFF_CHEEKS, MOVE_TACKLE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(playerLeft, MOVE_SUNNY_DAY); MOVE(playerRight, MOVE_CELEBRATE); }
        TURN { MOVE(playerLeft, MOVE_BESTOW, target: playerRight); MOVE(playerRight, MOVE_CELEBRATE); }
        TURN { MOVE(playerLeft, MOVE_CELEBRATE); MOVE(playerRight, MOVE_STUFF_CHEEKS); }
        TURN { MOVE(playerLeft, MOVE_TACKLE, target: opponentLeft); MOVE(playerRight, MOVE_TACKLE, target: opponentRight); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_STUFF_CHEEKS, playerRight);
        ABILITY_POPUP(playerRight, ABILITY_HARVEST);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_ORAN_BERRY);
        EXPECT_EQ(PartyItem(1), ITEM_NONE);
    }
}

WILD_BATTLE_TEST("Averon held items: capture cannot duplicate a player's same-ID donated item")
{
    enum Item item = ITEM_LEFTOVERS;
    PARAMETRIZE { item = ITEM_LEFTOVERS; }
    PARAMETRIZE { item = ITEM_ORAN_BERRY; }
    GIVEN {
        PLAYER(SPECIES_KLEFKI) { Ability(ABILITY_MAGICIAN); Level(1); Attack(1); Speed(200); Moves(MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Item(item); Speed(200); Moves(MOVE_BESTOW); }
        OPPONENT(SPECIES_MAGIKARP) { Item(item); Level(100); MaxHP(100); HP(100); Defense(100); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_TACKLE); }
        TURN { SWITCH(player, 1); }
        TURN { MOVE(player, MOVE_BESTOW); }
        TURN { USE_ITEM(player, ITEM_MASTER_BALL); }
    } SCENE {
        ABILITY_POPUP(player, ABILITY_MAGICIAN);
        ANIMATION(ANIM_TYPE_MOVE, MOVE_BESTOW, player);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_CAUGHT);
        EXPECT_EQ(CalculatePlayerPartyCount(), 3);
        EXPECT_EQ(PartyItem(0), item);
        EXPECT_EQ(PartyItem(1), item);
        EXPECT_EQ(PartyItem(2), ITEM_NONE);
    }
}

// The native runner skips random post-battle Pickup. Exercise its exact
// cleanup boundary: a donor has found a new Potion while its original Potion
// is still held by the teammate. Both real copies must survive cleanup.
AI_DOUBLE_BATTLE_TEST("Averon held items: a newly found item cannot replace or duplicate the borrowed original")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_POTION); Speed(200); Moves(MOVE_BESTOW, MOVE_TACKLE); }
        PLAYER(SPECIES_WOBBUFFET) { Speed(150); Moves(MOVE_TACKLE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
        OPPONENT(SPECIES_MAGIKARP) { HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(playerLeft, MOVE_BESTOW, target: playerRight); MOVE(playerRight, MOVE_TACKLE, target: opponentLeft); }
        TURN { MOVE(playerLeft, MOVE_TACKLE, target: opponentRight); }
    } THEN {
        enum Item potion = ITEM_POTION;
        SetMonData(&gParties[B_TRAINER_PLAYER][0], MON_DATA_HELD_ITEM, &potion);
        GetLostItemState(B_TRAINER_PLAYER, 0)->heldOrigin = HELD_ITEM_ORIGIN_NONE;
        SetMonData(&gParties[B_TRAINER_PLAYER][1], MON_DATA_HELD_ITEM, &potion);
        GetLostItemState(B_TRAINER_PLAYER, 1)->heldOrigin = 0;
        u32 bagBefore = CountTotalItemQuantityInBag(ITEM_POTION);
        TryRestoreHeldItems();
        EXPECT_EQ(PartyItem(0), ITEM_POTION);
        EXPECT_EQ(PartyItem(1), ITEM_POTION);
        EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_POTION), bagBefore);
        TryRestoreHeldItems();
        EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_POTION), bagBefore);
    }
}

WILD_BATTLE_TEST("Averon held items: same-holder wild loot survives normal and full-Bag cleanup boundaries")
{
    bool32 fullBag = FALSE;
    PARAMETRIZE { fullBag = FALSE; }
    PARAMETRIZE { fullBag = TRUE; }
    GIVEN {
        SetBagItemsPointers();
        ClearBag();
        PLAYER(SPECIES_KLEFKI) { Ability(ABILITY_MAGICIAN); Item(ITEM_LEFTOVERS); Level(100); Attack(1); Speed(200); Moves(MOVE_FLING, MOVE_TACKLE, MOVE_SEISMIC_TOSS); }
        OPPONENT(SPECIES_MAGIKARP) { Item(ITEM_POTION); Level(100); MaxHP(100); HP(100); Defense(100); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_FLING); }
        TURN { MOVE(player, MOVE_TACKLE); }
        TURN { MOVE(player, MOVE_SEISMIC_TOSS); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_FLING, player);
        ABILITY_POPUP(player, ABILITY_MAGICIAN);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_POTION);
        // The runner clears the Bag at StartBattle and only records ten
        // inventory slots. Exercise the full-Bag case at the actual cleanup
        // boundary after the real battle, not as claimed in-battle inventory.
        if (fullBag)
        {
            u32 added = 0;
            ClearBag();
            for (enum Item filler = ITEM_NONE + 1; filler < ITEMS_COUNT && added < BAG_ITEMS_COUNT; filler++)
            {
                if (filler != ITEM_LEFTOVERS && GetItemPocket(filler) == POCKET_ITEMS
                 && AddBagItem(filler, MAX_BAG_ITEM_CAPACITY))
                    added++;
            }
            EXPECT_EQ(added, BAG_ITEMS_COUNT);
            EXPECT_EQ(AddBagItem(ITEM_LEFTOVERS, 1), FALSE);
            GetLostItemState(B_TRAINER_PLAYER, 0)->preservedElsewhere = FALSE;
        }
        TryRestoreHeldItems();
        EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_LEFTOVERS), fullBag ? 0 : 1);
        TryRestoreHeldItems();
        EXPECT_EQ(PartyItem(0), ITEM_POTION);
        EXPECT_EQ(CountTotalItemQuantityInBag(ITEM_LEFTOVERS), fullBag ? 0 : 1);
        ClearBag();
    }
}

AI_SINGLE_BATTLE_TEST("Averon held items: Bestow to an uncaptured trainer Pokemon restores the player's non-Berry")
{
    GIVEN {
        PLAYER(SPECIES_WOBBUFFET) { Item(ITEM_LEFTOVERS); Speed(200); Moves(MOVE_BESTOW, MOVE_TACKLE); }
        OPPONENT(SPECIES_MAGIKARP) { MaxHP(1); HP(1); Speed(1); Moves(MOVE_CELEBRATE); }
    } WHEN {
        TURN { MOVE(player, MOVE_BESTOW); }
        TURN { MOVE(player, MOVE_TACKLE); }
    } SCENE {
        ANIMATION(ANIM_TYPE_MOVE, MOVE_BESTOW, player);
    } THEN {
        EXPECT_EQ(gBattleOutcome, B_OUTCOME_WON);
        EXPECT_EQ(PartyItem(0), ITEM_LEFTOVERS);
    }
}

