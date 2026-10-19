# Optional reciprocal seam contract for new map batches

Codex, 2026-10-19; base `1cbd690161045eebe3cccf0f46f53cbb6aeecc19`. Owner Phase4 task12. Existing #125/#126 tooling remains the implementation: add one opt-in policy, rather than another validator. No maps, scripts, identifiers, save bytes, generated output, Claude QA files or CI/governance changes.

The existing read-only map preflight reports a missing reciprocal cardinal connection only as a review warning. This preserves deliberate legacy one-way geography, but a developer checking a new connected batch can accidentally accept a broken seam because exit status remains0. Add **`--strict-connections`** (and keyword `strict_connections=True`): missing return becomes an error; more than one reciprocal edge to the source becomes an ambiguity error. Existing inverse-offset, overlap, registry/layout/metatile/warp/section checks stay active. The report states the selected connection policy.

The default remains unchanged: one-way cardinal edges still require review, not automatic rejection. Strict mode is a deliberately narrower construction contract, not a claim that every duplicate/one-way edge is inherently illegal in the engine. It covers cardinal up/down/left/right seams only; dive/emerge, dynamic/script transitions, collision, accessible seam tiles and graphical stepping still need their existing review/QA. An unselected neighbor's return metadata is inspected, but its entire geometry is audited only when selected too.

Actual commands from repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s 'Pokemon Game/scripts/tests' -p test_averon_map_readiness.py -v
python3 'Pokemon Game/scripts/audit-averon-map-readiness.py' \
  --engine 'Pokemon Game/engine' --group gMapGroup_Sinnoh --strict-connections
python3 'Pokemon Game/scripts/audit-averon-map-readiness.py' \
  --engine 'Pokemon Game/engine' --group gMapGroup_AveronOpening --strict-connections
```

**53/53 host tests PASS** (47 retained +6 new identities). New negative fixtures modify source documents **in memory**, never production maps: missing return in an unselected target; duplicate reciprocal edge; one valid inverse offset beside an invalid second return; retained nonoverlap/wrong-inverse failures. Positive fixture checks both actual integrated groups. A CLI fixture verifies strict-policy forwarding and nonzero exit on a broken seam; it mocks only the audit result, not graphical acceptance. Existing default one-way warning test remains unchanged.

Actual strict source scans: **3 Sinnoh maps /82 dependencies /0 errors /0 warnings** and **16 Averon maps /165 dependencies /0 errors /0 warnings**. Selected-map dependency hashes are in the tool's existing JSON output; no new saved IDs are consumed. `git diff --check` PASS. Existing source CI compiles the Python module but does not automatically execute this53-test suite; these results were actually run locally and are not relabeled as CI. Current GitHub guards remain separate merge conditions.

This R1 host-only improvement can integrate through the existing normal Fast Lane A after final-head checks. It does not certify #166, future maps, licensing, ordinary travel or gameplay acceptance. Recommended construction command: select **all** maps in the intended connected batch and use strict mode, then perform actual NORMAL/RELEASE/native/MAP-QA and Save→fresh Continue as applicable. No change to the broader map approval or review policy.
