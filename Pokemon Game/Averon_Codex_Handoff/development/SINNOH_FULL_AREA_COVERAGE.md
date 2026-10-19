# Sinnoh — complete geography coverage and missing-subarea audit

**Planning inventory for the [master roadmap](SINNOH_MASTER_PRODUCTION_ROADMAP.md) and [work packages](SINNOH_DEVELOPER_WORK_PACKAGES.md).** Generated against the existing [Sinnoh area register](SINNOH_AREA_REGISTER.csv) on 2026-10-19. The source register lists **87** tracker locations: **18 settlements/postgame hubs, 30 routes (201–230), 33 landmarks, and 6 special/optional sites**. Tracker keys are organizational strings only and **are not game map IDs, saved met codes, section numbers, event flags or approval statuses**. No future location has been fabricated as an implemented production map.

**Completeness check:** every existing register key appears exactly once below (programmatically compared to current source at authoring). A single registered landmark may need many child production maps. The assignment to geographic waves is a practical construction recommendation, **not fixed story/level chronology**. Routes/caves crossing waves should have a primary owner plus reciprocal links to neighboring waves.

**Authority:** physical geography may be selected and produced independently under the owner's [new delegated creative direction](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6261800483), but owner revision is expected later and the usual protected-file/save-ID/merge gates remain; no story, encounter tables, levels or trainer battles are approved by this index. Historical CSV \`LayoutApproval=PENDING\` data should not be relabeled APPROVED merely because design autonomy was delegated. Route202's documented trustworthy-reference condition remains.

## A. Area-register-to-production-wave coverage

### W0 — Existing approved Sandgem wedge (2 tracker entries)

| Tracker key | Registered location | Scope/physical construction note |
| --- | --- | --- |
| `SN-T02` | Sandgem Town | Exterior/Center previously integrated; natural healer44 tracked in #151; check LIVE merge |
| `SN-R201` | Route 201 | Owner-approved 64×22, section217, Sandgem ±4 in PR #150; check LIVE merge state |

**Exit:** registered area keys have actual referenced layout(s), build inclusion and authentic MAP-QA when constructed. A draft/candidate/blocked advanced feature is tracked honestly, never upgraded to EMULATOR_PASS without evidence.

### W1 — Southwest origin and Jubilife (5 tracker entries)

| Tracker key | Registered location | Scope/physical construction note |
| --- | --- | --- |
| `SN-T01` | Twinleaf Town | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-T03` | Jubilife City | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-R202` | Route 202 | Reference-blocked pending reliable original layout; do not invent geometry |
| `SN-L01` | Lake Verity | Physical landmark; split floors, shores and portals as needed |
| `SN-L04` | Verity Lakefront | Physical landmark; split floors, shores and portals as needed |

**Exit:** registered area keys have actual referenced layout(s), build inclusion and authentic MAP-QA when constructed. A draft/candidate/blocked advanced feature is tracked honestly, never upgraded to EMULATOR_PASS without evidence.

### W2 — Oreburgh, Floaroma, Eterna and west bypass (19 tracker entries)

| Tracker key | Registered location | Scope/physical construction note |
| --- | --- | --- |
| `SN-T04` | Oreburgh City | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-T05` | Floaroma Town | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-T06` | Eterna City | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-R203` | Route 203 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R204` | Route 204 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R205` | Route 205 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R206` | Route 206 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R207` | Route 207 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-L09` | Oreburgh Gate | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |
| `SN-L10` | Oreburgh Mine | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |
| `SN-L11` | Ravaged Path | Physical landmark; split floors, shores and portals as needed |
| `SN-L12` | Floaroma Meadow | Physical landmark; split floors, shores and portals as needed |
| `SN-L13` | Valley Windworks | Physical landmark; split floors, shores and portals as needed |
| `SN-L14` | Eterna Forest | Physical landmark; split floors, shores and portals as needed |
| `SN-L15` | Old Chateau | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |
| `SN-L16` | Fuego Ironworks | Physical landmark; split floors, shores and portals as needed |
| `SN-L17` | Wayward Cave | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |
| `SN-L18` | Cycling Road | Physical landmark; split floors, shores and portals as needed |
| `SN-O03` | Eterna Galactic Building | Physical-site candidate or advanced feasibility; narrative role intentionally undecided |

**Exit:** registered area keys have actual referenced layout(s), build inclusion and authentic MAP-QA when constructed. A draft/candidate/blocked advanced feature is tracked honestly, never upgraded to EMULATOR_PASS without evidence.

