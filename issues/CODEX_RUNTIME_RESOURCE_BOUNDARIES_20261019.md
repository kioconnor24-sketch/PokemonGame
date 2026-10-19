# Native resource boundaries and sampled menu resources

Codex, 2026-10-19, roadmap X03. Base main `0375f91cbb5353f72396bb873a6cc2de1c5b3c34`, production engine tree inherited from reviewed #154. Only `engine/test/averon_runtime_resources.c` and this evidence are new. No production allocator, menus, maps, artwork, save structures, IDs or workflows change. Cries remain OFF by default.

## Executable coverage

Five new native identities, **28 parameter combinations** on this source:

| Native identity | Actual contract exercised |
| --- | --- |
| `Averon resource heap fragmented capacity refuses oversized requests and coalesces after free` | Fill the real heap's tail, retain two separated8192B holes; a12288B unchecked allocation correctly returnsNULL despite16384B total free. Live allocations retain sentinel bytes. Free the intervening block, allocate/write12288B successfully, and restore the complete original block/free/allocation inventory. |
| `Averon resource linked field tilesets decompress within paired buffers and release heap` | All16 linked Averon and2 linked Sinnoh maps; four repetitions per map, both compressed tilesets held concurrently. Real linked codec outputs stay inside16B prefix/suffix guards and declared tile capacity; all allocations return after each repetition and both freeing orders. **144 actual decodes**, no raw/uncompressed sides skipped in this source. |
| `Averon resource sprite slot exhaustion preserves live sprites and permits exact slot reuse` | Fill all64 engine sprite slots using the existing dummy template; slot65 returns64 without altering live sprites; free/reuse slot32 and verify refusal again. No heap change. This is not128 hardware OAM entries or64 permitted field NPCs. |
| `Averon resource reserved sprite palette banks survive exhaustion and free tag reuse` | Reserved counts0/1/8/16 leave16/15/8/0 allocatable banks. Exhaustion returns255 without overwriting tags or reserved slots; one freed tag is reusable and full cleanup restores16 free banks. |
| `Averon resource real party and Field Kit menus restore heap across repeated regional visits` | Real party/menu task/window/fade callbacks through the existing native harness, one/six Pokémon, Averon/Sinnoh, three open→Field Kit→back→cancel cycles each. Four cases,12 visits,648 sampled callback steps. Heap inventory restores at normal exit **before** harness cleanup, then again after cleanup. |

The cases use existing linked maps, test-only Pokémon and transient sprite tags; no permanent test maps or registrations. Future linked maps in those two groups join the decoder matrix automatically; recalculate the actual counts at each source revision. New raw tilesets are explicitly reported as not decoded, not falsely accepted as compressed coverage.

## Actual local measurements

GCC14.2.1 (20241119), GNU ld2.44, newlib4.5.0.20241231, MODERN native TEST build, `/workspace/.onboarding/mgba-rom-test`. Native file SHA256 `bbc30c59cdbe5708c77ad7045ce34489712649457bf8f160a2eda4d41e441918`. Focused patched headless ELF SHA256 `782c1a10561bc7b692b0410928ccc178f0a3f45fea9c223829910335162113b6` (filter is part of this artifact).

- Configured heap **115968B**; measured native baseline free/largest **115756B**, runner payload164B and three16B headers. This heap is already within allocated EWRAM; linker-free EWRAM must not be added to it.
- Guarded paired output payload ranges **20864–32544B**, including64B of output canaries and excluding allocator headers/temporary codec workspace. Sandgem exterior32544B, Center31424B. Each real decoder returns its temporary allocation before the next snapshot. These are observed held-output stages, **not full codec or field high-water measurements**.
- Sprite capacity64; palette bank capacity16. Actual negative calls and recovery pass, rather than inferring capacity from a header constant alone.

| Sampled real menu fixture | Max allocated heap payload | Minimum largest free block | Max live engine sprites | Max unavailable OBJ palette banks |
| --- | ---: | ---: | ---: | ---: |
| Averon, one Pokémon | 32000B | 81088B | 5 | 9 |
| Averon, six Pokémon | 32000B | 80448B | 25 | 9 |
| Sinnoh, one Pokémon | 32000B | 81088B | 5 | 9 |
| Sinnoh, six Pokémon | 32000B | 80448B | 25 | 9 |

Each row samples162 callback steps across three visits. Heap payload includes native runner allocations and excludes headers; palette unavailability includes reservations. Column extrema need not occur at the same step. Sampling occurs after callback returns and misses allocations freed inside a callback. Native map entry and menu callbacks are fixtures, **not a fully rendered overworld, ordinary story transport, graphical acceptance or release performance guarantee**. No field/battle/follower peak, frame-rate, stack or Delta claim is made.

## Verification and reproducibility

From `Pokemon Game/engine`, with the documented toolchain active:

```sh
make -j4 -O check 'TESTS=Averon resource' ROMTEST=/workspace/.onboarding/mgba-rom-test
make -j4 -O check 'TESTS=Averon' ROMTEST=/workspace/.onboarding/mgba-rom-test
```

Focused **5/5 PASS**, zero failures/skips,28 actual combinations. Full Averon result is recorded in the exact-head PR handoff; it must contain the preexisting288 identities plus these5. This is a focused project suite, not the complete unfiltered M1 baseline.

The unchanged source preflight also passed **47/47 host tests** after #161's namespace extension; its existing buffer/asset checks are reused rather than reimplemented. Initial diagnostic `%u` fields were blank because this native logger supports `%d`; corrected and reran. Native palette tags also require initialization before the first sample, because zero-initialized native state is not the field's TAG_NONE sentinel. Neither fixture correction is claimed as a production defect. The emulator emits an RTC command warning during the menu fixture; tests still complete, and no RTC gameplay conclusion is drawn.

Existing actual NORMAL/RELEASE production builds and save headroom at the unchanged production source are recorded in [#154 evidence](CODEX_SINNOH_RESUME_REGRESSION_20261019.md). No new local production rebuild is needed for added test-only code; applicable GitHub CI builds NORMAL and runs the complete Averon filter. Final-head CI results/ROM identity belong in the PR handoff. No ROMs, ELFs or private saves are committed.

Next: after #150/#151 actually integrate, compare source identity to the pushed combined proof, then rerun only affected native/resource cases. Full runtime field/battle/follower/stack measurements remain separate X03 work, with Claude's real graphical QA ownership preserved. This PR establishes testable allocation failures/recovery and sampled menu costs; it does not close the whole resource package.
