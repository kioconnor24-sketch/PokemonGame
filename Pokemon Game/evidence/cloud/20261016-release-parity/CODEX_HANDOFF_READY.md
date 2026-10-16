# CODEX_HANDOFF_READY

Session: cloud-20261016-release-parity. All commands ran in Codex Cloud.
Branch: codex/cloud-release-parity-20261016, based on main
7f4ecc44270e98b2363fc49cb708aa4d9a3527fa. No main merges or protected edits.

## Recoverable commits

- 540b8935113776536e606115ffa07c6484750265: complete ready-to-apply release
  parity candidate, per-file source digests, positive test output, safety logs.
- 1bfafe25520c4494df5cdcf5822244dd13594eb2: read-only source review, exact safety patch IDs and fresh visible
  CI outcomes for #50/#51/#52 (including cancelled/skipped/unavailable states).
- This checkpoint commit adds final release-build evidence and this handoff.

Files in these commits are confined to
`Pokemon Game/evidence/cloud/20261016-release-parity/`.
The source/test implementation remains a patch because the required Issue #15
claim could not be posted. It applies only to these two NEW paths:

- `Pokemon Game/scripts/test-averon-release-config-parity.py`
- `Pokemon Game/Averon_Codex_Handoff/qa/PRE_SINNOH_RELEASE_PARITY.md`

## Proven results

Tested snapshot: codex/backend-safety-integration
c1d3460297a289a0e7fa7db62bdbeb2a8e5914b3. Relevant battle/config source is
unchanged from refreshed main. No #56 region-save/travel implementation is
included in this snapshot.

- Real ARM preprocessing against production include order, TESTING=0:
  development 139/139 assertions, RELEASE 139/139 assertions.
- ASan/UBSan host execution of extracted production EXP-share gate, gimmick
  gate and Set initialization; 12 config + 5 function regressions detected,
  17/17 mutants. A test-only gimmick gate is detected in actual release mode.
- Saved patch applies cleanly; reconstructed script passes both modes.
- Save-sector host ASan/UBSan 8/8; Fly host 8/8 groups, 1543 assertions plus
  synthetic special destination, 6/6 mutants. Both underlying commands exit 0.
- Real RELEASE build: exit 0; 33554432-byte private ROM, SHA256 c467cf2d672f281c4b18df2d254eb56673848417e174b5635c08f5f5fdd2f53f. Linker: EWRAM:      226418 B       256 KB     86.37%, IWRAM:       28328 B        32 KB     86.45%, ROM:    26849028 B        32 MB     80.02%. Full compiler warnings retained in release-build.log.gz; no new native/graphical/Delta claim.

No new native suite, graphical QA, Delta or complete backend readiness is
claimed. Host fixtures do not prove production struct layouts, dynamic
GetConfig resolution, full EXP/candy paths, form graphics, or every gimmick
activation route. Native test headers deliberately enable extra forms; the
candidate prevents that configuration from substituting for release evidence.

## Blocking gates and ownership

Public GitHub HTML and native Git fetch/push work. The active proxy still denies
api.github.com. The saved network draft is not applied to this instance. Thus
Issue #15 claims, PR creation, Issue #54 CODEX_CHECKPOINT/comment and final
CODEX_HANDOFF_READY comment could not be published. This Git branch/commit is
the durable checkpoint; no comment or PR creation is implied.

Two source reviewers found no correctness defect in safety #50/#51/#52. Fresh
visible build/hygiene checks pass on their exact heads; required-review policy,
required approvals, merge permission and authoritative mergeability remain
unverified. All remain open and show No reviews. Do not merge from these host
results alone. Patches already exist unchanged in Claude's stack: never
cherry-pick them again there. See safety-review.md for exact SHAs and patch IDs.

Claude retains all current #56 save/travel and #48 Pokémon/mechanics paths;
Playtest retains #20/#23 graphical QA. No source/test/map files in those scopes
were edited. No implementation file claims were published or reserved by this
session. This handoff releases the prepared parity lane; this session stops
writing it after pushing the checkpoint. Claude must refresh #15/#54, compare
current heads and post its exact takeover claim before applying the candidate.
No maps, story, art, saved IDs, final caps or protected source changes are in it.

## Next executable tasks

1. Restore the supported GitHub API route, publish exact-path claim and link this
   checkpoint in #15/#54. Refresh current Claude ownership; do not replay work.
2. Apply release-config-parity.patch on a new owned branch from fresh main,
   run the documented script, create a scoped PR and normal checks. Reuse it
   rather than rewriting. Check patch prerequisites if headers/config changed.
3. Check review/protection/merge gates for #50 -> #51 -> #52; integrate only
   once after normal authorization, then notify Claude of the verified main SHA.
   Keep QUEST and Claude save/travel QA/merge gates separate.

No scheduler is available in this environment. GitHub comments do not restart
agents; an owner-started cloud session or actual supported scheduling is needed.
