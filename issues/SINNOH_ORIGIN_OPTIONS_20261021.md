# Future Sinnoh origin names — decision evidence, not an allocation

Read-only proposal while northern PR206 graphical verification runs. Production IDs0–214, NONE215, specials253–255, all saved Pokémon and current meanings remain untouched. No227+ allocation, alias deployment, save migration, map or story is implemented here. Route numbers such as227 are geographic names, not proposed saved byte values.

Source: main `f4548cca06d56c45595cbcb3386ed32f09d5a362`; the anticipated already-owner-approved216–226 registry is PR206 code `79f2070e71b1358947ea87c0178914ec2c25e86a`. Live main still has only216–223 at generation time. Reserve224–226 for the approved northern integration rather than promising those slots twice. Afterward **26 of37 ordinary new codes remain**. The full CSV has87 tracker areas; it is not a complete child-map or future Averon naming inventory.

## Concrete choices

| Read-only scenario | Distinct Sinnoh names | Additional Averon reserve | New codes needed after approved11 | Available | Shortfall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Low, aggressive future parent grouping |33|4|26|26|0|
| Base, only the already approved three area pairs |84|4|77|26|51|
| High, additionally distinguish11 verified child headers across3 future parents |92|8|89|26|63|

The raw87-name, zero-reserve counterfactual exceeds the total37-name pool by50. Applying the **three** approved register pairs (Lake Verity/Lakefront, Route204/Ravaged Path, Floaroma Town/Meadow) gives84 names, shortfall47 before reserve. Route205's two halves are already ONE register entry, so do not subtract them again.

Low is a deliberately severe compromise, not a recommended production codebook. The [87-row proposal](../Pokemon%20Game/Averon_Codex_Handoff/design/sinnoh/origin-planning/name-groups.json) preserves every frozen name and approved pairing, then groups73 future areas under22 unapproved future labels. Examples: Eterna City would also label Forest/Chateau/Route206/Wayward/Cycling Road; Oreburgh City would label Route207/Mine; Iron Island would also label Fullmoon/Newmoon; Mt. Coronet would also label Spear Pillar/Hall of Origin. **In today's engine these losses affect both entry popups and Pokémon met text.** They are not invisible storage optimizations. All51 collapsed future names and every member are inspectable; merge of this proposal approves none of them.

Four/eight future Averon codes are illustrative nonzero reserves, NOT a verified estimate that the complete first region needs so few. Greater Averon demand or more named child areas increases the shortfall. Existing Hoenn/Kanto names or apparently unused values are never recycled. Identical text in another region is not permission to reuse its saved identity.

High reads actual immutable donor header blobs at `38228bb574a3557345852b758d5f1a65eb01bb22`:4 Mt.Coronet,5 OldChateau,2 OreburghMine headers. Replacing their3 parent labels with11 child labels adds8. [Header receipts](../Pokemon%20Game/Averon_Codex_Handoff/design/sinnoh/origin-planning/donor-child-headers.json) include blob IDs and declared sections/layouts. This proves source headers, not complete geography or asset rights. Ambiguous Hoenn/FRLG VictoryRoad headers are excluded; absent exact-prefixed Wayward/IronIsland/Stark headers in this bounded search are not proof that no differently named source exists.

## Recommended technical preparation

Prepare an **off-production** proof of distinct runtime display names with coarse immutable8-bit saved origins, then obtain the owner's player-facing precision decision. This could preserve Pokémon/PC/save structures while avoiding false promises that37 codes supply a full individually named atlas. Runtime labels and saved map group/slot identities are different from met-origin codes. No runtime widening or label override is implemented by this proposal.

If distinct caught-location names for most areas are required, an explicitly versioned expanded-origin design needs separate owner approval and adversarial old-save/party/PC/encryption/controller/trade/egg/hatch/summary tests. Existing13-bit work is incomplete; it is not migration acceptance. Reuse the October18 compatibility research rather than repeating it or silently adopting its prototype. Existing namespace/alias rejection guards remain intact.

The future decision is **how much saved-origin precision the owner wants**, not whether to click another routine GitHub handoff. Until that choice, keep approved IDs and source-stage additional geography; no new production codebook is selected.

## Executed verification and reproduction

Used existing `scripts/averon_origin_demand.py` with `audit-averon-mapsec-namespace.sections()`: raw87, base84, low33, high92; exact shortfalls50/51/0/63 in their stated scenarios. Checked all87 keys exactly once, all11 frozen names retained, no unknown grouping keys, unchanged source CSV hash, and zero production allocations. These are planning assertions, not native/ROM/gameplay tests.

For reproduction, read `name-groups.json`; make an in-memory copy of the CSV applying ONLY its three explicitly documented already-approved pair normalizations. Feed that copy to `origin_demand()` with reserve4, then apply its per-row proposed_low_name aliases for Low. For High replace each of the3 unallocated parent names with its first recorded child label and pass the remaining8 as `additional`, reserve8. The [machine-readable results](../Pokemon%20Game/Averon_Codex_Handoff/design/sinnoh/origin-planning/capacity-scenarios.json) preserve all group memberships and legacy-name collisions. Do not overwrite the production CSV or weaken the calculator's deliberate rejection of silently expanding a frozen name.
