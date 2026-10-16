# Pokémon Averon — cloud Codex handoff

Prepared 2026-10-16, America/New_York. This is a source/evidence checkpoint,
not a claim the game or backend is finished. Live GitHub instructions and
exact current file claims supersede historical ownership in this document.

## 1. Start here: ownership changed while Codex was inactive

Repository: https://github.com/kioconnor24-sketch/PokemonGame

Project prefix in this repository: `Pokemon Game/`. Engine: `Pokemon Game/engine/`.

**Do not resume the old Codex save assignment. Claude has already inherited
and implemented it in PR #56.** The owner approved isolated implementation
and testing, but did not authorize automatic merge or waive independent QA.

- [Issue #54 — dynamic Codex re-entry](https://github.com/kioconnor24-sketch/PokemonGame/issues/54): a returning Codex must refresh live state, select a currently unclaimed task and post an exact-path claim before editing.
- [Issue #15 — live claims and protected-file handoffs](https://github.com/kioconnor24-sketch/PokemonGame/issues/15): current exclusive claims override stale tables and former Codex ownership.
- [Issue #53 — inherited engineering backlog](https://github.com/kioconnor24-sketch/PokemonGame/issues/53): Claude's active work, known gaps and source-backed integration audit.
- [Issue #46 — pre-Sinnoh backend acceptance](https://github.com/kioconnor24-sketch/PokemonGame/issues/46): completion criteria, not permission to create content.
- [Issue #23 — independent graphical QA](https://github.com/kioconnor24-sketch/PokemonGame/issues/23): Playtest owns acceptance. Issue #31's generated ownership labels can be stale.
- [Issue #55 — problem desk](https://github.com/kioconnor24-sketch/PokemonGame/issues/55): candid reports and manager triage.

Current Claude claim: [#15 comment6209724674](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6209724674).
Leave `global.h`, `save.c`, `load_save.c`, `new_game.c`,
`averon_region_save.{h,c}`, its native test and host script alone unless Claude
explicitly releases the exact files. Claude also owns SCRIPTED, LEGEND and
Pokémon mechanics. Playtest owns QA code and rendered workflows.

The latest pasted owner brief identifies this chat as coordinator/reviewer.
For a cloud instance assigned implementation, follow #54; for a manager
instance, review/coordinate without becoming a competing author. A cloud
handoff does not itself reassign Claude's claimed work.

## 2. Project goal and non-negotiable boundaries

Build a real Emerald Expansion GBA game: Averon first, full Sinnoh later.
Finish feasible map-independent backend first. **All new maps, temporary
layouts, geography, story/dialogue expansion, encounters, Gym rosters, final
numeric level curves, legendary placement and new art remain frozen.**

Preserve normal Pokémon tone and the design documents. Requirements include
Gen5 held-item EXP Share, level100 maximum, forced Set, following Pokémon,
Mega Evolution and modern supported mechanics; no Z-Moves, Dynamax,
Terastallization, Primal Reversion or Ultra Burst. Do not invent creative
answers, permanent saved IDs or numeric cap policies.

Read the applicable root/project AGENTS.md and CODEX_WORK_ORDER.md. Reuse
READING_LOG.md and concise checkpoints; do not restart initial setup or reread
all design files. Read a design section only when relevant or changed.

Use recoverable feature branches; no direct main push, force push, guard
bypass, automatic merge or invented evidence. Keep ROMs, saves, secrets and
build caches out of public GitHub/Releases. Native/build evidence is distinct
from graphical mGBA and owner-run iPhone Delta acceptance.

## 3. Exact inherited source checkpoints

Main observed through `git ls-remote` while preparing this file:
`7f4ecc44270e98b2363fc49cb708aa4d9a3527fa`. Fetch again; this is not a promise
main or any PR is unchanged when the cloud session starts.

| Source | Exact checkpoint | Meaning |
| --- | --- | --- |
| `codex/two-region-groundwork` | `fc3e4a5f7d3d2ff57763bf08383f5609b2ede04f` | Pure region queries, native/flash fixtures, save guard copy, map/event contracts; normal gameplay region hooks largely unregistered |
| `codex/backend-safety-integration` | `c1d3460297a289a0e7fa7db62bdbeb2a8e5914b3` | Region groundwork plus unchanged safety #51/#52; #50 already present |
| `codex/region-save-integration` | `c1d3460297a289a0e7fa7db62bdbeb2a8e5914b3` | Baseline only; **no region-save implementation was added by Codex** |
| PR #50, `codex/save-sector-bounds` | `3c9d43de89eb41b4198a1c5056ee7cd8af1086ea` | Actual save-sector signature/ID guards |
| PR #51, `codex/field-fly-fixture` | `1ba7bf9cf2adf629a1e5456863e746bd2c9c2127` | Native Fly fixture heap fix; no production gameplay change |
| PR #52, `codex/fly-destination-bounds` | `476ba941c671cf6fdae709726c50a658d4dbcd08` | Actual Fly table guards in both paths |
| PR #14, `codex/quest-event-framework` | `db6baaea45e54100cdcbe220f575d28a824bb229` | QUEST draft; final branch change was whitespace-only |
| PR #56, `claude/region-save` | `88fb8140d5ce0fc5e972ef18a4813f1515206888` | New active Claude save implementation; refresh checks and changes |
| `claude/region-travel` | `c5a8e45290cd39bd1b1c1159ab3318119fc30bcd` | Claude reports compiled, untested travel transaction; do not duplicate |

PRs #14/#50/#51/#52/#56 were open/unmerged when inspected; #14 and #56 were
draft. Separate copies of #50/#51/#52 also exist in Claude's safety/save
stack. Compare patch IDs before reuse; never apply a safety fix twice.

## 4. What Codex actually completed and tested

### Production safety changes

- **#50:** guard invalid signatures/sector IDs before indexing the14-entry
  save table, in copy and both validation loops. Native57/57, including10 new
  named tests and112 real-flash corrupt-footer combinations; save-layout4/4;
  host ASan/UBSan8/8; GBA successful. Original source failed negative controls.
- **#51:** a0x884-byte automatic RegionMap overflowed the small native test
  stack under an unrelated1573-byte BSS shift. Reproduced bad task pointers;
  heap allocation/free passed the same pressure fixture. Compiled stack frame
  dropped2220→44 bytes. Final native47/47, save4/4, GBA successful.
- **#52:** `sMapHealLocations` has192 rows, but real Saltmere209 and
  Alderfield213 indexed past it. Guarded FilterFlyDestination's default
  lookup AND SetFlyDestination's fallback. Invalid IDs preserve the prepared
  warp; explicit special cases retain behavior. Native52/52, save4/4, GBA;
  host1543 exercises plus1 synthetic high-special fixture,6/6 mutants killed.
  Real Frontier is58, in range; do not call the synthetic relocation a real
  high-index destination. Guard-only footprint+8 ROM bytes,0 RAM.

These are source/native reproductions, not observed graphical player crashes.
Earlier missing-handoff guard failures for #50/#52 were subsequently resolved
by owner-specific authorization. Recheck current PR checks, not an old green
or red snapshot.

### Region groundwork

Owned pure module: `engine/include/averon_region_fixture.h`,
`engine/src/averon_region_fixture.c`, `engine/test/averon_region_fixture.c`.
It provides independent8+8 badge queries/capture; map-region resolution;
regional Fly eligibility; full-width warp validation; healer/fallback selection;
separate caller-supplied level-cap and obedience selection.

Native fixtures exercise real flash rollback and existing heal/whiteout APIs;
synthetic Sinnoh identities are RAM descriptors, never real maps. No persisted
Sinnoh bank or final caps were installed by this prototype.

Latest separate region run: **88/88 native**, all112 distinct corrupt-footer
tuples, save4/4, host32/32, mutations24/24, normal GBA successful. Healer IDs
over255 and map group/number over127 are rejected before narrowing into engine
APIs; representable boundaries and safe fallback are tested.

`scripts/test-averon-map-registry-contract.py`:17/17, checks stable group/order,
generated IDs, signed map/warp bounds, saved object capacity64 versus active
sprites16 and conflicting generated event macros. Existing16 Averon maps
measured max7objects/4warps. No map data was changed.

### Combined run finished after the usage interruption

At **c1d3460297a289a0e7fa7db62bdbeb2a8e5914b3**, local final logs were inspected
while preparing this handoff:

- Full Averon **93/93**; native save-layout **4/4**.
- Save host sanitizer8/8; Fly host exercises passed,6/6 mutants killed.
- GBA build completed: linked ROM26,729,660B, EWRAM226,420B, IWRAM28,392B.
- This stack does **not** include Claude's later PR #56 save schema. Do not
  transfer its4/4 save-layout result to the68-byte SaveBlock3 implementation.
- Region helper remains unregistered/linker-discarded in normal gameplay.

Local logs: `evidence/combined-codex-safety/{all-averon,save-layout,gba-build,save-host,fly-host}.log`.
Those local evidence directories are not guaranteed to exist in a cloud clone.
The source and checkpoints are pushed; use CI text logs or reproduce as needed.

## 5. Save approval, proposal and current Claude implementation

Codex's source-linked diagnostic measured ABI sizes:
SaveBlock1=15568, SaveBlock2=3884, old SaveBlock3=4, storage=34144.
Sector4096 = primary3968 + SB3extra116 + footer12;14 sectors/slot,2 slots.
Primary checksum does not cover SB3 extras:62816 primary single-bit faults
detected versus1856 extra single-bit faults undetected in the host probe.

Proposal: `Averon_Codex_Handoff/development/REGION_SAVE_INTEGRITY_PROPOSAL.md`
on the region/combined branches. Preserve existing4-byte SB3 prefix; use an
existing8-byte checksum-covered SB2 anchor at0x90 and a64-byte serialized record
at SB3 offset4. Include version/CRC/counter/trainer binding, whole-slot rollback,
legacy provenance and explicit unsupported-version policy.

**Owner approval was explicit:** “Approve isolated implementation and testing.”
Recorded in [#15/6209235704](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6209235704).
It was then inherited by Claude, not revoked and not a new Codex claim.

Claude's [PR #56](https://github.com/kioconnor24-sketch/PokemonGame/pull/56)
now contains real save code. Its description reports13/13 focused native tests
(131 parameter runs), GBA success and10/10 contract tests, with one detected
counter-coherence mutation and other mutations/full-suite work still pending.
**These are Claude-reported results, not independently rerun here, and the
description may lag head88fb8140. Refresh exact-head evidence.** It also reports
uninstalled cap/obedience/Fly/whiteout hooks and misleading existing “erased” UI
for unsupported saves; none should be called resolved on this handoff.

Read [Manager audit #53/6209836444](https://github.com/kioconnor24-sketch/PokemonGame/issues/53#issuecomment-6209836444):
whole-slot staging before RAM publication, unique IDs/coherent counters,
early ASLR trainer-ID selector, every normal/link/HoF/partial save entrypoint,
and old-writer provenance require specific proof. These are acceptance risks;
do not accuse the new implementation without inspecting it.

## 6. QUEST, other modules and graphical acceptance

QUEST has two traditional optional errands, not a journal/HUD. Preserve code
and story. Playtest independently reports Q2 tree/artist reward exactly3 Oran
and no duplication; genuine SAVE/Continue with restored artist DONE; Q1 no-badge
gate; Q4 refusal, real Wobbuffet gift and no duplicate. Full Q1–Q5 remains
PARTIAL: positive Badge01/Hiker reward, full pockets/full party, exact post-load
inventory, real whiteout, controls/follower/audio have remaining cases.

Do not inject flags/party/items to make graphical QA pass. Debugger stalls after
reset are reported harness problems, not proof of game-save failure. Screenshots
with dummy audio cannot prove sound. Read current ledger, not just job color.

Portable QA handoff now exists on `chatgpt/emulator-smoke-playtest`:
`Pokemon Game/Averon_Codex_Handoff/development/PLAYTEST_QA_CHAT_HANDOFF.md`.
See [#15/6211112048](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6211112048).

Claude owns #25 SCRIPTED, #47 LEGEND, #48 Pokémon readiness and their live
claims. Do not duplicate their state machines, follower/EXP/Mega tests or save
implementation. #14/#25 both touch protected event_scripts.s: textually
disjoint hunks do not remove the path-level gate. No QUEST merge before
independent acceptance; sequential review/registration still required.

Outstanding owner choices include final cap/obedience relationships, evolution
accessibility, capture EXP behavior, Mega Ring content and follower art. No
percentage-complete claim is justified. Backend ready is not full game ready.

## 7. Cloud bootstrap and practical continuation

Cloud needs authenticated repository access and its own Linux toolchain. Windows
paths, local WSL caches, attachments, ROMs and emulator state do not transfer
automatically. This handoff does not claim a cloud environment is configured.

```sh
git clone https://github.com/kioconnor24-sketch/PokemonGame.git
cd PokemonGame
git fetch origin
git branch -r
```

Refresh #15/#23/#46/#53/#54 and open PR changed files/checks. Follow the role
assigned by the owner. For engineering, choose a genuinely unclaimed task,
post exact files, then create a codex/ feature branch from the appropriate
reviewed source. Do not start from an old main and recreate branch work.

For reproducing the completed Codex combined snapshot only:

```sh
git switch --detach c1d3460297a289a0e7fa7db62bdbeb2a8e5914b3
# If required, install the same dependency classes used by repository CI:
sudo apt-get update
sudo apt-get install -y build-essential binutils-arm-none-eabi gcc-arm-none-eabi libnewlib-arm-none-eabi git libpng-dev python3
cd 'Pokemon Game/engine'
make -j4 -O all
make -j4 -O check TESTS='Averon'
make -j4 -O check TESTS='test/save.c'
cd ..
python3 scripts/test-averon-fly-destination-bounds.py --include-dir engine/include --mutations
python3 scripts/test-averon-save-sector-bounds.py
python3 scripts/test-averon-region-fixture.py
python3 scripts/test-averon-region-mutations.py
python3 scripts/test-averon-map-registry-contract.py --generated-header engine/include/constants/map_groups.h
python3 scripts/test-averon-save-extra-integrity.py --engine engine
```

Generated headers require a real build first. Use engine/INSTALL.md and its
Ubuntu instructions plus `.github/workflows/averon-native-build.yml` as the
source of setup commands. Reuse working cloud dependencies; do not reinstall
or rerun unchanged full suites merely to show activity. Different compilers
can produce different ROM hashes; record source/toolchain/hash separately.

Native runner permission, positive discovered counts and completion must be
checked. Never accept0 tests or a partial log as a pass. Use persistent jobs
for long runs and one build per working directory. Do not globally kill other
developers' processes. Full-suite baseline failures must be interpreted using
the existing expected-failure checker; do not dilute it to conceal bugs.

**Next engineering choice:** follow #54 Lane A/B/C/D after checking current
claims. Good candidates are a disjoint cross-feature regression on actually
available interfaces or a concrete unowned field bug. A proposed new
`test/averon_backend_safety.c` was claimed but NEVER written by Codex; do not
assume it exists or reserve it without refreshing claims. Actual save work is
Claude's. If no independent engineering scope is assigned, complete evidence
review and routing without editing claimed code.

## 8. Evidence transfer, limits and final prompt

Private local ROM examples, neither published nor proof of graphics:

- Fly476ba941:33554432B, SHA256 `fe7bcc6ee5c54796395552c9288f26d24573d6298890fefb197ce72f3851fd4e`.
- Regionaedf281c:33554432B, SHA256 `025d3e7f8d29d85f567ed000ee4ddf9f41ced08dfe6173d4502aa796f8c3415d`.

Latest earlier Codex handoff: [#41/6209127076](https://github.com/kioconnor24-sketch/PokemonGame/issues/41#issuecomment-6209127076).
It predates Claude's save takeover; use this document's ownership correction.
Firsthand problem report, with reproduced issues, attempts and suggestions:
[#55/6211029495](https://github.com/kioconnor24-sketch/PokemonGame/issues/55#issuecomment-6211029495).
The local session really hit a usage/approval-review limit; that was not a
determination that Git operations were unsafe. No reset, paid reload or credits
were purchased. GitHub comments do not wake agents. No ongoing automatic cloud
coding or schedule is promised.

Suggested first message to cloud Codex:

> Read this handoff, applicable AGENTS.md and live Issues15,23,46,53,54 before
> editing. Preserve current Claude/Playtest claims. Do not reimplement regional
> save PR56 or safety50–52. If assigned engineering, claim one currently
> unowned exact-file task, implement and test it, push a recoverable codex/
> branch and report source/build/native/graphical evidence separately. If
> assigned coordination, review and route without competing edits. Do not
> merge gameplay, invent acceptance, create maps or publish ROMs/saves. Leave
> an exact SHA, remaining gates and next executable task at interruption.
