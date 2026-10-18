"""Scratch debugging only: compare EWRAM between two savestates around gHeap
and report which ranges became zero, plus the old block headers' new bytes."""
import sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from ssread import state, read

before, after = state(sys.argv[1]), state(sys.argv[2])
base, size = 0x02001918, 0x1C500
a = read(before, base, size)
b = read(after, base, size)
runs, start = [], None
for i in range(size):
    became_zero = b[i] == 0 and a[i] != 0
    if became_zero and start is None:
        start = i
    elif not became_zero and start is not None:
        runs.append((start, i)); start = None
if start is not None:
    runs.append((start, size))
# merge runs separated by bytes that were already zero
merged = []
for s, e in runs:
    if merged and all(b[k] == 0 for k in range(merged[-1][1], s)):
        merged[-1] = (merged[-1][0], e)
    else:
        merged.append((s, e))
print('ranges that became zero (merged across already-zero bytes):')
for s, e in merged[:40]:
    print(f'  {base + s:08X}..{base + e:08X}  ({e - s} B)')
lead = next((i for i in range(size) if b[i] != 0), size)
print(f'first nonzero byte after gHeap start: +{lead:#x} ({base + lead:08X})')
for addr in (0x02001918, 0x02002128, 0x02002938, 0x02003148, 0x02003958, 0x020046E8):
    print(f'  header {addr:08X}: before={read(before, addr, 16).hex()} after={read(after, addr, 16).hex()}')
