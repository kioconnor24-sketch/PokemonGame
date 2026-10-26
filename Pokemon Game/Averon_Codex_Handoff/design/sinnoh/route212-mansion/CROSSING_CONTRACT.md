# Route 212 South on-foot crossing: contract for Codex's eastern-loop repair (C27/C32)

Claude does not edit `eastern-loop`. This page states what W17 (Route 212 North mansion) and the natural trip Pastoria → Route 212 South → Route 212 North need from that exterior. Evidence: #15 comment 6406549902.

## Defect

- Row 11 of `Route212_South` is `MB_HORIZONTAL_RAIL` at x 27–59 (elevation 15 at x 27–40, 4 beyond).
- `CheckForPlayerAvatarCollision` runs `CheckAcroBikeCollision` for every player step, so a rail tile is a collision on foot.
- The elevation-3 ground of row 12 (x 36–40) therefore cannot step north onto row 11 and down to the elevation-3 ground of row 10.
- Result: the Pastoria seam (129, 11–12) cannot reach the north seam (10–15, 0). Route 212 North is cut off.

## Minimal sufficient change (computed on the eastern-loop scene)

Making **any one** of these cells non-rail walkable restores the crossing: **(36,11), (37,11), (38,11), (39,11), (40,11)**. No other single rail cell does.

To satisfy the contract:
- one cell, or for a natural look a 2–5-cell span of those five;
- a walkable, non-rail behaviour, such as the family's plain bridge-deck or ground word, at elevation 15 (bridge) or 3;
- collision 0.

The other rail cells (rows 9, 10, 14, 15, 20, 22, 26 and the rest of row 11) can stay.

## Acceptance (Claude reruns these after the fix lands)

1. With the rail rule (#300), static map_qa on eastern-loop reports no `MAP_ROUTE212_SOUTH exit-unreachable`, and Codex's `test_sinnoh_eastern_hotel_link` world audit stays clean.
2. W17 DEV gate on eastern-loop + W17, NORMAL and RELEASE, from the Pastoria save fixture: Route 212 South → North → mansion 1F/2F and back, then Save → fresh Continue.

W17's own files need no change for this. Its overlay touches only `Route212_North` (24,38).
