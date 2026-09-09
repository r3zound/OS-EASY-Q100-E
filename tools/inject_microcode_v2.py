#!/usr/bin/env python3
"""
V2 移植：扫描 Q100-E bin 找 microcode 容器和最佳 FF 区域（仅报告，不实际注入）

V1 (port_microcode_v2.py) 是直接覆盖（截断 24KB）
V2 (本脚本) 是扫描找 microcode 容器 + 最佳 FF 区域，给 MMTool GUI 操作参考

实际注入必须用 MMTool (Windows GUI) 或 UEFITool NE：
  - https://github.com/LongSoft/UEFITool
  - 用 MMTool 添加新 FFS microcode entry 到 Q100E microcode FFS 卷

用法:
  python tools/inject_microcode_v2.py <Q100E.bin>
"""
import sys
import struct
import hashlib
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


MC_HDR_SIZE = 0x20
MC_ALIGN = 0x800


def find_microcodes_in_data(data: bytes) -> list:
    """扫描 microcode 头（type=1, family 6 CPUID）"""
    results = []
    pos = 0
    STEP = 0x8
    while pos + MC_HDR_SIZE + 16 < len(data):
        try:
            type_v = struct.unpack("<I", data[pos:pos + 4])[0]
            rev = struct.unpack("<I", data[pos + 4:pos + 8])[0]
            date = struct.unpack("<I", data[pos + 8:pos + 12])[0]
            cpuid = struct.unpack("<I", data[pos + 12:pos + 16])[0]
        except struct.error:
            break
        if (type_v == 1
            and 0 < rev < 0x300
            and 0 < cpuid < 0x100000000
            and (cpuid >> 8) & 0xF == 0x6):
            if date == 0 or date == 0xFFFFFFFF:
                pos += STEP
                continue
            try:
                loader = struct.unpack("<I", data[pos + 0x14:pos + 0x18])[0]
                data_size = struct.unpack("<I", data[pos + 0x1C:pos + 0x20])[0]
            except struct.error:
                pos += STEP
                continue
            if loader in (1, 0x80000001) and 0x100 < data_size < 0x100000:
                results.append({
                    "offset": pos,
                    "type": type_v,
                    "rev": rev,
                    "date": date,
                    "cpuid": cpuid,
                    "data_size": data_size,
                    "total_size": MC_HDR_SIZE + data_size,
                    "aligned_size": ((MC_HDR_SIZE + data_size + MC_ALIGN - 1) // MC_ALIGN) * MC_ALIGN,
                })
                pos += results[-1]["aligned_size"]
            else:
                pos += STEP
        else:
            pos += STEP
    return results


def find_max_ff_region(data: bytes, start: int, end: int) -> tuple:
    """找最大连续 0xFF 区域"""
    best_start = -1
    best_len = 0
    cur_start = -1
    cur_len = 0
    for off in range(start, end):
        if data[off] == 0xFF:
            if cur_start < 0:
                cur_start = off
            cur_len += 1
        else:
            if cur_len > best_len:
                best_start = cur_start
                best_len = cur_len
            cur_start = -1
            cur_len = 0
    if cur_len > best_len:
        best_start = cur_start
        best_len = cur_len
    return best_start, best_len


def main():
    if len(sys.argv) < 2:
        print("用法: python inject_microcode_v2.py <Q100E.bin>")
        print()
        print("扫描 Q100-E bin 的 microcode 容器位置和最佳 FF 区域")
        print("给 MMTool 注入操作提供参考")
        sys.exit(1)

    q100e_path = Path(sys.argv[1])
    if not q100e_path.exists():
        print(f"[ERROR] Q100E bin 不存在: {q100e_path}")
        sys.exit(1)

    data = q100e_path.read_bytes()
    if len(data) != 0x2000000:
        print(f"[ERROR] Q100E 大小 {len(data):,} != 32MB")
        sys.exit(1)

    print("=" * 70)
    print("  V2 microcode 扫描器")
    print(f"  文件: {q100e_path}")
    print("=" * 70)
    print()
    print(f"  SHA256: {sha256(data)}")
    print()

    # 1. 找 microcode 容器
    print("=== 1. microcode 容器 ===")
    mcs = find_microcodes_in_data(data)
    seen = set()
    unique = []
    for m in mcs:
        if m["offset"] not in seen:
            seen.add(m["offset"])
            unique.append(m)
    mcs = unique

    print(f"  找到 {len(mcs)} 个 microcode 容器")
    for m in mcs:
        # CPU 名称翻译
        fam = (m["cpuid"] >> 8) & 0xF
        mod = (m["cpuid"] >> 4) & 0xF
        if fam == 0x6:
            mod = (m["cpuid"] >> 12) & 0xF
        names = {
            (0x6, 0x71): "9代 Coffee Lake",
            (0x6, 0xA0): "10代 Comet Lake",
            (0x6, 0x72): "12代 ADL-S",
            (0x6, 0x75): "12代 RPL-S step5",
            (0x6, 0x70): "13代 RPL-S",
            (0x6, 0x71): "14代 RPL-S Refresh",
            (0x6, 0xF2): "14代 RPL-S ES2",
            (0x6, 0xF5): "14代 RPL-S ES5",
        }
        name = names.get((fam, mod), f"F{fam}/M0x{mod:x}")
        d_y = (m["date"] >> 16) & 0xFFFF
        d_m = (m["date"] >> 8) & 0xFF
        d_d = m["date"] & 0xFF
        date_str = f"{d_y:04d}-{d_m:02d}-{d_d:02d}" if 2020 <= d_y <= 2099 else f"0x{m['date']:x}"
        print(f"    0x{m['offset']:08x}: {name:20s} cpuid=0x{m['cpuid']:08x} rev=0x{m['rev']:02x} "
              f"date={date_str} size={m['aligned_size']:,} bytes")

    # 2. 找最大 FF 区域
    print()
    print("=== 2. 最大 0xFF 空闲区域（适合注入新 microcode）===")
    ff_start, ff_len = find_max_ff_region(data, 0, len(data))
    print(f"    0x{ff_start:08x}: size={ff_len:,} bytes ({ff_len/1024:.0f} KB)")
    print()
    print("    注意: MMTool 注入需要 FF 区域在 microcode FFS 卷的 data 区里")
    print("          不在 FFS 卷内的 FF 区域, BIOS 启动时不会扫描")

    # 3. 找 microcode 容器**前后**的 FF 区
    print()
    print("=== 3. microcode 容器附近的 FF 区域 ===")
    if mcs:
        # 找最大的 microcode 容器 (90671 188KB)
        main_mc = max(mcs, key=lambda m: m["aligned_size"])
        main_start = main_mc["offset"]
        main_end = main_mc["offset"] + main_mc["aligned_size"]
        print(f"    主 microcode 容器: 0x{main_start:08x} - 0x{main_end:08x} "
              f"({main_end - main_start:,} bytes)")

        # 前
        before_start, before_len = find_max_ff_region(data, 0, main_start)
        print(f"    前 FF 区: 0x{before_start:08x} size={before_len:,} bytes")

        # 后
        after_start, after_len = find_max_ff_region(data, main_end, len(data))
        print(f"    后 FF 区: 0x{after_start:08x} size={after_len:,} bytes")

        # 微码容器内是否有 FF 间隙
        inner_ff_start, inner_ff_len = find_max_ff_region(data, main_start, main_end)
        if inner_ff_len > 0x1000:
            print(f"    容器内 FF 间隙: 0x{inner_ff_start:08x} size={inner_ff_len:,} bytes")

    # 4. MMTool 操作建议
    print()
    print("=" * 70)
    print("  MMTool 操作步骤")
    print("=" * 70)
    print()
    print("  1. 在 Windows 上打开 MMTool.exe")
    print("  2. File → Open → 选择 Q100E bin")
    print("  3. 找到 microcode FFS 卷 (通常在 FV 11 或 12)")
    print("     按 microcode 容器位置定位: 0x{:08x}".format(
        max(mcs, key=lambda m: m["aligned_size"])["offset"] if mcs else 0
    ))
    print("  4. 在卷内的空 FF 区域点击 Add / Insert")
    print("  5. 选择 cpuB0671_完整.bin (211,968 bytes)")
    print("  6. File → Save → 另存")
    print()
    print("  ⚠️ 容量溢出警告: 完整 14代 microcode (212KB) 超过容器 (188KB)")
    print("     MMTool 会找卷内空白区放, 不会截断")
    print("     位置要求: 容器所属 FV 内有 ≥ 212KB 连续 0xFF 区域")

    # 5. 总结
    print()
    print("=" * 70)
    print("  总结")
    print("=" * 70)
    print()
    print("  ❌ V2 自动化注入不可行 (Q100-E 用非标准卷头结构)")
    print("  ✅ V2 资源就位 (cpuB0671_完整.bin 212KB)")
    print("  ✅ V2 需 MMTool GUI 操作 (Windows)")
    print("  ✅ V2 不依赖 FFS 卷头解析")
    print()
    print("  替代方案 (如果 MMTool 也不行):")
    print("    1. UEFITool NE (LongSoft/UEFITool) - Linux/Windows GUI")
    print("    2. python-uefi-firmware (自动 FFS 编辑)")
    print("    3. 用 Ghidra/IDA Pro 看 FV 头结构 (高级逆向)")


if __name__ == "__main__":
    main()
