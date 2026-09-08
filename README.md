# 噢易乾 Q100-E BIOS Mod — 14 代 CPU 适配项目

> 政企淘汰的 H610 准系统小主机的 BIOS 改装实战记录
> 目标机器：武汉噢易云计算 **乾 Q100-E**（1.5L 准系统，闲鱼 350 元常见）
> 目标 CPU：**Intel Core i5-14400**（14 代 RPL-R，10核 16 线程，65W）

## TL;DR（5 分钟看完）

这块 H610 定制板的 BIOS microcode **不在传统 BIOS region 里**，而是被塞在 **ME 区域的 PMCC000 容器**（Huffman 压缩），所以"追加 microcode 到 BIOS region"这条路走不通。

但有个好消息：**ME 已经是 16.1.25.1917**——ME 16.x 设计上已经支持 14 代 RPL-R，理论上可能**已经包含 i5-14400 的 microcode**。

**最简方案**：直接装上 i5-14400 试一下，可能直接亮机。详细分析见 [docs/bios-analysis-2026-09-07.md](docs/bios-analysis-2026-09-07.md)。

## 准系统视角（只写操作数量，不写具体型号/容量）

> 数据来源：[噢易云官网 Q100-E](https://www.os-easy.com/a/359.html)
>
> **本表只写操作数量、接口数量、功能支持——故意不写 CPU 型号、内存/硬盘容量**。这台机器是准系统，CPU/内存/硬盘由买家自选。

| 维度 | 数量 / 操作 |
| --- | --- |
| 内存插槽 | 2 个（笔记本 DDR4 SODIMM） |
| M.2 SSD 槽 | 1 个（2280 规格） |
| mSATA 槽 | 1 个（可扩展） |
| 千兆网口 | 1 个（可选配 2 个） |
| HDMI 输出 | 1 个 |
| VGA 输出 | 1 个 |
| USB 3.2 接口 | 4 个 |
| USB 2.0 接口 | 4 个 |
| 音频输入（MIC-IN） | 2 个 |
| 音频输出（AUDIO-OUT） | 2 个 |
| 串口（COM / RS-232） | 1 个 |
| 红外（IR） | 1 个 |
| 防盗锁孔 | 1 个 |
| DC 电源口 | 1 个 |
| 上电自启 | 支持 |
| 冷唤醒 | 支持 |
| 热唤醒 | 支持 |

## ⚠️ 刷 BIOS 警告

**刷 BIOS 有变砖风险**，操作前请确认：

- 刷前**必须**用编程器（CH341A + 烧录夹 + NeoProgrammer）完整备份原厂 32MB bin
- 备份至少 2 份，独立存储（不要只放在同一台机器上）
- 改 BIOS 前先校验 SHA256 / MD5
- 第一次刷请准备好编程器热救方案
- **任何操作前请明确知道自己在做什么**

只建议用编程器刷；系统内刷没试过，出问题后果自负。

## 📊 项目当前状态

| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| 硬件识别 | ✅ | i3-12100 正常进系统 |
| 二手 BIOS 实测分析 | ✅ | 18 个分析脚本 + 8.5KB 报告已落地 |
| 关键发现（microcode 在 ME） | ✅ | 颠覆原计划 |
| 原厂 BIOS 备份 | ⏳ | 待用 CH341A 备份 |
| 14 代 microcode 注入 | ❓ | 需要 huffman 解压 PMCC000 或升级 ME |
| i5-14400 实装点亮 | ⏳ | 待 i5-14400 到货 + 改 BIOS |

## 🔍 三个最重要的发现

### 发现 1：microcode 不在 BIOS region

这块 H610 定制板的 microcode 容器在 **ME 区域 PMCC000**（0x23000 - 0x3A000，Huffman 压缩），不在传统 BIOS region 内的 microcode 文件。

- 后果：传统"追加 microcode 到 BIOS region"方案不直接适用
- 影响：项目方向需要调整

### 发现 2：ME 已经是 16.x

- ME 版本：**16.1.25.1917**
- ME 16.x 设计上已经支持 14 代 RPL-R
- **有可能已经包含 i5-14400 的 microcode**——值得先直接试

### 发现 3：FD signature 偏移被 OEM 改到 0x10

- 标准 FD signature (5A A5 F0 0F) 应该在偏移 0x00
- 这块板子在偏移 0x10（OEM 16 字节前缀）
- UEFITool 默认搜 0x00 会显示"无效 FD"

## 🚀 推荐操作路径（按风险从低到高）

### 第 1 步：直接装 i5-14400 试（零风险）

如果手里已经有 i5-14400，直接装上看能不能亮：
- 进 BIOS 看能否识别 CPU 型号
- 进 Windows 用 HWiNFO 看 microcode 加载版本
- 如果能跑，就不用改 BIOS 了

### 第 2 步：备份原厂 BIOS（必备）

不论第 1 步结果如何，都要用 CH341A + NeoProgrammer 备份：
- 读 2 份原厂 bin
- 算 SHA256 / MD5 / CRC32
- 至少存到 2 个独立位置

工具脚本：`tools/analyze.py`

### 第 3 步（如果不亮）：分析原厂 bin

跑分析脚本看原厂 microcode 情况：

```bash
python tools/analyze.py backups/original/your_dump.bin
```

会输出：FD 布局、ME 版本、CPD 分区、microcode 位置。

### 第 4 步（如果需要改 microcode）：升级 ME 区域

**这是高阶操作**，不在本项目初期目标。详见 [docs/14th-gen-adaptation.md](docs/14th-gen-adaptation.md)。

## 📂 仓库结构

```
.
├── AGENTS.md                          # agent 阅读入口
├── README.md                          # 本文件
├── .gitignore
│
├── docs/                              # 资料文档（给同型号玩家看）
│   ├── bios-analysis-2026-09-07.md   # ⭐ BIOS 实测分析（含 PMCC000 发现）
│   ├── bios-deep-analysis-2026-09-07.md  # ⭐ 深度分析（microcode 列表 + 电源管理 + Setup）
│   ├── mmtool-analysis-2026-09-08.md # ⭐ MMTool 深度分析（FV 结构 + PCH/代工厂推断）
│   ├── bios-password-info.md         # ⭐ BIOS Setup 密码信息（vdiadmin）
│   ├── 14th-gen-adaptation.md        # 14 代适配方案（修订版）
│   ├── hardware.md                    # 硬件参数
│   ├── known-issues.md                # 已知问题
│   ├── flashing-guide.md              # 刷写流程
│   ├── tools.md                       # 工具使用
│   ├── bios-mod-history.md            # 修改记录
│   ├── references.md                  # 参考资料
│   └── analysis-raw/                  # 原始分析素材（不常用）
│       └── bios_2.mmtool.rpt          # MMTool 完整输出（57KB）
│
├── backups/                           # 原厂 BIOS 备份目录（待你备份后填入）
│   └── README.md
│
├── third-party-bios/                  # 别人提供的 BIOS（不混到本项目）
│   ├── README.md
│   ├── _notes/                        # 第三方作者原版提示（保存为 .md）
│   ├── bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin
│   └── bios_大佬改好的_没解锁PL4之类的选项 跑不满i9会严重降频.bin
│
└── tools/                             # 分析脚本
    ├── analyze.py                     # ⭐ 综合分析（hash + FD + ME + microcode 位置）
    ├── diff_bins.py                   # diff 两份 bin
    ├── find_mc_ifr.py                 # microcode + IFR 搜索
    ├── scan_setup.py                  # microcode 头扫描
    ├── scan_setup_full.py             # 全 UTF-16 字符串提取
    ├── scan_compressed.py             # LZMA / Tiano 压缩段解压
    ├── dump_setup_strings.py          # BIOS region 内 ASCII 字符串 dump
    ├── scan_ifr.py                    # IFR opcodes 扫描 + Setup 变量
    └── deep_analyze.py                # AutoParser 深度遍历
```

## 🛠️ 核心工具

### `tools/analyze.py`

综合 BIOS bin 分析脚本。需要 `uefi-firmware` Python 库：

```bash
pip install uefi-firmware
python tools/analyze.py your_dump.bin
```

输出包含：
- SHA256 / MD5 / CRC32
- Flash Descriptor 布局（含 OEM 偏移支持）
- ME 区域 + FPT 详细（13 个 partitions）
- $CPD (Code Partition Directory) 扫描
- microcode 位置（PMCC000 容器）
- 14 代 RPL-R 支持评估
- JSON 详细报告

### 刷写工具（外部）

不在本仓库内，你需要单独准备：

- **CH341A 编程器** + 烧录夹（30-50 元）
- **NeoProgrammer** 软件（不要用 CH341A编程器.exe）
- 详见 [docs/flashing-guide.md](docs/flashing-guide.md)

## 📚 文档导航（按阅读顺序）

1. **[docs/bios-analysis-2026-09-07.md](docs/bios-analysis-2026-09-07.md)** ⭐ **必读**——BIOS 详细分析 + 关键发现
2. **[docs/bios-deep-analysis-2026-09-07.md](docs/bios-deep-analysis-2026-09-07.md)** ⭐ **深度分析**——microcode + 电源管理 + Setup 全解析
3. **[docs/mmtool-analysis-2026-09-08.md](docs/mmtool-analysis-2026-09-08.md)** ⭐ **MMTool 分析**——完整 FV 结构 + 代工厂推断（PCH=TGL，代工=TPV）
4. **[docs/bios-password-info.md](docs/bios-password-info.md)** ⭐ **密码信息**——`vdiadmin` 的真相
5. [docs/hardware.md](docs/hardware.md) — 硬件参数 + 14 代适配矩阵
6. [docs/14th-gen-adaptation.md](docs/14th-gen-adaptation.md) — 14 代适配方案
7. [docs/flashing-guide.md](docs/flashing-guide.md) — 备份/改/刷 完整流程
8. [docs/known-issues.md](docs/known-issues.md) — 主板设计层面的坑
9. [docs/tools.md](docs/tools.md) — 工具使用详解
10. [docs/bios-mod-history.md](docs/bios-mod-history.md) — 修改记录
11. [docs/references.md](docs/references.md) — 外部资料链接

## 👥 致同型号玩家

如果你也有一台 Q100-E 准系统想做 14 代适配，欢迎参考本项目的方案。

**所有操作风险自负**——但本项目尽量提供"最稳"的操作路径（编程器刷 + 完整备份 + 详细分析）。

**最实用的建议**：先装上 14 代 CPU 试一下，ME 16.x 可能已经能跑。

## 📈 项目进展时间线

- **2026-09-07**：项目建立
  - 完成项目骨架（AGENTS.md / README.md / docs/）
  - 18 个 Python 分析脚本（已收敛为 `tools/analyze.py`）
  - 详细分析两份第三方 BIOS bin
  - **关键发现**：microcode 在 ME 区域 PMCC000 容器（不在 BIOS region）
  - 第三方 BIOS bin 已 commit（hash 已记录）

## 🤝 贡献

本项目欢迎：
- 提交你备份的原厂 BIOS bin（去标识后）
- 报告你自己的 Q100-E 主板硬件差异
- 分享 14 代适配的成功 / 失败经验
- 改进分析脚本

## ⚖️ 免责声明

本项目纯属技术研究，记录折腾过程。所有操作有风险，刷坏自负。
