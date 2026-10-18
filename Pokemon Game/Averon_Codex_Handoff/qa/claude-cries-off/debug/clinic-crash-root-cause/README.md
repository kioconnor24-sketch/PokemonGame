# RELEASE clinic-heal crash: root cause (Claude, 2026-10-17)

**Build:** unchanged `main` RELEASE. It was built at `447b67c8` (ROM `c918e880…`) with symbols from that ELF. The same crash happens on #117's RELEASE ON and OFF ROMs, so **cries are not involved**.

These are Claude's own emulator traces, not a third-party review. No savestates, saves, ROMs or ELFs are committed here, only scripts, logs and decoded values.

## Chain of events

1. **The nurse script calls the Union Room check.**
   - After `HealPlayerParty`, the shared nurse script (`data/scripts/pkmn_center_nurse.inc`) runs `specialvar VAR_RESULT, BufferUnionRoomPlayerName`.
   - Vanilla Pokémon Centers run `CableClub_OnResume` → `special InitUnionRoom` on entry, which sets `sUnionRoomPlayerName[0] = EOS`.
   - Averon's clinics never do, so the 12-byte `EWRAM_DATA` buffer is still zero-filled from boot.
2. **The name is copied without bound.**
   - `0x00` is not `EOS` (`0xFF`), so the function runs `StringCopy(gStringVar1, sUnionRoomPlayerName)`.
   - The copy stops only at the next `0xFF` byte in EWRAM.
3. **The copy wipes the heap.**
   - On RELEASE (LTO), `sUnionRoomPlayerName` is at `0x0203736C` with roughly 35 KB of zeros after it, while `gStringVar1` is at `0x0200154C`.
   - The copy therefore zero-fills `0x0200154C` onward, which includes every `gHeap` block header (heap starts at `0x02001918`).
   - `zerospan.txt` shows that all 6 headers are zeroed, and `0x02001918`–`0x020034D8` is entirely zero.
4. **The next allocation returns a bad pointer.**
   - The next `Alloc` is the text printer for "Thank you for waiting…" (`ScrCmd_message` → `AddTextPrinter` → `AllocateTextPrinter`).
   - It follows the zeroed head's `next = NULL` into BIOS space and returns `0 + sizeof(MemBlock) = 0x10`.
   - That value becomes `sFirstTextPrinter` (`watch-sFirstTextPrinter.json`: written `0 → 0x00000010` by `AddTextPrinter`).
5. **`RunTextPrinters` crashes.**
   - It reads the printer at `0x10`, so every field comes from BIOS open bus.
   - It calls `callback(printer, RENDER_UPDATE)` with an ARM BIOS opcode as the target, giving `Jumped to invalid address: E55EC002` (`onetrace-tail.log`).
   - That is why the bad target was a different "ARM instruction word" in each run.

## How it was found

Each step used new instrumentation; no failed approach was repeated.

| Step | Tool | Result |
| --- | --- | --- |
| Frame-step from the `HealPlayerParty` break | `cli_frames.py` | The crash is in the 8th frame; savestates are kept locally |
| One-frame instruction trace | `cli_onetrace.py` | The last 20,000 instructions end in `RunTextPrinters`, with printer `0x10` |
| Decode savestates offline | `ssread.py`, `heapwalk.py` | At the counter the heap is valid (6 blocks, magic `A3A3`). Six frames after the heal, the head header is all zero and `sFirstTextPrinter = 0x10` |
| Write watchpoint `0x02000020` | `cli_watch.py` | Bad value stored by `AddTextPrinter` (normal pointers come from the same instruction) |
| Write watchpoint on heap-head magic `0x0200191A` | `cli_watch_first.py` | First write is the byte loop in `BufferUnionRoomPlayerName` (`0x0826BC02`): dst `0x0200191A`, src `0x0203773B`, called from `ScrCmd_specialvar` |

## Why only RELEASE crashed

- The copy is unbounded on every build profile. It happens once per power-on, at the first heal in a center that did not run `InitUnionRoom`. After that, the function stores `EOS` in the buffer.
- On normal builds a `0xFF` byte presumably comes sooner after the array. That is inferred from the different EWRAM layout and from run05 healing 5 times without a crash; I did not measure the normal-build copy length.
- The bug is still present on normal builds. Read from the source but not seen in a screenshot: the function returns TRUE, so unless `FLAG_NURSE_UNION_ROOM_REMINDER` is already set, the first heal takes the nurse's "player waiting in the Union Room" path, using `gStringVar1` as the name.

## Ruled out earlier

These were all consistent with the cause above:
- Entering the clinic and debugger traffic: the crash needs the heal script.
- The fanfare end.
- `sio32intr_clock_master` words: that was coincidence, since the value was a BIOS opcode.
- IWRAM stack overflow: the corruption is in EWRAM.

## Fix

Branch `claude/clinic-union-room-overflow`: `sUnionRoomPlayerName` is now `EWRAM_INIT … = {EOS}`, so it is an empty string from boot. It adds the native regression test `test/averon_clinic_union_room.c`. Maps are frozen and need no change, and vanilla centers behave exactly as before because `InitUnionRoom` still resets the buffer.
