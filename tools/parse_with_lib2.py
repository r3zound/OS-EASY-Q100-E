#!/usr/bin/env python3
"""用 AutoParser 解析 FlashDescriptor 全部内容"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uefi_firmware import AutoParser

data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()

parser = AutoParser(data)
parsed = parser.parse()
print(f"Type: {type(parsed).__name__}")
print(f"Offset: 0x{parser.offset:08x}")
print()

# 递归展示所有 objects
def show(obj, depth=0):
    indent = "  " * depth
    name = type(obj).__name__
    extra = ""
    if hasattr(obj, "offset"):
        extra += f" offset=0x{obj.offset:08x}"
    if hasattr(obj, "length"):
        extra += f" length=0x{obj.length:x}"
    if hasattr(obj, "attrs"):
        attrs = obj.attrs
        if isinstance(attrs, dict):
            interesting = {k: v for k, v in attrs.items() if k in
                           ["Type", "GUID", "Name", "data_type", "region", "Subtype", "id", "version", "files"]}
            if interesting:
                extra += f" attrs={interesting}"

    print(f"{indent}- {name}{extra}")

    if hasattr(obj, "objects") and isinstance(obj.objects, list):
        for child in obj.objects:
            show(child, depth + 1)
    elif hasattr(obj, "sections") and isinstance(obj.sections, list):
        for child in obj.sections:
            show(child, depth + 1)

# 展示
for obj in parsed.objects:
    show(obj)
