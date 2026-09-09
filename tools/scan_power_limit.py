#!/usr/bin/env python3
"""
扫描 V1 BIOS 里的功耗墙相关设置 (PL1/PL2/PL4/TDP/Power Limit)

目标：找到限制 60W 的功耗墙位置，为 AMIBCP 解锁做准备
"""
import sys
import struct
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def find_ascii_strings(data, min_len=6):
    """提取 ASCII 字符串"""
    results = []
    cur = b""
    cur_off = 0
    for i, b in enumerate(data):
        if 32 <= b < 127:
            if not cur:
                cur_off = i
            cur += bytes([b])
        else:
            if len(cur) >= min_len:
                results.append((cur_off, cur.decode("ascii", errors="replace")))
            cur = b""
    if len(cur) >= min_len:
        results.append((cur_off, cur.decode("ascii", errors="replace")))
    return results


def find_unicode_strings(data, min_len=6):
    """提取 UTF-16LE 字符串"""
    results = []
    cur = ""
    cur_off = 0
    i = 0
    while i + 1 < len(data):
        c = struct.unpack("<H", data[i:i + 2])[0]
        if 32 <= c < 127:
            if not cur:
                cur_off = i
            cur += chr(c)
            i += 2
        else:
            if len(cur) >= min_len:
                results.append((cur_off, cur))
            cur = ""
            i += 2
    if len(cur) >= min_len:
        results.append((cur_off, cur))
    return results


def main():
    if len(sys.argv) < 2:
        print("用法: python scan_power_limit.py <32MB.bin>")
        sys.exit(1)

    bin_path = Path(sys.argv[1])
    data = bin_path.read_bytes()
    print(f"=== {bin_path.name} ===\n大小: {len(data):,} bytes\n")

    # 功耗墙关键词
    keywords = [
        "Power Limit", "PowerLimit", "PL1", "PL2", "PL3", "PL4",
        "Package Power", "TDP", "tdp", "Turbo Power", "TurboBoost",
        "Power Management", "PowerMgmt", "CpuPower", "CPU Power",
        "Current Limit", "IccMax", "ICC Max", "PowerLimit1",
        "Long Duration", "Short Duration", "Turbo Mode",
        "PowerMax", "Tau", "Power Limit 1", "Power Limit 2",
        "PPT", "MaxPower", "PowerLimit2",
    ]

    print("=== 功耗墙相关 ASCII 字符串 ===")
    ascii_strings = find_ascii_strings(data)
    print(f"  总 ASCII 字符串: {len(ascii_strings)}")
    ascii_hits = []
    for off, s in ascii_strings:
        for kw in keywords:
            if kw.lower() in s.lower():
                ascii_hits.append((off, s))
                break
    print(f"  功耗墙相关: {len(ascii_hits)} 个\n")
    for off, s in ascii_hits[:40]:
        print(f"  0x{off:08x}: {s[:100]}")

    print("\n=== 功耗墙相关 Unicode 字符串 ===")
    uni_strings = find_unicode_strings(data)
    print(f"  总 Unicode 字符串: {len(uni_strings)}")
    uni_hits = []
    for off, s in uni_strings:
        for kw in keywords:
            if kw.lower() in s.lower():
                uni_hits.append((off, s))
                break
    print(f"  功耗墙相关: {len(uni_hits)} 个\n")
    for off, s in uni_hits[:40]:
        print(f"  0x{off:08x}: {s[:100]}")

    # 找 60W / 65W / 148W 等功耗值 (毫瓦单位)
    print("\n=== 功耗值扫描 (60W/65W/148W 等, 毫瓦单位) ===")
    # 60W = 60000 mW = 0xEA60 (LE: 60 EA 00 00)
    # 65W = 65000 mW = 0xFDE8 (LE: E8 FD 00 00)
    # 148W = 148000 mW = 0x24220 (LE: 20 42 02 00)
    # 120W = 120000 mW = 0x1D4C0 (LE: C0 D4 01 00)
    power_values = {
        60000: "60W (0xEA60)",
        65000: "65W (0xFDE8)",
        95000: "95W",
        120000: "120W",
        125000: "125W",
        148000: "148W (i5-14400 MTP)",
        253000: "253W",
    }
    for val, label in power_values.items():
        le = struct.pack("<I", val)
        # 在全 bin 找这个值
        count = 0
        first = -1
        pos = 0
        while True:
            pos = data.find(le, pos)
            if pos < 0:
                break
            if first < 0:
                first = pos
            count += 1
            pos += 4
        if count > 0:
            print(f"  {label}: {count} 个, 首在 0x{first:08x}")

    # 找 CpuSetup 变量结构
    print("\n=== CpuSetup / PowerLimit 变量名 ===")
    for var in ["CpuSetup", "PowerLimit", "PkgPower", "CpuPowerMgmt", "TurboPowerLimit"]:
        pos = 0
        cnt = 0
        first = -1
        while True:
            pos = data.find(var.encode("ascii"), pos)
            if pos < 0:
                break
            if first < 0:
                first = pos
            cnt += 1
            pos += 1
        if cnt:
            print(f"  {var}: {cnt} 个, 首在 0x{first:08x}")


if __name__ == "__main__":
    main()
