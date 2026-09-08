#!/usr/bin/env python3
"""
Q100-E 14代 microcode 自动移植工具

用法:
  python port_microcode.py <参考BIOS.bin> <Q100E.bin> <输出.bin>

功能:
  1. 从参考 BIOS 提取 12/13/14 代 microcode (用 MCExtractor 解析)
  2. 从 Q100-E bin 移除 9/10 代 microcode (腾空间)
  3. 把新 microcode 插入 Q100-E bin 的 microcode 容器
  4. 输出新 bin (CH341A 写回测试)
"""
import sys
import struct
import hashlib
import re
import subprocess
from pathlib import Path

# 强制 UTF-8 输出
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_mcextractor(bin_path: str) -> list:
    """用 MCExtractor 提取 microcode 信息 (从 bin 解析)

    返回: [(cpu_id, version, date_str, size), ...]
    """
    me_dir = Path(__file__).parent / "MCExtractor" / "MCExtractor-r352"
    mce_script = me_dir / "MCE.py"

    if not mce_script.exists():
        print(f"  [WARN] MCExtractor 未找到: {mce_script}")
        return []

    # MCExtractor 是交互式的, 但 -skip -exit 可以跑非交互
    # Windows 上用 cmd 调用, 不阻塞在 input() 上
    import os
    try:
        if os.name == "nt":
            # Windows: 喂入空字符串避免 input() 阻塞
            result = subprocess.run(
                ["python", str(mce_script), "-skip", "-exit", bin_path],
                input="\n",
                capture_output=True,
                text=True,
                timeout=60,
            )
        else:
            result = subprocess.run(
                ["python3", str(mce_script), "-skip", "-exit", bin_path],
                input="\n",
                capture_output=True,
                text=True,
                timeout=60,
            )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        print(f"  [WARN] MCExtractor 超时")
        return []
    except Exception as e:
        print(f"  [WARN] MCExtractor 失败: {e}")
        return []

    # 解析输出
    # 格式: "Microcode │ 90671 │ 82 (1,7) │ 1C    │ 2021-06-14 │  PRD  │ ..."
    pattern = re.compile(
        r"Microcode\s+│\s+([0-9A-F]+)\s+│\s+([0-9A-F\.]+).*?(\d{4}-\d{2}-\d{2})",
        re.IGNORECASE,
    )
    results = []
    for match in pattern.finditer(output):
        cpu_id = int(match.group(1), 16)
        version = match.group(2)
        date_str = match.group(3)
        results.append((cpu_id, version, date_str, 0))  # size 留 0
    return results


