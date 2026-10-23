# Genuine foot-traversal limitation — not accepted

Corrected 66-file DEV engine `9571d23131b6793f908f469c73fe82d021340b74`, source `ac5a90b9e44b84eaa0d4dbbb10c8c0b0a3b98ed4`, NORMAL ROM SHA256 `16bfc6da6c11e281617813d9bb1085aacdd74901063ac4523eae17139b9611dd`.

Actual graphical mGBA run: **103/107 PASS, overall FAIL**. Hotel north/south door traversal and return succeeded. From Route212South (36,12), north seam probes (10,0),(13,0),(15,0) failed; final route planning raised Stuck. No final Save/Continue or complete thirteen-map acceptance from this run.

Observed native foot inputs failed at (40,11),(39,11),(38,11),(37,11),(36,11). Every cell is unchanged C0/E15 with full source `MB_HORIZONTAL_RAIL` behavior. Both pinned donor `38228bb574a3557345852b758d5f1a65eb01bb22` and current Averon field_player_avatar.c:CheckAcroBikeCollision return an Acro rail collision independently of current elevation. Collision-only static connectivity is insufficient to prove foot connectivity. The new real-World regression rejects rail destinations, including when used as goals, and proves no ordinary foot path from (36,12), layer3 to (10,0).

Do not clear rail attributes/collision, silently grant a bike or movement flag, or infer Surf/Bike progression. The default QA still tests all thirteen maps and retains this failure. Explicit optional subset scopes have distinct save labels and are bounded evidence only; they cannot establish this missing through-route. Separate northern DEV-entry evidence is not a natural arrival.

Next: prove intended original Acro rail/upper/lower-layer traversal using ordinary game inputs and a transparently declared legal DEV inventory setup, or propose a source-grounded physical adaptation with explicit changed-attribute review. Keep the present PR draft until genuine whole-corridor requirements are resolved or manager explicitly bounds its deliverable. No new saved origin, production engine or permanent map was altered.
