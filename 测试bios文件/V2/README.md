# ⚠️ V2 移植方案（按元宝 AI 思路）

> **核心思想（来自元宝 AI 的 `extract_inject_guide.md`）**：
> **只移植 microcode 块，不动其他 BIOS 内容**。
> **不截断，完整 14代 microcode 注入。**

## 0. 与 V1 的区别

| 维度 | V1（已完成） | V2（本目录） |
| --- | --- | --- |
| **方法** | 直接覆盖 Q100-E microcode 容器 | 完整 microcode 注入（不截断） |
| **microcode 大小** | 188KB 容器 → 212KB microcode | 找 0xFF 区域放完整 212KB |
| **状态** | ⚠️ 截断 24KB，MCExtractor 报 corrupted | ✅ 完整 microcode |
| **风险** | 中（i5-14400 可能 fallback 启动） | 低（microcode 完整） |
| **工具** | `port_microcode_v2.py` 直接覆盖 | MCExtractor + MMTOOL + Python FFS 编辑 |

## 1. 文件清单

| 文件 | 大小 | 来源 | 说明 |
| --- | --- | --- | --- |
| `cpuB0671_完整.bin` | 211,968 字节 | Shuttle XH610 0x1ECB000 提取 | 14代 RPL-S Refresh microcode (rev 0x12B, 2024-08-29) |
| `cpu90672_12代备份.bin` | 224,256 字节 | Shuttle XH610 0x1E05000 提取 | 12代 ADL-S microcode (rev 0x37, 2024-05-29) —— 备份参考 |

## 2. V2 移植流程

### 2.1 准备工作

```
✅ 备份当前 SPI flash（CH341A）
✅ 下载 Shuttle XH610 v2.11 BIOS（已在 third-party-bios/Shuttle XH610/）
✅ MCExtractor 提取 microcode（已在 tools/MCExtractor/）
✅ Python 3 + pltable（已装）
✅ NeoProgrammer（烧录）
✅ MMTool.exe（Windows 工具，V2 必需）
```

### 2.2 步骤 1：兼容性预检（按元宝 AI 思路）

```bash
# 在 Windows 上
python check_compat.py Q100E_original.bin ShuttleXH610.bin
```

参考 `third-party-bios/Shuttle XH610/yuanbao/check_compat.py`，它检查：
- 大小一致（都是 32MB）
- AMI 特征字符串
- UEFI FV 特征 (`_FVH`)
- 14代 microcode rev 0x12B 出现次数

**预期结果**：
- ✅ 大小一致（32MB）
- ✅ AMI/UEFI 特征
- ✅ XH610 含 0x12B，Q100E 缺 → 注入有效

### 2.3 步骤 2：写新 microcode 文件到 Q100E 的 microcode 卷

**思路**（元宝 AI 的 extract_inject_guide.md 步骤 3）：
1. 用 MMTool 打开 Q100E_original.bin
2. 定位 microcode 卷
3. 添加 `cpuB0671_完整.bin`
4. 保存

**但** Q100E 的 microcode 卷**容量有限**——`cpuB0671_完整.bin` 是 212KB，超过 Q100E 容器 188KB。

**解决方法**：
- MMTool 自动分配新 FFS entry 到卷的**空闲区域**（0xFF 填充部分）
- Q100E 的 FV 11 区域（0x1D90000-0x1E70000，1.5MB）有大量 0xFF 空白
- 212KB 的 microcode 头 + 数据可放入这些空白

### 2.4 步骤 3：验证

```bash
# 用 MCExtractor 验证
python tools/MCExtractor/MCExtractor-r352/MCE.py -skip -exit Q100E_with_14th_v2.bin
```

**预期结果**：
- 0x1D90D18 仍是 90671（原 9代 microcode，**不删**）
- 0x1E90B18 仍是 90671（副本）
- **新增 0x1D9xxxxx 位置** = B0671 14代 microcode（**完整 212KB**）

### 2.5 步骤 4：烧录

参考 V1 的烧录流程（README 第 4 节）。

## 3. 自动化脚本（V2 专用）

### 3.1 自动注入脚本（injection_v2.py）

**思路**：模拟 MMTool 的"添加新 microcode FFS entry"逻辑，用 Python 实现：

```python
# 伪代码
1. 找到 Q100E bin 里的 microcode FFS 卷
2. 找卷内最大空闲 FF 区域（能装下 212KB + 头部）
3. 创建新 FFS microcode 文件 entry
   - GUID: EFI_FIRMWARE_FILETYPE_MICROCODE
   - 头: 25 字节（GUID + checksum + type + attr + size + state）
   - 数据: cpuB0671_完整.bin (212KB)
4. 改卷头大小字段（如果需要）
5. 写新 bin
```