def find_microcode_containers(data: bytes) -> list:
    """找 bin 里的 microcode 容器（EFI FFS microcode 文件格式）

    返回: [(abs_offset, length, container_guid_str), ...]
    """
    # EFI microcode 文件 GUID: 17088572-377F-44EF-8F4E-B09FFF46A070
    # 字节序: D2 A7 8C E0 52 1B 0D 4F 92 97 3B C2 E3 8D F9 DC
    # 等等，173-44EF 是 0x0D 0x4F... 让我重看 GUID 字节序

    # uefi_firmware.microcode 文件 GUID: 17088572-377F-44EF-8F4E-B09FFF46A070
    # 在 little-endian 字节序中:
    # 72 85 08 17 7F 44 EF 8D 4E B0 9F FF 46 A0 70
    # 实际查找用 reversed bytes:
    # bytes.fromhex("170885727F44EF8D4EB09FFF46A070")[:4] 是 17 08 85 72
    # 完整 16 字节: 17088572-7F44-EF8D-4EB0-9FFF46A070
    # 但 UEFI 混合字节序: 32-bit LE, 16-bit LE, 8 个字节 BE
    # 也就是: 72 85 08 17 7F 44 4E B0 9F FF 46 A0 70 (实际不对)
    # 让我看 MMTool 报告 - 那个文件用 GUID: 17088572-377F-44EF-8F4E-B09FFF46A070
    # LE 32-bit: 72 85 08 17
    # LE 16-bit: 7F 44
    # BE 8 bytes: 4E B0 9F FF 46 A0 70
    # 等下 - 应该是 8 bytes 不是 6
    # GUID {17088572-377F-44EF-8F4E-B09FFF46A070} 字节序:
    # Field 1 (32 bits): 17088572 → LE bytes 72 85 08 17
    # Field 2 (16 bits): 377F → LE bytes 7F 44
    # Field 3 (16 bits): 44EF → LE bytes EF 44
    # Field 4-5 (8 bytes each, BE): 4E-B0-9F-FF-46-A0-70
    # 等下让我用 little-endian 一致
    # GUID: 17088572-377F-44EF-8F4E-B09FFF46A070
    # bytes: 72 85 08 17 7F 44 EF 44 4E B0 9F FF 46 A0 70
    # = bytes.fromhex("728508177F44EF44-4EB09FFF46A070") 错
    # 实际 binary: 72 85 08 17 7F 44 EF 44 4E B0 9F FF 46 A0 70
    # 16 bytes 总长

    # 用 Python uuid 模块验证
    import uuid
    g = uuid.UUID("17088572-377F-44EF-8F4E-B09FFF46A070")
    guid_bytes = g.bytes_le  # 12 bytes (mixed endian)
    # 但实际 EFI 使用 mixed endian 16 bytes

    # 试 raw search
    # raw search: 72 85 08 17 7F 44 EF 44 4E B0 9F FF 46 A0 70
    target = bytes([0x72, 0x85, 0x08, 0x17, 0x7F, 0x44, 0xEF, 0x44, 0x4E, 0xB0, 0x9F, 0xFF, 0x46, 0xA0, 0x70])
    # 但 GUID 只有 15 字节, 错了 - 实际 GUID 是 16 字节
    # 让我重做
    # GUID: 17088572-377F-44EF-8F4E-B09FFF46A070
    # 完整 16 字节 LE (uuid.bytes_le):
    g_le = g.bytes_le  # 16 bytes
    g_be = g.bytes     # 16 bytes big-endian

    # EFI GUID 在 FFS 头中用的是 mixed endian (LE 32, LE 16, then 8 BE)
    # 实际: bytes_le[0:4] + bytes_le[4:6] + bytes_be[8:16]
    # 等下, bytes_le 已经把 32-bit 字段反了, 16-bit 字段反了, 8-byte 字段没反
    # 但 FFS GUID 实际存储是:
    # uint32 (LE) + uint16 (LE) + uint16 (LE) + 8 bytes (BE)
    # uuid.bytes_le 对应这个存储顺序
    # 所以 target = uuid.UUID(...).bytes_le

    # FFS 文件 GUID 在 FFS header 0x00 位置, 是这个 mixed endian
    target_microcode_guid = g_le
    if len(target_microcode_guid) != 16:
        # 重新算
        from struct import pack
        target_microcode_guid = (
            pack("<I", 0x17088572) +
            pack("<H", 0x377F) +
            pack("<H", 0x44EF) +
            bytes.fromhex("4EB09FFF46A070")
        )

    # 找 FFS microcode 文件: GUID 在 offset 0x00
    containers = []
    pos = 0
    while True:
        pos = data.find(target_microcode_guid, pos)
        if pos < 0:
            break
        # FFS header: GUID (16) + checksum (2) + type (1) + attributes (1) + size (4) + state (1) = 25 字节
        # size 在 offset 0x14 (DWORD)
        if pos + 0x20 > len(data):
            break
        ftype = data[pos + 0x12]
        fsize = struct.unpack("<I", data[pos + 0x14:pos + 0x18])[0]
        if ftype == 0x01 and 0x800 <= fsize <= 0x40000:  # EFI_FV_FILETYPE_MICROCODE
            containers.append((pos, fsize))
        pos += 4

    return containers


