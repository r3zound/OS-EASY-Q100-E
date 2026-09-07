#!/usr/bin/env python3
"""用 uefi_firmware.me 解析 ME 区域，找 microcode"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import uefi_firmware
print(f"uefi_firmware 路径: {uefi_firmware.__file__}")
print(f"me 模块内容: {[a for a in dir(uefi_firmware.me) if not a.startswith('_')]}")

# 直接用 MEBinParser 解析
data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()

# 找 $FPT 起点（ME 区域入口）
FPT_SIG = b"$FPT"
fpt_offset = data.find(FPT_SIG)
print(f"\n$FPT 在 0x{fpt_offset:08x}")

# 解析 $FPT
# $FPT 头部：
#   0x00: '$FPT' (4 bytes)
#   0x04: ? (4 bytes)
#   0x08: ? (4 bytes)
#   0x0C: ? (4 bytes)
#   0x10: NumPartitions
#   0x14-0x17: ?
# 接下来是 partition entries (每个 32 bytes)
print()
print("=== $FPT Partition 列表 ===")
fpt = data[fpt_offset:]
num_parts = struct.unpack("<I", fpt[0x10:0x14])[0]
print(f"Partitions: {num_parts}")
for i in range(num_parts):
    entry_off = 0x20 + i * 0x20
    if entry_off + 0x20 > len(fpt): break
    name = fpt[entry_off:entry_off + 4].decode("latin-1")
    offset = struct.unpack("<I", fpt[entry_off + 4:entry_off + 8])[0]
    size = struct.unpack("<I", fpt[entry_off + 8:entry_off + 12])[0]
    flags = fpt[entry_off + 12]
    print(f"  [{i}] {name:6s} offset=0x{offset:08x} size=0x{size:08x} flags=0x{flags:02x} (绝对 0x{fpt_offset + offset:08x})")

# 找 PMCP 分区（Platform Microcode Patch）
print()
print("=== 找 PMCP (Platform Microcode Patch) ===")
for i in range(num_parts):
    entry_off = 0x20 + i * 0x20
    if entry_off + 0x20 > len(fpt): break
    name = fpt[entry_off:entry_off + 4].decode("latin-1")
    if "PMCP" in name or "MCP" in name or "MCD" in name or "MUP" in name:
        offset = struct.unpack("<I", fpt[entry_off + 4:entry_off + 8])[0]
        size = struct.unpack("<I", fpt[entry_off + 8:entry_off + 12])[0]
        print(f"  找到 {name}: offset=0x{offset:x} size=0x{size:x} (绝对 0x{fpt_offset + offset:x})")

# 也找 $CPD 起点
print()
print("=== 找 $CPD (Code Partition Directory) ===")
CPD_SIG = b"$CPD"
for i in range(num_parts):
    entry_off = 0x20 + i * 0x20
    if entry_off + 0x20 > len(fpt): break
    name = fpt[entry_off:entry_off + 4].decode("latin-1")
    if name == "FTPR" or name == "PMCP":
        offset = struct.unpack("<I", fpt[entry_off + 4:entry_off + 8])[0]
        size = struct.unpack("<I", fpt[entry_off + 8:entry_off + 12])[0]
        abs_offset = fpt_offset + offset
        cpd_pos = data.find(CPD_SIG, abs_offset, abs_offset + size)
        if cpd_pos >= 0:
            print(f"  {name} 子目录在 0x{cpd_pos:08x}")
            # 解析 CPD
            cpd = data[cpd_pos:cpd_pos + size]
            num_entries = struct.unpack("<I", cpd[0x04:0x08])[0]
            print(f"    Entries: {num_entries}")
            for j in range(min(num_entries, 20)):
                e_off = 0x20 + j * 0x20
                if e_off + 0x20 > len(cpd): break
                e_name = cpd[e_off:e_off + 12].decode("latin-1", errors="replace").rstrip("\x00")
                e_offset = struct.unpack("<I", cpd[e_off + 0x10:e_off + 0x14])[0]
                e_size = struct.unpack("<I", cpd[e_off + 0x14:e_off + 0x18])[0]
                e_flags = struct.unpack("<H", cpd[e_off + 0x18:e_off + 0x1A])[0]
                print(f"      [{j}] {e_name:14s} offset=0x{e_offset:08x} size=0x{e_size:08x} flags=0x{e_flags:x}")
