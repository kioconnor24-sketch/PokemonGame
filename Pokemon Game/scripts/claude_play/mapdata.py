"""Static map knowledge for the local playthrough driver, read from source.

Everything here comes from the engine's own map, layout and tileset files:
collision bits and elevation from each layout's map.bin, metatile behaviours
from the tilesets' metatile_attributes.bin, and warps, connections and objects
from map.json. The driver only uses this to plan ordinary walking; it never
changes the game.
"""
import json
import pathlib
import re
import struct
from collections import deque

DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}


def _behavior_names(engine):
    text = (engine / "include/constants/metatile_behaviors.h").read_text()
    body = text[text.index("enum {") + 6:text.index("};")]
    names = [m.group(1) for m in re.finditer(r"^\s*(MB_[A-Z0-9_]+)", body, re.M)]
    return {i: n for i, n in enumerate(names)}


class World:
    def __init__(self, engine):
        self.engine = pathlib.Path(engine)
        groups = json.loads((self.engine / "data/maps/map_groups.json").read_text())
        self.map_ids = {}  # "MAP_X" -> (group, num, folder)
        for g, gname in enumerate(groups["group_order"]):
            for n, folder in enumerate(groups[gname]):
                info = json.loads((self.engine / f"data/maps/{folder}/map.json").read_text())
                self.map_ids[info["id"]] = (g, n, folder)
        self.by_num = {(g, n): mid for mid, (g, n, _) in self.map_ids.items()}
        self.layouts = {l["id"]: l for l in json.loads(
            (self.engine / "data/layouts/layouts.json").read_text())["layouts"] if "id" in l}
        self.behavior_names = _behavior_names(self.engine)
        self._attrs = {}
        self._maps = {}
        headers = (self.engine / "src/data/tilesets/headers.h").read_text()
        self._tileset_attr_symbol = dict(re.findall(
            r"const struct Tileset (gTileset_\w+) =\s*\{[^}]*?\.metatileAttributes = (\w+)", headers, re.S))
        metatiles = (self.engine / "src/data/tilesets/metatiles.h").read_text()
        self._attr_file = dict(re.findall(r"const u16 (\w+)\[\] = INCBIN_U16\(\"([^\"]+)\"\)", metatiles))

    def _attributes(self, tileset):
        if tileset not in self._attrs:
            path = self.engine / self._attr_file[self._tileset_attr_symbol[tileset]]
            raw = path.read_bytes()
            self._attrs[tileset] = struct.unpack(f"<{len(raw) // 2}H", raw)
        return self._attrs[tileset]

    def map(self, map_id):
        if map_id not in self._maps:
            self._maps[map_id] = MapInfo(self, map_id)
        return self._maps[map_id]

    def map_at(self, group, num):
        return self.map(self.by_num[(group, num)])


