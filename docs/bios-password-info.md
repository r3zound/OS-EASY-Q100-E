# BIOS Setup 密码信息

> **机器 BIOS Setup 界面用户密码：`vdiadmin`**
> **来源**：用户口述（2026-09-07）

## 1. 这个密码是干什么的？

| 项目 | 含义 |
| --- | --- |
| **密码值** | `vdiadmin` |
| **作用** | 用户每次开机按 DEL 进 BIOS Setup 界面时被要求输入的密码 |
| **存储位置** | RTC/CMOS NVRAM 实时存储（不在 SPI flash dump 里） |
| **影响范围** | **只**影响 BIOS Setup 界面的访问权限 |
| **不影响** | SPI flash 内容、.bin 文件内容、ME 区域、microcode |

## 2. ⚠️ 这个密码与 .bin 文件分析无关

很多人会以为"BIOS 有密码"意味着 .bin 文件被加密——**不是**。

AMI BIOS 的密码机制**只是在用户进 Setup 改配置时**要求验证，**不加密任何 SPI flash 内容**。具体来说：

| 场景 | 密码起作用吗？ |
| --- | --- |
| 用户开机按 DEL 进 Setup 改配置 | ✅ 提示输入密码 |
| 编程器读 SPI flash 拿 .bin 文件 | ❌ 密码不影响 |
| 用 Python 脚本分析 .bin 文件 | ❌ 密码不影响 |
| 改 .bin 里的 Setup 字符串 / 选项 | ❌ 不需要密码（直接 hex 编辑） |
| 用 AMIBCP 看/改 .bin 的 Setup 树 | ❌ 不需要密码（AMIBCP 改的是默认值和可见性） |
| 刷回改后的 .bin | ❌ 不需要密码（编程器直接覆盖） |
| 刷回后用户进 Setup | ✅ 仍然问 `vdiadmin`（密码没变） |

## 3. 为什么之前分析找不到 Setup 字符串

`vdiadmin` 这个密码**完全不影响** .bin 文件内容。我们之前扫描找不到 "Hyper-Threading"、"PL1 Power Limit" 等 setup 关键词，**根本原因**是：

1. **EFI_HII String Token 编码** — AMI UEFI 用 GUID 引用 String Token，文本不在明文 UTF-16LE
2. **IFR（Internal Forms Representation）二进制格式** — Setup 选项定义在 IFR opcodes 里，不是 ASCII
3. **0 个 LZMA / Tiano / Standard 压缩头** — 文本不压缩也不明文，存放在 HII database
4. **ME 区域 PMCC000 用 Huffman 压缩** — 看不到 microcode 具体列表

**所有这些**都跟密码无关。

## 4. 如果要查看/修改实际 Setup 选项

虽然密码不影响 .bin 分析，但用户**想看** BIOS 实际有哪些 Setup 选项时，需要用专用工具：

### 4.1 AMIBCP（Aptio Configuration Protocol）

- **作用**：查看和修改 AMI BIOS 的 Setup 树
- **下载**：https://www.win-raid.com 或 GitHub 搜 `AMIBCP`
- **用法**：
  1. 打开 .bin 文件
  2. 展开 Setup 树
  3. 看到所有可见 + 隐藏选项
  4. 可以改默认值、解锁隐藏项
- **是否需要密码**：❌ **不需要**！AMIBCP 改的是 Setup 模块的默认值，**不涉及用户密码**

### 4.2 IRFExtractor（IFR Extractor）

- **作用**：从 .bin 提取所有 IFR 文本和选项
- **下载**：https://github.com/LongSoft/IFRExtractor
- **用法**：
  1. 打开 .bin
  2. 自动扫描所有 IFR 区域
  3. 输出可见 / 隐藏的 Setup 字符串
- **是否需要密码**：❌ 不需要

### 4.3 UEFITool + IFR Extractor 组合

- UEFITool 解析 FFS / IFR
- IFR Extractor 提取 setup 字符串
- 组合使用能看到所有 BIOS 设置

## 5. 改 BIOS 后密码会变吗？

**默认不变**。

- 编程器刷写 SPI flash 只覆盖 SPI flash 内容
- BIOS Setup 密码存在 **RTC/CMOS NVRAM**（不在 SPI flash 里）
- 刷写后 NVRAM 不动，所以密码仍是 `vdiadmin`
- ⚠️ 但如果刷写过程中 NVRAM 被意外清空（罕见），密码会恢复为默认（一般是空）

## 6. 密码重置（如果忘了）

如果将来 `vdiadmin` 这个密码被改/忘记：

1. **方法 1（推荐）**：扣掉主板 RTC 电池等 5 分钟，密码恢复默认
2. **方法 2**：跳 CMOS 跳线（参考主板说明书）
3. **方法 3**：刷回含默认密码的 .bin

## 7. 给同型号玩家的提示

如果你也是 Q100-E 用户，**默认 BIOS Setup 密码是 `vdiadmin`**（政企机器常见默认）。

如果你的机器密码**不是** `vdiadmin`，说明之前有人改过，扣电池可恢复。

## 8. 相关文档

- [docs/bios-analysis-2026-09-07.md](bios-analysis-2026-09-07.md) — 整体 BIOS 实测分析
- [docs/bios-deep-analysis-2026-09-07.md](bios-deep-analysis-2026-09-07.md) — 深度分析
- [AGENTS.md](../AGENTS.md) — 项目关键事实
- [docs/known-issues.md](known-issues.md) — 已知问题
