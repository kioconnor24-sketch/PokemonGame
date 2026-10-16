# Pre-Sinnoh release configuration parity

Recovered in Codex Cloud on 2026-10-16 from the tested patch at
`3536aa2565d69396c7f34ea56ab3acab9ac08bfa`, without rewriting its test script.
Applied after [exact-path claim #15](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6212086334)
and checking all live open PR paths and Claude inheritance claims. No production
code changes. The dedicated `Averon release configuration parity` workflow runs
on engine/parity changes in PRs and main, or by manual dispatch. It uses read-only
permissions and uploads only JSON/text evidence.

## Reproduce

After building repository-generated headers, with ARM GCC and host GCC available:

```sh
python3 scripts/test-averon-release-config-parity.py --engine engine --mutations --report release-parity-results.json
```

The script uses ARM GCC preprocessing with the real include order, MODERN=1,
EMERALD and TESTING=0 in both development and RELEASE configurations. The host
compiler executes extracted production functions under ASan/UBSan. Compilation
errors and missing generated headers fail the command rather than skipping checks.
The retained cloud toolchain is selected by `. /workspace/.onboarding/activate.sh`.
This traced cloud executor needs `ASAN_OPTIONS=detect_leaks=0` for the host probes:
LeakSanitizer otherwise fails under ptrace before tests complete. ASan bounds and
UBSan checks stay enabled; this is not a leak-test claim.

For a clean checkout, the workflow builds only the upstream `mapjson` and
`jsonproc` tools, then generates the required map-group/region-section constants
from existing unchanged inputs. The map generator's assembly and heal-metadata
side effects stay in a temporary directory; its ignored map-count header is a
normal generated prerequisite. No maps/layouts, assets or ROM are authored.
The workflow fails if tracked engine files change. It needs no emulator or ROM
assets; the ARM compiler/newlib packages are still required for preprocessing.

## Observed evidence

Source snapshot: codex/backend-safety-integration
c1d3460297a289a0e7fa7db62bdbeb2a8e5914b3. Its three safety fixes have matching
patch IDs with Claude's stack; none is reapplied by this candidate. Relevant
battle/header source files are unchanged from main 7f4ecc44. ARM GCC 14.2.1.

- Development production configuration (TESTING=0): 139 checks PASS.
- RELEASE production configuration (TESTING=0): 139 checks PASS.
- Twelve configuration mutants and five production-function mutants: 17/17
  DETECTED by assertion failures, including making the gimmick guard test-only.
- Exact source-file SHA256 values and compiler version are retained in results.json.

Fresh recovery run on main `7f4ecc44270e98b2363fc49cb708aa4d9a3527fa`:
the unchanged script again passed 139 development + 139 release assertions and
detected all 17 mutations. ARM GCC 14.2.1, host GCC, ASan/UBSan; no native or
graphical suite was rerun for this script/documentation-only change. The original
checkpoint retains per-file digests, test output, safety review and release log:
[3536aa25 evidence](https://github.com/kioconnor24-sketch/PokemonGame/tree/3536aa2565d69396c7f34ea56ab3acab9ac08bfa/Pokemon%20Game/evidence/cloud/20261016-release-parity).
A separate tracked-files-only scratch checkout also passed header generation,
139+139 assertions and 17/17 mutations, without retained generated headers.

Checks cover Gen V held-item EXP Share configuration and disabled team-share
flag lookup; hard-cap/candy configuration and MAX_LEVEL=100; configured Gen I-IX
families, regional forms, Mega enablement, disabled Primal/Ultra forms; release
removal of debug overworld entry; extracted CanActivateGimmick behavior for all
four battlers, all gimmick enum values, callback permission/denial/null cases;
and extracted battle initialization forcing Set while preserving existing fields.

Native test configuration intentionally overrides species/form settings. These
checks use TESTING=0 so those overrides cannot establish release evidence.
Gigantamax/Tera form data flags are not treated as authorization to activate the
corresponding battle gimmick; the production activation gate is tested separately.

## Limits and next gate

This is source-preprocessed host execution, not a linked release-ROM build or an
emulator run. Reduced callback/state fixtures do not verify production struct
layout, dynamic GetConfig behavior, complete EXP allocation, candy enforcement,
form rendering, every possible activation path, save compatibility, resource
budgets, or Delta acceptance. Existing native/graphical suites remain required.
A separate real `make -j5 -O release` of snapshot c1d34602 passed with LTO
enabled: 33,554,432 bytes, SHA256
`c467cf2d672f281c4b18df2d254eb56673848417e174b5635c08f5f5fdd2f53f`.
Linker EWRAM 226418 B, IWRAM 28328 B, linked ROM 26849028 B. Compiler warnings
are retained in the checkpoint release-build.log.gz; they were not silenced.
This does not prove release gameplay. No new native suite, graphical acceptance
or backend-ready claim is made for this candidate. Capture EXP and final regional numeric caps remain
owner decisions and are deliberately not assigned values here.

Next: pass normal PR checks including the production parity workflow.
Then exercise independently owned release gaps only
after checking current claims. Do not edit Claude's save/travel/mechanics or
Playtest files; no maps, saved IDs, or protected files are allocated here.
