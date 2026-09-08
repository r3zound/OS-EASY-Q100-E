#!/usr/bin/env python3
"""检查 uefi_firmware 库的 ME 解析能力"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uefi_firmware import me
print("=== uefi_firmware.me 模块内容 ===")
for name in dir(me):
    if not name.startswith("_"):
        print(f"  {name}")
print()

# 找 Huffman 相关
print("=== Huffman 相关类/函数 ===")
for name in dir(me):
    if "huff" in name.lower() or "lut" in name.lower():
        print(f"  {name}: {type(getattr(me, name))}")

# 找 ParseableType 等
print()
print("=== MeObject 子类 ===")
import inspect
for name, obj in inspect.getmembers(me):
    if inspect.isclass(obj) and "Me" in name:
        print(f"  {name}")
