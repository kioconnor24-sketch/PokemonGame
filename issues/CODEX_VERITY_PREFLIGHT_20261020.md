# Verity technical preflight — implementation handoff

Source main `ac4f6b1e` (full SHA in paired JSON), donor
`38228bb574a3557345852b758d5f1a65eb01bb22`. No production maps/engine/assets,
registry, saved IDs, story or Claude QA changed. #181 remains a separate protected
integration lane. Owner explicitly resumed Codex for this Verity-only assignment;
older STOP instructions are historical.

## Measured result

| | VerityLakefront | LakeVerity |
|---|---:|---:|
| Dimensions / bytes |20x20 /800|48x46 /4416|
| Git blob |916c66be28572f75c70af7a0ff25bcec17a78c05|1fba9218763961d1e2298f404d2bed0ed6a13c41|
| Distinct primary / secondary IDs |22 /12|41 /11|
| Secondary cells |20|17|
| Same-index primary record+attribute matches in Averon |14/22|8/41|
| Secondary same-record matches anywhere in Petalburg OR Dewford |0/12|0/11|
| Exact static pixels+full attribute candidates in General+Dewford |7/34|11/52|
| Missing target numeric indices (both candidate pairs) |0|0|
| Pond-water cells |0|1070|

**All numeric slots exist** in current Petalburg144/Dewford379 secondary records;
this is a content/behavior/graphics mismatch, not simply out-of-range indices.
The paired JSON lists EVERY used ID: frequency, upper-bit collision/elevation
counts, behavior name, full attribute/layer bits, graphic and palette IDs,
source static-pixel hash, all structural matches in each candidate and exact
static-pixel+attribute candidates. This includes map cells; border closure is
separately validated by the unchanged paired stager and its receipt.

Both maps successfully staged with merged178; inspection succeeds after the
null-connection count repair below. Staged
map bytes equal donor bytes exactly, proving ALL upper collision/elevation bits
preserved (not a claim of player reachability). No assets published. All required
General/Petalburg assets/frame dimensions/behavior/animation contracts passed.

### Graphics strategy — keep the seamless boundary compatible

Do not replace globally shared General or blindly reuse Route202's provisional
primary-only art decision. **A pure existing-record faithful remap is disproved**:
none of either map's secondary IDs has an exact static-pixel+attribute candidate,
and even primary structural matches do not imply the same art. The7 Lakefront
exact candidates are1,280,282,288,290,296,298; the11 lake candidates are1,161,
176,177,178,184,186,192,194,203,204. This static flattened daytime comparison is
not night/animation/sprite-layer acceptance. Approximate Averon-style substitutions
remain a possible deliberate graphical adaptation, not an equivalence claim.

Recommended bounded approach:
1. **Lakefront:** keep the Route201-facing seamless corridor in existing Averon
   General-compatible art/IDs/palettes. Reuse Claude's current Route202 remapping
   approach for ordinary pine/tree/ground substitutions; validate EVERY used
   record here, including ledges and arrow warp. It needs an explicit custom
   record for NORTH_ARROW_WARP: current General+Dewford has NO behavior0x64
   record in either bank. A pure remap to existing records cannot preserve it.
   An isolated secondary clone/extension (using cleared existing graphics and
   a new local record) is a narrow option for Claude, not a new saved identity.
   Keep any changed bank meaning outside streamed seam strips or verify those
   strips exactly compatible in both directions. No bank slot is allocated here.
2. **LakeVerity:** the existing isolated General/Petalburg paired family is the
   lowest-remap, source-faithful option, because entry/exit uses a full map warp,
   not a seamless connected edge. It preserves all52 source records/attributes,
   original water and secondary geometry with no manual reconstruction. Rights/
   attribution of the actual donor assets must still be documented before
   publishing them. If Claude instead chooses Averon-style art for continuity,
   every unmatched record needs explicit graphics AND behavior/layer verification;
   no automatic verified mapping is supplied by this preflight.

**Why not isolate both maps unchanged?** `fieldmap.c:FillConnection` CpuCopy16s
neighbor raw metatile IDs into the active buffer; `field_camera.c:DrawMetatileAt`
uses the active layout's primary/secondary records. It performs no donor/Averon
translation. An isolated Lakefront primary therefore renders copied Route201
strips through the wrong graphics, and vice versa. Use compatible seam bands or
an independently approved transition design; do not add speculative engine
translation/refactoring or silently replace the intended connection with a warp.

### Water, animations and semantics

All actually used graphics avoid the General animation write ranges432–461,
464–473,480–489,496–501,508–511. Tiles475–477 occur but are **not** in those ranges.
Lake water uses static tile286 with bank-specific shoreline pieces; **1070 cells
are MB_POND_WATER**, including metatile511 with SPLIT layer2. Pond water is
surfable/encounter-capable in existing `metatile_behavior.c`, not diveable; there
are no used waterfall/deep-water/current behaviors. Do not turn pond cells into
ordinary walkable floor, add encounters or grant Surf/progression. Check natural
Surf refusal/allowed use and shore exits under existing rules in graphical QA.

