---
name: averon-map-validation
description: Use when reviewing generated Averon maps, roads, trees, and rendered map defects.
---

# Validate map render and collision

1. Record ROM/source SHA, map name, player coordinates if known, direction and screenshot.
2. Inspect map generators and tileset/movement permissions in current source. Compare multi-tile tree footprints, road paths, foreground/background tile priority, and collision. A path painted over lower tree tiles can make trees appear cut off; verify rather than guess.
3. Evaluate blockers: inaccessible exits, out-of-bounds warps, movement softlocks, NPC blocking, follower clipping, terrain transition seams and overwritten tiles.
4. Reproduce visually in mGBA when emulator is actually accessible; source audits alone are not rendered acceptance.
5. Report expected/actual, exact reproducible steps, severity, source SHA, evidence and file ownership. Do not redesign unapproved Averon geography.
6. Developer implements fix on owned branch; QA independently retests the new ROM.

## Authority

Current code and live PRs override past notes and generated indices. Follow root/project AGENTS.md, development/AGENT_ROLES.md, WORKFLOW.md and issue #15. Preserve existing developer claims.
