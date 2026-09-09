# Q100-E V1 原厂 Setup 菜单解锁 + LOGO 替换指南（2026-09-09）

> **项目方向修正**：不再研究 microcode 移植（V1 已含 14代 RPL-S microcode）
> **新目标**：解锁隐藏 Setup 菜单 + 替换开机 LOGO

## 0. TL;DR

| 项目 | 状态 |
| --- | --- |
| **V1 原厂 BIOS** | ✅ 已 FPT 备份到 `backups/H610_full_32mb_V1.bin` (32MB) |
| **V1 含 14代 microcode** | ✅ B0671 rev 0x10E (2022-09-19) |
| **i5-14400 直接装** | ✅ 理论上能亮（**不需要任何 BIOS 修改**） |
| **新目标 1: 解锁隐藏菜单** | 待用 AMIBCP/MMTool 操作 |
| **新目标 2: 替换 LOGO** | 待提取原 LOGO + 替换 |

## 1. V1 备份详情

```
文件:   backups/H610_full_32mb_V1.bin
大小:   33,554,432 bytes (32.00 MB)
SHA256: f0b0a2b6f97d826af71f2c08d61e2e518d6dfe4fb4bc7e21c41e926c9d1faf0e
工具:   Intel FPT v16.0.15.1735 (CSME System Tools v16.0 r8)
ME 版本: 16.1.25.1917 (Alder Lake / Raptor Lake)
```

## 2. 微码完整列表

| 代 | CPUID | Rev | Date | 位置 | 大小 |
| --- | --- | --- | --- | --- | --- |
| 12代 ADL-S | 90672 | 26 | 2022-09-19 | 0x1D91000 | 0x35400 |
| 12代 ADL-S ES | 90675 | (extended) | - | 副本 | - |
| **14代 RPL-S Refresh** | **B0671** | **10E** | **2022-09-07** | **0x1DCB000** | **0x32000** |
| 14代 ES2 | B06F2 | 20 | 2022-03-31 | 0x1E05000 | 0x34400 |
| 12代 ADL-S | 90672 | 26 | 2022-09-19 | 0x1E91000 | 0x35400 (副本) |
| **14代 RPL-S Refresh** | **B0671** | **10E** | **2022-09-07** | **0x1ECB000** | **0x32000** (副本) |
| 14代 ES2 | B06F2 | 20 | 2022-03-31 | 0x1F05000 | 0x34400 (副本) |

**i5-14400 (CPUID 0x9067x) 应该能直接装上跑**。

## 3. 解锁隐藏 Setup 菜单（项目目标 1）

### 3.1 工具选择

| 工具 | 推荐度 | 用途 |
| --- | --- | --- |
| **AMIBCP (Aptio Configurator Program)** | ⭐⭐⭐⭐⭐ | 解锁隐藏菜单、改默认值、改类型（suppressed/greyout）|
| **MMTool 5.x (Aptio MMTool)** | ⭐⭐⭐⭐ | 直接编辑 IFR/Setup 树 |
| **UEFITool NE (LongSoft)** | ⭐⭐⭐ | 找 FFS/IFR 位置（辅助）|
| **AMISetupDataEditor** | ⭐⭐ | 改默认值 |
| **MMTOOL (AMI)** | ⭐⭐ | 综合编辑 |

### 3.2 推荐工作流

#### 步骤 1：用 UEFITool NE 找 Setup 模块位置

1. 下载 UEFITool NE: https://github.com/LongSoft/UEFITool/releases
2. 用 UEFITool 打开 V1 bin
3. 找到 HII Setup 模块（搜索 "Setup"）
4. 找 IFR FormSet（通常在 BIOS region 的 `0x1000000-0x1A0000` 范围）
5. 记录 GUID 和 offset

#### 步骤 2：用 AMIBCP 解锁隐藏菜单

1. 下载 AMIBCP (AMI 内部工具): https://www.win-raid.com/t596f39-AMIBCP-v51506.html
2. 用 AMIBCP 打开 V1 bin
3. 浏览 Setup 树（`/Main` → `Advanced` → `CPU Configuration` 等）
4. 找隐藏的菜单（通常灰色显示或带 `(Hidden)` 标记）
5. 关键要解锁的菜单：
   - `Advanced` → `CPU Configuration` → `Hyper-Threading`
   - `Advanced` → `CPU Configuration` → `Active Processor Cores`
   - `Advanced` → `Power Management` → `CPU Power Management`
   - `Advanced` → `Overclocking` (如存在)
   - `Advanced` → `Memory Configuration` → `Memory Timing`
   - `Chipset` → `Voltage Configuration` (如存在)

#### 步骤 3：用 MMTool 改默认值（可选）

1. 打开 MMTool（Windows）
2. File → Load Image → V1 bin
3. 找 Setup 模块
4. 修改默认值（PL1/PL2/PL4 等）
5. Save Image → 输出新 bin

### 3.3 预期解锁的隐藏菜单