Thus callbacks are not required by the measured used tile set. The existing
paired stager conservatively supplies26 verified General frames and namespaced
callback; that is usable integration input but NOT evidence those maps contain
animated water. A NULL primary callback is technically sufficient for these
measured references if Claude selects the static family; check all final adapted
records again. Petalburg callback has no animation transfers. Do not reuse
General's existing callback blindly with different assets.

Lakefront ledges:133/254 jump-west,135/213/214 jump-south,141 jump-southwest.
Preserve their behavior and original collision/elevation bits when remapping.
LakeVerity167 is MB_NON_ANIMATED_DOOR at **(23,19)**, collision0/elevation0, with
**no warp event**. Eight mountain-top cells around21..25,16..17 are collision1.
Do not create an unapproved cavern/interior to satisfy the door; close the unused
physical entrance or supply a separately authorized destination. This is a real
source integration hazard, not a demonstrated current Averon gameplay defect.

### Navigation / seam specifics for Claude

Lakefront0:(2,4) -> lake0:(38,43); Lakefront1:(3,4) -> lake1:(39,43), with exact
reciprocal indices. Headers use elevation0; actual warp cells are collision0,
elevation0. Lakefront574 is NORTH_ARROW_WARP; lake626 SOUTH_ARROW_WARP. Preserve
stepping direction and test exiting either member of each pair without immediate
bounce. Current Dewford has south-arrow record852 (not a verified pixel substitute),
while neither current General nor Dewford has a north-arrow record.

Route201 west currently has no connection. Lakefront right has donor offset0.
At zero offset, both edges are open/elevation3 at rows10,13,14; Route201-only open
rows8,9,11 and Lakefront-only open rows6,7,12,15 do NOT line up. Numeric offset0 is
not a completed seam. Claude must align/close/widen physical boundaries with
reciprocal inverse offsets and check both directions; no final offset is chosen
here. Engine streams7 neighbor columns west /8 east: review those full strips,
not just the outermost walkable tile. Both metadata and graphical palette/tree
continuity require testing. The lake itself has no edge connection.

Drop all donor story objects/coord triggers/items/hidden flags, sign scripts and
encounters. Preserve only neutral physical navigation under Claude's scope.
Both maps share owner-approved section220; no221/new saved format is needed.

## Narrow tooling repair and actual tests

Existing bank audit had two restrictions: CLI only allowed Route202, and the
library guessed `LAYOUT_`+uppercase map name. After admitting Verity, real source
reproduced **ValueError: missing donor layout**, because actual names contain
underscores. Reuse the already validated donor header/layout/block reader from
176 instead of adding another converter; retain Route202 default behavior.
Support only the two requested maps plus Route202. Optional
`--target-secondary dewford` compares the real neighboring destination; default
Petalburg unchanged. Add per-used-record structural evidence and cell counts.
LakeVerity also reproduced a second real failure in pilot inspect:
`TypeError: object of type NoneType has no len()` for its explicit
`connections:null`. Count that as zero, matching absent/empty connections; one
focused regression proves it. Conversion/staging behavior unchanged.
No CI/workflow/guard changes.

**PASS54/54 local tests**:7 focused bank-audit tests +16 pilot (15 retained +1 null-connections regression) +19 static
family +12 paired-family tests,0 failures/skips. The7 cover all3 maps with
non-guessed header layout IDs, both Verity CLI invocations, Dewford comparison,
missing target/source entries, malformed banks and invalid paths/families.
These are host/temporary fixtures, not native GBA/mGBA/ROM acceptance.

Reproduce for EACH `VerityLakefront` and `LakeVerity` with pinned donor checkout:
```
python3 "Pokemon Game/scripts/sinnoh-donor-map-pilot.py" inspect --donor-root DONOR --map MAP --donor-revision 38228bb574a3557345852b758d5f1a65eb01bb22
python3 "Pokemon Game/scripts/sinnoh-donor-bank-audit.py" --donor-root DONOR --engine-root "Pokemon Game/engine" --map MAP --target-secondary dewford
python3 "Pokemon Game/scripts/sinnoh-dual-bank-family.py" --donor-root DONOR --engine-root "Pokemon Game/engine" --revision 38228bb574a3557345852b758d5f1a65eb01bb22 --map MAP --output NEW_SCRATCH
python3 -m unittest discover -s "Pokemon Game/scripts/tests" -p test_sinnoh_donor_bank_audit.py -v
```

DONE: exact source objects, used-ID evidence, successful staging, safe mixed
strategy and navigation hazards identified. PUSHED: see PR head/handoff for exact
source SHA. BLOCKED: production integration remains Claude's protected lane;
actual asset permissions, seam adaptation and genuine paired-ROM/mGBA acceptance
are not supplied by a host preflight. NEXT: Claude chooses the explicit Lakefront
seam-compatible remap/secondary definition, isolates the lake bank if desired,
closes the orphan door, integrates neutral reciprocal warps, then tests the actual
connected source after normal exact-path authorization. No waiting on this
preflight or old Codex infrastructure is necessary.
