#!/usr/bin/env python3
"""第四轮：找 FFS Microcode 文件 (搜 GUID)"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = open(sys.argv[1] if len(sys.argv) > 1 else
            "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
            "rb").read()
print(f"文件大小: {len(data)} bytes\n")

# 已知 microcode 相关 GUID
# Intel microcode 容器 GUID: 0x197DB236-F11A-4FD3-9A6C-000000000000 (但存储可能是 reversed)
# BIOS region GUID: 0x1B2A7C28-7B47-4D0F-89E2-7B6B7E3C0000 (AMI BIOS region)
# FIT pointer GUID: 0x1B2A7C28-7B47-4D0F-89E2-7B6B7E3C0000
# 等等

# 让我先扫一些常见 microcode GUID (大端)
guids_to_check = [
    "197DB236-F11A-4FD3-9A6C-000000000000",  # microcode 标准
    "197DB236-F11A-4FD3-9A6C-1234567890AB",  # 变体
    "B7F0A7E0-7B47-4D0F-89E2-7B6B7E3C0000",  # ?
    "E08CA7D2-1B52-4F0D-9297-3BC2E38DF9DC",  # 旧 microcode
    "DE5F5680-1B0E-4CFA-9B6B-1BF5C0000001",  # ?
]

# GUID 字节序
import uuid
def parse_guid(s):
    # 大端 -> 实际存储（GUID 是混合字节序）
    u = uuid.UUID(s)
    return u.bytes_le  # UEFI 用 LE

print("=== 搜已知 microcode GUID ===")
for g in guids_to_check:
    try:
        b = parse_guid(g)
    except Exception:
        continue
    pos = 0
    while True:
        pos = data.find(b, pos)
        if pos < 0: break
        print(f"  [+] 0x{pos:08x}: GUID {g}")
        for j in range(0, 64, 16):
            print("    0x{:08x}: {}".format(pos + j, " ".join(f"{b:02x}" for b in data[pos + j:pos + j + 16])))
        pos += 1

# 现在搜 GUID 头（看 GUID 后 0x14 位置 type）
# microcode 文件 GUID 通常以 197D 开头
print()
print("=== 扫所有以 197D 开头的 GUID ===")
hits = []
for i in range(0, len(data) - 24, 0x10):
    if data[i:i+2] == bytes.fromhex("197d"):
        # 验证 FFS header: 0x14-0x17 type (1=microcode), 0x18-0x1B size
        if i + 0x24 > len(data): continue
        ftype = data[i + 0x14]
        size = struct.unpack("<I", data[i + 0x18:i + 0x1C])[0]
        # 0x1C 位置（紧接 FFS header 后）才是 microcode payload 头
        if ftype == 0x01 and 0x800 <= size <= 0x4000:
            # 验证 microcode payload 头
            if i + 0x40 > len(data): continue
            # payload 起点 = i + 0x18 + (header 长度？)
            # 实际 FFS header 是 24 字节 (0x18)，紧接着是 file body
            payload_start = i + 0x18
            # microcode payload 头 (0x18 位置) type
            if payload_start + 0x20 > len(data): continue
            # microcode 头: 0x00 type (1), 0x04 rev, 0x08 date, 0x0C cpuid
            uc_type = struct.unpack("<I", data[payload_start:payload_start + 4])[0]
            uc_rev = struct.unpack("<I", data[payload_start + 4:payload_start + 8])[0]
            uc_date = struct.unpack("<I", data[payload_start + 8:payload_start + 12])[0]
            uc_cpuid = struct.unpack("<I", data[payload_start + 12:payload_start + 16])[0]
            # microcode 头通常是: type=1, rev=0xB7+, date=0xYYYYMMDD, cpuid=0x000XXXXX
            if uc_type == 1 and 0 < uc_rev < 0x300 and 0 < uc_date < 0x300000 and 0 < uc_cpuid < 0x100000000:
                fam = (uc_cpuid >> 8) & 0xF
                if fam == 0xF: fam += (uc_cpuid >> 20) & 0xFF
                mod = (uc_cpuid >> 4) & 0xF
                if fam in (0x6, 0xF): mod += (uc_cpuid >> 12) & 0xF0
                d = uc_date
                date = f"{(d>>16)&0xffff:04d}-{(d>>8)&0xff:02d}-{d&0xff:02d}"
                hits.append((i, uc_rev, uc_cpuid, fam, mod, date, size))

seen = set()
unique = []
for h in hits:
    if h[0] not in seen:
        seen.add(h[0])
        unique.append(h)

print(f"找到 {len(unique)} 个 microcode 文件（GUID 197D 开头 + payload 头匹配）：\n")
print(f"  {'#':>3s}  {'偏移':>10s}  {'版本':>6s}  {'日期':>12s}  "
      f"{'CPUID':>10s}  {'F/M':>10s}  {'size':>6s}  代号")
print(f"  {'-'*3}  {'-'*10}  {'-'*6}  {'-'*12}  {'-'*10}  {'-'*10}  {'-'*6}  {'-'*25}")
for idx, (off, ver, cpuid, fam, mod, date, size) in enumerate(unique, 1):
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
          f"0x{cpuid:08x}  {fm:>10s}  0x{size:04x}  {nm}")

# 14 代检测
has_rpl_r = any((fam, mod) == (0x6, 0xBF) for off, ver, cpuid, fam, mod, date, size in unique)
print()
print(f"14 代 RPL-R microcode: {'[+] 存在' if has_rpl_r else '[-] 不存在'}")
