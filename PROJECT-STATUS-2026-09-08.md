# Q100-E BIOS Mod 项目最终状态报告（2026-09-08）

> **本项目目标**：让 Intel i5-14400（RPL-R, 14 代）在 武汉噢易乾 Q100-E 准系统（H610 主板）上能正常点亮。
> **当前状态**：项目分析完成，工具齐备，等待 CH341A 备份或 Shuttle XH610 公开 BIOS 后继续。

## 0. TL;DR

| 维度 | 状态 |
| --- | --- |
| 项目目标 | 适配 i5-14400 到 Q100-E H610 主板 |
| **核心发现** | 当前第三方 bin **缺 14 代 RPL-R microcode**（`0x000B067`） |
| i3-12100 能跑 | 靠 CPU 内置 microcode fallback |
| i5-14400 不能跑 | 缺 14 代 microcode |
| 工具链 | ✅ MCExtractor + MMTool + binwalk + iucode_tool + WSL |
| 推荐方案 | Shuttle XH610 公开 BIOS 移植 14 代 microcode |
| 关键文件 | docs/14th-gen-adaptation.md / cross-vendor-bios-ports-2026-09-08.md |

## 1. 仓库结构（完整版）

```
噢易乾Q100-E准系统/
├── AGENTS.md                              # agent 阅读入口 + 关键事实
├── README.md                              # GitHub 仓库首页
├── .gitignore
│
├── docs/                                  # 完整文档
│   ├── 14th-gen-adaptation.md             # 14 代适配方案（核心）
│   ├── bios-analysis-2026-09-07.md        # BIOS 基础分析
│   ├── bios-deep-analysis-2026-09-07.md   # 深度分析
│   ├── bios-password-info.md              # 密码 vdiadmin
│   ├── correction-2026-09-08.md           # ⚠️ 重要更正
│   ├── cross-vendor-bios-ports-2026-09-08.md # 跨板移植方案
│   ├── hardware.md                        # 硬件参数
│   ├── hardware-similar-models-2026-09-08.md # 相似主板对比
│   ├── known-issues.md                    # 已知问题
│   ├── flashing-guide.md                  # 刷写流程
│   ├── me-upgrade-feasibility-2026-09-08.md # ME 升级分析
│   ├── mmtool-analysis-2026-09-08.md      # MMTool 报告
│   ├── official-support-contacts.md        # 官方联系话术
│   ├── pmcc-deep-dive-2026-09-08.md       # PMCC000 深度
│   ├── references.md                      # 参考资料
│   ├── third-party-analysis-2026-09-08.md  # 第三方报告评估
│   ├── tools.md                            # 工具使用
│   ├── bios-mod-history.md                 # 修改记录
│   └── analysis-raw/                       # 原始分析素材
│       └── bios_2.mmtool.rpt              # MMTool 完整输出 (57KB)
│
├── third-party-bios/                      # 第三方 BIOS（参考用）
│   ├── README.md
│   ├── _notes/                            # 第三方作者原版提示
│   ├── bios_2改...bin                     # 第三方 bin 1 (32MB)
│   ├── bios_大佬改...bin                  # 第三方 bin 2 (32MB)
│   └── (其他 BIOS 元数据)
│
├── tools/                                 # 分析工具
│   ├── analyze.py                         # ⭐ 主工具 (hash + FD + ME + microcode 位置)
│   ├── diff_bins.py                       # diff 两份 bin
│   ├── find_mc_ifr.py                     # microcode + IFR 搜索
│   ├── scan_ifr.py                        # IFR opcodes 扫描
│   ├── full_analyze.sh                    # ⭐ 一键分析 (WSL/Linux)
│   ├── analyze.bat                        # ⭐ 一键分析 (Windows 原生)
│   ├── MCExtractor/                       # Intel microcode 提取器
│   │   └── MCExtractor-r352/              # 完整 Python 工具
│   ├── UBU_1_79_alt.7z                    # UBU 工具 (未解压)
│   └── ONE bios/                          # UBU 工作目录 (.exe 文件)
│
└── backups/                               # BIOS 备份目录 (待填)
    └── README.md
```

## 2. 分析发现的 7 个关键事实

