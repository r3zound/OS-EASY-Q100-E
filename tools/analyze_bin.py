#!/usr/bin/env python3
"""
BIOS bin 解包分析脚本 v2

输入：32MB 整片 SPI flash .bin 文件
输出：
  - 整体 hash（SHA256 + MD5 + CRC32）
  - 多策略找 Intel Flash Descriptor
  - 找 ME 区域（字符串 / FPT 模式 / 4KB 边界结构）
  - 找 BIOS 区域
  - 全 bin 扫描 microcode 列表

依赖：uefi-firmware 1.16（如果存在）
"""

import hashlib
import struct
import sys
import json
import re
import zlib
from pathlib import Path


# 强制 UTF-8 输出，绕过 Windows PowerShell 默认 GBK
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ---------- 工具函数 ----------

def crc32(data: bytes) -> int:
    return zlib.crc32(data) & 0xFFFFFFFF


def find_intel_fd(data: bytes):
    """查找 Intel Flash Descriptor（FD signature 0x5A A5 F0 0F，可被 OEM 保护）"""
    FD_SIG = bytes.fromhex("5aa5f00f")
    result = {"found": False, "offset": None, "note": None}

    # 搜索 0x0000 - 0x0010（标准位置）
    for off in range(0, 0x100, 4):
        if data[off:off+4] == FD_SIG:
            result["found"] = True
            result["offset"] = off
            return result

    # OEM 锁了：尝试搜索 "FLPTR" 字符串
    for i in range(0, 0x1000):
        if data[i:i+4] == FD_SIG:
            result["found"] = True
            result["offset"] = i
            return result

    # 检查 FD 是否被加密/保护
    # 头部如果是 0xFF 填充，可能 FD 未启用
    if all(b == 0xFF for b in data[0:0x10]):
        result["note"] = "头部全 0xFF，FD 未启用"
    elif data[0] in (0x00, 0x5A, 0x9C):
        result["note"] = f"头部首字节 0x{data[0]:02x}，可能是 OEM 锁定或非标准 FD"

    return result


def find_fd_regions(data: bytes, fd_offset: int = 0):
    """从 FD 起点解析各 region（FREG）"""
    if fd_offset + 0x1000 > len(data):
        return []

    # 0x10-0x13: FLPTR signature
    flptr_sig = data[fd_offset+0x10:fd_offset+0x14]
    if flptr_sig != b"\x46\x4c\x50\x54":  # "FLPT"
        return []

    flptr = struct.unpack("<I", data[fd_offset+0x14:fd_offset+0x18])[0]
    frba_offset = fd_offset + flptr * 16  # 经验：FLPTR 是 dword 偏移

    if frba_offset + 0x40 > len(data):
        return []

    region_names = ["FD", "BIOS", "ME", "GbE", "PD", "Reserved1", "Reserved2", "Reserved3",
                    "EC", "Reserved5", "Reserved6", "Reserved7", "Reserved8", "Reserved9",
                    "Reserved10", "Reserved11"]

    regions = []
    for i in range(15):
        off = frba_offset + i * 4
        if off + 4 > len(data):
            break
        reg = struct.unpack("<I", data[off:off+4])[0]
        if reg == 0 or reg == 0xFFFFFFFF:
            continue
        base = (reg & 0x1FFF) * 0x1000
        limit = ((reg >> 16) & 0x1FFF) * 0x1000
        if limit == 0 or base > limit:
            continue
        regions.append({
            "index": i,
            "name": region_names[i] if i < len(region_names) else f"R{i}",
            "base": base,
            "limit": limit,
            "size": limit - base + 0x1000,
        })

    return regions


def find_me_region(data: bytes, fd_regions: list = None):
    """找 ME 区域：通过 FD 解析 或 字符串扫描"""
    if fd_regions:
        for r in fd_regions:
            if r["name"] == "ME":
                return r

    # 兜底 1：扫 "$FPT" 字符串（Flash Partition Table）
    for i in range(0, len(data) - 4, 0x1000):
        if data[i:i+4] == b"$FPT":
            return {"base": i, "size": 0, "found_by": "$FPT signature"}

    # 兜底 2：扫 "ME" 字符串头部
    for i in range(0, len(data) - 4, 0x1000):
        if data[i:i+4] in (b"MEFW", b"$MME", b"$FPT"):
            return {"base": i, "size": 0, "found_by": f"signature {data[i:i+4].hex()}"}

    # 兜底 3：ME 通常在 flash 后部
    for off in [0x1000000, 0x1800000, 0x2000000, 0xE00000, 0xF00000]:
        if off < len(data) and data[off:off+4] in (b"MEFW", b"$MME", b"$FPT"):
            return {"base": off, "size": 0, "found_by": f"offset 0x{off:x}"}

    return None


