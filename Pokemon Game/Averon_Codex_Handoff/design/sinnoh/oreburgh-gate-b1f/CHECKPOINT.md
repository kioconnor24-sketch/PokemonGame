# W16 Oreburgh Gate B1F: checkpoint

OFF-ENGINE staging on W1 (`claude/iron-island-w1`, for the cave kit). It is built on the **production** Oreburgh Gate 1F; no Codex family is needed.

## Maps

**OreburghGate_1F-dev-overlay**
- The derived 1F blockdata changes **one** cell: a Granite Cave down-ladder at (18,5) in the dead-end north alcove.
- The header appends one warp. The Route 203 exit stays warp 0.
- The production engine files are unchanged.
- Codex's DEV east-exit restoration (oreburgh-donor warp-plan) is independent and is appended at integration.

**OreburghGate_B1F (new, 44×34, General + Cave)**
- One chamber, split into lanes by seven rock outcrops (W1 cave kit).
- An up-ladder at (5,4) leads back to the 1F ladder.

## Tests run

- `test_sinnoh_oreburgh_gate_b1f.py` 6/6. The tests cover:
  - a reproducible build;
  - one changed 1F cell, with the header otherwise identical;
  - the ladder reachable from the Route 203 exit;
  - reciprocal ladder indices;
  - B1F is one closed region with no stranded floor;
  - a crowded-outcrop negative.
- Static map_qa (#252 `64d0e222`) on the production scene: Route 203, Gate 1F and B1F, **0 findings**.
- No ROM, mGBA or Save/Continue claim yet.

## Not included

No boulders, Rock Smash, items, objects, encounters or story. Sections are MAPSEC_PENDING_OWNER. The new layout and map ID are owner-gated at integration.
