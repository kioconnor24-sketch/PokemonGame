AlderfieldGym_MapScripts::
    map_script MAP_SCRIPT_ON_LOAD, Alderfield_GymLoad
    .byte 0
Alderfield_GymLoad:
    call_if_set FLAG_AVERON_WEST_SLUICE, Alderfield_CheckEast
    end
Alderfield_CheckEast:
    call_if_set FLAG_AVERON_EAST_SLUICE, Alderfield_OpenGate
    return
Alderfield_OpenGate:
    setmetatile 4, 9, AV_GYM_FLOOR, FALSE
    return
Alderfield_ClinicNurse::
    setvar VAR_0x800B, 1
    call Common_EventScript_PkmnCenterNurse
    waitmessage
    waitbuttonpress
    release
    end
Alderfield_GymRules::
    lockall
    specialvar VAR_RESULT, GetCurrentLevelCap
    buffernumberstring STR_VAR_1, VAR_RESULT
    msgbox Alderfield_Text_Rules, MSGBOX_DEFAULT
    releaseall
    end
Alderfield_WestSluice::
    lock
    faceplayer
    msgbox Alderfield_Text_West, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Alderfield_Release
    setflag FLAG_AVERON_WEST_SLUICE
    call Alderfield_CheckEast
    special DrawWholeMapView
    msgbox Alderfield_Text_WestDone, MSGBOX_DEFAULT
    release
    end
Alderfield_EastSluice::
    lock
    faceplayer
    msgbox Alderfield_Text_East, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Alderfield_Release
    setflag FLAG_AVERON_EAST_SLUICE
    call_if_set FLAG_AVERON_WEST_SLUICE, Alderfield_OpenGate
    special DrawWholeMapView
    msgbox Alderfield_Text_EastDone, MSGBOX_DEFAULT
    release
    end
Alderfield_Elio::
    lock
    faceplayer
    goto_if_set FLAG_BADGE01_GET, Alderfield_ElioAfter
    goto_if_unset FLAG_AVERON_WEST_SLUICE, Alderfield_ElioNotReady
    goto_if_unset FLAG_AVERON_EAST_SLUICE, Alderfield_ElioNotReady
    msgbox Alderfield_Text_ElioIntro, MSGBOX_DEFAULT
    trainerbattle_no_intro TRAINER_AVERON_ELIO, Alderfield_Text_ElioDefeat
    setflag FLAG_BADGE01_GET
    msgbox Alderfield_Text_Badge, MSGBOX_DEFAULT
    playfanfare MUS_OBTAIN_BADGE
    waitfanfare
    goto Alderfield_ElioAfter
Alderfield_ElioNotReady:
    msgbox Alderfield_Text_NotReady, MSGBOX_DEFAULT
    release
    end
Alderfield_ElioAfter:
    goto_if_set FLAG_AVERON_GYM1_TM, Alderfield_ElioAdvice
    call Alderfield_ClaimGymTM
    setvar VAR_0x8000, ITEM_TM_WORK_UP
    setvar VAR_0x8001, 1
    setvar VAR_0x8006, ITEM_TM_WORK_UP
    copyvar VAR_0x8007, VAR_RESULT
    call EventScript_ObtainItemMessage
    goto_if_eq VAR_RESULT, FALSE, Alderfield_TMBagFull
Alderfield_ElioAdvice:
    msgbox Alderfield_Text_Advice, MSGBOX_DEFAULT
Alderfield_Release:
    release
    end
Alderfield_TMBagFull:
    msgbox Alderfield_Text_TMBagFull, MSGBOX_DEFAULT
    release
    end
Alderfield_ClaimGymTM::
    setvar VAR_RESULT, FALSE
    goto_if_unset FLAG_BADGE01_GET, Alderfield_TMReturn
    goto_if_set FLAG_AVERON_GYM1_TM, Alderfield_TMReturn
    additem ITEM_TM_WORK_UP, 1
    goto_if_eq VAR_RESULT, FALSE, Alderfield_TMReturn
    setflag FLAG_AVERON_GYM1_TM
Alderfield_TMReturn:
    return
Alderfield_GymTrainer::
    trainerbattle_double TRAINER_AVERON_GYM1, Alderfield_Text_Nico, Alderfield_Text_NicoDefeat, Alderfield_Text_NicoNeedTwo
    msgbox Alderfield_Text_NicoAfter, MSGBOX_AUTOCLOSE
    end
