# 工具指南

> 本项目主要用 Python 脚本做分析，外部工具（CH341A、UEFITool、AMIBCP 等）见末尾"参考工具"章节。

## 1. 本项目自带工具

### `tools/analyze.py`（主工具）

**综合 BIOS bin 分析脚本**。输入 32MB 整片 SPI flash dump，输出：

- 整体 hash（SHA256 / MD5 / CRC32）
- Flash Descriptor 布局（**自动处理 OEM 偏移**）
- ME 区域 + FPT 详细（13 个 partitions）
- $CPD (Code Partition Directory) 扫描
- microcode 位置（PMCC000 容器）
- 14 代 RPL-R 支持评估
- JSON 详细报告

**安装**：

```bash
pip install -r tools/requirements.txt
```

需要 `uefi-firmware >= 1.16`（Python 库）。

**运行**：

```bash
python tools/analyze.py your_dump.bin
```

**输出示例**：

```
=== your_dump.bin ===
大小:    33554432 bytes (32.00 MB)
SHA256:  50bf84a961e8cc861f6375e231a7e9723c8396c706d86a81f33befc5085b5b41
MD5:     47bffc5a3543c54b39f09737480059bb
CRC32:   f42ddf2c

【Flash Descriptor】
  FD signature 在 0x00000010 (标准是 0x00，本机偏移到 0x10 说明有 OEM 前缀)

【ME 区域 $FPT】
  $FPT 在 0x001a9000
  ME 版本: 16.1.25.1917
  Partitions: 13

【microcode 位置】
  BIOS region (传统 FFS microcode 文件):
    [-] 未找到（这块板的 microcode 不在 BIOS region）
  ME 区域 (PMCP 容器):
    [+] PMCC000 in $CPD @ 0x00023000

【14 代 RPL-R 支持评估】
  ME 版本: 16.1.25.1917 (16.x - 理论支持 14 代)
```

**JSON 报告**：自动生成 `<dump>.analysis.json`，含完整结构化数据。

**已知限制**：

- ME 区域内的 Huffman 压缩 microcode 容器**不会自动解压**
- 要看具体 microcode 列表，需要二次开发（huffman 解压 + microcode 解析）
- 如果你需要做这个，欢迎 PR

### `tools/requirements.txt`

Python 依赖列表。当前只有 `uefi-firmware>=1.16`。

## 2. 编程器刷写工具（外部）

### 2.1 CH341A 编程器 + 烧录夹

**作用**：读 / 写 SPI Flash 芯片（BIOS 芯片）

**推荐软件**：

- ✅ **NeoProgrammer**（首选）— 开源、读全、稳
- ❌ CH341A编程器.exe（不推荐，读出来不完整）

**使用要点**：

- 红线对 1 脚（芯片上有小圆点标识 1 脚）
- 夹紧，但不要压坏 PCB
- 接触不良是最大失败原因
- 24xx / 25xx 系列 SPI Flash 都支持

**获取**：

- 淘宝 / 拼多多搜"CH341A 编程器 烧录夹"，30-50 元全套

### 2.2 NeoProgrammer 操作流程

```
芯片型号选择：先 Detect（自动识别）→ 不能识别时手动选
电压：3.3V（5V 会烧 SPI Flash）
SPI 模式：Standard
时钟：默认
```

```
1. Detect → 2. Read（保存原厂 .bin）→ 3. Blank Check → 4. Open（新 .bin）→ 5. Program → 6. Verify
```

## 3. BIOS 解析工具（外部，可选）

### 3.1 UEFITool

**作用**：解析 UEFI 镜像、查看 FIT 表

**下载**：https://github.com/LongSoft/UEFITool

**注意**：这块 Q100-E 的 FD signature 在 0x10（OEM 偏移），UEFITool 默认搜 0x00 可能误判"无效 FD"——**先用 `tools/analyze.py` 看清楚再开 UEFITool**。

### 3.2 ME Analyzer

**作用**：解析 ME 区域版本、大小、配置

**下载**：https://github.com/LongSoft/MEAnalyzer

### 3.3 IRFExtractor

**作用**：提取 Setup IFR，把隐藏 BIOS 选项转成可读文本

**下载**：https://github.com/LongSoft/IFRExtractor

## 4. BIOS 修改工具（外部，本项目用不到）

### 4.1 MMTool（Aptio 版）

**作用**：添加 / 替换 / 删除 microcode

**下载**：https://www.win-raid.com/t596f39-AMI-Aptio-MMTool.html

> ⚠️ **本项目暂不直接使用**——这块板的 microcode 在 ME 区域，不在传统 BIOS region。
> 如果以后改 ME 区域内的 microcode，可能需要 Huffman 解压工具（MEBin、UEFITool NE）。

### 4.2 AMIBCP

**作用**：修改 AMI BIOS 的 Setup 隐藏选项默认值

**下载**：win-raid 论坛或 GitHub 搜

**Q100-E 典型用途**：

- 改 PL1 / PL2 默认值（第三方 BIOS 已改）
- 解锁 mSATA 隐藏选项
- 关闭超线程默认值

## 5. 验证工具

### 5.1 哈希工具

Windows PowerShell：

```powershell
Get-FileHash -Algorithm SHA256 .\file.bin
Get-FileHash -Algorithm MD5 .\file.bin
```

Linux：

```bash
sha256sum file.bin
md5sum file.bin
```

### 5.2 HWiNFO64

**作用**：进入系统后查看 CPU microcode 实际加载版本

**使用**：

```
HWiNFO64 → CPU → CPU 0 → Microcode Update Revision
```

确认刷写后 microcode 已成功加载。

## 6. 工具链总览

| 阶段 | 工具 | 用途 |
| --- | --- | --- |
| 备份 | CH341A + NeoProgrammer | 读原厂 bin |
| **分析** | **`tools/analyze.py`** | **整体结构 + 14 代评估**（本项目主工具） |
| 解析 | UEFITool | UEFI region 树状图 |
| 解析 | ME Analyzer | ME 详细参数 |
| 改 microcode | MMTool | ⚠️ 本项目用不到（microcode 不在 BIOS region） |
| 改隐藏项 | AMIBCP | 改 Setup 默认值（电源管理） |
| 校验 | hash | 确认其他 region 没动 |
| 刷回 | CH341A + NeoProgrammer | 写新 bin |
| 验证 | HWiNFO64 | 系统内确认 microcode 加载 |
