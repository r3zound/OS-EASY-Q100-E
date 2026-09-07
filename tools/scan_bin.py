#!/usr/bin/env python3
"""一次性扫描脚本：dump 头部 + 找 microcode + 找 _FIT_ + 找 ME 标识"""
import sys
import struct

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

bin_path = sys.argv[1] if len(sys.argv) > 1 else "D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin"
data = open(bin_path, "rb").read()
print(f"文件: {bin_path}")
print(f"大小: {len(data)} bytes ({len(data)/1024/1024:.2f} MB)\n")

# === 头部 256 字节 ===
print("=== 头部 256 字节 hex dump ===")
for i in range(0, 0x100, 16):
    hex_str = " ".join(f"{b:02x}" for b in data[i:i+16])
    asc = "".join(chr(b) if 32 <= b < 127 else "." for b in data[i:i+16])
    print(f"  0x{i:04x}: {hex_str}  {asc}")

# === 找 microcode 模式 ===
print()
print("=== 找 microcode 模式 (loader_sig 1,1) ===")
target = bytes([1, 0, 0, 0, 1, 0, 0, 0])
count = 0
for i in range(0, len(data) - 0x30, 0x800):
    if data[i:i+8] == target:
        rev = struct.unpack("<I", data[i+12:i+16])[0]
        rev_id = struct.unpack("<I", data[i+16:i+20])[0]
        cpuid = struct.unpack("<I", data[i+20:i+24])[0]
        ucode_date = struct.unpack("<I", data[i+28:i+32])[0]
        if rev_id == 1 and cpuid != 0 and cpuid != 0xFFFFFFFF and ucode_date < 0x300000:
            count += 1
            if count <= 50:
                d = ucode_date
                date = f"{d>>16:04d}-{(d>>8)&0xff:02d}-{d&0xff:02d}"
                fam = (cpuid >> 8) & 0xF
                mod = (cpuid >> 4) & 0xF
                if fam == 0x6:
                    mod += (cpuid >> 12) & 0xF0
                print(f"  [+] 0x{i:08x}: rev=0x{rev:02x} cpuid=0x{cpuid:08x} F{fam}/M0x{mod:x} date={date}")
print(f"共找到 {count} 个 microcode 容器（0x800 步长扫全 bin）")

# === 找 _FIT_ ===
print()
print("=== 找 _FIT_ 头部 ===")
fit_found = False
for i in range(0, 0x400000, 0x10):
    if data[i:i+4] == b"_FIT_":
        fit_found = True
        print(f"  [+] 0x{i:08x}: _FIT_ found")
        for j in range(0, 64, 16):
            print(f"    0x{i+j:08x}: " + " ".join(f"{b:02x}" for b in data[i+j:i+j+16]))
        break
if not fit_found:
    print("  [-] 0x000000 - 0x400000 内未找到 _FIT_")

# === 找 ME 标识 ===
print()
print("=== 找 ME 区域标识 ===")
for sig in [b"$FPT", b"$MME", b"MEFW", b"Intel(R) Management Engine", b"ME Version:"]:
    pos = 0
    while True:
        pos = data.find(sig, pos)
        if pos < 0:
            break
        if pos < 0x2000000:
            ctx = data[pos:pos+80]
            printable = "".join(chr(b) if 32 <= b < 127 else "." for b in ctx[:40])
            print(f"  [+] 0x{pos:08x}: '{sig.decode('latin-1')}' → {printable}")
        pos += 1

# === 找 4KB 边界 + 内容非 FF 的区域（找 flash 实际使用范围）===
print()
print("=== 找实际 flash 使用范围（4KB 边界非全 FF）===")
in_use = False
ranges = []
start = 0
for off in range(0, len(data), 0x1000):
    if any(b != 0xFF for b in data[off:off+0x1000]):
        if not in_use:
            start = off
            in_use = True
    else:
        if in_use:
            ranges.append((start, off))
            in_use = False
if in_use:
    ranges.append((start, len(data)))

print(f"  共 {len(ranges)} 段非空数据：")
for s, e in ranges[:20]:
    print(f"    0x{s:08x} - 0x{e-1:08x}  ({e-s} bytes, { (e-s)/1024:.0f} KB)")
if len(ranges) > 20:
    print(f"    ... 及其他 {len(ranges)-20} 段")