### W3 — Hearthome, Solaceon, Celestic, Canalave and central Mt. Coronet (15 tracker entries)

| Tracker key | Registered location | Scope/physical construction note |
| --- | --- | --- |
| `SN-T07` | Hearthome City | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-T08` | Solaceon Town | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-T11` | Celestic Town | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-T12` | Canalave City | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-R208` | Route 208 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R209` | Route 209 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R210` | Route 210 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R211` | Route 211 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R212` | Route 212 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R218` | Route 218 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-L07` | Mt. Coronet | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |
| `SN-L19` | Amity Square | Physical landmark; split floors, shores and portals as needed |
| `SN-L20` | Lost Tower | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |
| `SN-L21` | Solaceon Ruins | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |
| `SN-L27` | Iron Island | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |

**Exit:** registered area keys have actual referenced layout(s), build inclusion and authentic MAP-QA when constructed. A draft/candidate/blocked advanced feature is tracked honestly, never upgraded to EMULATOR_PASS without evidence.

### W4 — Veilstone, Pastoria, eastern lakes and wetlands (13 tracker entries)

| Tracker key | Registered location | Scope/physical construction note |
| --- | --- | --- |
| `SN-T09` | Veilstone City | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-T10` | Pastoria City | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-R213` | Route 213 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R214` | Route 214 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R215` | Route 215 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-L02` | Lake Valor | Physical landmark; split floors, shores and portals as needed |
| `SN-L05` | Valor Lakefront | Physical landmark; split floors, shores and portals as needed |
| `SN-L22` | Great Marsh | Physical landmark; split floors, shores and portals as needed |
| `SN-L23` | Trophy Garden | Physical landmark; split floors, shores and portals as needed |
| `SN-L24` | Sendoff Spring | Physical landmark; split floors, shores and portals as needed |
| `SN-L25` | Spring Path | Physical landmark; split floors, shores and portals as needed |
| `SN-L26` | Turnback Cave | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |
| `SN-O04` | Veilstone Galactic Headquarters | Physical-site candidate or advanced feasibility; narrative role intentionally undecided |

**Exit:** registered area keys have actual referenced layout(s), build inclusion and authentic MAP-QA when constructed. A draft/candidate/blocked advanced feature is tracked honestly, never upgraded to EMULATOR_PASS without evidence.

### W5 — Northern snowfield, Sunyshore and League (13 tracker entries)

| Tracker key | Registered location | Scope/physical construction note |
| --- | --- | --- |
| `SN-T13` | Snowpoint City | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-T14` | Sunyshore City | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-T15` | Pokémon League | Recognizable town/city/League exterior; practical interior-and-service child maps |
| `SN-R216` | Route 216 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R217` | Route 217 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R222` | Route 222 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R223` | Route 223 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R224` | Route 224 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-L03` | Lake Acuity | Physical landmark; split floors, shores and portals as needed |
| `SN-L06` | Acuity Lakefront | Physical landmark; split floors, shores and portals as needed |
| `SN-L08` | Spear Pillar | Physical landmark; split floors, shores and portals as needed |
| `SN-L28` | Snowpoint Temple | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |
| `SN-L29` | Victory Road | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |

**Exit:** registered area keys have actual referenced layout(s), build inclusion and authentic MAP-QA when constructed. A draft/candidate/blocked advanced feature is tracked honestly, never upgraded to EMULATOR_PASS without evidence.

### W6 — Southern sea and remote islands (6 tracker entries)

| Tracker key | Registered location | Scope/physical construction note |
| --- | --- | --- |
| `SN-R219` | Route 219 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R220` | Route 220 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R221` | Route 221 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-L31` | Fullmoon Island | Physical landmark; split floors, shores and portals as needed |
| `SN-L32` | Newmoon Island | Physical landmark; split floors, shores and portals as needed |
| `SN-L33` | Pal Park | Physical landmark; split floors, shores and portals as needed |

**Exit:** registered area keys have actual referenced layout(s), build inclusion and authentic MAP-QA when constructed. A draft/candidate/blocked advanced feature is tracked honestly, never upgraded to EMULATOR_PASS without evidence.

### W7 — Battle Zone postgame mainland (11 tracker entries)

| Tracker key | Registered location | Scope/physical construction note |
| --- | --- | --- |
| `SN-T16` | Fight Area | Battle Zone settlement, facilities and safe port/junctions |
| `SN-T17` | Survival Area | Battle Zone settlement, facilities and safe port/junctions |
| `SN-T18` | Resort Area | Battle Zone settlement, facilities and safe port/junctions |
| `SN-R225` | Route 225 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R226` | Route 226 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R227` | Route 227 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R228` | Route 228 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R229` | Route 229 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-R230` | Route 230 | Overworld path, terrain, route junctions and safe edge/bridge access |
| `SN-L30` | Stark Mountain | Multi-floor/submap coverage; exact stairs/warps and safe returns, no copied story |
| `SN-O05` | Battle Park / Battle Frontier | Physical Frontier campus; five competitive facility rulesets not authorized/implemented by geography |

