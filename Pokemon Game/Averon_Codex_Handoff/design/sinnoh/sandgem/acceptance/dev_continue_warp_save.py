"""DEV-ONLY QA FIXTURE (disclosed in every evidence README): copy a real save and
set the engine's own continue-game warp so CONTINUE warps the player to a map.

It sets SaveBlock2.specialSaveWarpFlags |= CONTINUE_GAME_WARP (offset 0x09) and
SaveBlock1.continueGameWarp (offset 0x0C) in the newest valid slot, then fixes
both sector checksums. CB2_ContinueSavedGame then calls WarpIntoMap through
the normal map-load path. No ROM or source change.

usage: dev_continue_warp_save.py ENGINE IN.sav OUT.sav GROUP NUM X Y
"""
import struct, sys
from pathlib import Path

engine, src, dst = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
group, num, x, y = (int(v) for v in sys.argv[4:8])
sys.path.insert(0, str(engine.parent / 'scripts/coordination'))
import codex_cry_gameplay as w  # flash layout helpers already used for save evidence

sizes = w.chunk_sizes(*w.save_struct_sizes(engine, Path('/tmp/claude-0/-root-averon/0199c508-a967-4d20-a027-90b38c139b0e/scratchpad/devfix-sizes'), 'off', release=False))
data = bytearray(src.read_bytes())
slots = w.flash_slots(bytes(data), sizes)
newest = max((i for i, s in enumerate(slots) if s['status'] == 'valid'), key=lambda i: slots[i]['counter'])
base = newest * w.SECTORS_PER_SLOT * w.SECTOR_SIZE
patched = set()
for n in range(w.SECTORS_PER_SLOT):
    off = base + n * w.SECTOR_SIZE
    sid, _, sig, counter = struct.unpack_from('<HHII', data, off + 0xFF4)
    if sid == 0:      # SaveBlock2 first chunk
        data[off + 0x09] |= 1
    elif sid == 1:    # SaveBlock1 first chunk
        struct.pack_into('<bbbBhh', data, off + 0x0C, group, num, -1, 0, x, y)
    else:
        continue
    struct.pack_into('<H', data, off + 0xFF6, w.sector_checksum(bytes(data[off:off + w.SECTOR_DATA_SIZE]), sizes[sid]))
    patched.add(sid)
assert patched == {0, 1}, patched
assert w.flash_slots(bytes(data), sizes)[newest]['status'] == 'valid'
dst.write_bytes(bytes(data))
print(f'DEV fixture: slot {newest} counter {slots[newest]["counter"]}: continue-warp to group {group} num {num} ({x},{y})')
