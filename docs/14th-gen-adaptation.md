# 14 代 CPU 适配技术方案（核心文档）

## 0. TL;DR

**核心动作**：在原厂 32MB BIOS 备份的 microcode region 里，**追加 Intel RPL-R (Raptor Lake Refresh) microcode**，让 H610 PCH 能识别 i5-14400。

**风险点**：

- ME（Management Engine）区域不要动，否则可能变砖
- microcode region 在 BIOS 镜像中部，需要先定位
- microcode 体积可能撑爆，需在 32MB 总容量内合理腾挪

**最小可执行方案**（推荐先试）：

1. 用 NeoProgrammer 备份原厂 32MB bin
2. 用 UEFITool 打开 bin，定位到 microcode region（FIT 表）
3. 用 MMTool 追加 14 代 RPL-R microcode（CPUID `0x000B0671` / `0x00090675` 等）
4. 检查 ME 区域、FD、PEI 等有没有破坏
5. 用 NeoProgrammer 写回芯片
6. 装 i5-14400 测试

## 1. 为什么 H610 默认不认 14 代

i5-14400 = **Raptor Lake Refresh (RPL-R)**，CPUID 一般是 `0x000B0671` 或 `0x00090675`（具体看 stepping），硅片代号 RPL-S 系列的 Refresh 步进。

原 H610 定制板的 BIOS（2022 年前发布）只包含：

- ADL-S（12 代 Alder Lake）的 microcode
- 可能 RPL-S（13 代 Raptor Lake）的 microcode（如果 BIOS 较新）

但**没有 RPL-R（14 代 Refresh）** 的 microcode，导致：

- CPU 上电后 MRC 找不到匹配的 microcode
- 早期 reset 阶段就卡住
- 表现：风扇转、屏幕黑、完全不 POST

**解法**：往 microcode region 里追加 RPL-R microcode。CPU 启动时 MRC 会自动匹配对应 microcode 加载，绕过这层"未识别"判定。

## 2. microcode 关键事实

### 2.1 microcode 文件格式

每个 microcode 容器是 2048 字节（典型）：

```
[Header: 48 字节，含版本/CPUID/日期/校验]
[Body: 剩余部分，含 microcode 实际指令]
```

CPUID 是核心标识，常见 14 代 RPL-R 系列：

| SKU | 核心 | CPUID | 备注 |
| --- | --- | --- | --- |
| i5-14400 / i5-14500 / i7-14700 | 6P+4E 或 8P+12E | `0x00090675` 或 `0x000B0671` | RPL-S Refresh |

> **注意**：CPUID 编码因 stepping 不同会有多个值，需要从 Intel microcode 更新包提取正确的那个。

### 2.2 microcode 容器大小 & 数量限制

- 每个 microcode patch 大小：通常 8KB - 16KB（含对齐）
- BIOS region 可用空间：取决于原 BIOS 已经塞了多少
- H610 板常见 microcode 区域：128KB - 512KB
- 实测方案：先 UEFITool 看容量，再追加

### 2.3 RPL-R microcode 关键版本

参考 Intel 公开的 microcode 更新包，RPL-R 常用版本：

- 早期：0xB7 stepping（Family 6 Model 0xB7）
- 较新：0xBF stepping（Family 6 Model 0xBF 等）
- Vmin 修复：0x12B 微码（针对 13/14 代 Vmin 崩溃问题，但 i5-14400 是非 K，影响小但建议加）

> 截止当前（2026 年）Intel 已经在多个 0x12x 修复版本上迭代，建议用 Intel 官网最新 Linux microcode 包（`microcode-202xxxxx.tar.gz`）里的 `06-97-05`（RPL-S Refresh 步进 5）系列。

## 3. 改 BIOS 的具体步骤

### Step 1：备份原厂 BIOS（编程器）

工具：CH341A 编程器 + 烧录夹 + NeoProgrammer（**不要用 CH341A编程器.exe**，读出来不完整）

```
1. 拆机 → 找到 SPI Flash 芯片（一般 8-pin SOIC 在内存槽附近）
2. 红线对 1 脚，夹紧
3. NeoProgrammer → Detect → Read → 导出原厂 .bin
4. 保存 2 份以上（一份冷备份，一份工作副本）
5. 记录 CRC32、SHA256
```

### Step 2：用 UEFITool 解析 bin

```
1. UEFITool 打开 .bin
2. 看 Intel FIT（Flash Image Tool）表
3. 定位 Microcode region（多个 Volume，每个含若干 microcode）
4. 记录已有 microcode 列表（展开看 CPUID）
5. 记录 BIOS region 总大小
```

