@ Two completely optional, independent short adventures.
@ They use six unused saved flag slots. No forced story stops, no global vars.
@ Never mark a reward flag until additem succeeds, including a full Bag.

Averon_FieldNotes_Researcher::
    lock
    faceplayer
    goto_if_set FLAG_AVERON_NOTES_REWARDED, Averon_NotesDone
    goto_if_set FLAG_AVERON_NOTES_RECORDED, Averon_NotesReward
    goto_if_set FLAG_AVERON_NOTES_STARTED, Averon_NotesWaiting
    msgbox Averon_Text_NotesAsk, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Averon_NotesDeclined
    setflag FLAG_AVERON_NOTES_STARTED
Averon_NotesWaiting:
    msgbox Averon_Text_NotesWaiting, MSGBOX_DEFAULT
    release
    end
Averon_NotesDeclined:
    msgbox Averon_Text_NotesDeclined, MSGBOX_DEFAULT
    release
    end
Averon_NotesReward:
    call Averon_FieldNotes_TryReward
    goto_if_eq VAR_RESULT, FALSE, Averon_NotesBagFull
    msgbox Averon_Text_NotesReward, MSGBOX_DEFAULT
    playfanfare MUS_OBTAIN_ITEM
    waitfanfare
Averon_NotesDone:
    msgbox Averon_Text_NotesDone, MSGBOX_DEFAULT
    release
    end
Averon_NotesBagFull:
    msgbox Averon_Text_NotesBagFull, MSGBOX_DEFAULT
    release
    end
Averon_FieldNotes_Observer::
    lock
    faceplayer
    goto_if_unset FLAG_AVERON_NOTES_STARTED, Averon_NotesViewOnly
    goto_if_set FLAG_AVERON_NOTES_RECORDED, Averon_NotesViewOnly
    setflag FLAG_AVERON_NOTES_RECORDED
    msgbox Averon_Text_NotesRecorded, MSGBOX_DEFAULT
    release
    end
Averon_NotesViewOnly:
    msgbox Averon_Text_NotesViewOnly, MSGBOX_DEFAULT
    release
    end

Averon_BerrySketch_Artist::
    lock
    faceplayer
    goto_if_set FLAG_AVERON_SKETCH_REWARDED, Averon_SketchDone
    goto_if_set FLAG_AVERON_SKETCH_FOUND, Averon_SketchReward
    goto_if_set FLAG_AVERON_SKETCH_STARTED, Averon_SketchWaiting
    msgbox Averon_Text_SketchAsk, MSGBOX_YESNO
    goto_if_eq VAR_RESULT, NO, Averon_SketchDeclined
    setflag FLAG_AVERON_SKETCH_STARTED
Averon_SketchWaiting:
    msgbox Averon_Text_SketchWaiting, MSGBOX_DEFAULT
    release
    end
Averon_SketchDeclined:
    msgbox Averon_Text_SketchDeclined, MSGBOX_DEFAULT
    release
    end
Averon_SketchReward:
    call Averon_BerrySketch_TryReward
    goto_if_eq VAR_RESULT, FALSE, Averon_SketchBagFull
    msgbox Averon_Text_SketchReward, MSGBOX_DEFAULT
    playfanfare MUS_OBTAIN_ITEM
    waitfanfare
Averon_SketchDone:
    msgbox Averon_Text_SketchDone, MSGBOX_DEFAULT
    release
    end
Averon_SketchBagFull:
    msgbox Averon_Text_SketchBagFull, MSGBOX_DEFAULT
    release
    end
Averon_BerrySketch_Observer::
    lock
    faceplayer
    msgbox Averon_Text_SketchHint, MSGBOX_DEFAULT
    release
    end

@ An existing meadow tree, approached from its west side. No new map tiles.
Averon_BerrySketch_Tree::
    lockall
    call Averon_BerrySketch_ObserveTree
    goto_if_eq VAR_RESULT, FALSE, Averon_SketchTreeViewOnly
    msgbox Averon_Text_SketchFound, MSGBOX_DEFAULT
    releaseall
    end
