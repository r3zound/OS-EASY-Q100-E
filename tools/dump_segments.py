#!/usr/bin/env python3
"""手动检查 BIOS 早期区段 + ME 区域 + microcode 可能位置"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()


def hex_dump(off, length=256):
    print(f"=== 0x{off:08x} - 0x{off + length:08x} ({length} bytes) ===")
    for i in range(off, min(off + length, len(data)), 16):
        hex_str = " ".join(f"{b:02x}" for b in data[i:i + 16])
        asc = "".join(chr(b) if 32 <= b < 127 else "." for b in data[i:i + 16])
        print(f"  0x{i:08x}: {hex_str}  {asc}")
    print()


# 看几个关键区段开头
hex_dump(0x100, 256)        # FD 详细
hex_dump(0x23000, 256)      # 第一个数据使用段（92 KB）
hex_dump(0x63000, 256)      # BIOS region 主体
hex_dump(0x1a9000, 256)     # $FPT 起点
hex_dump(0x1f9000, 256)     # "No Microcode" 字符串附近
