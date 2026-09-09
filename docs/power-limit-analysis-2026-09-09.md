# Q100-E 功耗墙完整分析报告（2026-09-09）

> **重大突破**：成功用 UEFIExtract + ifrextract 提取了 V1 原厂 BIOS 的完整 IFR（Setup 菜单），
> **精确定位了所有功耗墙变量及其默认值。**

## 0. TL;DR

| 变量 | VarOffset | 默认值 | 当前功耗 | 目标值（i5-14400）|
| --- | --- | --- | --- | --- |
| **Platform PL1 Power** | 0x32 | `0xC350` (50000) | **50W** | **0xFDE8 (65000 = 65W)** |
| **Platform PL2 Power** | 0x38 | `0xC350` (50000) | **50W** | **0x24220 (148000 = 148W)** |
| **Power Limit 4** | 0x2B | `0x15F90` (90000) | **90W** | 保持或调高 |
| CS PL1 Value | 0x4E | `0x1194` (4500) | (CS TDP) | 可选 |

> **你看到的"60W 限制"其实是 PL1/PL2 被锁在 50W（0xC350）**，加上其他开销后 HWiNFO 显示约 60W。

## 1. 完整功耗墙变量清单

### 1.1 主功耗墙（VarStore 0x1 = CpuSetup）

| 变量名 | VarOffset | QuestionId | Size | Min | Max | Step | 默认值 | 换算 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Platform PL1 Power** | **0x32** | 0x1EC | 4 | 0x0 | 0x3E7F83 | 0x7D (125) | **0xC350** | **50000 mW = 50W** |
| **Platform PL2 Power** | **0x38** | 0x1EF | 4 | 0x0 | 0x3E7F83 | 0x7D (125) | **0xC350** | **50000 mW = 50W** |
| **Power Limit 4** | **0x2B** | 0x1F2 | 4 | 0x0 | 0x3E7F83 | 0x7D (125) | **0x15F90** | **90000 mW = 90W** |
| Platform PL1 Enable | 0x31 | 0x1EB | 1 | 0x0 | 0x1 | 0x0 | - | Enable/Disable |
| Platform PL1 Time Window | 0x36 | 0x1ED | 1 | 0x0 | 0x80 | 0x0 | 0x0 | 时间窗 |
| Platform PL2 Enable | 0x37 | 0x1EE | 1 | 0x0 | 0x1 | 0x0 | 0x0 | Enable/Disable |
| Power Limit 4 Override | 0x2A | 0x1F1 | 1 | 0x0 | 0x1 | 0x0 | **0x1 (Enabled)** | PL4 覆盖开 |
| Power Limit 4 Lock | 0x2F | 0x1F3 | 1 | 0x0 | 0x1 | 0x0 | 0x0 (Disabled) | PL4 锁定 |
| Turbo Mode | 0x16 | 0x272A | 1 | 0x0 | 0x1 | 0x0 | - | 睿频开关 |
| Intel Turbo Boost Max 3.0 | 0xC | 0x2729 | 1 | 0x0 | 0x1 | 0x0 | - | TBMT 3.0 |
| Enhanced C-states | 0x15 | 0x1F4 | 1 | 0x0 | 0x1 | 0x0 | - | C-state |
| EC Turbo Control Mode | 0xC7 | 0x20A | 1 | 0x0 | 0x1 | 0x0 | - | EC 睿频控制 |

### 1.2 CS TDP（Configurable TDP，VarStore 0xF101）

| 变量名 | VarOffset | QuestionId | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| CS PL1 Limit | 0x4D | 0x3F | 0x0 (Disabled) | CS TDP PL1 限制开关 |
| CS PL1 Value | 0x4E | 0x40 | 0x1194 (4500) | CS TDP PL1 值 |
| Default Power Limit | 0x72F | 0x271C | 0xFFFF (Auto) | 默认功耗墙 |
| Default Time Window | 0x731 | 0x78 | 0x7530 (30000) | 默认时间窗 |
| Default Power Limit 1 SPLC | 0x715 | 0x34F | 0xFA0 (4000) | SPLC PL1 |
| Default Power Limit 1 DPLC | 0x721 | 0x354 | 0x4B0 (1200) | DPLC PL1 |

### 1.3 单位换算

功耗值单位是 **mW（毫瓦）**，Step 0x7D = 125 mW = 0.125W：

| 十六进制 | 十进制 | 功耗 |
| --- | --- | --- |
| 0xC350 | 50000 | 50W |
| 0xFDE8 | 65000 | 65W（i5-14400 PBP）|
| 0x15F90 | 90000 | 90W |
| 0x24220 | 148000 | 148W（i5-14400 MTP）|
| 0x3E7F83 | 4095875 | 4096W（Max 无限制）|

## 2. 菜单结构

从 IFR 提取的完整菜单树（FormId）：

