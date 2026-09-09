# Q100-E 功耗墙解锁 — 可执行方案（2026-09-09）

> **目标**：解锁功耗墙，PL1/PL2 从 50W 提升到 65W/80W（适配 90W 电源）
> **关键定位**（已从 IFR 提取确认）：

## 0. 功耗墙变量完整定位

```
CpuSetup VarStore:
  GUID: B08F97FF-E6E8-4193-A997-5E9E9B0ADB32
  Name: CpuSetup (VarStoreId 0x1)
  Size: 0x3C1 (961 字节)

功耗墙变量（都在 CpuSetup VarStore 里）:
  Platform PL1 Power:  VarOffset 0x32 (4字节)  当前 0xC350 (50W)
  Platform PL2 Power:  VarOffset 0x38 (4字节)  当前 0xC350 (50W)
  Power Limit 4:       VarOffset 0x2B (4字节)  当前 0x15F90 (90W)
  Platform PL1 Enable: VarOffset 0x31 (1字节)
  Platform PL2 Enable: VarOffset 0x37 (1字节)
  Power Limit 4 Override: VarOffset 0x2A (1字节)
```

## 1. 推荐值（90W 电源适配器）

| 变量 | VarOffset | 当前 | 推荐 | 十六进制 |
| --- | --- | --- | --- | --- |
| PL1 Power | 0x32 | 50W | **65W** | `0xFDE8` (65000) |
| PL2 Power | 0x38 | 50W | **80W** | `0x13880` (80000) |
| PL4 | 0x2B | 90W | 保持 | `0x15F90` |

**功耗预算**（19V × 4.74A = 90W）：
- 非 CPU 部件（内存+SSD+主板+风扇）≈ 20-30W
- CPU 可用 ≈ 60-70W
- PL1=65W 是安全上限，PL2=80W 是峰值（留 10W 余量）

## 2. 方案 A：RU.efi 改 NVRAM（推荐，不改 BIOS 文件）

### 2.1 准备

1. 下载 RU.efi（UEFI 变量编辑器）：https://ruefi.blogspot.com/ 或 win-raid
2. 准备 FAT32 U 盘，把 RU.efi 放根目录（改名为 shellx64.efi 放 /efi/boot/）
3. U 盘插入 Q100-E

### 2.2 操作

```
1. 开机按 F7/F11 进 Boot Menu
2. 选 UEFI: USB (从 U 盘启动)
3. 进入 UEFI Shell（RU.efi 自动启动）
4. 在 RU.efi 主界面:
   - 按 Alt + = 打开变量列表
   - 找到 GUID B08F97FF-E6E8-4193-A997-5E9E9B0ADB32 (CpuSetup)
   - 选中后回车进入变量内容
5. 定位 VarOffset:
   - 0x32 处: PL1 Power（4字节，当前 50 C3 00 00 = 50000）
   - 0x38 处: PL2 Power（4字节，当前 50 C3 00 00 = 50000）
6. 修改:
   - PL1: 改成 E8 FD 00 00 (65000 = 65W)  [小端: 0xFDE8]
   - PL2: 改成 80 38 01 00 (80000 = 80W)  [小端: 0x13880]
7. 按 Ctrl + W 保存
8. 重启
9. 进 Windows 用 HWiNFO64 验证功耗
```

### 2.3 验证

```
1. HWiNFO64 → CPU → 看 Package Power
2. 跑 Cinebench R23 多核
3. 观察功耗:
   - 解锁前: 锁在 ~50W
   - 解锁后: 应该能到 ~65W (PL1)
4. 同时看 CPU 频率（应该比之前高）
```

### 2.4 注意

- RU.efi 改的是 NVRAM，如果 BIOS 每次启动都重置默认值，改动会失效
- 如果失效，需要改 BIOS 文件的 IFR Default（方案 B）

## 3. 方案 B：修 AMIBCP 语言错误（改 BIOS 文件，一劳永逸）

### 3.1 问题

AMIBCP 报 `Language name exceeds 0x08`，因为 ROM 的 HII 语言包名称超过 8 字节。

### 3.2 修复思路

1. 用 UEFIExtract 解包，找 HII 语言包
2. 找到语言名称字段（>8字节的字符串）
3. 改成 ≤8 字节（如 "en-US"）
4. 重新打包，AMIBCP 就能正常显示 Setup

### 3.3 风险

- 改语言包有风险，可能影响 BIOS 显示
- 需要 UEFIExtract + 手动编辑 + UEFIReplace
- 复杂，容易出错

## 4. 方案 C：Windows 工具（最简单，但可能被锁）

### 4.1 Intel XTU

```
1. 下载 Intel Extreme Tuning Utility
2. 打开 → Advanced Tuning
3. Turbo Boost Power Max (PL1) → 65W
4. Turbo Boost Short Power Max (PL2) → 80W
5. Apply
```

### 4.2 ThrottleStop

```
1. 下载 ThrottleStop
2. TPL 按钮 → Turbo Power Limits
3. Long Power PL1 → 65
4. Short Power PL2 → 80
5. Apply → OK
```

**注意**：如果 BIOS 锁了功耗墙（MSR 锁定），XTU/ThrottleStop 可能改不了，需要先方案 A 或 B。

## 5. 关键文件

- `backups/H610_full_32mb_V1.ifr_full.txt` — 完整 IFR（含 VarStore GUID + VarOffset）
- `docs/power-limit-analysis-2026-09-09.md` — 功耗墙完整分析
- `C:\SPI\ifr_setup.txt` — IFR 提取（临时）
- `C:\SPI\MMTool_a5.exe` — MMTool（注意：不适用改功耗墙）

## 6. 总结

| 方案 | 推荐度 | 说明 |
| --- | --- | --- |
| **A. RU.efi 改 NVRAM** | ⭐⭐⭐⭐ | 不改文件，GUID+VarOffset 已定位，最直接 |
| **B. 修 AMIBCP** | ⭐⭐⭐ | 一劳永逸但复杂有风险 |
| **C. XTU/ThrottleStop** | ⭐⭐⭐ | 最简单，但可能被 BIOS 锁 |

**推荐先试方案 C（XTU/ThrottleStop）**，如果被锁，再试方案 A（RU.efi），最后才是方案 B（修 AMIBCP）。
