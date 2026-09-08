# MMTool 深度分析报告（2026-09-08）

> **本报告基于 MMTool.exe 5.00.0007 对 `bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin` 的实际分析。**
> 完整 .rpt 输出在 `docs/analysis-raw/bios_2.mmtool.rpt`（57 KB）。

## 0. TL;DR

MMTool 解析确认了 15 个 Firmware Volumes（FV）+ 多个 Nested FVs 的完整结构。关键收获：

1. **microcode 容器 GUID 确认**：`17088572-377F-44EF-8F4E-B09FFF46A070`（共两份副本）
2. **每份 microcode 容器 188416 字节** = binwalk 识别的 188KB 一致
3. **第三方 BIOS 实际硬件支持（来自 driver 名称）**：
   - **PCH 是 Tiger Lake**（`PchInitDxeTgl` 标识）—— 说明定制板用 TGL 时代的 PCH，可能是 H610 变种
   - **代工厂是 TPV**（`TpvPei` 标识）—— TPV 是全球最大显示器代工大厂
   - **Super I/O 是 ITE IT8613**（`IT8613PeiInit`）
   - **网卡：Realtek PCIe GBE**（PXE IPv4/IPv6 启动项）
4. **DXE driver 数量 200+**，覆盖全功能：HII、ACPI、TPM、SecureBoot、Intel ME、AMT、Storage、Network

## 1. MMTool 解析的 Firmware Volume 列表

| FV # | 位置 | 大小 | FFS 数 | 备注 |
| --- | --- | --- | --- | --- |
| 00 | 0x01000000 | 0x30000 (192 KB) | 1 | 引导码 / NVRAM 镜像 |
| 01 | 0x01030000 | 0x30000 (192 KB) | 1 | FV 00 镜像（？可能是 recovery 副本） |
| 02 | 0x01070000 | 0x640000 (6.25 MB) | 4 | 主 BIOS region，含 nested FV (2.9MB) |
| 03 | 0x00000000 (parent 02) | 0xF3E000 (15.2 MB) | 314 | **DXE 主驱动集合** |
| 04 | 0x00000000 (parent 02) | 0x5000 | 2 | 小容量 nested FV |
| 05 | 0x016B0000 | 0x3C0000 (3.75 MB) | 1 | Nested FV |
| 06 | 0x00000000 (parent 05) | 0x2C4000 | 17 | Setup 配置？ |
| 07 | 0x00000000 (parent 05) | 0x1000 | 0 | 空 |
| 08 | 0x00000000 (parent 05) | 0x286000 | 22 | |
| 09 | 0x00000000 (parent 05) | 0x1000 | 0 | 空 |
| 0A | 0x01A70000 | 0x90000 (576 KB) | 5 | ME 区域相关 |
| 0B | 0x00000000 (parent 0A) | 0x79000 | 31 | |
| 0C | 0x01B00000 | 0xB0000 (704 KB) | 1 | |
| 0D | 0x00000000 | 0x5A000 | 19 | |
| 0E | 0x01BB0000 | 0xBC000 (736 KB) | 11 | |
| 0F | 0x01D00000 | 0x10000 (64 KB) | 3 | |
| 10 | 0x01D10000 | 0x80000 (512 KB) | 52 | **PEI 阶段驱动** |
| 11 | 0x01D90000 | 0x100000 (1 MB) | 5 | **microcode 容器之一** |
| 12 | 0x01E90000 | 0xF0000 (960 KB) | 6 | **microcode 容器之二**（副本） |
| 13 | 0x01F80000 | 0x40000 (256 KB) | 12 | Boot Block FV |
| 14 | 0x01FC0000 | 0x40000 (256 KB) | 12 | Boot Block FV 副本 |

**Total Bytes Free**: 8,562 KB
**Total Bytes Used**: 24,205 KB

## 2. microcode 容器详细信息

### 2.1 容器位置和 GUID

```
FV 11 (0x01D90000):
  File 002: GUID 17088572-377F-44EF-8F4E-B09FFF46A070
            Location 0x01D90D00, Size 0x02E018 (188,416 bytes)

FV 12 (0x01E90000):
  File 002: GUID 17088572-377F-44EF-8F4E-B09FFF46A070  (同一 GUID)
            Location 0x01E90B00, Size 0x02E018 (188,416 bytes) (副本)
```

