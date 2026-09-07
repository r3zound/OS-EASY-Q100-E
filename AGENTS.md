# 噢易乾 Q100-E BIOS Mod — 14 代 CPU 适配项目

> 武汉噢易云计算（OS-Easy）乾 Q100-E 准系统小主机的 BIOS 改装项目
> **当前目标：把 H610 定制板（原配 12 代）改造为支持 Intel 14 代 Raptor Lake Refresh CPU（目标 U：i5-14400）**

## 项目背景

- **机器**：噢易乾 Q100-E 准系统小主机（武汉噢易云计算 12 代云终端）
- **当前状态**：i3-12100 正常运行中，准备上 i5-14400
- **平台**：LGA1700 + H610 定制板（具体芯片待实测）
- **BIOS 容量**：32MB 整片 SPI flash（含 BIOS + ME + GbE 等分区）
- **刷写工具**：CH341A 编程器 + 烧录夹（NeoProgrammer）

## 项目目标

- **核心目标**：在不动 ME 的前提下，向原厂 BIOS 注入 14 代 RPL-R microcode + 必要的 Intel Reference Code 补丁，使 H610 板能点亮 i5-14400
- **次要目标**：保留 i3-12100 兼容性（不能改完 14 代后 12 代不亮了）
- **终极目标**：形成可复用的「备份 → 改 microcode → 校验 → 刷回 → 验证」一站式流程，公开给同型号玩家

## 工作目录

```
D:/OneDrive/User/硬件Fix/噢易乾Q100-E准系统/
├── AGENTS.md                    # 本文件（agent 阅读入口）
├── README.md                    # GitHub 仓库入口
├── .gitignore                   # git 忽略配置
├── docs/                        # 资料文档
│   ├── hardware.md              # 硬件参数
│   ├── 14th-gen-adaptation.md   # 【核心】14 代 CPU 适配技术方案
│   ├── bios-mod-history.md      # BIOS 备份与修改记录
│   ├── known-issues.md          # 已知问题
│   ├── tools.md                 # 工具指南
│   ├── flashing-guide.md        # 刷写流程
│   └── references.md            # 外部资料链接
├── backups/                     # BIOS 原始/改版备份（待组织）
│   └── README.md
└── tools/                       # 工具脚本（待添加）
    └── README.md
```

## 关键事实

- [x] 当前 CPU：i3-12100（能正常进系统）
- [x] 目标 CPU：i5-14400（RPL-R, 10核16线程, 65W TDP, UHD730）
- [x] 平台：LGA1700 + H610
- [x] BIOS 容量：32MB 整片 SPI flash
- [x] 仓库地址：https://github.com/r3zound/OS-EASY-Q100-E
- [ ] BIOS 芯片具体型号（Winbond / Macronix / GigaDevice 等，待拆机确认）
- [ ] 当前 BIOS 版本号（待用 UEFITool / ME Analyzer 分析）
- [ ] ME 区域版本与大小（决定能否不动 ME 改 microcode）
- [ ] 当前 BIOS 已含哪些 microcode 版本（ADL-S? RPL-S? RPL-R?）
