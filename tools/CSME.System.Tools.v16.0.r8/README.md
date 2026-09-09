# Intel CSME System Tools v16.0 r8 — 工具使用手册

> **完整工具集 + 命令参考**
> 工具来源：Intel ME System Tools v16.0 r8（用户机器备份自 backups/）

## 1. 工具清单

```
CSME System Tools v16.0 r8/
├── Flash Programming Tool/    ← FPT 备份/刷写（最常用）
├── FWUpdate/                  ← 通过 ME 通道更新固件
├── MEInfo/                     ← 查 ME 信息
├── MEManuf/                    ← ME 制造模式
├── Manifest Extension Utility/ ← 修改 ME manifest
└── Modular Flash Image Tool/  ← 高级多组件 flash 工具
```

## 2. 工具用途与命令

### 2.1 🔥 Flash Programming Tool (FPT) — **最常用**

| 平台 | 可执行文件 | 用途 |
| --- | --- | --- |
| EFI64 | `EFI64/Fpt.efi` | UEFI Shell 下的 FPT |
| Linux64 | `LINUX64/FPT` | Linux 下的 FPT |
| WIN32 | `WIN32/FPTW.exe` | 32-bit Windows FPT |
| **WIN64** | **`WIN64/FPTW64.exe`** | **64-bit Windows FPT（最常用）** |

**常用命令**（管理员 CMD）：

```cmd
cd "D:\OneDrive\User\硬件Fix\噢易乾Q100-E准系统\tools\CSME.System.Tools.v16.0.r8\Flash Programming Tool\WIN64"

REM 1. 查看芯片信息（看锁状态）
FPTW64.exe -i

REM 2. 全量备份 SPI flash (32MB) - Q100-E H610 用
FPTW64.exe -d H610_full_32mb.bin
   备份后算 SHA256 验证
   certutil -hashfile H610_full_32mb.bin SHA256

REM 3. 只备份 BIOS region (16MB)
FPTW64.exe -bios -d bios_only.bin

REM 4. 只备份 ME region
FPTW64.exe -me -d me_only.bin

REM 5. 备份 GbE region
FPTW64.exe -gbe -d gbe.bin

REM 6. 验证备份（不写）
FPTW64.exe -v

REM 7. 完整写入（危险！要备份完整再操作）
FPTW64.exe -f new_image.bin
```

**错误速查**（参考 docs/backups/H610_SPI备份指导书.docx）：
- Error 26: SPI 读权限被锁 → BIOS 里关 SPI Lock
- Error 25: 写权限被锁 → 仅备份没影响
- Error 7: Region locked → BIOS 关闭保护
- Error 280: cannot disable write protect → FD 锁定，需跳线

### 2.2 FWUpdate — 通过 ME 通道更新

| 平台 | 可执行文件 | 用途 |
| --- | --- | --- |
| EFI64 | `EFI64/FWUpdLcl.efi` | UEFI Shell 下通过 ME 更新 BIOS |
| Linux64 | `LINUX64/FWUpdLcl` | Linux 通过 ME 更新 |
| WIN32 | `WIN32/FWUpdLcl.exe` | 32-bit Windows 通过 ME 更新 |
| WIN64 | `WIN64/FWUpdLcl64.exe` | 64-bit Windows 通过 ME 更新 |

**用法**：

```cmd
cd "...\FWUpdate\WIN64"

REM 显示帮助
FWUpdLcl64.exe -h

REM 通过 ME 通道刷写 BIOS（需要 ME 已工作）
FWUpdLcl64.exe -f H610_full_32mb.bin
```

**注意**：
- FWUpdate 通过 ME 通道刷写，**不直接写 SPI**
- 适合 Windows 下刷 ME 区域更新
- 但仍然需要 ME 与 SPI 之间的访问（很多 OEM 锁了）

### 2.3 MEInfo — 查 ME 信息

