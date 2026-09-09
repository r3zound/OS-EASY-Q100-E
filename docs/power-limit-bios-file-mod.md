# Q100-E 改 BIOS 文件解锁功耗墙 — 完整流程（2026-09-09）

> **目标**：修改 BIOS 文件本身，把 PL1/PL2 功耗墙从 50W 解锁到 65W/80W，刷写后永久生效。

## 0. 已完成的工作

### 0.1 功耗墙变量精确定位（IFR 提取）

```
CpuSetup VarStore GUID: B08F97FF-E6E8-4193-A997-5E9E9B0ADB32

功耗墙变量（6 处 PL=50W + 2 处 PL4=90W）:
  Platform PL1 Power (VarOffset 0x32): 0xC350 (50W) ×2
  Platform PL2 Power (VarOffset 0x38): 0xC350 (50W) ×2
  Power Limit 1 (VarOffset 0x17): 0xC350 (50W) ×1
  Power Limit 2 (VarOffset 0x1E): 0xC350 (50W) ×1
  Power Limit 4 (VarOffset 0x2B): 0x15F90 (90W) ×2
```

### 0.2 已修改 setup_body.bin

修改了 6 处功耗墙：
- PL1（3 处）：0xC350 (50W) → 0xFDE8 (65W)
- PL2（3 处）：0xC350 (50W) → 0x13880 (80W)
- PL4（2 处）：保持 0x15F90 (90W)

**产物**：`backups/setup_body_modified_PL65W_PL80W.bin`（1MB，修改后的 Setup 模块 PE32 镜像）

## 1. 关键难点：Setup 模块在压缩卷里

- 32MB bin 里的 Setup 模块是 **LZMA 压缩**存储的
- 直接 hex 改 32MB 不可行（功耗墙字节在压缩数据里找不到）
- 需要：解压 → 改（已完成）→ **重新打包替换回 32MB**

## 2. 最后一步：用 UEFITool NE 替换回 32MB

### 2.1 工具

`tools/UBU_1_79_alt/UEFITool_NE.exe`（GUI 工具）

### 2.2 操作步骤

```
1. 双击 UEFITool_NE.exe
2. File → Open → 选 C:\SPI\H610_V1.bin（或 backups/H610_full_32mb_V1.bin）
3. 左侧树形结构展开：
   Intel image
   └── BIOS region
       └── 4F1C52D3-D824-4D2A-A2F0-EC40C23C5916
           └── 9E21FD93-9C72-4C15-8C4B-E77F1DB2D792
               └── EE4E5898-3914-4259-9D6E-DC7BD79403CF
                   └── Volume image section (可能是 LZMA 压缩的)
                       └── 5C60F367-A505-419A-859E-2A4FF6CA6FE5
                           └── Setup (112 Setup)  ← 这里！
4. 右键 "Setup" → Replace body...
5. 选择 backups/setup_body_modified_PL65W_PL80W.bin
6. UEFITool NE 会自动重新压缩 + 重建 Volume
7. File → Save image file → 保存为 H610_V1_unlocked.bin
```

### 2.3 验证

```
1. 用 UEFIExtract 重新解包新 bin
2. 确认 Setup 模块的功耗墙值已改（用 ifrextract 看）
3. 或者用 MCExtractor 看 microcode 没变（确认只改了功耗墙）
```

## 3. 刷写 + 验证

```
1. FPT 备份当前 SPI（保险）: FPTW64.exe -d before.bin
2. FPT 刷写新 bin: FPTW64.exe -f H610_V1_unlocked.bin
3. 重启进 Windows
4. HWiNFO64 跑 Cinebench R23
5. 看 Package Power:
   - 解锁前: 锁 ~50W
   - 解锁后: 应到 ~65W (PL1)
```

## 4. 关键文件

| 文件 | 说明 |
| --- | --- |
| `backups/H610_full_32mb_V1.bin` | V1 原厂 32MB（基准）|
| `backups/setup_body_modified_PL65W_PL80W.bin` | 修改后的 Setup 模块（1MB）|
| `backups/H610_full_32mb_V1.ifr_full.txt` | 完整 IFR 提取（2.6MB）|
| `tools/modify_power_limit.py` | 功耗墙修改脚本 |
| `tools/find_power_limit.py` | 功耗墙定位脚本 |
| `tools/UBU_1_79_alt/UEFITool_NE.exe` | UEFITool NE（GUI 替换用）|

## 5. 推荐值回顾（90W 电源适配器）

| 变量 | 当前 | 修改后 | 说明 |
| --- | --- | --- | --- |
| PL1 | 50W | **65W** | i5-14400 PBP，长期功耗 |
| PL2 | 50W | **80W** | 睿频峰值，留 10W 余量 |
| PL4 | 90W | 90W | 保持 |

## 6. 风险提示

- ⚠️ 刷写前必须 FPT 备份当前 SPI
- ⚠️ 1.5L 散热上限 ~65W，PL1=65W 长时间满载会撞温度墙降频
- ⚠️ PL2=80W 峰值会贴 90W 电源，但瞬时 OK
- ⚠️ 改错会导致黑屏，用编程器救回

## 7. 总结

| 步骤 | 状态 |
| --- | --- |
| 1. 功耗墙精确定位 | ✅ 完成（GUID + VarOffset + 默认值）|
| 2. 修改 setup_body.bin | ✅ 完成（6 处：PL1→65W, PL2→80W）|
| 3. 替换回 32MB | ⏳ 待 UEFITool NE GUI 操作 |
| 4. 刷写 + 验证 | ⏳ 待执行 |
