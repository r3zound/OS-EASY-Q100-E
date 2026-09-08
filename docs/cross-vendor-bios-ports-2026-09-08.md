# 跨板 BIOS 移植方案（2026-09-08）

> **思路：用其他品牌 H610（已支持 12-14 代）的 BIOS 逆向分析出可移植参数，**
> **应用到 Q100-E 上实现 14 代 CPU 支持。**
> **这是 ME 升级方案之外的最稳妥备选。**

## 0. TL;DR

| 维度 | 结论 |
| --- | --- |
| **可行性** | ✅ **高**——H610 标准化，AMI 通用模板，Intel microcode 跨板通用 |
| **难度** | ⭐⭐⭐ 中（找好 BIOS + 提取可移植部分 + 替换） |
| **风险** | ⭐⭐ 中（**需要 CH341A 备份**，刷错能救回）|
| **推荐度** | ⭐⭐⭐⭐ **强烈推荐**（比 ME 升级稳，比打电话快）|

## 1. 为什么可行？

### 1.1 H610 是 Intel 标准化 PCH

H610 芯片组规格由 Intel 定义：
- CPU 接口：LGA1700（12/13/14 代通用）
- DDR4/DDR5 内存（Q100-E 是 DDR4 SODIMM 笔记本规格）
- PCIe 4.0 x16
- USB 3.2
- SATA
- M.2

**H610 PCH 行为是统一的**——不同品牌的 H610 板**硬件层面相似**。

### 1.2 AMI UEFI 模板大体相同

AMI 给所有 OEM 授权 Aptio 4.x/5.x/6.x 模板，**核心模块（Intel RC、CPU 初始化、内存初始化）**都是同一份代码。

| 模块 | 是否通用 |
| --- | --- |
| Intel Reference Code (RC) | ✅ 跨 OEM 通用 |
| AMI Generic SIO 驱动 | ✅ 部分通用 |
| AMI CPU 初始化 | ✅ 通用 |
| AMI 电源管理框架 | ✅ 通用 |
| AMI Secure Boot | ✅ 通用 |
| **OEM Super I/O 驱动** | ❌ **不通用**（每家板子不同）|
| **OEM EC 固件** | ❌ **不通用** |
| **OEM GPIO / Straps** | ❌ **不通用** |
| **OEM ME manifest** | ❌ **不通用**（签名）|
| **OEM 标识 (Logo, 默认值)** | ⚠️ 部分 |

### 1.3 Intel microcode 跨板通用

**关键**：Intel 14 代 RPL-R microcode（`0x000B067`）是 Intel 直接发布的——**任何 H610 板都能用**。

- Intel ME 16.x 包含 14 代 microcode → 任何 H610 板都能用这版 ME（如果签名能过）
- BIOS region EFI microcode 文件 → 任何 H610 板都能用
- microcode 本身**不依赖板子设计**——只依赖 CPU

## 2. 可以 / 不能移植什么？

### 2.1 ✅ 可以移植（不依赖板子设计）

| 项 | 描述 | 大小 |
| --- | --- | --- |
| **14 代 RPL-R microcode** | 跨板通用，Intel 发布 | ~40 KB |
| **13 代 RPL-S microcode** | 跨板通用 | ~40 KB |
| **Intel Reference Code 片段** | 通用 RC | 几百 KB |
| **AMI 电源管理默认参数** | 跨板通用 | KB 级 |
| **CPU 特性 (HT, TXT, VT)** | 跨板通用 | KB 级 |
| **通用电源选项默认值** | BIOS Setup 默认值 | KB 级 |

### 2.2 ❌ 不能移植（依赖板子设计）

| 项 | 描述 | 风险 |
| --- | --- | --- |
| **Super I/O 驱动** | Q100-E 用 ITE IT8613 | 刷错 → 串口/LPC 没响应 |
| **EC 固件** | 政企定制板 EC | 刷错 → 不开机 |
| **GPIO / Straps 配置** | 每家板子不同 | 刷错 → 风扇不转/USB 失效 |
| **ME manifest** | 签名保护 | 刷错 → 永久砖 |
| **Boot Block** | 早期启动代码 | 刷错 → 完全不启动 |
| **OEM Logo / 标识** | 可选 | 刷错 → 显示别家 Logo |

### 2.3 ⚠️ 需要谨慎

| 项 | 描述 |
| --- | --- |
| 内存初始化代码 | **部分通用**——DDR4 时序可能不同 |
| 音频驱动 | Realtek 通用，但 HDA codec 不同 |
| 网络驱动 | Realtek RTL8111 通用，但 MAC 地址不同 |

## 3. 跨板移植工作流（详细步骤）

### Step 1: 找参考 BIOS

**关键**：找一个**其他品牌 H610 主板 BIOS**（已支持 12-14 代 CPU）。

#### 1.1 推荐品牌

| 品牌 | 型号 | 找 BIOS 渠道 |
| --- | --- | --- |
| **铭瑄 (Maxsun)** | H610M 挑战者 | 铭瑄官网 |
| **华擎 (ASRock)** | H610M-HDV / H610M-HVS | 华擎官网 |
| **技嘉 (Gigabyte)** | H610M H / H610M S2 | 技嘉官网 |
| **微星 (MSI)** | PRO H610M-B / PRO H610M-A | 微星官网 |
| **翔升 (ASL)** | H610M | 翔升官网 |
| **七彩虹 (Colorful)** | H610M | 七彩虹官网 |

