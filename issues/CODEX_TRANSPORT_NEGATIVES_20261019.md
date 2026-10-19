# Transport refusal hardening and integrated compatibility

Codex, 2026-10-19. Runtime/test source `5f21a9238bf1723959ed69312ae48926711b5073`, based on actual merged transport `bd705ed5b0987b7a7dcc071d553d5bd89cdcb2d4`. This is a separate R2 change: Claude's review of #163 does **not** approve this new behavior. A targeted independent source review and newest applicable checks are required before normal integration. No maps, scripts, saved identities, encoding, migrations, Claude files or CI changes.

## Reproduced gap and narrow fix

Inject inconsistent state: active/physical Sinnoh at Sandgem, but `lastHealLocation` names real Averon Alderfield. Previously the adapter accepted travel to Averon; the unchanged low-level transaction then cached Alderfield as Sinnoh's healer, so the next return would be refused by the existing wrong-target-healer check. The new focused native refusal assertion actually **FAILED1/1** on unchanged production code (`test/averon_transport.c:261`, EXPECT failed). See issue55 comment6273033934. This is a deliberately malformed-state reproduction, **not a naturally reproduced current gameplay failure**: no ordinary script activates this adapter yet.

Add9 production lines before the transaction: if the departing last-heal warp is a **recognized** healer, validate its physical region with the existing point validator; refuse an inconsistent source before any write. Unrecognized coordinate arrival fallbacks remain permitted. No auto-clearing, save rewrite or competing travel transaction. A preexisting wrong-target-healer record still requires explicit correction; this patch prevents creating a new one through this adapter, not a migration/recovery policy. Low-level direct callers remain unchanged.

The regression requires exact refusal, byte-preserved state, then explicitly corrects the source healer to44 and proves a normal outbound/return with the captured Sandgem healer works. Legitimate visits and repeat travel in both directions remain exercised.

## Missing test boundaries now covered

- Every refusal snapshot now compares the raw **64-byte record and8-byte anchor**, in addition to decoded state/location/heal/escape/position. Pending warp comparison now includes `warpId`.
- Same-coordinate wrong-map case uses real40×32 Alderfield at(18,18), which passes physical shape validation, so it reaches the active-map identity check. The prior10×9 greenhouse case failed geometry first.
- An indexed departure with deliberately inconsistent matching(-1,-1) player coordinates is refused without mutation; first-arrival indexed destinations remain supported.
- Wrong target healer is tested **both ways**, including actual Sandgem44 in an Averon record. After explicit correct target selection, leave/revisit remains usable. Sinnoh-start fixtures now use actual healer44.
- New TEST-only metadata fixture compiles the **actual adapter source body**, under private names, substituting only its metadata lookup. Shared shape validation still uses real linked maps. A copied in-memory header exercises NONE, the current table boundary and0xFD–0xFF; each must fail despite Hoenn's display fallback. No ROM header writes, disposable production maps or production injection interface. This body-reuse fixture does not claim the immutable real map header was corrupted in gameplay.

Snapshot preservation applies to initialized records (NewGame/load), as in the existing adapter contract; the preexisting lazy initialization of a never-initialized record is not relabeled byte-preserving.

## Executed tests and actual builds

Commands from `Pokemon Game/engine`, activated GCC14.2.1(20241119), GNU ld2.44/newlib4.5.0.20241231:

```sh
make -j4 -O check 'TESTS=Averon transport refuses a physically wrong departing healer' ROMTEST=/workspace/.onboarding/mgba-rom-test
make -j4 -O check 'TESTS=Averon transport' ROMTEST=/workspace/.onboarding/mgba-rom-test
make -j4 -O check 'TESTS=Averon' ROMTEST=/workspace/.onboarding/mgba-rom-test
make -j4 -O RELEASE=0 all
make -j4 -O RELEASE=1 all
```

Actual RED before fix: **1 failed/1 total**. After fix: **11/11 focused identities PASS**,28 parameter combinations plus the257 region-input loop; **309/309 complete Averon-filter identities PASS**, zero FAIL/ERROR/SKIP. The previously integrated306 and intermediate test-only308 runs also passed; these are different source/test sets, not duplicate claims of a new unfiltered M1 baseline. Strict expected-failure baseline is unchanged. Existing native suites cover legacy saved origins/IDs, encrypted party/PC, save-slot interruption/rollback, progression, followers, held EXP Share and field/menu behavior. No graphical/ordinary travel/human audio/Delta acceptance is invented.

Both actual ordinary **cries-OFF** profiles PASS on this source. NORMAL0 warnings; RELEASE4 existing newlib syscall-stub warnings. The adapter is still unused and linker/LTO removes it, so activation cost remains unmeasured.

| Profile | Linked ROM / free B | EWRAM / IWRAM B | ROM SHA256 |
| --- | --- | --- | --- |
| NORMAL |17326872 /16227560|226480 /28392|`b59523623853c03652d6321c497ecc2b63f3e995b15faf531fe503ed9febf19a`|
| RELEASE |17446008 /16108424|226482 /28336|`f1ef364e4f641d04d48a2c652e7c01db191edf6028d44a5d09b72dd7e8a6ab30`|

Both ROM hashes and linked budgets are **identical to the actual #163 integrated proof**;0 incremental linked/RAM/save bytes. SaveBlock1/2/3/PC remain15568/3884/68/34144B with304/84/1556/1568B free. ELF SHA256 NORMAL `c41307d99c35bd3575c5a533429f7df53c6ff08d0847ae38b54b12b718605419`, RELEASE `5a86ba2b20b49a46fa5746318a4a6d7e71fe18b824469272906e480d1b2a2a36`. An independently scoped host reporter enhancement verifies each ELF's3 ROM load segments against its actual ROM and exact linker ROM extent; mixed log/ROM/ELF inputs were rejected. It does not authenticate caller source labels or claim gameplay acceptance.

| Source file | SHA256 |
| --- | --- |
|`src/averon_transport.c`|`69b746f672ff99f22f2930dad622ac63366497450b1ecd36269513a5e7b44d85`|
|`include/averon_transport.h`|`36287909eaa837c8cce997007bfd25363fa3bc1e569778f226523cee53df14d0`|
|`test/averon_transport.c`|`ac47d0ee4800227b22cec7c699ff2fb7c8816706cf28d56fc69efce64a10c158`|
|`test/averon_transport_metadata.c`|`4aaeceaa5b25a7736f65ac2c248e982ad56ab91ec77a64a07abe7ae95f8bbd30`|

No ROM/ELF/private save is uploaded. Workspace evidence: `transport-departing-healer-red.log`, `transport-hardening-focused.log`, `transport-hardening-all.log`, `hardening-{normal,release}.{log,json}` under `/workspace/averon-session-evidence`. Final remote SHA, current CI and peer outcome belong in the PR handoff, not invented in this report. WAITING_ON targeted peer review + exact-head checks; RESUME_WHEN they pass, refresh main/collisions and merge normally. Continue disjoint engineering meanwhile.
