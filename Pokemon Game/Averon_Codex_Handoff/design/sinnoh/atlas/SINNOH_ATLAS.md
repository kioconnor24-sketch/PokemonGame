# Sinnoh topology atlas (roadmap C02): source layer + Averon adaptation layer

**Status: planning reference.** Nothing here builds a map or allocates a map, section or heal ID. Under the owner's delegation ([#15 comment 6261800483](https://github.com/kioconnor24-sketch/PokemonGame/issues/15#issuecomment-6261800483)), ordinary physical geography is chosen by the developers and reviewed after development. Permanent IDs, met-origin capacity, story, encounters and Route 202's reference prerequisite stay reserved for the owner.

## 1. Source layer: every adjacency is cited

[`build_sinnoh_atlas.py`](build_sinnoh_atlas.py) reads all 87 rows of [`SINNOH_AREA_REGISTER.csv`](../../../development/SINNOH_AREA_REGISTER.csv) and, for each:
1. fetches the matching Bulbapedia page's lead section through the MediaWiki API;
2. parses the route, town or location **infobox**;
3. records compass neighbours (`north=`, `east=` …), landmark relations (`location=`, e.g. "West end of Route 201"), size and map images, together with the **page revision ID**.

The output is [`sinnoh-atlas.json`](sinnoh-atlas.json). Raw API responses are cached outside the repo and never committed. Re-running with `--offline` against the same cache reproduces the file exactly.

| Result | Count |
|---|---|
| Register areas resolved to a page | **87 / 87** |
| With compass neighbours | 54 |
| With a landmark relation (no compass fields on that page type) | 33 |
| Compass links | 125 |

## 2. Audit

[`audit_sinnoh_atlas.py`](audit_sinnoh_atlas.py) `--self-test` checks that every compass link is reciprocal. If A is north of B, then B must be south of A, whenever both pages carry compass data. Its mutation, a Twinleaf link put on the wrong side, is caught.

- **1 genuine source note.** Floaroma Town lists Route 205 to its east, but Route 205's infobox lists Fuego Ironworks to its west. Route 205 is two halves in DPPt: the southern half runs from Floaroma to the Valley Windworks side, and the northern half to Eterna Forest. Build it as **two maps** (205 South / 205 North) so each seam is reciprocal.
- **Names outside the register** (add rows or treat as sub-areas): Mount Coronet's interior network, Maniac Tunnel (Underground/Route 214 area) and Seabreak Path (Flower Paradise approach).
- **Single-link areas** (legitimate dead ends): Twinleaf Town (north only), Canalave City (Route 218 on land, plus sea links to Iron Island and Fullmoon Island), the Pokémon League (Route 223 / Victory Road) and the Resort Area (Route 229). Each needs a return path and must not become a softlock.
- **Cycling Road** is Route 206's page; it is treated as Route 206.

## 3. Averon adaptation layer (current state)