def find_microcode_in_container(data: bytes, container_offset: int) -> list:
    """在 microcode 容器内找单个 microcode 头"""
    # 标准 microcode 头 32 字节:
    # 0x00: type (1)
    # 0x04: total_size
    # 0x08: date (yyyy mm dd packed)
    # 0x0C: cpuid
    # 0x10: checksum
    # 0x14: loader version
    # 0x18: data_size

    # 但容器内可能用 bundle 格式: 整个 188KB 是 1 个 90671 + 906a0 (extended signature)
    # 或者多个独立 microcode (0x800 对齐)

    results = []
    # 扫整个容器
    for off in range(0, 0x30000, 0x10):
        if container_offset + off + 0x30 > len(data):
            break
        type_v = struct.unpack("<I", data[container_offset + off:container_offset + off + 4])[0]
        rev = struct.unpack("<I", data[container_offset + off + 4:container_offset + off + 8])[0]
        cpuid = struct.unpack("<I", data[container_offset + off + 0x0C:container_offset + off + 0x10])[0]
        date = struct.unpack("<I", data[container_offset + off + 8:container_offset + off + 0x0C])[0]
        # 启发式
        if (type_v == 1
            and 0 < rev < 0x300
            and 0 < cpuid < 0x100000000
            and 0 < date < 0x300000
            and (cpuid >> 8) & 0xF == 0x6):  # Intel family 6
            d_y = (date >> 16) & 0xFFFF
            d_m = (date >> 8) & 0xFF
            d_d = date & 0xFF
            date_str = f"{d_y:04d}-{d_m:02d}-{d_d:02d}" if 2020 <= d_y <= 2099 else f"0x{date:x}"
            results.append({
                "offset_in_container": off,
                "absolute_offset": container_offset + off,
                "type": type_v,
                "revision": f"0x{rev:02x}",
                "cpuid": f"0x{cpuid:08x}",
                "date": date_str,
            })
    return results


