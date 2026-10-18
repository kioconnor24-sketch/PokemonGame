# run08: stopped by Claude, kept as partial evidence

**Build:** RELEASE `CRIES=off` from merged head `c77fbd69`, ROM `06e3e40a…`. **Save:** run02's RELEASE save `73c3b87d…`. **Phases:** `heal catch2 train8 sam heal save`.

**What it shows, from real input on the fixed RELEASE build:**
- **The first clinic heal after power-on completed with no crash.** This exact trigger crashed every unfixed RELEASE attempt.
- Two more clinic heals completed, also with no crash.
- Several wild battles ran to their end screens. The Piplup lost some of them and respawned through the normal clinic path.

**Why it was stopped (a QA driver defect, not a game defect):**
- LTO renames static functions, so on RELEASE the battle controller is `HandleInputChooseAction.lto_priv.N`.
- The driver compares controller names exactly, so its **action-menu** logic never ran: no Poké Ball and no run. The default A presses picked FIGHT. The move menu (`HandleInputChooseMove`, plain name under LTO) still worked, so the driver chose moves normally: there are 46 `turn` events.
- With no Pokémon caught, the catch phase then looped toward the shop. The log showed no new events for 18 minutes, so the wrapper was interrupted (SIGINT).

**Fix:** the wrapper now reports functions by their source names (`use_source_function_names`, with a test) and the driver is unchanged. Normal builds were never affected. Battles, capture, trainer and save on RELEASE are rerun as run09.
