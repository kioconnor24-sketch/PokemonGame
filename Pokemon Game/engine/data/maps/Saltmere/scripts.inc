Saltmere_MapScripts::
    map_script MAP_SCRIPT_ON_TRANSITION, Saltmere_OnTransition
    map_script MAP_SCRIPT_ON_FRAME_TABLE, Saltmere_OnFrame
    .byte 0

Saltmere_OnTransition:
    clearflag FLAG_HIDE_MAP_NAME_POPUP
    setrespawn HEAL_LOCATION_LITTLEROOT_TOWN_BRENDANS_HOUSE_2F
    end

Saltmere_OnFrame:
    map_script_2 VAR_AVERON_INTRO, 0, Saltmere_Welcome
    .2byte 0

Saltmere_Welcome:
    lockall
    setvar VAR_AVERON_INTRO, 1
    setflag FLAG_SYS_B_DASH
    msgbox Saltmere_Text_Welcome, MSGBOX_DEFAULT
    releaseall
    end

Saltmere_ExitGate::
    goto_if_set FLAG_AVERON_STARTER, Saltmere_End
    lockall
    msgbox Saltmere_Text_PartnerFirst, MSGBOX_DEFAULT
    applymovement LOCALID_PLAYER, Saltmere_StepBack
    waitmovement 0
    releaseall
Saltmere_End:
    end

Saltmere_StepBack:
    walk_down
    step_end

Saltmere_GreenhouseKeeper::
    lock
    faceplayer
    goto_if_ne VAR_AVERON_GREENHOUSE, 0, Saltmere_GreenhouseRepeat
    msgbox Saltmere_Text_GreenhouseAsk, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Saltmere_DeclineErrand
    call_if_eq VAR_AVERON_FIRST_HOUSE, 0, Saltmere_FirstGreenhouse
    setvar VAR_AVERON_GREENHOUSE, 1
Saltmere_GreenhouseRepeat:
    msgbox Saltmere_Text_TrayBench, MSGBOX_DEFAULT
    release
    end
Saltmere_FirstGreenhouse:
    setvar VAR_AVERON_FIRST_HOUSE, 1
    return
Saltmere_Tray::
    lockall
    goto_if_eq VAR_AVERON_GREENHOUSE, 0, Saltmere_TrayEmpty
    setvar VAR_AVERON_GREENHOUSE, 2
    msgbox Saltmere_Text_TrayDone, MSGBOX_DEFAULT
    releaseall
    end
Saltmere_TrayEmpty:
    msgbox Saltmere_Text_Seedlings, MSGBOX_DEFAULT
    releaseall
    end

Saltmere_WorkshopKeeper::
    lock
    faceplayer
    goto_if_ne VAR_AVERON_WORKSHOP, 0, Saltmere_WorkshopRepeat
    msgbox Saltmere_Text_WorkshopAsk, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Saltmere_DeclineErrand
    call_if_eq VAR_AVERON_FIRST_HOUSE, 0, Saltmere_FirstWorkshop
    setvar VAR_AVERON_WORKSHOP, 1
Saltmere_WorkshopRepeat:
    msgbox Saltmere_Text_ScrewShelf, MSGBOX_DEFAULT
    release
    end
Saltmere_FirstWorkshop:
    setvar VAR_AVERON_FIRST_HOUSE, 2
    return
Saltmere_WorkshopScrew::
    lockall
    goto_if_eq VAR_AVERON_WORKSHOP, 0, Saltmere_ScrewEmpty
    setvar VAR_AVERON_WORKSHOP, 2
    msgbox Saltmere_Text_ScrewDone, MSGBOX_DEFAULT
    releaseall
    end
Saltmere_ScrewEmpty:
    msgbox Saltmere_Text_ToolShelf, MSGBOX_DEFAULT
    releaseall
    end

Saltmere_HarborKeeper::
    lock
    faceplayer
    goto_if_ne VAR_AVERON_HARBOR, 0, Saltmere_HarborRepeat
    msgbox Saltmere_Text_HarborAsk, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Saltmere_DeclineErrand
    call_if_eq VAR_AVERON_FIRST_HOUSE, 0, Saltmere_FirstHarbor
    setvar VAR_AVERON_HARBOR, 1
Saltmere_HarborRepeat:
    msgbox Saltmere_Text_ParcelDock, MSGBOX_DEFAULT
    release
    end
Saltmere_FirstHarbor:
    setvar VAR_AVERON_FIRST_HOUSE, 3
    return
Saltmere_DeclineErrand:
    msgbox Saltmere_Text_NoRush, MSGBOX_DEFAULT
    release
    end
