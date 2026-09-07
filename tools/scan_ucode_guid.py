#!/usr/bin/env python3
"""搜 microcode 文件 GUID (EFI_FIRMWARE_FILETYPE_MICROCODE)"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = open(
    "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin",
    "rb"
).read()

# EFI_PI_MICROCODE_GUID = {0xE08CA7D2, 0x1B52, 0x4F0D, {0x92, 0x97, 0x3B, 0xC2, 0xE3, 0x8D, 0xF9, 0xDC}}
# 存储（UEFI mixed-endian）：
#   bytes 0-3 (uint32 LE): 0xE08CA7D2 -> D2 A7 8C E0
#   bytes 4-5 (uint16 LE): 0x1B52 -> 52 1B
#   bytes 6-7 (uint16 LE): 0x4F0D -> 0D 4F
#   bytes 8-15 (uint8 BE): 92 97 3B C2 E3 8D F9 DC
ucode_guid = bytes.fromhex("D2A78CE0521B0D4F92973BC2E38DF9DC")
print(f"Microcode GUID 字节序: {ucode_guid.hex()}")
print()

print("=== 搜 microcode GUID ===")
matches = []
pos = 0
while True:
    pos = data.find(ucode_guid, pos)
    if pos < 0:
        break
    matches.append(pos)
    if len(matches) <= 10:
        # 显示上下文
        for j in range(0, 64, 16):
            line = " ".join(f"{b:02x}" for b in data[pos + j:pos + j + 16])
            print(f"  0x{pos + j:08x}: {line}")
    pos += 1

print(f"\n共 {len(matches)} 个 microcode GUID 匹配点")

# 找 microcode 容器的另一种方法：
# 文件 type 在 FFS header 0x12 位置 = 0x01 (microcode)
# 文件 size 在 0x18 位置（DWORD）
# 文件后面紧跟 EFI_FIRMWARE_FILE_HEADER + EFI_FIRMWARE_VOLUME_HEADER
print()
print("=== 用 FFS header type=0x01 (microcode) 找 ===")
ffs_hits = []
for i in range(0, len(data) - 0x20, 0x10):
    if i + 0x20 > len(data): continue
    # FFS header 0x12 位置是 type
    ftype = data[i + 0x12]
    fsize = struct.unpack("<I", data[i + 0x18:i + 0x1C])[0]
    # FFS GUID 头 0x00-0x0F
    guid_head = data[i:i + 4]
    # 严格 type 0x01 + size 0x800-0x4000
    if ftype == 0x01 and 0x800 <= fsize <= 0x4000:
        # 文件内容起点 (header 后) = i + 0x18
        if i + 0x18 + 0x20 > len(data): continue
        # microcode payload 头
        # EFI_MICROCODE_HEADER:
        #   uint32_t HeaderVersion (1)
        #   uint32_t UpdateRevision
        #   uint32_t Date
        #   uint32_t ProcessorSignature (CPUID)
        #   uint32_t ProcessorFlags (1)
        #   uint32_t Platform
        #   uint32_t DataSize
        #   uint32_t TotalSize
        #   uint32_t Reserved[3]
        payload = i + 0x18
        hdr_ver = struct.unpack("<I", data[payload:payload + 4])[0]
        ucode_rev = struct.unpack("<I", data[payload + 4:payload + 8])[0]
        ucode_date = struct.unpack("<I", data[payload + 8:payload + 12])[0]
        ucode_cpuid = struct.unpack("<I", data[payload + 12:payload + 16])[0]
        if hdr_ver == 1 and 0 < ucode_rev < 0x300 and 0 < ucode_date < 0x300000 and 0 < ucode_cpuid < 0x100000000:
            fam = (ucode_cpuid >> 8) & 0xF
            if fam == 0xF: fam += (ucode_cpuid >> 20) & 0xFF
            mod = (ucode_cpuid >> 4) & 0xF
            if fam in (0x6, 0xF): mod += (ucode_cpuid >> 12) & 0xF0
            d = ucode_date
            date = f"{(d>>16)&0xffff:04d}-{(d>>8)&0xff:02d}-{d&0xff:02d}"
            names = {
                (0x6, 0x97): "ADL-S (12代)", (0x6, 0x9E): "KBL (7代)",
                (0x6, 0x9F): "CFL (8/9代)", (0x6, 0xA5): "CML (10代)",
                (0x6, 0xB7): "RPL (13代)", (0x6, 0xBA): "RPL-P",
                (0x6, 0xBF): "RPL-R (14代)",
                (0x6, 0xAA): "MTL (新)", (0x6, 0xAC): "MTL",
            }
            nm = names.get((fam, mod), f"F{fam}/M0x{mod:x}")
            ffs_hits.append((i, ucode_rev, ucode_cpuid, fam, mod, date, fsize, nm))
            if len(ffs_hits) <= 30:
                print(f"  0x{i:08x}: rev=0x{ucode_rev:02x} cpuid=0x{ucode_cpuid:08x} ({nm}) date={date} size=0x{fsize:x}")

print(f"\n共 {len(ffs_hits)} 个 FFS microcode 文件")

# 14 代检测
has_rpl_r = any((fam, mod) == (0x6, 0xBF) for off, rev, cpuid, fam, mod, date, size, nm in ffs_hits)
print(f"14 代 RPL-R microcode: {'[+] 存在' if has_rpl_r else '[-] 不存在'}")
