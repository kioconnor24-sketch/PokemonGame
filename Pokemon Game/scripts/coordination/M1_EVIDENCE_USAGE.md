# M1 evidence tooling — no new gameplay gate

These are **optional independent manager-owned evidence helpers**. They reduce
missing provenance and overclaiming, but **do not** add another mandatory approval
dependency before a developer can code, build, debug or test. Exact merged source,
CI logs and Playtest's own reviewed screenshots remain authoritative.

## 1. Local builds

The existing owner-private `package_local_playtest.sh` now writes an extra file,
`toolchain.json`, alongside `manifest.json`, after its ROM copy. Both stay in
`Pokemon Game/build-output/local-playtest/`, which the script requires to be
gitignored. **Never commit or upload the ROM or a private save.**

```bash
python3 "Pokemon Game/scripts/coordination/toolchain_manifest.py" \
  --repo "." --engine "Pokemon Game/engine" \
  --rom "Pokemon Game/engine/pokeemerald.gba" \
  --out "/tmp/averon-toolchain.json" --strict
```

Reports real `git HEAD`, committed engine-tree SHA, engine dirty state,
available tool versions, ROM SHA-256/byte size. Strict mode returns nonzero
if the engine is dirty, required tools cannot be identified, or ROM is missing.
Without `--rom` it is a SOURCE/TOOL inventory, not build proof.

**Limit:** compiler version + ROM hash is provenance, not proof that this
exact commit was successfully compiled/tested under the stated configuration.
Use actual build and native logs for those facts. Matching stock Emerald ROM
hash is *not* required for modified Averon.

## 2. Graphical gameplay evidence review readiness

Record genuine observed files (produced by mGBA), not fabricated test fixtures.
A development-only synthetic fixture can test the evidence tool itself, but
must NEVER be relabeled as authentic player acceptance.

Example `qa-evidence-input.json`, with relative filenames inside an existing
private evidence directory:

```json
{
  "source_sha": "<exact 40-hex Git source commit>",
  "rom_sha256": "<exact 64-hex ROM hash>",
  "cases": [
    {
      "case_id": "Q1",
      "input_trace": "q1-inputs.txt",
      "screenshots": ["q1-gym-result.png", "q1-reward.png"],
      "state_observations": [
        {
          "statement": "Badge01 and reward state recorded after ordinary player interaction",
          "evidence_file": "q1-state.json",
          "expected": 1,
          "observed": 1
        }
      ]
    }
  ]
}
```

```bash
python3 "Pokemon Game/scripts/coordination/qa_evidence_report.py" qa \
  --input "qa-evidence-input.json" --evidence-root "/private/qa-evidence" \
  --out "/tmp/averon-qa-evidence-audit.json"
```

Missing files, broken PNG headers, duplicate case IDs, SHA format errors,
missing traces/observations or declared expected/observed mismatches produce
`INCOMPLETE_OR_CONTRADICTORY`. Presence of all named files produces
`READY_FOR_INDEPENDENT_REVIEW`, **never a gameplay PASS**.

Review must still verify actual player-input progression, source/ROM provenance,
real badge/reward/party/save facts, fixture honesty, game constraints and
screenshot authenticity. File checks cannot do this. Playtest independently
decides Gate A, Q1–Q5 and Gate B; Manager reviews integration; Claude's local
emulator results may be submitted as supporting evidence.

## 3. GitHub check status triage

```bash
python3 "Pokemon Game/scripts/coordination/qa_evidence_report.py" checks \
  --input "/tmp/github-checks.json" --out "/tmp/averon-check-triage.json"
```

Input is an array of GitHub check objects with `name`, `status`, and
`conclusion`. Any failed check is marked `FAILURE_REQUIRES_LOG_REVIEW`,
not automatically a game bug. Pending checks remain pending; successful
source checks do not imply gameplay acceptance. The **actual log review**
must distinguish engine, script, instrumentation, compiler and runner faults.

## Milestone division

- **Manager:** tools, CI integration, independent review of reported evidence,
  and normal eligible merges.
- **Claude (local):** full M1 engine development; may independently reuse the
  tools above, add genuine mGBA controller traces and *actual* state inspection
  for Q1–Q5 in its claimed local branch. Do not wait on optional manager scripts.
- **Playtest:** independent genuine graphical outcomes, verdicts, and retests.
- **Sinnoh authoring:** map/script/tileset production pipelines remain deferred
  until owner authorizes maps after M1.

No new map, canon, encounter placement, saved ID, or game logic is created here.
