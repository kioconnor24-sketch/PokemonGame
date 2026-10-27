# West packet final integration checkpoint — 2026-10-26

## Recoverable source

Codex branch: `codex/west-packet-current-main-20261026`.
Reconciliation commit: `5f0e91a8c786384cd3a353786a72256fd316b948`.
Parents retain Claude #306 `cdbbd4900c7e8c182f36b8b529feb208b5266473` and accepted main #323 `e595de41d2642524b6acf4aab95010019d50a2ec`. No history rewritten.

Resolved only the three paths claimed in Issue #15 comment 6430024279: the Codex eastern DEV assembler, its regression tests, and the Route 212 source checkpoint. Retained the 22-slot recipe/test and fa12ccb08ace46bedfc527509b44c93429eba4de baseline. Main's separate 19-slot source recipe is preserved. Every engine byte and Claude west-packet, Jubilife-shells, Gate-B1F and Iron Island source byte remains identical to #306. Candidate engine tree: `320fc1f48b1d1da85a83bcf943dbb30103379e0f`.

## Actual checks

- HOST: 9/9 west packet + west DEV repin tests PASS (1.239 s).
- HOST: 13/13 eastern runtime tests PASS (1.403 s).
- `git diff --check` PASS; exact engine/Claude-source equality checks PASS.
- Prior #306 head cdbbd490 CI native 322/322 PASS is historical candidate evidence, not a new-head test claim.

## Remaining gates / issues

This reconciliation is not a production merge or gameplay acceptance. New exact-final-head NORMAL and RELEASE builds, real emulator traversal of the three added production maps (Global Terminal 1F, Global Terminal 2F, Oreburgh Gate B1F), game-written Save and fresh-process Continue remain required. Do not substitute the old ten-map scratch evidence. Preserve original legacy flash and report fixture-based initial arrival honestly.

Environment disconnected briefly but recovered; committed source is intact. Disk is constrained (~288 MiB free). Only reproducible inactive generated caches have been pruned; final ROM/ELF/map, saves, source and evidence remain private/intact. Do not publish ROMs/private saves. #322 remains independently blocked by reproduced output path traversal and tracked bytecode; no Claude branch edits. #307 requires genuine revised workflow authorization/review; no dispatch.

## Next executable task

Push this reconciliation as a normal child PR targeting `claude/west-packet-a`; require applicable current checks. Use an isolated exact-source build scene, retaining old artifacts and verifying tracked source identity before reusing generated assets. Run the paired production-map gates, publish exact source/ROM hashes and actual results, then perform only eligible normal integration. #318 was independently reviewed (3/3 host tests), refreshed, all applicable checks passed and normally merged at `f870930bd9ba9c6b98ee118bf6a9da25b6ee0e78`; it makes no coherent-world/runtime acceptance claim.
