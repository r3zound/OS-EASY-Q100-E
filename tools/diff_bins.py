#!/usr/bin/env python3
"""
完整 diff 两个 BIOS bin：找出改了什么区段
输出：变更区间列表 + 每段 hash + 推测含义
"""
import sys
import struct
import hashlib
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def find_changed_regions(bin_a: bytes, bin_b: bytes, min_block: int = 0x1000):
    """找出 bin_a vs bin_b 改动的所有区段（4KB 块粒度）"""
    if len(bin_a) != len(bin_b):
        print(f"⚠️  大小不同: {len(bin_a)} vs {len(bin_b)}")
        return []

    size = len(bin_a)
    changed = []
    in_change = False
    start = 0
    same_count = 0

    for off in range(0, size, min_block):
        end = min(off + min_block, size)
        if bin_a[off:end] != bin_b[off:end]:
            if not in_change:
                start = off
                in_change = True
            same_count = 0
        else:
            if in_change:
                same_count += min_block
                if same_count >= min_block * 4:  # 4 块连续相同才结束
                    changed.append((start, off + min_block - same_count))
                    in_change = False
                    same_count = 0
    if in_change:
        changed.append((start, size))

    return changed


def analyze_region(data_a: bytes, data_b: bytes, off: int, end: int):
    """分析一段区间的变更，输出 hash + 头部 hex + 推测"""
    block_a = data_a[off:end]
    block_b = data_b[off:end]
    h_a = hashlib.sha256(block_a).hexdigest()[:16]
    h_b = hashlib.sha256(block_b).hexdigest()[:16]

    size = end - off
    print(f"\n  0x{off:08x} - 0x{end:08x} ({size} bytes, {size/1024:.1f} KB)")
    print(f"    SHA256: {h_a}... → {h_b}...")

    # 头部 hex
    if size <= 0x200:
        head_a = " ".join(f"{b:02x}" for b in block_a[:32])
        head_b = " ".join(f"{b:02x}" for b in block_b[:32])
        print(f"    HEAD A: {head_a}")
        print(f"    HEAD B: {head_b}")
    else:
        head_a = " ".join(f"{b:02x}" for b in block_a[:32])
        head_b = " ".join(f"{b:02x}" for b in block_b[:32])
        print(f"    HEAD A: {head_a}")
        print(f"    HEAD B: {head_b}")

    # 推测含义
    if off < 0x1000:
        print(f"    推测: Flash Descriptor 区（OEM 头 + FD 元数据）")
    elif off >= 0x1A0000 and off < 0x1AC000:
        print(f"    推测: ME 区域（{size//1024} KB）")
    elif off >= 0x23000 and off < 0x3A000:
        print(f"    推测: ME PMCP 容器（microcode 容器）")
    elif off >= 0x60000 and off < 0x170000:
        print(f"    推测: BIOS region 主体（含 Setup / IFR / 各种 driver）")
    else:
        print(f"    推测: 未知区段（待分析）")

    # 找 ASCII 字符串
    printable_a = []
    cur = b""
    for b in block_a:
        if 32 <= b < 127:
            cur += bytes([b])
        else:
            if len(cur) >= 8:
                printable_a.append(cur.decode("latin-1"))
            cur = b""
    if len(cur) >= 8:
        printable_a.append(cur.decode("latin-1"))

    printable_b = []
    cur = b""
    for b in block_b:
        if 32 <= b < 127:
            cur += bytes([b])
        else:
            if len(cur) >= 8:
                printable_b.append(cur.decode("latin-1"))
            cur = b""
    if len(cur) >= 8:
        printable_b.append(cur.decode("latin-1"))

    # 比较字符串差异
    set_a = set(printable_a)
    set_b = set(printable_b)
    only_a = set_a - set_b
    only_b = set_b - set_a
    if only_a:
        print(f"    A-only 字符串: {list(only_a)[:5]}")
    if only_b:
        print(f"    B-only 字符串: {list(only_b)[:5]}")


def main():
    if len(sys.argv) < 3:
        print("用法: python diff_bins.py <bin1> <bin2>")
        sys.exit(1)

    p_a = Path(sys.argv[1])
    p_b = Path(sys.argv[2])
    if not p_a.exists() or not p_b.exists():
        print("文件不存在")
        sys.exit(1)

    bin_a = p_a.read_bytes()
    bin_b = p_b.read_bytes()

    print(f"A: {p_a}")
    print(f"   SHA256: {hashlib.sha256(bin_a).hexdigest()}")
    print(f"   MD5:    {hashlib.md5(bin_a).hexdigest()}")
    print(f"   CRC32:  {hashlib.sha256(bin_a).hexdigest()[:8]}")
    print()
    print(f"B: {p_b}")
    print(f"   SHA256: {hashlib.sha256(bin_b).hexdigest()}")
    print(f"   MD5:    {hashlib.md5(bin_b).hexdigest()}")
    print(f"   CRC32:  {hashlib.sha256(bin_b).hexdigest()[:8]}")
    print()

    changed = find_changed_regions(bin_a, bin_b)
    if not changed:
        print("✅ 两个文件完全一致")
        return

    print(f"=== 变更区段（共 {len(changed)} 段）===")
    total_changed = 0
    for off, end in changed:
        analyze_region(bin_a, bin_b, off, end)
        total_changed += end - off

    print(f"\n=== 汇总 ===")
    print(f"  总变更区段: {len(changed)}")
    print(f"  变更总字节: {total_changed} ({total_changed/1024:.1f} KB)")
    print(f"  占总大小:   {total_changed/len(bin_a)*100:.2f}%")


if __name__ == "__main__":
    main()