class MapInfo:
    def __init__(self, world, map_id):
        self.world = world
        self.id = map_id
        self.group, self.num, self.folder = world.map_ids[map_id]
        info = json.loads((world.engine / f"data/maps/{self.folder}/map.json").read_text())
        self.info = info
        layout = world.layouts[info["layout"]]
        self.width, self.height = layout["width"], layout["height"]
        raw = (world.engine / layout["blockdata_filepath"]).read_bytes()
        self.blocks = struct.unpack(f"<{self.width * self.height}H", raw)
        self._primary = world._attributes(layout["primary_tileset"])
        self._secondary = world._attributes(layout["secondary_tileset"])
        self._derive_behaviors()
        self.warps = [(w["x"], w["y"], w["dest_map"], int(w["dest_warp_id"]))
                      for w in info.get("warp_events", [])]
        self.connections = [(c["direction"], c["map"], int(c["offset"]))
                            for c in (info.get("connections") or [])]
        self.objects = [(o["x"], o["y"], o.get("script", ""), o.get("graphics_id", ""))
                        for o in info.get("object_events", [])]
        self.triggers = {(c["x"], c["y"]) for c in info.get("coord_events", []) if c.get("type", "trigger") == "trigger"}

    def _derive_behaviors(self):
        self.behaviors = []
        for b in self.blocks:
            mid = b & 0x3FF
            if mid < 512:
                attr = self._primary[mid] if mid < len(self._primary) else 0
            else:
                attr = self._secondary[mid - 512] if mid - 512 < len(self._secondary) else 0
            self.behaviors.append(self.world.behavior_names.get(attr & 0xFF, "MB_?"))

    def with_live_blocks(self, blocks):
        """A copy using the game's current map grid (setmetatile changes, gates)."""
        import copy
        live = copy.copy(self)
        live.blocks = tuple(blocks)
        live._derive_behaviors()
        return live

    def inside(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def collision(self, x, y):
        return (self.blocks[y * self.width + x] >> 10) & 3

    def elevation(self, x, y):
        return self.blocks[y * self.width + x] >> 12

    def behavior(self, x, y):
        return self.behaviors[y * self.width + x]

    def is_grass(self, x, y):
        return self.behavior(x, y) in ("MB_TALL_GRASS", "MB_LONG_GRASS")

    def walkable(self, x, y):
        if not self.inside(x, y) or self.collision(x, y):
            return False
        b = self.behavior(x, y)
        if "WATER" in b or b.startswith("MB_JUMP") or b == "MB_COUNTER":
            return False
        return True

    def warp_at(self, x, y):
        for wx, wy, dest, warp in self.warps:
            if (wx, wy) == (x, y):
                return dest, warp
        return None


def elevation_at(m, x, y):
    """Map elevation of a tile (0 when the map model has none, e.g. test fakes: no restriction)."""
    return m.elevation(x, y) if hasattr(m, "elevation") else 0


def step_across(cur, frm_e, to_e):
    """The player's elevation after a step from a tile of elevation frm_e onto one of to_e (on the same map or
    across a seam), or None when the engine refuses it.

    Mirrors pokeemerald: IsElevationMismatchAt blocks entering a tile whose elevation is neither 0 nor 15 nor
    the player's own (unless the player is at 0); ObjectEventUpdateElevation then takes the new tile's
    elevation, except to or from a 15 (bridge) tile, which keeps the previous one.
    """
    if cur != 0 and to_e not in (0, 15) and to_e != cur:
        return None
    return cur if to_e == 15 or frm_e == 15 else to_e


def step_elevation(m, cur, frm, to):
    """step_across for a step frm -> to on m."""
    return step_across(cur, elevation_at(m, *frm), elevation_at(m, *to))


def crossable(m, tile, other, to):
    """Whether some player who can stand on tile (any start_elevations) may step across the seam onto other's to."""
    return any(step_across(e, elevation_at(m, *tile), elevation_at(other, *to)) is not None
               for e in start_elevations(m, tile))


def reach_states(m, start, elevation=None):
    """{tile: elevations} reachable on foot from start (as bfs: a takeable warp tile is reached, not crossed)."""
    first = [(start, e) for e in (start_elevations(m, start) if elevation is None else [elevation])]
    seen, q = set(first), deque(first)
    while q:
        cur, e = q.popleft()
        if cur != start and takeable(m, *cur):
            continue
        for dx, dy in DIRS.values():
            nxt = (cur[0] + dx, cur[1] + dy)
            if not m.walkable(*nxt):
                continue
            ne = step_elevation(m, e, cur, nxt)
            if ne is not None and (nxt, ne) not in seen:
                seen.add((nxt, ne))
                q.append((nxt, ne))
    out = {}
    for t, e in seen:
        out.setdefault(t, set()).add(e)
    return out


def start_elevations(m, start):
    """Elevations the player may have on start when the actual one is unknown.

    Normally the tile's own. A 15 (bridge) tile keeps the elevation the player arrived with: that of any walkable
    tile next to the bridge (the connected 15 tiles around start), or 15 itself when warped straight onto it."""
    e = elevation_at(m, *start)
    if e != 15:
        return [e]
    seen, todo, levels = {start}, [start], {15}
    while todo:
        x, y = todo.pop()
        for dx, dy in DIRS.values():
            t = (x + dx, y + dy)
            if t in seen or not (m.inside(*t) and m.walkable(*t)):
                continue
            if elevation_at(m, *t) == 15:
                seen.add(t)
                todo.append(t)
            else:
                levels.add(elevation_at(m, *t))
    return sorted(levels)


def bfs(m, start, goals, blocked=frozenset(), allow_goal_unwalkable=True, elevation=None):
    """Shortest list of direction names from start to any goal tile, honouring the engine's elevation rules.

    elevation is the player's actual elevation; when None, every possible one on start (start_elevations)."""
    goals = set(goals)
    if start in goals:
        return []
    first = [(start, e) for e in (start_elevations(m, start) if elevation is None else [elevation])]
    prev = dict.fromkeys(first)
    q = deque(first)
    while q:
        state = q.popleft()
        cur, e = state
        for name, (dx, dy) in DIRS.items():
            nxt = (cur[0] + dx, cur[1] + dy)
            if nxt in blocked:
                continue
            ok = m.walkable(*nxt) or (allow_goal_unwalkable and nxt in goals and m.inside(*nxt))
            if not ok:
                continue
            # A warp tile that is not the goal would take us elsewhere.
            if nxt not in goals and takeable(m, *nxt):
                continue
            ne = step_elevation(m, e, cur, nxt) if m.walkable(*nxt) else e
            if ne is None or (nxt, ne) in prev:
                continue
            prev[(nxt, ne)] = (state, name)
            if nxt in goals:
                path = []
                node = (nxt, ne)
                while prev[node]:
                    node, step = prev[node]
                    path.append(step)
                return path[::-1]
            q.append((nxt, ne))
    return None


STEP_ON = ("MB_LADDER", "MB_MT_PYRE_HOLE")


def takeable(m, x, y):
    """Whether the warp at (x, y) can be taken at all. The engine warps only through a door, arrow, stair, ladder,
    escalator or hole behaviour (TryArrowWarp, TryDoorWarp, IsWarpMetatileBehavior) or a coord trigger; a warp on
    any other tile is only an arrival point (e.g. the floor where a Mt. Pyre hole drops the player). Step-on behaviours
    (ladder, hole, non-animated door, escalator) also need the tile to be enterable; an animated door is pushed into."""
    if m.warp_at(x, y) is None:
        return False
    b = m.behavior(x, y)
    if (x, y) in getattr(m, "triggers", ()):
        return True
    if b in STEP_ON or b == "MB_NON_ANIMATED_DOOR" or "ESCALATOR" in b:
        return m.walkable(x, y)          # IsWarpMetatileBehavior warps only when stepped onto: a solid one is shut
    return "DOOR" in b or "WARP" in b


def trigger_entry(m, x, y):
    """A warp tile that also carries a coord trigger is a step-on warp (no arrow/door metatile).

    Returns (approach tile, direction to step onto the warp) or None. The player arrives on the warp tile.
    """
    triggers = getattr(m, "triggers", ())
    if m.warp_at(x, y) is None:
        return None
    # A ladder or a Mt. Pyre hole warps when stepped onto (field_control_avatar IsWarpMetatileBehavior): the player
    # arrives standing on it and must step off and back on to use it, exactly as a coord-trigger warp.
    if (x, y) not in triggers and not (m.behavior(x, y) in STEP_ON and m.walkable(x, y)):
        return None
    for d, (dx, dy) in DIRS.items():
        approach = (x - dx, y - dy)
        if m.walkable(*approach) and approach not in triggers and not takeable(m, *approach):
            return approach, d
    return None


def across(m, other, direction, offset, tile):
    """Where stepping off m at tile lands in the connected map (fieldmap: pos -= offset)."""
    x, y = tile
    if direction == "up":
        return (x - offset, other.height - 1)
    if direction == "down":
        return (x - offset, 0)
    if direction == "left":
        return (other.width - 1, y - offset)
    return (0, y - offset)


def warp_arrival(m, x, y):
    """Where a warp into (x, y) of m lands the player: on a step-on (trigger) warp or an arrow mat, the tile
    itself; at a door or any solid warp tile, the doorstep below it."""
    if trigger_entry(m, x, y):
        return (x, y)
    if "DOOR" in m.behavior(x, y) or not m.walkable(x, y):
        return (x, y + 1)
    return (x, y)


def edge_exits(m, direction):
    """Tiles on m's edge from which stepping `direction` enters the connected map."""
    conn = next((c for c in m.connections if c[0] == direction), None)
    if conn is None:
        return []
    other = m.world.map(conn[1])
    offset = conn[2]
    tiles = []
    if direction in ("up", "down"):
        y = 0 if direction == "up" else m.height - 1
        oy = other.height - 1 if direction == "up" else 0
        for x in range(m.width):
            ox = x - offset
            if m.walkable(x, y) and other.inside(ox, oy) and other.walkable(ox, oy):
                tiles.append((x, y))
    else:
        x = 0 if direction == "left" else m.width - 1
        ox = other.width - 1 if direction == "left" else 0
        for y in range(m.height):
            oy = y - offset
            if m.walkable(x, y) and other.inside(ox, oy) and other.walkable(ox, oy):
                tiles.append((x, y))
    return tiles
