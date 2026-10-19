# Route 201: Save → fresh Continue taken on Route 201 itself

This run uses the production ROMs from this PR, rebuilt clean at final head `633ddcab` (engine tree `c76d66ad`). Those rebuilds are **byte-identical** to the ROMs tested in `../`. The harness is main's `map_qa.py` after #152 (single-step seams).

| Build | ROM SHA-256 | Run | Saved at | Fresh Continue |
|---|---|---|---|---|
| NORMAL | `a93de284…8266d` | **PASS 11/11** | `MAP_ROUTE201` (63, 9) | **PASS 3/3**, restored on `MAP_ROUTE201` (63, 9) |
| RELEASE | `4e085926…7827` | **PASS 11/11** | `MAP_ROUTE201` (63, 9) | **PASS 3/3**, restored on `MAP_ROUTE201` (63, 9) |

- **Entry:** a disclosed DEV-only `map_qa fixture-save` continue-warp onto Route 201 (20, 10). Its base saves are the existing NORMAL (`offn-a`) and RELEASE (`rel-off-r9`) saves; no source changes.
- **Each run checks:**
  - the closed edges: Twinleaf (16, 21) and Lake Verity (0, 10) and (0, 14);
  - the Sandgem seam, out and back, on rows 6, 8 and 9;
  - the Start menu;
  - SAVE on Route 201.
- **Continue:** a second, fresh mGBA process with the saved flash checks that CONTINUE restores the same map, position, flags and party (`*-continue/continue-check.json`). The screenshot `release-continue/0008-continued.png` shows the "ROUTE 201" popup on load.
- No ROMs, saves or savestates are committed.
