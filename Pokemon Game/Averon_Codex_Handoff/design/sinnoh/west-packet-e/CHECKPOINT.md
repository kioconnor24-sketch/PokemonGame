# Packet E source stage (C51)

Built on main `43d8ad33`. This is source only: no section, slot, registry or engine file is touched.

`stage_packet_e.py` selects the one staged source for each of the 37 maps in `../PACKET_E_PLAN.md`:
- Codex `hearthome-solaceon`: the seven outdoor maps and gates.
- Overlays: `city-shells` (Route 208, Route 210 South), `amity-square` (Hearthome), `lost-tower` (Route 209), `solaceon-ruins-entrance` (Solaceon).
- Interiors: `city-shells`, `lost-tower`, `solaceon-ruins-entrance`, `solaceon-depths` (B2F East without the tunnel warp) and `amity-square`.

It pins all 159 source files by SHA-256 (`source-pins.json`) and proves the combined graph is closed:
- every warp lands on a warp that leads back;
- every connection has its opposite with the negated offset;
- nothing leaves the 37 maps;
- there are no objects or bg events;
- the only coord events are Lost Tower's 4 Route 209 trigger warps.

**Still closed:** Route 208 ↔ Mt. Coronet 1F South waits for packet D. Hearthome's Route 212 doors wait for packet F, which appends them at indices 15–16. Maniac Tunnel waits for packet G. Route 210 North and Route 215 come later.

## Evidence

- `test_sinnoh_packet_e_stage`: 9/9. The negatives are: a changed byte, a wrong return index, a one-sided offset, the tunnel variant leaving the packet, and an added object.
- **Static audit:** I installed the scene with `static_scene.py REPO hearthome-solaceon BATCH <37 maps>` and audited all 37 maps with `map_qa static`. Result: **PASS, 0 findings**.
- **Live NORMAL/RELEASE traversal with Save → fresh Continue:** see the PR thread.

## Reproduce

```
stage_packet_e.py --check
stage_packet_e.py --out BATCH        # then static_scene.py REPO hearthome-solaceon BATCH <map ids>
```

## Next

Packet E production install needs:
- packet D on main, then the two-cell Coronet join;
- the owner's section record (231–238 are still proposed);
- an owner exact-path handoff.
