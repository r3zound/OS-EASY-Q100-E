#!/usr/bin/env python3
"""
Q100-E 14代 microcode 移植脚本 v2

基于 microcode 头直接扫描（不靠 FFS GUID）
Q100-E 和 Shuttle XH610 的 microcode 容器都是直接 microcode 头格式（无 FFS wrapper）

用法:
  python port_microcode_v2.py <参考BIOS.bin> <Q100E.bin> <输出.bin>
"""
import sys
import struct
import hashlib
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# microcode 头常量
MC_HDR_SIZE = 0x20  # 32 字节 microcode 头
MC_ALIGN = 0x800   # microcode 容器对齐 (2KB)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def find_microcodes_in_data(data: bytes, base: int = 0, end: int = None) -> list:
    """在 data 中找所有 microcode 头

    重要: microcode 容器在 BIOS 镜像里可能不是 0x10 对齐 (Q100-E 90671 在 0x1D90D18, 0x1D90D18 % 0x10 = 8)
    必须用 0x8 步进扫描, 然后用 aligned_size 跳过整个 microcode 块

    返回: [{offset, cpuid, date, total_size, data_size, ...}, ...]
    """
    if end is None:
        end = len(data)
    results = []
    pos = 0
    STEP = 0x8  # 0x8 步进 (兼容 0x8 / 0x10 / 0x800 / 0x1000 对齐)
    while pos + MC_HDR_SIZE + 16 < end:
        try:
            type_v = struct.unpack("<I", data[pos:pos + 4])[0]
            rev = struct.unpack("<I", data[pos + 4:pos + 8])[0]
            date = struct.unpack("<I", data[pos + 8:pos + 12])[0]
            cpuid = struct.unpack("<I", data[pos + 12:pos + 16])[0]
        except struct.error:
            break
        # microcode 头检查
        if (type_v == 1
            and 0 < rev < 0x300
            and 0 < cpuid < 0x100000000
            and (cpuid >> 8) & 0xF == 0x6):  # Intel family 6
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
                d_y = (date >> 16) & 0xFFFF
                d_m = (date >> 8) & 0xFF
                d_d = date & 0xFF
                date_str = f"{d_y:04d}-{d_m:02d}-{d_d:02d}" if 2020 <= d_y <= 2099 else f"0x{date:x}"
                results.append({
                    "offset": base + pos,
                    "abs_offset": pos,
                    "type": type_v,
                    "revision": f"0x{rev:02x}",
                    "date_int": date,
                    "date": date_str,
                    "cpuid_int": cpuid,
                    "cpuid": f"0x{cpuid:08x}",
                    "data_size": data_size,
                    "total_size": MC_HDR_SIZE + data_size,
                    "aligned_size": ((MC_HDR_SIZE + data_size + MC_ALIGN - 1) // MC_ALIGN) * MC_ALIGN,
                })
                pos += results[-1]["aligned_size"]  # 跳到 microcode 末尾
            else:
                pos += STEP
        else:
            pos += STEP
    return results


def main():
    if len(sys.argv) < 4:
        print("用法: python port_microcode_v2.py <参考BIOS.bin> <Q100E.bin> <输出.bin>")
        print()
        print("例: python port_microcode_v2.py \\")
        print("    'third-party-bios/Shuttle XH610/XH610000.211 (Asia)/shell/XH610000.211.bin' \\")
        print("    third-party-bios/bios_2改...bin \\")
        print("    /tmp/Q100E_with_14th.bin")
        print()
        print("特性:")
        print("  - 直接扫 microcode 头（不靠 FFS GUID）")
        print("  - 提取参考 BIOS 的 12/13/14 代 microcode")
        print("  - 替换到 Q100-E microcode 容器")
        print("  - 报告大小溢出警告")
        sys.exit(1)

    ref_path = Path(sys.argv[1])
    q100e_path = Path(sys.argv[2])
    out_path = Path(sys.argv[3])

    if not ref_path.exists():
        print(f"[ERROR] 参考 BIOS 不存在: {ref_path}")
        sys.exit(1)
    if not q100e_path.exists():
        print(f"[ERROR] Q100-E BIOS 不存在: {q100e_path}")
        sys.exit(1)

    print("=" * 70)
    print("  Q100-E 14代 microcode 移植工具 v2")
    print("=" * 70)
    print(f"  参考 BIOS:  {ref_path} ({ref_path.stat().st_size:,} bytes)")
    print(f"  Q100-E BIOS: {q100e_path} ({q100e_path.stat().st_size:,} bytes)")
    print(f"  输出:     {out_path}")
    print()

    ref_data = ref_path.read_bytes()
    q100e_data = bytearray(q100e_path.read_bytes())

    if len(ref_data) != 0x2000000:
        print(f"[WARN] 参考 BIOS 大小 {len(ref_data):,} != 32MB")
    if len(q100e_data) != 0x2000000:
        print(f"[ERROR] Q100-E BIOS 大小 {len(q100e_data):,} != 32MB")
        sys.exit(1)

    print("=== 1. SHA256 ===")
    print(f"  参考 BIOS:  {sha256(ref_data)}")
    print(f"  Q100-E BIOS: {sha256(bytes(q100e_data))}")
    print()

    # 1. 找参考 BIOS 的 microcode
    print("=== 2. 参考 BIOS microcode 列表 ===")
    ref_mcs = find_microcodes_in_data(ref_data)
    if not ref_mcs:
        print("  [WARN] 参考 BIOS 没找到 microcode, 试 microcode 容器位置...")
        # 试常见位置: 0x1D91000, 0x1DCB000
        for pos in [0x1D91000, 0x1DCB000, 0x1E05000, 0x1E91000, 0x1ECB000, 0x1F05000]:
            mcs = find_microcodes_in_data(ref_data, base=0, end=pos + 0x40000)
            ref_mcs.extend(mcs)
    # 去重 (按 offset)
    seen = set()
    unique_ref = []
    for m in ref_mcs:
        if m["offset"] not in seen:
            seen.add(m["offset"])
            unique_ref.append(m)
    ref_mcs = unique_ref

    print(f"  找到 {len(ref_mcs)} 个 microcode 容器")
    for m in ref_mcs:
        print(f"    0x{m['offset']:08x}: CPUID {m['cpuid']} rev={m['revision']} "
              f"date={m['date']} size={m['aligned_size']:,} bytes "
              f"(data={m['data_size']:,})")

    # 2. 检查 14 代 microcode
    print()
    print("=== 3. 14代 microcode 检查 ===")
    target_cpuid = 0x000B0671  # 14代 RPL-S Refresh (i5-14400)
    target_14th = [m for m in ref_mcs if m["cpuid_int"] == target_cpuid]
    if not target_14th:
        print(f"  [WARN] 参考 BIOS 没含 CPUID 0x{target_cpuid:08x} (14代 RPL-S Refresh)")
        # 试其他 14 代 CPUID
        alt_cpids = [0x000B0670, 0x00090675, 0x000B06F2, 0x000B06F5]
        for cpuid in alt_cpids:
            alt = [m for m in ref_mcs if m["cpuid_int"] == cpuid]
            if alt:
                print(f"  找到 alt 14代 microcode: {hex(cpuid)}")
                target_14th = alt
                break
    if not target_14th:
        print(f"  [ERROR] 参考 BIOS 完全没 14 代 microcode, 移植无效")
        sys.exit(1)
    print(f"  ✅ 找到 14代 microcode: {len(target_14th)} 个副本")
    for t in target_14th:
        print(f"    0x{t['offset']:08x}: CPUID {t['cpuid']} rev={t['revision']} "
              f"size={t['aligned_size']:,} bytes (data={t['data_size']:,})")

    # 选最后一个副本（通常最新）
    target_mc = target_14th[-1]
    print(f"\n  使用 microcode @ 0x{target_mc['offset']:08x}")

    # 3. 找 Q100-E 的 microcode 容器
    print()
    print("=== 4. Q100-E microcode 容器 ===")
    q100e_mcs = find_microcodes_in_data(q100e_data)
    seen = set()
    unique_q = []
    for m in q100e_mcs:
        if m["offset"] not in seen:
            seen.add(m["offset"])
            unique_q.append(m)
    q100e_mcs = unique_q

    print(f"  找到 {len(q100e_mcs)} 个 microcode 容器")
    for m in q100e_mcs:
        print(f"    0x{m['offset']:08x}: CPUID {m['cpuid']} rev={m['revision']} "
              f"date={m['date']} size={m['aligned_size']:,} bytes (data={m['data_size']:,})")

    # 4. 替换
    print()
    print("=== 5. 替换 microcode ===")
    if not q100e_mcs:
        print("  [ERROR] Q100-E 没找到 microcode 容器")
        sys.exit(1)

    src_mc = target_mc  # 参考 BIOS 的 14代 microcode
    src_data = ref_data[src_mc["offset"]:src_mc["offset"] + src_mc["aligned_size"]]

    # 找一个 Q100-E microcode 容器来替换
    # 优先选最大的 90671 容器 (这是 BIOS region 实际放 EFI microcode 文件的地方)
    # 通常 90671 + 906A0 在 188KB 容器, 是最大那个
    target_container = max(q100e_mcs, key=lambda m: m["aligned_size"])
    tgt_off = target_container["offset"]
    tgt_size = target_container["aligned_size"]

    print(f"  目标容器: 0x{tgt_off:08x} (size {tgt_size:,})")
    print(f"  源 microcode: 0x{src_mc['offset']:08x} (size {src_mc['aligned_size']:,})")
    print(f"  源 CPUID:    {src_mc['cpuid']} (14代 RPL-S Refresh)")

    if src_mc["aligned_size"] > tgt_size:
        diff = src_mc["aligned_size"] - tgt_size
        print(f"\n  ⚠️ 源 microcode ({src_mc['aligned_size']:,}) 比目标容器 ({tgt_size:,}) 大 {diff:,} bytes!")
        print(f"  策略: 截断后写入 (会丢失 microcode 末尾 {diff:,} bytes)")
        print(f"  风险: i5-14400 可能仍能跑 (靠 CPU 内置 fallback), 但缺部分修复")
    else:
        print(f"\n  源 microcode 比目标容器小, 完美替换")

    # 写入
    bytes_to_write = min(src_mc["aligned_size"], tgt_size)
    src_bytes = ref_data[src_mc["offset"]:src_mc["offset"] + bytes_to_write]
    for i in range(bytes_to_write):
        q100e_data[tgt_off + i] = src_bytes[i]
    # 剩余用 0xFF 填充
    if bytes_to_write < tgt_size:
        for i in range(bytes_to_write, tgt_size):
            q100e_data[tgt_off + i] = 0xFF
    print(f"  写入 {bytes_to_write:,} bytes @ 0x{tgt_off:08x}")
    if bytes_to_write < tgt_size:
        print(f"  剩余 {tgt_size - bytes_to_write:,} bytes 填 0xFF")

    # 5. 写输出
    out_path.write_bytes(bytes(q100e_data))
    print()
    print("=" * 70)
    print("  完成")
    print("=" * 70)
    print(f"  输出文件: {out_path}")
    print(f"  大小:     {out_path.stat().st_size:,} bytes")
    print(f"  SHA256:   {sha256(bytes(q100e_data))}")
    print()
    print("  移植内容:")
    print(f"    Q100-E 位置 0x{tgt_off:08x} 的 microcode")
    print(f"    CPUID {target_container['cpuid']} (rev {target_container['revision']}, {target_container['date']})")
    print(f"  → 替换为:")
    print(f"    CPUID {src_mc['cpuid']} (rev {src_mc['revision']}, {src_mc['date']})")
    print()
    print("  ⚠️ 下一步 (CH341A 写回流程):")
    print("  1. 用 NeoProgrammer 验证新 bin 的 microcode 区域")
    print("  2. CH341A 烧写新 bin 到 SPI flash")
    print("  3. 装 i5-14400 测试")
    print("  4. 如果不亮, 烧回备份救回")
    print()
    print("  推荐先打电话 4001-027-580 看能否拿到原厂 12 代+ BIOS (最稳)")


if __name__ == "__main__":
    main()
