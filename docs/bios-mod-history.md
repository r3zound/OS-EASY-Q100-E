# BIOS 备份与修改记录

## 1. 当前 BIOS 文件（位于 `third-party-bios/`）

| 文件 | SHA256 | 描述 | 用途 |
| --- | --- | --- | --- |
| `bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin` | `50bf84a961e8cc861f6375e231a7e9723c8396c706d86a81f33befc5085b5b41` | 改 BIOS 第二版：关闭超线程 + 解锁 PL4 + 解锁 ICCmax + 修改 C-State | 性能优化 / 高 TDP 适配 |
| `bios_大佬改好的_没解锁PL4之类的选项 跑不满i9会严重降频.bin` | `bf0463f2378c53151aec19a8445c76098b46729c6cb2da7b19db4eda95949a45` | 大佬改好的 BIOS，未解锁 PL4 等电源管理项 | 12 代标压 U 基础版 |

> 两个 .bin 均为 32 MB 整片 SPI flash 备份（含 BIOS + ME + GbE 等分区），不是纯 BIOS region。
> 两份文件 ME 部分相同（都是 ME 16.1.25.1917），差异在 BIOS region（电源管理项）。

## 2. 当前 14 代适配项目使用的备份

> **待补充**：本项目首次备份后填入

```
[ ] 原厂未改 bin（编程器读出，已校验 CRC32 / SHA256）
    文件名：
    CRC32：
    SHA256：
    备份时间：
    备份工具：NeoProgrammer
    备注：
```

## 3. 修改记录

### 3.1 计划中的修改

| 版本 | 描述 | 状态 |
| --- | --- | --- |
| v1.0-14gen | 追加 RPL-R microcode，目标点亮 i5-14400 | ⏳ **方案调整**（见 bios-analysis-2026-09-07.md） |

### 3.2 已尝试的修改

> 留空，等实际操作后填

### 3.3 分析记录（2026-09-07）

详见 [bios-analysis-2026-09-07.md](bios-analysis-2026-09-07.md)。

关键发现：
- ✅ 两份 bin 整体结构一致（FD + ME + BIOS）
- ✅ ME 已经是 16.1.25.1917（设计支持 14 代）
- ❌ microcode **不在** BIOS region 内的传统 FFS microcode 文件
- ✅ microcode 在 ME 区域 PMCC000 容器（0x23000 起，huffman 压缩）
- ⚠️ 这意味着原"追加 microcode 到 BIOS region"方案需重做

接下来可能要做的：
1. 装 i5-14400 试一下（ME 16.1.25.1917 可能已含 RPL-R）
2. 如不亮，再考虑 huffman 解压 PMCC000 升级 microcode
3. 或升级 ME（高级操作）

## 4. 文件命名规范（建议）

```
backups/
├── original/
│   ├── Q100E_original_2026xxxx.bin
│   └── Q100E_original_2026xxxx.sha256
├── modified/
│   ├── Q100E_v1.0_14gen_2026xxxx.bin
│   └── Q100E_v1.0_14gen_2026xxxx.sha256
└── experiments/
    └── （失败案例留档，避免重复踩坑）
```

## 5. 重要提醒

- 任何 .bin 备份都**必须**配同名 .sha256（用 `Get-FileHash` 生成）
- 工作副本与原厂副本分开存放
- 改 BIOS 失败的 bin 也要保留（方便回滚分析）