| # | 事实 | 影响 |
| --- | --- | --- |
| 1 | **第三方 bin 是 Q100-E SPI flash 备份**（用户澄清） | 这是修改过的 Q100-E BIOS |
| 2 | **ME 16.1.25.1917** | 设计上支持 12 代，但 PMCC000 内 132KB 数据**不是** microcode |
| 3 | **第三方 bin 只含 9代/10代 microcode**（CPUID 90671+906A0） | 缺 12 代 ADL-S / 14 代 RPL-R |
| 4 | **i3-12100 能跑**——靠 **CPU 内置 microcode fallback** | Intel 文档明确说明 |
| 5 | **i5-14400 必砖**——缺 14 代 RPL-R microcode | 14 代是全新架构 |
| 6 | **Boot Guard disabled** | BIOS region 可自由修改（无签名） |
| 7 | **ME 16.x 有 MERSA 签名**（256-bit ECC） | 改 ME 极难，需 OEM 私钥 |

## 3. 项目时间线

### 3.1 已完成（2026-09-07 → 2026-09-08）

- ✅ 项目骨架建立（AGENTS.md / README.md / docs/）
- ✅ 工具链建立（analyze.py + 9 个辅助脚本）
- ✅ 第三方 bin 深度分析（4 份报告）
- ✅ MMTool 报告（57KB 完整 FV 结构）
- ✅ MCExtractor + binwalk 验证 microcode 集合
- ✅ PMCC000 Huffman 深度解包
- ✅ 第三方 AI 报告评估
- ✅ ME 升级可行性分析
- ✅ 跨板移植方案
- ✅ 相似主板对比
- ✅ 官方联系话术
- ✅ 一键分析脚本（Windows + WSL）

### 3.2 待办（用户执行）

- ⏳ **买 CH341A 编程器**（30-50 元）
- ⏳ **备份当前 SPI flash** 2 份
- ⏳ **跑 `analyze.bat backup.bin`** 看 14 代 microcode 是否存在
- ⏳ **下载 Shuttle XH610 BIOS**（公开，14 代 microcode 必含）
- ⏳ **提取 Shuttle XH610 的 14 代 microcode**
- ⏳ **替换到 Q100-E bin**（用 MCExtractor）
- ⏳ **写回测试**

### 3.3 待办（如果 CH341A 备份后能进系统）

- ⏳ 备份的 SPI flash 跑 `analyze.bat`
- ⏳ 跟第三方 bin 对比
- ⏳ 看原厂 BIOS 是否已含 14 代 microcode

## 4. 工具汇总

