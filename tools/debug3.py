import struct

data = open(r'third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin', 'rb').read()
target_off = 0x1D90D18

# 直接读 32 字节
hdr = data[target_off:target_off+32]
print(f"Raw 32 bytes @ 0x{target_off:08x}:")
print(f"  {' '.join(f'{b:02x}' for b in hdr)}")
type_v, rev, date, cpuid = struct.unpack("<IIII", hdr[:16])
print(f"  type={type_v}, rev=0x{rev:x}, date=0x{date:x}, cpuid=0x{cpuid:08x}")
print()

# 步进 0x10 扫整个 bin
print("0x10 step scan:")
pos = 0
count = 0
while pos + 0x20 < len(data):
    t = struct.unpack("<I", data[pos:pos+4])[0]
    r = struct.unpack("<I", data[pos+4:pos+8])[0]
    d = struct.unpack("<I", data[pos+8:pos+12])[0]
    c = struct.unpack("<I", data[pos+12:pos+16])[0]
    if t == 1 and 0 < r < 0x300 and c != 0:
        print(f"  0x{pos:08x}: type={t} rev=0x{r:x} date=0x{d:x} cpuid=0x{c:08x}")
        count += 1
    pos += 0x10
print(f"Total: {count}")

# 步进 0x800
print()
print("0x800 step scan (跳过 Q100-E 位置):")
pos = 0
count = 0
while pos + 0x20 < len(data):
    t = struct.unpack("<I", data[pos:pos+4])[0]
    r = struct.unpack("<I", data[pos+4:pos+8])[0]
    d = struct.unpack("<I", data[pos+8:pos+12])[0]
    c = struct.unpack("<I", data[pos+12:pos+16])[0]
    if t == 1 and 0 < r < 0x300 and c != 0:
        print(f"  0x{pos:08x}: type={t} rev=0x{r:x} date=0x{d:x} cpuid=0x{c:08x}")
        count += 1
    pos += 0x800
print(f"Total: {count}")
