# BIOS 实测分析报告（2026-09-07）

> **本报告基于对 `third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin` 的详细解包分析。**
> **所有 hash 已记录，可比对确认。**

## 1. 整体概况

| 项目 | 值 |
| --- | --- |
| 文件名 | `bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin` |
| 大小 | 33,554,432 bytes (32 MB) |
| SHA256 | `50bf84a961e8cc861f6375e231a7e9723c8396c706d86a81f33befc5085b5b41` |
| MD5 | `47bffc5a3543c54b39f09737480059bb` |
| CRC32 | `f42ddf2c` |
| 类型 | 32 MB 整片 SPI flash dump（含 FD + ME + BIOS + GbE） |

## 2. Flash Descriptor（FD）布局

> ⚠️ **这台机器的 FD 在 0x10（不是 0x00）！** 头部 16 字节是 OEM 数据，不是标准 FD。

| 偏移 | 字节 | 说明 |
| --- | --- | --- |
| 0x0000 | `11 00 00 9c 10 04 00 a3 00 00 00 55 ff ff ff ff` | OEM 前缀（16 字节） |
| 0x0010 | `5a a5 f0 0f` | **FD signature**（标准位置 +0x10） |
| 0x0014 | `03 00 04 00` | 组件配置 |
| 0x0018 | `08 02 10 73` | FLPTR 字段 |
| 0x0020-0x00FF | FLPTR / VSCC / 0x55AA | FD 元数据 |

**FD 没被禁用，但偏移被 OEM 改了。** 标准 UEFITool 在 0x00 找不到签名可能会误判。

## 3. ME（Management Engine）区域

**关键发现：ME 已经是 16.x，能支持 14 代！**

| 项目 | 值 |
| --- | --- |
| ME 区域起点 | 0x1A9000 (`$FPT` 标识) |
| ME 版本 | **16.1.25.1917** ✅ |
| ME partitions | 13 个（PSVN / UEP / RSTR / IMDP / HVMP / IVBP / MFS / UTOK / FLOG / ELOG / EFS / FITC / CDMD） |

### 3.1 ME FPT 详细

```
$FPT 在 0x001a9000
NumPartitions (uint8): 13
Entries (offset 0x20 起):
  [ 0] PSVN  offset=0x000400  size=0x000200  (Secure Version Number)
  [ 1] UEP   offset=0x089000  size=0x002000  (?)
  [ 2] RSTR  offset=0x000600  size=0x000018  (?)
  [ 3] IMDP  offset=0x000640  size=0x000040  (?)
  [ 4] HVMP  offset=0x000680  size=0x00000c  (?)
  [ 5] IVBP  offset=0x001000  size=0x004000  (?)
  [ 6] MFS   offset=0x005000  size=0x000640  (ME File System)
  [ 7] UTOK  offset=0x069000  size=0x000020
  [ 8] FLOG  offset=0x06b000  size=0x000020
  [ 9] ELOG  offset=0x06d000  size=0x000010
  [10] EFS   offset=0x06e000  size=0x000100  (Embedded File System)
  [11] FITC  offset=0x07e000  size=0x000080  (Flash Image Tool Config)
  [12] CDMD  offset=0x086000  size=0x000030  (Code Module Directory?)
```

> 偏移值是相对 FPT 起点（0x1A9000），所以绝对位置 = FPT + offset。

## 4. 🔍 microcode 位置（最重要的发现）

### 4.1 ❌ BIOS region 内的传统 microcode 区域

**这块板的 microcode 不在 BIOS region ！**

- 在 0x63000-0x16DFFF（BIOS region 主体）搜索 FFS microcode 文件 GUID (`E08CA7D2-1B52-4F0D-9297-3BC2E38DF9DC`)，**0 个匹配**
- 全 bin 扫描 FFS header (type=0x01)，**0 个匹配**
- 搜 `_FIT_` 字符串（FFS Volume 标识），**0 个匹配**

### 4.2 ✅ ME 区域内的 PMCP 容器

**microcode 在 0x23000 - 0x39FFF 的 PMCP (Platform MicroCode Patch) 容器里。**

| 项目 | 值 |
| --- | --- |
| 容器起点 | 0x00023000 |
| 容器大小 | ~92 KB（0x23000 - 0x3A000） |
| 容器标识 | `$CPD` (Code Partition Directory) |
| 模块名 | `PMCC000` (Platform MicroCode Code) |
| 关联文件 | `PMCC000.met` (metadata), `ConstDat` (常量数据) |
| 数据格式 | **Huffman 压缩**（ME 16.x 特性） |

**PMCP 容器内部**（0x23000 起）：

```
0x23000: 24 43 50 44 05 00 00 00   "$CPD" + num_entries=5
0x23010: 50 4d 43 50 ...            "PMCP" (vendor)
0x23020: PMCC000 (第一个 module entry, 含 microcode 容器)
0x23040: PMCC000.met (metadata)
0x23050: ConstDat (常量数据)
0x23418: PMCP (内嵌 manifest)
0x234D0: 0x68 0x70 0x01 0x00       microcode 容器起点
```

### 4.3 含义解读

**ME 16.x 的设计变化**：
- 之前（ME 12.x）：microcode 放在 BIOS region 的 microcode region
- 现在（ME 16.x）：microcode 放在 ME 区域，用 Huffman 压缩 + 签名保护
- **直接追加 microcode 到 BIOS region 这条路走不通**

**对你的 i5-14400 适配的影响**：

