#!/usr/bin/env python3
"""
解析 ME 16.x 区域：FPT partitions + CPD containers + Huffman microcode

输入：32MB 整片 SPI flash .bin
输出：ME 16.x PMCC000 容器的 microcode 列表（Huffman 解压）
"""
import sys
import struct
import hashlib
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uefi_firmware.me import (
    MePartitionTable, MeContainer, MeObject, MeCpdEntryType,
    HuffmanLUTHeader, MeLLUT, COMP_TYPE_HUFFMAN, COMP_TYPE_LZMA, COMP_TYPE_NOT_COMPRESSED
)


def parse_me_16(bin_path: str):
    data = Path(bin_path).read_bytes()
    print(f"=== {bin_path} ===")
    print(f"大小: {len(data)} bytes\n")

    # 1. 找 $FPT
    FPT_SIG = b"$FPT"
    fpt_off = data.find(FPT_SIG)
    if fpt_off < 0:
        print("未找到 $FPT")
        return
    print(f"$FPT 在 0x{fpt_off:08x}")

    # 2. 解析 FPT
    fpt = data[fpt_off:]
    mpt = MePartitionTable(fpt)
    # 触发解析
    if hasattr(mpt, "_header"):
        mpt._header()
    num_parts = fpt[0x04]
    print(f"Partitions: {num_parts}")
    print()

    # 3. 列所有 partitions
    print("=== ME Partitions ===")
    for i in range(num_parts):
        e_off = 0x20 + i * 0x20
        if e_off + 0x20 > len(fpt): break
        name = fpt[e_off:e_off+4].decode("latin-1")
        part_offset = struct.unpack("<I", fpt[e_off + 0x08:e_off + 0x0C])[0]
        part_size = struct.unpack("<I", fpt[e_off + 0x0C:e_off + 0x10])[0]
        print(f"  [{i:2d}] {name:6s} @ 0x{part_offset:08x} size=0x{part_size:08x} (abs 0x{fpt_off+part_offset:08x})")

    # 4. 找 PMCC000 (Platform MicroCode Code) 容器
    # ME 16.x 的 PMCC000 容器在 ME 主区域内的某个子区域
    # 通常在 ME 区域前部 (靠近 $FPT)
    # 让我们搜索 PMCP / PMCC000 字符串
    print("\n=== 找 PMCC 容器 ===")
    for sig in [b"PMCC000", b"PMCP", b"$CPD", b"PMCC"]:
        pos = 0
        while True:
            pos = data.find(sig, pos)
            if pos < 0: break
            print(f"  0x{pos:08x}: {sig.decode()}")
            pos += 1

    # 5. 找 $CPD (Code Partition Directory) 区域
    CPD_SIG = b"$CPD"
    cpd_positions = []
    pos = 0
    while True:
        pos = data.find(CPD_SIG, pos)
        if pos < 0: break
        cpd_positions.append(pos)
        pos += 1
    print(f"\n=== 找到 {len(cpd_positions)} 个 $CPD ===")
    for cpd_pos in cpd_positions:
        cpd = data[cpd_pos:]
        try:
            num_entries = struct.unpack("<I", cpd[0x04:0x08])[0]
        except:
            continue
        if num_entries > 50 or num_entries == 0:
            continue
        print(f"\n  $CPD @ 0x{cpd_pos:08x}, entries={num_entries}")
        for j in range(num_entries):
            e_off = 0x20 + j * 0x20
            if e_off + 0x20 > len(cpd): break
            e_name = cpd[e_off:e_off + 12].decode("latin-1", errors="replace").rstrip("\x00").strip()
            e_offset = struct.unpack("<I", cpd[e_off + 0x10:e_off + 0x14])[0]
            e_size = struct.unpack("<I", cpd[e_off + 0x14:e_off + 0x18])[0]
            if "MCP" in e_name or "MCD" in e_name or "Microcode" in e_name:
                print(f"    [{j:2d}] ⭐ {e_name:14s} offset=0x{e_offset:08x} size=0x{e_size:08x}")
            elif j < 8:
                print(f"    [{j:2d}] {e_name:14s} offset=0x{e_offset:08x} size=0x{e_size:08x}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python parse_me_pmcc.py <bin>")
        sys.exit(1)
    parse_me_16(sys.argv[1])
