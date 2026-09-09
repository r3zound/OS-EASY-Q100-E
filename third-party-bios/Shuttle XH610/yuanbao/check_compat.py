#!/usr/bin/env python3
"""
微码卷兼容性预检脚本
====================
功能：检查 XH610 与 JHS65F BIOS 镜像的基本兼容性，判断微码注入是否可行。

使用方法（在本地 Windows / Linux 环境运行）：
    python check_compat.py <XH610.bin> <JHS65F.bin>

注意：本脚本仅做**结构级**预检（大小、FFS、微码卷特征）。
真正的微码提取与注入需用 MCExtractor + MMTOOL 完成。
"""

import sys

# AMI Aptio UEFI 常见签名
FFS_GUID_MICROCODE_VOL = b"\xDE\x9B\x4A\x43"  # 微码卷常见 GUID 前缀（示意）
FFS2_MAGIC = b"_FVH"  # FFS2 卷头
CAPSULE_MAGIC = b"\x00\x00\x00\x00\x00\x00\x00\x00"


def analyze(path):
    print(f"\n{'='*60}")
    print(f"分析: {path}")
    print(f"{'='*60}")
    try:
        with open(path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print("  [错误] 文件不存在")
        return None

    size = len(data)
    print(f"  文件大小: {size} 字节 ({size/1024/1024:.2f} MB)")
    print(f"  大小是否为 32MB (33554432): {'是 ✅' if size == 32*1024*1024 else '否 ⚠️'}")

    # 检查是否为 AMI/UEFI 镜像（查找常见字符串）
    has_ami = b"AMI" in data or b"American Megatrends" in data
    has_uefi = b"_FVH" in data
    print(f"  AMI 特征: {'是 ✅' if has_ami else '否 ⚠️'}")
    print(f"  UEFI FV 特征: {'是 ✅' if has_uefi else '否 ⚠️'}")

    # 查找微码卷 GUID 特征（示意：搜索 FFS2 卷头数量）
    fvh_count = data.count(FFS2_MAGIC)
    print(f"  FFS2 卷(_FVH)数量: {fvh_count}")

    # 查找 14 代微码 rev 0x12B 特征（小端: 2B 01 00 00）
    rev_12b_le = b"\x2B\x01\x00\x00"
    count_12b = data.count(rev_12b_le)
    print(f"  rev 0x12B (14代稳定版) 出现次数: {count_12b} "
          f"{'✅ 含14代微码' if count_12b > 0 else '⚠️ 未检测到'}")

    # 12 代常见 rev 0x2C/0x30
    rev_2c = data.count(b"\x2C\x00\x00\x00")
    rev_30 = data.count(b"\x30\x00\x00\x00")
    print(f"  12代 rev 0x2C/0x30 出现次数: {rev_2c} / {rev_30}")

    return {
        "size": size,
        "has_ami": has_ami,
        "has_uefi": has_uefi,
        "count_12b": count_12b,
    }


def main():
    if len(sys.argv) < 3:
        print("用法: python check_compat.py <XH610.bin> <JHS65F.bin>")
        sys.exit(1)

    xh = analyze(sys.argv[1])
    jh = analyze(sys.argv[2])

    if not xh or not jh:
        sys.exit(1)

    print(f"\n{'='*60}")
    print("兼容性判定")
    print(f"{'='*60}")

    # 判定 1：大小一致
    if xh["size"] == jh["size"]:
        print("[✅] 两份镜像大小一致 → 微码卷空间布局兼容概率高")
    else:
        print("[⚠️] 两份镜像大小不一致 → 注入前需手动调整卷大小，风险较高")

    # 判定 2：均为 AMI UEFI
    if xh["has_ami"] and jh["has_ami"] and xh["has_uefi"] and jh["has_uefi"]:
        print("[✅] 两份均为 AMI Aptio UEFI → 可用 MMTOOL 处理")
    else:
        print("[⚠️] 至少有一份非标准 AMI UEFI，需谨慎")

    # 判定 3：源含 14 代、目标缺 14 代
    if xh["count_12b"] > 0 and jh["count_12b"] == 0:
        print("[✅] XH610 含 0x12B，JHS65F 缺 0x12B → 注入有明确收益")
    elif xh["count_12b"] > 0 and jh["count_12b"] > 0:
        print("[ℹ️] 两份均含 0x12B → JHS65F 已支持 14 代，无需注入")
    else:
        print("[⚠️] XH610 未检测到 0x12B → 提取源不足，需换源")

    print("\n建议：以上仅为结构预检。请务必再用 MCExtractor 精确扫描确认。")


if __name__ == "__main__":
    main()
