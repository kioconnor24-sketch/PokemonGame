# Sinnoh world link graph: tracker (C41)

This tracks how far production and staged Sinnoh maps join into one walkable world.

To regenerate:

```bash
python3 'Pokemon Game/scripts/claude_play/world_graph.py' MAIN_CHECKOUT [BRANCH_WORKTREE ...]
```

The tool reads:
- production `gMapGroup_Sinnoh`;
- every staged map (`design/sinnoh/*/staged/<Map>/map.json`, and recipe `source_headers`);
- `-dev-overlay` headers, which add their warps and connections to the map they overlay.

A link is a warp or connection to a known map. This is a **graph of declared links**. It is not walkability: walking is checked per batch by map_qa static and the mGBA gates. It also says nothing about production status: only the 19 production maps are integrated.

## Snapshot 2026-10-26

| Scope | Maps | Links | Groups | Largest group |
| --- | ---: | ---: | ---: | --- |
| main `f870930b` | 144 | 144 | 9 | 46 (central/eastern staging); production's group has 30 |
| main + Claude's open PRs (W4, W10, W11, W14–W28, #306) | 215 | 229 | **3** | **209, including all 19 production maps** |

The open PRs that join groups:

| PR | Join |
| --- | --- |
| W21 #311 | Oreburgh City's interiors |
| W22 #312 | Eterna ↔ production Route 205 North (donor seam) |
| W23 #313 | production Route 205 South ↔ Eterna Forest and Old Chateau (donor tunnel) |
| W24 #315 | Hearthome ↔ Route 212; Route 210 South ↔ Route 210 North and Route 215; Route 211 West ↔ Mt. Coronet North Room 1 (west to central) |
| W25 #317 | Cycling Road ↔ Route 207 |
| W26 #319 | Valor Lakefront ↔ Lake Valor (inside the eastern group) |
| W27 #320 | production Jubilife ↔ Route 218 East: joins the Canalave / Iron Island / Route 218 group |
| W28 #321 | production Floaroma Town and Floaroma Meadow ↔ five donor interiors |

## Groups still apart, and the decisions on them

The owner delegated these decisions (#15 comment 6425492105):

| Group | Maps | Missing link | Decision |
| --- | ---: | --- | --- |
| Fuego Ironworks | 2 | The Surf river off Route 205 South | **Surf-only, as the original.** No land path; unreachable on foot by design until Surf access exists. |
| Snowpoint corridor | 4 | Route 216 ↔ Mt. Coronet North Room 2 | Codex (northern lane, active) |

Also not linked, though it doesn't change the grouping: Eterna Forest's east exit to Route 205 North's gatehouse. The donor building art has no Averon equivalent yet.

The Canalave / Iron Island / Route 218 group (23 maps) is joined by W27 #320. The owner-delegated decision is to open the original geometry (6425492105). Production integration needs an exact-path handoff for JubilifeCity.

**Donor interiors for production doors:**
- staged: Floaroma Mart, Flower Shop, House 1 and House 2, and the Floaroma Meadow house (W28 #321, neutral indoor packer, own DEV tileset pair); the Route 205 South house (W23 #313, stock `LAYOUT_HOUSE1`);
- not staged here, because production Sandgem and Twinleaf were redrawn (the donor doors don't line up): Sandgem House 1 and Mart; Twinleaf's two houses. Codex #238 holds source rooms for these towns.

## One-way on foot (not graph defects)

A link in the graph can still be walkable in one direction only. The mGBA gates found two Muddy Slopes in donor geometry (Codex-owned; recorded, not changed). They have collision 0, but on foot the player slides back down them:
- **Route 210 South** (26, 80–81) and (21, 71–72): Solaceon → Route 210 North needs a bike. Southbound on foot works.
- **Route 207** (18, 14–15): Oreburgh → Route 206 (Cycling Road) needs a bike. Southbound on foot works.

Fuego Ironworks is Surf-only by decision (above). Gate runs that cross these slopes use a runner that keeps the same checks and tests down seams last (#315).
