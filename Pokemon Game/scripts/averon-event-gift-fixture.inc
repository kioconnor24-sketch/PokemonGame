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