Averon_SketchTreeViewOnly:
    msgbox Averon_Text_SketchViewOnly, MSGBOX_DEFAULT
    releaseall
    end

Averon_BerrySketch_ObserveTree::
    setvar VAR_RESULT, FALSE
    goto_if_unset FLAG_AVERON_SKETCH_STARTED, Averon_EventRewardReturn
    goto_if_set FLAG_AVERON_SKETCH_FOUND, Averon_EventRewardReturn
    setflag FLAG_AVERON_SKETCH_FOUND
    setvar VAR_RESULT, TRUE
    return
@ Callable, UI-free reward boundaries shared by NPCs and native regression tests.
@ A failed claim leaves all saved state and inventory untouched.
Averon_FieldNotes_TryReward::
    setvar VAR_RESULT, FALSE
    goto_if_unset FLAG_AVERON_NOTES_STARTED, Averon_EventRewardReturn
    goto_if_unset FLAG_AVERON_NOTES_RECORDED, Averon_EventRewardReturn
    goto_if_set FLAG_AVERON_NOTES_REWARDED, Averon_EventRewardReturn
    additem ITEM_GREAT_BALL, 2
    goto_if_eq VAR_RESULT, FALSE, Averon_EventRewardReturn
    setflag FLAG_AVERON_NOTES_REWARDED
    return

Averon_BerrySketch_TryReward::
    setvar VAR_RESULT, FALSE
    goto_if_unset FLAG_AVERON_SKETCH_STARTED, Averon_EventRewardReturn
    goto_if_unset FLAG_AVERON_SKETCH_FOUND, Averon_EventRewardReturn
    goto_if_set FLAG_AVERON_SKETCH_REWARDED, Averon_EventRewardReturn
    additem ITEM_ORAN_BERRY, 3
    goto_if_eq VAR_RESULT, FALSE, Averon_EventRewardReturn
    setflag FLAG_AVERON_SKETCH_REWARDED
Averon_EventRewardReturn:
    return

Averon_Text_NotesAsk:
    .string "I'm logging the coast's bird calls.\nCould you check the bluffs for me?$"
Averon_Text_NotesWaiting:
    .string "Ask the HIKER along the high path.\nHe watches the sea every morning.$"
Averon_Text_NotesDeclined:
    .string "No rush! The birds won't mind.$"
Averon_Text_NotesRecorded:
    .string "Wingull calls before a shower.\nI'll note that for the field guide.$"
Averon_Text_NotesViewOnly:
    .string "Rookidee take the high trail.\nThey seem to own the place.$"
Averon_Text_NotesReward:
    .string "Perfect! I'll send this to the lab.\nTake these spare GREAT BALLS.$"
Averon_Text_NotesDone:
    .string "Now to tell Wingull from its echo.\nThat's the tricky part.$"
Averon_Text_NotesBagFull:
    .string "Your Bag's full. Those GREAT BALLS\nwill be here when you return.$"

Averon_Text_SketchAsk:
    .string "I'm drawing the meadow trees.\nWould you look at one for me?$"
Averon_Text_SketchWaiting:
    .string "The boy knows a lovely old tree.\nTake a look if you pass that way.$"
Averon_Text_SketchDeclined:
    .string "All right. I'll keep sketching.$"
Averon_Text_SketchFound:
    .string "Round leaves, a sturdy trunk...\nA good tree for a sketch.$"
Averon_Text_SketchViewOnly:
    .string "The leaves rustle in the breeze.$"
Averon_Text_SketchHint:
    .string "See the old tree below me?\nYou can look from its left side.$"
Averon_Text_SketchReward:
    .string "Round leaves! That helps a lot.\nHere, take some ORAN BERRIES.$"
Averon_Text_SketchDone:
    .string "I made it look a bit taller.\nDon't tell the tree.$"
Averon_Text_SketchBagFull:
    .string "No room for the berries?\nCome back when you've got space.$"
