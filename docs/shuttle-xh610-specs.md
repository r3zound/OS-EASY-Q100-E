# Shuttle XH610 / XH610V 完整规格（2026-09-08）

> **本项目最实用的参考 BIOS 来源**
> 来源：https://au.shuttle.com/products/productsSpec?productId=2651
> BIOS 公开下载：https://au.shuttle.com/

## 0. 简介

**Shuttle XH610 / XH610V** 是 Shuttle 推出的 **3.5L 迷你准系统**（Mini-ITX 主板），使用 **Intel H610 芯片组**，支持 **12/13/14 代 LGA1700 65W CPU**。

**这是本项目**：
- 跟 Q100-E 体积类似（1.5L vs 3.5L，差 2L）
- 都用 H610 芯片组
- 都用 AMI Aptio UEFI BIOS
- Shuttle XH610 **公开 BIOS 下载**（Shuttle 官网直接提供）
- XH610 **最新 BIOS 支持 12-14 代**——可直接提取 14 代 RPL-S Refresh microcode

## 1. XH610V 完整规格

| 项目 | 规格 |
| --- | --- |
| **型号** | Shuttle XH610V (也有些 SKU 标 XH610) |
| **形态** | Mini-ITX 主板 + 3.5L 机箱 |
| **尺寸** | 240(L) × 200(W) × 72(H) mm |
| **CPU 支持** | Intel 12/13/14 代 Core i3/i5/i7/i9, Pentium, Celeron LGA1700 max. TDP 65W |
| **BIOS 备注** | v2.03 及更新版本支持 Raptor Lake (13 代) CPU；新版支持 14 代 RPL-S Refresh |
| **芯片组** | Intel H610 Express |
| **内存** | 2 × DDR4 SODIMM, 32GB per DIMM (max 64GB), DDR4-3200 |
| **显示输出** | HDMI + DisplayPort + D-Sub (VGA) — **三显独立输出** |
| **音频** | Realtek ALC662/ALC897/ALC888S 5.1 channel High Definition Audio |
| **网络** | (1) Intel GbE LAN + (1) Intel 2.5 GbE LAN, Wake-On-LAN |
| **存储** | SATA 6.0Gb/s interface + NVMe interface |
| **板载连接器** | (3) SATA connectors, (1) 1x4 pin USB 2.0 header, (2) 4pin fan connectors, (1) SATA power (5V), (1) SATA power (12V), (1) Auto power on, (1) RS232 voltage switch, **(4) RS232 connectors**, (1) Battery connector |
| **前面板** | (2) USB 2.0, (2) USB 3.2 Gen1 (含 Type-C x 1), Mic-in, Earphone-Out, Power-On, Power LED, HDD LED |
| **背板** | (2) RJ45 GbE LAN w/LED, (1) DisplayPort, (1) HDMI, (1) D-Sub (VGA), (2) USB 2.0, (2) USB 3.2 Gen1, **(1) RS232**, **(1) RS232/RS422/RS485**, Line in/out/MIC, External 4pin header, DC in, Kensington lock, (2) Wireless Antenna fixture |
| **驱动器位** | (1) 2.5" HDD/SSD bay + (1) Slim ODD bay (用户可装 1 Slim ODD 或 1 × 2.5" HDD/SSD) |
| **电源** | 120W Power Adapter (Input: 100-240V AC, 19V 6.32A) |
| **扩展槽** | (1) M.2 2280 Type M key socket (NVMe+SATA), (1) M.2 2230 Type E Key socket |
| **操作系统** | Windows 10/11 64 bit, Linux |
| **工作温度** | 0°C ~ 50°C |
| **认证** | CB, BSMI, cTUVus, FCC, CE, BSMI, UKCA, RCM, VCCI |
| **附送配件** | XPC 多语种快速用户指南, XPC DVD Driver, 1× Power cord, 1× SATA cable (pre-install for HDD), 1× SATA cable (pre-install for ODD), 1× 4 pin to SATA power cable, Screws |

## 2. XH610G 规格（更新版，3L）

