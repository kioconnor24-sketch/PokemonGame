# Acceptance and test matrix

Only mark a test **PASS** after executing it in the compiled target. 'Code appears correct' or 'data file exists' is not a pass. Add actual emulator build/revision, save state and reproduction steps.

## Binary and environment
- [ ] Pinned `pokeemerald-expansion` build succeeds from fresh checkout and documented toolchain.
- [ ] Actual file has `.gba` format and boots to title/new game in mGBA; checksum/hash and build path recorded.
- [ ] Map renders, audio works, D-pad moves, menus and battle function, no blank screen or crash.
- [ ] Cold boot + native in-game save/load + reset preserve party, location, badges and flags.
- [ ] Delta on user iPhone imports and launches the same authorized build; separate evidence from local mGBA.
- [ ] Release patch can be applied to correct, legitimately owned base where applicable; no Nintendo ROM bundled by mistake.

## Design-data integrity
- [ ] `python3 scripts/validate_design.py` exits zero.
- [ ] Main 8 Gym route is connected at the appropriate unlock times and never requires a badge not yet available.
- [ ] Every map warp pair arrives in a walkable location; station/ferry destinations cannot send player into walls.
- [ ] Every side area accessible eventually; no unreturnable caves, tide traps, rift, waterfalls or cliffs.
- [ ] Distinct palette/tileset/art identity; no empty loops, placeholder tiles or unreviewed off-style assets.

## Progression and difficulty
- [ ] Gym badges always awarded after legitimate battle and persist on whiteout, including post-Nadia ambush.
- [ ] Before each milestone, level cap prevents all overlevel sources (battle, EXP item, candies, daycare, NPC gift, trade/evolution etc.).
- [ ] **No free switch prompt**, always Set behavior; test Singles, Doubles, Gym, rival, League, tournament.
- [ ] Original held-item EXP Share behavior tested for all six slots, with/without item and on cap.
- [ ] No mandatory HM in Pokémon moveslots; player can learn Surf/Cut etc for battle if desired.
- [ ] Smart trainer switching and move choices are strong but legal; no omniscient lookahead to input selection.
- [ ] Actual playthrough pacing tested for parties of 3, 4 and 6, beating ~65%, 80%, 100% visible trainers.
- [ ] Typical team can reach level ~100 near Red without excessive grinding, no early required overcap.

## Opening, player and follower
- [ ] All permutations of first visit to three houses consistently award intended Snivy/Fennekin/Piplup.
- [ ] Starter assignment persists through save/reload and visiting houses afterward does not change it; refusal/party-full cases safe.
- [ ] Renn picks a type advantage starter and Mira the third every time; consistent subsequent evolution and battles.
- [ ] Follower selection updates with front party changes, is hidden on bikes/Surf/cutscenes where required, and never blocks doors or stairs.

## Story and cutscene edge cases
- [ ] Renn's scripted loss always progresses even if player uses an unexpected move/ability/item; Nuzlocke exception and money protection correctly applied.
- [ ] Dorian's help is self-interested; later discovery correctly occurs; no explicit early revelation.
- [ ] Nadia's two-mon illegal follow-up starts without healing, is recoverable after loss, and leaves badge.
- [ ] Coup flags swap limited environment/NPC visuals without blocking shops, Centers or map connections.
- [ ] Only two mandatory post-coup reactions, both short; old NPCs still have ordinary lives.
- [ ] Player directly obtains key blueprint evidence; Calder supports but does not solve everything.
- [ ] Renn rigging revelation happens before final assault; his later reaction is not instant redemption.
- [ ] Ten sequential single-Pokémon operative battles preserve party HP/status and maintain checkpoint resilience.
- [ ] Ally healing happens *after* tenth opponent and before corrupt leader rematches, only once per gauntlet phase.
- [ ] After first boss four Pokémon, device malfunction seamlessly transitions to short dimensional dungeon; no residual active-battle corruption.
- [ ] Player and party survive dimensional ambient energy because it isn't the test-subject-killing concentrated pulse.
- [ ] Final Vale loss/win and Giratina return do not softlock or consume player party/items unexpectedly.

## Species/forms and quests
- [ ] Complete generated National Dex spreadsheet for each officially supported Gen IX species + relevant alternate forms; every family has at least one solo catch/evolution route.
- [ ] Trade-only, version-only and external-event evolutions have solo alternatives usable on Delta.
- [ ] Battle sprites/icons/followers/moves/abilities/typing evolutions audited at actual runtime; no broken missing species textures.
- [ ] Megas activate/deactivate correctly, no Z-Move, Dynamax, Gigantamax or Tera mechanics active.
- [ ] All legendary/mythical quest flags and catch methods pass; missing legends rejected by audit.
- [ ] Jirachi **Odd Key** acquired via Vesper store route, door in actual map opens and quest works after correct condition.
- [ ] Heatran is in Ashfall Caldera Depths, Celebi in early forest revisit, Zygarde origin story and catchable arc distinct.

## Postgame and narrative
- [ ] Entire Sinnoh map, 8 Gyms, Cynthia, second League and progress flags function across saves.
- [ ] Champions' Circuit repeatable after completion, gauntlets offer meaningful variation and fair rest rules.
- [ ] Red identity not stated in prior lore hints; final level-100 battle plays after correct milestones; no canonical boss supersedes him.
- [ ] Dialogue proofread for text overflow, repetitive catchphrases, implausible solemnity and excessive foreshadowing; most NPCs unrelated to plot.
- [ ] Art/audio attribution documented with legal sources and clear omissions/stand-ins if unavailable.

## Defect severity
P0 = white/black-screen boot failure, crash, softlock, corrupt save, unobtainable critical badge; P1 = entire required quest/region broken, moves wildly incorrect, overlevel cap bypass, major visual wrong; P2 = dialogue overflow, missing noncritical sprites/optional legend, difficulty concern; P3 = cosmetic punctuation/animation polish. No P0/P1 release. P2 may only remain documented as known issue with explicit user approval; complete game is not 'finished' otherwise.
