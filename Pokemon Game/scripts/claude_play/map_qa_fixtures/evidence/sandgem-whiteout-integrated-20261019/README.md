# Healer 44 on the integrated tree: main + #150 + #151

Tree: main `0b46609c` + #150 (`af28cc6e`) + #151 (`b2e45a0c`), merged locally and not pushed. That is what main becomes once both PRs land. Engine tree `57707119`.

| Check | Result |
|---|---|
| NORMAL build | `d15f8db3…`, linked 17,326,944 B (+3,096 over main: Route 201 +3,072, healer 44 +24), 0 compiler warnings |
| RELEASE build | `963e4f09…`, linked 17,446,112 B (+3,096), 0 compiler warnings |
| Native Averon | **289/289**, with the 2 Route 201 and 3 Sandgem healer tests |
| Production smoke, NORMAL (`smoke-*`): Route 201 + Sandgem + Center | **35/35**, then fresh Continue **3/3** |
| Production smoke, RELEASE | **35/35**, then fresh Continue **3/3** |
| Real whiteout (`whiteout-positive-*`) | PASS, then Continue PASS. Entering the Center sets anchor (15, 10); a level-80 battle is lost with ordinary input; the game's whiteout lands at Sandgem Center (7, 4) facing the nurse; healed; money lost |
| Negative, `setrespawn` stripped (`whiteout-negative-*`) | FAIL as required, on the anchor and landing checks |

The smoke runs cover both Route 201 seams, the closed edges, the Center door and mats, the follower, the Start menu and Save → fresh Continue.

- **DEV-only setup, disclosed:**
  - entry is a `map_qa fixture-save` continue-warp to Sandgem (15, 10);
  - the whiteout battle is a TEST-ONLY `wildbattle` fixture on the Sandgem man (27, 12), applied in a throwaway tree.
- There are no wild encounters in production.
- No ROMs or saves are committed.