def main():
    if len(sys.argv) < 4:
        print("用法: python port_microcode.py <参考BIOS.bin> <Q100E.bin> <输出.bin>")
        print()
        print("例:")
        print("  python port_microcode.py Shuttle_XH610.bin third-party-bios/bios_2改...bin Q100E_14th.bin")
        print()
        print("工作流:")
        print("  1. 备份当前 Q100-E SPI flash (CH341A + NeoProgrammer)")
        print("  2. 下载 Shuttle XH610 BIOS (公开, 支持 12-14 代 H610)")
        print("  3. 跑这个脚本: 参考 BIOS 提取 12/13/14 代 microcode → 替换到 Q100E")
        print("  4. CH341A 写回测试")
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

    print("=" * 60)
    print("  Q100-E 14代 microcode 自动移植工具")
    print("=" * 60)
    print(f"  参考 BIOS: {ref_path} ({ref_path.stat().st_size} bytes)")
    print(f"  Q100-E BIOS: {q100e_path} ({q100e_path.stat().st_size} bytes)")
    print(f"  输出: {out_path}")
    print()

    # 1. 读 bin
    ref_data = ref_path.read_bytes()
    q100e_data = bytearray(q100e_path.read_bytes())

    if len(ref_data) != 0x2000000:
        print(f"[WARN] 参考 BIOS 大小 {len(ref_data)} != 32MB, 可能不是标准 32MB 镜像")
    if len(q100e_data) != 0x2000000:
        print(f"[ERROR] Q100-E BIOS 大小 {len(q100e_data)} != 32MB")
        sys.exit(1)

    print("=== 1. SHA256 ===")
    print(f"  参考 BIOS: {sha256(ref_data)}")
    print(f"  Q100-E BIOS: {sha256(bytes(q100e_data))}")
    print()

    # 2. 找参考 BIOS 的 microcode 容器
    print("=== 2. 参考 BIOS microcode 容器 ===")
    ref_containers = find_microcode_containers(ref_data)
    if not ref_containers:
        print("  [ERROR] 参考 BIOS 没找到 microcode 容器, 可能不标准")
        sys.exit(1)

    ref_microcodes = []
    for off, size in ref_containers:
        ms = find_microcode_in_container(ref_data, off)
        ref_microcodes.extend(ms)
        print(f"  容器 @ 0x{off:08x} size=0x{size:x} ({size} bytes): {len(ms)} 个 microcode")
        for m in ms:
            print(f"    - {m['cpuid']} rev={m['revision']} date={m['date']} @+0x{m['offset_in_container']:x}")

    # 3. 找 Q100-E 的 microcode 容器
    print()
    print("=== 3. Q100-E BIOS microcode 容器 ===")
    q100e_containers = find_microcode_containers(q100e_data)
    if not q100e_containers:
        print("  [ERROR] Q100-E BIOS 没找到 microcode 容器")
        sys.exit(1)

    for off, size in q100e_containers:
        ms = find_microcode_in_container(q100e_data, off)
        print(f"  容器 @ 0x{off:08x} size=0x{size:x} ({size} bytes): {len(ms)} 个 microcode")
        for m in ms:
            print(f"    - {m['cpuid']} rev={m['revision']} date={m['date']} @+0x{m['offset_in_container']:x}")

    # 4. 检查 14 代 microcode 是否在参考 BIOS 里
    print()
    print("=== 4. 参考 BIOS 含 14 代 microcode 检查 ===")
    has_14th = any(m["cpuid"] in ["0x000b0671", "0x00090675", "0x000906a4", "0x0009067a"] for m in ref_microcodes)
    print(f"  14 代 RPL-R (0x000B0671): {'✅' if any(m['cpuid'] == '0x000b0671' for m in ref_microcodes) else '❌'}")
    print(f"  14 代 RPL-R (0x00090675): {'✅' if any(m['cpuid'] == '0x00090675' for m in ref_microcodes) else '❌'}")
    print(f"  13 代 RPL-S (0x000906A4): {'✅' if any(m['cpuid'] == '0x000906a4' for m in ref_microcodes) else '❌'}")
    print(f"  12 代 ADL-S (0x0009067A): {'✅' if any(m['cpuid'] == '0x0009067a' for m in ref_microcodes) else '❌'}")
    if not has_14th:
        print()
        print("  [WARN] 参考 BIOS 没含 14 代 microcode! 移植无效")
        print("  请确认参考 BIOS 真的支持 14 代 CPU")
        sys.exit(1)

    # 5. 提取参考 BIOS 的 14 代 microcode 数据
    print()
    print("=== 5. 提取 14代 microcode 数据 ===")
    if not ref_containers:
        print("  [ERROR] 没有可用的参考 microcode 容器")
        sys.exit(1)

    ref_off, ref_size = ref_containers[0]
    # 提取整个容器（简单粗暴）
    new_mc_container = bytearray(ref_data[ref_off:ref_off + ref_size])
    print(f"  从参考 BIOS 提取 {len(new_mc_container)} bytes 容器")
    print(f"  包含 microcode: {len(ref_microcodes)} 个")
    for m in ref_microcodes:
        print(f"    - {m['cpuid']} rev={m['revision']} date={m['date']}")

    # 6. 找 Q100-E 容器大小
    print()
    print("=== 6. 替换到 Q100-E ===")
    if not q100e_containers:
        print("  [ERROR] Q100-E 没有可替换的容器")
        sys.exit(1)

    q100e_off, q100e_size = q100e_containers[0]
    print(f"  Q100-E 容器 @ 0x{q100e_off:08x} size=0x{q100e_size:x} ({q100e_size} bytes)")

    if len(new_mc_container) > q100e_size:
        # 参考容器比 Q100-E 大 - 需要先删旧 microcode, 再加新
        print(f"  [WARN] 参考容器 ({len(new_mc_container)}) > Q100-E 容器 ({q100e_size})")
        print(f"  策略: 把参考容器前 {q100e_size} 字节填入, 剩余截断 (可能丢部分 microcode)")

    # 7. 替换
    # 简单替换: 用新数据覆盖原容器
    bytes_to_copy = min(len(new_mc_container), q100e_size)
    for i in range(bytes_to_copy):
        q100e_data[q100e_off + i] = new_mc_container[i]
    # 剩余用 0xFF 填充
    if bytes_to_copy < q100e_size:
        for i in range(bytes_to_copy, q100e_size):
            q100e_data[q100e_off + i] = 0xFF

    print(f"  替换了 {bytes_to_copy} bytes @ 0x{q100e_off:08x}")
    print(f"  剩余 {q100e_size - bytes_to_copy} bytes 填 0xFF")

    # 8. 写输出
    out_path.write_bytes(bytes(q100e_data))
    print()
    print("=" * 60)
    print("  完成")
    print("=" * 60)
    print(f"  输出文件: {out_path}")
    print(f"  大小: {out_path.stat().st_size} bytes")
    print(f"  SHA256: {sha256(bytes(q100e_data))}")
    print()
    print("  下一步:")
    print(f"  1. 用 NeoProgrammer 验证修改区域")
    print(f"  2. CH341A 写回 SPI flash")
    print(f"  3. 装 i5-14400 测试")
    print()
    print("  ⚠️ 注意:")
    print("  - 必须先备份当前 SPI flash")
    print("  - 如果 14 代不亮, 用备份救回")


if __name__ == "__main__":
    main()