| 项目 | 规格 |
| --- | --- |
| **形态** | 3L chassis |
| **CPU** | Intel 12/13/14 代 LGA1700 max. TDP 65W |
| **芯片组** | Intel H610 |
| **内存** | (注意：XH610G 是 **DDR5** 不是 DDR4) 2 × DDR5 SODIMM, 32GB per DIMM (max 64GB), DDR5 5600 MHz |
| **显示** | (2) HDMI 2.0b + (1) DisplayPort, 4K 三显独立输出 |
| **音频** | Realtek ALC888S |
| **网络** | (1) Intel GbE + (1) Intel 2.5 GbE |
| **扩展** | (1) M.2 2280 M key (NVMe+SATA), (1) M.2 2280 M key (SATA only), (1) M.2 2230 E key, (1) PCI-E X16 |
| **电源** | 180W Adapter (19.5V/9.23A) |
| **尺寸** | 250(L) × 200(W) × 78.5(H) mm |

## 3. XH610G2 规格（5L 工作站版）

| 项目 | 规格 |
| --- | --- |
| **形态** | 5L Form factor |
| **CPU** | Intel 12/13/14 代 LGA1700 max. TDP 65W |
| **芯片组** | Intel H610 |
| **内存** | 2 × DDR5 SODIMM, 32GB per DIMM (max 64GB), DDR5 5600 MHz |
| **显示** | (2) HDMI 2.0b + (1) DisplayPort, 三显独立输出 |
| **网络** | (1) Intel GbE + (1) Intel 2.5 GbE |
| **扩展** | (1) M.2 2280 (NVMe+SATA) + (1) M.2 2280 (SATA only) + (1) M.2 2230 E key + **(1) PCI-E X16** + **(1) PCI-E X1** |
| **电源** | 180W Adapter (19.5V/9.23A) |
| **尺寸** | 250 × 200 × 95 mm |

## 4. XH610 系列对比

| 型号 | 体积 | 内存 | 扩展槽 | 电源 | 特色 |
| --- | --- | --- | --- | --- | --- |
| XH610V | 3.5L | 2× DDR4 SODIMM | 2× M.2 | 120W | 4× RS232 + RS422/485, 双 GbE |
| XH610G | 3L | 2× **DDR5** SODIMM | 3× M.2 + 1× PCIe X16 | 180W | DDR5, 扩展卡 |
| XH610G2 | 5L | 2× **DDR5** SODIMM | 3× M.2 + 2× PCIe | 180W | DDR5, 工作站 |

## 5. 与 Q100-E 详细对比

| 维度 | Q100-E | XH610V | XH610G | 备注 |
| --- | --- | --- | --- | --- |
| 体积 | 1.5L | 3.5L | 3L | XH610V 体积更大但仍迷你 |
| CPU | 12 代 H610 | **12/13/14 代 H610** | 12/13/14 代 H610 | XH610 **支持 14 代** |
| 内存 | 2× DDR4 SODIMM | 2× DDR4 SODIMM | 2× **DDR5** SODIMM | Q100-E 是 DDR4 |
| M.2 SSD | 1× 2280 | 1× 2280 (NVMe+SATA) | 2× 2280 + 1× 2230 E-key | XH610G 存储更强 |
| mSATA | ✅ | ❌ (用 2.5" SATA) | ❌ (用 2.5" SATA) | Q100-E 有 mSATA 复用 |
| 2.5" SATA | ❌ (mSATA 复用) | 1× 2.5" HDD/SSD | 1× 2.5" HDD/SSD | XH610 用 2.5" |
| RS-232 | **1×** | **4× RS232 + 1× RS232/422/485 = 5 串口** | 1× RS232 | XH610 串口更多 |
| VGA | ✅ | ✅ (D-Sub) | ❌ (无 VGA) | Q100-E 强 |
| HDMI | 1× | 1× (XH610V) / 2× (XH610G) | 2× | XH610G 多 |
| DisplayPort | ❌ | ✅ | ✅ | XH610 强 |
| 千兆网 | 1× (可选 2) | 2× (1G + 2.5G) | 2× (1G + 2.5G) | XH610 强 |
| USB | 4× 3.2 + 4× 2.0 | 4× 3.2 + 4× 2.0 | 4× 3.2 + 4× 2.0 | 相当 |
| 电源 | 90W DC | 120W (外置 19V/6.32A) | 180W (外置 19.5V/9.23A) | XH610G 强 |
| 散热设计 | 1.5L 限制 | 3.5L 强 | 3L 强 | XH610 散热好 |
| **BIOS 公开** | ❌ 政企锁 | ✅ **Shuttle 官网下载** | ✅ | ⭐ 关键优势 |
| **microcode 移植** | 90671 + 906A0 | **B0670 + B0671 + 90672** | (DDR5 不同) | 移植价值高 |

