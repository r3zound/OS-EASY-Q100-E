#!/usr/bin/env python3
"""用 strings 找 microcode 关键词 + 用 uefi_firmware 库解析"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()

print("=== 关键字符串扫描（每关键词最多 3 个匹配）===")
for kw in [b"Microcode", b"microcode", b"ME FW", b"BIOS", b"Fit", b"FIT", b"BDS",
           b"DXE", b"PEI", b"Verified", b"SecureBoot", b"AMI", b"Aptio", b"Intel"]:
    pos = 0
    cnt = 0
    while True:
        pos = data.find(kw, pos)
        if pos < 0:
            break
        cnt += 1
        if cnt <= 3:
            ctx = data[max(0, pos - 8):pos + 40]
            printable = "".join(chr(b) if 32 <= b < 127 else "." for b in ctx)
            print(f"  0x{pos:08x}: {printable}")
        pos += 1
    if cnt > 3:
        print(f"  ... 共 {cnt} 个")
    if cnt == 0:
        print(f"  [-] '{kw.decode('latin-1')}' 未找到")

print()
print("=== 用 uefi_firmware 库解析 ===")
try:
    from uefi_firmware.uefi import Uefi
    print("uefi_firmware 库已加载")
    try:
        parsed = Uefi(data)
        print(f"  parsed type: {type(parsed).__name__}")
        attrs = [a for a in dir(parsed) if not a.startswith("_")][:40]
        print(f"  attributes: {attrs}")
    except Exception as e:
        print(f"  parse 失败: {e}")
except Exception as e:
    print(f"  uefi_firmware 导入失败: {e}")
