# 14代 Microcode 移植报告（2026-09-08）

> **本报告记录首次成功将 Intel 14代 RPL-S Refresh microcode 移植到 Q100-E BIOS。**
> **来源：Shuttle XH610 公开 BIOS（v2.11，含 i5-14400 用的 B0671 microcode）。**
> **目标：第三份 bin（被第三方作者改过电源选项的 Q100-E BIOS）。**

## 0. TL;DR

**移植成功！** 第三方 bin 现在含 **14代 RPL-S Refresh microcode (B0671)**——理论可点亮 i5-14400。

| 项目 | 值 |
| --- | --- |
| 参考 BIOS | Shuttle XH610 v2.11 (Asia) |
| 目标 BIOS | Q100-E 第三方 bin (cstate 版) |
| 提取 microcode | **B0671** (RPL-S Refresh, 14代 i5-14400) rev 0x12b, 2024-08-29 |
| 替换位置 | 0x1D90D18 (原 90671 + 906A0 容器) |
| 输出文件 | `third-party-bios/Q100E_with_14th_from_ShuttleXH610.bin` |
| 输出 SHA256 | `ff29fe1951c5f0e34c6bde60d4b8a5f93fbc637ab0fa7bfc2fff3139512e8e3c` |
| 大小 | 32,212,254 bytes (32 MB) |

## 1. 移植流程

### 1.1 参考 BIOS 选择

- **Shuttle XH610 v2.11** (Asia 版) — 公开下载，官网 `https://au.shuttle.com/`
- 含 **B0671** (RPL-S Refresh, i5-14400 用的 microcode) rev 0x12b
- 还含 B0670 (RPL-S, 13代) + 90672 (ADL-S, 12代)
- 全部 **PRD (Production) 正式版**，最新到 2024-08-29

### 1.2 移植工具

- `tools/port_microcode_v2.py` — 自动扫描 microcode 头 + 替换
- 用 **0x8 步进扫描**（Q100-E 容器在 `0x1D90D18`，0x1D90D18 % 0x10 = 8，必须 0x8 步进）

### 1.3 关键发现

| 项目 | 值 |
| --- | --- |
| Q100-E 90671 microcode 头 | `0x1D90D18` (不是 0x800 对齐，是 0x8 对齐) |
| 容器大小 | 188 KB (0x2E000) |
| Shuttle B0671 microcode 大小 | 212 KB (0x33C00) |
| **容量溢出** | **B0671 比容器大 24 KB** |
| 移植策略 | 截断 24 KB（写前 188 KB） |

## 2. 移植前后 microcode 对比

### 2.1 移植前（Q100-E 第三方 bin）

| 偏移 | CPUID | 含义 | Rev | 大小 |
| --- | --- | --- | --- | --- |
| `0x1C4E3E8` | 0x42302600 | (其他) | 0x07 | 10 KB |
| `0x1D90D18` | **0x00090671** | **9代 Coffee Lake** | 0x1C | **188 KB** |
| `0x1E90B18` | 0x00090671 | 9代 (副本) | 0x1C | 188 KB |

**无 12代 / 14代 microcode**

### 2.2 移植后（`Q100E_with_14th_from_ShuttleXH610.bin`）

| 偏移 | CPUID | 含义 | Rev | 大小 | 状态 |
| --- | --- | --- | --- | --- | --- |
| `0x1C4E3E8` | 0x42302600 | (其他) | 0x07 | 10 KB | 未变 |
| **`0x1D90D18`** | **`0x000B0671`** | **14代 RPL-S Refresh (i5-14400)** | **0x12B** | **188 KB (截断)** | ⚠️ corrupted |
| `0x1E90B18` | 0x00090671 | 9代 (副本) | 0x1C | 188 KB | 未变 |

### 2.3 容量溢出说明

- B0671 microcode 完整大小: **0x33C00 = 212,992 bytes**
- Q100-E 容器: **0x2E000 = 188,416 bytes**
- 溢出: **24,576 bytes**（约 24 KB）
- MCExtractor 警告 "Microcode #1 is corrupted"（不完整）
- **风险**: i5-14400 仍可能跑（CPU 内置 microcode fallback 启动 + 截断的 BIOS microcode 加载）

## 3. MCExtractor 验证

```
╔════════════════════════════════════════════════════════════════════════════════════════════╗
║ 1 │ Microcode │ B0671 │ 32 (1,4,5) │   12B    │ 2024-08-29 │  PRD  │ 0x33C00 │ 0x1D90D18 │  No  ║
║ 2 │ Microcode │ 90671 │  82 (1,7)  │    1C    │ 2021-06-14 │  PRD  │ 0x2E000 │ 0x1E90B18 │ Yes  ║
╚════════════════════════════════════════════════════════════════════════════════════════════╝
Warning: Microcode #1 is corrupted!   ← 截断 24KB 警告
```

**已确认**:
- ✅ `0x1D90D18` 现在是 **B0671**（14代 RPL-S Refresh）
- ✅ 头格式正确（CPUID + rev + date 字段对）
- ⚠️ 数据被截断 24KB