## 6. XH610 microcode 详细列表（MCExtractor 验证）

MCExtractor v1.104 跑 `XH610000.211.bin` (Asia) 结果：

| # | CPUID | 含义 | 平台 | 版本 | 日期 | 状态 | 大小 | 偏移 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **B0670** | **RPL-S (13 代)** | 02 (1) | 0xE | 2022-02-20 | PRD | 0x30800 | 0x1D91000 |
| 2 | **B0671** | **RPL-S Refresh (14 代 i5-14400)** ⭐ | 32 (1,4,5) | 0x12B | 2024-08-29 | PRD | 0x33C00 | 0x1DCB000 |
| 3 | **90672** | **ADL-S (12 代)** | 07 (0,1,2) | 0x37 | 2024-05-29 | PRD | 0x36C00 | 0x1E05000 |
| 4 | B0670 | (副本) | 02 (1) | 0xE | 2022-02-20 | PRD | 0x30800 | 0x1E91000 |
| 5 | **B0671** | (副本) ⭐ | 32 (1,4,5) | 0x12B | 2024-08-29 | PRD | 0x33C00 | 0x1ECB000 |
| 6 | 90672 | (副本) | 07 (0,1,2) | 0x37 | 2024-05-29 | PRD | 0x36C00 | 0x1F05000 |

**Extended signatures**（同一 microcode 容器的其他 CPUID）：
- 90675（RPL-S step 5，13 代 ES 步进）
- B06F2（RPL-S Refresh ES2，14 代 ES 步进）
- B06F5（RPL-S Refresh ES5，14 代 ES 步进）

**关键发现**：
- ✅ **B0671 (CPUID 0x000B0671) = 14 代 RPL-S Refresh = i5-14400 用的 microcode**
- ✅ B0670 (CPUID 0x000B0670) = 13 代 RPL-S
- ✅ 90672 (CPUID 0x00090672) = 12 代 ADL-S
- ✅ 全部 PRD 正式版，最新到 2024-08-29
- ⚠️ 但每个 microcode size (198KB-224KB) **比 Q100-E 容器 (188KB) 大**——直接覆盖会截断

## 7. BIOS 下载方法

### 7.1 官方下载

1. 访问 https://au.shuttle.com/
2. 搜索 "XH610" 或 "XH610V"
3. 进入产品页 → Downloads / Support → BIOS
4. 下载最新版本（**2026 时最新 v2.11+ 含 14 代支持**）
5. 解压 ZIP → `shell/XH610000.211.bin` (32MB 完整 SPI flash 镜像)

### 7.2 BIOS v2.11 升级包结构

```
XH610000.211.zip (149KB)
├── XH610000.211 (Asia)/
│   ├── startup.nsh                              # UEFI 启动脚本
│   ├── efi/boot/
│   │   ├── bootia32.efi
│   │   ├── bootx64.efi
│   │   ├── Shell.efi
│   │   └── Shellx64.efi
│   └── shell/
│       ├── AfuEfix64.efi                        # AMI 刷写工具
│       ├── Fpt.efi                              # Intel FPT
│       ├── ifu64.efi                            # Intel 工具
│       ├── ChkSHUid_x64.efi
│       ├── EC00144.ADL                          # EC 固件
│       ├── flash1.nsh / flash64.nsh / FlashEC64.NSH
│       ├── XH610.BIN                            # 16MB 部分镜像
│       └── XH610000.211.bin                     # ⭐ 32MB 完整 SPI flash 镜像
└── XH610000.211 (Taiwan)/
    └── (同样结构)
```

