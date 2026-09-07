# 工具脚本目录

本目录用于存放 BIOS 修改相关的自动化脚本。

## 计划中的脚本

- [ ] `extract_microcode.ps1` — 从 .bin 提取所有 microcode 到独立文件
- [ ] `inject_microcode.ps1` — 包装 MMTool 命令行操作，追加 RPL-R microcode
- [ ] `verify_bin.ps1` — 对比新旧 bin 的 region hash，确认其他 region 未动
- [ ] `make_backup.ps1` — 备份 BIOS 的一键脚本（自动生成时间戳、hash）
- [ ] `parse_microcode_list.py` — 解析 bin 中的 microcode 列表，输出可读报告

## 工具选择

- **PowerShell**：Windows 原生，方便调用 Get-FileHash、文件操作
- **Python**：解析复杂数据（如 microcode 容器）更方便
- 避免引入过重依赖（Node.js、Docker 等），尽量用单文件可执行

## 当前状态

暂无脚本，待首次备份 BIOS 后开始写第一个 make_backup.ps1。
