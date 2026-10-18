# Route 201: next-area design candidate (owner review)

**Status: CANDIDATE.** This is not approved, no map file is built, and it creates no map or section ID, encounter table, trainer or script. It is the next connected area after Sandgem Town (PR #133), proposed because it keeps the original geography.

![Route 201 candidate](route201-candidate.png)

![Route 201 collision](route201-collision.png)

The render comes from [`route201-candidate.json`](route201-candidate.json), which [`make_route201_plan.py`](make_route201_plan.py) generates. It uses the same approved temporary in-repo pieces as Sandgem: grass, the Route 101 dirt road, round trees, tall grass and ledges from the General primary. Marks: yellow = exits, orange = reserved space, magenta = NPC slots.

## Original geography kept (PRESERVE)

The geography follows the original DPPt overhead at the same 16 px tile scale, which comes out to **64 × 22 metatiles**:
- **East exit:** the path climbs to the east edge at rows 7–8, leading to **Sandgem's west exit**. Sandgem's exit is at rows 11–12, so the map connection uses a vertical offset of 4. No geometry has to change.
- **South exit:** a sand path drops to the south edge at columns 16–17, leading to **Twinleaf Town**. Twinleaf is not approved, so this edge stays closed.
- **West exit:** the open corridor at rows 8–11 heads toward **Lake Verity**. Lake Verity is not approved, so this edge stays closed too.
- **Ledges:** a long south-facing ledge (`MB_JUMP_SOUTH`) crosses the west half, with a walk-around gap at columns 9–10 so the corridor isn't one-way. There is a short ledge near the east end.
- **Tall grass:** three patches, including the big one beside the eastern path. They are **physical only**: there is no encounter table until wild Pokémon are approved.

## Decisions requested

1. Is Route 201 the next area, or should Route 202 come first? There's no Route 202 overhead reference yet, so it would need one.
2. Is this geometry acceptable? Should the ledge gap at columns 9–10 stay?
3. Section ID: Route 201 needs its own met-location section, which is Codex's next allocation from 217 upward.
4. Twinleaf and Lake Verity edges stay closed until those areas are approved. (Yes / no.)

Building it after approval would cost about 2.8 KB of layout (64 × 22 × 2 B) plus headers. It reuses already-linked art, the placeholder tooling and the acceptance scripts from Sandgem.