**Exit:** registered area keys have actual referenced layout(s), build inclusion and authentic MAP-QA when constructed. A draft/candidate/blocked advanced feature is tracked honestly, never upgraded to EMULATOR_PASS without evidence.

### W8 — Special optional or mechanically advanced world sites (3 tracker entries)

| Tracker key | Registered location | Scope/physical construction note |
| --- | --- | --- |
| `SN-O01` | Flower Paradise | Physical-site candidate or advanced feasibility; narrative role intentionally undecided |
| `SN-O02` | Hall of Origin | Physical-site candidate or advanced feasibility; narrative role intentionally undecided |
| `SN-O06` | Distortion World | Physical-site candidate or advanced feasibility; narrative role intentionally undecided |

**Exit:** registered area keys have actual referenced layout(s), build inclusion and authentic MAP-QA when constructed. A draft/candidate/blocked advanced feature is tracked honestly, never upgraded to EMULATOR_PASS without evidence.


## B. Required child-map / missing-in-87 inventory

The 87-row tracker is an **area index, not a complete engine-map inventory**. The following candidates are **not asserted to be separately registered yet**. Underlying games sometimes treat these as separate floors/buildings, facilities or version-specific areas. Assign a child key and clear parent only when the exact footprint is researched; don't allocate a saved section code to every house. These physical venues are part of the broad whole-region coverage or explicit owner-adaptation review, **not automatic authorization to implement their original activities**.

| Geographic cluster | Candidate missing subareas or specialized map layers | Construction acceptance / deferral |
| --- | --- | --- |
| Twinleaf / Sandgem | recognizable homes, lab/service shells and future entry-space; utility interiors | Doors/warps/collision; no copied starter script, rival scene or origin story |
| Jubilife | Trainers' School, Pokétch Company, TV building, Global Terminal, major service interiors | Neutral buildings and signage; wireless/network-specific Gen4 functionality deferred |
| Oreburgh | Mining Museum, mine floors, Gate floors/crossing, Gym exterior/interior structure | Multiple working stairs/exits; no Gym team, fossils/economy or mandatory story quests yet |
| Floaroma / Eterna | Meadow branches, Windworks building, Eterna Condominiums, former Galactic Building, Old Chateau rooms, Fuego internal floors | Repurpose former Galactic *building* physically; no plot/faction ownership; distinct forest/industrial building visuals |
| Cycling / caves | Cycle Road bridge/underpass, Wayward Cave hidden approach and floors, Mt. Coronet's distinct lower entrances, exits and chasms | Real map grid adjacency, bridges, travel ability placeholders, floor-specific Save/Continue |
| Hearthome | Contest Hall, Amity Square interiors, future Gym building shell, side plazas | No Contest gameplay/leader team/Amity species eligibility inferred |
| Solaceon / Celestic | Lost Tower floors, Solaceon Ruins branching rooms, Celestic ruins, Hallowed Tower on Route209 | Neutral ruins/graveyard physical designs; separate future ghost/legendary/quest events |
| Veilstone | Department Store levels, former Galactic Headquarters, Galactic Warehouse, city facilities | Interior stack with reversible stairs; replace former faction purposes with TBD roles |
| Pastoria / south | Great Marsh internal zones, Route212 marsh, Pokémon Mansion main interior, Trophy Garden, Hotel Grand Lake, Seven Stars restaurant near Valor shore, Maniac Tunnel (Ruin Maniac Cave) | Physical area diversity and safe movement; no Safari rates, prizes or NPC progression |
| Canalave / west sea | Library floors, ferry dock candidate, Iron Island cave floors, connecting shore maps | No fixed interregional transport origin or Riley quest copied |
| Snowpoint / high mountain | Route216/217 subsegments, Acuity Lakefront and lake, Snowpoint Temple basement levels, Mt. Coronet snow/upper floors and Spear Pillar | Ice/snow mechanical behavior based on implemented physics; no legendary encounters |
| Sunyshore / League | Lighthouse, market, harbor, Route223 sea subdivisions, Victory Road floors, League lobby/rooms, Route224 exit | No final Gym/Champion battles or Shiny Stone/item assumptions |
| South sea | Route219/220/221 passages, Pal Park complex or later Ramanas-style adaptive candidate | Version-specific venue reuse is an owner-design candidate, not a mandate to copy BDSP |
| Offshore/rare sites | Fullmoon Island, Newmoon Island, Seabreak Path, Flower Paradise, Hall of Origin | Neutral physical maps and safe exits; no mythical quests, events or provenance claims |
| Battle Zone | Fight Area port, Survival battleground building, Resort Villa/other facilities, Stark Mountain multiple floors; Battle Tower, Arcade, Castle, Factory, Hall **as separate optional mechanics facilities** | Campus structure and landmarks first; full Platinum rule systems require separate feasibility/owner decisions |
| Underground | Original Underground and/or BDSP Grand Underground zones, tunnel layer, caves/hideaways, surface entrance/exit pairs | Scope a feasible single-player GBA interpretation with native/GBA tests before approving a faithful online/mining implementation |
| Distortion World | multiple puzzle/floor regions and transition architecture | Experimental GBA-capability spike required; do not claim original DS 3D gravity, inverted cameras or full puzzles already implemented |
| Special Platinum / version differences | optional Regi ruins (Rock Peak, Iron and Iceberg), Hallowed Tower, Hotel Grand Lake, Contest Hall, original Galactic building sites, Pal Park vs Ramanas-style concept | Identify canonical physical reference, map location and adaptation purpose; story/legendary mechanics deferred |