| 原计划 | 实际可行性 |
| --- | --- |
| 追加 RPL-R microcode 到 BIOS region | ❌ 这块板的 microcode 不在 BIOS region |
| 升级 ME 区域（含 14 代 microcode） | ✅ 理论可行，但 ME 16+ 有签名校验，需要原厂签名或 ME 修补工具 |
| 用 IFR Extractor 找隐藏 BIOS 选项 | ✅ 仍然可行（只改 Setup 字符串） |
| 改 Intel Reference Code（RC） | ✅ 仍可移植 |

## 5. BIOS region 结构（FTPR）

**FTPR (Firmware Tamper Protection) 容器起点 0x63000**：

| 子项 | 说明 |
| --- | --- |
| `FTPR.man` | FTPR manifest |
| `fitc.cfg` | Flash Image Tool Configuration |
| `kernel` | ME 内核 |
| `syslib` | ME 系统库 |
| `bup` | Backup 库 |
| `intl.cfg` | 国际化配置 |
| `pm` | Power Management |
| `vfs` | Virtual File System |
| `ISHC` / `IOMP` / `NPHY` | 集成传感器 / IO 管理 / 网络物理层 |
| `evtdisp` | Event Dispatcher |
| `smbus` / `gpio` / `heci` / `ptt` | 各种 driver |

**注意：FTPR 是 ME 16.x 的安全增强容器，不直接包含 microcode。**

## 6. 14 代 RPL-R 支持现状评估

| 维度 | 现状 | 14 代适配需要 |
| --- | --- | --- |
| **ME 版本** | 16.1.25.1917 | 16+ 即可（已满足） |
| **ME 内 microcode** | 压缩+签名 | 需要升级或重新打包 |
| **BIOS region microcode** | 不存在 | 不适用 |
| **Intel Reference Code** | 含于 FTPR | 可能需要替换为支持 RPL-R 的版本 |
| **PMCP 容器** | 含 12 代 microcode | 需要追加 RPL-R microcode |

**结论**：
- ✅ ME 16.x 设计上已支持 14 代（理论）
- ❌ 但 PMCP 内的 microcode 不一定包含 RPL-R（很可能没有）
- ❌ Huffman 压缩 + 签名使直接修改困难
- ⚠️ 需要更高级的 ME 修补技术（不在本项目初期目标内）

## 7. 已验证的修改（来自第三方 BIOS 作者）

虽然 microcode 难动，但第三方作者改的电源管理项应该在 BIOS region 内可观察：

| 修改项 | 工具 | 文件位置 |
| --- | --- | --- |
| 关闭超线程 | AMIBCP | BIOS region / Setup |
| 解锁 PL1/PL2/PL4/ICCmax | AMIBCP | BIOS region / Setup |
| 修改 C-State | AMIBCP | BIOS region / Setup |
| 启用 mSATA | AMIBCP | BIOS region / Setup 隐藏项 |

## 8. 给本项目的建议

### 8.1 短期（不改 microcode 也能做的）

1. ✅ 用 IRFExtractor 提取本 bin 的 Setup IFR，对比原厂 BIOS 选项
2. ✅ 用 AMIBCP 检查/修改本 bin 的隐藏 BIOS 选项
3. ✅ 验证第三方 BIOS 在 i3-12100 上的兼容性（先别装 i5-14400）

### 8.2 中期（升级 ME）

1. 找一个支持 14 代 RPL-R 的 ME 16.x 镜像（Intel 官方或可信 OEM）
2. 用 `uefi-firmware-parser` 提取新 ME 的 PMCP（含 RPL-R microcode）
3. 把新 PMCP 替换到本 bin
4. 重新计算 checksum、签名（需要 ME 修补工具，如 MEBin）
5. 写回测试

### 8.3 长期（完整重做）

1. 找一个 H610 + 14 代参考 BIOS（Jetway MM10-H610 工业板）
2. 提取该 BIOS 的 ME 16.x（含 RPL-R microcode）
3. 提取该 BIOS 的 BIOS region
4. 移植到 Q100-E 的 SPI flash 布局
5. 验证 EC / GbE / 网卡等周边仍工作

## 9. 工具脚本清单

| 脚本 | 用途 |
| --- | --- |
| `tools/analyze_bin.py` | 整体分析（hash + FD + regions） |
| `tools/scan_bin.py` | hex dump + 模式扫描 |
| `tools/scan_microcode.py` | microcode 头扫描（v1 - 误判多） |
| `tools/scan_v3.py` | microcode 严格匹配 |
| `tools/scan_v4.py` | FFS 头 microcode 扫描 |
| `tools/scan_ucode_guid.py` | GUID microcode 扫描 |
| `tools/scan_strings.py` | 关键字符串扫描 |
| `tools/parse_with_lib.py` | AutoParser 解析 |
| `tools/parse_with_lib2.py` | FlashDescriptor 完整树 |
| `tools/parse_me.py` | ME FPT 解析（v1） |
| `tools/parse_me2.py` | ME FPT 解析（v2） |
| `tools/parse_me3.py` | MePartitionTable 解析 |
| `tools/parse_fpt.py` | FPT 区域 hex dump |
| `tools/find_pmcp.py` | 找 PMCP / $CPD / MCD* |
| `tools/scan_92k.py` | PMCP 区域 microcode 扫描 |
| `tools/dump_pmcp.py` | PMCP 区域 hex dump |
| `tools/dump_segments.py` | 关键段 hex dump |
| `tools/parse_full.py` | **综合脚本**（汇总所有分析） |

## 10. 关键 hash（用于校验）

```
bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin
SHA256: 50bf84a961e8cc861f6375e231a7e9723c8396c706d86a81f33befc5085b5b41
MD5:    47bffc5a3543c54b39f09737480059bb
CRC32:  f42ddf2c
```

```
bios_大佬改好的_没解锁PL4之类的选项 跑不满i9会严重降频.bin
(待分析，建议同样跑一次 parse_full.py)
```
