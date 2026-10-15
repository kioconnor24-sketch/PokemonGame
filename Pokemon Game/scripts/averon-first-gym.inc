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
    msgbox Alderfield_Text_EastDone, MSGBOX_DEFAULT
    release
    end
Alderfield_Elio::
    lock
    faceplayer
    goto_if_set FLAG_BADGE01_GET, Alderfield_ElioAfter
    msgbox Alderfield_Text_ElioIntro, MSGBOX_DEFAULT
    trainerbattle_no_intro TRAINER_AVERON_ELIO, Alderfield_Text_ElioDefeat
    setflag FLAG_BADGE01_GET
    msgbox Alderfield_Text_Badge, MSGBOX_DEFAULT
    playfanfare MUS_OBTAIN_BADGE
    waitfanfare
Alderfield_ElioAfter:
    goto_if_set FLAG_AVERON_GYM1_TM, Alderfield_ElioAdvice
    giveitem ITEM_TM_WORK_UP
    goto_if_eq VAR_RESULT, FALSE, Alderfield_Release
    setflag FLAG_AVERON_GYM1_TM
Alderfield_ElioAdvice:
    msgbox Alderfield_Text_Advice, MSGBOX_DEFAULT
Alderfield_Release:
    release
    end
Alderfield_GymTrainer::
    trainerbattle_single TRAINER_AVERON_GYM1, Alderfield_Text_Nico, Alderfield_Text_NicoDefeat
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
    msgbox Alderfield_Text_Market, MSGBOX_NPC
    end
Alderfield_Canal::
    msgbox Alderfield_Text_Canal, MSGBOX_NPC
    end
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
Alderfield_Text_ElioDefeat:
    .string "A good team, and a good day's work.$"
Alderfield_Text_Badge:
    .string "ELIO: Here's your first Badge!\nYou can now train up to Lv. 23.$"
Alderfield_Text_Advice:
    .string "Work Up gives your team a boost.\nTry it when you've got room to set up.$"
Alderfield_Text_Nico:
    .string "I train before the morning chores.\nYou're just in time!$"
Alderfield_Text_NicoDefeat:
    .string "Right. Now for the chores.$"
Alderfield_Text_NicoAfter:
    .string "ELIO likes a team that works\ntogether. Normal types can surprise you.$"
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
Alderfield_Text_Canal:
    .string "The locks keep our fields watered.\nMy boots keep the mud inside.$"
Alderfield_Text_Field:
    .string "Lechonk found my lost glove.\nThen it ran off with the other one.$"
