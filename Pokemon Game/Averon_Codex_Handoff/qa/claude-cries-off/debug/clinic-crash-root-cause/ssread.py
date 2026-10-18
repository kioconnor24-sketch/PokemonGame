"""Scratch debugging only: read memory out of an mGBA 0.10 PNG savestate.
The state lives zlib-compressed in the private 'gbAs' chunk; EWRAM starts at
offset 0x21000 and IWRAM at 0x19000 of the serialized state."""
import struct, sys, zlib

def state(path):
    data = open(path, 'rb').read()
    pos = 8
    while pos < len(data):
        n, kind = struct.unpack_from('>I4s', data, pos)
        if kind == b'gbAs':
            return zlib.decompress(data[pos + 8:pos + 8 + n])
        pos += 12 + n
    raise SystemExit(f'{path}: no gbAs chunk')

def read(st, addr, n):
    if 0x02000000 <= addr < 0x02040000:
        off = 0x21000 + addr - 0x02000000
    elif 0x03000000 <= addr < 0x03008000:
        off = 0x19000 + addr - 0x03000000
    else:
        raise ValueError(hex(addr))
    return st[off:off + n]

def u32(st, addr):
    return struct.unpack('<I', read(st, addr, 4))[0]

if __name__ == '__main__':
    for path in sys.argv[1:]:
        st = state(path)
        head = u32(st, 0x02000020)
        print(f'{path}: len={len(st):#x} gFonts={u32(st, 0x02000010):08X} sMenu={read(st, 0x02000014, 12).hex()} sFirstTextPrinter={head:08X}')
        node, seen = head, 0
        while node and seen < 12:
            if not (0x02000000 <= node < 0x02040000):
                print(f'   -> {node:08X} (outside EWRAM)'); break
            raw = read(st, node, 48)
            print(f'   node {node:08X}: {raw.hex()}  next={struct.unpack_from("<I", raw, 44)[0]:08X}')
            node = struct.unpack_from('<I', raw, 44)[0]; seen += 1
