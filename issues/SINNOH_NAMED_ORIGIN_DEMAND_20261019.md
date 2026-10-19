# Sinnoh named-origin capacity: executable decision evidence

Codex, 2026-10-19. X02 from the merged [work packages](../Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_DEVELOPER_WORK_PACKAGES.md). This is a read-only planning tool and decision packet, not allocation, a migration, or a complete child-map inventory. Existing IDs 0–214, NONE215, Sandgem216 and special met codes253–255 retain their meanings. Route201217 is already owner-approved in #150, but was still draft when measured.

## Reproducible demand, not raw map counts

Input main source `aebdd89bd368f7e7ec49b4d2c28cc2f82011dc08`; unchanged 87-row register SHA256 `174213decc8984602896130ee617db0d9a0ffccfb81646cff56875bd31482df4`; section JSON SHA256 `885c5ac0f02404b0acdc7e46afb0b6d86449b9e321c4d7fe0fcc6783cddf19ee`. Later navigation/governance-only main commits do not change these inputs.

Run from repository root:

```sh
python3 'Pokemon Game/scripts/audit-averon-mapsec-namespace.py' --check-pins \
  --planned-area-register 'Pokemon Game/Averon_Codex_Handoff/development/SINNOH_AREA_REGISTER.csv' \
  --json /tmp/sinnoh-origin-all.json
python3 'Pokemon Game/scripts/audit-averon-mapsec-namespace.py' --check-pins \
  --planned-area-register 'Pokemon Game/Averon_Codex_Handoff/development/SINNOH_AREA_REGISTER.csv' \
  --origin-kinds SETTLEMENT,POSTGAME_HUB,ROUTE --json /tmp/sinnoh-origin-main-names.json
```

Both actually exited **1**, explicitly reporting an exceeded *planning* budget; neither means the existing ROM is broken. Existing no-scenario audit exits0. Malformed scenario input exits2. All seven saved-ID pins pass. No legacy holes or historical “reuse candidates” are treated as available.

| Explicit naming scenario | Distinct names | Already assigned Sinnoh | Additional names | Available216–252 | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: |
| 15 settlements + 3 postgame hubs + 30 routes, current main | 48 | 1 | 47 | 36 | **11** |
| All87 tracker labels remain distinct, current main | 87 | 1 | 86 | 36 | **50** |
| Same48, temporary combined #150/#151/#154 source | 48 | 2 | 46 | 35 | **11** |
| Same87, temporary combined source | 87 | 2 | 85 | 35 | **50** |

Combined source is the pushed recovery experiment `81ddd4235c9b8f7a41fc8e59e89c89ed637bd196`, not accepted main. Its section JSON was read directly from Git; no production maps or names were authored by this experiment. Allocating approved217 both consumes a code and satisfies one planned name, so it does not change the deficit. Two currently built maps share Sandgem216; the combined three maps use two origin names. Map counts therefore cannot estimate met-origin demand.

The48-name scenario already exceeds capacity before any caves, lakes, landmarks, distinct floors, new Averon locations or additional child names. The87-name scenario is a fidelity choice, **not proof exactly87 codes suffice for full Sinnoh**. Child sites can share a parent origin, as Sandgem Center already does; distinct child origins and remaining Averon demand must be added explicitly. The tool accepts `--additional-origins` (JSON list) and `--origin-reserve N` for those declared inputs. It never invents them or labels the inventory complete.

Names normalize Unicode NFC, case and whitespace only. Geographic grouping must be an explicit `--origin-aliases` JSON object keyed by tracker key. Existing saved Sinnoh names cannot be regrouped or expanded to another registered area. Same-spelled legacy **Pokémon League** and **Victory Road** are reported as collisions, not reused as Sinnoh origins: doing so would silently change saved meaning/region.

## One owner decision, with existing experimental evidence

**Recommendation:** retain the approved bounded byte allocations now; authorize a separately reviewed, tagged extended-origin engineering project if distinct full-atlas place names are desired. Do not adopt an encoding until old/imported records, all consumers, and special codes can be distinguished unambiguously. The current codebook alone cannot preserve even48 distinct main-place names. A deliberately coarser immutable codebook is the alternative if the owner accepts reduced future origin precision; no grouping is selected here.

