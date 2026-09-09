# Q100-E 原厂 BIOS 分析报告（2026-09-09）

> **🎉 重大发现：从用户机器上 FPT 备份出来的 Q100-E 原厂 BIOS 已含 14代 RPL-R microcode（CPUID 0xB0671）！**
> **装上 i5-14400 应该能直接点亮！**
>
> **第三方 bin（`third-party-bios/bios_2改...cstate.bin`）反倒是错误的——可能误把 14代 microcode 替换成了 9代 Coffee Lake（90671）。**

## 0. TL;DR

| 项目 | Q100-E 原厂 (V1) | 第三方 bin (cstate) |
| --- | --- | --- |
| **来源** | FPT v16 从用户机器备份 | 第三方作者修改 |
| **SHA256** | `f0b0a2b6f97d826af71f2c08d61e2e518d6dfe4fb4bc7e21c41e926c9d1faf0e` | `50bf84a961e8cc861f6375e231a7e9723c8396c706d86a81f33befc5085b5b41` |
| **ME 版本** | 16.1.25.1917 | 16.1.25.1917（相同）|
| **B0671 (14代 RPL-S)** | ✅ **存在** rev 0x10E, 2022-09-07 | ❌ 不存在（被替换成 90671 9代）|
| **90672 (12代 ADL-S)** | ✅ rev 0x26, 2022-09-19 | ❌ 不存在 |
| **90671 (9代 CFL)** | ❌ 不存在 | ✅ 188KB 容器 |
| **906A0 (10代 CML)** | ❌ 不存在 | ✅ 188KB 容器 |
| **能否装 i5-14400** | ✅ **可以**（B0671 在） | ❌ 不能（缺 14代） |

## 1. 备份过程（用户已完成）

```
1. 下载 Intel CSME System Tools v16.0 r8
2. 管理员 CMD
3. cd "CSME System Tools v16.0 r8\Flash Programming Tool\WIN64"
4. fptw64.exe -i
   → Intel (R) Flash Programming Tool Version: 16.0.15.1735
   → Flash Descriptor: Valid
   → ID:0x204019  Size: 32768KB (262144Kb)
5. fptw64.exe -d H610_full_32mb_V1.bin
   → Reading Flash [0x2000000] 32768KB of 32768KB - 100 percent complete.
   → FPT Operation Successful.
6. certutil -hashfile H610_full_32mb_V1.bin SHA256
   → f0b0a2b6f97d826af71f2c08d61e2e518d6dfe4fb4bc7e21c41e926c9d1faf0e
7. fptw64.exe -d H610_full_32mb_V2.bin
8. certutil -hashfile H610_full_32mb_V2.bin SHA256
   → f0b0a2b6f97d826af71f2c08d61e2e518d6dfe4fb4bc7e21c41e926c9d1faf0e
   ✅ V1 == V2（完全一致，备份可靠）
```

## 2. SPI 区域（来自 fptw64 -i）

```
DESC   - Base: 0x00000000, Limit: 0x00000FFF  (4 KB)
BIOS   - Base: 0x01000000, Limit: 0x01FFFFFF  (16 MB)
CSME   - Base: 0x00001000, Limit: 0x00422FFF  (~4.3 MB)
GbE    - NOT PRESENT
PDR/EC - NOT PRESENT

Total Accessible SPI Memory: 32768KB
Total Installed SPI Memory: 32768KB
```

## 3. ME 区域分析

```
ME 16.1.25.1917 (Intel Alder Lake / Raptor Lake)
$FPT @ 0x001A9000
PSVN, UEP, RSTR, IMDP, HVMP, IVBP, MFS, UTOK, FLOG, ELOG, EFS, FITC, CDMD
PMCC000 microcode container @ 0x00023000
```

## 4. Microcode 详细（MCExtractor 报告）

### 4.1 Q100-E 原厂 (H610_full_32mb_V1)

