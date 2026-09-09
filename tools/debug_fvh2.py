import struct
data = open(r'third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin', 'rb').read()

print('=== 所有 _FVH 位置及 _FVH + 8 (UINT32 LE) ===')
pos = 0
while True:
    pos = data.find(b'_FVH', pos)
    if pos < 0: break
    if pos + 16 <= len(data):
        v32 = struct.unpack('<I', data[pos+8:pos+12])[0]
        v64 = struct.unpack('<Q', data[pos+8:pos+16])[0]
        valid32 = 1024 < v32 < len(data)
        valid64 = 1024 < v64 < len(data)
        size_32_kb = v32 / 1024
        size_64_mb = v64 / 1024 / 1024
        print(f'  0x{pos:08x}: u32=0x{v32:x} ({v32:,} bytes, {size_32_kb:.0f} KB) {valid32}, u64=0x{v64:x} ({v64:,}) {valid64}')
    pos += 4
