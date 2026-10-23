# Sinnoh donor reuse ledger — 2026-10-23

Implements manager directive [6373183781](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6373183781), not a second world tracker. The master87-site register remains the scope source; none of its historical implementation/approval columns is used as completion evidence.

`SINNOH_DONOR_REUSE_LEDGER.csv` separates actual registered donor maps from uncovered physical construction targets. `SINNOH_DONOR_REUSE_INPUTS.json` freezes actual pinned registry/header/layout/binary facts and committed evidence at current main plus exact live PR heads. The generator reads immutable Git objects; published technical headers exclude all story/object/coordinate/background events. It verifies159 distinct donor definitions,87 master-site coverage, explicit naming aliases, unique row keys and stale receipt source hashes. Snapshot-only rendering needs no donor/network/history and is tested against the CSV byte-for-byte.

Initial pre-batch scan:19 maps on main,49 with matched source stages,91 unstaged. The91 have now been implemented through the merged stager, including two narrow source-defect repairs; see `../design/sinnoh/remaining-donor/CHECKPOINT.md` and the exact receipt. The evidence snapshot is advanced to that committed source batch before final publication. Existing staged/production geometry is never counted as newly built.

`COMMITTED_SOURCE_BOUND_CLUSTER` runtime entries reproduce actual result.json PASS/FAIL counts, profile, ROM hash and exact evidence-file revision/hash. They are historical scene receipts, **not a claim of a fresh test against current main or whole-map acceptance**. Fresh-Continue cases can list the whole cluster while testing only three checks. Production membership is separately read from main's actual Sinnoh registry and does not itself prove runtime acceptance. `UNKNOWN`, untested targets and the unresolved #235 snow bridge visual remain explicit. Art candidate presence means a file exists, not owner visual acceptance. LakeAcuity's zero warps/connections do not make it linked. Source spellings `PokmonLeague`, `FloaromaTwon_*`, `ValleyWindoworks_*` and `TwinleafTown_Haouse1` are retained, with explicit site aliases only.

All unregistered layout declarations were inspected separately against the Git tree. FuegoIronworks has a declared layout but no map.bin; similarly named Hoenn/FRLG VictoryRoad layouts are not proof of Sinnoh geometry. Missing settlement interiors remain explicit aggregate child targets because the87-site scope does not specify an exact floor-by-floor interior count. These targets do not authorize gameplay/services or fabricate floor plans.

Reproduce the frozen CSV without historical Git objects:

```sh
python3 'Pokemon Game/scripts/build_sinnoh_donor_reuse_ledger.py' --inputs 'Pokemon Game/Averon_Codex_Handoff/development/SINNOH_DONOR_REUSE_INPUTS.json' --out /tmp/reuse.csv
```

Refresh evidence intentionally by supplying `--donor <pinned-git-repo> --repo <averon-repo> --refs <JSON-label-to-full-commit-map>` plus the same inputs/output arguments. Fetch the exact main/open-PR heads first; never infer newer state from this dated snapshot. The inputs list every inspected full commit. The generated CSV is a source/reuse/gap ledger, not production acceptance or permission for IDs227+.
