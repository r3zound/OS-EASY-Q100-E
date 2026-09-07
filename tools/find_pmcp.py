#!/usr/bin/env python3
"""直接搜 PMCP / MCD1 / MCD2 / $MCP / microcode 标识"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()

# 搜 microcode 相关的字符串
print("=== 搜 microcode 相关字符串 ===")
for kw in [b"PMCP", b"MCP", b"MCD1", b"MCD2", b"$MCP", b"microcode", b"uCode", b"ucode",
           b"_MICROCODE_", b"Microcode", b"fitc.cfg", b"pmcp", b"PMcc", b"Micr",
           b"fitc", b"FITC"]:
    pos = 0
    cnt = 0
    while True:
        pos = data.find(kw, pos)
        if pos < 0: break
        cnt += 1
        if cnt <= 5:
            ctx = data[max(0, pos - 8):pos + 40]
            printable = "".join(chr(b) if 32 <= b < 127 else "." for b in ctx)
            print(f"  0x{pos:08x}: {printable}")
        pos += 1
    if cnt > 5:
        print(f"  ... 共 {cnt} 个")
    elif cnt == 0:
        print(f"  [-] '{kw.decode('latin-1')}' 未找到")

# 解析所有 $CPD
print()
print("=== 解析所有 $CPD 找到的子目录 ===")
CPD_SIG = b"$CPD"
pos = 0
while True:
    pos = data.find(CPD_SIG, pos)
    if pos < 0: break
    print(f"\n  $CPD 在 0x{pos:08x}")
    cpd = data[pos:]
    num_entries = struct.unpack("<I", cpd[0x04:0x08])[0]
    print(f"    entries={num_entries}")
    for j in range(num_entries):
        ee_off = 0x20 + j * 0x20
        if ee_off + 0x20 > len(cpd): break
        e_name = cpd[ee_off:ee_off + 12].decode("latin-1", errors="replace").rstrip("\x00")
        e_offset = struct.unpack("<I", cpd[ee_off + 0x10:ee_off + 0x14])[0]
        e_size = struct.unpack("<I", cpd[ee_off + 0x14:ee_off + 0x18])[0]
        e_flags = struct.unpack("<H", cpd[ee_off + 0x18:ee_off + 0x1A])[0]
        if j < 25 or "MCP" in e_name or "MCD" in e_name:
            print(f"      [{j:2d}] {e_name:14s} offset=0x{e_offset:08x} size=0x{e_size:08x} flags=0x{e_flags:x}")
    pos += 1
