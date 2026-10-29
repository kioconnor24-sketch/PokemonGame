# Claude open issues: 2026-10-29

These are issues Claude still deals with on this project. Anything already in `iron-island/SESSION_ISSUES_20261026.md` (#309) is not repeated. **[model]** marks issues caused by Claude's own reasoning or diligence, not by the environment or by other agents.

## Caused by Claude [model]

1. **Staging ahead of approvals.**
   - **What happened:** source stages and about 25 batches were built faster than sections and handoffs were approved. A 2026-10-28 audit found that all 11 production maps added that week came from Claude's packet installers (#306, #330), while most other staging sat unused.
   - **Now:** Claude checks whether a task can reach production without an unmade decision before starting it.
2. **The same rooms staged repeatedly.** The Solaceon Ruins A/B/C, B1F, B2F East and the Solaceon overlay each exist in two or three variants on main (W8/W15/W19/W20). Only the latest is used; the older copies are dead files that complicate source selection.
3. **A wrong fact in a plan.** `PACKET_E_PLAN.md` (#349) said no Hearthome interiors were staged anywhere, while Claude's own unmerged #269 had them. Corrected in #350. **Lesson:** search your own open PRs too.
4. **Validator gaps that reviewers found** in the packet E/F/G stagers:
   - external exits counted with a set, so duplicates collapsed;
   - five consumed DEV-context directories left unpinned;
   - no checks for wrong-entrance returns or negative warp indices.

   Fixed in #352, #354 and #356.
5. **Background waits that never finish.** A suite runner waited for an `rc=` line the native run never printed, and idled until noticed.
6. **A test run invalidated by Claude.** A worktree was fast-forwarded while a full suite ran in it, so the result was discarded.
7. **Live-test plans that included bike-only terrain.** Listing Route 207 sent the driver down its one-way mud with no listed way back, which failed a run of the packet E join for an unrelated reason. Live map lists must leave out, or account for, one-way mud.
8. **Ad-hoc script bugs.** For example, converting `1F` to a map constant as `1_F` crashed a static audit.

## Environment and tooling

9. **Permission-classifier blocks.**
   - Posting a relayed `HANDOFF_APPROVED` was blocked even after explicit owner approval in chat.
   - Stopping a child process by pattern was blocked.
   - Chained `sleep` waits are blocked.

   Work stalls until the owner acts or an allowed route exists.
10. **One shared GitHub account.** The owner, Codex, the manager and Claude all post as the same user. No formal approve or request-changes reviews are possible, and the guards must tell genuine owner approvals from relayed ones by comment text.
11. **`node` is missing on the host as well as `jq`,** so `test_agent_board_dispatch` (and 2 `jq` tests) always fail locally.
12. **Session limits.**
    - Long sessions are summarized and lose detail.
    - Background jobs are orphaned when a session ends: the C52/C53 live runs (#352/#353) never finished after the 2026-10-28 shutdown and remain incomplete.
13. **Throwaway checkouts keep stale DEV scenes.** A previous install blocks the next checkout until the engine tree is reset.
14. **Superseded CI runs show as failures.** For example, `native-build` on #356 was a cancelled run, not a real failure, but it costs diagnosis time.

## Process and coordination

15. **Contradictory routing on #15.** "Claude paused" kept being carried forward after the owner resumed Claude, and Claude-owned files were routed to Codex. The owner clarified on 2026-10-28 (#15 6483969221) that Claude is active.
16. **Duplicate fixes with Codex.** Codex's #340 duplicated Claude's packet C test fix in the same hour. #355's identity guard covers map files only, not code fixes.
17. **Stacked PRs and moving heads.**
    - #269 waited days behind its parent #260.
    - #337's head moved three times while it waited for approval, so the approval text had to be redone.
    - #352/#353 depend on #351.
18. **Every production packet needs an owner exact-path handoff** for the reserved section and pin files. This is correct, but it is the main bottleneck: nothing reaches production between approvals.
19. **PR-body rules from the identity guard.** Map-touching PRs fail `unique-map-work` without `Sinnoh-Work` / `Sinnoh-Maps` / `Sinnoh-Sources` lines (#358 failed until they were added). The guard has a known regression under repair (#357).
20. **Overlays that disagree for the same map.** W11 and central-joins number Hearthome's doors differently; the Solaceon overlays differ too. Each packet reconciles them by hand, and a mistake silently breaks a return door.

## Open, affecting the game

21. **No bike-aware movement QA.** Routes 207 and 228 (at least) need the Mach or Acro Bike (#15 6484003998), but map_qa and mud_qa probe on foot only, so those routes cannot be verified as playable.
22. **Sections are decided only up to 238.** Packets F and G, the north, the coasts and the League each need new owner values before they can install.
23. **Installed maps are geography only.** By standing rules there are no NPCs, trainers, encounters, items or story. Nobody yet owns turning maps into playable content.
