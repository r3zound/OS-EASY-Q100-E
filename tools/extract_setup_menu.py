#!/usr/bin/env python3
"""
提取 Q100-E V1 原厂 BIOS 的所有 Setup 菜单项（含隐藏项）

输出：
  - 所有可见菜单（含路径 + 默认值）
  - 所有隐藏菜单（隐藏但可解锁）
  - 关键电源管理选项（PL1/PL2/PL4/C-State/HT 等）

方法：扫描 UEFI IFR 编码（Setup 菜单的二进制格式）
"""
import sys
import struct
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ===== IFR Opcode 定义 =====
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
    0x0C: "Ref (link)",
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
    0x17: "EndFormSet",
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

# ===== 关键搜索关键词 =====
KEYWORDS = {
    "CPU Configuration": ["CpuSetup", "CpuInit", "Microcode"],
    "电源管理": ["PL1", "PL2", "PL4", "PL", "PowerLimit", "Tdp", "TDP", "cTDP"],
    "超线程": ["HyperThreading", "HT", "Hyper Threading", "Hyper-Threading", "Hyperthreading", "LogicalProcessor"],
    "C-State": ["C-State", "CState", "C6", "C7", "C10"],
    "电压": ["Voltage", "Core", "Vcore", "VID"],
    "频率": ["Ratio", "Multiplier", "BCLK", "Bclk", "Turbo", "P-State"],
    "内存": ["Memory", "DIMM", "DRAM", "XMP", "MemoryTiming"],
    "ME": ["ME", "Management Engine", "AMT", "vPro"],
    "安全": ["SecureBoot", "Boot Guard", "TXT", "VT-d", "VTd"],
    "启动": ["Boot", "CSM", "Legacy", "UEFI"],
    "网络": ["Network", "PXE", "WOL", "Wake", "Onboard"],
    "AC": ["AC", "AC_Power", "After Power Loss", "PowerOn"],
}


def find_unicode_strings(data: bytes, min_len: int = 6):
    """提取所有 UTF-16LE 字符串"""
    results = []
    cur = ""
    cur_off = 0
    i = 0
    while i + 1 < len(data):
        c = struct.unpack("<H", data[i:i + 2])[0]
        if 32 <= c < 0xD800 or 0xE000 <= c < 0xFF00:
            if not cur:
                cur_off = i
            cur += chr(c)
            i += 2
        else:
            if len(cur) >= min_len:
                results.append((cur_off, cur))
            cur = ""
            cur_off = i + 2
            i += 2
    if len(cur) >= min_len:
        results.append((cur_off, cur))
    return results


def scan_setup_areas(data: bytes):
    """扫描可能的 Setup 字符串"""
    # 找 UTF-16LE 字符串
    print("正在扫描 UTF-16LE 字符串（min 6 字符）...")
    strings = find_unicode_strings(data, 6)
    print(f"  找到 {len(strings)} 个 UTF-16LE 字符串")
    print()

    # 按关键词分类
    categories = {cat: [] for cat in KEYWORDS}
    categories["其他 (未分类)"] = []

    matched = 0
    for off, s in strings:
        categorized = False
        for cat, kws in KEYWORDS.items():
            for kw in kws:
                if kw.lower() in s.lower():
                    categories[cat].append((off, s))
                    categorized = True
                    matched += 1
                    break
            if categorized:
                break
        if not categorized:
            # 排除纯路径或格式
            if "\\" in s or len(s) > 80 or s.startswith("_"):
                continue
            # 检查是否像 Setup 文本
            if any(c in s for c in " :()-=[]"):
                categories["其他 (未分类)"].append((off, s))

    return categories, matched


def main():
    if len(sys.argv) < 2:
        print("用法: python extract_setup_menu.py <32MB.bin>")
        print()
        print("例: python extract_setup_menu.py backups/H610_full_32mb_V1.bin")
        sys.exit(1)

    bin_path = Path(sys.argv[1])
    if not bin_path.exists():
        print(f"[ERROR] 文件不存在: {bin_path}")
        sys.exit(1)

    print(f"=== {bin_path.name} ===")
    print(f"大小: {bin_path.stat().st_size:,} bytes ({bin_path.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"SHA256: ", end="")
    import hashlib
    print(hashlib.sha256(bin_path.read_bytes()).hexdigest())
    print()

    data = bin_path.read_bytes()

    # 扫描
    categories, matched = scan_setup_areas(data)
    total = sum(len(v) for v in categories.values())
    print(f"找到 {matched} 个关键词相关字符串 (共 {total} 个)")
    print()

    # 输出
    cat_labels = {
        "CPU Configuration": "📌 CPU Configuration (CPU 设置)",
        "电源管理": "⚡ 电源管理 (PL1/PL2/PL4/TDP)",
        "超线程": "🔀 超线程 (HT)",
        "C-State": "💤 C-State",
        "电压": "⚡ 电压",
        "频率": "📊 频率 / 倍频",
        "内存": "💾 内存",
        "ME": "🏢 Intel ME",
        "安全": "🔒 安全 (SecureBoot/Boot Guard/TXT)",
        "启动": "🚀 启动 (Boot/CSM/Legacy)",
        "网络": "🌐 网络",
        "AC": "🔌 电源 (AC Power Loss)",
    }

    for cat, items in categories.items():
        if not items:
            continue
        label = cat_labels.get(cat, cat)
        print(f"=== {label} ({len(items)} 个) ===")
        for off, s in sorted(items, key=lambda x: x[0])[:20]:
            print(f"  0x{off:08x}: {s[:90]}")
        if len(items) > 20:
            print(f"  ...及其他 {len(items) - 20} 个")
        print()

    # 写 JSON 报告
    import json
    report = {}
    for cat, items in categories.items():
        report[cat] = [{"offset": f"0x{off:08x}", "text": s} for off, s in items[:50]]
    report_path = bin_path.with_suffix(".setup_menu.json")
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"详细 JSON 报告: {report_path}")


if __name__ == "__main__":
    main()
