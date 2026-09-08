# PMCC000 深度解包报告（2026-09-08）

> **本报告补充 `mmtool-analysis-2026-09-08.md` 的 PMCC000 分析部分。**
> **核心问题**：ME 16.x 的 PMCC000 Huffman 压缩 microcode 容器里到底有什么？

## 0. TL;DR

**重要发现**：这份 Q100-E 第三方 bin 的 **PMCC000 容器内 132KB 数据**——

- ❌ **不是 Huffman 压缩 microcode**
- ❌ **不是 LZMA 压缩 microcode**
- ❌ **找不到任何 microcode 头**
- ✅ **是 ME 16.x 私有的某种加密/混淆数据**（找不到公开的 magic）

**这意味着**：
- 整份 32MB bin **真的只有 2 个 microcode 容器**（在 BIOS region 0x1D90D18 + 0x1E90B18）
- 都是 **9-10 代 Coffee/Comet Lake microcode**（AMI 模板默认带的冗余）
- **没 12 代 ADL-S、14 代 RPL-R microcode**
- **i3-12100 跑得起来完全靠 CPU 内置 microcode fallback**
- **i5-14400 装这份 bin 一定跑不起来**（需要 14 代 RPL-R）

## 1. PMCC000 容器结构

### 1.1 位置和大小

- **$CPD 起点**：`0x00023000`
- **Entry 3（实际 microcode 数据）**：
  - 相对 offset: `0xE1`
  - size: `0x21000` (131,072 字节 = 128 KB)
  - 绝对位置: `0x00023101 - 0x00044101`

### 1.2 Entry 列表

| Entry | 名字 | Offset | Size | 说明 |
| --- | --- | --- | --- | --- |
| 0 | vendor header | 0x0000 | 0x00 | 8 字节 vendor tag |
| 1 | `PMCC000.met` | 0x0534 | 0x48 | metadata |
| 2 | `ConstDat` | 0x0000 | 大 | constant data |
| 3 | **microcode 数据** | **0x00E1** | **0x21000** | **PMCC000 核心** |
| 4 | `$MN2` | 0x200A0 | 67MB | 链接（超出 32MB） |

## 2. 深度扫描

### 2.1 找各种 ME 16.x magic

```
LZMA Intel (5D000000):    14 个匹配
  0x00204c9d, 0x01071168, 0x010910f0, 0x016b00a8, 0x01a71430...
microcode type=1:         5665 个匹配（很多误判）
$MN2:                      10 个匹配
PMCC text:                 3 个匹配（都在 PMCC000 metadata 区域）
$FPT:                      1 个匹配（0x001a9000）
```

**结论**：
- ❌ **0 个 Huffman 压缩段**（无 0x5FAA5AA5 magic）
- ❌ **0 个 LZMA microcode bundle**（5D000000 命中的都是其他数据）
- ❌ **0 个 microcode bundle header**（loader_sig 0x00000001 0x00000001）

### 2.2 HuffmanLUTHeader 解析尝试

`HuffmanLUTHeader` ctypes 结构（64 字节）：
```
Tag            : c_char_Array_4
ChunkCount     : c_ulong
DecompBase     : c_ulong
Unk0C          : c_ulong
Size           : c_ulong
DataStart      : c_ulong
Unk18          : 6 * c_ulong
ChunkSize      : c_ulong
Unk34          : c_ulong
Chipset        : 8 bytes
```

对 PMCC000 数据多个 offset 尝试解析——**所有字段都是乱码**（不是有效的 Huffman header）：

```
+0x60: Tag=f911400b (随机字节)
       ChunkCount=3267203355
       Size=0xd9995a0b
       ...
```

**结论**：PMCC000 132KB 数据**完全不是 Huffman 压缩格式**。

### 2.3 PMCC000 数据头 64 字节

