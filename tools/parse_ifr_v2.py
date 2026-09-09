#!/usr/bin/env python3
"""
用 uefi_firmware 库深度遍历 BIOS 提取所有 Setup 菜单项
"""
import sys
import json
import struct
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uefi_firmware.uefi import FirmwareVolume, FirmwareFileSystem, FirmwareFile


def walk(obj, depth=0):
    """递归遍历所有对象"""
    if depth > 15:
        return
    yield obj
    for attr in ["objects", "sections", "files"]:
        v = getattr(obj, attr, None)
        if isinstance(v, list):
            for c in v:
                if isinstance(c, FirmwareFile) or hasattr(c, "objects") or hasattr(c, "sections"):
                    yield from walk(c, depth + 1)


def main():
    if len(sys.argv) < 2:
        print("用法: python parse_ifr_v2.py <32MB.bin>")
        sys.exit(1)

    bin_path = Path(sys.argv[1])
    data = bin_path.read_bytes()
    print(f"=== {bin_path.name} ===\n大小: {len(data):,} bytes\n")

    items = []
    string_pool = {}

    # Q100-E V1 已知 FV 位置 (从 MMTool 报告 + 之前扫描)
    fv_positions = [
        0x01000000, 0x01030000, 0x01070000, 0x01071000, 0x01370000,  # FV 0-4
        0x016B0000, 0x01A70000, 0x01B00000, 0x01BB0000, 0x01D00000,  # FV 5-9
        0x01D10000, 0x01D90000, 0x01E90000, 0x01F80000, 0x01FC0000,  # FV 10-14
    ]
    # 找 0x1C-0x1F 区间的嵌套 FV
    for off in range(0x01D00000, 0x02000000, 0x100):
        if data[off:off + 4] == b"_FVH":
            fv_positions.append(off)

    fv_count = 0
    file_count = 0
    hii_count = 0
    all_items = []

    for off in fv_positions:
        if off + 4 > len(data) or data[off:off + 4] != b"_FVH":
            continue
        fv_count += 1
        try:
            fv = FirmwareVolume(data[off:off + 0x100000], off=off)
        except Exception as e:
            continue

        # 收集 string pool
        # 收集所有 files
        for ff in walk(fv):
            if not isinstance(ff, FirmwareFile):
                continue
            file_count += 1
            guid = getattr(ff, "guid", None)
            if guid is None:
                continue
            try:
                guid_str = guid.bytes_le.hex() if hasattr(guid, "bytes_le") else str(guid).lower()
            except:
                guid_str = str(guid).lower()
            # HII data: 1C6825A2-1418-4F2A-9083-2A8C9C9A8E22
            if "1c6825a21418" in guid_str:
                hii_count += 1
                print(f"  找到 HII 数据包: FV @ 0x{off:08x} file GUID={guid_str[:32]}...")

    print(f"\n扫到 {fv_count} 个 FFS volumes (已知位置)")
    print(f"扫到 {file_count} 个 FFS files")
    print(f"找到 {hii_count} 个 HII 数据包")

    out = bin_path.with_suffix(".ifr_v2.json")
    out.write_text(json.dumps({
        "bin": str(bin_path),
        "fv_count": fv_count,
        "file_count": file_count,
        "hii_count": hii_count,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n报告: {out}")


if __name__ == "__main__":
    main()