| Approach | What it buys | Proven limits / decision cost |
| --- | --- | --- |
| Current append-only byte policy | Preserves all old meanings and structure sizes; Sandgem216 and approved217 remain valid | Only37 total new ordinary names216–252. Main has36 left; #150 consumes one. Does not accommodate48 distinct main-place names. |
| Wider runtime section IDs + immutable byte met-origin groups | More physical/UI sections can map to a smaller saved-origin vocabulary without enlarging saved Pokémon | Still only37 new saved names. Must deliberately group future places; cannot later recover erased detail or regroup216/217. Runtime MapHeader, map grids and TV consumers are also byte-sized today. Owner must accept precision policy and approve the codebook before allocation. |
| Tagged extended saved origin, possibly13 bits | Prototype can physically carry8192 values in existing encrypted bits | **No safe version/import policy is implemented.** Previously used spare bits can be nonzero with a valid checksum; hatching leaves proposed high bits stale; byte API/controller/summary paths truncate. “Unused bits” is not a migration strategy. |
| Enlarge saved Pokémon records | Could provide explicit space/versioning | Requires owner-approved schema/migration and old-save/import strategy. Conditional 80→84-byte BoxPokemon growth costs at least420×4=1680B in PC boxes, already112B beyond measured1568B storage headroom, before four stored fusion party records grow. Exact final alignment/layout is not established. |

Reuse merged executable experiments; they are not new successes of this PR:

- [#130 compatibility report](../Pokemon%20Game/Averon_Codex_Handoff/development/SINNOH_LOCATION_ID_COMPATIBILITY_20261018.md): byte getters truncate0x1234, extended0x1FD aliases the egg code, fresh battle-controller recipients lose high bits; summary/hatching/runtime-header consumers also need auditing.
- #134 source `b6dd5dabdb1592ad7d533252dd26a2ed78fa8372`: **3/3** focused native tests, all24 encryption permutations and PC/rekey preservation; checksum-valid legacy spare-bit ambiguity and stale hatch-high-bits reproduced. CI **267/267**, run39172261690/job117807613859/artifact12152842735; ZIP SHA256 `c25dd5ef2e20de400b883c4a8547900d0da0fcdea3f96ac1b9179b1cb16ceb23`.
- #141 source `17449dfc61e929ac09f47912622735bf5de52ace`: **2/2** focused native tests, all256 legacy bytes preserved, but two wide origins sharing one group byte become indistinguishable after PC→flash→party→summary. CI **266/266**, run39173797907/job117812198389/artifact12153751862; ZIP SHA256 `55fffe8c8390a14f1a302f8f12c34042221d53d9869fb5784edceda508029d61`.
- These test sources remain `engine/test/averon_location_compatibility.c`, `averon_extended_location_experiment.c`, and `averon_grouped_origin_experiment.c`; see the [prior checkpoint](CODEX_RESUME_CHECKPOINT_20261018.md). Older research claims that five spare bits imply migration-free compatibility are superseded by those actual negative results.

An extended-origin project must cover encrypted checksum/permutation/rekey; party/PC/fusions; trade/import and battle-controller payloads; eggs/hatching/daycare; summary caches and exact special-value comparisons; runtime map/header/TV widths; old/corrupt saves and cross-version writes. SaveBlock sizes and Pokémon structures are unchanged here. Neither lossless backward downgrade to older ROMs nor compatibility with arbitrary external GBA trades is established. The owner decision is **distinct future origins with a separately validated extension, or deliberately grouped future origins with an immutable approved vocabulary**; the specific version tag and implementation need evidence rather than a speculative commitment now.

## Delivered tool and verification

New `scripts/averon_origin_demand.py` implements name-demand scenarios; the existing namespace CLI gains optional inputs and JSON evidence while retaining its default path. New temporary-fixture regression module covers exact fit/overflow, read-only inputs, legacy-name collisions, frozen-name protection, duplicate/missing keys, reserved bytes, unknown filters and real CLI exit/output behavior.

Actual local commands, Python3.12.14:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s 'Pokemon Game/scripts/tests' -p test_sinnoh_origin_demand.py -v
PYTHONDONTWRITEBYTECODE=1 python3 'Pokemon Game/scripts/test-audit-averon-mapsec-namespace.py'
```

**28/28 new and18/18 existing identities PASS, zero failures.** The existing standalone suite prints one expected `PIN ERROR` for its deliberate mutation. Normal no-scenario CLI, fitting temporary scenario, both real overflow scenarios, and invalid/frozen temporary inputs were executed. No production maps, codebook, workflow, engine, generated headers or save bytes change. No new GBA build, graphical/Delta run or native result is claimed for this host-only work; actual #154 and temporary-combination ROM/native measurements are in the [travel evidence](CODEX_SINNOH_RESUME_REGRESSION_20261019.md).

The current source-check workflow does **not** discover this new28-test module automatically. Its GitHub checks provide their actual syntax/guard coverage; they must not be relabeled as execution of these28 local tests. A future CI-wiring change is separable and governance-reviewed if needed.

Next executable action: owner selects precision direction once; meanwhile continue disjoint resource/pipeline work and existing approved216/217 integration. No speculative production encoding or further permanent identity allocation is part of this PR.