| 菜单 | 解锁前 | 解锁后 |
| --- | --- | --- |
| Hyper-Threading | 灰色 | 可改 (Enabled/Disabled) |
| Active Cores | 隐藏 | 可改 (1-8 核) |
| C-State 支持 | 部分 | 全开 |
| PL1/PL2 功耗墙 | 65W 锁定 | 可调到 253W |
| PL3 (Tau) | 隐藏 | 可设时间 |
| PL4 | 隐藏 | 可设值 |
| 电压 (Vcore) | 隐藏 | 可设 |
| Memory XMP | 灰 | 可开 |
| BCLK | 隐藏 | 可设 |

## 4. 替换开机 LOGO（项目目标 2）

### 4.1 LOGO 位置定位

OEM LOGO 在 BIOS region 的 **`0x1F0000-0x200000`** 范围（具体位置需要找）。

查找步骤：
1. 用 UEFITool NE 打开 V1 bin
2. 搜 "logo" / "Logo" 字符串
3. 找到包含 image 数据的 GUID file

V1 bin 中可能的 LOGO 位置（在 BIOS region 0x1000000-0x1FFFFFF 内）：
- 通常在 `0x1F0000-0x200000` (最后 64KB)
- 或在 FFS 文件 `0x12345` GUID 位置

### 4.2 提取原 LOGO

1. 用 UEFITool NE 导出 LOGO 为 BMP
2. 确认 LOGO 大小（通常 1024x768 或 640x480 或 800x600）

### 4.3 替换 LOGO

工具：
- **LogoBuilder** (AMI 工具)
- **ChromaTool** (OEM LOGO 转换工具)
- **YUV-RGB 转换工具**（如需要）

替换步骤：
1. 准备新 LOGO (BMP/JPG)
2. 用 LogoBuilder 转换 LOGO 为 AMI 格式
3. 用 MMTool 替换原 LOGO 数据
4. 重新计算 checksum
5. Save Image

### 4.4 V1 备份 LOGO 提取（建议先做）

1. 用 UEFITool 导出 V1 原 LOGO
2. 保存到 `backups/original_logo.bmp`
3. 这样如果改坏了可以恢复

## 5. 工具下载清单

| 工具 | 来源 |
| --- | --- |
| UEFITool NE | https://github.com/LongSoft/UEFITool/releases |
| AMIBCP | https://www.win-raid.com/t596f39-AMIBCP-v51506.html |
| MMTool 5.x | https://www.win-raid.com/t621f39-AMI-Aptio-5-XX-Toolkit-MMTool-v50306P.html |
| Intel FPT v16.0 | https://www.intel.com/content/www/us/en/download/747929/ |
| CH341A + NeoProgrammer | 淘宝 30-50 元（救砖用）|

## 6. 操作流程

```
1. 备份 V1 (已完成)
2. 提取 V1 原 LOGO 保存为 bmp
3. 用 AMIBCP/MMTool 解锁隐藏菜单
4. 保存新 bin 为 backups/V1_unlocked.bin
5. 替换 LOGO 为自定义图
6. 保存最终 bin 为 backups/V1_beautified.bin
7. 写新 V1 到 SPI flash（先用 FPT 验证 + 备份）
8. 进 BIOS 验证隐藏菜单出现 + LOGO 显示
9. 装 i5-14400 验证 14代 CPU 跑得起来
```

## 7. 已完成的"setup 提取尝试"经验

- 用 `tools/extract_setup_menu.py`：扫了 158,482 个 UTF-16LE 字符串，分类到 1643 个关键词项
- 用 `tools/parse_ifr.py`：扫描 IFR opcode 找到 6 个 IFR 流（33536 字节 / 768 字节），但**需要真正的 string pool 才能解码**（我的实现不完整）
- 结论：IFR 自动提取复杂，**实际工作用 UEFITool NE + AMIBCP 更直接**

## 8. 相关文件

- `backups/H610_full_32mb_V1.bin` — V1 原厂 32MB 备份（**主参考**）
- `backups/H610_full_32mb_V2.bin` — V2 备份（V1==V2 一致性确认）
- `backups/执行记录.md` — FPT 备份完整操作记录
- `backups/H610_SPI备份指导书.docx` — 备份教程
- `backups/CSME System Tools v16.0 r8/` — 完整 Intel ME 工具链
- `tools/extract_setup_menu.py` — Setup 字符串提取（粗略）
- `tools/parse_ifr.py` — IFR opcode 扫描（粗略）
- `tools/parse_ifr_v2.py` — FFS 遍历（实验性）
- `docs/q100e-original-bios-analysis-2026-09-09.md` — V1 完整 microcode 分析

## 9. 下一步

1. **提取 V1 原 LOGO**（保护现状）
2. **用 AMIBCP 跑 V1** 看完整 Setup 树结构
3. **列出要解锁的菜单项**（按用户优先级）
4. **替换 LOGO** 为用户提供的自定义图
5. **烧录 + 测 i5-14400**（验证 14代 + 自定义 LOGO）

## 10. 之前已归档的"错误"文档

这些 V1 已包含 14代 microcode，所以**之前所有"microcode 移植"方向是错的**：
- `docs/14th-gen-microcode-port-report-2026-09-08.md`
- `docs/cross-vendor-bios-ports-2026-09-08.md`
- `docs/me-upgrade-feasibility-2026-09-08.md`
- `测试bios文件/Q100E_with_14th_from_ShuttleXH610.bin`
- `测试bios文件/V2/`

**保留为参考教训**（不删除——记录项目演化历史）。