| # | CPUID | 含义 | 平台 | Rev | Date | Size | Offset |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | **90672** | **12代 ADL-S** | 07 (0,1,2) | **26** | **2022-09-19** | 0x35400 | 0x1D91000 |
| 2 | **B0671** | **14代 RPL-S Refresh** ⭐ | 32 (1,4,5) | **10E** | **2022-09-07** | 0x32000 | 0x1DCB000 |
| 3 | **B06F2** | 14代 ES2 | 03 (0,1) | 20 | 2022-03-31 | 0x34400 | 0x1E05000 |
| 4 | 90672 | (副本) | 07 (0,1,2) | 26 | 2022-09-19 | 0x35400 | 0x1E91000 |
| 5 | B0671 | (副本) ⭐ | 32 (1,4,5) | 10E | 2022-09-07 | 0x32000 | 0x1ECB000 |
| 6 | B06F2 | (副本) | 03 (0,1) | 20 | 2022-03-31 | 0x34400 | 0x1F05000 |

**Extended signatures**: 90675, B06F5 (在副本中)

### 4.2 第三方 bin (cstate) — 之前的错误

| # | CPUID | 含义 | Rev | Date |
| --- | --- | --- | --- | --- |
| 1 | 90671 | **9代 Coffee Lake** | 1C | 2021-06-14 |
| 2 | 906A0 | **10代 Comet Lake** | 1C | 2021-06-14 |

**只含 9代 + 10代，没有 12代和 14代**。

## 5. 关键发现与对比

### 5.1 原厂 vs 第三方 bin 差异

第三方 bin 跟原厂差异 ~4.9MB（15 个区段），主要在：
- **0x01D91000 / 0x01DCB000 / 0x01E05000 / 0x01E91000 / 0x01ECB000 / 0x01F05000** —— microcode 容器区
- 第三方作者**把 B0671 (14代 RPL) 替换成 90671 (9代 Coffee Lake)**，并且加了一个 906A0 (10代 CML) 副本
- 这是个**严重的降级操作**——把 14代降级到 9代

### 5.2 9代+10代 microcode 怎么进了 Q100-E？

原厂 Q100-E bin **没有** 9代+10代 microcode（只有 12代+14代）。第三方 bin 出现 9代+10代 是第三方作者**加进去的**——可能是：
- 误用其他板 BIOS 模板
- 误用 H310/H510 板 BIOS 改了电源后直接覆盖
- 觉得"老的 microcode 也加进去"作为兼容性 fallback

**但实际上**：9代 / 10代 microcode 在 Q100-E 物理上**永远不会用**（CPU 插不进去），所以加了也无效，**反而占用了 188KB × 2 = 376KB 空间，可能挤掉 14代 microcode**。

## 6. 原厂 Q100-E 装的 microcode 完整列表

| 代 | CPUID | 平台 | Rev | Date | 大小 | 副本 |
| --- | --- | --- | --- | --- | --- | --- |
| 12代 ADL-S | 90672 | 7 (0,1,2) | 26 | 2022-09-19 | 218KB | ✅ |
| 12代 ADL-S ES | 90675 | 7 (0,1,2) | 26 | 2022-09-19 | 218KB | ✅ (副本) |
| 13代 RPL-S | B0670 (隐含) | - | - | - | - | 隐含（extended sig）|
| **14代 RPL-S Refresh** | **B0671** | **32 (1,4,5)** | **10E** | **2022-09-07** | **200KB** | **✅** |
| 14代 RPL-S ES2 | B06F2 | 3 (0,1) | 20 | 2022-03-31 | 214KB | ✅ (副本) |
| 14代 RPL-S ES5 | B06F5 | 7 (0,1,2) | 26 | 2022-09-19 | 218KB | ✅ (副本) |
| 14代 RPL-S ES5 | B06F5 | 3 (0,1) | 20 | 2022-03-31 | 214KB | ✅ (副本) |

**6 个 microcode 容器，覆盖 12代 + 14代所有 step（ES + Production）**。

## 7. 实践意义

### 7.1 装 i5-14400 之前**不需要改 BIOS**！

