#!/usr/bin/env python3
"""
综合 BIOS bin 分析脚本（v3 终极版）

输入：32MB 整片 SPI flash .bin 文件
输出：
  - 整体 hash
  - Flash Descriptor 解析（含 OEM 偏移支持）
  - ME 区域 + FPT 详细
  - ME 各 partition 列表
  - microcode 位置（PMCP/PMCC000）
  - BIOS region FTPR 概要
  - 14 代 RPL-R 支持评估
  - JSON 报告

依赖：uefi-firmware 1.16
"""

import sys
import struct
import json
import hashlib
import zlib
import re
from pathlib import Path

# 强制 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def analyze_bin(bin_path: str):
    path = Path(bin_path)
    if not path.exists():
        print(f"[X] 文件不存在: {bin_path}")
        return

    data = path.read_bytes()
    size = len(data)
    sha256 = hashlib.sha256(data).hexdigest()
    md5 = hashlib.md5(data).hexdigest()
    crc = crc32(data)

    print(f"=== {bin_path} ===")
    print(f"大小:    {size} bytes ({size/1024/1024:.2f} MB)")
    print(f"SHA256:  {sha256}")
    print(f"MD5:     {md5}")
    print(f"CRC32:   {crc:08x}\n")

    report = {
        "file": str(path),
        "size": size,
        "hashes": {"sha256": sha256, "md5": md5, "crc32": f"{crc:08x}"},
    }

    # 1. Flash Descriptor
    print("=" * 60)
    print("【Flash Descriptor】")
    FD_SIG = bytes.fromhex("5aa5f00f")
    fd_offset = -1
    for off in range(0, 0x100):
        if data[off:off + 4] == FD_SIG:
            fd_offset = off
            break

    if fd_offset >= 0:
        print(f"  FD signature 在 0x{fd_offset:08x} (标准是 0x00，本机偏移到 0x{fd_offset:x} 说明有 OEM 前缀)")
        report["fd_offset"] = fd_offset
    else:
        print("  FD signature 未找到")

    # 2. $FPT (ME Flash Partition Table)
    print()
    print("=" * 60)
    print("【ME 区域 $FPT】")
    FPT_SIG = b"$FPT"
    fpt_offset = data.find(FPT_SIG)
    if fpt_offset < 0:
        print("  $FPT 未找到")
    else:
        print(f"  $FPT 在 0x{fpt_offset:08x}")
        fpt = data[fpt_offset:]
        num_parts = fpt[0x04]
        report["fpt_offset"] = fpt_offset
        report["me_partitions"] = []

        # 找版本字符串
        ver_match = re.search(rb"(\d+\.\d+\.\d+\.\d+)", fpt[0:0x10000])
        if ver_match:
            me_ver = ver_match.group(0).decode("latin-1")
            print(f"  ME 版本: {me_ver}")
            report["me_version"] = me_ver

        print(f"  Partitions: {num_parts}")
        # entries 起点 0x20
        for i in range(num_parts):
            e_off = 0x20 + i * 0x20
            if e_off + 0x20 > len(fpt):
                break
            name = fpt[e_off:e_off + 4].decode("latin-1")
            part_offset = struct.unpack("<I", fpt[e_off + 0x08:e_off + 0x0C])[0]
            part_size = struct.unpack("<I", fpt[e_off + 0x0C:e_off + 0x10])[0]
            report["me_partitions"].append({
                "name": name,
                "offset": part_offset,
                "size": part_size,
                "abs_offset": fpt_offset + part_offset,
            })

    # 3. $CPD (Code Partition Directory) 扫描
    print()
    print("=" * 60)
    print("【$CPD (Code Partition Directory) 扫描】")
    CPD_SIG = b"$CPD"
    pos = 0
    cpds = []
    while True:
        pos = data.find(CPD_SIG, pos)
        if pos < 0:
            break
        cpd = data[pos:]
        try:
            num_entries = struct.unpack("<I", cpd[0x04:0x08])[0]
        except struct.error:
            pos += 1
            continue
        if num_entries > 50 or num_entries == 0:
            pos += 1
            continue

        cpd_info = {"offset": pos, "entries": []}
        for j in range(num_entries):
            ee_off = 0x20 + j * 0x20
            if ee_off + 0x20 > len(cpd):
                break
            e_name = cpd[ee_off:ee_off + 12].decode("latin-1", errors="replace").rstrip("\x00").strip()
            e_offset = struct.unpack("<I", cpd[ee_off + 0x10:ee_off + 0x14])[0]
            e_size = struct.unpack("<I", cpd[ee_off + 0x14:ee_off + 0x18])[0]
            cpd_info["entries"].append({
                "name": e_name,
                "offset": e_offset,
                "size": e_size,
            })
        cpds.append(cpd_info)
        pos += 1

    for cpd in cpds:
        print(f"\n  $CPD @ 0x{cpd['offset']:08x}, entries={len(cpd['entries'])}")
        for e in cpd["entries"][:10]:
            print(f"    - {e['name']:14s} offset=0x{e['offset']:08x} size=0x{e['size']:08x}")
        if len(cpd["entries"]) > 10:
            print(f"    ...及其他 {len(cpd['entries']) - 10} 个")

    report["cpds"] = cpds

    # 4. microcode 位置
    print()
    print("=" * 60)
    print("【microcode 位置】")
    print("  BIOS region (传统 FFS microcode 文件):")
    UCODE_GUID = bytes.fromhex("D2A78CE0521B0D4F92973BC2E38DF9DC")
    if data.find(UCODE_GUID) >= 0:
        print("    [+] 找到 EFI microcode GUID")
    else:
        print("    [-] 未找到（这块板的 microcode 不在 BIOS region）")

    print("  ME 区域 (PMCP 容器):")
    pmcp_found = False
    for cpd in cpds:
        for e in cpd["entries"]:
            if "PMCC" in e["name"] or "PMCP" in e["name"]:
                if "PMCC" in e["name"]:
                    pmcp_found = True
                    print(f"    [+] {e['name']} in $CPD @ 0x{cpd['offset']:08x}")
                    print(f"        offset=0x{e['offset']:08x} size=0x{e['size']:08x}")
    if not pmcp_found:
        print("    [-] 未找到 PMCC 容器")

    # 5. 14 代 RPL-R 支持评估
    print()
    print("=" * 60)
    print("【14 代 RPL-R 支持评估】")
    me_ver = report.get("me_version", "")
    if me_ver.startswith("16."):
        print(f"  ME 版本: {me_ver} (16.x - 理论支持 14 代)")
    elif me_ver.startswith("15."):
        print(f"  ME 版本: {me_ver} (15.x - 部分支持)")
    elif me_ver.startswith("14.") or me_ver.startswith("13."):
        print(f"  ME 版本: {me_ver} (14.x 以下 - 不支持 14 代)")
    else:
        print(f"  ME 版本: {me_ver or '未知'}")

    # 写 JSON 报告
    json_path = path.with_suffix(".analysis.json")
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  详细 JSON 报告: {json_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python parse_full.py <bin文件>")
        sys.exit(1)
    analyze_bin(sys.argv[1])
