"""直接解析 ME 区域（不用 MEInfo）"""
import sys
import struct
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uefi_firmware.me import MePartitionTable, MeContainer, MeObject

bin_path = Path("D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/backups/H610_full_32mb_V1.bin")
data = bin_path.read_bytes()

# 找 $FPT
fpt_off = data.find(b"$FPT")
print(f"$FPT @ 0x{fpt_off:08x}")
fpt = data[fpt_off:]

# 解析 partitions
num = fpt[0x04]
print(f"Partitions: {num}")
for i in range(num):
    e = 0x20 + i * 0x20
    if e + 0x20 > len(fpt): break
    name = fpt[e:e+4].decode("latin-1")
    off = struct.unpack("<I", fpt[e+0x08:e+0x0C])[0]
    size = struct.unpack("<I", fpt[e+0x0C:e+0x10])[0]
    print(f"  [{i:2d}] {name:6s} @ 0x{off:08x} size=0x{size:x} (abs 0x{fpt_off+off:08x})")

# 找 ME manifest (version)
# ME 区域在 CSME 分区
# 通常 CSME 起始位置 0x3000 或 0x1000
print()
print("=== 找 ME 版本字符串 ===")
import re
for m in re.finditer(rb'(\d+\.\d+\.\d+\.\d{4})', data):
    pos = m.start()
    if 0x1000 < pos < 0x1000000:  # ME 区域
        ctx = data[max(0, pos-20):pos+20]
        printable = "".join(chr(b) if 32 <= b < 127 else "." for b in ctx)
        print(f"  0x{pos:08x}: {m.group(0).decode()} ctx: {printable}")
        if pos > 0x50000:  # 跳过太多
            break
