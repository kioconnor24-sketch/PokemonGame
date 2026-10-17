"""Test fixture (disclosed): flip one SaveBlock1 data byte in the newest flash
slot of a COPY, so its sector checksum fails. Prints what was changed."""
import struct, sys, hashlib
src, dst = sys.argv[1], sys.argv[2]
d = bytearray(open(src, "rb").read())
def counter(slot):
    return struct.unpack_from("<I", d, slot * 14 * 4096 + 0xFFC)[0]
newest = 0 if counter(0) > counter(1) else 1
for i in range(14):
    off = (newest * 14 + i) * 4096
    if struct.unpack_from("<H", d, off + 0xFF4)[0] == 1:  # SECTOR_ID_SAVEBLOCK1_START
        d[off + 0x100] ^= 0xFF
        print(f"slot {newest} (counter {counter(newest)}) sector {i} id 1 byte 0x100 flipped; "
              f"older slot counter {counter(1 - newest)}")
        break
open(dst, "wb").write(d)
print("before", hashlib.sha256(open(src, "rb").read()).hexdigest()[:12], "after", hashlib.sha256(d).hexdigest()[:12])