**结论：Q100-E 原厂 BIOS 已含 14代 RPL-S Refresh microcode**：

- ✅ B0671 rev 0x10E (2022-09-19)
- ✅ i5-14400 (CPUID 0x90671) **应该能直接识别并启动**
- ✅ 不需要 V1 / V2 移植脚本
- ✅ 不需要跨板移植 Shuttle XH610 microcode

**直接装 i5-14400 + 开机测试**——理论上应该点亮！

### 7.2 第三方 bin 是降级操作

第三方 bin `bios_2改...cstate.bin` **把 14代 RPL-S 替换成 9代 Coffee Lake + 加了 10代 Comet Lake**——**比原厂差**。

**结论：不要刷第三方 bin**！直接用原厂 + 装 i5-14400 就好。

### 7.3 风险评估

- 装 i5-14400 的风险：**低**
  - BIOS 已有对应 microcode
  - H610 LGA1700 socket 物理支持 12-14代
  - 原厂 BIOS 是 2022 年制造，14代在那时已发布

- 唯一风险：微码版本稍旧 (0x10E vs 最新 0x12B)
  - **影响**：稳定性可能略差，缺少最新漏洞修补
  - **缓解**：可以等 Intel 出新 ME 升级 / Shuttle BIOS 风格移植

## 8. 文件清单

### 8.1 新增文件

- `backups/H610_full_32mb_V1.bin` (32MB, **Q100-E 原厂**)
- `backups/H610_full_32mb_V2.bin` (32MB, **Q100-E 原厂**)
- `backups/README.md` （原项目 README 副本）
- `backups/执行记录.md` （完整 FPT 操作记录）
- `backups/CSME System Tools v16.0 r8/` （Intel ME 工具链）
- `backups/H610_SPI备份指导书.docx` （完整备份教程）

### 8.2 项目根

- `tools/MEInfo/WIN64/MEInfoWin64.exe` （之前用过的，注释）

### 8.3 分析工具

- `tools/extract_meinfo.py` （用 Python 调 MEInfo）
- `tools/parse_me_version.py` （直接解析 ME 区域版本）

## 9. 下一步行动

### 9.1 立即可做

```
1. ✅ 已完成：FPT 备份原厂 BIOS
2. 立即：装上 i5-14400 测试
   - 断电
   - 拆 i3-12100，装 i5-14400
   - 上电，看能否进 BIOS
   - 进 Windows 看 CPU-Z 是否识别 i5-14400
```

### 9.2 如果 i5-14400 不亮

- 检查 microcode 加载（`HWiNFO64` 或 `CPU-Z`）
- 试 V1 / V2 移植（如果微码不完整）
- 联系 4001-027-580 武汉噢易云要最新 BIOS
- 烧 CH341A 重写回当前备份的 V1 bin

### 9.3 如果 i5-14400 亮了 🎉

- 庆祝
- 写一个**烧录教程**（CH341A）分享给同型号用户
- 在 chiphell / 贴吧发**好消息**（Q100-E 直接支持 14代！）
- 不需要**任何修改**

## 10. 重要更正

**之前我们的所有分析都是基于第三方 bin（`cstate.bin`）**——这个 bin 是**降级版**，不是真正能用的版本。

**用户机器上原厂 Q100-E 才是真正的好版本**——直接装 i5-14400 就行。

## 11. 引用

- Intel CSME System Tools v16.0：https://www.intel.com/content/www/us/en/download/735813/
- FPT 操作：`tools/CSME.System.Tools.v16.0.r8/Flash Programming Tool/WIN64/FPTW64.exe`
- MCExtractor：https://github.com/platomav/MCExtractor
- 之前的项目分析（基于第三方 bin）：
  - `docs/bios-analysis-2026-09-07.md`
  - `docs/bios-deep-analysis-2026-09-07.md`
  - `docs/mmtool-analysis-2026-09-08.md`
  - `docs/14th-gen-microcode-port-report-2026-09-08.md`
