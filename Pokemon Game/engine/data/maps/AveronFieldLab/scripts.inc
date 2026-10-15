AveronFieldLab_MapScripts::
    .byte 0
AveronFieldLab_Enter::
    warp MAP_AVERONFIELDLAB, 4, 4
    waitstate
    end
AveronFieldLab_Grant::
    lockall
    msgbox AveronFieldLab_TextConfirm, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, AveronFieldLab_Release
    setflag FLAG_AVERON_LICENSE_CUT
    setflag FLAG_AVERON_LICENSE_ROCK_SMASH
    setflag FLAG_AVERON_LICENSE_STRENGTH
    setflag FLAG_AVERON_LICENSE_SURF
    setflag FLAG_AVERON_LICENSE_WATERFALL
    setflag FLAG_AVERON_LICENSE_DIVE
    setflag FLAG_AVERON_LICENSE_FLY
    msgbox AveronFieldLab_TextGranted, MSGBOX_DEFAULT
    releaseall
    end
AveronFieldLab_Revoke::
    lockall
    clearflag FLAG_AVERON_LICENSE_CUT
    clearflag FLAG_AVERON_LICENSE_ROCK_SMASH
    clearflag FLAG_AVERON_LICENSE_STRENGTH
    clearflag FLAG_AVERON_LICENSE_SURF
    clearflag FLAG_AVERON_LICENSE_WATERFALL
    clearflag FLAG_AVERON_LICENSE_DIVE
    clearflag FLAG_AVERON_LICENSE_FLY
    clearflag FLAG_SYS_USE_STRENGTH
    msgbox AveronFieldLab_TextRevoked, MSGBOX_DEFAULT
    releaseall
    end
AveronFieldLab_PrepareFly::
    lockall
    msgbox AveronFieldLab_TextFlyConfirm, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, AveronFieldLab_Release
    setflag FLAG_VISITED_LITTLEROOT_TOWN
    msgbox AveronFieldLab_TextFlyReady, MSGBOX_DEFAULT
    releaseall
    end
AveronFieldLab_Exit::
    lockall
    warp MAP_SALTMERE, 18, 18
    waitstate
    end
AveronFieldLab_TextFlyConfirm:
    .string "DEV: Enable a test Fly destination?\nUse a backed-up test save.$"
AveronFieldLab_TextFlyReady:
    .string "DEV: Fly to LITTLEROOT TOWN.\nIts landing point is SALTMERE.\pThe Fly license is still required.\nScript4 returns to this lab.$"
AveronFieldLab_TextGranted:
    .string "DEV: All field licenses granted.\nBack up your save before testing.$"
AveronFieldLab_TextRevoked:
    .string "DEV: Field licenses revoked.$"
AveronFieldLab_Release:
    releaseall
    end
AveronFieldLab_TextConfirm:
    .string "DEV: Grant all field licenses?\nUse a backed-up test save.$"
@ Developer-only native gift boundary. Included by the existing lab generator.
AveronFieldLab_Gift::
    lock
    faceplayer
    goto_if_set FLAG_AVERON_DEV_GIFT_RECEIVED, AveronFieldLab_GiftDone
    goto_if_unset FLAG_AVERON_SKETCH_REWARDED, AveronFieldLab_GiftNotReady
    msgbox AveronFieldLab_TextGiftOffer, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, AveronFieldLab_GiftEnd
    call AveronFieldLab_TryGift
    goto_if_eq VAR_RESULT, FALSE, AveronFieldLab_GiftFull
    msgbox AveronFieldLab_TextGiftReceived, MSGBOX_DEFAULT
    goto AveronFieldLab_GiftEnd
AveronFieldLab_GiftFull:
    msgbox AveronFieldLab_TextGiftFull, MSGBOX_DEFAULT
    goto AveronFieldLab_GiftEnd
AveronFieldLab_GiftNotReady:
    msgbox AveronFieldLab_TextGiftNotReady, MSGBOX_DEFAULT
    goto AveronFieldLab_GiftEnd
AveronFieldLab_GiftDone:
    msgbox AveronFieldLab_TextGiftDone, MSGBOX_DEFAULT
AveronFieldLab_GiftEnd:
    release
    end

AveronFieldLab_TryGift::
    setvar VAR_RESULT, FALSE
    goto_if_unset FLAG_AVERON_SKETCH_REWARDED, AveronFieldLab_GiftReturn
    goto_if_set FLAG_AVERON_DEV_GIFT_RECEIVED, AveronFieldLab_GiftReturn
    getpartysize
    goto_if_eq VAR_RESULT, PARTY_SIZE, AveronFieldLab_GiftBlocked
    givemon SPECIES_WOBBUFFET, 5
    goto_if_ne VAR_RESULT, MON_GIVEN_TO_PARTY, AveronFieldLab_GiftBlocked
    setflag FLAG_AVERON_DEV_GIFT_RECEIVED
    setvar VAR_RESULT, TRUE
AveronFieldLab_GiftReturn:
    return
AveronFieldLab_GiftBlocked:
    setvar VAR_RESULT, FALSE
    return

AveronFieldLab_TextGiftOffer:
    .string "DEV: Receive a test WOBBUFFET?\nThis changes your test save.$"
AveronFieldLab_TextGiftReceived:
    .string "DEV: WOBBUFFET joined the party.$"
AveronFieldLab_TextGiftFull:
    .string "DEV: Your party is full.\nMake room and come back.$"
AveronFieldLab_TextGiftNotReady:
    .string "DEV: Finish the tree sketch first.$"
AveronFieldLab_TextGiftDone:
    .string "DEV: The test gift was received.$"