| 平台 | 可执行文件 | 用途 |
| --- | --- | --- |
| EFI64 | `EFI64/MEInfo.efi` | UEFI Shell 下查 ME 信息 |
| Linux64 | `LINUX64/MEInfo` | Linux 下查 ME 信息 |
| WIN32 | `WIN32/MEInfoWin.exe` | 32-bit Windows |
| **WIN64** | **`WIN64/MEInfoWin64.exe`** | **64-bit Windows** |

**用法**：

```cmd
cd "...\MEInfo\WIN64"

REM 显示 ME 信息
MEInfoWin64.exe -verbose

REM 显示特定属性
MEInfoWin64.exe -FEAT "MeFwUpdateEnabled"

REM 解析镜像文件
MEInfoWin64.exe <bin文件>
```

**注意**：
- MEInfo 不接受文件参数时，**从 HECI 接口读 ME**（需要 ME 已启动）
- 跑在已启的 Windows 下通常能读到 ME 信息
- 跑 `MEInfoWin64.exe -verbose` 看完整信息

### 2.4 MEManuf — ME 制造模式

| 平台 | 可执行文件 | 用途 |
| --- | --- | --- |
| EFI64 | `EFI64/MEManuf.efi` | UEFI Shell |
| Linux64 | `LINUX64/MEManuf` | Linux |
| WIN32 | `WIN32/MEManufWin.exe` | 32-bit Windows |
| **WIN64** | **`WIN64/MEManufWin64.exe`** | **64-bit Windows** |

**用法**：

```cmd
cd "...\MEManuf\WIN64"

REM 进入制造模式（危险！需要 HDAudioSPI 等支持）
MEManufWin64.exe -h

REM 解锁 SPI 区域（部分板子）
MEManufWin64.exe -unlock
```

**注意**：
- 这是**最强大也最危险**的工具
- 可以读写 ME 区域、修改 SPI Lock
- 改错直接**永久砖**
- **不推荐普通用户使用**

### 2.5 Manifest Extension Utility (meu) — 改 ME manifest

| 平台 | 可执行文件 | 用途 |
| --- | --- | --- |
| Linux64 | `LINUX64/meu` | Linux |
| WIN32 | `WIN32/meu.exe` | 32-bit Windows |

**用途**：
- 修改 ME manifest 字段（如 PCH sku、PCH stepping 等）
- 用于**伪 PCH**（rarely needed）
- 通常**不需要**用

### 2.6 Modular Flash Image Tool (mfit) — 高级多组件

| 平台 | 可执行文件 | 用途 |
| --- | --- | --- |
| Linux64 | `LINUX64/mfit` | Linux |
| WIN32 | `WIN32/mfit.exe` | 32-bit Windows |

**用途**：
- 高级：编辑多组件 flash 镜像
- 提取/合并 SPI flash 各部分（BIOS + ME + GbE）
- 主要用于 OEM 工厂生产

## 3. Q100-E BIOS 美化工作流

### 3.1 备份（已完成 ✅）

```cmd
cd "D:\...\CSME System Tools v16.0 r8\Flash Programming Tool\WIN64"
FPTW64.exe -i                    # 查芯片
FPTW64.exe -d H610_full_32mb.bin  # 备份
certutil -hashfile H610_full_32mb.bin SHA256
```

**结果**：
- backups/H610_full_32mb_V1.bin (32MB, SHA256 f0b0a2b6...)
- backups/H610_full_32mb_V2.bin (32MB, V1==V2 验证)

### 3.2 提取原 LOGO

```cmd
REM 1. 备份 V1 后，先转一份为分析用副本
copy backups\H610_full_32mb_V1.bin work\logo_extraction.bin

REM 2. 用 UEFITool NE 打开 work\logo_extraction.bin
REM    找 "logo" 字符串
REM    导出 logo 为 BMP
```

### 3.3 解锁隐藏菜单 + 改 LOGO

