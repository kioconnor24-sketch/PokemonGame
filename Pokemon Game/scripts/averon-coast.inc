CoastalBluffs_MapScripts::
    .byte 0
CoastalBluffs_BadgeGate::
    goto_if_set FLAG_BADGE01_GET, CoastalBluffs_End
    lockall
    msgbox CoastalBluffs_Text_BadgeGate, MSGBOX_DEFAULT
    applymovement LOCALID_PLAYER, CoastalBluffs_StepBack
    waitmovement 0
    releaseall
CoastalBluffs_End:
    end
CoastalBluffs_StepBack:
    walk_left
    step_end
CoastalBluffs_Trainer::
    trainerbattle_single TRAINER_AVERON_COAST, CoastalBluffs_Text_Trainer, CoastalBluffs_Text_Defeat
    msgbox CoastalBluffs_Text_After, MSGBOX_AUTOCLOSE
    end
CoastalBluffs_Lookout::
    msgbox CoastalBluffs_Text_Lookout, MSGBOX_NPC
    end
CoastalBluffs_Beach::
    msgbox CoastalBluffs_Text_Beach, MSGBOX_NPC
    end
CoastalBluffs_Repairs::
    msgbox CoastalBluffs_Text_Repairs, MSGBOX_NPC
    end
CoastalBluffs_Item::
    finditem ITEM_SUPER_POTION
    end
CoastalBluffs_Text_BadgeGate:
    .string "The bluffs are a longer walk.\nEarn ELIO's Badge before heading out.$"
CoastalBluffs_Text_Trainer:
    .string "These two keep racing the sea breeze.\nLet's see what they've learned!$"
CoastalBluffs_Text_Defeat:
    .string "The breeze gets this round.$"
CoastalBluffs_Text_After:
    .string "Wingull can glide for ages.\nRookidee mostly argues with the wind.$"
CoastalBluffs_Text_Lookout:
    .string "BREAKWATER's lighthouse is beyond\nthose bluffs. Keep an eye out!$"
CoastalBluffs_Text_Beach:
    .string "Packed my rod. Forgot my bait.\nThe sandwiches are doing fine, though.$"
CoastalBluffs_Text_Repairs:
    .string "The cliff steps are being repaired.\nThe beach path is still open.$"
