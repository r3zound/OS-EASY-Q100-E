# BIOS 备份与修改记录

## 1. 当前工作目录下的 BIOS 文件

| 文件 | 大小 | 描述 | 用途 |
| --- | --- | --- | --- |
| `bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin` | 32 MB | 改 BIOS 第二版：关闭超线程 + 解锁 PL4 + 解锁 ICCmax + 修改 C-State | 性能优化 / 高 TDP 适配 |
| `bios_大佬改好的_没解锁PL4之类的选项 跑不满i9会严重降频.bin` | 32 MB | 大佬改好的 BIOS，未解锁 PL4 等电源管理项 | 12 代标压 U 基础版 |

> 两个 .bin 均为 32 MB 整片 SPI flash 备份（含 BIOS + ME + GbE 等分区），不是纯 BIOS region。

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
| v1.0-14gen | 追加 RPL-R microcode，目标点亮 i5-14400 | ⏳ 待执行 |

### 3.2 已尝试的修改

> 留空，等实际操作后填

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