#### 1.2 找 BIOS 的具体途径

1. **品牌官网** —— 搜型号 → Support → BIOS
2. **Win-Raid 论坛** —— https://www.win-raid.com/ （AMI BIOS 资源多）
3. **chiphell 论坛** —— 网友分享
4. **贴吧** —— Q100-E / H610 吧
5. **GitHub** —— 搜 "H610 BIOS" / "AMI Aptio H610"
6. **百度网盘 / 115 网盘** —— 找网友分享的 H610 BIOS 备份
7. **CH341A 备份群** —— 各种品牌的备份通常共享

#### 1.3 BIOS 选哪个版本？

**关键要求**：
- ✅ **必须支持 12 代到 14 代**（看 release notes 写"Support 12th/13th/14th Gen"）
- ✅ **最好是最新版**（microcode 越新越好）
- ✅ **ME 16.x**（跟 Q100-E 16.1.25.1917 接近）

### Step 2: 备份 Q100-E 当前 SPI flash

**绝对必要**——任何改动前必须先备份。

```
CH341A + 烧录夹
+ NeoProgrammer
→ 读 SPI flash 2 份
→ 保存到安全位置
```

### Step 3: 用 MCExtractor 分析参考 BIOS

```bash
python tools/MCExtractor/MCExtractor-r352/MCE.py 参考BIOS.bin
```

**找什么**：
- ✅ **CPUID 0x000B067** (RPL-S Refresh, 14 代 i5-14400)
- ✅ **CPUID 0x000906A4** (RPL-S, 13 代)
- ✅ **CPUID 0x0009067A** (ADL-S, 12 代)

**预期结果**：参考 BIOS 应该含 3+ microcode（12/13/14 代都有）。

### Step 4: 提取可移植的 microcode

```bash
# 提取参考 BIOS 的 microcode
python tools/MCExtractor/MCExtractor-r352/MCE.py 参考BIOS.bin
# 输出在 tools/MCExtractor/.../Extracted/Intel/
# 找到 cpu9067A / cpu906A4 / cpuB067 文件
```

**保存这些文件**：
- `cpu9067A_*.bin`（12 代 ADL-S microcode）
- `cpu906A4_*.bin`（13 代 RPL-S microcode）
- `cpuB067_*.bin`（14 代 RPL-R microcode）⭐ 关键

### Step 5: 替换到 Q100-E bin

**两种替换方式**：

#### 方式 A：用 MCExtractor / MMTool 替换 BIOS region 的 EFI microcode 文件

```bash
# MCExtractor 的 microcode 替换功能
python tools/MCExtractor/MCExtractor-r352/MCE.py Q100E.bin -rep 14代microcode.bin
```

**优势**：
- 只改 BIOS region 的 microcode 容器
- **不涉及 ME 签名**——不砖
- 容易操作

**风险**：
- microcode 容器容量可能不够（要删旧 90671/906A0 腾空间）
- Q100-E 的 microcode 容器 GUID `17088572-...` 是否兼容新 microcode（应该兼容）

#### 方式 B：替换 ME 区域的 PMCC000 容器

**更复杂**——需要先解 Huffman，再换 microcode，再重打包。

**风险**：**ME 签名**——但**只改 PMCC000 不动 manifest 可能签名不算失效**（manifest 包含 PMCC000 的 hash 的话改一个字节就失效）。

**建议**：先用方式 A（BIOS region），不行再试方式 B。

### Step 6: 验证

```
1. 写回新 bin 到 SPI flash
2. 装 i5-14400
3. 上电看：
   - 黑屏 → 用备份救回
   - 亮屏进 BIOS → 成功！验证 CPU 识别
4. 进 Windows 验证
```

### Step 7: 失败回退

```
如果刷坏：
1. CH341A 重读 SPI flash
2. 烧回备份的原始 bin
3. 恢复原状
```

## 4. 具体操作（用代码描述）

### 4.1 提取 14 代 microcode

```bash
# 在参考 BIOS 上
python tools/MCExtractor/MCExtractor-r352/MCE.py 参考BIOS.bin
# 输出: tools/MCExtractor/.../Extracted/Intel/cpuB067_plat82_ver000XXXXX_2024-XX-XX_PRD_*.bin
```

### 4.2 看 Q100-E bin 的 microcode 容器空间

```bash
# 看 Q100-E bin 的 FV 11 (0x1D90000) 和 FV 12 (0x1E90000) 的 microcode 容器
# 用 UEFITool 或 MMTool 提取
python tools/MCExtractor/MCExtractor-r352/MCE.py Q100E.bin
# 输出: cpu90671 + cpu906A0
# 它们每个是 188KB = 0x2E000
```

### 4.3 替换 microcode