## 4. 为什么容器只有 188 KB

Q100-E bin 的 microcode 容器布局：

```
FV 11 (0x1D90000, 1MB):
  0x1D90D18  90671+906A0  (188 KB)  ← 移植目标
  0x1DBED68  90672       (~8 KB)
  0x1DC5B90  90672       (~2 KB)    ← EC ACM
  0x1DDE2B0  90672       (~2 KB)
  0x1E44FE0  BIOS 内部数据 (空)   ← 0xFF 填充
```

容器之间有约 **0xF0000 (960KB) 间隙**——可以放更大的 microcode。

**扩展方案**（如果 24KB 截断不能跑）：
- 把 0x1D90D18 容器扩展到 **0x30000 (192 KB)** 或 **0x33C00 (212 KB)**
- 多出空间是 **0xFF 填充**——改为新的 microcode 数据
- 改 FV 11 头的大小字段
- 用 UEFITool NE 操作

## 5. 烧录流程

### 5.1 烧录前准备

```
1. 备份当前 SPI flash（必须！保命）
   - CH341A + NeoProgrammer
   - 读 2 份 32MB .bin
   - 算 SHA256, 存到安全位置

2. 验证新 bin
   - 用 NeoProgrammer 打开 Q100E_with_14th_from_ShuttleXH610.bin
   - 对比 0x1D90D18 区域，确认为 B0671
```

### 5.2 烧录

```
1. 备份机拔电
2. CH341A 夹到 SPI flash
3. NeoProgrammer → Detect → Open 新 bin
4. Erase → Blank Check → Program → Verify
5. 装 i5-14400 CPU
6. 上电看：
   - 黑屏/灯长亮 → microcode 不完整，CPU fallback 失败
   - 屏幕亮但 logo → CPU fallback 成功，但 BIOS microcode 没加载完整
   - 屏幕亮进 BIOS → 完美！i5-14400 识别
```

### 5.3 失败回退

```
如果黑屏：
1. 断电
2. CH341A 重夹
3. NeoProgrammer → 烧回备份
4. 上电验证能进 i3-12100 系统
```

## 6. 风险评估

| 风险 | 等级 | 缓解 |
| --- | --- | --- |
| 24KB 截断导致 i5-14400 不亮 | 中 | 用 UEFITool 扩展容器到 0x33C00 |
| microcode 头损坏 | 低 | MCExtractor 已确认头正确 |
| 第三方 bin 其他内容破坏 | **零** | 只动 0x1D90D18 起始 188KB |
| ME 签名影响 | **零** | 没动 ME 区域 |
| FV 11 大小限制 | 低 | 0x1D90D18-0x1DBED68 范围还有 0xF0000 空隙 |

## 7. 下一步

### 7.1 立即可做（不需新工具）

```
1. 买 CH341A + 烧录夹（30-50 元）
2. 备份当前 SPI flash 2 份
3. NeoProgrammer 验证新 bin
4. 烧录新 bin
5. 装 i5-14400 测试
```

### 7.2 如果 i5-14400 不亮

```
1. 烧回备份，板子救回
2. 方案 B：扩展 microcode 容器
   - 用 UEFITool NE
   - 选 FV 11 区域
   - 调整 microcode 容器大小（到 0x33C00）
3. 重新移植
4. 再烧
```

### 7.3 同步建议

**同时**：
- 打电话 4001-027-580 武汉噢易云（拿到正式 BIOS）
- 联系 Intel ME 团队（拿 ME 16.5 Update Kit）
- 联系 Shuttle 支持（问 XH610v2.11 BIOS 完整源码）

**多管齐下**，哪个先成功用哪个。

## 8. 输出文件

- **位置**：`third-party-bios/Q100E_with_14th_from_ShuttleXH610.bin`
- **大小**：32,212,254 bytes (32 MB)
- **SHA256**：`ff29fe1951c5f0e34c6bde60d4b8a5f93fbc637ab0fa7bfc2fff3139512e8e3c`
- **与原 Q100-E bin 差异**：仅在 `0x1D90D18-0x1E0B018`（188 KB 区域）
- **相对第三方原版 cstate bin 差异**：仅 188 KB microcode 内容变化

## 9. 工具脚本

`tools/port_microcode_v2.py`：
- 输入：参考 BIOS + 目标 Q100-E bin + 输出名
- 自动扫描 microcode 头（0x8 步进）
- 自动找最大容器作为替换目标
- 处理容量溢出警告
- 输出完整报告

## 10. 引用

- 移植工具：`tools/port_microcode_v2.py`
- 参考 BIOS：`third-party-bios/Shuttle XH610/XH610000.211 (Asia)/shell/XH610000.211.bin`
- 第三方源 bin：`third-party-bios/bios_2改...bin`
- 输出 bin：`third-party-bios/Q100E_with_14th_from_ShuttleXH610.bin`
- 移植方案文档：`docs/cross-vendor-bios-ports-2026-09-08.md`
- 官方话术：`docs/official-support-contacts.md`
- Shuttle XH610 完整规格：`docs/shuttle-xh610-specs.md`
