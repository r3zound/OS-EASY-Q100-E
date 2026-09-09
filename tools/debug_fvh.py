import sys
sys.path.insert(0, 'tools')
from inject_microcode_v2 import find_ffh_volumes
data = open(r'third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin', 'rb').read()
vols = find_ffh_volumes(data)
print(f'找到 {len(vols)} 个 FFS 卷')
for v in vols[:30]:
    print(f'  0x{v["offset"]:08x} vol_length=0x{v["vol_length"]:x} ({v["vol_length"]:,}) header_len={v["header_length"]}')

# 第一个 _FVH 位置 0x1000028 的字节
import struct
pos = 0x1000028
print(f'\n头 32 字节 @ 0x{pos:08x}:')
print(' '.join(f'{b:02x}' for b in data[pos:pos+32]))
# 各种尝试
for off_in_fvh, label, fmt in [
    (4, "header_len (LE u16)", "<H"),
    (6, "???", None),
    (8, "vol_length LE u32 (FFSv2)", "<I"),
    (8, "vol_length LE u64 (FFSv3)", "<Q"),
    (12, "???", None),
    (16, "???", None),
]:
    raw = data[pos+off_in_fvh:pos+off_in_fvh+8]
    print(f'  +{off_in_fvh:2d} {label}: raw={" ".join(f"{b:02x}" for b in raw)}')
    if fmt:
        v32 = struct.unpack(fmt[:2], raw[:4])[0]
        print(f'    {fmt} = 0x{v32:x} = {v32:,}')
        if len(fmt) > 2 and 'Q' in fmt:
            v64 = struct.unpack(fmt, raw[:8])[0]
            print(f'    {fmt} = 0x{v64:x} = {v64:,}')