### Submap authoring rules

1. Every child map records **parent tracker key**, source-reference location, any split into floors/sheets, planned entrance/exit warp graph, collision semantics, necessary field-traversal dependencies, art/rights lineage, and an honest readiness state.
2. Never assume all optional DS mechanics have a direct GBA equivalent; deliver a real playable physical shell or explicitly blocked feasibility state.
3. Distinguish **"world map done"**, **"individual map source linked"**, **"graphically traversable"**, and **"gameplay and story functional"**. A neutral Gym shell is *not* a Gym win.
4. Establish a parent->child table in existing tracker/companion repo design files (not new GitHub issues for each room). Owner-directed visual/geographic revisions are grouped into meaningful post-build batches.
5. In a full Sinnoh pass, verify every named route 201–230 is accounted for, every key settlement/hub, three lakes with lakefronts, all three main Mt. Coronet traversal axes, all coasts/islands, snowy north, central ruins, postgame volcano, and special-world feasibility. Don't create arbitrary "87/87 complete" metrics by counting this markdown row list alone.

## C. Completion audits by type

- **Settlement:** exterior town/city, primary services that have a physical shell, regional recognizability, entrances, street-to-route junctions, safe returns; gyms/plot/encounters deferred until designed.
- **Route:** landmark/elevation/biome, deliberate walkable lanes plus optional detours, ledge/water/field barriers, both ends of each built connection, physical ecological niches for future Gen1–9 Pokémon, collision/Save→Continue.
- **Landmark:** exact floor/zone graph, entry/exit/return, ability gating as neutral capabilities not story flags, distinct visual identity, authentic emulator movement and persistence.
- **Optional site:** decide whether physical site can be built now or requires a demonstrated architecture spike; no silent omission, no premature legendary or Frontier behavior.
- **Complete region:** connected geography, documented physically closed future boundaries, islands/postgame geography, technically honest optional-world statuses, one eventual regional travel system, owner geographic review and correction pass. Full gameplay/release is a separate later milestone.

## D. Source references

- Existing [87-row area register](SINNOH_AREA_REGISTER.csv) (primary coverage identity).
- [Bulbapedia Sinnoh geographic overview](https://bulbapedia.bulbagarden.net/wiki/Sinnoh), [Platinum location catalog](https://bulbapedia.bulbagarden.net/wiki/Category:Platinum_locations), [Battle Zone](https://bulbapedia.bulbagarden.net/wiki/Battle_Zone). These are **reference candidates** for cross-checking topology, not permission to copy map art, scripts, audio or screenshots into the ROM.
- Any new pixel-accurate per-map geometry still requires its own verified source/notes; never infer exact tile coordinates from this coverage file.