预期：原 BIOS 含 ADL-S + RPL-S 的 microcode，**不**含 RPL-R。

### Step 3：准备 RPL-R microcode 文件

来源：Intel 官方 microcode 更新包（Linux 平台发布）

```
# Linux 平台 microcode 包
https://github.com/intel/Intel-Linux-Processor-Microcode-Data-Files

# 或 Intel 官方下载
https://downloadcenter.intel.com/download/?productId=88345
```

提取方式：

- Windows：用 `MMTool` 加载新 microcode 二进制，复制到剪贴板
- Linux：`iucode_tool` 提取

### Step 4：用 MMTool 追加 microcode

```
1. MMTool 打开 .bin
2. 切到 "CPU Patch" tab
3. "CPU Patch List" 看到已有 microcode
4. "Load Patch" → 选 RPL-R microcode 文件
5. 选择 "Insert" → 选第一个 microcode 容器位置
6. 应用 → 保存为新 .bin
```

**注意**：

- MMTool 会自动找空位，但容量不够时会提示
- 容量不够时要：删除冗余的旧 microcode（如有重复 stepping），或扩大 microcode region
- 改完立即用 UEFITool 验证：原 ME / FD / Option ROM 都没动

### Step 5：校验新 bin

```
1. UEFITool 打开新 .bin → 确认所有原 Volume 还在
2. 提取新 microcode 区域 hash → 与原区域对比（应只有微码段不同）
3. ME Analyzer 打开 .bin → 确认 ME 区域未变（hash 一致）
4. 整体 CRC32、SHA256 → 记录
```

### Step 6：写回芯片

```
1. NeoProgrammer → Open 改后 .bin
2. Erase → Blank Check → Program → Verify
3. 中间不要断电、不要动夹子
4. 完成后断开编程器，恢复主板供电
```

### Step 7：上电测试

```
1. 先插回 i3-12100 → 确认能进 BIOS（兼容性测试）
2. 关机，换 i5-14400 → 上电
3. 预期：屏幕亮、BIOS 识别 CPU 型号为 "Intel Core i5-14400"
4. 进 Windows 后用 HWiNFO 确认 microcode 版本加载正确
```

## 4. 进阶：如果改了 microcode 还是不亮

按可能性排序排查：

1. **ME 区域不兼容** — 14 代可能需要 ME 16.x，原 BIOS 是 ME 12.x
   - 解法：升级 ME（高风险，可能需要 32MB ME 镜像）
   - 备选：用 AMIBCP 关闭 ME 校验 / 改 ME 启动策略
2. **Intel Reference Code (RC) 不识别 RPL-R** — MRC 阶段卡住
   - 解法：从其他 H610 板（如 Jetway MM10-H610）移植 RC
   - 备选：找同芯片组的公开 BIOS dump 提取 RC 替换
3. **PMC / PMC 固件版本旧** — 14 代 PCH 电源管理有变
   - 解法：注入新版 PMC firmware
4. **Boot Guard / Verified Boot 阻止** — 签名校验失败
   - 解法：AMIBCP 关闭 Boot Guard，或找到 OEM 签名的 microcode 包

## 5. 不推荐的做法

- ❌ **直接刷其他 H610 主板的公版 BIOS** — 定制板的 LAN / Audio / EC 固件可能完全不匹配，刷完必砖
- ❌ **升级 ME 区域** — 32MB 整片里 ME 占了相当空间，错误操作等于重做整个 ME 镜像
- ❌ **不备份就改 BIOS** — 必后悔
- ❌ **跳过 NeoProgrammer 用 CH341A.exe** — 读写不完整

## 6. 工具链（详见 tools.md）

- **备份 / 刷写**：CH341A + 烧录夹 + NeoProgrammer
- **解析 BIOS**：UEFITool、IRFExtractor、ME Analyzer
- **改 microcode**：MMTool（AMI）、iucode_tool（Linux）
- **改 Setup 选项**：AMIBCP（解隐藏项 / 改默认值）
- **验证**：CRC32、SHA256、HWiNFO（确认 microcode 加载版本）

## 7. 参考资源（详见 references.md）

- Intel microcode 数据：https://github.com/intel/Intel-Linux-Processor-Microcode-Data-Files
- Jetway MM10-H610 BIOS changelog（参考"Support 14th Gen Raptor Lake Refresh Processor"的 changelog 表述）
- H610 + 14 代相关 BIOS 刷写教程（B 站、贴吧、chiphell 等）
