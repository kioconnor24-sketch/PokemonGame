# Packet G side connection: Solaceon Ruins ↔ Maniac Tunnel ↔ Route 214 (C53)

This is source only. It is stacked on packet E's stage (C51, #351) and touches no section, slot, registry or engine file.

`stage_tunnel_link.py` starts from packet E's 37 maps and makes three changes:
1. **B2F East:** swaps in `maniac-ruins-link`'s variant. Its warp 2 is the tunnel ladder at (24,16). Packet E keeps the two-warp `solaceon-depths` variant, so this ladder exists only once packet G's tunnel exists.
2. **Tunnel:** adds ManiacTunnel and ManiacTunnel_B1F (`maniac-ruins-link`).
3. **Route 214:** adds Codex `eastern-loop`'s map with `sendoff-spring`'s overlay, whose warp 2 at (9,35) is the tunnel mouth.

**The chain**, reciprocal index for index: Route214 w2 ↔ ManiacTunnel w0; ManiacTunnel w1 ↔ B1F w0; B1F w1 ↔ Ruins B2F East w2.

It pins all 182 source files. Every warp and connection inside the 40 maps is reciprocal, and every Ruins stair returns to its source floor. Route 214's other exits are an exact declared-external list:
- gate warps 0/1 → Route214_Access;
- Veilstone (up), Valor Lakefront (down), Spring Path (right).

An undeclared exit fails, and so does a declared exit that disappears.

## Evidence

- `test_sinnoh_packet_g_tunnel_stage`: 8/8, run together with packet E's 9/9.
- **Static audit:** installed with `static_scene.py REPO hearthome-solaceon+eastern-loop BATCH <40 maps>`. The batch carries the Spring Path / Sendoff Spring / Turnback Cave maps as DEV context only. Result: **PASS, 0 findings**, nothing skipped.
- **Live NORMAL/RELEASE traversal with Save → fresh Continue:** see the PR thread. It runs after the C51 gate.

## Not included

- No Unown condition, story, objects or sections.
- Packet G's outdoors are not staged here: Route 213/214 production, Valor Lakefront, Veilstone and the Route 214 gate. Route 214 is here only as the tunnel's physical endpoint.