def find_bios_region(data: bytes, fd_regions: list = None, me_base: int = None):
    """找 BIOS 区域：通过 FD 解析 或 启发式（FIT 头部 0x5F 0x49 0x54 0x5F = "_FIT_"）"""
    if fd_regions:
        for r in fd_regions:
            if r["name"] == "BIOS":
                return r

    # 找 FIT 头（_FIT_）通常在 BIOS region 顶部
    for i in range(0, 0x200000, 0x1000):
        if i + 8 > len(data):
            break
        if data[i:i+4] == b"_FIT_":
            return {"base": i & ~0xFFF, "size": 0, "found_by": "_FIT_ signature"}

    return {"base": 0x1000, "size": 0, "found_by": "兜底 0x1000"}


def find_microcodes(data: bytes, search_start: int = 0, search_limit: int = None):
    """在数据中扫描 microcode 容器

    改进：
    - 不严格 0x800 对齐（很多 OEM BIOS 是 0x1000 对齐）
    - 尝试 0x800 / 0x1000 两种步长
    - 放宽 CPUID 验证
    """
    microcodes = []
    if search_limit is None:
        search_limit = len(data)
    search_limit = min(search_limit, len(data))
    search_data = data[search_start:search_limit]

    # 找 microcode 容器：扫描 0x800 步长
    for stride in [0x800, 0x1000, 0x2000]:
        i = 0
        while i + 0x30 < len(search_data):
            try:
                data_size = struct.unpack("<I", search_data[i:i+4])[0]
                loader_sig_1 = struct.unpack("<I", search_data[i+4:i+8])[0]
                loader_sig_2 = struct.unpack("<I", search_data[i+8:i+12])[0]
                ucode_rev = struct.unpack("<I", search_data[i+12:i+16])[0]
                rev_id = struct.unpack("<I", search_data[i+16:i+20])[0]
                cpuid_sig = struct.unpack("<I", search_data[i+20:i+24])[0]
                cpuid_flags = struct.unpack("<I", search_data[i+24:i+28])[0]
                ucode_date = struct.unpack("<I", search_data[i+28:i+32])[0]
            except struct.error:
                break

            # microcode 特征：loader_sig 都为 1，revision_id = 1
            is_microcode = (
                loader_sig_1 == 1
                and loader_sig_2 == 1
                and rev_id == 1
                and cpuid_sig != 0
                and cpuid_sig != 0xFFFFFFFF
                and ucode_date != 0
                and ucode_date < 0x300000  # 现实日期（年到 2000+）
                and 0 < data_size < 0x20000
            )

            if is_microcode:
                # 解析日期
                date_d = ucode_date & 0xFF
                date_m = (ucode_date >> 8) & 0xFF
                date_y = (ucode_date >> 16) & 0xFFFF

                microcodes.append({
                    "offset": i + search_start,
                    "offset_hex": f"0x{i + search_start:08x}",
                    "stride": f"0x{stride:x}",
                    "data_size": data_size,
                    "ucode_version": f"0x{ucode_rev:02x}",
                    "ucode_version_dec": ucode_rev,
                    "cpuid_sig": f"0x{cpuid_sig:08x}",
                    "cpuid_flags": f"0x{cpuid_flags:08x}",
                    "ucode_date": f"{date_y:04d}-{date_m:02d}-{date_d:02d}",
                })
                i += max(data_size, stride)
            else:
                i += stride

        if microcodes:
            break

    # 去重（同一个 offset 可能被多次扫描到）
    seen = set()
    unique = []
    for m in microcodes:
        if m["offset"] not in seen:
            seen.add(m["offset"])
            unique.append(m)
    return sorted(unique, key=lambda m: m["offset"])