Saltmere_Dockhand::
    lock
    faceplayer
    goto_if_ne VAR_AVERON_HARBOR, 1, Saltmere_DockSmallTalk
    setvar VAR_AVERON_HARBOR, 2
    msgbox Saltmere_Text_ParcelDone, MSGBOX_DEFAULT
    release
    end
Saltmere_DockSmallTalk:
    msgbox Saltmere_Text_Dock, MSGBOX_DEFAULT
    release
    end

Saltmere_Fenwick::
    lock
    faceplayer
    goto_if_set FLAG_AVERON_STARTER, Saltmere_ProfessorAfter
    switch VAR_AVERON_FIRST_HOUSE
    case 1, Saltmere_OfferSnivy
    case 2, Saltmere_OfferFennekin
    case 3, Saltmere_OfferPiplup
    msgbox Saltmere_Text_HelpFirst, MSGBOX_DEFAULT
    release
    end
Saltmere_OfferSnivy:
    goto_if_ne VAR_AVERON_GREENHOUSE, 2, Saltmere_FinishErrand
    bufferspeciesname STR_VAR_1, SPECIES_SNIVY
    msgbox Saltmere_Text_StarterOffer, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Saltmere_DeclineStarter
    specialvar VAR_RESULT, CalculatePlayerPartyCount
    goto_if_ge VAR_RESULT, 6, Saltmere_PartyFull
    givemon SPECIES_SNIVY, 5
    goto_if_ne VAR_RESULT, MON_GIVEN_TO_PARTY, Saltmere_PartyFull
    setvar VAR_AVERON_MIRA_STARTER, SPECIES_PIPLUP
    goto Saltmere_StarterReceived
Saltmere_OfferFennekin:
    goto_if_ne VAR_AVERON_WORKSHOP, 2, Saltmere_FinishErrand
    bufferspeciesname STR_VAR_1, SPECIES_FENNEKIN
    msgbox Saltmere_Text_StarterOffer, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Saltmere_DeclineStarter
    specialvar VAR_RESULT, CalculatePlayerPartyCount
    goto_if_ge VAR_RESULT, 6, Saltmere_PartyFull
    givemon SPECIES_FENNEKIN, 5
    goto_if_ne VAR_RESULT, MON_GIVEN_TO_PARTY, Saltmere_PartyFull
    setvar VAR_AVERON_MIRA_STARTER, SPECIES_SNIVY
    goto Saltmere_StarterReceived
Saltmere_OfferPiplup:
    goto_if_ne VAR_AVERON_HARBOR, 2, Saltmere_FinishErrand
    bufferspeciesname STR_VAR_1, SPECIES_PIPLUP
    msgbox Saltmere_Text_StarterOffer, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Saltmere_DeclineStarter
    specialvar VAR_RESULT, CalculatePlayerPartyCount
    goto_if_ge VAR_RESULT, 6, Saltmere_PartyFull
    givemon SPECIES_PIPLUP, 5
    goto_if_ne VAR_RESULT, MON_GIVEN_TO_PARTY, Saltmere_PartyFull
    setvar VAR_AVERON_MIRA_STARTER, SPECIES_FENNEKIN
Saltmere_StarterReceived:
    setflag FLAG_AVERON_STARTER
    setflag FLAG_SYS_POKEMON_GET
    setflag FLAG_SYS_POKEDEX_GET
    setflag FLAG_SYS_NATIONAL_DEX
    special EnableNationalPokedex
    special HealPlayerParty
    special UpdateFollowingPokemon
    msgbox Saltmere_Text_StarterReceived, MSGBOX_DEFAULT
    giveitem ITEM_POKE_BALL, 5
    call_if_eq VAR_RESULT, TRUE, Saltmere_MarkSupplies
    msgbox Saltmere_Text_RennWaiting, MSGBOX_DEFAULT
    release
    end
Saltmere_FinishErrand:
    msgbox Saltmere_Text_FinishErrand, MSGBOX_DEFAULT
    release
    end
Saltmere_DeclineStarter:
    msgbox Saltmere_Text_NoRush, MSGBOX_DEFAULT
    release
    end
Saltmere_PartyFull:
    msgbox Saltmere_Text_PartyFull, MSGBOX_DEFAULT
    release
    end
Saltmere_ProfessorAfter:
    setflag FLAG_SYS_NATIONAL_DEX
    special EnableNationalPokedex
    goto_if_set FLAG_AVERON_SUPPLIES, Saltmere_ProfessorReady
    giveitem ITEM_POKE_BALL, 5
    goto_if_eq VAR_RESULT, FALSE, Saltmere_SuppliesFull
    setflag FLAG_AVERON_SUPPLIES
Saltmere_ProfessorReady:
    msgbox Saltmere_Text_ProfessorAfter, MSGBOX_DEFAULT
    release
    end