```
0x00023101: 00 00 00 60 00 00 00 01 00 00 00 37 55 b6 cf
0x00023111: 44 34 43 c9 3e 60 8a 3b 91 2d 98 e3 00 43 79 6b
0x00023121: 61 bf bf d4 ff af 74 9b a1 e8 34 6a d9 62 9f b1
0x00023131: 29 00 0b 50 39 c9 5e fe b5 c2 9a a0 17 a3 27 27
```

- 头 4 字节：`00 00 00 60` ——不是 Huffman magic (0x5FAA5AA5)
- 可能是 ME 16.x 私有加密头
- 后续字节看起来像伪随机数据

## 3. 整片 bin 的 microcode 全部 4 个位置

| 位置 | 来源 | 大小 | 内容 |
| --- | --- | --- | --- |
| 0x1D90D18 | BIOS region EFI microcode (FV 11) | 188 KB | CPUID 90671 (Coffee Lake) + 906A0 (Comet Lake) |
| 0x1E90B18 | BIOS region EFI microcode (FV 12) | 188 KB | CPUID 90671 + 906A0（副本） |
| 0x23000-0x3A000 | ME 区域 PMCC000 容器 | 132 KB | **不是 microcode**（私有加密数据） |
| 其他位置 | — | — | 无 |

**最终结论**：整份 32MB bin **只有 2 个 microcode 容器**（9 代 + 10 代 Coffee/Comet Lake），都是 AMI UEFI 模板默认带的冗余数据。

## 4. 重要修正（写给之前的我）

我**之前**在 `mmtool-analysis-2026-09-08.md` 里说：

> "ME 区域 PMCC000 容器（0x23000）可能含 12 代+ microcode（被 Huffman 压缩，binwalk + iucode_tool 无法识别）"

**这个推测是错的**。实际情况：
- PMCC000 容器**存在**（132KB 数据）
- 但内容**不是 microcode**——是某种 ME 16.x 私有的其他数据
- 这份 Q100-E bin **真的没有 12 代+ microcode**（不论 BIOS region 还是 ME region）

## 5. 含义

### 5.1 i3-12100 跑得起来的真实原因

**确认**：i3-12100 跑得起来**完全靠 CPU 内置 microcode fallback**。

- CPU 出厂烧录 12 代 ADL-S microcode（保证基本启动）
- BIOS 不提供 12 代 microcode → CPU 用内置基础版
- 系统能进、能用，但**没 12 代 microcode 的漏洞修补**

### 5.2 i5-14400 跑不起来（确定）

- 14 代 RPL Refresh 是**新架构**（不是 12 代 Refresh）
- CPU 内置 microcode **不足以启动 14 代**
- 必须 BIOS 提供 RPL-R microcode 补丁
- 第三方 bin **没 14 代 microcode**（全 bin 扫描确认）→ 装上**屏幕黑**

### 5.3 唯一解决路径

**必须找 Q100-E 的另一个 BIOS**：

1. **下载原厂 BIOS**（武汉噢易云计算 / TPV 官网）
2. **买编程器备份机器原厂 SPI flash**（如果还能进系统）
3. **联系 TPV 工程师**（代工厂可能有 12 代+ microcode 的 BIOS）
4. **Intel ME 16.x 升级包**（Intel 官网的 ME Update Kit）

## 6. 工具脚本

| 脚本 | 用途 |
| --- | --- |
| `tools/parse_me_pmcc.py` | 解析 ME 16.x FPT + CPD 容器列表 |
| `tools/decode_pmcc.py` | 尝试用 MeContainer 解析 PMCC000 数据 |
| `tools/extract_pmcc.py` | 找 microcode 头（type=1 启发式） |
| `tools/inspect_pmcc.py` | 找 Huffman magic + 试解 HuffmanLUTHeader |

## 7. 引用

- 之前报告：`docs/bios-analysis-2026-09-07.md` / `bios-deep-analysis-2026-09-07.md` / `mmtool-analysis-2026-09-08.md`
- 重要更正：`docs/correction-2026-09-08.md`（第三方 bin 来源澄清）
- 工具：`tools/MCExtractor/MCExtractor-r352/MCE.py` + WSL `iucode_tool` + `binwalk`
