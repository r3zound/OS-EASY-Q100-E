#!/usr/bin/env python3
"""第二轮扫描：用正确偏移找 microcode"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

bin_path = sys.argv[1] if len(sys.argv) > 1 else "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin"
data = open(bin_path, "rb").read()
print(f"文件: {bin_path}")
print(f"大小: {len(data)} bytes\n")

# microcode 容器内正确偏移：
# 0x00: 0x01 0x00 0x00 0x00  (type/magic)
# 0x04: total_size (DWORD)
# 0x08: reserved
# 0x0C: reserved
# 0x10: 0x01 0x00 0x00 0x00  (revision)
# 0x14: cpuid_sig
# 0x18: cpuid_flags
# 0x1C: date
# 0x20: signature/checksum
# 实际：0x00 0x00 0x00 0x00 / 0x01 0x00 0x00 0x00 / 0x00 0x00 0x00 0x00 / 0xB7 0x00 0x00 0x00 / 0x01 0x00 0x00 0x00 / <CPUID> ...

# 找 microcode 容器：
# - 偏移 0x10-0x13: 0x01 0x00 0x00 0x00 (revision)
# - 偏移 0x0C-0x0F: microcode version (0x01-0x200)
# - 偏移 0x1C-0x1F: date (yyyy mm dd packed)
# - 偏移 0x14-0x17: CPUID (Family 6, Model < 0x100)

print("=== 找 microcode 容器（正确偏移）===")
print("条件: offset[0x10]=1, [0x0C]=version<0x200, [0x1C]=date<0x300000, [0x14]!=0\n")

count = 0
results = []
for i in range(0, len(data) - 0x30, 0x10):  # 步长 0x10
    if i + 0x30 > len(data): break
    rev_id = struct.unpack("<I", data[i+0x10:i+0x14])[0]
    ucode_ver = struct.unpack("<I", data[i+0x0C:i+0x10])[0]
    ucode_date = struct.unpack("<I", data[i+0x1C:i+0x20])[0]
    cpuid = struct.unpack("<I", data[i+0x14:i+0x18])[0]
    flags = struct.unpack("<I", data[i+0x18:i+0x1C])[0]
    total_size = struct.unpack("<I", data[i+0x04:i+0x08])[0]

    # 启发式匹配
    is_ucode = (
        rev_id == 1
        and 0 < ucode_ver < 0x200
        and cpuid != 0 and cpuid != 0xFFFFFFFF
        and ucode_date < 0x300000 and ucode_date > 0
        and 0x100 < total_size < 0x10000
    )
    if is_ucode:
        # 解析 Family/Model
        fam = (cpuid >> 8) & 0xF
        if fam == 0xF: fam += (cpuid >> 20) & 0xFF
        mod = (cpuid >> 4) & 0xF
        if fam in (0x6, 0xF): mod += (cpuid >> 12) & 0xF0
        step = cpuid & 0xF
        # 解析日期
        d = ucode_date
        date = f"{d>>16:04d}-{(d>>8)&0xff:02d}-{d&0xff:02d}"
        # 代号
        names = {
            (0x6, 0x9E): "Kaby Lake", (0x6, 0x9C): "Apollo Lake",
            (0x6, 0x9F): "Coffee Lake", (0x6, 0xA5): "Comet Lake",
            (0x6, 0xA7): "Rocket Lake", (0x6, 0x97): "Alder Lake-S",
            (0x6, 0x9A): "Alder Lake-P", (0x6, 0xB7): "Raptor Lake-S",
            (0x6, 0xBA): "Raptor Lake-P",
            (0x6, 0xBF): "RPL-S Refresh (14代?)",
            (0x6, 0xAA): "Meteor Lake", (0x6, 0xAC): "Meteor Lake",
        }
        name = names.get((fam, mod), f"Family {fam} Model 0x{mod:x}")
        results.append((i, ucode_ver, cpuid, fam, mod, step, date, total_size, name))
        count += 1

# 去重 + 排序
seen = set()
unique = []
for r in results:
    if r[0] not in seen:
        seen.add(r[0])
        unique.append(r)

print(f"找到 {len(unique)} 个 microcode 容器（候选）\n")
print(f"  {'#':>3s}  {'偏移':>10s}  {'版本':>6s}  {'日期':>12s}  "
      f"{'CPUID':>10s}  {'F/M/S':>13s}  {'size':>6s}  代号")
print(f"  {'-'*3}  {'-'*10}  {'-'*6}  {'-'*12}  "
      f"{'-'*10}  {'-'*13}  {'-'*6}  {'-'*30}")
for idx, (off, ver, cpuid, fam, mod, step, date, size, name) in enumerate(unique[:50], 1):
    fm = f"F{fam}/M0x{mod:x}/S{step}"
    print(f"  {idx:>3d}  0x{off:08x}  0x{ver:02x}    {date:>12s}  "
          f"0x{cpuid:08x}  {fm:>13s}  0x{size:04x}  {name}")

# 14 代检测
has_rpl_r = any((fam, mod) in [(0x6, 0xBF), (0x6, 0xB7)] for off, ver, cpuid, fam, mod, step, date, size, name in unique)
print()
print(f"14 代 RPL-R microcode: {'[+] 存在' if has_rpl_r else '[-] 不存在'}")
