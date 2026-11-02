# Link-cable session harness (work in progress, for #362)

Not yet run against a game. Saved mid-task on 2026-11-02 when work was stopped.

- `linkharness.c`: two real GBA cores joined by mGBA 0.10.5's own GBA SIO lockstep driver (the code behind mGBA-Qt's multiplayer window), stepped from one thread. Build: `apt-get install libmgba-dev`, then `gcc -O2 linkharness.c -o linkharness -lmgba`. Compile WITHOUT `-DNDEBUG`: the Ubuntu libmgba is built with the debug-only lockstep fields. Commands on stdin: `run N`, `keys P MASK`, `read P ADDR LEN`, `shot P PATH`, `quit`.
- `link_fixture.py`: offline DEV save fixture, using the same origin encoding as `wide_origin_qa.py`. Clones the first party Pokemon into slots with given met locations, optionally sets FLAG_SYS_POKEDEX_GET (the Direct Corner precondition) and rewrites sector checksums. Place the player with `map_qa.py fixture-save` (for example MAP_OLDALE_TOWN_POKEMON_CENTER_2F, facing the Direct Corner attendant at 10,2).

Remaining plan: build the #362 ROM and the current main ROM. Make a format-2 wide save, which needs one solo save on the #362 ROM before adding origins above 255. Run Trade Center sessions wide<->wide (compatible: an origin of 1021 must arrive intact) and wide<->main (legacy: wide Pokemon refused, byte origins unchanged). Check both parties and the saved flash afterwards.
