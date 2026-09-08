#!/usr/bin/env python3
"""
直接用 uefi_firmware.me 的 MeContainer + HuffmanLUTHeader 解压 PMCC000

目标：从第三方 bin 提取 ME 16.x 的 PMCC000 Huffman 压缩 microcode 容器
"""
import sys
import struct
import hashlib
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uefi_firmware.me import (
    MeContainer, MeObject, HuffmanLUTHeader, COMP_TYPE_HUFFMAN,
    COMP_TYPE_LZMA, COMP_TYPE_NOT_COMPRESSED
)


def decompress_huffman(data: bytes, offset: int):
    """手动解压 ME 16.x Huffman 压缩数据

    格式：
    - 0x00: 0x5F 0xAA 0x5A 0xA5 (Huffman magic)
    - 0x04: total_size
    - 0x08: data_size (解压后)
    - 0x10: entry_count
    - 0x14: header_size
    - 0x18-...: Huffman LUT
    - ...: 压缩数据
    """
    if data[offset:offset+4] != b"\x5f\xaa\x5a\xa5":
        return None, "magic mismatch"

    total_size = struct.unpack("<I", data[offset+4:offset+8])[0]
    data_size = struct.unpack("<I", data[offset+8:offset+12])[0]
    print(f"  Huffman header @ 0x{offset:08x}:")
    print(f"    total_size=0x{total_size:x}, decompressed_size=0x{data_size:x}")

    return None, "Huffman decompression needs specific tool"


def extract_pmcc(bin_path: str):
    data = Path(bin_path).read_bytes()
    print(f"=== {bin_path} ===")
    print(f"大小: {len(data)} bytes\n")

    # 找 $CPD @ 0x23000
    CPD_SIG = b"$CPD"
    cpd_pos = data.find(CPD_SIG, 0x20000, 0x40000)
    if cpd_pos < 0:
        print("未找到 PMCC000 $CPD")
        return

    print(f"PMCC000 $CPD @ 0x{cpd_pos:08x}")
    cpd = data[cpd_pos:]
    num_entries = struct.unpack("<I", cpd[0x04:0x08])[0]
    print(f"  entries: {num_entries}\n")

    # entry 0: vendor
    # entry 1: PMCC000.man (metadata)
    # entry 2: ConstDat
    # entry 3: actual microcode data (Huffman)
    # entry 4: $MN2

    for j in range(num_entries):
        e_off = 0x20 + j * 0x20
        if e_off + 0x20 > len(cpd): break
        # entry 名字 (12 字节)
        name_bytes = cpd[e_off:e_off+12]
        name = name_bytes.decode("latin-1", errors="replace").rstrip("\x00").strip()
        # vendor (4 bytes at +0x04)
        vendor = cpd[e_off+0x04:e_off+0x08]
        # offset (4 bytes at +0x10)
        e_offset = struct.unpack("<I", cpd[e_off + 0x10:e_off + 0x14])[0]
        # size (4 bytes at +0x14)
        e_size = struct.unpack("<I", cpd[e_off + 0x14:e_off + 0x18])[0]
        # flags
        e_flags = struct.unpack("<H", cpd[e_off + 0x18:e_off + 0x1A])[0]

        # 实际内容起点 = $CPD 起点 + 0x20 + offset
        content_abs = cpd_pos + 0x20 + e_offset
        content_end = content_abs + e_size

        print(f"  Entry {j}: {name!r}")
        print(f"    vendor={vendor.hex()}")
        print(f"    offset=0x{e_offset:x}, size=0x{e_size:x}, flags=0x{e_flags:x}")
        print(f"    absolute content: 0x{content_abs:08x} - 0x{content_end:08x}")

        # 如果是 microcode 数据 entry (entry 3 通常)
        if "PMCC" in name or e_size > 0x10000:
            # 看内容头部
            head = data[content_abs:content_abs+32]
            head_hex = " ".join(f"{b:02x}" for b in head)
            print(f"    head hex: {head_hex}")

            # 尝试识别 compression type
            if head[:4] == b"\x5f\xaa\x5a\xa5":
                print(f"    *** Huffman compressed ***")
                try:
                    result, msg = decompress_huffman(data, content_abs)
                    if result:
                        print(f"    Decompressed: {len(result)} bytes")
                except Exception as e:
                    print(f"    Huffman decode error: {e}")
            elif head[:4] == b"\x5d\x00\x00\x00":
                print(f"    *** LZMA compressed (Intel) ***")
            elif head[:4] == b"\x01\x00\x00\x00":
                print(f"    *** Raw (no compression) ***")
        print()

    # 找 microcode 容器 — 扫描 PMCC 区域所有可能的 microcode 头
    print("=== 在 PMCC 区域 (0x23000-0x3A000) 找 microcode 头 ===")
    for off in range(0x23000, min(0x3A000, len(data)) - 0x30, 0x10):
        # 标准 microcode 头: type=1, rev=?
        # 90671 = 71 06 09 00, 906A0 = A0 06 09 00
        cpuid_bytes = data[off+0x0C:off+0x10]
        if cpuid_bytes in [bytes.fromhex("71060900"), bytes.fromhex("A0060900")]:
            rev = struct.unpack("<I", data[off+0x04:off+0x08])[0]
            date = struct.unpack("<I", data[off+0x08:off+0x0C])[0]
            print(f"  0x{off:08x}: rev=0x{rev:x}, date=0x{date:x}, CPUID={cpuid_bytes.hex()}")

    # 也找其他 CPUID (9067A, B0671 等)
    print("\n=== 找可能的 12 代 / 14 代 microcode (PMCC 区域) ===")
    found_12_14 = []
    for off in range(0x23000, min(0x3A000, len(data)) - 0x30, 0x10):
        # microcode 头: type(1) at 0x00, rev(非零) at 0x04, date(8位 packed) at 0x08, cpuid at 0x0C
        type_v = struct.unpack("<I", data[off:off+4])[0]
        rev = struct.unpack("<I", data[off+4:off+8])[0]
        date = struct.unpack("<I", data[off+8:off+12])[0]
        cpuid = struct.unpack("<I", data[off+0x0C:off+0x10])[0]
        # 启发式
        if (type_v == 1
            and 0 < rev < 0x300
            and 0 < date < 0x300000
            and 0 < cpuid < 0x100000000
            and (cpuid & 0xFFF) > 0x600  # likely Intel CPU
        ):
            # 排除 90671 / 906A0 (已知)
            if cpuid in [0x00090671, 0x000906A0]:
                continue
            print(f"  0x{off:08x}: type={type_v} rev=0x{rev:x} date=0x{date:x} cpuid=0x{cpuid:08x}")
            found_12_14.append((off, cpuid, rev, date))

    if not found_12_14:
        print("  未找到新的 microcode 容器 (除 90671/906A0 外)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python extract_pmcc.py <bin>")
        sys.exit(1)
    extract_pmcc(sys.argv[1])
