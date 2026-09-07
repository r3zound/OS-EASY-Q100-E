# 工具指南

## 1. 备份 / 刷写工具

### 1.1 CH341A 编程器 + 烧录夹

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
- 软硬件完全开源，避免被坑

### 1.2 编程器软件设置

```
芯片型号选择：先 Detect（自动识别）→ 不能识别时手动选
电压：3.3V（5V 会烧 SPI Flash）
SPI 模式：Standard
时钟：默认
```

**操作流程**：

```
1. Detect → 2. Read（保存原厂 .bin）→ 3. Blank Check → 4. Open（新 .bin）→ 5. Program → 6. Verify
```

## 2. BIOS 解析工具

### 2.1 UEFITool

**作用**：解析 UEFI 镜像、查看 FIT（Flash Image Table）、定位 microcode region

**下载**：https://github.com/LongSoft/UEFITool

**关键操作**：

```
File → Open → 选 .bin
左侧树状图展开：
  Intel Flash Image
  ├── FD (Flash Descriptors)
  ├── ME (Management Engine)
  ├── BIOS Region
  │   ├── Microcode
  │   │   ├── 06-97-05/... (ADL-S)
  │   │   ├── 06-B7-XX/... (RPL-S)
  │   │   └── (RPL-R 待追加)
  │   └── ...
  └── GbE
```

**导出 microcode**：

- 右键 microcode → Extract body → 保存为独立 .bin
- 多个 microcode 用 Extract as-is → 批量导出

### 2.2 ME Analyzer

**作用**：解析 ME 区域版本、大小、配置

**下载**：https://github.com/LongSoft/MEAnalyzer

**关键操作**：

```
File → Open → 选 .bin
查看：
  - ME 版本（如 12.0.x）
  - ME Region 大小
  - 厂商（AMI / Insyde / Phoenix）
  - SKU（Corporate / Consumer）
  - 固件大小、占位大小
```

**重要**：改 BIOS 前记录 ME 区域 hash，刷回后对比确认 ME 没动。

### 2.3 IRFExtractor

**作用**：提取 Setup IFR（Internal Forms Representation），把隐藏 BIOS 选项转成可读文本

**下载**：https://github.com/LongSoft/IFRExtractor

**用途**：

- 查看 BIOS 有哪些隐藏选项
- AMIBCP 改过哪些项后能 diff 对比

## 3. microcode 注入工具

### 3.1 MMTool（Aptio 版）

**作用**：添加 / 替换 / 删除 microcode

**下载**：https://www.win-raid.com/t596f39-AMI-Aptio-MMTool.html

**关键操作**：

```
1. 打开 .bin
2. 切到 "CPU Patch" tab
3. CPU Patch List 显示已有 microcode
4. 记录每个 microcode 的：
   - CPUID
   - Platform / Version
   - Date
5. Load Patch → 选要追加的 .bin
6. 选好插入位置（默认第一个空位）
7. Apply → 保存为新 .bin
```

**风险提示**：

- 容量不够时会报错 → 需要先删旧 microcode 或扩大 region
- 删错会让旧 CPU 不亮 → **必须先备份**

### 3.2 iucode_tool（Linux 端）

**下载**：`apt install intel-microcode` 或 GitHub microcode 仓库

**提取 microcode**：

```bash
iucode_tool -L /lib/firmware/intel-ucode/ -l | grep "RPL"
# 或
iucode_tool --scan-system 提取系统中已有的 microcode
```

## 4. 改 Setup / 解锁选项

### 4.1 AMIBCP

**作用**：直接修改 AMI BIOS 的 Setup 隐藏选项默认值

**下载**：https://github.com/LongSoft/AMIBIOS-Configuration-Program 或 win-raid 论坛

**使用**：

```
1. 打开 .bin
2. 展开 Setup tree
3. 找到要改的项 → 改 Default / Visible / Access
4. 保存
```

**Q100-E 典型用途**：

- 改 PL1 / PL2 默认值
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
| 解析 | UEFITool | 定位 microcode region |
| 解析 | ME Analyzer | 查看 ME 区域 |
| 改 microcode | MMTool | 追加 RPL-R |
| 改隐藏项 | AMIBCP | 改 Setup 默认值 |
| 校验 | UEFITool + hash | 确认其他 region 没动 |
| 刷回 | CH341A + NeoProgrammer | 写新 bin |
| 验证 | HWiNFO64 | 系统内确认 microcode 加载 |
