#!/usr/bin/env python3
"""
用 MeContainer 解 PMCC000 数据 + 全区域扫 microcode

MeContainer 是 uefi_firmware 的 ME 16.x 容器解析器
"""
import sys
import struct
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uefi_firmware.me import MeContainer, MeObject, COMP_TYPE_HUFFMAN, COMP_TYPE_LZMA, COMP_TYPE_NOT_COMPRESSED


def try_parse_container(data: bytes, offset: int, size: int, name: str = ""):
    """尝试用 MeContainer 解析"""
    print(f"\n=== 尝试 MeContainer 解析 {name} @ 0x{offset:08x} (size=0x{size:x}) ===")
    container_data = data[offset:offset + size]

    # MeContainer 需要 buf 指针
    try:
        container = MeContainer(container_data)
        # 显示对象
        if hasattr(container, "objects"):
            print(f"  objects: {len(container.objects)}")
            for obj in container.objects[:5]:
                print(f"    - {type(obj).__name__}")
                if hasattr(obj, "attrs"):
                    for k, v in list(obj.attrs.items())[:5]:
                        print(f"      {k}: {v}")
        else:
            print(f"  type: {type(container).__name__}")
            print(f"  attrs: {container.attrs if hasattr(container, 'attrs') else 'N/A'}")
    except Exception as e:
        print(f"  解析失败: {e}")

    # 显示头 64 字节
    print(f"  head 64 bytes:")
    for i in range(0, min(64, size), 16):
        h = " ".join(f"{b:02x}" for b in container_data[i:i+16])
        print(f"    0x{offset+i:08x}: {h}")

    # 显示尾 64 字节
    if size > 128:
        print(f"  tail 64 bytes:")
        tail_off = size - 64
        for i in range(0, 64, 16):
            h = " ".join(f"{b:02x}" for b in container_data[tail_off+i:tail_off+i+16])
            print(f"    0x{offset+tail_off+i:08x}: {h}")


def main():
    if len(sys.argv) < 2:
        print("用法: python decode_pmcc.py <bin>")
        sys.exit(1)

    data = Path(sys.argv[1]).read_bytes()
    print(f"=== {sys.argv[1]} ===")
    print(f"大小: {len(data)} bytes\n")

    # 找 PMCC000 $CPD
    cpd_pos = data.find(b"$CPD", 0x20000, 0x40000)
    if cpd_pos < 0:
        print("未找到 PMCC000 $CPD")
        return

    # Entry 3 实际数据
    e3_off = 0x20 + 3 * 0x20
    e3_offset = struct.unpack("<I", data[cpd_pos + e3_off + 0x10:cpd_pos + e3_off + 0x14])[0]
    e3_size = struct.unpack("<I", data[cpd_pos + e3_off + 0x14:cpd_pos + e3_off + 0x18])[0]
    e3_abs = cpd_pos + 0x20 + e3_offset

    print(f"PMCC000 数据 entry:")
    print(f"  CPD @ 0x{cpd_pos:08x}")
    print(f"  Entry 3 offset=0x{e3_offset:x}, size=0x{e3_size:x}")
    print(f"  Absolute: 0x{e3_abs:08x} - 0x{e3_abs + e3_size:08x}")

    try_parse_container(data, e3_abs, e3_size, "PMCC000 Data")

    # 同时检查 entry 0 的 vendor 头
    print("\n=== Entry 0 vendor 头 ===")
    e0_off = 0x20
    e0_abs = cpd_pos + 0x20
    e0_head = " ".join(f"{b:02x}" for b in data[e0_abs:e0_abs+64])
    print(f"  0x{e0_abs:08x}: {e0_head}")

    # 找 microcode bundle magic
    # Intel microcode bundle 头: 0x00000001 0x00000001 (loader sig)
    # microcode 头: 0x00000001 (type) + rev + date + cpuid
    print("\n=== 找 microcode 头（type=1, 8 字节对齐, rev>0）===")
    found_mc = []
    for off in range(0x23000, min(0x3A000, len(data)) - 0x30, 0x08):
        if (off & 0x7) != 0:  # 8 字节对齐
            continue
        type_v = struct.unpack("<I", data[off:off+4])[0]
        rev = struct.unpack("<I", data[off+4:off+8])[0]
        if type_v != 1 or rev == 0 or rev > 0x1000:
            continue
        # 看 date 和 cpuid
        date = struct.unpack("<I", data[off+8:off+12])[0]
        cpuid = struct.unpack("<I", data[off+0x0C:off+0x10])[0]
        if 0 < date < 0x300000 and 0 < cpuid < 0x100000000:
            # 进一步验证: cpuid 应该像 Intel CPUID
            fam = (cpuid >> 8) & 0xF
            if fam == 0x6 or (cpuid & 0xF000) == 0:
                found_mc.append((off, type_v, rev, date, cpuid))

    print(f"找到 {len(found_mc)} 个 microcode 头")
    seen = set()
    for off, t, rev, date, cpuid in found_mc:
        key = (cpuid, rev, date)
        if key in seen: continue
        seen.add(key)
        d_year = (date >> 16) & 0xFFFF
        d_mon = (date >> 8) & 0xFF
        d_day = date & 0xFF
        print(f"  0x{off:08x}: rev=0x{rev:02x} date={d_year:04d}-{d_mon:02d}-{d_day:02d} CPUID=0x{cpuid:08x}")


if __name__ == "__main__":
    main()
