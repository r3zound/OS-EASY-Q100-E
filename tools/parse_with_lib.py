#!/usr/bin/env python3
"""用 uefi_firmware AutoParser 智能解析 SPI flash"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uefi_firmware import AutoParser, search_firmware_volumes, guids

data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()
print(f"文件大小: {len(data)} bytes\n")

print("=== 已知 GUID 列表（部分）===")
# 找出 microcode 相关 GUID
for name in dir(guids):
    if "microcode" in name.lower() or "MICROCODE" in name or "MCHP" in name.upper():
        print(f"  {name}")

print()
print("=== 用 AutoParser 解析 ===")
parser = AutoParser(data)
print(f"parser type: {type(parser).__name__}")
attrs = [a for a in dir(parser) if not a.startswith("_")]
print(f"parser attrs: {attrs}")

try:
    parsed = parser.parse()
    print(f"parse 成功: {type(parsed).__name__}")
    for attr in ["objects", "files", "sections", "root", "volumes", "images"]:
        if hasattr(parsed, attr):
            v = getattr(parsed, attr)
            if callable(v): continue
            if hasattr(v, "__len__"):
                print(f"  {attr}: {type(v).__name__} (len={len(v)})")
            else:
                print(f"  {attr}: {v}")
except Exception as e:
    print(f"parse 失败: {e}")
    import traceback
    traceback.print_exc()