Alderfield_RouteTrainerA::
    trainerbattle_single TRAINER_AVERON_FARMER, Alderfield_Text_Sam, Alderfield_Text_SamDefeat
    msgbox Alderfield_Text_SamAfter, MSGBOX_AUTOCLOSE
    end
Alderfield_RouteTrainerB::
    trainerbattle_single TRAINER_AVERON_PICNIC, Alderfield_Text_Lina, Alderfield_Text_LinaDefeat
    msgbox Alderfield_Text_LinaAfter, MSGBOX_AUTOCLOSE
    end
Alderfield_RouteTrainerC::
    trainerbattle_single TRAINER_AVERON_ORCHARD, Alderfield_Text_Milo, Alderfield_Text_MiloDefeat
    msgbox Alderfield_Text_MiloAfter, MSGBOX_AUTOCLOSE
    end
Alderfield_ExpShare::
    lock
    faceplayer
    goto_if_set FLAG_AVERON_EXP_SHARE, Alderfield_ExpAdvice
    msgbox Alderfield_Text_ExpShare, MSGBOX_DEFAULT
    giveitem ITEM_EXP_SHARE
    goto_if_eq VAR_RESULT, FALSE, Alderfield_Release
    setflag FLAG_AVERON_EXP_SHARE
Alderfield_ExpAdvice:
    msgbox Alderfield_Text_ExpAdvice, MSGBOX_DEFAULT
    release
    end
Alderfield_Shop::
    lock
    faceplayer
    message gText_HowMayIServeYou
    waitmessage
    pokemart Alderfield_Items
    msgbox gText_PleaseComeAgain, MSGBOX_DEFAULT
    release
    end
    .align 2
Alderfield_Items:
    .2byte ITEM_POKE_BALL
    .2byte ITEM_POTION
    .2byte ITEM_ANTIDOTE
    .2byte ITEM_PARALYZE_HEAL
    .2byte ITEM_AWAKENING
    pokemartlistend
Alderfield_Market::
    lock
    faceplayer
    goto_if_eq VAR_AVERON_HARVEST_FAIR, 3, Alderfield_FairDone
    goto_if_eq VAR_AVERON_HARVEST_FAIR, 2, Alderfield_FairReward
    goto_if_eq VAR_AVERON_HARVEST_FAIR, 1, Alderfield_FairWaiting
    msgbox Alderfield_Text_FairAsk, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Alderfield_FairNoRush
    call Alderfield_AcceptFair
Alderfield_FairWaiting:
    msgbox Alderfield_Text_FairWaiting, MSGBOX_DEFAULT
    release
    end
Alderfield_FairNoRush:
    msgbox Alderfield_Text_Market, MSGBOX_DEFAULT
    release
    end
Alderfield_FairReward:
    call Alderfield_ClaimFairReward
    goto_if_eq VAR_RESULT, FALSE, Alderfield_FairBagFull
    msgbox Alderfield_Text_FairReward, MSGBOX_DEFAULT
    playfanfare MUS_OBTAIN_ITEM
    waitfanfare
Alderfield_FairDone:
    msgbox Alderfield_Text_FairDone, MSGBOX_DEFAULT
    release
    end
Alderfield_FairBagFull:
    msgbox Alderfield_Text_FairBagFull, MSGBOX_DEFAULT
    release
    end
Alderfield_Canal::
    lock
    faceplayer
    goto_if_ne VAR_AVERON_HARVEST_FAIR, 1, Alderfield_CanalSmallTalk
    call Alderfield_CollectFairCrate
    msgbox Alderfield_Text_FairCrate, MSGBOX_DEFAULT
    release
    end
Alderfield_CanalSmallTalk:
    msgbox Alderfield_Text_Canal, MSGBOX_DEFAULT
    release
    end
Alderfield_AcceptFair::
    goto_if_ne VAR_AVERON_HARVEST_FAIR, 0, Alderfield_FairReturn
    setvar VAR_AVERON_HARVEST_FAIR, 1
    return
Alderfield_CollectFairCrate::
    goto_if_ne VAR_AVERON_HARVEST_FAIR, 1, Alderfield_FairReturn
    setvar VAR_AVERON_HARVEST_FAIR, 2
    return
Alderfield_ClaimFairReward::
    setvar VAR_RESULT, FALSE
    goto_if_ne VAR_AVERON_HARVEST_FAIR, 2, Alderfield_FairReturn
    additem ITEM_SUPER_POTION, 1
    goto_if_eq VAR_RESULT, FALSE, Alderfield_FairReturn
    setvar VAR_AVERON_HARVEST_FAIR, 3