def decode_cpuid(cpuid_sig: int):
    """解码 Intel CPUID 签名为 Family/Model/Stepping"""
    family = (cpuid_sig >> 8) & 0xF
    if family == 0xF:
        family += (cpuid_sig >> 20) & 0xFF
    model = (cpuid_sig >> 4) & 0xF
    if family in (0x6, 0xF):
        model += (cpuid_sig >> 12) & 0xF0
    stepping = cpuid_sig & 0xF

    # 已知代号对照
    cpu_names = {
        (0x6, 0x9E): "Kaby Lake (7代)",
        (0x6, 0x9C): "Apollo Lake",
        (0x6, 0x9F): "Coffee Lake",
        (0x6, 0xA5): "Comet Lake",
        (0x6, 0xA7): "Rocket Lake",
        (0x6, 0x97): "Alder Lake-S (12代)",
        (0x6, 0x9A): "Alder Lake-P",
        (0x6, 0xB7): "Raptor Lake-S (13代)",
        (0x6, 0xBA): "Raptor Lake-P",
        (0x6, 0xBF): "Raptor Lake-S Refresh (14代)",
        (0x6, 0xAA): "Meteor Lake",
        (0x6, 0xAC): "Meteor Lake",
    }

    cpu_name = cpu_names.get((family, model), f"Family {family} Model 0x{model:x}")

    return {
        "family": family,
        "model": model,
        "stepping": stepping,
        "family_hex": f"0x{family:x}",
        "model_hex": f"0x{model:x}",
        "stepping_hex": f"0x{stepping:x}",
        "cpu_name": cpu_name,
    }


# ---------- 主函数 ----------

