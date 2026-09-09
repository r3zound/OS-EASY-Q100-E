# Tools 索引（Q100-E BIOS 美化项目）

> 项目工作根：`D:\OneDrive\User\硬件Fix\噢易乾Q100-E准系统\tools\`
> 项目目标：解锁隐藏 Setup 菜单（重点：功耗墙 60W→120W+）+ 替换开机 LOGO

## 📁 当前结构

```
tools/
├── 📌 主分析工具 (Python)
│   ├── analyze.py                              ⭐ 综合分析 (hash + FD + ME + microcode 位置)
│   ├── extract_setup_menu.py                   ⭐ Setup 字符串扫描（粗略）
│   ├── parse_ifr.py                             ⭐ IFR opcode 扫描（粗略）
│   ├── parse_ifr_v2.py                         ⭐ FFS 遍历（实验性）
│   ├── debug_fvh.py                            debug 工具
│   ├── debug_fvh2.py                           debug 工具
│   ├── debug2.py / debug3.py / debug_scan.py   debug 工具
│   ├── scan2.py                                debug 工具
│   ├── debug_fvh.py / debug_fvh2.py            debug 工具
│   ├── debug2.py / debug3.py / debug_scan.py   debug 工具
│   └── debug2.py / debug3.py / debug_scan.py   debug 工具
├── 🔧 BIOS 修改工具（Windows）
│   ├── AMI 8.0 BIOS修改工具(AMIBCP) 3.46 中文版\    ⭐ 解锁隐藏菜单首选
│   │   ├── AMIBCP346cn.exe                     中文版（推荐）
│   │   └── AMIBCP346.exe                       英文版
│   └── UBU_1_79_alt\                          UBU（垃圾佬圈，含 14代 microcode 库）
│                                               我们的 V1 已含 microcode，不需要 UBU 移植
├── 💾 Intel ME 工具集（V1 备份用过的）
│   └── CSME.System.Tools.v16.0.r8\           ⭐ Intel 官方工具集
│       ├── README.md                            工具使用手册
│       ├── Flash Programming Tool\            ⭐ FPT（备份/刷写）
│       ├── FWUpdate\                          通过 ME 通道更新
│       ├── MEInfo\                            查 ME 信息
│       ├── MEManuf\                           制造模式（危险）
│       ├── Manifest Extension Utility\        改 ME manifest
│       └── Modular Flash Image Tool\          高级多组件
├── 📦 备份的原始 CSME 工具（已 gitignore）
│   └── backups\CSME System Tools v16.0 r8\    V1 备份时拷的副本
└── ⚙️ 杂项
    └── __pycache__\                          Python 缓存（要清理）
```

## 🛠️ 推荐工作流（V1 改隐藏菜单 + 改 LOGO）

```
┌─ 提取原 LOGO（保护现状）────────────────┐
│ 1. 用 UEFITool NE 打开 backups\H610_full_32mb_V1.bin   │
│ 2. 找 "logo" / "Logo" 字符串                                │
│ 3. 导出为 bmp 保存为 backups\original_logo.bmp   │
└────────────────────────────────────────────────┘
                              ↓
┌─ 解锁隐藏菜单（重点：功耗墙 60W→120W+）─┐
│ 1. 打开 tools\AMI 8.0 BIOS修改工具(AMIBCP) 3.46 中文版\   │
│    AMIBCP346cn.exe                                          │
│ 2. File → Open → backups\H610_full_32mb_V1.bin   │
│ 3. 浏览 Setup 树（Main → Advanced → CPU Configuration）  │
│ 4. 右键隐藏菜单 → Unsuppress                            │
│ 5. 改默认值（PL1/PL2/PL4 60W→120W）         │
│ 6. Save As → backups\V1_unlocked.bin                │
└────────────────────────────────────────────────┘
                              ↓
┌─ 替换 LOGO ──────────────────────────────────┐
│ 1. 准备 BMP (1024x768 或 640x480)              │
│ 2. 用 MMTool 5.x 或 LogoBuilder 替换          │
│ 3. Save As → backups\V1_beautified.bin          │
└────────────────────────────────────────────────┘
                              ↓
┌─ 烧录测试 ──────────────────────────────────┐
│ 1. CSME FPT 备份当前 SPI 到 V0_backup.bin   │
│ 2. FPT 写 backups\V1_beautified.bin            │
│ 3. 重启进 BIOS 验证菜单 + LOGO              │
│ 4. 装 i5-14400 验证 14代 CPU 跑得起来   │
└────────────────────────────────────────────────┘
```

## 🔑 关键工具快捷方式

### 解锁隐藏菜单（重点：功耗墙）
```
tools\AMI 8.0 BIOS修改工具(AMIBCP) 3.46 中文版\AMIBCP346cn.exe
```

### 备份/刷写 SPI flash
```
tools\CSME.System.Tools.v16.0.r8\Flash Programming Tool\WIN64\FPTW64.exe
```

### 查 ME 信息
```
tools\CSME.System.Tools.v16.0.r8\MEInfo\WIN64\MEInfoWin64.exe
```

### 找 LOGO 位置
```
UEFITool NE (LongSoft) - https://github.com/LongSoft/UEFITool/releases
```

## 🗑️ 归档和清理（不删）

旧项目（microcode 移植方向）相关脚本，**已标记为归档**：
- `tools/archive/microcode_port_v1.py`（原 port_microcode.py）
- `tools/archive/microcode_port_v2.py`（原 port_microcode_v2.py）
- `tools/archive/microcode_inject_v2.py`（原 inject_microcode_v2.py）

旧报告（仅参考教训）：
- `docs/14th-gen-microcode-port-report-2026-09-08.md`
- `docs/cross-vendor-bios-ports-2026-09-08.md`
- `docs/me-upgrade-feasibility-2026-09-08.md`
- `测试bios文件/Q100E_with_14th_from_ShuttleXH610.bin`
- `测试bios文件/V2/`

## 📚 关键文档（按项目当前方向）

1. `tools/CSME.System.Tools.v16.0.r8/README.md` — **CSME 工具使用手册** ⭐
2. `tools/INDEX.md` — **本文件，工具索引**
3. `docs/setup-menu-unlock-guide.md` — 解锁菜单 + LOGO 替换完整指南
4. `docs/q100e-original-bios-analysis-2026-09-09.md` — V1 完整 microcode 分析
5. `backups/H610_SPI备份指导书.docx` — FPT 备份教程
6. `backups/执行记录.md` — FPT 备份操作记录
