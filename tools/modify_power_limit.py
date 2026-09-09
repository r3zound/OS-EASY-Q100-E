#!/usr/bin/env python3
"""
修改 Q100-E 功耗墙 Default 值（在解压后的 Setup 模块里）

功耗墙变量（已从 IFR 确认）：
- Platform PL1 Power (VarOffset 0x32): 0xC350 (50W) → 0xFDE8 (65W)
- Platform PL2 Power (VarOffset 0x38): 0xC350 (50W) → 0x13880 (80W)
- Power Limit 1 (VarOffset 0x17): 0xC350 (50W) → 0xFDE8 (65W)
- Power Limit 2 (VarOffset 0x1E): 0xC350 (50W) → 0x13880 (80W)
- Power Limit 4 (VarOffset 0x2B): 保持 0x15F90 (90W)

Default opcode: 5B 09 00 00 02 <4字节小端值>

用法:
  python modify_power_limit.py <setup_body.bin> <输出.bin>
"""
import sys
import struct
import hashlib
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    if len(sys.argv) < 2:
        print("用法: python modify_power_limit.py <setup_body.bin> [输出.bin]")
        sys.exit(1)

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else in_path.with_suffix(".modified.bin")

    data = bytearray(in_path.read_bytes())
    print(f"=== 修改 {in_path.name} 功耗墙 ===")
    print(f"大小: {len(data):,} bytes\n")

    # 功耗墙 Default opcode（旧值 0xC350 = 50W）
    old_pl50 = bytes.fromhex("5B0900000250C30000")

    # 新值
    pl1_65w = struct.pack("<I", 65000)   # 0xFDE8
    pl2_80w = struct.pack("<I", 80000)   # 0x13880

    new_pl1 = bytes.fromhex("5B09000002") + pl1_65w
    new_pl2 = bytes.fromhex("5B09000002") + pl2_80w

    # 搜索所有 PL=50W 位置
    positions = []
    pos = 0
    while True:
        pos = data.find(old_pl50, pos)
        if pos < 0:
            break
        positions.append(pos)
        pos += 1

    print(f"找到 {len(positions)} 个 PL=50W Default:\n")

    # 按位置判断 PL1 还是 PL2
    # 已知位置:
    #   0x35212: Platform PL1 Power → PL1
    #   0x3532a: Platform PL2 Power → PL2
    #   0x367b4: Power Limit 1 → PL1
    #   0x368fa: Power Limit 2 → PL2
    #   0x420c9: Platform PL1 Power (重复) → PL1
    #   0x4211f: Platform PL2 Power (重复) → PL2
    pl1_positions = set([0x35212, 0x367b4, 0x420c9])
    pl2_positions = set([0x3532a, 0x368fa, 0x4211f])

    modified = 0
    for p in positions:
        if p in pl1_positions:
            new_opcode = new_pl1
            label = "PL1 → 65W"
        elif p in pl2_positions:
            new_opcode = new_pl2
            label = "PL2 → 80W"
        else:
            # 未知位置，保守：保持 50W（不动）
            print(f"  0x{p:08x}: 未知位置，保持 50W (不动)")
            continue

        data[p:p + len(new_opcode)] = new_opcode
        modified += 1
        print(f"  0x{p:08x}: 0xC350 (50W) → {label}")

    # PL4 保持 90W（不动）
    print(f"\n  Power Limit 4 (0x15F90 = 90W): 保持不动")

    # 保存
    out_path.write_bytes(data)
    print(f"\n=== 完成 ===")
    print(f"修改了 {modified} 处功耗墙")
    print(f"输出: {out_path}")
    print(f"新 SHA256: {hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
