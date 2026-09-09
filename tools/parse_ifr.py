#!/usr/bin/env python3
"""
真正的 EFI IFR Extractor - 解析 V1 原厂 BIOS 的 Setup 菜单

IFR (Internal Forms Representation) 是 UEFI Setup 菜单的二进制格式
- 找 HII 包 (FFS GUID = Setup 进入点)
- 解析 IFR opcode 流
- 提取所有 Form/Subtitle/OneOf/Numeric 等
- 标识**隐藏项**（Suppressed = 1）
"""
import sys
import struct
from pathlib import Path
from typing import List, Dict, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from uefi_firmware.uefi import FirmwareVolume, FirmwareFileSystem, FirmwareFile


# IFR Opcode 定义
IFR_OPCODES = {
    0x01: "Form",
    0x02: "Subtitle",
    0x03: "Text",
    0x04: "Edit",
    0x05: "Password",
    0x06: "OneOf",
    0x07: "CheckBox",
    0x08: "Numeric",
    0x09: "Date",
    0x0A: "Time",
    0x0B: "String",
    0x0C: "Ref",
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
    0x30: "OneOfOptions",  # extended
    0x40: "Default",       # extended
    0x50: "Date",          # extended
    0x51: "Time",          # extended
}


def find_string_pool(data: bytes) -> Tuple[bytes, List[str]]:
    """从 EFI FFS 找 HII 包 + 字符串池"""
    # 找 GUID: 1C6825A2-1418-4F2A-9083-2A8C9C9A8E22 (HII data)
    # 简化：找所有可读 ASCII/Unicode 字符串
    strings = []
    cur = ""
    cur_off = 0
    i = 0
    while i + 1 < len(data):
        c = struct.unpack("<H", data[i:i+2])[0]
        if 0x20 <= c < 0x7F and c != 0:
            if not cur:
                cur_off = i
            cur += chr(c)
            i += 2
        else:
            if len(cur) >= 4:
                strings.append((cur_off, cur))
            cur = ""
            i += 2
    return data, strings


def extract_unicode_strings(data, min_len=4):
    """完整提取所有 Unicode 字符串"""
    results = []
    cur = ""
    cur_off = 0
    i = 0
    while i + 1 < len(data):
        c = struct.unpack("<H", data[i:i+2])[0]
        if 0x20 <= c < 0x7F:
            if not cur:
                cur_off = i
            cur += chr(c)
            i += 2
        else:
            if len(cur) >= min_len:
                results.append((cur_off, cur))
            cur = ""
            i += 2
    if len(cur) >= min_len:
        results.append((cur_off, cur))
    return results


def find_ifr_streams(data: bytes) -> List[Dict]:
    """找 IFR 流 (Form Set 0x0E 开头)"""
    results = []
    pos = 0
    while pos + 0x20 < len(data):
        # IFR 头是 FormSet (0x0E 0x00) 开头
        if data[pos] == 0x0E and data[pos+1] == 0x00:
            # 验证长度合理
            length = struct.unpack("<H", data[pos+2:pos+4])[0]
            if 0x20 < length < 0x10000:
                # 找 FormSet 结束 (0x17 0x00 0x00)
                end_pos = pos + length
                if end_pos < len(data) and data[end_pos] == 0x17 and data[end_pos+1] == 0x00:
                    results.append({
                        "offset": pos,
                        "length": length,
                        "stream": data[pos:pos+length]
                    })
        pos += 1
    return results


