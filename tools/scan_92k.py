#!/usr/bin/env python3
"""在 PMCP 区域 (0x23000 - 0x39FFF) 扫 microcode 头"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()

# PMCP 区域 (0x23000 - 0x39FFF)
START = 0x23000
END = 0x3A000
print(f"扫描 0x{START:x} - 0x{END:x} ({END-START} bytes)\n")

# microcode 头格式（PMCP/ME 容器内的格式）：
# 0x00: type (1)
# 0x04: total_size
# 0x08: ?
# 0x0C: microcode version (e.g. 0xB7)
# 0x10: revision (1)
# 0x14: cpuid signature
# 0x18: cpuid flags / platform
# 0x1C: date
# 0x20: signature / checksum
#
# 但 ME 区域 microcode 容器可能前缀不同
# 让我用更宽松的匹配：0x0C 是 version (0xB7-0x200), 0x10 是 1, 0x1C 是合理 date, 0x14 是合理 cpuid

hits = []
for i in range(START, END - 0x30, 0x08):
    ucode_ver = struct.unpack("<I", data[i + 0x0C:i + 0x10])[0]
    rev_id = struct.unpack("<I", data[i + 0x10:i + 0x14])[0]
    ucode_date = struct.unpack("<I", data[i + 0x1C:i + 0x20])[0]
    cpuid = struct.unpack("<I", data[i + 0x14:i + 0x18])[0]

    # 启发式
    if (0 < ucode_ver < 0x300
        and rev_id == 1
        and 0 < ucode_date < 0x300000
        and 0 < cpuid < 0x100000000):
        d = ucode_date
        date = f"{(d>>16)&0xffff:04d}-{(d>>8)&0xff:02d}-{d&0xff:02d}"
        fam = (cpuid >> 8) & 0xF
        if fam == 0xF: fam += (cpuid >> 20) & 0xFF
        mod = (cpuid >> 4) & 0xF
        if fam in (0x6, 0xF): mod += (cpuid >> 12) & 0xF0
        hits.append((i, ucode_ver, cpuid, fam, mod, date))

# 去重
seen = set()
unique = []
for h in hits:
    if h[0] not in seen:
        seen.add(h[0])
        unique.append(h)

print(f"找到 {len(unique)} 个候选 microcode 容器\n")
print(f"  {'#':>3s}  {'偏移':>10s}  {'版本':>6s}  {'日期':>12s}  "
      f"{'CPUID':>10s}  {'F/M':>10s}  代号")
print(f"  {'-'*3}  {'-'*10}  {'-'*6}  {'-'*12}  "
      f"{'-'*10}  {'-'*10}  {'-'*30}")
for idx, (off, ver, cpuid, fam, mod, date) in enumerate(unique, 1):
    names = {
        (0x6, 0x97): "ADL-S (12代)", (0x6, 0x9E): "KBL (7代)",
        (0x6, 0x9F): "CFL (8/9代)", (0x6, 0xA5): "CML (10代)",
        (0x6, 0xB7): "RPL (13代)", (0x6, 0xBA): "RPL-P",
        (0x6, 0xBF): "RPL-R (14代)",
        (0x6, 0xAA): "MTL (新)", (0x6, 0xAC): "MTL",
    }
    nm = names.get((fam, mod), f"F{fam}/M0x{mod:x}")
    fm = f"F{fam}/M0x{mod:x}"
    print(f"  {idx:>3d}  0x{off:08x}  0x{ver:02x}    {date:>12s}  "
          f"0x{cpuid:08x}  {fm:>10s}  {nm}")

# 14 代检测
has_rpl_r = any((fam, mod) == (0x6, 0xBF) for off, ver, cpuid, fam, mod, date in unique)
print()
print(f"14 代 RPL-R microcode: {'[+] 存在' if has_rpl_r else '[-] 不存在'}")

# 12 代检测
has_adl_s = any((fam, mod) == (0x6, 0x97) for off, ver, cpuid, fam, mod, date in unique)
print(f"12 代 ADL-S microcode: {'[+] 存在' if has_adl_s else '[-] 不存在'}")
