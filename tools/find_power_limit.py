#!/usr/bin/env python3
"""
定位 Q100-E V1 BIOS 里的功耗墙 Default 值，并可选修改

功耗墙默认值（从 IFR 提取）：
- Platform PL1 Power (VarOffset 0x32): Default 0xC350 = 50000 mW = 50W
- Platform PL2 Power (VarOffset 0x38): Default 0xC350 = 50000 mW = 50W
- Power Limit 4 (VarOffset 0x2B): Default 0x15F90 = 90000 mW = 90W

IFR Default opcode 字节序列：
  5B = Default opcode
  09 = (scope=0, size=2 → 32-bit)
  00 00 = DefaultId 0
  02 = 32-bit size
  <value little-endian 4 bytes>

所以 PL1/PL2 = 50W 的 Default opcode = 5B 09 00 00 02 50 C3 00 00

用法:
  python find_power_limit.py <bin>            # 只定位（只读）
  python find_power_limit.py <bin> --modify   # 修改 PL1→65W, PL2→148W
"""
import sys
import struct
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    if len(sys.argv) < 2:
        print("用法: python find_power_limit.py <bin> [--modify]")
        sys.exit(1)

    bin_path = Path(sys.argv[1])
    modify = "--modify" in sys.argv

    data = bytearray(bin_path.read_bytes())
    print(f"=== {bin_path.name} ===\n大小: {len(data):,} bytes\n")

    # PL1/PL2 = 50W 的 Default opcode
    # 5B 09 00 00 02 50 C3 00 00 (50 C3 = 0xC350 小端 = 50000)
    pl50_default = bytes.fromhex("5B0900000250C30000")

    # 新值
    pl1_65w = 65000   # 0xFDE8
    pl2_148w = 148000  # 0x24220

    # 搜索所有匹配
    positions = []
    pos = 0
    while True:
        pos = data.find(pl50_default, pos)
        if pos < 0:
            break
        positions.append(pos)
        pos += 1

    print(f"找到 {len(positions)} 个 PL=50W (0xC350) 的 Default opcode:\n")
    for p in positions:
        # 显示上下文
        ctx_start = max(0, p - 16)
        ctx = data[ctx_start:p + 16]
        ctx_hex = " ".join(f"{b:02x}" for b in ctx)
        print(f"  0x{p:08x}: ...{ctx_hex}...")

    # 也搜 PL4 = 90W (0x15F90 = 90000)
    pl4_90w_default = bytes.fromhex("5B09000002905F0100")
    pl4_positions = []
    pos = 0
    while True:
        pos = data.find(pl4_90w_default, pos)
        if pos < 0:
            break
        pl4_positions.append(pos)
        pos += 1
    print(f"\n找到 {len(pl4_positions)} 个 PL4=90W (0x15F90) 的 Default opcode:")
    for p in pl4_positions:
        print(f"  0x{p:08x}")

    # 修改模式
    if modify and positions:
        print("\n=== 修改 ===")
        # 修改前 2 个 50W → 65W (PL1)，后 2 个 → 148W (PL2)
        # 实际：PL1 和 PL2 各 2 处（Power&Performance + OverClocking 菜单）
        for i, p in enumerate(positions):
            if i < len(positions) // 2:
                # PL1 → 65W
                new_val = struct.pack("<I", pl1_65w)
                new_opcode = bytes.fromhex("5B09000002") + new_val
                print(f"  PL1 @ 0x{p:08x}: 0xC350 (50W) → 0x{pl1_65w:04X} (65W)")
            else:
                # PL2 → 148W
                new_val = struct.pack("<I", pl2_148w)
                new_opcode = bytes.fromhex("5B09000002") + new_val
                print(f"  PL2 @ 0x{p:08x}: 0xC350 (50W) → 0x{pl2_148w:04X} (148W)")
            data[p:p + len(new_opcode)] = new_opcode

        # 保存
        out = bin_path.with_suffix(".power_unlocked.bin")
        out.write_bytes(data)
        print(f"\n已保存修改到: {out}")
        print(f"新 SHA256: ", end="")
        import hashlib
        print(hashlib.sha256(data).hexdigest())
    elif modify and not positions:
        print("\n未找到可修改的功耗墙 Default 值（可能已被修改或格式不同）")
    elif not modify:
        print("\n提示: 加 --modify 参数可修改 PL1→65W, PL2→148W")


if __name__ == "__main__":
    main()