def analyze_bin(bin_path: str):
    print(f"=== 分析 {bin_path} ===\n")
    path = Path(bin_path)
    if not path.exists():
        print(f"[X] 文件不存在: {bin_path}")
        return

    data = path.read_bytes()
    size = len(data)
    print(f"文件大小: {size} bytes ({size / 1024 / 1024:.2f} MB)")
    print(f"SHA256:   {hashlib.sha256(data).hexdigest()}")
    print(f"MD5:      {hashlib.md5(data).hexdigest()}")
    print(f"CRC32:    {crc32(data):08x}\n")

    # 0. 文件头 16 字节
    print("=" * 60)
    print("【0. 文件头部 16 字节】\n")
    head_hex = " ".join(f"{b:02x}" for b in data[0:16])
    print(f"  0x0000: {head_hex}")
    print(f"  ASCII: {''.join(chr(b) if 32 <= b < 127 else '.' for b in data[0:16])}\n")

    # 1. 找 FD
    print("=" * 60)
    print("【1. Intel Flash Descriptor】\n")
    fd = find_intel_fd(data)
    if fd["found"]:
        print(f"  [+] 找到 FD signature 在 0x{fd['offset']:08x}")
        regions = find_fd_regions(data, fd["offset"])
        if regions:
            print(f"  [+] 解析到 {len(regions)} 个 region:")
            for r in regions:
                print(f"      - {r['name']:10s}: 起点 0x{r['base']:08x} 终点 0x{r['limit']:08x} "
                      f"大小 0x{r['size']:08x} ({r['size'] / 1024:.0f} KB)")
        else:
            print(f"  [-] FLPTR / FREG 未找到")
    else:
        print(f"  [-] FD signature 未找到: {fd['note']}")
        regions = []

    # 2. 找 ME 区域
    print("\n" + "=" * 60)
    print("【2. ME（Management Engine）区域】\n")
    me_info = find_me_region(data, regions)
    if me_info:
        if "found_by" in me_info:
            print(f"  [+] ME 在 0x{me_info['base']:08x} (通过 {me_info['found_by']})")
        else:
            print(f"  [+] ME 区域: 0x{me_info['base']:08x} - 0x{me_info['base'] + me_info['size'] - 1:08x}")
            print(f"      大小: {me_info['size'] / 1024:.0f} KB")

        # 尝试找版本字符串
        for off in [me_info["base"], me_info["base"] - 0x1000 if me_info["base"] > 0 else 0]:
            if off + 0x100000 > len(data):
                continue
            seg = data[off:off + 0x100000]
            for pat, name in [
                (rb"(\d+\.\d+\.\d+\.\d+)", "version"),
                (rb"(\d{1,2}\.\d{1,2}\.\d{1,2}\.\d{1,4})", "version_alt"),
                (rb"Intel\(R\) Management Engine", "intel_me_marker"),
            ]:
                m = re.search(pat, seg)
                if m:
                    print(f"      {name}: {m.group(0)[:80]}")
                    break
    else:
        print(f"  [-] 未找到 ME 区域")

    # 3. 找 BIOS 区域 + microcode
    print("\n" + "=" * 60)
    print("【3. BIOS 区域与 microcode】\n")
    bios_info = find_bios_region(data, regions, me_info["base"] if me_info else None)
    print(f"  BIOS region 起点: 0x{bios_info['base']:08x}")
    if "found_by" in bios_info:
        print(f"  识别方式: {bios_info['found_by']}")

    print(f"\n  全 bin 扫描 microcode...")
    microcodes = find_microcodes(data, bios_info["base"])
    if microcodes:
        print(f"\n  [+] 找到 {len(microcodes)} 个 microcode:\n")
        print(f"    {'#':>3s}  {'偏移':>10s}  {'版本':>8s}  {'日期':>12s}  "
              f"{'CPUID':>10s}  {'F/M/S':>15s}  {'代号'}")
        print(f"    {'-'*3}  {'-'*10}  {'-'*8}  {'-'*12}  "
              f"{'-'*10}  {'-'*15}  {'-'*30}")
        for idx, mc in enumerate(microcodes, 1):
            cpuid_int = int(mc["cpuid_sig"], 16)
            ci = decode_cpuid(cpuid_int)
            fm = f"F{ci['family']}/M0x{ci['model']:x}/S{ci['stepping']}"
            print(f"    {idx:>3d}  {mc['offset_hex']:>10s}  {mc['ucode_version']:>8s}  "
                  f"{mc['ucode_date']:>12s}  {mc['cpuid_sig']:>10s}  {fm:>15s}  "
                  f"{ci['cpu_name']}")
    else:
        print(f"  [-] 未找到 microcode（可能 BIOS region 起点不对）")

    # 4. 总结
    print("\n" + "=" * 60)
    print("【4. 总结】\n")
    print(f"  整体 SHA256: {hashlib.sha256(data).hexdigest()}")
    print(f"  整体大小:   {size} bytes ({size / 1024 / 1024:.2f} MB)")

    if microcodes:
        families = set()
        cpu_names = set()
        for m in microcodes:
            ci = decode_cpuid(int(m["cpuid_sig"], 16))
            families.add(f"Family {ci['family']} (0x{ci['family']:x})")
            cpu_names.add(ci["cpu_name"])
        print(f"  已含 microcode 家族: {', '.join(sorted(families))}")
        print(f"  已含代号: {', '.join(sorted(cpu_names))}")

        # 14 代 RPL-R 检测
        has_rpl_r = any(int(m["cpuid_sig"], 16) == 0x000B0671 or
                        decode_cpuid(int(m["cpuid_sig"], 16))["cpu_name"].startswith("Raptor Lake-S Refresh")
                        for m in microcodes)
        print(f"  是否支持 14 代（RPL-R）: {'[+] 是' if has_rpl_r else '[-] 否'}")

        # 12 代 ADL-S 检测
        has_adl_s = any(decode_cpuid(int(m["cpuid_sig"], 16))["cpu_name"].startswith("Alder Lake-S")
                        for m in microcodes)
        print(f"  是否支持 12 代（ADL-S）: {'[+] 是' if has_adl_s else '[-] 否'}")

    # JSON 报告
    json_path = path.with_suffix(".analysis.json")
    report = {
        "file": str(path),
        "size": size,
        "hashes": {
            "sha256": hashlib.sha256(data).hexdigest(),
            "md5": hashlib.md5(data).hexdigest(),
            "crc32": f"{crc32(data):08x}",
        },
        "head_bytes_hex": head_hex,
        "flash_descriptor": fd,
        "regions": regions,
        "me": me_info,
        "bios": bios_info,
        "microcodes": microcodes,
    }
    if me_info:
        report["me_sha256"] = hashlib.sha256(data[me_info["base"]:me_info["base"] + (me_info.get("size") or 0x200000)]).hexdigest()
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  详细 JSON 报告: {json_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python analyze_bin.py <bin文件>")
        sys.exit(1)
    analyze_bin(sys.argv[1])
