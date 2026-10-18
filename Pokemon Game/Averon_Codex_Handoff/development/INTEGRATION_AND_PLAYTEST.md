> **ARCHIVED PROCESS / SNAPSHOT — superseded 2026-10-18.** Use the [single operating contract](CURRENT_PHASE_AND_HANDOFF.md), [integration queue](INTEGRATION_QUEUE.md) and [#15 live claims](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). All prior “current”, “authoritative”, pause, freeze, manager-only and resume commands below are historical. Retained evidence and approved product constraints are preserved; this file grants no new work or content approval.

---

# Averon integration builds, playtest readiness, and decision queue

**Purpose:** give the two peer developers a reproducible, independent compatibility check without making them wait for one another's full QA/merge. This does not authorize new maps, trainers, story, encounters, or changes to live game save identifiers.

## Combined build: opt-in GitHub Actions or precise trusted team comment

A trusted collaborator can also comment **exactly** `AVERON_BUILD PRS=14,25` on [team Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15). That one explicit message triggers the same disposable paired build with graphical boot enabled. No other text, untrusted account, issue or PR numbers can activate this shortcut. It does NOT launch Codex/Claude/ChatGPT agents or merge a PR.

## Standard manual GitHub Actions run

Open [Actions — Averon combined build and playtest readiness](https://github.com/kioconnor24-sketch/PokemonGame/actions/workflows/averon-combined-build.yml), select **Run workflow**, and choose:

- **Branch:** main
- **first_pr:** `14` (QUEST)
- **second_pr:** `25` (SCRIPTED-BATTLE)
- **graphical_smoke:** true

For a stable-main control, use `0` and `0` for the two PR fields. PRs must exist, be open, and originate from this same repository. The job records each exact GitHub PR SHA; if it changes while fetching, it fails rather than testing the wrong source.

**What it does:** fetches and merges those two branch heads in a temporary GitHub-hosted checkout. It runs `git diff --check`, the existing QUEST/SCRIPTED-BATTLE source contracts, a full GBA compile, actual `make check TESTS=Averon`, and actual `make check TESTS=test/save.c`. After verifying both native suites ran with positive counts, it captures the linker memory footprint, ephemeral ROM size and SHA-256, plus two actual graphical mGBA boot-window frames when requested.

**What it uploads:** the exact source-pin manifest, linker/resource report, real build/native/save logs, evidence-only readiness JSON and optionally two boot PNGs. **Never the ROM, save file, game assets, or secret.** A green job proves its stated build/native/save/limited graphical boot checkpoints only. It is NOT a player-tested QUEST, LEGEND, SCRIPTED-BATTLE scene, two-region travel or Delta iOS release.

**What failure means:** a git conflict or missing source contract belongs to the relevant PR owner; a test/build regression needs a minimal reproduction compared to main and to each feature's known passing branch. An opt-in graphical-boot failure is not proof that quest reward/dialogue logic is broken. Report exact pinned SHAs, failing command, expected/observed and job link on the affected PR. Do not send generalized "please retry" comments or make a developer repeat a build on unchanged source.

**Safety:** opt-in manual dispatch or an exact authorized Issue #15 command limits duplicate 50-minute ARM jobs and additional GitHub Actions consumption. The workflow has read-only GitHub permissions, rejects forks, performs no PR/main push or code review approval, and stores no distributable ROM. Untrusted code from unrelated GitHub forks is not run. Review PR source before dispatch, even for collaborators.

## One-command owner-local development package (WSL)

From a **clean, verified** checkout with the existing ARM toolchain installed, at the repository root run:

```bash
bash "Pokemon Game/scripts/coordination/package_local_playtest.sh"
```

The script stops rather than silently compiling a dirty engine, runs a real GBA build plus positive-count Averon and save tests, confirms linker/ROM budget and SHA, then writes `Pokemon Game/build-output/local-playtest/Averon-DEV-<git-short-sha>.gba`, `manifest.json` and named logs. The output directory and `.gba` are **gitignored and local only**. Copy the private ROM to your own iOS device through your chosen file-transfer method, then import it into Delta for **separate** manual playtesting. There is no guarantee of iOS compatibility from successful local compilation.

If you use Windows and Windows Subsystem for Linux (WSL), this command runs **inside the WSL checkout**, not in a PowerShell window unless Bash and its ARM toolchain are available. A clean committed engine is necessary; never reset or discard unsaved local work merely to satisfy this script. It does not fetch/merge PRs or change your source branch.

## How to produce an actual owner-side playtest ROM

An accepted *development build* can be compiled locally from the exact pinned source SHA and PR heads in the JSON manifest using the project's working WSL ARM toolchain and `make -j4 -O all` from `Pokemon Game/engine`. Verify the local ROM SHA-256 matches that manifest **when reproduced from identical inputs/toolchain**; a different compiler or build environment may yield different bytes and is not automatically an error.

For owner gameplay in Delta on iOS, the project needs a locally available, rights-compliant `.gba` file. GitHub Actions intentionally does not provide one for download. **Actual device test remains separate:** boot, ordinary overworld movement, save→exit→reopen→Continue, wild/trainer battles, named QUEST interactions, battle recovery, persistent progression and repeated failure/retry conditions. Do not call the game ready for final release until an owner-tested Delta run and the relevant content milestones are accepted.

## Independent review checklist before integration

1. **Source integrity:** main SHA, both PR head SHAs, exact changed-file overlap, registry include ordering, duplicate allocations and source-generated file parity.
2. **Build:** GBA ROM exists within 32 MiB; resource checks show actual linker ROM/EWRAM/IWRAM usage; no new native failures.
3. **Save lifecycle:** real native save tests and verified old-save compatibility; no reserved IDs allocated without explicit handoff; correct whiteout/respawn state.
4. **Game-facing behavior:** independent Playtest emulator evidence for actually accessible scenes; no label inflation from synthetic source tests or graphical boot.
5. **Release:** confirm provenance, accessible player route, and a separately verified Delta iOS session. Do not merge features dependent on QUEST until independent Q1–Q5 acceptance and existing protected-source rules are met.

## Owner questions — consolidate, do not interrupt on every issue

| Decision | Current status | Who can proceed while unanswered |
| --- | --- | --- |
| Run during scripted trainer battles | **DECIDED: No running**, normal trainers unchanged. Scoped handoff in [Issue #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6207271002). | Claude implements/test it now, no new owner prompt needed. |
| Operative-chain retry after a mid-chain defeat: preserve defeated operatives or restart the whole chain? | **UNDECIDED.** Requires a real gameplay pacing choice before final registered scenes. | Claude can test both backend recovery policies in synthetic fixtures without canon content or persistent IDs; do not decide story checkpoint semantics unilaterally. |
| Final roster/dialogue and scripted scenarios for Renn, Gym ambush and operative chain | **OWNER-RESERVED.** Under story/Gym/character freeze. | Claude develops generic primitives/tests; no final trainer tables or scenes. |
| Actual Averon/Sinnoh geography and legendary encounter sites | **OWNER-RESERVED.** No maps, including temporary content files, authorized. | Codex/Claude develop verified backend contracts using synthetic IDs or unchanged existing maps. |

**Communication rule:** resolve ordinary source-level technical choices by developers in their own PR with tests. Only collect and present consequential unresolved game-design decisions when they genuinely block user-visible implementation. Do not turn every test, minor engine edge case, or CI failure into a user prompt.

## Division of labor

Codex owns QUEST and the isolated TWO-REGION code. Claude owns SCRIPTED-BATTLE and a file-disjoint backend track. Playtest owns actual rendered UI/quest testing. ChatGPT Manager owns this integration pipeline, independent source/build evidence checks, compatibility triage, safe merges after normal QA and maintaining this compact decision record. All four can work in parallel.
