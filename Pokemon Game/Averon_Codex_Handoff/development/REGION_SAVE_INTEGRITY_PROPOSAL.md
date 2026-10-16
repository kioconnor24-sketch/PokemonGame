# Region save integrity proposal — review required

Status: **NOT ALLOCATED / NOT IMPLEMENTED / NOT REGISTERED**. This document
answers Issue15 comment6208645826. It does not approve identifiers, SaveBlock3
fields, save hooks, new flags or gameplay integration. The existing region
queries remain unregistered prototypes; their earlier87/87 native result is
not evidence for this proposed format.

## Executed evidence and exact current layout

Source checkpoint: `b4e85252b76b5674abcb6ae1289c5ef50140af74`, including
the approved PR50 guards. Run:

```sh
python3 scripts/test-averon-save-extra-integrity.py --engine /path/to/generated/engine
```

This read-only diagnostic compiles real headers using ARM APCS ABI, then runs
the extracted `CalculateChecksum` under host ASan/UBSan. Source hashes are in
its output. Current measured bytes:

| Object/member | Size or byte offset |
| --- | --- |
| SaveBlock1 / SaveBlock2 / SaveBlock3 / storage |15568 /3884 /4 /34144 |
| SaveBlock3.dexNavChain |0 |
| SaveBlock2.filler_90 (candidate, **not reserved**) |0x90,8 bytes |
| SaveSector.data |0..3967 (0x000..0xF7F) |
| SaveSector.saveBlock3Chunk |3968..4083 (0xF80..0xFF3),116 bytes |
| sector ID / checksum / signature / counter |4084 /4086 /4088 /4092 |
| sector / slots |4096 bytes;14 sectors per slot;2 slots |

Current SaveBlock3 is4 bytes under the actual ABI, despite its one enabled
u8 field. Preserve the entire existing4-byte prefix, including ABI padding;
do not allocate that padding. Total extra capacity is14*116=1624 bytes,
currently1620 beyond the existing prefix. Neither free space nor a member
named filler grants ownership.

Actual `save.c` writer clears the whole sector, copies primary data and
SaveBlock3 separately, and calculates the footer checksum over primary
`data,size` only. Both validators and the copy path use that same primary
range; `CopyToSaveBlock3` then copies extra bytes without an integrity check.
Executed fault proof: **62816/62816 primary single-bit flips detected** across
lengths3884 and3968; **1856/1856 extra-chunk single-bit flips undetected**
(116*8 per primary length). This diagnoses the existing checksum boundary;
it is not a native flash corruption test or a claim all checksum faults are
detected. The diagnostic intentionally fails if these assumptions change.

## Recommended design for review

Use a primary-checksummed migration anchor **and** a versioned CRC-protected
extension. An SB3-only magic/version is insufficient: clearing its header
could make a damaged new save look like an old save. Do not silently initialize
Sinnoh progress whenever an extension fails validation.

Candidate anchor: existing SaveBlock2.filler_90 bytes0x90..0x97. A targeted
source search finds its declaration and no named consumers; new-game
`ClearSav2` zeroes SaveBlock2. These are necessary observations, not proof
every historical/imported save has zero there. Approval requires explicit
ownership and provenance checks. Proposed8-byte anchor has a reviewed4-byte
tag,2-byte format and2-byte format complement. **No tag/version value is
assigned here.** Reusing these existing checksummed bytes would leave
SaveBlock2's size/checksum length unchanged. If the owner rejects this range,
stop format integration and review another protected anchor; do not silently
append fields or use unchecksummed tail space instead.

Candidate extension:64 serialized little-endian bytes, starting at SB3 offset4
(prospective SB3 size68). It fits wholly in logical sector0's extra chunk:
sector-relative0xF84..0xFC3 inclusive.48 bytes remain before the sector footer.
This placement makes the anchor, full record and footer part of the same
physical sector write. Sector rotation means logical0 is **not always
physical0**; locate it by validated ID and the existing slot/rotation rules.

| Record-relative bytes | Proposed meaning (all subject to review) |
| --- | --- |
|0..3 | reviewed record tag, unassigned |
|4..5 /6..7 | format / length64 |
|8..11 | exact save-slot counter, bound to the containing sector footer |
|12..15 | CRC-32/ISO-HDLC over bytes0..11 and16..63 |
|16 /17 /18 /19 | logical active region / Averon badge mirror / Sinnoh badges / reserved zero |
|20..27 /28..35 | Averon / Sinnoh return target |
|36..37 /38..39 | Averon / Sinnoh existing heal identifier,0 meaning unset |
|40..43 | existing playerTrainerId bytes, bound to the candidate SaveBlock2 |
|44..63 | reserved zero; no implicit Fly flag or identifier allocation |

Each return target uses explicit u8 group,u8 number, then signed16 warp,x,y;
no raw C struct memcpy or host padding. No numeric region encoding is
allocated; adapters must reconcile actual engine enums with the private
fixture enum. Translate through full-width validation before any signed-byte
engine warp call. Unset targets need an explicitly reviewed representation.
No new map, heal ID, destination, visited bank or level curve is implied.

