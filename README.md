# 噢易乾 Q100-E BIOS Mod — 14 代 CPU 适配

> 把政企淘汰的 H610 准系统小主机的 BIOS 改成支持 Intel 14 代 Raptor Lake Refresh CPU
>
> 目标机器：武汉噢易云计算 乾 Q100-E（1.5L 准系统小主机）
> 目标 U：i5-14400

## ⚠️ 刷 BIOS 警告

刷 BIOS 有变砖风险，**强烈建议**：

- 刷前**必须**用编程器（CH341A + 烧录夹）完整备份原厂 BIOS
- 备份至少保留 2 份，独立存储（不要只放在同一台机器上）
- 改 BIOS 前先校验签名 / CRC（如有 OEM 校验，盲刷可能直接黑屏）
- 第一次刷请准备好编程器热救方案
- 任何操作前请明确知道自己在做什么

只建议用编程器刷，系统内刷没试过，出问题后果自负。

## 项目状态

| 项目 | 状态 |
| --- | --- |
| 硬件识别 | ✅ i3-12100 正常进系统 |
| 备份当前 BIOS | ⏳ 待用 CH341A 备份原厂 |
| microcode 分析 | ⏳ 待用 UEFITool 解析 |
| 注入 RPL-R microcode | ⏳ 待操作 |
| 验证 12 代兼容性 | ⏳ 待回滚测试 |
| 验证 14 代点亮 | ⏳ 待刷 i5-14400 测试 |

## 文档导航

- [硬件参数](docs/hardware.md) — 官方规格 + 实际装机配置
- [14 代 CPU 适配技术方案](docs/14th-gen-adaptation.md) — **核心文档**，改 microcode 的具体步骤
- [BIOS 备份与修改记录](docs/bios-mod-history.md) — 当前 bin 备份说明
- [已知问题](docs/known-issues.md) — 主板设计层面的坑
- [工具指南](docs/tools.md) — UEFITool / MMTool / ME Analyzer 等
- [刷写流程](docs/flashing-guide.md) — 备份 → 改 → 刷 → 验证
- [参考资料](docs/references.md) — 外部资料链接

## 目录结构

- `AGENTS.md` — agent 阅读入口
- `docs/` — 资料文档
- `backups/` — BIOS 备份（待组织）
- `tools/` — 工具脚本（待添加）

## 致同型号玩家

如果你也有 Q100-E 准系统，欢迎参考本项目的方案。所有操作风险自负。