**难点**：
- 解析 FFS 卷头（_FVH 标识）
- 找 FFS 文件 entry
- 修改 EFI_FV_FILETYPE_MICROCODE 的 entry
- 重新计算 checksum

### 3.2 状态

- 🟡 **待写** `injection_v2.py`
- 🟡 **待写** FFS 编辑底层函数
- 🟢 已有 MCExtractor 提取的 microcode 文件（在本目录）

## 4. V1 vs V2 对比

| 维度 | V1 | V2 |
| --- | --- | --- |
| 文件位置 | `../Q100E_with_14th_from_ShuttleXH610.bin` | `../V2/Q100E_with_14th_v2.bin`（待生成）|
| 方法 | 直接覆盖 microcode 容器 | 添加新 microcode FFS entry |
| 截断 | **有**（24KB）| **无** |
| MCExtractor 警告 | "corrupted" | "正常" |
| microcode 完整性 | 缺部分数据 | 完整 |
| 工具 | `port_microcode_v2.py` | MMTool + 自动化脚本 |
| 难度 | 低 | 中 |
| 风险 | 中（缺数据）| 低（完整数据）|

## 5. 元宝 AI 思路精华（V2 核心）

来自 `third-party-bios/Shuttle XH610/yuanbao/XH610_分析结论.md`：

> **这份 XH610 BIOS 最大的价值不是"整包刷"，而是它比噢易云定制 BIOS 开放得多——Setup 变量表完整**。
> **正确的跨板复用方式是"模块化提取"：只取 microcode（CPU 支持），最多参考 Setup 选项的 VarStore 结构，绝不整包替换。**

应用到 V2：
- ✅ 只移植 microcode 块
- ✅ 不动 EC / Super I/O / ME / Setup
- ✅ 保留 JHS65F（Q100E）原版一切，只新增 CPU 识别能力
- ✅ 最小改动 = 最小风险

## 6. ⚠️ 风险与限制

### 6.1 V2 特有风险

| 风险 | 说明 | 缓解 |
| --- | --- | --- |
| MMTool 不支持 | MMTool 是 Windows GUI，WSL 不能用 | 用 Wine 跑 / 在 Windows 实机 |
| FFS 容量计算错误 | 卷内空 FF 区域不够 | 提前算好 |
| 写错文件 | 烧不进 BIOS | MMTool 验证步骤 |
| ME 签名 | 不动 ME → 安全 | 不动 ME 区域 |

### 6.2 通用风险（V1/V2 共用）

- **必须备份当前 SPI flash**——任何操作前
- **必须用 CH341A + 烧录夹**——不依赖 BIOS 软件刷写
- **必须准备 i3-12100（12代）CPU**——回退方案
- **必须知道怎么拆 SPI flash 芯片**——可能需要热风枪

## 7. 进度状态

- [x] **元宝 AI 思路研究**（`check_compat.py` + `extract_inject_guide.md` + `XH610_分析结论.md`）
- [x] **V1 完成**（直接覆盖，截断 24KB）——在 `../`
- [x] **V2 资源就绪**（B0671 microcode 完整 212KB）——在本目录
- [x] **V2 扫描器写好**（`tools/inject_microcode_v2.py`）——只报告不注入
  - 发现 microcode 容器**后** 0x01dbf198 有 **528KB 连续 FF 区**（足够装 212KB B0671）
- [x] **MMTool 操作指南**在本目录 README
- [ ] **V2 bin 生成**（用 MMTool GUI 跑）——待用户操作
- [ ] **V2 实际烧录测试**——等用户备份 + CH341A

## 8. 相关文件

- `../Q100E_with_14th_from_ShuttleXH610.bin` — V1 输出（截断 24KB）
- `../README.md` — V1 测试警告
- `../../tools/MCExtractor/MCExtractor-r352/Extracted/Intel/` — 所有 microcode 提取
- `../../tools/port_microcode_v2.py` — V1 自动脚本
- `../../third-party-bios/Shuttle XH610/yuanbao/` — 元宝 AI 完整分析
- `../../docs/14th-gen-microcode-port-report-2026-09-08.md` — 完整移植报告
- `../../docs/cross-vendor-bios-ports-2026-09-08.md` — 跨板移植方案

## 9. 一句话

> **V1 已完成（直接覆盖方案，可能截断 24KB）**
> **V2 待做（按元宝 AI 思路的不截断方案，需要 MMTool GUI 或写 FFS 注入脚本）**
> **两者都是「未测试的实验品」—— 刷写前必备份！**

最后更新：2026-09-09
