# Field-license developer fixture runtime results — 2026-10-15

Scope: FIELD backend prototype, PR #10. This is not a completed region,
full Gym walkthrough, final travel map or Delta iOS acceptance.

## Exact artifact and execution

- Game/test source: `5c92e6ffa02b1c120704ea0871a377ddcfe6a7a7`.
- Local ROM: `build-output/Pokemon-Averon-Field-Menu-5c92e6ff.gba`.
- Size: **33,554,432 bytes**; SHA256:
  `86800da9ec7531feabe5ef59fc0ceec0b4d2a188ac01d088567b3e3568e3dada`.
- Executed that identical ROM in Windows **mGBA 0.10.5**, using an isolated
  copy at `evidence/field-runtime/averon-field-runtime.gba` and copied test save.
- Inputs used the existing `scripts/mgba-smoke.lua` public frame/key/screenshot
  API. No game RAM was written. An additional local Lua callback read native
  object coordinates for diagnostic logging only.
- Snivy level 6 knows **Tackle and Leer only**, verified in the actual summary
  screen (`field_summary_moves.png`). No HM moves were taught for these tests.
- The source save `evidence/m2/averon-first-gym.sav` was preserved. Only the
  isolated save was overwritten. ROMs and saves are not published.

## Observed checks

All screenshot names below are under local `evidence/field-runtime/`.

| Check | Observed outcome | Evidence |
| --- | --- | --- |
| Normal party / Field Kit | Both action windows render legibly with seven traversal actions and Cancel | `field_mon_actions.png`, `field_kit_open.png` |
| Locked Cut action | Returned to party selection without applying an effect; native tests separately verify all seven locked actions | `field_cut_locked.png` |
| Cut | Native prompt, used-move text and effect completed; tree removed and controls resumed | `field_cut_offer.png`, `field_cut_effect.png` |
| Rock Smash | Native prompt/effect completed; rock removed and following Pokemon remained present | `field_rock_offer.png`, `field_rock_effect.png` |
| Strength | Activation text completed; pushing moved the boulder and player one tile | `field_strength_close.png`, `field_strength_push_test.png`, `positions.log` |
| Surf | Native prompt/animation put player onto water at (17,10); follower hid | `field_surf_offer.png`, `field_surf_effect.png`, `positions.log` |
| Waterfall | Ascended actual waterfall from (20,10) to (20,6), then descended to (20,10) | `field_waterfall_offer.png`, `field_waterfall_effect.png`, `field_waterfall_descend.png`, `positions.log` |
| Dive / emerge | Reached enclosed underwater map at (20,12), then surfaced to the same coordinates | `field_dive_effect.png`, `field_emerge_effect.png`, `positions.log` |
| Follower land recovery | After dismounting Surf and stepping onto land, Snivy reappeared behind the player | `field_follower_land_recovery.png` |
| Fly cancellation | B from Fly map returned to the normal party selection screen; menu could reopen | `field_fly_cancel_runtime.png` |
| Fly actual execution | Placeholder LITTLEROOT destination used native flight and landed in SALTMERE at (18,18); controls returned | `field_fly_final_home.png`, `field_fly_execute.png`, `positions.log` |
| Native save / reset / Continue | In-game save completed; emulator reported SAVE_DATA_UPDATED; reset/Continue restored Saltmere and updated save time | `field_save_complete.png`, `field_reload_menu.png`, `field_reload_continue.png`, `emulator-actions.log` |
| Persisted Fly access | After reset/Continue, Field Kit opened Fly and the visited home destination remained available | `field_reload_fly_home.png` |
| Safe exit from menus | Cancelled Fly, party and start menus after reload; normal overworld remained active | `field_reload_field_ready.png` |

## Independent native and build evidence

- Local `make check -j12 TESTS=Averon`: **43/43 named tests PASS**, zero failures
  in the final run. Includes all seven independent licenses, actual flash
  persistence, locked/unusable actions, healthy partner rules, maximum menu
  capacity, Back/B, second-slot Fly cancellation, native destination selection,
  actual terrain preparation and obstacle target safety.
- Local `make check -j12 TESTS=test/save.c`: **4/4 PASS**, save layout unchanged.
- Normal `make -j12 -O all`: PASS. EWRAM 226420, IWRAM 28392,
  linked ROM 26729636 bytes under local ARM GCC 14.2.1.
- Clean GitHub native build/test run **38764296123**, head `705e4585`: PASS;
  job **116523357694** log confirms **43/43** named tests. Source, readiness
  and PR hygiene workflows also passed. CI uses its own documented toolchain;
  its binary hash/resource footprint is not substituted for the local artifact.
- Initial optional-NPC-follower test assumption failed because that human NPC
  feature is disabled in the actual build. Corrected the test to respect the
  production setting; enabled Pokemon followers were tested separately above.

Status: **BUILD / NATIVE-TESTED / EMULATOR-TESTED for this developer fixture**.
**DELTA NOT TESTED.** Final license earning locations, world-map graphics,
regional destination registry and production progression remain separate tasks.
The Fly-map Hoenn label is an explicit temporary fixture, not final geography.
Broader game balance, first-Gym natural walkthrough and long-term gameplay QA
remain outside these field-license results.