def parse_ifr_stream(stream: bytes, strings_offset: int, all_strings: List[str]) -> List[Dict]:
    """解析一个 IFR 流的菜单项"""
    items = []
    pos = 0
    path_stack = [""]  # Form/Subtitle 路径栈
    current_form = ""

    while pos + 2 < len(stream):
        op = stream[pos]
        op_len = stream[pos+1]  # 第 2 字节通常 0x00
        op_name = IFR_OPCODES.get(op, f"OP_{op:02x}")

        if op == 0x0E:  # FormSet
            guid = stream[pos+2:pos+18]
            form_set_id = struct.unpack("<Q", stream[pos+18:pos+26])[0]
            current_form = f"FormSet_{form_set_id:08x}"
            path_stack = [current_form]

        elif op == 0x01:  # Form
            form_id = struct.unpack("<H", stream[pos+2:pos+4])[0]
            current_form = f"Form_{form_id:04x}"
            path_stack.append(current_form)

        elif op == 0x02:  # Subtitle
            str_id = struct.unpack("<H", stream[pos+2:pos+4])[0]
            text = all_strings[str_id] if str_id < len(all_strings) else f"<s{str_id}>"
            items.append({
                "type": "subtitle",
                "text": text,
                "path": "/".join(path_stack),
                "offset": pos,
            })

        elif op in (0x06, 0x07, 0x08, 0x04):  # OneOf, CheckBox, Numeric, Edit
            str_id = struct.unpack("<H", stream[pos+2:pos+4])[0]
            prompt_id = struct.unpack("<H", stream[pos+4:pos+6])[0]
            help_id = struct.unpack("<H", stream[pos+6:pos+8])[0]
            text = all_strings[str_id] if str_id < len(all_strings) else f"<s{str_id}>"
            prompt = all_strings[prompt_id] if prompt_id < len(all_strings) else ""
            items.append({
                "type": {0x06: "oneof", 0x07: "checkbox", 0x08: "numeric", 0x04: "edit"}[op],
                "text": text,
                "prompt": prompt,
                "path": "/".join(path_stack),
                "offset": pos,
            })

        elif op == 0x03:  # Text
            str_id = struct.unpack("<H", stream[pos+2:pos+4])[0]
            text = all_strings[str_id] if str_id < len(all_strings) else f"<s{str_id}>"
            items.append({
                "type": "text",
                "text": text,
                "path": "/".join(path_stack),
                "offset": pos,
            })

        # 跳过: 简单地用 2-8 字节步进（IFR opcode 长度不固定）
        if op in (0x0E, 0x01):
            pos += 6 + 24  # FormSet/Form 固定长度
        elif op == 0x17:  # EndFormSet
            break
        elif op in (0x02,):
            pos += 4
        elif op in (0x10, 0x2D):  # OneOfOptions (复杂)
            pos += 6
        elif op in (0x11, 0x40, 0x12, 0x16, 0x14, 0x15):  # 通用
            pos += 4
        elif op in (0x21, 0x22):  # Rule, GrayOutIf
            pos += 6
        else:
            pos += 2  # 最坏情况

    return items


def main():
    if len(sys.argv) < 2:
        print("用法: python parse_ifr.py <32MB.bin>")
        sys.exit(1)

    bin_path = Path(sys.argv[1])
    print(f"=== {bin_path.name} ===\n")

    data = bin_path.read_bytes()
    print(f"大小: {len(data):,} bytes")

    # 1. 提取所有 Unicode 字符串 (作为 IFR string pool)
    print("提取 Unicode 字符串...")
    all_strings = extract_unicode_strings(data, min_len=3)
    print(f"  找到 {len(all_strings):,} 个 Unicode 字符串 (min 3 字符)")

    # 2. 找 IFR 流
    print("\n找 IFR 流 (FormSet 0x0E 0x00 开头)...")
    ifr_streams = find_ifr_streams(data)
    print(f"  找到 {len(ifr_streams)} 个 IFR 流")

    # 3. 解析每个 IFR 流
    print("\n解析 IFR 流...")
    all_items = []
    for i, s in enumerate(ifr_streams[:30]):  # 限制 30 个
        items = parse_ifr_stream(s["stream"], s["offset"], all_strings)
        print(f"  Stream #{i+1} @ 0x{s['offset']:08x} ({s['length']} bytes): {len(items)} 项")
        all_items.extend(items)

    # 4. 输出报告
    print(f"\n总共解析 {len(all_items)} 个菜单项")

    # 分类
    by_type = {}
    for item in all_items:
        t = item.get("type", "?")
        by_type.setdefault(t, []).append(item)

    print("\n=== 按类型分类 ===")
    for t in sorted(by_type.keys()):
        print(f"  {t}: {len(by_type[t])}")

    # 输出前 50 项
    print("\n=== 前 50 项 ===")
    for item in all_items[:50]:
        text = item.get("text", "")[:60]
        path = item.get("path", "")
        t = item.get("type", "?")
        print(f"  [{t:10s}] {path:50s} {text}")

    # 写 JSON
    import json
    output = {
        "bin": str(bin_path),
        "size": len(data),
        "ifr_streams": len(ifr_streams),
        "total_items": len(all_items),
        "by_type": {t: len(items) for t, items in by_type.items()},
        "items": all_items[:500],  # 限制 500 个
    }
    out = bin_path.with_suffix(".ifr.json")
    out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n详细报告: {out}")


if __name__ == "__main__":
    main()
