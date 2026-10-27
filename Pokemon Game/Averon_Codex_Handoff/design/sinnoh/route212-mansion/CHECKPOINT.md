# W17 Route 212 North mansion: checkpoint

OFF-ENGINE staging, stacked on W12 (`claude/city-shells-w12`, which supplies `civic()` and `map_bin()`).

## Source anchor

Codex's eastern-loop `Route212_North` draws a large mansion facade at the DS Pokémon Mansion position. Its door (24,38) is the bank's closed door picture 529, which is solid. The source receipt lists 0 closures, so the door is solid in the source itself.

## Maps (3)

**Route212_North-dev-overlay**
- The derived blockdata changes **one** cell: (24,38) gets the family's animated door word, copied from Veilstone's north-east door (41,14). Both cells have the same 528/528/525 surroundings, and the copy is asserted.
- The header appends one warp. Everything else is identical.

**Interior**
- `Route212_North_Mansion_1F/2F` reuse the stock Cove Lily Motel 1F/2F layouts unchanged, with the stair pair copied and renamed.
- The 1F mats return to the door.
- FRLG interiors (such as the Celadon condominiums) were tried first and rejected. mapjson skips `layout_version: frlg` layouts in the Emerald build, and the static audit caught it.

## Not done

The fenced garden behind the facade (the DS Trophy Garden) is solid in the source, so it stays closed. No source cell supports a walkable garden.

## Tests run

- `test_sinnoh_route212_mansion.py` 5/5 (with W12's 5/5). The tests cover:
  - a reproducible build;
  - only the door cell changes, and it equals the working door word;
  - one appended warp;
  - the stock stair graph is reciprocal, plus a one-way negative;
  - the interior layouts are in the Emerald build.
- Static map_qa (#252 `64d0e222`) on the eastern-loop scene: Route 212 North/South/Access, Mansion 1F/2F, **0 findings**.
- No ROM, mGBA or Save/Continue claim yet.

## Not included

No NPCs, services, objects, story or sections (MAPSEC_PENDING_OWNER).
