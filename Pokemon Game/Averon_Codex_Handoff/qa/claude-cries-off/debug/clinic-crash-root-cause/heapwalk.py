"""Scratch debugging only: walk the malloc.c block list in an mGBA savestate
(MemBlock: u16 allocated:1/unused:4/locationHi:11, u16 magic 0xA3A3,
u32 size:18/locationLo:14, prev, next; 16-byte header)."""
import struct, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from ssread import state, read, u32

HEAP_START_VAR = 0x030008AC
EWRAM = range(0x02000000, 0x02040000)


def walk(st, limit=400):
    head = u32(st, HEAP_START_VAR)
    pos, prev_seen, out, problems = head, None, [], []
    for _ in range(limit):
        if pos not in EWRAM:
            problems.append(f'block pointer {pos:08X} outside EWRAM (reached from {prev_seen:08X})')
            break
        w0, magic, w1, prev, nxt = struct.unpack('<HHIII', read(st, pos, 16))
        blk = dict(addr=pos, alloc=w0 & 1, size=w1 & 0x3FFFF, magic=magic, prev=prev, next=nxt)
        out.append(blk)
        if magic != 0xA3A3:
            problems.append(f'{pos:08X}: magic {magic:04X}')
        if prev_seen is not None and pos != head and prev != prev_seen:
            problems.append(f'{pos:08X}: prev {prev:08X} but reached from {prev_seen:08X}')
        if nxt != head and nxt in EWRAM and nxt != pos + 16 + blk['size']:
            problems.append(f'{pos:08X}: next {nxt:08X} != addr+16+size {pos + 16 + blk["size"]:08X}')
        prev_seen, pos = pos, nxt
        if pos == head:
            break
    return head, out, problems


if __name__ == '__main__':
    for path in sys.argv[1:]:
        st = state(path)
        head, blocks, problems = walk(st)
        used = sum(b['size'] for b in blocks if b['alloc'])
        print(f'== {path}: head={head:08X} blocks={len(blocks)} allocated={used} B')
        for b in blocks:
            print(f"  {b['addr']:08X} {'A' if b['alloc'] else '-'} size={b['size']:6d} "
                  f"magic={b['magic']:04X} prev={b['prev']:08X} next={b['next']:08X}")
        for p in problems:
            print('  PROBLEM', p)