### 7.3 刷写方法

#### 方式 A：EFI Shell 升级（推荐，Intel FPT）

1. 把 `XH610000.211.zip` 解压到 FAT32 U 盘
2. U 盘插入 XH610，启动时按 F7 进 Boot Menu
3. 选择 UEFI: Built-in EFI Shell
4. 输入 `FS0:` 进 U 盘
5. 跑 `startup.nsh` 或 `flash64.nsh`
6. 重启

#### 方式 B：编程器刷写（CH341A）

1. CH341A + 烧录夹读出 XH610 板 SPI flash（备份）
2. CH341A 写入 `XH610000.211.bin`（32MB 完整镜像）
3. 装任意 LGA1700 CPU 测试

## 8. 移植到 Q100-E 的具体策略

### 8.1 microcode 容器大小问题

| microcode | size | Q100-E 容器 (188KB) | 装得下？ |
| --- | --- | --- | --- |
| B0670 (RPL-S) | 198KB | 188KB | ❌ 差 10KB |
| **B0671 (RPL-S Refresh, 14代)** | **212KB** | 188KB | ❌ 差 24KB |
| 90672 (ADL-S) | 224KB | 188KB | ❌ 差 36KB |

**问题**：Shuttle 的每个 microcode 都比 Q100-E 容器大——直接覆盖会截断。

### 8.2 三种解决方案

#### 方案 A：截断 + 风险
- 用 0x2E000 (188KB) 数据覆盖 Q100-E 容器
- microcode 头部会写对，但 data 段会缺 10-36KB
- **结果**：i5-14400 可能能跑（基础 microcode），但**可能缺稳定性修复**

#### 方案 B：合并 90672 + B0671 到 1 个容器
- 用 Intel microcode 合并工具（platomav 的 cpumicrocodes 工具）
- 90672 + B0671 共享 1 个 microcode 头（extended signatures）
- 合并后大小：~212KB + 224KB ≈ 436KB → **装不下 188KB 容器**
- 仍需扩展容器

#### 方案 C（推荐）：扩展 microcode 容器
- Q100-E bin 0x1D90000-0x1E70000 有 ~1.5MB 空闲空间
- 创建一个 **larger microcode FFS**（0x60000 = 384KB）覆盖两个 0x2E000 容器位置
- 装入合并的 90672 + B0671 microcode (436KB)
- 改 FV 11 的 FFS 头大小字段

### 8.3 推荐工具

- **MCExtractor** 已经能列出 microcode
- **platomav/CPUMicrocodes** 提供合并工具
- **iucode_tool** 支持直接编辑 microcode bundle
- **UEFITool NE** 能编辑 FFS 容量

## 9. 为什么 Shuttle BIOS 仍可作为参考

即使不能直接覆盖 Q100-E 容器，Shuttle XH610 BIOS 仍是**极有价值的参考**：

1. **microcode 头格式**完全相同（已确认）
2. **FFS 容器格式**相同
3. **AMI Aptio 模板**相同
4. **Intel H610 芯片**相同
5. **14代 microcode 数据**直接可用
6. **BIOS 容量充足**（能装下完整 microcode）

## 10. 引用

- Shuttle XH610/XH610V 官方页：https://au.shuttle.com/products/productsSpec?productId=2651
- Shuttle XH610G 官方页：https://au.shuttle.com/products/productsSpec?pn=XH610G
- Shuttle XH610G2 官方页：https://au.shuttle.com/products/productsSpec?pn=XH610G2
- MCExtractor 项目：https://github.com/platomav/MCExtractor
- Intel CPUMicrocodes：https://github.com/platomav/CPUMicrocodes
- 本项目 14 代适配方案：docs/14th-gen-adaptation.md
- 本项目跨板移植方案：docs/cross-vendor-bios-ports-2026-09-08.md