Saltmere_MarkSupplies:
    setflag FLAG_AVERON_SUPPLIES
    return
Saltmere_SuppliesFull:
    msgbox Saltmere_Text_SuppliesFull, MSGBOX_DEFAULT
    release
    end

Saltmere_Renn::
    lock
    faceplayer
    goto_if_unset FLAG_AVERON_STARTER, Saltmere_RennBefore
    goto_if_ne VAR_AVERON_RENN, 0, Saltmere_RennAfter
    msgbox Saltmere_Text_RennAsk, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Saltmere_DeclineErrand
    setvar VAR_AVERON_RENN, 1
    switch VAR_AVERON_FIRST_HOUSE
    case 1, Saltmere_RennFennekin
    case 2, Saltmere_RennPiplup
    case 3, Saltmere_RennSnivy
    release
    end
Saltmere_RennFennekin:
    trainerbattle_earlyrival TRAINER_AVERON_RENN_FENNEKIN, RIVAL_BATTLE_HEAL_AFTER, Saltmere_Text_RennLose, Saltmere_Text_RennWin
    goto Saltmere_RennBattleComplete
Saltmere_RennPiplup:
    trainerbattle_earlyrival TRAINER_AVERON_RENN_PIPLUP, RIVAL_BATTLE_HEAL_AFTER, Saltmere_Text_RennLose, Saltmere_Text_RennWin
    goto Saltmere_RennBattleComplete
Saltmere_RennSnivy:
    trainerbattle_earlyrival TRAINER_AVERON_RENN_SNIVY, RIVAL_BATTLE_HEAL_AFTER, Saltmere_Text_RennLose, Saltmere_Text_RennWin
Saltmere_RennBattleComplete:
    special HealPlayerParty
Saltmere_RennAfter:
    msgbox Saltmere_Text_RennAfter, MSGBOX_DEFAULT
    release
    end
Saltmere_RennBefore:
    msgbox Saltmere_Text_RennBefore, MSGBOX_DEFAULT
    release
    end
Saltmere_Mira::
    lock
    faceplayer
    goto_if_unset FLAG_AVERON_STARTER, Saltmere_MiraBefore
    bufferspeciesname STR_VAR_1, VAR_AVERON_MIRA_STARTER
    msgbox Saltmere_Text_MiraAfter, MSGBOX_DEFAULT
    release
    end
Saltmere_MiraBefore:
    msgbox Saltmere_Text_MiraBefore, MSGBOX_DEFAULT
    release
    end
Saltmere_HomeHeal::
    lock
    faceplayer
    msgbox Saltmere_Text_Heal, MSGBOX_DEFAULT
    special HealPlayerParty
    playfanfare MUS_HEAL
    waitfanfare
    release
    end
Saltmere_Pip::
    msgbox Saltmere_Text_Pip, MSGBOX_NPC
    end
Saltmere_PipScrew::
    lockall
    goto_if_set FLAG_AVERON_PIP_SCREW, Saltmere_PipDone
    msgbox Saltmere_Text_PipFound, MSGBOX_DEFAULT
    giveitem ITEM_POTION
    goto_if_eq VAR_RESULT, FALSE, Saltmere_ReleaseAll
    setflag FLAG_AVERON_PIP_SCREW
Saltmere_PipDone:
    msgbox Saltmere_Text_PipDone, MSGBOX_DEFAULT
Saltmere_ReleaseAll:
    releaseall
    end
Windrow_Berries::
    lock
    faceplayer
    goto_if_set FLAG_AVERON_BERRIES, Windrow_BerriesDone
    msgbox Windrow_Text_Berries, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Saltmere_DeclineErrand
    giveitem ITEM_ORAN_BERRY, 3
    goto_if_eq VAR_RESULT, FALSE, Saltmere_Release
    setflag FLAG_AVERON_BERRIES
Windrow_BerriesDone:
    msgbox Windrow_Text_BerriesDone, MSGBOX_DEFAULT
Saltmere_Release:
    release
    end
Windrow_RoadAhead::
    msgbox Windrow_Text_RoadAhead, MSGBOX_NPC
    end
Averon_Lookout::
    msgbox Averon_Text_Lookout, MSGBOX_NPC
    end
Averon_MeadowTrainer::
    trainerbattle_single TRAINER_AVERON_MEADOW, Averon_Text_MeadowChallenge, Averon_Text_MeadowDefeat
    msgbox Averon_Text_MeadowAfter, MSGBOX_AUTOCLOSE
    end

Saltmere_Text_Welcome:
    .string "FENWICK: Morning, {PLAYER}!\nThe pier's already busy.\pOur neighbors could use a hand.\nCome see me when you're done.$"
Saltmere_Text_PartnerFirst:
    .string "Better find a partner before\nheading into the long grass.$"
