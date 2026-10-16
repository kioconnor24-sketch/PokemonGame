# Safety review, 2026-10-16 cloud run

Current main observed: 7f4ecc44270e98b2363fc49cb708aa4d9a3527fa.
Read current public Issues #15 and #54, including dashboard updated 08:43 UTC.
No repository implementation claims or issue comments were posted: API writes
are denied by the active environment proxy. Git fetch/push and public HTML work.

Two read-only source reviews found no correctness defects in these changes:

| PR | Head | Stable patch ID | Copy already on Claude safety stack |
| --- | --- | --- | --- |
| #50 | 3c9d43de89eb41b4198a1c5056ee7cd8af1086ea | d797a3e8b696e9ac9ba2804e1b159d5d0b9110ef | 62177aed1e9a9ac2904eee6046e59b39497a7b35 |
| #51 | 1ba7bf9cf2adf629a1e5456863e746bd2c9c2127 | 4dd500846b51646c211a9f4d9f347feb8453f524 | 6b4d44c7eb99369e4e8ee1b1d19aba453fc9de45 |
| #52 | 476ba941c671cf6fdae709726c50a658d4dbcd08 | e6987be5a688df3e09a6f7fc6a265106843feb4e | 7feda0c429cad7e872312b684068b0ae6aa5190b |

They touch disjoint paths. Source blobs match the existing Claude safety stack.
Do not cherry-pick them again on either combined stack. #50 checks signature and
sector index before table access/copy, retaining signed-corrupt classification;
#51 moves the test fixture RegionMap to the tracked heap and frees it; #52
bounds-checks both default Fly lookups without disabling explicit special cases.

Fresh public exact-head checks observed at 08:49 UTC:

| PR | Observed checks | Other outcomes |
| --- | --- | --- |
| #50 | exclusive-files SUCCESS 116846350019; python-source-checks SUCCESS 116811345688; native-build SUCCESS 116811343744; file-guard SUCCESS 116811344570 | route CANCELLED; weekly audit SKIPPED |
| #51 | exclusive-files SUCCESS 116815655282; native-build SUCCESS 116815659163; file-guard SUCCESS 116815658956 | no source-check job listed; route CANCELLED; weekly audit SKIPPED |
| #52 | exclusive-files SUCCESS 116846357957; python-source-checks SUCCESS 116830658659; native-build SUCCESS 116830660328; file-guard SUCCESS 116830659836; route SUCCESS 116830659973 | weekly audit SKIPPED |

All three PRs were OPEN and displayed No reviews. Required approval counts,
required-check policy, merge permissions and authoritative mergeability were
unavailable in signed-out payloads. Existing scoped approvals in Issue #15 do
not establish those missing repository gates. No merge or approval was issued.

Independently executed on combined source c1d3460297a289a0e7fa7db62bdbeb2a8e5914b3:
- Save-sector host ASan/UBSan: 8/8 named tests PASS (process exit 0).
- Fly host ASan/UBSan: 8/8 groups, 1543 exact assertions, synthetic high-index
  special case PASS; 6/6 source mutations detected (process exit 0).
- These are host-source tests, not new native or graphical save/Fly acceptance.
