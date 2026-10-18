> **Historical (superseded, Claude 2026-10-18).** This is Codex's checkpoint from before the takeover. Its "NOT ELIGIBLE TO MERGE" / "PENDING" status is out of date. For the current evidence and status, see `Pokemon Game/Averon_Codex_Handoff/qa/claude-cries-off/README.md` and the PR #117 description. The text below is unchanged.

# Reversible cry safety — pushed checkpoint, 2026-10-17

PR [#117](https://github.com/kioconnor24-sketch/PokemonGame/pull/117), branch `codex/reversible-cries-safety-20261017`. Build/source evidence pinned to `d84f6d52ae5ad02c6690fc46487f7ce5a5d9c527`, engine tree `4f092611d8039bcd1a7a5790f16f7c890929fb93`. **DRAFT / NOT ELIGIBLE TO MERGE.** The owner requested this immediate durable checkpoint; work continues.

## Implemented

`StopCry` and cry polling refuse NULL player submissions. Script wait/task cleanup retain their normal bounded behavior. OFF cries no longer lower BGM volume, including unpaired duck APIs. Default TRUE and enabled behavior retained. No RAM/save/ID/map changes or Claude source edits. All cry sources, definitions, species associations and tables retained.

Explicit `make -j8 -O RELEASE=1 CRIES=on` / `CRIES=off` isolate both object directories and output filenames. `CRIES=default` preserves existing builds. Invalid/multiple values are rejected. ON/OFF are reversible from the same source without deleting/restoring assets. Do not adopt OFF as the production default before policy gates.

## Actual results

| RELEASE | Linked bytes | Free under32MiB | Change from prior matched study |
| --- | ---: | ---: | ---: |
| ON | 26,855,116 | 6,699,316 | +192 B |
| OFF | 17,438,548 | 16,115,884 | +272 B |

Current exact saving **9,416,568 B**. All **530 music/effect song objects** and **156 non-cry samples** match byte-for-byte. ON links1,156 cry sample blobs; OFF links zero. Both EWRAM226,486 / IWRAM28,336 B. SB1/SB2/SB3/PC free304/**84**/1,556/1,568 B unchanged. RELEASE has the inherited4 newlib stub warnings; builds succeed.

ON ROM `cec3be3dd3814f7967c59d0c955de026c6323e77af04c2c27a42b83a644a89a1`

ON ELF `e427c8dd18511b9e0aeff3f550bea8c2d4f49c880aa801223dc88ab0a2d0fc3b`

OFF ROM `c0ee9c231a6d3bf5fb272b3afe5b5fb302932664fdbdf70b192007d4d04e545d`

OFF ELF `8c852ac12189b148931603c09355051f067157866d3cbe3ee1ca82499c52390f`

- Old source + isolated OFF config: **6 PASS /2 FAIL** identities. Probe caught3 NULL stops/3 NULL polls before unsafe reads; independent BGM regression failed21 vs64 volume. GBA open-bus behavior can otherwise hide NULL reads. Not a claim of observed graphical crash.
- Fixed source OFF instrumented: **10/10 PASS**, zero NULL stops/polls. Native-only linker wrapper delegates all valid pointers to the real driver.
- Real UNWRAPPED native ON **9/9 PASS**, OFF **9/9 PASS**; each16 parameter cases; `headless=0` actually logged. Covers cold stop/poll, script wait/replay, real playmoncry→waitmoncry bytecode, absent species, all14 cry modes and Mega lookup, unpaired duck, title/town/route/battle/victory/heal starts and menu/door SFX. These are API/native proof, not full gameplay acceptance.
- Host **17/17 PASS**. Invalid profile strings rejected. Standard CI protection/source/routing checks passed atd84f6d52; native CI still running. No baseline or guard edited.
- An additional OFF native save/compatibility/corruption/flash recovery batch is **RUNNING**, not yet a final result.

## Actual graphical attempts and remaining gates

Signed Debian packages made graphical mGBA0.10.5/Xvfb/xdotool available locally. Use tool network permission for the local GDB socket; the sandbox-isolated attempt could not bind it. Codex wrapper reuses Claude driver READ-ONLY and resolves only unique exact ELF `.lto_priv.N` variable aliases, with3 host tests.

On the NEW cries-ON RELEASE, real input completed fresh naming/opening/harbor/parcel/Piplup reception; rendered screenshots, frame-stamped input trace and actual mixed audio were captured locally. It displayed **saved the game**, and the closed emulator wrote a complete flash slot1 (all14 IDs, signatures, counter1). The driver then falsely rejected save status0: actual RELEASE disassembly of TrySavingData proves LTO removes writes to `gSaveAttemptStatus` because production never reads it. This is an **observer limitation**, not reproduced save corruption. The original failed run remains labeled FAILED. Next: verify actual save-success callback plus fresh Continue. Do not modify protected save.c or weaken Claude checks.

Cries-OFF graphical gameplay, fresh Continue, battle entry/faint/capture, evolution, Mega, Pokédex cry UI, cry-dependent moves/scripts, town/route/battle/victory/heal audio, followers and complete requested scene coverage remain PENDING. Human listening and Delta are UNTESTED. Independent source review has been requested; no review/merge fabricated.

Full safe machine evidence: `Pokemon Game/scripts/coordination/codex_cry_evidence_20261017.json`. No ROM/ELF/save/audio binary uploaded. Local raw artifacts/logs under `/tmp/averon-cry-*`; source worktree `/workspace/averon-rom-capacity`.

## Exact next commands

Activate `/workspace/.onboarding/activate.sh`. Focused native build requires all FOUR runner sources (`test_runner.c`, `test_runner_battle.c`, `test_runner_args.c`, `test_test_runner.c`) plus `test/averon_cry_safety.c`; TESTS=`Averon cry safety`. Run the ELF directly with `/workspace/.onboarding/mgba-rom-test`, without make check's headless patch; parse positive counts because the runner can return0 despite a failed test.

`python3 Pokemon\ Game/scripts/coordination/codex_cry_profiles.py Pokemon\ Game/engine --output /tmp/cry-profiles.json` compares both built RELEASE profiles.

Finish the RELEASE save observer and Continue; execute OFF graphical coverage, then independent review/CI before any integration. If a required runtime gate remains blocked, retain draft and take a separately claimed noncontent Phase2 capacity/registry task. Permanent-ID decisions remain owner-reserved.
