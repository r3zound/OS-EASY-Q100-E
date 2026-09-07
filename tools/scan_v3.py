#!/usr/bin/env python3
"""第三轮：找 FVH / microcode (0x800 边界 + 严格条件)"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = open(sys.argv[1] if len(sys.argv) > 1 else
            "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
            "rb").read()
print(f"文件大小: {len(data)} bytes\n")

# 找 FFS Volume Header
print("=== 找 _FVH 字符串 ===")
for i in range(0, len(data) - 4, 0x40):
    if data[i:i + 4] == b"_FVH":
        print(f"  [+] 0x{i:08x}: FVH")
        for j in range(0, 64, 16):
            print("    0x{:08x}: {}".format(i + j, " ".join(f"{b:02x}" for b in data[i + j:i + j + 16])))

# 找 0x55 0xAA at 0x1FE
print()
print("=== 找 0x55AA at offset 0x1FE (legacy boot sector) ===")
for i in range(0, len(data) - 2, 0x100):
    if data[i:i + 2] == b"\x55\xaa" and (i & 0x1FF) == 0x1FE:
        print(f"  [+] 0x{i:08x}: legacy boot block")

# microcode 严格匹配
print()
print("=== 找 microcode (0x800 边界 + 严格条件) ===")
hits = []
for i in range(0, len(data) - 0x30, 0x800):  # 0x800 步长
    if (i & 0x7FF) != 0:
        continue
    if i + 0x30 > len(data):
        break
    type_v = struct.unpack("<I", data[i:i + 4])[0]
    total_size = struct.unpack("<I", data[i + 4:i + 8])[0]
    rev_id = struct.unpack("<I", data[i + 0x10:i + 0x14])[0]
    ucode_ver = struct.unpack("<I", data[i + 0x0C:i + 0x10])[0]
    ucode_date = struct.unpack("<I", data[i + 0x1C:i + 0x20])[0]
    cpuid = struct.unpack("<I", data[i + 0x14:i + 0x18])[0]

    # microcode 头条件：
    # - type = 0x01
    # - total_size 0x1000-0x4000 (典型 0x800-0x2000)
    # - rev_id = 1
    # - ucode_ver 0x01-0x200
    # - cpuid 非 0 / FFFFFFFF
    # - date 现实范围
    if (type_v == 1
        and 0x800 <= total_size <= 0x4000
        and rev_id == 1
        and 0 < ucode_ver < 0x200
        and 0 < cpuid < 0x100000000
        and 0 < ucode_date < 0x300000):
        d = ucode_date
        date = f"{(d >> 16) & 0xffff:04d}-{(d >> 8) & 0xff:02d}-{d & 0xff:02d}"
        hits.append((i, ucode_ver, cpuid, date, total_size))

# 去重
seen = set()
unique = []
for h in hits:
    if h[0] not in seen:
        seen.add(h[0])
        unique.append(h)

print(f"找到 {len(unique)} 个 microcode 容器：\n")
print(f"  {'#':>3s}  {'偏移':>10s}  {'版本':>6s}  {'日期':>12s}  "
      f"{'CPUID':>10s}  {'F/M':>10s}  {'size':>6s}  代号")
print(f"  {'-' * 3}  {'-' * 10}  {'-' * 6}  {'-' * 12}  "
      f"{'-' * 10}  {'-' * 10}  {'-' * 6}  {'-' * 25}")
for idx, (off, ver, cpuid, date, size) in enumerate(unique, 1):
    fam = (cpuid >> 8) & 0xF
    if fam == 0xF:
        fam += (cpuid >> 20) & 0xFF
    mod = (cpuid >> 4) & 0xF
    if fam in (0x6, 0xF):
        mod += (cpuid >> 12) & 0xF0
    step = cpuid & 0xF
    names = {
        (0x6, 0x9E): "KBL (7代)", (0x6, 0x9C): "APL",
        (0x6, 0x9F): "CFL (8/9代)", (0x6, 0xA5): "CML (10代)",
        (0x6, 0x97): "ADL-S (12代)", (0x6, 0x9A): "ADL-P",
        (0x6, 0xB7): "RPL (13代)", (0x6, 0xBA): "RPL-P",
        (0x6, 0xBF): "RPL-R (14代)",
        (0x6, 0xAA): "MTL (新)", (0x6, 0xAC): "MTL",
    }
    nm = names.get((fam, mod), f"F{fam}/M0x{mod:x}")
    fm = f"F{fam}/M0x{mod:x}"
    print(f"  {idx:>3d}  0x{off:08x}  0x{ver:02x}    {date:>12s}  "
          f"0x{cpuid:08x}  {fm:>10s}  0x{size:04x}  {nm}")

# 14 代检测
has_rpl_r = any((fam := (((cpuid >> 8) & 0xF) + ((cpuid >> 20) & 0xFF) if ((cpuid >> 8) & 0xF) == 0xF else ((cpuid >> 8) & 0xF)),
                 mod := (((cpuid >> 4) & 0xF) + ((cpuid >> 12) & 0xF0) if fam in (0x6, 0xF) else ((cpuid >> 4) & 0xF)),
                 (fam, mod) in [(0x6, 0xBF)])[2] for off, ver, cpuid, date, size in unique)
# 上面这行可能语法有问题，让我直接重做检测
has_rpl_r = False
for off, ver, cpuid, date, size in unique:
    fam = (cpuid >> 8) & 0xF
    if fam == 0xF:
        fam += (cpuid >> 20) & 0xFF
    mod = (cpuid >> 4) & 0xF
    if fam in (0x6, 0xF):
        mod += (cpuid >> 12) & 0xF0
    if (fam, mod) == (0x6, 0xBF):
        has_rpl_r = True
        break

print()
print(f"14 代 RPL-R microcode: {'[+] 存在' if has_rpl_r else '[-] 不存在'}")
