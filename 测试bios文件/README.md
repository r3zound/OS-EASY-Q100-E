# 测试 BIOS 文件（功耗墙解锁版）

> ⚠️ **本目录的 .bin 文件是修改功耗墙后的测试版，刷写前务必先 FPT 备份当前 SPI！**

## 当前文件

| 文件 | 大小 | 说明 |
| --- | --- | --- |
| `H610_V1_PL65W_PL80W.bin` | 32 MB | **功耗墙解锁版**：PL1 50W→65W，PL2 50W→80W |

## 修改内容

基于 `backups/H610_full_32mb_V1.bin`（原厂 V1），修改了 Setup 模块里的功耗墙默认值：

| 变量 | VarOffset | 原值 | 新值 |
| --- | --- | --- | --- |
| Platform PL1 Power | 0x32 | 50W (0xC350) | **65W (0xFDE8)** |
| Platform PL2 Power | 0x38 | 50W (0xC350) | **80W (0x13880)** |
| Power Limit 1 | 0x17 | 50W (0xC350) | **65W (0xFDE8)** |
| Power Limit 2 | 0x1E | 50W (0xC350) | **80W (0x13880)** |
| Power Limit 4 | 0x2B | 90W (0x15F90) | 保持 |

共 6 处功耗墙修改（PL1×3, PL2×3），全部在 CpuSetup VarStore（GUID `B08F97FF-E6E8-4193-A997-5E9E9B0ADB32`）。

## 验证结果

- ✅ 差异范围只在 LZMA section（0x1091000-0x1372000，3MB），未破坏其他数据
- ✅ PL=50W 旧值全部消失
- ✅ PL=65W 新值 3 处，PL=80W 新值 3 处
- SHA256: `5317dbc7453bb1674af7cad97c2d0c3c15a5e576a55818aa33fdd6060d67fd78`

## ⚠️ 刷写前强制清单

```
✅ 已用 FPT 备份当前 SPI（fptw64.exe -d backup.bin）
✅ 备份已算 SHA256 并保存到独立位置
✅ 已知如何用 CH341A 编程器救砖
✅ 90W 电源适配器（19V 4.74A）
```

## 刷写方法

```
1. FPT 备份当前 SPI（保险）
   fptw64.exe -d before_flash.bin

2. FPT 刷写新 bin
   fptw64.exe -f H610_V1_PL65W_PL80W.bin

3. 重启进 Windows
4. HWiNFO64 跑 Cinebench R23，看 Package Power:
   - 解锁前: 锁 ~50W
   - 解锁后: 应到 ~65W (PL1)
```

## 风险提示

- ⚠️ 1.5L 散热上限 ~65W，PL1=65W 长时间满载会撞温度墙降频
- ⚠️ PL2=80W 峰值会贴 90W 电源，但瞬时 OK
- ⚠️ 改错会导致黑屏，用编程器救回
- ⚠️ 这是**未实机验证的测试版**，风险自负

## 相关文档

- `docs/power-limit-bios-file-mod.md` — 完整修改流程
- `docs/power-limit-analysis-2026-09-09.md` — 功耗墙分析
- `tools/modify_power_limit.py` — 功耗墙修改脚本
