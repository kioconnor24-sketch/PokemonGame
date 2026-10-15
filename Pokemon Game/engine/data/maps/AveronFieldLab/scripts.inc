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