```bash
# 删除旧的 9-10 代 microcode
python tools/MCExtractor/MCExtractor-r352/MCE.py Q100E.bin -rm cpu90671
python tools/MCExtractor/MCExtractor-r352/MCE.py Q100E.bin -rm cpu906A0

# 添加新的 12/13/14 代 microcode
python tools/MCExtractor/MCExtractor-r352/MCE.py Q100E.bin -add 12代.bin
python tools/MCExtractor/MCExtractor-r352/MCE.py Q100E.bin -add 13代.bin
python tools/MCExtractor/MCExtractor-r352/MCE.py Q100E.bin -add 14代.bin

# 输出: Q100E_modified.bin
```

### 4.4 写回 SPI flash

```bash
# 1. 备份当前能跑 i3-12100 的 SPI flash
# 2. 烧写 Q100E_modified.bin
# 3. 装 i5-14400 测试
```

## 5. 风险评估

| 风险 | 概率 | 后果 | 缓解 |
| --- | --- | --- | --- |
| 刷坏不启动 | 低（只动 microcode 容器） | 永久砖 | **CH341A 备份**（必须）|
| microcode 不兼容 | 中 | i5-14400 仍不亮 | 试不同版本 microcode |
| BIOS region 容量不够 | 中 | 改写失败 | 删旧 microcode 腾空间 |
| 烧录夹接触不良 | 低 | 写错 | 重夹 |
| ME 签名失败 | **0%（只动 BIOS region）** | — | 安全 |

## 6. 完整时间线估计

| 步骤 | 时间 | 难度 |
| --- | --- | --- |
| 找参考 BIOS | 0.5-2 小时 | 低 |
| 备份 Q100-E | 0.5 小时 | 低（需要 CH341A）|
| 分析参考 BIOS | 10 分钟 | 低（MCExtractor 自动） |
| 提取 14 代 microcode | 1 分钟 | 低（已自动）|
| 替换到 Q100-E | 5-30 分钟 | 中（MCExtractor 命令）|
| 写回 + 测试 | 0.5 小时 | 中 |
| **总计** | **1.5-3 小时** | — |

## 7. 找参考 BIOS 的具体推荐

### 7.1 优先找

1. **铭瑄 (Maxsun) H610M 挑战者** — 性价比高，BIOS 公开
   - 官网：https://www.maxsun.com.cn/
2. **华擎 (ASRock) H610M-HDV** — 用户多，资源多
   - 官网：https://www.asrock.com/mb/Intel/H610M-HDV/
3. **微星 (MSI) PRO H610M-B DDR4** — DDR4，跟 Q100-E 内存类型一致
   - 官网：https://www.msi.com/Motherboard/PRO-H610M-B-DDR4

### 7.2 BIOS 选版本

- 看 release notes 里**最近** 1-2 个版本（含"Support 14th Gen"）
- 下载最新 Beta + Stable 两个版本（备选）

### 7.3 找 BIOS 的关键关键词

- "H610 BIOS 14代" / "H610 BIOS Raptor Lake"
- "MS-7D45 / 7D46 / 7D48" （微星 H610M 型号代码）
- "H610M-HDV BIOS" （华擎）
- "Maxsun H610M BIOS" （铭瑄）

## 8. Q100-E 特殊性

Q100-E 是**政企定制板**（TPV 代工），跟零售 H610 板有差异：
- **Super I/O**：ITE IT8613（IT8613PeiInit 在 MMTool 报告里看到）
- **PMIC**：CastroCovePmicN（Tiger Lake 时代 PCH 电源管理）
- **ME**：16.1.25.1917（2023 年）
- **PCH 标识**：H610 定制（看 PchInitDxeTgl）

**特殊风险**：
- Q100-E 的 GPIO / Straps 配置可能跟零售 H610 不同
- 移植零售 H610 BIOS 到 Q100-E 时，**Setup 选项可能错位**
- 电源管理默认值可能不匹配

**但 microcode 移植不受这些影响**——microcode 是 CPU 用的，不依赖板子设计。

## 9. 推荐方案

### 9.1 最实用方案

```
1. 找铭瑄 H610M 挑战者 BIOS（支持 12-14 代）
2. CH341A 备份 Q100-E（必须）
3. MCExtractor 提取参考 BIOS 的 12/13/14 代 microcode
4. MCExtractor 替换到 Q100-E 的 microcode 容器
5. 写回测试
6. 失败用备份救回
```

### 9.2 备选方案

```
1. 找其他 H610 板 BIOS（ASRock / MSI / Gigabyte）
2. 同上流程
```

### 9.3 互补方案

跟**打电话 4001-027-580** 配合：
- 同时找参考 BIOS（自己改）+ 打电话要官方 BIOS
- 哪个先到用哪个

## 10. 引用

- MCExtractor：https://github.com/platomav/MCExtractor
- MMTool 5.0：见 win-raid.com
- UEFITool：https://github.com/LongSoft/UEFITool
- Intel 14 代 microcode 来源：https://github.com/platomav/CPUMicrocodes
- 本项目其他文档：
  - `bios-analysis-2026-09-07.md`（基础分析）
  - `pmcc-deep-dive-2026-09-08.md`（ME 区域）
  - `me-upgrade-feasibility-2026-09-08.md`（ME 升级分析）