| Corridor | Sourced links | Averon state |
|---|---|---|
| Twinleaf – Route 201 – Sandgem | Twinleaf N→201; 201 E→Sandgem, W→Verity Lakefront | Sandgem built (#133). Route 201 built (#150, Fast Lane B pending). Twinleaf candidate #156 (junction offset 0). Verity Lakefront not started. |
| Sandgem – Route 202 – Jubilife | Sandgem N→202; Jubilife S→202 | **Deferred**: no trustworthy full Route 202 overhead (#139). Sandgem's north edge stays closed. |
| Sandgem – Route 219 (south, water) | Sandgem S→219 | Not started; Sandgem's south edge is closed. Needs Surf; no story. |
| Jubilife hub | N→204, E→203, S→202, W→218 | Not started; the next hub after Route 202. |

**Proposed build order** (southwest first; C04):
1. Twinleaf (#156);
2. Verity Lakefront and Lake Verity (relation: "West end of Route 201");
3. Jubilife, its interiors and Route 218 once Route 202 is sourced;
4. otherwise Route 203, Oreburgh Gate and Oreburgh, built behind a closed Route 202 edge.

Each batch uses MAP-QA: real mGBA seams, closed edges, Save → fresh Continue.

**Seam rules carried forward** (from Route 201 and Twinleaf):
- Connections are added in reciprocal pairs only.
- Offsets are even wherever 2 × 2 placeholder trees meet a seam.
- Every open edge must meet a built neighbour; otherwise it stays closed until that neighbour exists.

## 4. Full sourced adjacency

| Key | Area | Kind | Sourced neighbours (Bulbapedia infobox) | Averon state | Source rev |
|---|---|---|---|---|---|
| SN-T01 | Twinleaf Town | settlement | north: Route 201 | candidate (#156) | [4615815](https://bulbapedia.bulbagarden.net/wiki/Twinleaf_Town) |
| SN-T02 | Sandgem Town | settlement | north: Route 202; south: Route 219; west: Route 201 | BUILT (#133) | [4594572](https://bulbapedia.bulbagarden.net/wiki/Sandgem_Town) |
| SN-T03 | Jubilife City | settlement | north: Route 204; east: Route 203; south: Route 202; west: Route 218 | not started | [4609301](https://bulbapedia.bulbagarden.net/wiki/Jubilife_City) |
| SN-T04 | Oreburgh City | settlement | north: Route 207; south: Oreburgh Mine; west: Oreburgh Gate | not started | [4521456](https://bulbapedia.bulbagarden.net/wiki/Oreburgh_City) |
| SN-T05 | Floaroma Town | settlement | north: Fuego Ironworks; east: Route 205; south: Route 204 | not started | [4541353](https://bulbapedia.bulbagarden.net/wiki/Floaroma_Town) |
| SN-T06 | Eterna City | settlement | east: Route 211; south: Route 206; west: Route 205 | not started | [4538432](https://bulbapedia.bulbagarden.net/wiki/Eterna_City) |
| SN-T07 | Hearthome City | settlement | north: Amity Square; east: Route 209; south: Route 212; west: Route 208 | not started | [4536010](https://bulbapedia.bulbagarden.net/wiki/Hearthome_City) |
| SN-T08 | Solaceon Town | settlement | north: Route 210; east: Solaceon Ruins; south: Route 209 | not started | [4650214](https://bulbapedia.bulbagarden.net/wiki/Solaceon_Town) |
| SN-T09 | Veilstone City | settlement | south: Route 214; west: Route 215 | not started | [4559221](https://bulbapedia.bulbagarden.net/wiki/Veilstone_City) |
| SN-T10 | Pastoria City | settlement | north: Great Marsh; east: Route 213; west: Route 212 | not started | [4633710](https://bulbapedia.bulbagarden.net/wiki/Pastoria_City) |
| SN-T11 | Celestic Town | settlement | east: Route 210; west: Route 211 | not started | [4509692](https://bulbapedia.bulbagarden.net/wiki/Celestic_Town) |
| SN-T12 | Canalave City | settlement | east: Route 218 | not started | [4638842](https://bulbapedia.bulbagarden.net/wiki/Canalave_City) |
| SN-T13 | Snowpoint City | settlement | north: Snowpoint Temple; west: Acuity Lakefront | not started | [4521465](https://bulbapedia.bulbagarden.net/wiki/Snowpoint_City) |
| SN-T14 | Sunyshore City | settlement | north: Route 223; west: Route 222 | not started | [4535233](https://bulbapedia.bulbagarden.net/wiki/Sunyshore_City) |
| SN-T15 | Pokémon League | settlement | south: Route 223 | not started | [4623652](https://bulbapedia.bulbagarden.net/wiki/Pokémon_League_(Sinnoh)) |
| SN-T16 | Fight Area | postgame_hub | north: Route 225; east: Route 230 | not started | [4613662](https://bulbapedia.bulbagarden.net/wiki/Fight_Area) |
| SN-T17 | Survival Area | postgame_hub | east: Route 226; west: Route 225 | not started | [4613661](https://bulbapedia.bulbagarden.net/wiki/Survival_Area) |
| SN-T18 | Resort Area | postgame_hub | north: Route 229 | not started | [4603687](https://bulbapedia.bulbagarden.net/wiki/Resort_Area) |
| SN-R201 | Route 201 | route | east: Sandgem Town; south: Twinleaf Town; west: Verity Lakefront | BUILT, merge pending (#150) | [4633683](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_201) |
| SN-R202 | Route 202 | route | north: Jubilife City; south: Sandgem Town | DEFERRED (reference gap) | [4613216](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_202) |
| SN-R203 | Route 203 | route | east: Oreburgh Gate; west: Jubilife City | not started | [4613217](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_203) |
| SN-R204 | Route 204 | route | north: Floaroma Town; south: Jubilife City | not started | [4613218](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_204) |
| SN-R205 | Route 205 | route | north: Eterna Forest; east: Eterna City; west: Fuego Ironworks | not started | [4590442](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_205) |
| SN-R206 | Route 206 | route | north: Eterna City; south: Route 207 | not started | [4590443](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_206) |
| SN-R207 | Route 207 | route | north: Route 206; east: Mount Coronet; south: Oreburgh City | not started | [4596196](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_207) |
| SN-R208 | Route 208 | route | east: Hearthome City; west: Mount Coronet | not started | [4596197](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_208) |
| SN-R209 | Route 209 | route | north: Solaceon Town; west: Hearthome City | not started | [4612392](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_209) |
| SN-R210 | Route 210 | route | east: Route 215; south: Solaceon Town; west: Celestic Town | not started | [4613680](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_210) |
| SN-R211 | Route 211 | route | north: Mount Coronet; east: Celestic Town; south: Mount Coronet; west: Eterna City | not started | [4595959](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_211) |
| SN-R212 | Route 212 | route | north: Hearthome City; east: Pastoria City | not started | [4375363](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_212) |
| SN-R213 | Route 213 | route | north: Valor Lakefront; west: Pastoria City | not started | [4637914](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_213) |
| SN-R214 | Route 214 | route | north: Veilstone City; east: Spring Path; south: Valor Lakefront; west: Maniac Tunnel | not started | [4613196](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_214) |
| SN-R215 | Route 215 | route | east: Veilstone City; west: Route 210 | not started | [4613219](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_215) |
| SN-R216 | Route 216 | route | north: Route 217; east: Mount Coronet | not started | [4624697](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_216) |
| SN-R217 | Route 217 | route | north: Acuity Lakefront; south: Route 216 | not started | [4626966](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_217) |
| SN-R218 | Route 218 | route | east: Jubilife City; west: Canalave City | not started | [4613754](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_218) |
| SN-R219 | Route 219 | route | north: Sandgem Town; south: Route 220 | not started | [4630033](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_219) |
| SN-R220 | Route 220 | route | north: Route 219; east: Route 221 | not started | [4646776](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_220) |
| SN-R221 | Route 221 | route | north: Pal Park; west: Route 220 | not started | [4339852](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_221) |
| SN-R222 | Route 222 | route | east: Sunyshore City; west: Valor Lakefront | not started | [4520775](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_222) |
| SN-R223 | Route 223 | route | north: Pokémon League; south: Sunyshore City | not started | [4228073](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_223) |
| SN-R224 | Route 224 | route | north: Seabreak Path; west: Victory Road | not started | [4646777](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_224) |
| SN-R225 | Route 225 | route | east: Survival Area; south: Fight Area | not started | [4349736](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_225) |
| SN-R226 | Route 226 | route | north: Route 227; east: Route 228; west: Survival Area | not started | [4387983](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_226) |
| SN-R227 | Route 227 | route | north: Stark Mountain; south: Route 226 | not started | [4392888](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_227) |
| SN-R228 | Route 228 | route | south: Route 229; west: Route 226 | not started | [4392969](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_228) |
| SN-R229 | Route 229 | route | north: Route 228; south: Resort Area; west: Route 230 | not started | [4646778](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_229) |
| SN-R230 | Route 230 | route | east: Route 229; west: Fight Area | not started | [4515254](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_230) |
| SN-L01 | Lake Verity | landmark | located: West end of Route 201  / Western Obsidian Fieldlands | not started | [4556699](https://bulbapedia.bulbagarden.net/wiki/Lake_Verity) |
| SN-L02 | Lake Valor | landmark | located: South end of Route 214 / Northeastern Crimson Mirelands | not started | [4649593](https://bulbapedia.bulbagarden.net/wiki/Lake_Valor) |
| SN-L03 | Lake Acuity | landmark | located: North end of Route 217  / North Alabaster Icelands | not started | [4598639](https://bulbapedia.bulbagarden.net/wiki/Lake_Acuity) |
| SN-L04 | Verity Lakefront | landmark | north: Lake Verity; east: Route 201 | not started | [4613226](https://bulbapedia.bulbagarden.net/wiki/Verity_Lakefront) |
| SN-L05 | Valor Lakefront | landmark | north: Route 214; east: Route 222; south: Route 213; west: Lake Valor | not started | [4613197](https://bulbapedia.bulbagarden.net/wiki/Valor_Lakefront) |
| SN-L06 | Acuity Lakefront | landmark | north: Lake Acuity; east: Snowpoint City; south: Route 217 | not started | [4347594](https://bulbapedia.bulbagarden.net/wiki/Acuity_Lakefront) |
| SN-L07 | Mt. Coronet | landmark | located: Center of Sinnoh/Hisui Between Route 207 and Route 208, center of Route 211, east of Route 216 | not started | [4624270](https://bulbapedia.bulbagarden.net/wiki/Mount_Coronet) |
| SN-L08 | Spear Pillar | landmark | located: Mount Coronet | not started | [4633935](https://bulbapedia.bulbagarden.net/wiki/Spear_Pillar) |
| SN-L09 | Oreburgh Gate | landmark | east: Oreburgh City; west: Route 203 | not started | [4339856](https://bulbapedia.bulbagarden.net/wiki/Oreburgh_Gate) |
| SN-L10 | Oreburgh Mine | landmark | located: Oreburgh City | not started | [4591312](https://bulbapedia.bulbagarden.net/wiki/Oreburgh_Mine) |
| SN-L11 | Ravaged Path | landmark | located: Route 204 | not started | [4541354](https://bulbapedia.bulbagarden.net/wiki/Ravaged_Path) |
| SN-L12 | Floaroma Meadow | landmark | located: In northern Floaroma Town | not started | [4636262](https://bulbapedia.bulbagarden.net/wiki/Floaroma_Meadow) |
| SN-L13 | Valley Windworks | landmark | located: East of Floaroma Town | not started | [4631282](https://bulbapedia.bulbagarden.net/wiki/Valley_Windworks) |
| SN-L14 | Eterna Forest | landmark | located: Route 205 | not started | [4624286](https://bulbapedia.bulbagarden.net/wiki/Eterna_Forest) |
| SN-L15 | Old Chateau | landmark | located: Eterna Forest / Canalave City () | not started | [4518870](https://bulbapedia.bulbagarden.net/wiki/Old_Chateau) |
| SN-L16 | Fuego Ironworks | landmark | located: West of Route 205, north of Floaroma Town | not started | [4564207](https://bulbapedia.bulbagarden.net/wiki/Fuego_Ironworks) |
| SN-L17 | Wayward Cave | landmark | located: Beneath Sinnoh's Cycling Road  / Southern Coronet Highlands | not started | [4596195](https://bulbapedia.bulbagarden.net/wiki/Wayward_Cave) |
| SN-L18 | Cycling Road | landmark | north: Eterna City; south: Route 207 | not started | [4590443](https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_206) |
| SN-L19 | Amity Square | landmark | located: Hearthome City | not started | [4631942](https://bulbapedia.bulbagarden.net/wiki/Amity_Square) |
| SN-L20 | Lost Tower | landmark | located: Route 209 | not started | [4612633](https://bulbapedia.bulbagarden.net/wiki/Lost_Tower) |
| SN-L21 | Solaceon Ruins | landmark | located: Between Solaceon Town and Maniac Tunnel  / Central Crimson Mirelands | not started | [4612799](https://bulbapedia.bulbagarden.net/wiki/Solaceon_Ruins) |
| SN-L22 | Great Marsh | landmark | located: Pastoria City | not started | [4614031](https://bulbapedia.bulbagarden.net/wiki/Great_Marsh) |
| SN-L23 | Trophy Garden | landmark | located:  | not started | [4623792](https://bulbapedia.bulbagarden.net/wiki/Trophy_Garden) |
| SN-L24 | Sendoff Spring | landmark | located: East of Route 214 | not started | [4541358](https://bulbapedia.bulbagarden.net/wiki/Sendoff_Spring) |
| SN-L25 | Spring Path | landmark | east: Sendoff Spring; west: Route 214 | not started | [4591833](https://bulbapedia.bulbagarden.net/wiki/Spring_Path) |
| SN-L26 | Turnback Cave | landmark | located: Sendoff Spring / Spring Path | not started | [4604697](https://bulbapedia.bulbagarden.net/wiki/Turnback_Cave) |
| SN-L27 | Iron Island | landmark | located: Off the western coast of Sinnoh | not started | [4613755](https://bulbapedia.bulbagarden.net/wiki/Iron_Island) |
| SN-L28 | Snowpoint Temple | landmark | located: Snowpoint City / Northern Alabaster Icelands | not started | [4572184](https://bulbapedia.bulbagarden.net/wiki/Snowpoint_Temple) |
| SN-L29 | Victory Road | landmark | located:  | not started | [4580359](https://bulbapedia.bulbagarden.net/wiki/Victory_Road_(Sinnoh)) |
| SN-L30 | Stark Mountain | landmark | located: End of Route 227 | not started | [4604700](https://bulbapedia.bulbagarden.net/wiki/Stark_Mountain) |
| SN-L31 | Fullmoon Island | landmark | located: Off the west coast of Sinnoh | not started | [4541360](https://bulbapedia.bulbagarden.net/wiki/Fullmoon_Island) |
| SN-L32 | Newmoon Island | landmark | located: Off the west coast of Sinnoh | not started | [4520047](https://bulbapedia.bulbagarden.net/wiki/Newmoon_Island) |
| SN-L33 | Pal Park | landmark | located: Route 221, Fuchsia City | not started | [4541362](https://bulbapedia.bulbagarden.net/wiki/Pal_Park) |
| SN-O01 | Flower Paradise | story_or_optional_site | located: North of Seabreak Path | not started | [4382574](https://bulbapedia.bulbagarden.net/wiki/Flower_Paradise) |
| SN-O02 | Hall of Origin | story_or_optional_site | located: Above Spear Pillar / Above Temple of Sinnoh | not started | [4556700](https://bulbapedia.bulbagarden.net/wiki/Hall_of_Origin) |
| SN-O03 | Eterna Galactic Building | story_or_optional_site | located: Eterna City | not started | [4631283](https://bulbapedia.bulbagarden.net/wiki/Team_Galactic_Eterna_Building) |
| SN-O04 | Veilstone Galactic Headquarters | story_or_optional_site | located: Veilstone City | not started | [4631284](https://bulbapedia.bulbagarden.net/wiki/Team_Galactic_HQ) |
| SN-O05 | Battle Park / Battle Frontier | story_or_optional_site | located: Fight Area (Sinnoh) /  (Johto) | not started | [4633021](https://bulbapedia.bulbagarden.net/wiki/Battle_Frontier_(Generation_IV)) |
| SN-O06 | Distortion World | story_or_optional_site | located: The other side of the | not started | [4604699](https://bulbapedia.bulbagarden.net/wiki/Distortion_World) |