**两份副本**（FV 11 和 FV 12），**GUID 都是 `17088572-377F-44EF-8F4E-B09FFF46A070`**。

### 2.2 GUID 反查

GUID `17088572-377F-44EF-8F4E-B09FFF46A070` 是 **Intel 标准的 EFI Microcode File GUID**（Intel 在 EFI 微码文件中使用的固定 GUID）。

### 2.3 容器内容（结合 iucode_tool 解析）

每个 188416 字节容器含 **2 个 microcode**：

| CPUID | 含义 | 版本 | 日期 |
| --- | --- | --- | --- |
| `0x00090671` | **9 代 Coffee Lake** (F6/M0x67) | 0x1c | 2021-06-14 |
| `0x000906a0` | **10 代 Comet Lake** (F6/M0x6a) | 0x1c | 2021-06-14 |

**没有 12 代 ADL-S / 13 代 RPL-S / 14 代 RPL-R microcode**。

## 3. 第三方 BIOS 实际硬件推断（从 driver 名）

通过 MMTool 报告中的 driver 名称，可以推断出原厂定制板的设计：

| 标识 | 文件名 | 推断 |
| --- | --- | --- |
| `PchInitDxeTgl` | PchInitDxeTgl | PCH 是 **Tiger Lake** 时代的（11 代移动 PCH） |
| `TpvPei` | TpvPei | 代工厂是 **TPV**（冠捷 / 飞利浦显示器代工） |
| `IT8613PeiInit` | IT8613PeiInit | Super I/O 芯片是 **ITE IT8613** |
| `Realtek PCIe GBE Family Controller` | 网络栈 | 网卡是 **Realtek RTL8111 系列**（千兆） |
| `WifiProfileSync` | WiFi | 有 WiFi 模块（型号未明） |
| `IT8613_SMF` | Super I/O | 确认 IT8613 芯片 |
| `RstUefiDriverSu` | Storage | Intel RST 存储驱动（VMD） |
| `AtaPassThru` | Storage | ATA 直通驱动 |
| `Nvme` | Storage | NVMe 驱动 |
| `Ahci` | Storage | AHCI 驱动 |
| `SataController` | Storage | SATA 控制器驱动 |
| `SecureEraseDxe` | Security | 安全擦除 |
| `AmiTcgPlatformD` | TPM | AMI TPM 平台驱动 |
| `TxtDxe` | TXT | Intel TXT（受信执行技术） |
| `MeSmbiosDxe` | ME | ME SMBIOS 驱动 |
| `MeUlvCheckDxe` | ME | ME ULV 检查 |
| `AsfDxe` | AMT | ASF 驱动 |
| `Mebx` / `MebxSetup` | AMT | ME BIOS Extension |
| `AmtInitDxe` | AMT | AMT 初始化 |
| `WdtDxe` | WDT | 看门狗驱动 |
| `SerialIo` | Serial IO | 串行 IO |
| `SpiHcOperation` | SPI | SPI Host Controller |
| `CastroCovePmicN` | PMIC | PMIC 驱动（**Castro Cove 是 TGL PCH 的代号**） |
| `HstiIhvDxe` / `HstiResultDxe` | Security | HSTI 驱动（Intel 安全标准） |
| `SioDxeInit` | Super I/O | SIO 初始化 |
| `PowerLostNotify` | 电源 | 断电通知 |

### 3.1 关键推断

1. **PCH 是 Tiger Lake 时代的设计**（`PchInitDxeTgl` + `CastroCovePmicN`）
   - **H610 本质上就是 12 代 ADL 的桌面 PCH**，但工业 H610 板会复用 TGL 时代的设计资产
   - 这进一步确认了 Q100-E 是**政企定制 H610 板**（不是消费 H610）

2. **代工厂是 TPV**（`TpvPei` 标识）
   - TPV 是全球最大显示器 OEM（飞利浦、AOC 等品牌都是 TPV 代工）
   - 武汉噢易云计算作为云终端厂商，找 TPV 代工很正常
   - 意味着这块板**可能**有 TPV 后续 BIOS 更新（要查 TPV 官网）

