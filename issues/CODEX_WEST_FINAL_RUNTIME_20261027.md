# West packet final source verification — 2026-10-27

Tested #306 head `0e3d74d6faabfb79f828176dff08637493b9439b`, after normally merging reconciliation #325. Engine tree `320fc1f48b1d1da85a83bcf943dbb30103379e0f` is identical to build source `e119fab5a867538df689d70f9e16edfba6ff9670` and Claude's cdbbd490 candidate. Every one of30,450 tracked engine files was verified after both actual builds. No production or Claude source bytes changed during reconciliation; the three additions remain slots19–21, preserving all19 earlier registrations, section221/223 and save layouts.

## Actual results

| Check | NORMAL | RELEASE |
|---|---:|---:|
| Real six-map controller traversal, seams, warps, followers, game SAVE |69/69 PASS|69/69 PASS|
| Fresh-process CONTINUE restores game-written state |3/3 PASS|3/3 PASS|
| Separate actual native menu-task/action-list, B return, unchanged source flash |3/3 PASS|3/3 PASS|
| Unmodified original legacy flash CONTINUE/state |3/3 PASS|3/3 PASS|
| Linked ROM bytes |17,396,620|17,515,740|
| Growth versus matching19-slot build |3,276|3,276|
| EWRAM / IWRAM bytes |226480 /28392|226482 /28336|

Both real builds use `CRIES=off`, GCC14.2.1, Make4.4.1 and padded32MiB ROMs. Commands: `make -j8 -O CRIES=off all` and `make -j8 -O CRIES=off RELEASE=1 all`. Actual candidate six-map static audit:0findings. Focused HOST:22/22 PASS.

NORMAL ROM SHA256: `6ed6830fdda5b189060b92a0256a413872e0172ea448d674da1e2a8d2d865ee1`.
RELEASE ROM SHA256: `a540a7b8c3ebbde22567911a114598a9794d6b34c904deedaeb31eafbbe99a16`.

[Full build identities, actual check names/results and limitations](evidence/west-packet-final-20261027/BUILD_AND_RUNTIME.json). Genuine screenshots: [Terminal follower](evidence/west-packet-final-20261027/NORMAL_TERMINAL_FOLLOWER.png), [RELEASE fresh Continue](evidence/west-packet-final-20261027/RELEASE_FRESH_CONTINUE.png), [native menu](evidence/west-packet-final-20261027/RELEASE_NATIVE_MENU.png).

The controller route covers Jubilife, Global Terminal1F/2F, Route203, Gate1F/B1F, including actual reciprocal stairs/doors and follower restoration. Save completed at GateB1F(5,3), observed the game's success callbacks, advanced valid flash sectors and survived a fresh emulator process in each profile. Initial entry used an explicitly disclosed Continue-warp fixture on private legacy-save copies; this is not natural Sinnoh progression or final owner acceptance. The original flash SHA256 remains `44cd2e2d651128b18439e9f9763705beee6ae32e6c901fc3f24d982328512f9d`, byte-identical after both original-save checks. Original and game-written flashes remain private; separate temporary map registries never share saves.

## Issues and integration status at capture

Fresh exact-head native [run40423377720](https://github.com/kioconnor24-sketch/PokemonGame/actions/runs/40423377720) is still PENDING at capture. Other current checks pass. Do not substitute earlier322/322 results or merge #306 while required CI is pending/failing. This document records verified runtime evidence, not a production merge. Use the current head/checks and subsequent exact-SHA closure comment for actual integration status.

Two initial emulator startup attempts produced no window: restricted local socket setup, then default OpenGL rendering. Successful genuine graphical mGBA uses the normal local-network permission and a private launcher adding only `-C videoRenderer=0`; synchronization remains unchanged. Shared QA/game files were not edited. Failure logs are retained. The generic menu return assertion is supplemented by real native menu-task/action-list observations and rendered-menu captures, rather than treated alone as proof.

The old Saltmere north(7,0)→CoastalMeadow(7,31) static warning remains disclosed in both legacy results. Those3/3 checks establish loading/state preservation, not acceptance of that unrelated seam. Final Delta/human acceptance, expanded identities and story/encounters remain outside this evidence. Disk pressure was handled only by pruning reproducible inactive generated objects; all unique source, earlier baseline artifacts, final binaries and saves remain recoverable privately.

## Next executable work

After every required exact-head #306 check passes, recheck genuine path authorization/review and normally integrate the bounded three-map packet. In parallel, continue existing #305 Gate→campus real traversal: source triage from the actual Gate(7,19) game-written save reaches54/54 valid campus portals, but26 blocked-facing edges and all original32 static findings remain recorded for controller classification. Do not flatten terrain to silence them. #322 traversal vulnerability/bytecode and #307 revised workflow authorization remain separate blocked lanes; preserve Claude branches.
