#!/usr/bin/env python3
"""
深度扫描：找 EFI IFR opcodes + Setup 相关结构
"""
import sys
import struct
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    if len(sys.argv) < 2:
        print("用法: python scan_ifr.py <bin>")
        sys.exit(1)

    data = Path(sys.argv[1]).read_bytes()
    print(f"=== {sys.argv[1]} ===\n")

    # EFI IFR opcodes (UEFI Spec)
    IFR_OPCODES = {
        0x01: "Form",
        0x02: "Subtitle",
        0x03: "Text",
        0x04: "Edit (text)",
        0x05: "Password",
        0x06: "OneOf (select)",
        0x07: "CheckBox",
        0x08: "Numeric",
        0x09: "Date",
        0x0A: "Time",
        0x0B: "String",
        0x0C: "Ref (reference)",
        0x0D: "ResetButton",
        0x0E: "FormSet",
        0x0F: "Ref2",
        0x10: "OneOfOptions",
        0x11: "Default",
        0x12: "DefaultStore",
        0x13: "Value",
        0x14: "Disabled",
        0x15: "Action",
        0x16: "Reset",
        0x17: "FormSet",
        0x18: "Ref3",
        0x19: "NoSubmitIf",
        0x1A: "InconsistentIf",
        0x1B: "EqIdVal",
        0x1C: "EqIdId",
        0x1D: "EqIdValList",
        0x1E: "And",
        0x1F: "Or",
        0x20: "Not",
        0x21: "Rule",
        0x22: "GrayOutIf",
        0x23: "Date",
        0x24: "Time",
        0x25: "String",
        0x26: "Refresh",
        0x27: "DisableIf",
        0x28: "Action",
        0x29: "ResetButton",
        0x2A: "FormSet",
        0x2B: "Ref4",
        0x2C: "DisableIf",
        0x2D: "OneOfOptions",
        0x2E: "Goto",
        0x2F: "Banner",
    }

    # BIOS region 0x01000000-0x02000000
    region = data[0x01000000:0x02000000]

    # 找所有 IFR Form (0x01) - Setup 菜单入口
    print("=== 找 IFR Form (opcode 0x01) - Setup 菜单 ===")
    forms = []
    i = 0
    while i < len(region) - 4:
        if region[i] == 0x01 and region[i+1] == 0x00:
            # 0x01 0x00 0x?? 0x?? 是 Form 头
            forms.append(i + 0x01000000)
        i += 4
    print(f"  找到 {len(forms)} 个 IFR Form (Setup 菜单入口)")
    for off in forms[:30]:
        print(f"    0x{off:08x}")

    # 找 FormSet (0x0E) - 顶级菜单
    print()
    print("=== 找 IFR FormSet (opcode 0x0E) ===")
    formsets = []
    i = 0
    while i < len(region) - 4:
        if region[i] == 0x0E and region[i+1] == 0x00:
            formsets.append(i + 0x01000000)
        i += 4
    print(f"  找到 {len(formsets)} 个 IFR FormSet")
    for off in formsets[:30]:
        print(f"    0x{off:08x}")

    # 找 OneOf (0x06) - 选择型 Setup 项
    print()
    print("=== 找 IFR OneOf (opcode 0x06) - 选择型 Setup 项 ===")
    oneofs = []
    i = 0
    while i < len(region) - 4:
        if region[i] == 0x06 and region[i+1] == 0x00:
            oneofs.append(i + 0x01000000)
        i += 4
    print(f"  找到 {len(oneofs)} 个 IFR OneOf")
    for off in oneofs[:20]:
        print(f"    0x{off:08x}")

    # 找所有 IFR 头 (按 opcode 分组)
    print()
    print("=== 所有 IFR 头 (按 opcode 统计) ===")
    opcodes = {}
    i = 0
    while i < len(region) - 2:
        op = region[i]
        # 验证：第二个字节是长度（>0, < 0x80）
        if 0 < region[i+1] < 0x80 and 0x01 <= op <= 0x30:
            opcodes[op] = opcodes.get(op, 0) + 1
        i += 1
    for op, cnt in sorted(opcodes.items(), key=lambda x: -x[1]):
        name = IFR_OPCODES.get(op, f"Unknown (0x{op:02x})")
        print(f"  opcode 0x{op:02x} ({name}): {cnt} 个")

    # 找 ICC Advanced Setup Data Variable
    print()
    print("=== ICC Advanced Setup Data Variable ===")
    var_str = b"IccAdvancedSetupDataVar"
    pos = 0
    while True:
        pos = data.find(var_str, pos)
        if pos < 0: break
        print(f"  0x{pos:08x}: IccAdvancedSetupDataVar")
        pos += 1

    # 找关键 HII Form GUID
    print()
    print("=== 关键 Setup Form GUID 搜索 ===")
    # ICC Setup Form GUID: 0xC3E1B4D5, 0x1234, 0xABCD, ...
    # 实际 ICC 的是 intel ICC GUID
    common_guids = [
        # CpuSetup: B2DA8B53-... (AMI)
        # PchSetup: ...
        # 一般搜: CpuSetup, PchSetup, MeSetup
    ]
    for var in [b"CpuSetup", b"PchSetup", b"MeSetup", b"IccAdvancedSetupDataVar",
                b"SecureBootSetup", b"BoardInfoSetup", b"PlatformLastLangCodes",
                b"MemoryConfig", b"MonotonicCounter", b"AcousticVarName",
                b"AMITCGPPIVAR", b"TPMPERBIOSFLAGS", b"UsbTypeC"]:
        pos = 0
        cnt = 0
        first = -1
        while True:
            pos = data.find(var, pos)
            if pos < 0: break
            if first < 0: first = pos
            cnt += 1
            pos += 1
        if cnt > 0:
            print(f"  '{var.decode()}': {cnt} 个, 首在 0x{first:08x}")


if __name__ == "__main__":
    main()