Saltmere_Text_GreenhouseAsk:
    .string "Mind carrying that tray over?\nThe little ones need more light.$"
Saltmere_Text_TrayBench:
    .string "The sunny bench is by the bookcase.\nJust set the tray there.$"
Saltmere_Text_TrayDone:
    .string "You set the seedlings in the light.\nKEEPER: Perfect. That's better!$"
Saltmere_Text_Seedlings:
    .string "Tiny seedlings lean toward the sun.$"
Saltmere_Text_WorkshopAsk:
    .string "Could you check the tool shelf?\nI'm one screw short of a boat.$"
Saltmere_Text_ScrewShelf:
    .string "Left shelf. Small brass screw.\nTry not to bring me a nail!$"
Saltmere_Text_ScrewDone:
    .string "You find the screw on the shelf.\nThe keeper fixes it into place.\pThere! This boat might even float.$"
Saltmere_Text_ToolShelf:
    .string "Tools of every size fill the shelf.$"
Saltmere_Text_HarborAsk:
    .string "Could you take this parcel down\nto the dockhand by the water?$"
Saltmere_Text_ParcelDock:
    .string "He's east of the little pier.\nYou'll hear him complaining.$"
Saltmere_Text_ParcelDone:
    .string "My lunch! I thought I'd packed\na whole bag of fishing line.\pThanks. You saved my afternoon.$"
Saltmere_Text_Dock:
    .string "Wingull got my sandwich yesterday.\nToday I'm watching the sky.$"
Saltmere_Text_NoRush:
    .string "No rush. I'll be right here.$"
Saltmere_Text_HelpFirst:
    .string "The greenhouse, workshop, and\nharbor house all need a hand.\pPick somewhere to start.\nI'll keep these three company.$"
Saltmere_Text_StarterOffer:
    .string "{STR_VAR_1} took quite a shine to you.\nWant to set off together?$"
Saltmere_Text_StarterReceived:
    .string "{STR_VAR_1} joined your party!\nFENWICK: Take care of each other.$"
Saltmere_Text_RennWaiting:
    .string "RENN's waiting by the north path.\nWINDROW is just past the meadow.$"
Saltmere_Text_FinishErrand:
    .string "Finish the errand you started.\nThen we'll get you ready to go.$"
Saltmere_Text_PartyFull:
    .string "Your party needs a free space.\nCome back when there's room.$"
Saltmere_Text_ProfessorAfter:
    .string "Try the meadow grass for a catch.\nYour family can heal your team.$"
Saltmere_Text_SuppliesFull:
    .string "Make some room in your BAG.\nI'll keep your Poke Balls here.$"
Saltmere_Text_RennAsk:
    .string "We made it farther than the pier.\nOne battle before we go?$"
Saltmere_Text_RennLose:
    .string "Okay, okay. I should've seen\nthat coming!$"
Saltmere_Text_RennWin:
    .string "Ha! You picked a bad time\nto try that move.$"
Saltmere_Text_RennAfter:
    .string "I've got supplies for both of us.\nSee you in WINDROW!$"
Saltmere_Text_RennBefore:
    .string "FENWICK has our partners ready.\nI hope mine likes boat rides.$"
Saltmere_Text_MiraBefore:
    .string "I'm checking the tide pools first.\nBadges can wait till after lunch.$"
Saltmere_Text_MiraAfter:
    .string "{STR_VAR_1} and I are taking our time.\nThere's a whole coast to explore.$"
Saltmere_Text_Heal:
    .string "Put your feet up for a moment.\nI'll look after your team.$"
Saltmere_Text_Pip:
    .string "Don't step on that screw.\nI dropped it somewhere by the pier.$"
Saltmere_Text_PipFound:
    .string "You find PIP's missing screw!\nPIP: I was about to blame Wingull.\pHere. Take this for the road.$"
Saltmere_Text_PipDone:
    .string "PIP's tackle box is fixed.\nFor now, anyway.$"
Windrow_Text_Berries:
    .string "We've picked too many Oran Berries.\nWant to sort a few for the road?$"
Windrow_Text_BerriesDone:
    .string "The best ones are firm and blue.\nThe squashed ones go in the pie.$"
Windrow_Text_RoadAhead:
    .string "ALDERFIELD is up the farm lane.\nFollow the path past the picnic.$"
Averon_Text_Lookout:
    .string "You can see SALTMERE from here.\nThat pier looks tiny now!$"
Averon_Text_MeadowChallenge:
    .string "My Lechonk found the best grass.\nLet's see how it does in a battle!$"
Averon_Text_MeadowDefeat:
    .string "Maybe it was just hungry.$"
Averon_Text_MeadowAfter:
    .string "WINDROW's growers can help you\nfind Berries for your team.$"
