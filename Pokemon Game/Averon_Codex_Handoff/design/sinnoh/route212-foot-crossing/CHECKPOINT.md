# Route 212 South foot crossing — SOURCE / DEV only

Contract: PR291 `0089e5ff88ab3d511975fe37f23ca176127e01a3`, Issue15 comment6408018613. This packet composes the existing thirteen-map eastern scene without changing its original artifacts, Claude's W17 mansion or any engine/production file.

Exactly (38,11) changes from F24C (horizontal rail) to F001 (existing General plain ground). Collision0 and elevation15 are unchanged; all other cell words, rails, map headers, warps, connections, graphics banks, IDs and registry bytes remain identical. This is the contract's permitted bridge-height crossing; visual and bicycle behavior still need genuine runtime evaluation. Original source SHA25633ca15c567c5a28eec9cae20589db3bf94fe07e6b5ef372913eeee23af7a7d97; patched6bc8df49ac8947767fc2ac9cd7698fdc4b6019a4eb1a70d30e52c34ea0b78b8f.

## Executed evidence
- Five focused HOST tests PASS,135.707s: original rail-aware exit-unreachable reproduction; patched thirteen-map static audit with zero findings and every map reachable from Pastoria-side South(129,12); exact one-cell/C/E preservation; wrong/already-patched source refusal; collision mutation restores failure; existing Hotel Grand Lake world/ghost-frontier audit remains clean.
- Two added HOST tests PASS,0.143s: committed map/receipt reproduce exactly; changed source bank semantics rejected before input mutation. Total7/7, no skipped cases. No whole-game native or ROM claim.
- `python3 Pokemon Game/Averon_Codex_Handoff/scripts/validate_design.py`: PASS design CSV/connectivity. Initial obsolete scripts/validate_design.py location absent; used actual canonical path.
- Actual CLI export PASS into new off-engine /tmp directory. No production installation.

Tests scope PR300's exact five Acro-only behavior exclusions onto the existing World class without editing shared QA. Pending PR300 is not represented as merged. Original uncorrected source fails the same rail-aware audit; closing just the new crossing restores the failure. Existing plain-ground and rail full attributes are checked, not inferred from raw IDs.

## Integration use and outstanding gate
Call `prepare_crossing.assemble(repo, acro_fixture=False)` instead of eastern-loop.prepare_runtime.assemble: it returns the same overlay files/receipt plus the guarded one-cell change. Alternatively replace only generated data/layouts/Route212_South/map.bin with the committed route212-south-map.bin after verifying the original hash, before W17 composition. No new installer or protected-source bypass is supplied. Never copy into an active/dirty production checkout.

Existing eastern assembler remains pinned to its audited nineteen-production-map engine inputs; newest main6ada35bed504c17ea517b0239b514134481e6b05 contains source-only integrations, but no latest-main installation is claimed here. Original pending-owner sections and DEV217 surrogate remain as before; this allocates no saved identity.

NEXT: normal review/checks; integrate this composition in W17's disposable joined scene; run NORMAL/RELEASE Pastoria→South→North→mansion and return, bicycle/upper-layer/follower checks, Save→fresh-process Continue. Claude paused; no session restarted. No ROMs/private saves uploaded. Local disk~7MiB prevents safe full ROM builds; retain unique private archives rather than delete them.

## Exact current QA follow-up
Re-ran all7 crossing tests against the actual Git-blob-verified Python modules from PR300@a0a1bcc20d4a46f2161402006acc2a70d1d83683: **7/7 PASS242.785s**. This includes that version's elevation-aware traversal, not merely the five-behavior predicate scoped onto the older local QA. PR300 independently reviewed/tested (33 map_qa PASS;39 claude_play run,38PASS/1 existingSKIP), normally squash merged as7e919fd21b2702f4db2b82d5d2cc80c5223c1a6a. GitHub initially returned504 during merge; authoritative reread/API result confirmed the merge. No protection bypass. Initial isolated-review setup errors (symlink resolved to older local modules, absent fixture directory, sandbox socket restrictions) corrected before the reported passing exact-head runs; no game defect inferred from those errors.

## West22 integration follow-up
This preserved source packet is now reused by the eastern assembler itself on the PR306 child compatibility branch. Every original staged donor/native-art file stays unchanged. Updated compose receipts hash the actual patched output; standalone assemble recognizes the already-composed receipt instead of applying twice. Original nineteen-slot evidence above remains historical. New22-slot runtime-recipe-west22.json is separate. No production geometry or gameplay acceptance added.
