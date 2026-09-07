#!/usr/bin/env python3
"""完整 dump FPT 区域，正确解析 entries"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()

FPT_SIG = b"$FPT"
fpt_offset = data.find(FPT_SIG)
print(f"$FPT 在 0x{fpt_offset:08x}\n")

# Dump 整个 0x400 字节
print("=== FPT 区域 0x400 字节 ===")
for i in range(0, 0x400, 16):
    hex_str = " ".join(f"{b:02x}" for b in data[fpt_offset + i:fpt_offset + i + 16])
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in data[fpt_offset + i:fpt_offset + i + 16])
    print(f"  0x{fpt_offset + i:08x} (FPT+0x{i:03x}): {hex_str}  {asc}")
