#!/usr/bin/env python3
"""
手动扫描：
1. microcode 文件 (用 EFI microcode GUID D2A78CE0-521B-0D4F-9297-3BC2E38DF9DC)
2. FFS volume header (_FVH)
3. Setup IFR 字符串
"""
import sys
import struct
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    if len(sys.argv) < 2:
        print("用法: python find_mc_ifr.py <bin>")
        sys.exit(1)

    data = Path(sys.argv[1]).read_bytes()
    print(f"=== {sys.argv[1]} ===\n")

    # 1. FFS Volume Header _FVH
    print("=== FFS Volume Header (_FVH) ===")
    fvh_pos = 0
    fvh_count = 0
    while True:
        fvh_pos = data.find(b"_FVH", fvh_pos)
        if fvh_pos < 0: break
        fvh_count += 1
        # 显示 FVH 头部
        head = " ".join(f"{b:02x}" for b in data[fvh_pos:fvh_pos+48])
        # 找 FFS Guid
        guid = data[fvh_pos+0x10:fvh_pos+0x20].hex()
        print(f"  [{fvh_count:2d}] 0x{fvh_pos:08x}  guid={guid}")
        if fvh_count >= 30:
            print(f"  ... (truncated)")
            break
        fvh_pos += 4

    # 2. EFI microcode 文件 GUID
    print()
    print("=== EFI Microcode 文件 GUID (D2A78CE0-521B-0D4F-9297-3BC2E38DF9DC) ===")
    UCODE_GUID = bytes.fromhex("D2A78CE0521B0D4F92973BC2E38DF9DC")
    pos = 0
    count = 0
    while True:
        pos = data.find(UCODE_GUID, pos)
        if pos < 0: break
        count += 1
        print(f"  [{count}] 0x{pos:08x}: GUID match")
        # FFS header 0x12 type, 0x18 size
        if pos + 0x20 > len(data): break
        ftype = data[pos + 0x12]
        fsize = struct.unpack("<I", data[pos + 0x18:pos + 0x1C])[0]
        # FFS 之后是 file body (offset 0x18, 24 字节头)
        if ftype == 0x01 and 0x800 <= fsize <= 0x4000:
            print(f"        -> FFS microcode file (type=0x{ftype:02x}, size=0x{fsize:x})")
        else:
            print(f"        -> 命中但 ftype=0x{ftype:02x}, size=0x{fsize:x}（不像是 microcode）")
        pos += 4
    print(f"  共 {count} 个匹配")

    # 3. 搜 microcode 头模式（绕过 GUID，直接找 microcode 数据）
    print()
    print("=== microcode 数据头扫描 (不限 GUID) ===")
    print("特征: offset[0x0C]=version(0xB7+), [0x10]=1, [0x1C]=date, [0x14]=CPUID\n")

    candidates = []
    for i in range(0, len(data) - 0x30, 0x10):
        ucode_ver = struct.unpack("<I", data[i + 0x0C:i + 0x10])[0]
        rev_id = struct.unpack("<I", data[i + 0x10:i + 0x14])[0]
        ucode_date = struct.unpack("<I", data[i + 0x1C:i + 0x20])[0]
        cpuid = struct.unpack("<I", data[i + 0x14:i + 0x18])[0]

        # 严格匹配
        if (0 < ucode_ver < 0x300
            and rev_id == 1
            and 0 < ucode_date < 0x300000
            and 0 < cpuid < 0x100000000
            and (cpuid & 0xF000) == 0x0000  # Family 6 (low 12 bits, simplified)
            and ucode_ver > 0x10  # 版本至少 0x11 避免 noise
        ):
            d = ucode_date
            date = f"{(d>>16)&0xffff:04d}-{(d>>8)&0xff:02d}-{d&0xff:02d}"
            fam = (cpuid >> 8) & 0xF
            if fam == 0xF: fam += (cpuid >> 20) & 0xFF
            mod = (cpuid >> 4) & 0xF
            if fam in (0x6, 0xF): mod += (cpuid >> 12) & 0xF0
            candidates.append((i, ucode_ver, cpuid, fam, mod, date))

    # 去重
    seen = set()
    unique = []
    for c in candidates:
        if c[0] not in seen:
            seen.add(c[0])
            unique.append(c)

    print(f"找到 {len(unique)} 个候选 microcode 容器\n")
    if unique:
        print(f"  {'#':>3s}  {'偏移':>10s}  {'版本':>6s}  {'日期':>12s}  {'CPUID':>10s}  {'F/M':>10s}  代号")
        print(f"  {'-'*3}  {'-'*10}  {'-'*6}  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*30}")
        names = {
            (0x6, 0x97): "ADL-S (12代)", (0x6, 0x9E): "KBL (7代)",
            (0x6, 0x9F): "CFL (8/9代)", (0x6, 0xA5): "CML (10代)",
            (0x6, 0xB7): "RPL-S (13代)", (0x6, 0xBA): "RPL-P",
            (0x6, 0xBF): "RPL-R (14代) ⭐",
            (0x6, 0xAA): "MTL", (0x6, 0xAC): "MTL",
        }
        for idx, (off, ver, cpuid, fam, mod, date) in enumerate(unique, 1):
            nm = names.get((fam, mod), "")
            fm = f"F{fam}/M0x{mod:x}"
            print(f"  {idx:>3d}  0x{off:08x}  0x{ver:02x}    {date:>12s}  0x{cpuid:08x}  {fm:>10s}  {nm}")

    # 4. 电源管理 / Setup 关键词
    print()
    print("=== 电源管理 / Setup 关键词扫描 ===")
    keywords = [
        (b"Hyper-Threading", "超线程"),
        (b"HyperThreading", "超线程 (无连字符)"),
        (b"Hyper Threading", "超线程 (带空格)"),
        (b"C-State", "C-State"),
        (b"PL1 Power Limit", "PL1 短时功耗"),
        (b"PL2 Power Limit", "PL2 长时功耗"),
        (b"PL4", "PL4 峰值功耗"),
        (b"ICCMAX", "ICCmax 电流"),
        (b"IccMax", "ICCmax 电流"),
        (b"Power Limit", "Power Limit"),
        (b"Current Limit", "Current Limit"),
        (b"Turbo Boost", "Turbo Boost"),
        (b"Boot Guard", "Boot Guard"),
        (b"SecureBoot", "Secure Boot"),
        (b"Intel TXT", "TXT"),
        (b"VT-d", "VT-d"),
        (b"VMX", "VMX (VT-x)"),
        (b"AC Power Loss", "AC 掉电恢复"),
        (b"After Power Loss", "AC 掉电恢复"),
        (b"HyperThreading", "HT"),
        (b"MultiThreading", "MT"),
        (b"PowerOn", "上电"),
        (b"Wake on", "Wake on"),
        (b"Auto Wake", "自动唤醒"),
    ]
    for kw, desc in keywords:
        pos = 0
        cnt = 0
        first = -1
        while True:
            pos = data.find(kw, pos)
            if pos < 0: break
            if first < 0: first = pos
            cnt += 1
            pos += 1
        if cnt > 0:
            print(f"  '{kw.decode('latin-1', errors='replace')}' ({desc}): {cnt} 个匹配, 首在 0x{first:08x}")


if __name__ == "__main__":
    main()
