#!/usr/bin/env python3
"""用 HuffmanLUTHeader 直接解析 PMCC000 数据"""
import sys
import struct
import ctypes
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uefi_firmware.me import HuffmanLUTHeader

# HuffmanLUTHeader 结构 (uefi_firmware):
# - Tag: 4 bytes
# - ChunkCount: uint32
# - DecompBase: uint32
# - Unk0C: uint32
# - Size: uint32
# - DataStart: uint32
# - Unk18: 6 * uint32
# - ChunkSize: uint32
# - Unk34: uint32
# - Chipset: 8 bytes
# 总: 0x40 = 64 字节

print("=== HuffmanLUTHeader 字段 ===")
for f_name, f_type in HuffmanLUTHeader._fields_:
    print(f"  {f_name:15s}: {f_type.__name__}")
print()

# 加载数据
bin_path = Path("D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin")
data = bin_path.read_bytes()
print(f"=== {bin_path.name} ===\n")

# 试多种 Huffman / ME magic
print("=== 找各种可能的 ME 16.x magic ===")
for magic, name in [
    (b"\x5f\xaa\x5a\xa5", "Huffman LUT (5FAA5AA5 LE)"),
    (b"\xa5\x5a\xaa\x5f", "Huffman LUT reversed"),
    (b"\x5d\x00\x00\x00", "LZMA Intel (5D000000)"),
    (b"\x01\x00\x00\x00", "microcode type=1 (any)"),
    (b"\x24\x4d\x4e\x32", "$MN2"),
    (b"PMCC", "PMCC text"),
    (b"$FPT", "$FPT"),
]:
    pos = 0
    hits = []
    while True:
        pos = data.find(magic, pos)
        if pos < 0: break
        hits.append(pos)
        pos += 1
    if hits:
        print(f"  {name}: {len(hits)} 个匹配, 首在 0x{hits[0]:08x}")
        for h in hits[:5]:
            print(f"    0x{h:08x}")

# 用 HuffmanLUTHeader 试解析 PMCC000 数据
print("\n=== 试解析 PMCC000 数据 (0x23101) 为 HuffmanLUTHeader ===")
pmcc_data = data[0x23101:0x23101 + 0x21000]
for off in [0, 0x60, 0x80, 0x100, 0x200, 0x400]:
    if off + ctypes.sizeof(HuffmanLUTHeader) > len(pmcc_data):
        break
    try:
        h = HuffmanLUTHeader.from_buffer_copy(pmcc_data, off)
        tag_bytes = bytes(h.Tag)
        if any(b != 0 for b in tag_bytes):
            print(f"  +0x{off:x}: Tag={tag_bytes.hex()}")
            print(f"    ChunkCount={h.ChunkCount}, DecompBase=0x{h.DecompBase:x}")
            print(f"    Size=0x{h.Size:x}, DataStart=0x{h.DataStart:x}")
            print(f"    ChunkSize=0x{h.ChunkSize:x}, Chipset={bytes(h.Chipset).hex()}")
    except Exception as e:
        pass

# 试从 PMCC000 起点 (0x23101) 找 microcode bundle
print("\n=== PMCC000 区域 0x23101-0x44101 找 microcode bundle (loader_sig=1) ===")
for off in range(0, 0x21000 - 8, 0x10):
    if struct.unpack("<I", pmcc_data[off:off+4])[0] == 1 and struct.unpack("<I", pmcc_data[off+4:off+8])[0] == 1:
        # 找到 loader sig (0x00000001 0x00000001) — microcode bundle 起点
        print(f"  +0x{off:x} (abs 0x{0x23101+off:x}): loader_sig found")
        # 显示后面 32 字节
        for j in range(0, 32, 16):
            h = " ".join(f"{b:02x}" for b in pmcc_data[off+j:off+j+16])
            print(f"    +0x{off+j:x}: {h}")
        if off > 0x100: break  # 不打印太多

# 试整片 bin 找 microcode bundle
print("\n=== 整片 bin 找 microcode bundle (loader_sig=1,1) ===")
for off in range(0, len(data) - 8, 0x100):
    if (struct.unpack("<I", data[off:off+4])[0] == 1
        and struct.unpack("<I", data[off+4:off+8])[0] == 1
        and (off & 0x7FF) == 0):  # 0x800 对齐
        # 看后续 16 字节
        date = struct.unpack("<I", data[off+8:off+12])[0]
        cpuid = struct.unpack("<I", data[off+12:off+16])[0]
        if 0 < date < 0x300000 and 0 < cpuid < 0x100000000:
            print(f"  0x{off:08x}: date=0x{date:x} cpuid=0x{cpuid:08x}")
            if len([1 for x in [(off & 0x7FF) == 0]]) > 10: break