Alderfield_FairReturn:
    return
Alderfield_Field::
    msgbox Alderfield_Text_Field, MSGBOX_NPC
    end

Alderfield_Text_West:
    .string "West sluice is ready.\nWant to turn the handle?$"
Alderfield_Text_Rules:
    .string "Your team can train up to Lv. {STR_VAR_1}.\nLeague battles use SET style.$"
Alderfield_Text_East:
    .string "The east channel's nearly clear.\nWant to open its sluice?$"
Alderfield_Text_WestDone:
    .string "Water runs through the west ditch.\nBoth sluices open the farm gate.$"
Alderfield_Text_EastDone:
    .string "The east ditch fills with water.\nThat's one happy field.$"
Alderfield_Text_ElioIntro:
    .string "ELIO: Nice work with those sluices.\nWe've got a battle to fit in, too!$"
Alderfield_Text_NotReady:
    .string "ELIO: Could you help with the water?\nBoth sluices need opening first.$"
Alderfield_Text_ElioDefeat:
    .string "A good team, and a good day's work.$"
Alderfield_Text_Badge:
    .string "ELIO: Here's your first Badge!\nYou can now train up to Lv. 23.$"
Alderfield_Text_Advice:
    .string "Work Up gives your team a boost.\nTry it when you've got room to set up.$"
Alderfield_Text_TMBagFull:
    .string "That TM pocket's full.\nI'll keep Work Up here for you.$"
Alderfield_Text_Nico:
    .string "Two at a time, like the farm chores.\nWant to see how our team works?$"
Alderfield_Text_NicoNeedTwo:
    .string "Bring two Pokemon ready to battle.\nI'll keep the field clear for you!$"
Alderfield_Text_NicoDefeat:
    .string "Right. Now for the chores.$"
Alderfield_Text_NicoAfter:
    .string "ELIO likes a team that works\ntogether. Normal types have surprises.$"
Alderfield_Text_Sam:
    .string "My Sentret keeps watch for me.\nLet's give it something to do!$"
Alderfield_Text_SamDefeat:
    .string "You slipped right past us.$"
Alderfield_Text_SamAfter:
    .string "ALDERFIELD's clinic is past\nthe canal-side market.$"
Alderfield_Text_Lina:
    .string "One battle before the sandwiches?$"
Alderfield_Text_LinaDefeat:
    .string "Lunch wins this round.$"
Alderfield_Text_LinaAfter:
    .string "Hoppip keep landing in our basket.\nThey're not on the menu!$"
Alderfield_Text_Milo:
    .string "These two have been racing all day.\nGot time for a battle?$"
Alderfield_Text_MiloDefeat:
    .string "I think we need a water break.$"
Alderfield_Text_MiloAfter:
    .string "The northern path goes straight\nto ALDERFIELD. Can't miss the roofs.$"
Alderfield_Text_ExpShare:
    .string "I've got a spare Exp. Share.\nIt might help your newest catch.$"
Alderfield_Text_ExpAdvice:
    .string "Have a Pokemon hold it.\nThat Pokemon shares battle EXP.$"
Alderfield_Text_Market:
    .string "Apple pie, Berry pie, plain old pie.\nWe've been busy since sunrise.$"
Alderfield_Text_FairAsk:
    .string "The harvest fair's nearly ready.\nCould you fetch our apple crate?\pThe canal keeper has it.\nMy hands are full of flour!$"
Alderfield_Text_FairWaiting:
    .string "Ask the keeper by the canal.\nHe'll know which crate is ours.$"
Alderfield_Text_FairCrate:
    .string "Oh, the apples! Here you go.\nMind the one with the wobbly handle.\pYou take the apple crate.\nTime to head back to the stall.$"
Alderfield_Text_FairReward:
    .string "Just in time! Here's a little thanks.\nYou received a Super Potion!$"
Alderfield_Text_FairDone:
    .string "First pie's for the fair judges.\nSecond one's for the cook. Fair's fair!$"
Alderfield_Text_FairBagFull:
    .string "I've got a Super Potion for you.\nMake some room and come back.$"
Alderfield_Text_Canal:
    .string "The locks keep our fields watered.\nMy boots keep the mud inside.$"
Alderfield_Text_Field:
    .string "Lechonk found my lost glove.\nThen it ran off with the other one.$"
