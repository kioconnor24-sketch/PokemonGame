---
name: averon-map-validation
description: Validate authored Averon map or generator changes for connectivity, interactions, collision and visible defects.
---

Work from `Pokemon Game/`. Run `scripts/check-averon-maps.py` and, for generator
changes, `scripts/check-averon-authoring.py`. Check both the authoring input and
generated output: terrain stamping order, trees over roads, warp indexes, facing,
elevation, counters, reachable NPCs and backgrounds, map borders and closed gates.
Run dialogue checks when text changes. Keep static reachability separate from
rendered graphics, layering, follower behavior and player-control evidence.

Use the existing renderer and targeted source reads; do not build a replacement
map engine. ChatGPT QA handles bounded mGBA checks when access is real. Report
exact map/coordinates, source SHA and reproduction; preserve approved geography.