## 4. 主 BIOS region (FV 02) 的内容

FV 02 (0x01070000, 6.25 MB) 含 4 个文件：

| File | GUID | Location | Size | Type | 含义 |
| --- | --- | --- | --- | --- | --- |
| 000 | `414D94AD-998D-47D2-BFCD-4E882241DE32` | 0x01070078 | 0x102C | FRFM | Freeform header |
| 001 | `05CA020B-0FC1-11DC-9011-00173153EBA8` | 0x010710A8 | 0x20018 | RAW | 原始数据 |
| 002 | `9E21FD93-9C72-4C15-8C4B-E77F1DB2D792` | 0x010910C0 | 0x2E0F90 (3.0 MB) | FV | **Nested FV 包含 314 个 DXE driver** |
| 003 | `FFCFC736-9DD8-4C63-ABDD-6DFB301799DF` | 0x01372068 | 0x5028 | FV | 小 nested FV（2 个 PEI driver） |

**关键**：diff 显示两份 bin 在 **0x01091000-0x01377000** 段不同（2.9 MB）—— 这正好对应**File 002 (Nested FV 0x2E0F90 字节 ≈ 3 MB)**！说明两份 bin 的 DXE driver 集合有差异。

## 5. 与之前发现的对比

| 维度 | binwalk 发现 | MMTool 报告 | 一致？ |
| --- | --- | --- | --- |
| microcode 容器位置 | 0x1D90D18, 0x1E90B18 | 0x1D90D00, 0x1E90B00 | ✅ 匹配 |
| microcode 容器大小 | 188416 | 188416 (0x02E018) | ✅ 匹配 |
| microcode 内容 | 9代+10代（iucode_tool 验证） | — | ✅ 已知 |
| 第三方 BIOS 不是 Q100-E 原厂 | 没有 12 代 microcode | 没有 12 代 microcode | ✅ 确认 |

## 6. 重要发现总结

### 6.1 microcode 状态（最终确认）

- ✅ **9 代 Coffee Lake** (`0x00090671`, 2021-06-14)
- ✅ **10 代 Comet Lake** (`0x000906a0`, 2021-06-14)
- ❌ **没有 12 代 ADL-S**（i3-12100 用的）—— **这份 BIOS 装不亮 i3-12100**
- ❌ **没有 13/14 代 RPL** —— **绝对装不亮 i5-14400**

### 6.2 第三方 BIOS 实际能点亮的 CPU

根据 microcode 集合反推，这两份第三方 BIOS 实际能点亮的 CPU：

- 9 代 Coffee Lake-S (i7-9700K, i9-9900K 等)
- 10 代 Comet Lake-S (i9-10900K, i5-10600K 等)
- **不能**点亮 11 代 / 12 代 / 13 代 / 14 代 CPU

**结论**：这两份 bin 是给**早期 H310 / H510 主板**的 12 代之前 BIOS，第三方作者针对 i7-9700K / i9-10900K 等标压 U 改了电源墙 / ICC。**完全不能用于 Q100-E 的 12 代 H610 平台**。

### 6.3 实际需求

要装 i5-14400 到 Q100-E，**必须用 Q100-E 原厂 BIOS**（含 12 代+ microcode）。**这两份第三方 bin 完全没用**。

## 7. 后续建议

1. **立即备份你机器的原厂 BIOS**（用 CH341A + NeoProgrammer）
2. 跑相同分析（iucode_tool + MMTool）确认原厂 BIOS 含哪些 microcode
3. 如果原厂 BIOS 含 12 代 ADL-S 但没 14 代 RPL-R：考虑升级 ME（高级操作）
4. 如果原厂 BIOS 含 14 代 RPL-R：直接装机测试

## 8. 引用

- 完整 .rpt 输出：`docs/analysis-raw/bios_2.mmtool.rpt` (57 KB)
- 之前分析：`docs/bios-analysis-2026-09-07.md` / `docs/bios-deep-analysis-2026-09-07.md`
- microcode 提取：binwalk + iucode_tool 在 WSL Ubuntu 22.04
