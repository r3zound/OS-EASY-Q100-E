#!/usr/bin/env python3
"""正确解析 ME FPT + CPD + microcode"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()

# 找 $FPT
FPT_SIG = b"$FPT"
fpt_offset = data.find(FPT_SIG)
print(f"$FPT 在 0x{fpt_offset:08x}")

fpt = data[fpt_offset:]
print(f"  头部字节: {fpt[:0x40].hex()}")
print()

# 头部结构（参考 ME 文档）：
# 0x00-0x03: signature "$FPT"
# 0x04: NumPartitions (uint8)
# 0x05: FlashPartitionVersion (uint8)
# 0x06-0x07: ?
# 0x08-0x0B: ?
# 0x0C-0x0F: ?
# 0x10-0x13: EntryOffset (4 bytes, 一般是 0x20 或 0x30)
# 0x14-0x1F: ?
# 0x20 起: entries (each 0x20 bytes)
num_parts = fpt[0x04]
entry_offset = struct.unpack("<I", fpt[0x10:0x14])[0]
flash_version = fpt[0x05]
print(f"NumPartitions (uint8): {num_parts}")
print(f"FlashPartitionVersion: 0x{flash_version:02x}")
print(f"EntryOffset: 0x{entry_offset:x}")
print()

print("=== $FPT Partition Entries ===")
for i in range(num_parts):
    e_off = entry_offset + i * 0x20
    if e_off + 0x20 > len(fpt): break
    name = fpt[e_off:e_off + 4].decode("latin-1")
    # 解析 partition entry:
    # 0x00-0x03: name
    # 0x04-0x07: ? (vendor / type)
    # 0x08-0x0B: offset (in flash)
    # 0x0C-0x0F: ?
    # 0x10-0x13: size
    # 0x14: ?
    # 0x15: ?
    # 0x16-0x17: ?
    part_offset = struct.unpack("<I", fpt[e_off + 0x08:e_off + 0x0C])[0]
    part_size = struct.unpack("<I", fpt[e_off + 0x10:e_off + 0x14])[0]
    print(f"  [{i:2d}] {name:6s} offset=0x{part_offset:08x} size=0x{part_size:08x} (绝对 0x{fpt_offset + part_offset:08x}, {part_size/1024:.0f} KB)")

# 找 PMCP 或类似 microcode partition
print()
print("=== 找 microcode partition ===")
for i in range(num_parts):
    e_off = entry_offset + i * 0x20
    if e_off + 0x20 > len(fpt): break
    name = fpt[e_off:e_off + 4].decode("latin-1")
    if "MCP" in name or "PMCP" in name or "MCD" in name or "MUP" in name or "MCE" in name:
        part_offset = struct.unpack("<I", fpt[e_off + 0x08:e_off + 0x0C])[0]
        part_size = struct.unpack("<I", fpt[e_off + 0x10:e_off + 0x14])[0]
        print(f"  找到 {name}: offset=0x{part_offset:08x} size=0x{part_size:08x}")
        # 解析 partition 内部
        abs_start = fpt_offset + part_offset
        abs_end = abs_start + part_size
        partition_data = data[abs_start:abs_end]
        # 找 $CPD
        cpd_pos = partition_data.find(b"$CPD")
        if cpd_pos >= 0:
            cpd = partition_data[cpd_pos:]
            num_entries = struct.unpack("<I", cpd[0x04:0x08])[0]
            print(f"    $CPD 在 +0x{cpd_pos:x}, entries={num_entries}")
            for j in range(num_entries):
                ee_off = 0x20 + j * 0x20
                if ee_off + 0x20 > len(cpd): break
                e_name = cpd[ee_off:ee_off + 12].decode("latin-1", errors="replace").rstrip("\x00")
                e_offset = struct.unpack("<I", cpd[ee_off + 0x10:ee_off + 0x14])[0]
                e_size = struct.unpack("<I", cpd[ee_off + 0x14:ee_off + 0x18])[0]
                e_flags = struct.unpack("<H", cpd[ee_off + 0x18:ee_off + 0x1A])[0]
                print(f"      [{j:2d}] {e_name:14s} offset=0x{e_offset:08x} size=0x{e_size:08x} flags=0x{e_flags:x}")
                # 如果名字含 Microcode / MCD 关键词，dump 头部
                if "MCD" in e_name or "Microcode" in e_name or "ucode" in e_name.lower():
                    abs_e = abs_start + cpd_pos + e_offset
                    print(f"          absolute: 0x{abs_e:08x}, 头部 32 字节:")
                    for k in range(0, 32, 16):
                        print(f"            {' '.join(f'{b:02x}' for b in data[abs_e+k:abs_e+k+16])}")

# 也找 FTPR（主 code partition）
print()
print("=== FTPR (主 Code Partition) ===")
for i in range(num_parts):
    e_off = entry_offset + i * 0x20
    if e_off + 0x20 > len(fpt): break
    name = fpt[e_off:e_off + 4].decode("latin-1")
    if name == "FTPR":
        part_offset = struct.unpack("<I", fpt[e_off + 0x08:e_off + 0x0C])[0]
        part_size = struct.unpack("<I", fpt[e_off + 0x10:e_off + 0x14])[0]
        print(f"  FTPR offset=0x{part_offset:08x} size=0x{part_size:08x} (绝对 0x{fpt_offset + part_offset:08x})")
        abs_start = fpt_offset + part_offset
        partition_data = data[abs_start:abs_start + part_size]
        cpd_pos = partition_data.find(b"$CPD")
        if cpd_pos >= 0:
            cpd = partition_data[cpd_pos:]
            num_entries = struct.unpack("<I", cpd[0x04:0x08])[0]
            print(f"  $CPD 在 +0x{cpd_pos:x}, entries={num_entries}")
            for j in range(num_entries):
                ee_off = 0x20 + j * 0x20
                if ee_off + 0x20 > len(cpd): break
                e_name = cpd[ee_off:ee_off + 12].decode("latin-1", errors="replace").rstrip("\x00")
                e_offset = struct.unpack("<I", cpd[ee_off + 0x10:ee_off + 0x14])[0]
                e_size = struct.unpack("<I", cpd[ee_off + 0x14:ee_off + 0x18])[0]
                print(f"    [{j:2d}] {e_name:14s} offset=0x{e_offset:08x} size=0x{e_size:08x}")