Existing Averon badges remain canonical in the existing saved badge flags;
the proposed mirror must equal those flags at save/load. Sinnoh must never
inherit that bank. Changes to either flag hooks or badge consumers require a
separate handoff. Cap and obedience values remain caller policies, not saved
numbers chosen by this format.

## Load, migrate, save and rollback contract

1. Validate sector signatures, IDs, checksums, complete unique sector set and
   coherent counter for each slot using bounded reads. Then inspect anchor
   and record in **that same candidate slot**, before publishing RAM state or
   accepting it as newest. Retain the save-sector bounds fix.
2. All-zero anchor permits legacy classification only for supported proven
   old-writer provenance. Ignore old extra tail bytes; derive Averon badges
   from canonical flags, initialize Sinnoh badges to0, and validate existing
   map/heal identity. Migration initially exists only in a temporary RAM
   snapshot; do not write flash while loading or grant travel/licenses.
3. Matching anchor/tag/version requires exact record length, CRC, counter,
   reserved bytes, trainer-ID binding, badge mirror, active-region and map/heal semantics. Missing,
   torn or zeroed record with a new-format anchor is **corrupt**, never legacy.
   A malformed nonzero anchor is corrupt. A recognizable newer format is
   **unsupported**, not permission to initialize or overwrite it.
4. If newest is corrupt, select a coherent older **whole** slot. Never splice
   old region progress into newer party/items/badges. If no valid slot exists,
   return explicit failure and preserve diagnostic flash; do not auto-save
   defaults. Unknown-format handling must prevent an older client from
   silently overwriting newer progress; exact UI/error behavior needs review.
5. Normal save stages canonical state, anchor, serialized record, upcoming
   slot counter and CRC together. Use current alternating-slot writes. Only
   report success after all required writes succeed; preserve last complete
   slot if interrupted. A later clean save after legacy migration creates
   the new anchor/record atomically within the normal slot transaction.

Existing primary16-bit additive checksums and proposed CRC detect accidental
corruption; they are not authentication. Zero anchor plus arbitrary old tail
cannot unconditionally identify every historical save. Historical fixtures,
the supported old-writer boundary, collision policy, unknown-version handling
and downgrade behavior must be approved before implementation. Downgraded
old binaries do not understand the anchor/CRC and must not be advertised as
safe writers for new-format progress.

## Required fault-injection and compatibility acceptance

Implement these only after the format/range and protected paths are approved:

- Historical old-source flash fixtures: empty,new game,8+0 badges, partially
  earned Averon badges, legal healer/return and arbitrary old tail. Load keeps
  party/PC, decrypted Bag/money, quests/licenses and existing maps byte-exact;
  zero Sinnoh badges; no flash writes until a successful ordinary save.
- Real native flash: every bit in the64-byte extension and8-byte anchor;
  erased/zeroed header or record, truncation, wrong CRC/version/length,
  illegal reserved bits, unknown region, wrong badge mirror, invalid full-width
  map/warp/heal IDs and unvisited/cross-region Fly requests. Require bounded
  rejection and unchanged outputs, including marker-correct/record-zero.
- Copy a valid record from the other slot/player or a different counter;
  recompute CRC for semantic-invalid records so validation is not merely a
  CRC test. Check the recorded existing trainer ID against the same candidate
  SaveBlock2, including a CRC-valid record from a different player at the same
  counter. No new player identifier is allocated.
- Interrupt before/after **each of14 sector writes**, both slot directions,
  each observed logical0 rotation. Verify chosen entire snapshot and saved
  party/Bag/money/badges/healer, then subsequent clean save and reload.
- Corrupt newest-only, older-only,both slots; duplicate/missing IDs,
  out-of-range IDs14/65535, counter mismatch/wrap and unsupported newer
  version. Never interpret damaged new progress as legacy or mix snapshots.
- Repeat Averon↔Sinnoh bank changes/save/load with synthetic identities and
  existing untouched maps; verify cap/obedience/field/Fly/heal/whiteout and
  legacy badge independence through approved adapters. No new map is needed.
- Native negatives must kill removed CRC/anchor/counter/region/mirror guards,
  oldest/newest selection reversal and per-sector snapshot mixing. Maintain
  native save-layout assertions (unchanged SB1/SB2/storage; approved SB3 only),
  full Averon suite, normal GBA build and resource report. Graphical QA and
  Delta are separate gates.

## Approval boundary and next executable task

Needed: explicit review of anchor ownership/provenance,64-byte record schema
and region encoding, error/downgrade policy, and exact protected integration
handoff (`global.h`, staged save candidate validation/write paths, appropriate
load/new-game and region adapters). This is a request for review, not a claim.

Prospective storage/RAM impact: SB3+64 bytes, sector format remains4096 bytes,
SB1/SB2/storage sizes unchanged; decoder staging/ROM/stack still to measure.
No fields/IDs/hooks have changed. The only executable addition is the
read-only diagnostic. Next unblocked code: strengthen existing pure regional
field/heal/warp validation or native tests; revisit persistence only after the
specific approval, not after unrelated PR completion.