1. 打开 AMIBCP（`tools/AMI 8.0 BIOS修改工具(AMIBCP) 3.46 中文版/AMIBCP346cn.exe`）
2. File → Open → `backups/H610_full_32mb_V1.bin`
3. 浏览 Setup 树，**右键 → Unsuppress** 解锁隐藏菜单
4. 保存新 bin 为 `backups/V1_unlocked_PL120W.bin`
5. 替换 LOGO 图像（在 AMIBCP 内或用 MMTool）
6. 保存为 `backups/V1_beautified.bin`

### 3.4 烧录回 SPI flash

**先准备 CH341A 编程器**（救砖用）：
```cmd
REM 1. 先备份当前 SPI flash 到文件 A
FPTW64.exe -d before_write_32mb.bin

REM 2. 烧新 bin（V1_unlocked_PL120W.bin）
FPTW64.exe -f V1_unlocked_PL120W.bin
```

**如果失败**：
- 用 CH341A 编程器恢复备份的 before_write_32mb.bin
- 编程器方式不依赖 ME 状态

## 4. 关键风险

| 操作 | 风险 | 缓解 |
| --- | --- | --- |
| FPT -d (备份) | **0** | 只读不写 |
| FPT -f (写) | **中-高** | 先备份完整 SPI flash |
| AMIBCP 解锁菜单 | 中 | 解锁可能让 BIOS 不稳定，需测试 |
| AMIBCP 改 LOGO | 低 | 仅替换图像数据 |
| MEManuf 解锁 | **高** | 改错可永久砖 |
| ME 区域改写 | **极高** | 改错永久砖，需 CH341A |

## 5. Q100-E 项目的具体规划

```
1. ✅ 完成 FPT 备份原厂 V1/V2
2. ⏳ 提取 V1 原 LOGO
3. ⏳ 用 AMIBCP 解锁隐藏菜单 (HT/PL1/PL2/PL4/C-State/电压)
4. ⏳ 改 LOGO 为用户提供的图
5. ⏳ 烧录测试
6. ⏳ 装 i5-14400 验证
```

## 6. 重要文件清单

```
D:\OneDrive\User\硬件Fix\噢易乾Q100-E准系统\tools\
├── CSME.System.Tools.v16.0.r8\        ← Intel ME 工具集（V1 备份用的）
├── AMI 8.0 BIOS修改工具(AMIBCP) 3.46 中文版\
│   ├── AMIBCP346.exe                  ← AMIBCP 标准版
│   └── AMIBCP346cn.exe                ← AMIBCP 中文版（推荐用这个）
├── UBU_1_79_alt\                      ← UBU（垃圾佬圈的工具，含 14代 microcode 库）
│                                       （但我们 V1 已含 microcode，不需要 UBU 移植）
├── backups\CSME System Tools v16.0 r8\ ← 原始备份（已 gitignore）
├── backups\H610_full_32mb_V1.bin       ← 主参考（V1 = 原厂）
├── backups\H610_full_32mb_V2.bin       ← V2 验证备份
└── backups\H610_SPI备份指导书.docx     ← 完整备份教程
```

## 7. AMIBCP vs MMTool vs UEFITool NE — 选哪个？

| 工具 | 用途 | 何时用 |
| --- | --- | --- |
| **AMIBCP** | 解锁/隐藏菜单、改默认值 | ⭐ **改隐藏菜单首选** |
| **MMTool 5.x** | 改 IFR、Setup、默认值 | 改具体 Setup 数值时用 |
| **UEFITool NE** | 找 FFS、IFR、image 位置 | 改 LOGO 前看布局用 |
| **CSME FPT** | 备份/刷写 SPI flash | 备份/烧录用 |

**推荐工作流**：
1. **UEFITool NE** 找 LOGO 位置 + 提取
2. **AMIBCP** 解锁隐藏菜单
3. **MMTool 5.x** 改具体默认值
4. **CSME FPT** 烧写回 SPI flash
