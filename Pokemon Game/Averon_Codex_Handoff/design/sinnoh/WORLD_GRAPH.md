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

## Groups still apart, and what each needs

| Group | Maps | Missing link | Owner of the decision |
| --- | ---: | --- | --- |
| Canalave / Iron Island / Route 218 | 23 | The donor's Route 218 East gate warps into Jubilife, but production Jubilife has no west entrance (its west edge is solid), and the donor Jubilife geometry is not in the pinned export used here. | owner/manager (a new entrance on a production map) |
| Snowpoint corridor | 4 | Route 216 ↔ Mt. Coronet North Room 2 | Codex (northern lane, active) |
| Fuego Ironworks | 2 | The Surf river off Route 205 South | owner (field-move access) |

Also not linked, though it doesn't change the grouping: Eterna Forest's east exit to Route 205 North's gatehouse. The donor building art has no Averon equivalent yet.
