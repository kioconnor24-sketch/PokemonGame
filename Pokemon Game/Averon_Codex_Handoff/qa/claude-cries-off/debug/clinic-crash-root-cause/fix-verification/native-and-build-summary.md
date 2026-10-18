# PR #124 verification summary (Claude's own runs; head 98329090 = main 30a32203 + fix)

## Full native suite: make -j16 -O check (nice 10), unfiltered
- Tests FAILED:          327
- Tests KNOWN_FAILING:   17
- Tests TO_DO:           421
- Tests EXPECT_FAILING:  9
- Tests PASSED:          5333
- Tests TOTAL:           6108
real	11m37.311s

## New test line from that log
[12] Averon clinic union-room check without InitUnionRoom copies nothing: PASS

## Baseline: python3 scripts/check-averon-native-baseline.py <log>
failing tests in log: 327; baseline entries: 327
OK: matches the Averon baseline

## RED / GREEN: make check TESTS=test/averon_clinic_union_room.c
RED (src/union_room.c reverted, test kept):
[00] Averon clinic union-room check without InitUnionRoom copies nothing: CRASH
GREEN (fix):
[00] Averon clinic union-room check without InitUnionRoom copies nothing: PASS

## Builds
make (normal): EXIT=0; compiler/linker warnings: 0; ROM sha256 60d82e5fc6bb89652979d88360bcc86b1dec68bc0d97c28f80f31cd25792e387
make release: EXIT=0; warnings: 4 (the 4 newlib stub notes: _close/_lseek/_read/_write); ROM sha256 6e37d30ef82455374b5720fb480383eeeac76632acd274f4be91c3a37f134814