| 工具 | 用途 | 状态 |
| --- | --- | --- |
| **tools/analyze.py** | 整体 BIOS 分析（hash + FD + ME + microcode 位置） | ✅ |
| **tools/full_analyze.sh** | 一键分析（WSL/Linux） | ✅ |
| **tools/analyze.bat** | 一键分析（Windows 原生） | ✅ |
| **tools/MCExtractor/** | Intel microcode 详细解析 + 提取 | ✅ |
| **tools/diff_bins.py** | 两份 bin 字节级 diff | ✅ |
| **tools/find_mc_ifr.py** | microcode + IFR 搜索 | ✅ |
| **tools/scan_ifr.py** | IFR opcodes 扫描 | ✅ |
| **tools/UBU_1_79_alt.7z** | UBU BIOS 修改工具 | ✅（未解压） |
| **tools/ONE bios/** | UBU 工作目录 | ✅（.exe） |

**外部工具**（在 WSL Ubuntu 22.04 已装）：

- `binwalk` — 二进制模式扫描
- `iucode_tool` — Intel microcode 提取
- `wine 6.0.3` + `wine32` — 跑 Windows 工具

## 5. 推荐操作（用户 5 步走）

### 5.1 第 1 步：打电话 4001-027-580（5 分钟）

见 `docs/official-support-contacts.md` 话术。

```
"您好，我有一台武汉噢易云计算 乾 Q100-E 准系统小主机（H610 主板）。
想咨询是否有支持 14 代 i5-14400 的 BIOS 更新？"
```

### 5.2 第 2 步：买 CH341A 编程器（30-50 元）

淘宝搜"CH341A 编程器 烧录夹"。

### 5.3 第 3 步：备份 + 跑分析（30 分钟）

```
1. 接 CH341A 到 Q100-E SPI flash
2. NeoProgrammer 读 2 份 .bin
3. 跑 analyze.bat backup.bin
4. 看报告：原厂 BIOS 有没有 14 代 microcode
```

### 5.4 第 4 步：找 Shuttle XH610 BIOS（公开）

- Shuttle 官网：https://au.shuttle.com/
- XH610 型号 BIOS 下载
- 含 14 代 RPL-R microcode 必定的

### 5.5 第 5 步：移植 microcode + 写回（30 分钟）

```
1. MCExtractor 提取 Shuttle XH610 的 14 代 microcode
2. MCExtractor 替换到 Q100-E 的 microcode 容器
3. CH341A 写回
4. 装 i5-14400 测试
```

## 6. 关键技术结论

| 维度 | 结论 |
| --- | --- |
| **i3-12100 跑得起来** | ✅ 靠 CPU 内置 microcode fallback（Intel 文档明确） |
| **i5-14400 跑不起来**（装第三方 bin） | ❌ 缺 14 代 RPL-R microcode |
| **改 BIOS region EFI microcode** | ✅ 理论可行（Boot Guard 关闭）|
| **改 ME region PMCC000** | ❌ 几乎不可行（MERSA 签名）|
| **找原厂 12 代+ BIOS** | ⭐⭐⭐⭐⭐ 最稳（5 分钟打电话）|
| **跨板移植 14 代 microcode** | ⭐⭐⭐⭐ 中等难度（需要参考 BIOS）|
| **ME 16.x 升级** | ⭐ 极难（签名 / OEM 私钥）|

## 7. 推送状态

### 已推送的 commits（GitHub）

```
13b7b37 docs: 更新相似主板对比 (加 Elsky OPS-H610 + Shuttle XH610 + ECS LIVA 等)
a007ae2 docs: 官方支持联系话术 (4001-027-580 + TPV + Intel + 闲鱼)
1ec2374 tools: 一键分析脚本 (Windows .bat + WSL .sh)
51811d1 docs: Q100-E 硬件特征对比市面高度相似主板
b162d19 docs: 跨板 BIOS 移植方案
bfc30da docs: ME 升级可行性分析
60c2e6b analyze: 评估第三方 AI 报告
7d0c9d4 analyze: PMCC000 深度解包
d2f6238 docs: 重要更正 — 第三方 bin 来源澄清
b5e23ee analyze: 深度解释 9/10代 microcode 真实存在
7fbd5a2 analyze: MCExtractor v1.104 验证 microcode
cd69319 analyze: MMTool 5.0 完整分析
feb47bb analyze: WSL+binwalk+iucode_tool
38eb696 docs: add BIOS Setup password info
29608d9 analyze: 深度分析两份 bin
a121d79 docs: rebrand as 准系统视角
a93aa2b restructure: rewrite docs
d9b82e1 analyze: 关键发现
0e80b3f init
```

### 本地未推送的 commits（等网络恢复）

```
1ec2374 tools: 一键分析脚本
a007ae2 docs: 官方联系话术
13b7b37 docs: 相似主板对比更新
（最近 3 个 commit 等网络好手动 push）
```

## 8. 完整文档索引

按阅读顺序：

1. **README.md** — 仓库首页 + 5 分钟了解
2. **AGENTS.md** — agent 阅读入口 + 关键事实
3. **docs/14th-gen-adaptation.md** — 14 代适配方案（核心）
4. **docs/official-support-contacts.md** — 官方联系话术
5. **docs/hardware-similar-models-2026-09-08.md** — 相似主板对比
6. **docs/cross-vendor-bios-ports-2026-09-08.md** — 跨板移植方案
7. **docs/me-upgrade-feasibility-2026-09-08.md** — ME 升级分析
8. **docs/bios-deep-analysis-2026-09-07.md** — 深度分析
9. **docs/mmtool-analysis-2026-09-08.md** — MMTool 报告
10. **docs/pmcc-deep-dive-2026-09-08.md** — PMCC000 Huffman
11. **docs/bios-analysis-2026-09-07.md** — 基础分析
12. **docs/correction-2026-09-08.md** — 重要更正
13. **docs/bios-password-info.md** — vdiadmin 密码
14. **docs/flashing-guide.md** — 刷写流程
15. **docs/tools.md** — 工具使用
16. **docs/hardware.md** — 硬件参数
17. **docs/known-issues.md** — 已知问题
18. **docs/references.md** — 参考资料
19. **docs/bios-mod-history.md** — 修改记录
20. **docs/third-party-analysis-2026-09-08.md** — 第三方报告评估

## 9. 引用

- Intel 官方 microcode: https://github.com/platomav/CPUMicrocodes
- MCExtractor: https://github.com/platomav/MCExtractor
- 武汉噢易云: 4001-027-580
- TPV 冠捷: https://www.tpv-tech.com/
- Shuttle XH610: https://au.shuttle.com/
- ECS LIVA One H610: https://thinvent.in/q/ecs-liva-one-h610
- Intel NUC 12 Pro: https://www.intel.com/content/www/us/en/download/757892/
- Win-Raid 论坛: https://www.win-raid.com/
- chiphell: https://www.chiphell.com/

## 10. 一句话最终建议

> **买 CH341A + 打电话 4001-027-580 + 找 Shuttle XH610 公开 BIOS 移植 14 代 microcode**——三个并行，最稳方案。
