# Averon Region Atlas — design-to-map instructions

**IMPORTANT:** `reference_maps/Averon_Travel_Network_v2.png` is the approved geographic *network* reference. `Averon_Master_Map_v1.png` contains outdated placement/ordering and is historical inspiration only. Neither is a deployable tileset. All maps must be laid out in Porymap or equivalent native decomp map data, with walkable collision, events, warps and in-game reviews.

## Geographic logic
Averon is a single large irregular continent. Westerly moisture feeds rainforests and waterfalls, central ridges throw eastern lands into a rain shadow, northern height creates snowy alpine terrain, and geothermal activity builds a southern offshore volcanic chain. The principal rivers begin in the north, flow through foothills into Vesper's basin, and meet the sea near Gullhaven. Beaches face sheltered southern waters; Breakwater is a rugged western sea cliff and port. Changing biomes requires transitional routes: coastal scrub → wet forest; foothills → stony plain → dry canyon; mountain foothill → conifer forest → high tundra. Never snap directly from white snow to palm-lined desert with no explanation.

## Traversal topology
The approved main loop runs **Saltmere → Windrow → Alderfield (Gym 1) → Breakwater (2) → Coralside → Mossveil (3) → Rillfall → Slateford (4) → Juniper Rest → Sunscar (5) → Vesper → Frostmere → Palehaven (6) → Crownspine (7) → express back toward Vesper → Gullhaven → Ashfall Islands (8) → Victory Isle**. Vesper is *not* a Gym. A returnable side network links Alderfield–Mossveil, Saltmere–Breakwater, southern reefs–ports, postgame Sunscar–Rillfall, and mountain shortcuts. Old rail lines later restore connections. A physical path and a railway should not be conflated: railway shortcuts can teleport between labeled, player-visited stations after their flag is earned. See `data/route_network.csv` for the edge list and unlock rule.

## Scale and visual readability
- Build an overworld as dozens of individually streaming GBA map sections, not one massive physical tilemap.
- Main routes generally have **two interesting visual scenes and one gameplay beat** every short stretch; do not stretch emptiness just to increase hours. Optional forks should end in a reward, landmark, NPC activity or shortcut; never just more grass.
- Match path width to movement mechanics: avoid wall-to-wall bottlenecks and random one-tile zigzags. Use visible landmarks and natural leading lines to point toward exit edges and paths.
- Waterfalls must source from higher reservoirs and drain into rivers or coastal basins. Bridges only where the flow/topology makes sense. Buildings connect to workable streets with credible land access.
- Use believable clustered neighborhoods, not a rectangle of evenly spaced houses. Capitals need districts, squares, infrastructure and public spaces; remote hamlets need modest services and local character.
- Pokémon Center and Shop access must never be lost during coup changes. Ferry/rail maps need safe waiting spaces and distinct departure/arrival positions.

## Towns and signature content
**Saltmere (start, western headland)** — Seagrass roofs, pale weatherboard fishing cottages, tiny stone jetty, overlooking lighthouse visible from a later coastal route. Player home, Pip's repair hobby, three houses (greenhouse, workshop, harbor), short starter-dependent errand, small pier festival and one friendly early rival battle. Walkable fields south of town open after first wild encounter. Feel welcoming, not eerie. Morning music bright and quiet.

**Windrow Hamlet (support)** — Orchard rows, irrigation ditches, growers' cooperative, lantern-lit greenhouse, early Berry harvest side quest and first subtle ecological diversity. One shortcut lane to Alderfield opens after badge 1. Don't turn this into a second big city.

**Alderfield (Gym 1)** — Open market, canals with working locks, wooden mill, dairy and grain farms. Normal-type Gym uses changing farm-gate routes to teach positioning; badge reward and simple side festival. Show how non-trainer residents use Pokémon alongside human farm machinery without editorializing.

**Breakwater (Gym 2)** — Three elevations cut into slate sea cliffs, windy footbridges, busy docks, tall lighthouse and harbor promenade. Flying Gym uses rooftop vanes and wind lifts. Fishing derby and harbor work optional. Zapdos belongs on the lighthouse during a late storm return, not during the first Gym quest.

**Coralside (support)** — Seaside cottages, boardwalk, low-tide tidepools, beach volleyball, boat workshop and a route to wet forest. Seaweed green gives way to rainforest near Route R05. A modest beach-race side quest is entirely unrelated to Vantage.

**Mossveil (Gym 3)** — Terraced humid cloud forest town between three cascading waterfalls. Rope bridges, open-air art studio, mushroom gardens, a lantern theater. Ghost Gym is a friendly illusion and performance house, not a horror prison. Oldwood shrine is visible as an obscure *optional* fork and reopens as Celebi's quest later.

**Rillfall Outpost (support)** — Ranger's hut and supply bridge overlooking high-volume falls. Exploration is layered with upper/lower trails and caves. On first passage, no mandatory HM move teaching; later waterfall license reveals higher basins and Suicune route. Local waterfall portrait contest.

**Slateford (Gym 4)** — Mountain quarry with compact stone houses, freight spur, mine elevator and mineral museum. Fighting Gym is a training hall, not a fort. Dorian's trusted public demeanor should hold up to casual interactions; he is competent and sometimes genuinely helpful. The player helps him oppose commander Aster here without recognizing their factional rivalry. Renn fails repeated Gym tests in nearby scenes, but those scenes occupy very little screen time.

