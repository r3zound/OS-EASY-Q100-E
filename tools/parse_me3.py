#!/usr/bin/env python3
"""用 uefi_firmware.me 的 MePartitionTable 正确解析"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uefi_firmware.me import MePartitionTable, MeContainer, MeObject
from uefi_firmware.base import StructuredObject

data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()

FPT_SIG = b"$FPT"
fpt_offset = data.find(FPT_SIG)
print(f"$FPT 在 0x{fpt_offset:08x}\n")

# MePartitionTable 期望从 $FPT 开始的数据
fpt_data = data[fpt_offset:]
print("=== 解析 MePartitionTable ===")
mpt = MePartitionTable(fpt_data)
print(f"Type: {type(mpt).__name__}")
print(f"Attrs: {mpt.attrs if hasattr(mpt, 'attrs') else '?'}")

# 手动调用 parse
if hasattr(mpt, "parse"):
    try:
        mpt.parse()
        print("parse() 成功")
    except Exception as e:
        print(f"parse() 失败: {e}")

# 展示
def show(obj, depth=0):
    indent = "  " * depth
    name = type(obj).__name__
    extra = ""
    if hasattr(obj, "offset"):
        extra += f" offset=0x{obj.offset:08x}"
    if hasattr(obj, "length"):
        extra += f" length=0x{obj.length:x}"
    if hasattr(obj, "attrs") and isinstance(obj.attrs, dict):
        interesting = {k: v for k, v in obj.attrs.items() if k in
                       ["Name", "Type", "GUID", "Subtype", "version", "Major", "Minor",
                        "Hotfix", "Build", "Vendor", "size", "Offset", "HeaderLength"]}
        if interesting:
            extra += f" attrs={interesting}"
    print(f"{indent}- {name}{extra}")
    if hasattr(obj, "objects") and isinstance(obj.objects, list):
        for child in obj.objects:
            show(child, depth + 1)

show(mpt)
