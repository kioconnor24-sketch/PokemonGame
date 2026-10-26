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
| main `187193c2` | 144 | 144 | 9 | 46 (central/eastern staging); production's group has 30 |
| main + Claude's open PRs (W10, W11, W15–W25, #306) | 208 | 221 | **4** | **179, including all 19 production maps** |

The open PRs that join groups:

| PR | Join |
| --- | --- |
| W21 #311 | Oreburgh City's interiors |
| W22 #312 | Eterna ↔ production Route 205 North (donor seam) |
| W23 #313 | production Route 205 South ↔ Eterna Forest and Old Chateau (donor tunnel) |
| W24 #315 | Hearthome ↔ Route 212; Route 210 South ↔ Route 210 North and Route 215; Route 211 West ↔ Mt. Coronet North Room 1 (west to central) |
| W25 #317 | Cycling Road ↔ Route 207 |

## Groups still apart, and the decisions on them

The owner delegated these decisions (#15 comment 6425492105):

| Group | Maps | Missing link | Decision |
| --- | ---: | --- | --- |
| Canalave / Iron Island / Route 218 | 23 | Production Jubilife's sealed west-arrow (4,20) ↔ Route 218 East's closed east mat (11,5) | **Open it**, as the original does: W27 #320 (DEV overlays; static 0 findings). This takes the world to 3 groups. Production integration needs an exact-path handoff for JubilifeCity. |
| Fuego Ironworks | 2 | The Surf river off Route 205 South | **Surf-only, as the original.** No land path; unreachable on foot by design until Surf access exists. |
| Snowpoint corridor | 4 | Route 216 ↔ Mt. Coronet North Room 2 | Codex (northern lane, active) |

Also not linked, though it doesn't change the grouping: Eterna Forest's east exit to Route 205 North's gatehouse. The donor building art has no Averon equivalent yet.

**Donor interiors for production doors that are not staged anywhere:**
- these sit at the donor's own door coordinates in production: Floaroma Mart, Flower Shop, House 1 and House 2; the Floaroma Meadow house; the Route 205 house;
- these don't, because production Sandgem and Twinleaf were redrawn: Sandgem House 1 and Mart; Twinleaf's two houses.

They need the neutral indoor packer (`hearthome-solaceon/adapt_gate_art.py`) plus a DEV scene that declares the resulting tileset pair.