**Juniper Rest (support)** — Roadside inn, coach station, old prospectors' sheds, scruffy pine-to-rock vegetation. Wild Pokémon migration quest, cheerful campfire chat, no major conspiracy reveal.

**Sunscar (Gym 5)** — Huge sand-colored oasis town; shaded market lanes, stone aqueducts, water-clock square, old city walls, small underground cistern network. Ground Gym is a tasteful cistern/pump puzzle. Nadia's post-badge two-Pokémon attack is a sharp contrast to the town's normal warmth; badge persists and failure never softlocks.

**Sablewatch (optional)** — Red canyon lookout, modest fossil lab, scenic ledges and small ranger competition. Late return pass to Crownspine is a demanding optional climbing route; build alternate safety waypoints.

**Vesper (capital; NO Gym)** — Terrace riverfront, older brick courthouse, shaded civic gardens, grand station, public library, commercial arcades, department store, battle arcade, quiet residential section. Vesper needs several logically connected native maps. Its political role should never erase its identity as a lively city. Jirachi's 'Odd Key' is acquired in an antique counter/department-store side event and described plainly enough not to miss permanently. The coup visibly changes posters and guards, a rail line opens, shopkeepers continue trading, and exactly TWO mandatory social-reaction sequences follow; optional dialogue can be broader.

**Frostmere (support)** — Lakeside railway stopping point at beginning of snowline; larch forest, stone boathouse, narrow alpine paths, warming lodge. Wildlife tracking contest, small ropeway and low-risk optional cave.

**Palehaven (Gym 6)** — Living glacial village, colored winter banners, climbing hut, market, rink and lake frozen at edges. Ice Gym teaches weather counterplay and clever terrain traversal. Sera later aids the finale because of established trust, not because of a secret identity.

**Crownspine (Gym 7)** — Lofty stone-and-timber city built on multiple ridgelines with safe covered walkways and mountain views. Dragon Gym uses high-altitude trails and an observatory, but should not be a giant endurance trek after the mountain routes. Kellan is a serious mountain guide and genuine mentor. Train shortcut to Vesper opens here; Gym 7 is NOT the last Gym.

**Gullhaven (support)** — Warm estuary rail terminus and ferry port with ceramic roof warehouses, botanical plaza, fishing quay and a ship-repair yard. No Gym. Transition from mountains back to warmer coast should be visibly gradual via lower river valleys, not a sudden terrain swap. Its small post-coup sequence includes both a material improvement and somebody left behind.

**Ashfall Island Chain (Gym 8)** — Three purposeful island sections: friendly residential hot-spring island, geothermal works island, and larger volcano island with black beaches, steam vents, lava caves and Gyms; ferry access from Gullhaven, optional extra reefs and small coves. Fire Gym uses stable pressure/valve puzzles, not punishing unavoidable hazard damage. Heatran lives in the *separate, optional deepest caldera* with its own physical geology, reached later by a geothermal quest.

**Victory Isle (League)** — Remote garden cliffs and fortress-like natural ridge reached by boat after badge 8 and the story finale, with a challenging but readable Victory Road, optional return healing before Elite Four, and a clearly marked League building. Do not make a mandatory 60-minute maze.

**Threshold Annex (story)** — An old government installation behind multiple disused maintenance approaches and a protected interior. Early-game access fails because it is classified; the hidden research records are traced through separate facilities. The final approach has coalition action, ten-battle gauntlet, ally heal, upgraded corrupt Gyms and dimensional rift. Avoid placing its front gate beside an ordinary Route 3 house.

**Tideglass Reefs (optional)** — Reef chain linked to Breakwater and Gullhaven through fishing/surf routes; multiple water encounter tables, diving niches, rare spawning islands, Manaphy research and Mew side quest. More than one island identity; do not copy/paste empty palm islands.

**Starfall Observatory (optional)** — Small abandoned northern astronomy campus. A department-store **Odd Key** physically opens the sealed access door after relevant story flags. Interior puzzles involve constellations and telescope alignment. Jirachi appears through a clear but discoverable quest, not an unexplained random room.

## Structure inside each main route
Every section must have: a meaningful physical transition from previous map, a visible next destination, a visual set piece, an ecological encounter reason, one small interactive detail, 1–4 relevant trainer groups, a no-trainer alternate path or clever shortcut where fitting, and clean event/warp coverage. Trainer counts depend on region progression, not an arbitrary quota. Routes with ferry transitions should also have tide/weather logic or optional islands. Keep two or three natural town interiors per small village (plus Center/shop) and many well differentiated interiors in larger cities.

## Art-direction consistency tests
- One palette/tileset guide per biome. Avoid mixing top-down sprite perspectives with 3/4 buildings or GBA and DS pixel scales.
- Every tall cliff shadow falls the same general direction within a scene. Rivers and terrain heights must match exits.
- Water edges, stair ends, slopes, fences and collision tiles all reviewed in emulator. No walkable black backgrounds, duplicate NPCs after story flag update, teleporting through walls, or irrecoverable cliff jumps.
- Show each settlement as a standalone Porymap screenshot before publishing it as 'done'. Take day/night screenshots if the engine includes time-of-day.