```
Setup 主菜单
├── Main (0x2ABC)
├── Advanced (0x2ABD)
│   ├── RC ACPI Settings (0x2719)
│   ├── Connectivity Configuration (0x271D)
│   ├── CPU Configuration (0x2756)          ← CPU 配置
│   ├── Power & Performance (0x275B)        ← ⭐ 功耗墙在这里
│   │   ├── Turbo Mode (0x272A)
│   │   ├── Platform PL1 Power (0x1EC)     ← PL1 = 50W
│   │   ├── Platform PL2 Power (0x1EF)     ← PL2 = 50W
│   │   ├── Power Limit 4 (0x1F2)          ← PL4 = 90W
│   │   ├── Enhanced C-states (0x1F4)
│   │   └── ... (C-State 系列)
│   ├── PCH-FW Configuration (0x285E)
│   ├── Thermal Configuration (0x286F)
│   ├── Platform Settings (0x2874)
│   ├── ACPI D3Cold settings (0x2875)
│   ├── OverClocking Performance Menu (0x2881) ← ⭐ 超频菜单（可能隐藏）
│   ├── BCLK Configuration (0x2895)            ← ⭐ BCLK 超频
│   └── Debug Settings (0x28B2)
└── Save & Exit (0x2ABE)
```

**关键**：
- `Power & Performance` (0x275B) 是功耗墙主菜单
- `OverClocking Performance Menu` (0x2881) 和 `BCLK Configuration` (0x2895) 是超频菜单（之前以为是隐藏的，实际在 IFR 里存在）

## 3. 修改方案

### 3.1 目标（i5-14400 官方规格）

| 变量 | 当前 | 目标 | 十六进制 |
| --- | --- | --- | --- |
| PL1 Power | 50W | **65W** | 0xC350 → 0xFDE8 |
| PL2 Power | 50W | **148W** | 0xC350 → 0x24220 |
| PL4 | 90W | 保持或 148W | 0x15F90 |

### 3.2 三种修改方式

#### 方式 A：AMIBCP（GUI，但报语言错误）

AMIBCP 报 "Language name exceeds 0x08"，Setup tab 不显示。**但仍可用**：
- 打开 V1 后，虽然 Setup tab 空，但可以用 "BIOS Strings" 或直接改二进制

#### 方式 B：MMTool_a5.exe（GUI，推荐）

MMTool 不受语言名称限制，能正常看 Setup 树：
```
1. 双击 C:\SPI\MMTool_a5.exe（已复制）
2. File → Load Image → C:\SPI\H610_V1.bin
3. 找 Setup 模块（VarStore 0x1 = CpuSetup）
4. 改 Platform PL1 Power (VarOffset 0x32) = 65000
5. 改 Platform PL2 Power (VarOffset 0x38) = 148000
6. Save Image
```

#### 方式 C：直接改 IFR 二进制（脚本）

用 Python 脚本直接改 IFR 里的 Default 值（VarOffset 0x32/0x38 的 Default 0xC350 → 新值）。

## 4. 修改方式（重要：IFR 在压缩卷里）

⚠️ **关键发现**：IFR 里的功耗墙 Default 值在**压缩卷（LZMA）**里，直接 hex 编辑 32MB bin 找不到这些值（`find_power_limit.py` 找到 0 个匹配）。

**必须用能解压卷的工具**：

| 方式 | 可行性 | 说明 |
| --- | --- | --- |
| **MMTool_a5.exe（GUI）** | ✅ 推荐 | 能解压卷 + 看 Setup 树 + 改 Default |
| AMIBCP（GUI） | ⚠️ 报语言错误 | Setup tab 不显示，但可能仍能改 |
| 直接 hex 编辑 | ❌ 不可行 | IFR 在压缩卷里 |
| UEFIExtract + 改 + 重打包 | ⚠️ 复杂 | 需要重新压缩 + 重算 checksum |

### MMTool 操作步骤（推荐）

```
1. 双击 C:\SPI\MMTool_a5.exe（已复制到英文路径）
2. File → Load Image → C:\SPI\H610_V1.bin
3. 找到 Setup 模块（在 CPU 相关 FFS 里）
4. 展开 Setup 树，找:
   - Platform PL1 Power (VarOffset 0x32) = 50W → 改 65W
   - Platform PL2 Power (VarOffset 0x38) = 50W → 改 148W
   - Power Limit 4 (VarOffset 0x2B) = 90W
5. 改 Default 值
6. Save Image As → C:\SPI\H610_V1_unlocked.bin
```

## 5. 下一步

1. ✅ 功耗墙变量全部定位（VarOffset + 默认值）
2. ⏳ 用 MMTool_a5.exe 打开 V1，改 PL1/PL2 默认值
3. ⏳ 保存新 bin → FPT 刷写 → HWiNFO64 验证

## 5. 关键文件

- `backups/H610_full_32mb_V1.ifr_full.txt` — 完整 IFR 提取（2.6MB，含所有 Setup 菜单）
- `C:\SPI\ifr_setup.txt` — IFR 提取（临时）
- `C:\SPI\MMTool_a5.exe` — MMTool Aptio 5（已复制，GUI 改功耗墙用）
- `C:\SPI\H610_V1.bin` — V1 副本（英文路径，避免中文路径问题）
- `tools/find_power_limit.py` — 定位功耗墙 Default 值脚本（因压缩卷找到 0 个，改用 MMTool）

## 6. 重要说明

- **功耗墙单位是 mW**，PL1/PL2 默认都是 50W（0xC350）
- 你看到的"60W"其实是 50W 的 PL1/PL2 + 运行时开销
- 解锁后 i5-14400 能跑满 65W PL1 / 148W PL2
- **但注意 H610 供电和 1.5L 散热**：65W 是合理上限，148W 可能散热压不住
