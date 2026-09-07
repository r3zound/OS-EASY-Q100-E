#!/usr/bin/env python3
"""详细 dump PMCP 区域 0x23000 - 0x24000 (找 PMCC000 实际内容)"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()

print("=== PMCP 区域 0x23000 - 0x24000 ===")
for i in range(0x23000, 0x24000, 16):
    hex_str = " ".join(f"{b:02x}" for b in data[i:i + 16])
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in data[i:i + 16])
    print(f"  0x{i:08x}: {hex_str}  {asc}")

print()
print("=== PMCC000 (0x23030) 区域 ===")
# 0x23030 是 PMCC000 name
# 0x23030 + 0x10 = 0x23040 是 offset field
# 0x23030 + 0x14 = 0x23044 是 size field
entry_off = 0x23030
print(f"  Name: {data[entry_off:entry_off+12]}")
e_offset = struct.unpack("<I", data[entry_off + 0x10:entry_off + 0x14])[0]
e_size = struct.unpack("<I", data[entry_off + 0x14:entry_off + 0x18])[0]
print(f"  Offset: 0x{e_offset:x}, Size: 0x{e_size:x}")
# 内容起点 = 0x23000 + 0x20 (CPD header) + e_offset
# 0x23000 + 0x20 + e_offset (但 e_offset 是不是相对 0x23020?)
content_start = 0x23000 + 0x20 + e_offset
print(f"  Content start: 0x{content_start:x}")
print(f"\n  Dump 0x{content_start:x} - 0x{content_start + 0x200:x} (前 512 字节):")
for i in range(content_start, min(content_start + 0x200, len(data)), 16):
    hex_str = " ".join(f"{b:02x}" for b in data[i:i + 16])
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in data[i:i + 16])
    print(f"  0x{i:08x}: {hex_str}  {asc}")
