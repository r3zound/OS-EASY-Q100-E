# ⚠️ 重要更正（2026-09-08）

> **本项目早期的几份分析报告里有一个严重错误。**
> **本文件先说清楚错误，然后给出正确理解。**

## 1. 错误回顾

之前几份报告（`bios-analysis-2026-09-07.md` / `bios-deep-analysis-2026-09-07.md` / `mmtool-analysis-2026-09-08.md`）都包含以下**错误说法**：

> "这两份第三方 bin 是给 9-10 代 H310/H510 主板用的早期 BIOS"
> "9-10 代 microcode 真实存在 → 这份 BIOS 不是 Q100-E 的原厂"
> "i3-12100 跑得起来是 CPU 内置 microcode fallback"

## 2. 实际情况（2026-09-08 用户澄清）

用户明确说：

> **"这两份第三方的 BIOS 文件就是从这块 H610 主板中提取出来，修改过电源选项后的产物。"**

**这意味着**：
- ✅ 两份 bin **就是** Q100-E H610 板读出来的
- ✅ 它们**在物理上跟这块板匹配**（SPI flash 备份）
- ✅ 第三方作者**改过电源选项**（这跟文件名暗示的"PL4/ICC/CState"一致）
- ❌ 我之前推测"是 H310/H510 板 BIOS 改的"——**完全错**

## 3. 那为什么 bin 里出现 9-10 代 microcode？

这是**最关键的新理解**：

**Q100-E 板的 AMI UEFI BIOS 模板里默认就含 9/10 代 microcode**——OEM 不清理历史 microcode。

| 原因 | 解释 |
| --- | --- |
| **AMI 通用模板** | AMI Aptio 4.x/5.x 模板为了兼容性，会打包多个 CPU 代的 microcode |
| **OEM 不清理** | 政企定制板 OEM（TPV 代工）不主动删除老 microcode——多带无害 |
| **第三方不改** | 第三方作者**只改电源选项**（Setup 模块 + 隐藏项），没动 microcode region |
| **物理上无效** | Q100-E 物理接口 LGA1700，9-10 代 CPU 根本插不进——这些 microcode **永远不会被执行** |

**关键**：
- LGA1151（9 代）/ LGA1200（10 代）的 CPU **物理上**不能装到 LGA1700（H610）板上
- microcode 在 bin 里只是**冗余数据**，不影响 Q100-E 实际功能
- bin 里**没 12 代+ microcode** 才是真正的问题

## 4. 真正的关键问题

不管第三方 bin 来自哪里、为什么含 9-10 代 microcode，**核心问题没变**：

| microcode | 存在？ | 含义 |
| --- | --- | --- |
| 9 代 Coffee Lake (`0x90671`) | ✅ | AMI 模板自带，Q100-E 上无效 |
| 10 代 Comet Lake (`0x906A0`) | ✅ | 同上 |
| **12 代 Alder Lake** (`0x9067A` / `0x906E5`) | ❌ **不存在** | **i3-12100 跑得起来是奇迹（CPU fallback）** |
| 13 代 Raptor Lake (`0x906A4`) | ❌ | — |
| **14 代 RPL Refresh** (`0x000B0671` / `0x90675`) | ❌ **不存在** | **i5-14400 跑不起来** |

## 5. i3-12100 跑得起来的原因——两种可能

**可能 A**：CPU 内置 microcode fallback
- i3-12100 出厂时 Intel 烧录了基础 12 代 microcode
- 即使 BIOS 没提供 12 代 microcode，CPU 仍能用基础版启动
- 系统能进、能用，但**没 12 代 microcode 的漏洞修补**

**可能 B**：i3-12100 跑得起来是因为第三方作者**也加了 12 代 microcode**，但**不在我们扫到的位置**（在 ME 区域 PMCC000 容器的 Huffman 压缩流里）
- 这就需要解压 PMCC000 验证

