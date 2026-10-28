# Packet F corridor stage (C52): Hearthome → Route 212 → Pastoria → Great Marsh

This is source only. It is stacked on packet E's stage (C51, #351) and touches no section, slot, registry or engine file.

`stage_packet_f.py` adds 20 maps to packet E's 37 and pins all 248 source files:
- **Route 212:** Route212_Access; Route212_North (eastern-loop + the W17 mansion overlay) with Mansion 1F/2F; Route212_South (eastern-loop + `city-shells` house overlay + Codex's one-cell `route212-foot-crossing` map) with House1.
- **Pastoria:** eastern-loop + the W10 overlay, with the stock Center 1F (main's latest W10, not the older house shell) and Houses 2–8.
- **Great Marsh:** the gate, plus GreatMarsh / North / NorthWest / West (W18).

**Reconciled with packet E.** These files are derived, with each change asserted:
- **Hearthome warps:** W11's warps 0–14 are kept unchanged, and central-joins' two Route 212 Access doors are **appended at 15–16**.
- **Hearthome cells:** only (8,46) and (9,46) change. Their collision bit is cleared, and the result must equal central-joins' reopened words.
- **Route212_Access:** its Hearthome return is 15 (it was 2 in central-joins).

A reordered W11 header and a changed crossing source are both refused.

**External exits** (packet G), declared exactly: Pastoria warp 0 → Route213_Access, and Pastoria → Route 213 connection.

## Evidence

- `test_sinnoh_packet_f_stage`: 7/7, run together with packet E's 9/9.
- **Static audit:** installed with `static_scene.py REPO hearthome-solaceon+eastern-loop BATCH <57 maps>`. Result: **PASS, 0 findings**.
- **Live NORMAL/RELEASE traversal with Save → fresh Continue:** see the PR thread. It is queued after the C53 gate.

## Not included

No sections, story, objects or Route 213 / Veilstone / Valor (packet G).