**判断方法**：必须备份**原厂 BIOS**（用户机器上现在跑的那个）跑 MCExtractor 看真实 microcode 列表。

## 6. i5-14400 跑不起来的原因（更明确）

无论 9-10 代 microcode 怎么解释，**i5-14400 跑不起来**是确定事实：
- 14 代 RPL Refresh 是**新架构**（不是 12 代 Refresh）
- CPU 内置 microcode **不足以启动 14 代**（Intel 14 代是全新制程 + 新电源管理）
- 必须 BIOS 提供 RPL-R microcode 补丁
- 第三方 bin **确实没 14 代 microcode**——所以**装 i5-14400 + 第三方 bin = 屏幕黑**

## 7. 修正后正确的理解

| 维度 | 之前理解 | 正确理解 |
| --- | --- | --- |
| 这两份 bin 来源 | ❌ 误以为 H310/H510 板 BIOS | ✅ **Q100-E H610 板的 SPI flash 备份** |
| 9-10 代 microcode 含义 | ❌ "给 9-10 代用" | ✅ **AMI 模板默认带的冗余数据，Q100-E 物理上用不到** |
| i3-12100 跑得起来 | ⚠️ "CPU fallback 唯一解释" | ⚠️ 还是可能，但**也需要验证**原厂 BIOS 是否含 12 代 microcode |
| i5-14400 跑不起来 | ✅ 缺 14 代 microcode | ✅ **不变** |
| 第三方 bin 能否用 | ❌ "完全不能用" | ⚠️ "在 Q100-E 上能跑（i3-12100），但不能装 i5-14400" |

## 8. 项目后续方向（修正）

之前我列了"4 个方向"，现在**重新调整优先级**：

1. **最关键**：备份你机器的**原厂 BIOS**（在 SPI flash 里现在跑的那个）
   - 跑 `tools/MCExtractor/MCExtractor-r352/MCE.py` 看 microcode
   - 预期**应该看到** 12 代 ADL-S microcode（`0x9067A`）—— 否则 i3-12100 真就靠 CPU fallback 跑起来
   - 看是否含 14 代 RPL-R microcode（`0x000B0671`）

2. **如果原厂含 12 代但没 14 代**：升级 ME 区域（含 14 代 RPL-R microcode 的 ME 16.x）

3. **如果原厂含 14 代**：直接装机试 i5-14400

4. **第三方 bin 用法**：作为**参考**（不刷），用 MCExtractor / MMTool 继续分析，**学习 AMI BIOS 结构**

## 9. 致歉

我之前**逻辑混乱**：
- 把"bin 文件层"和"机器物理层"混了
- 看到 9-10 代 microcode 出现，没意识到是 AMI 模板冗余
- 直接推测"是 H310/H510 板 BIOS"——**没考虑到用户 Q100-E 板的 AMI 模板就含这些 microcode**

用户两次指出问题：
- 第一次（"逻辑不对"）—— 我承认错误但仍推测有 CPU fallback
- 第二次（"是这台 H610 板提取的"）—— 才知道是 AMI 模板的冗余数据

**记下教训**：分析 BIOS bin 文件时，必须**先确认 bin 来自哪台机器**——不能只看 microcode 集合就推测。

## 10. 相关文档

- [bios-analysis-2026-09-07.md](bios-analysis-2026-09-07.md) — 早期分析（含错误推断）
- [bios-deep-analysis-2026-09-07.md](bios-deep-analysis-2026-09-07.md) — 深度分析（含错误推断）
- [mmtool-analysis-2026-09-08.md](mmtool-analysis-2026-09-08.md) — MMTool 报告（含错误推断，需要修正）

以上三份文档**部分内容有错**——但**核心事实**（microcode 集合 90671+906A0、ME 16.1.25.1917、VF 结构、driver 列表）**都正确**。**需要修正的只是"为什么含 9-10 代 microcode"的解释**。
