# Q100-E 功耗墙解锁指南（60W → 120W+）

> **目标**：把 Q100-E 的 CPU 功耗上限从 60W 解锁到 120W+（让 i5-14400 跑满 65W PL1 / 148W PL2）
> **工具**：AMIBCP 3.46 中文版（`tools/AMI 8.0 BIOS修改工具(AMIBCP) 3.46 中文版/AMIBCP346cn.exe`）

## 0. 关键结论（扫描 V1 结果）

| 检查项 | 结果 |
| --- | --- |
| "Power Limit" 明文字符串 | ❌ 几乎没找到（功耗墙藏在 IFR 编码里，不是明文）|
| "60W" 值（60000 mW） | ❌ 没找到（说明 60W 可能是运行时限制，不是 BIOS 静态默认值）|
| "65W" 值（65000 mW） | ✅ 1 个（0x01d54a2a）— 可能是 i5-14400 的 PL1 |
| "120W" 值（120000 mW） | ✅ 4 个 |
| "125W" 值（125000 mW） | ✅ 4 个 |
| CpuSetup 变量 | ✅ 7 处（首在 0x01000df9）|

**结论**：功耗墙不在 SPI flash 的明文里，而是：
1. 编译在 **IFR（Internal Forms Representation）二进制编码**里
2. 存在 **CpuSetup NVRAM varstore** 里
3. 需要用 **AMIBCP** 打开并可视化编辑

## 1. 用 AMIBCP 解锁功耗墙的步骤

### 1.1 打开 V1 BIOS

```
1. 双击 tools\AMI 8.0 BIOS修改工具(AMIBCP) 3.46 中文版\AMIBCP346cn.exe
2. File → Open (或 文件 → 打开)
3. 选择 backups\H610_full_32mb_V1.bin
4. 等待加载（AMIBCP 会解析整个 Setup 树）
```

### 1.2 找功耗墙菜单

在 Setup 树中查找（**常见路径**）：

```
Setup 树
├── Main
├── Advanced
│   ├── CPU Configuration        ← 重点看这里
│   │   ├── Hyper-Threading
│   │   ├── Active Processor Cores
│   │   ├── Intel (VMX) Virtualization
│   │   ├── CPU Power Management ← 功耗墙在这里
│   │   │   ├── Package Power Limit 1 (PL1)  ← 60W 限制在这
│   │   │   ├── Package Power Limit 2 (PL2)
│   │   │   ├── Power Limit 3 (PL3)
│   │   │   ├── Power Limit 4 (PL4)
│   │   │   ├── Turbo Mode
│   │   │   ├── C-States
│   │   │   └── Package C-State Limit
│   │   └── ...
│   ├── Power & Performance        ← 或在这里
│   │   ├── CPU - Power Management Control
│   │   │   ├── Power Limit 1
│   │   │   ├── Power Limit 2
│   │   │   └── ...
│   ├── OverClocking               ← 如果有
│   └── ...
├── Chipset
└── ...
```

### 1.3 解锁隐藏菜单

**关键操作**：找到功耗墙相关项后，检查它们是否被隐藏：

1. 每个菜单项右边有 **Suppress If** / **Access Level** / **条件**
2. 灰色 = 被 Suppress（隐藏条件满足）
3. **右键 → Unsuppress**（或改 Access Level = Default / Full）

**AMIBCP 关键字段**：
- `Suppress If`：设为 `DISABLED` 或删除条件 → 菜单始终显示
- `Grayout If`：设为 `DISABLED` → 菜单不再灰色
- `Access`：改为 `Default` 或 `Full` → 可编辑

### 1.4 改功耗墙值

找到 PL1/PL2 后，改默认值：

| 设置项 | 当前值（推测）| 目标值 | 说明 |
| --- | --- | --- | --- |
| **Power Limit 1 (PL1)** | 60W | **65W** | i5-14400 的 PBP（长期功耗）|
| **Power Limit 2 (PL2)** | 60W 或更低 | **148W** | i5-14400 的 MTP（峰值功耗）|
| **Power Limit Time (Tau)** | 8s 或 28s | **28s** | PL2 持续时间 |
| **Power Limit 3 (PL3)** | 隐藏 | 148W | 可选 |
| **Power Limit 4 (PL4)** | 隐藏 | 253W | 可选（极限）|

> 注：具体值取决于 i5-14400 的实际规格。i5-14400 的：
> - PBP (Processor Base Power) = 65W
> - MTP (Maximum Turbo Power) = 148W
> - 建议 PL1=65W, PL2=148W

### 1.5 保存修改

```
1. File → Save As (文件 → 另存为)
2. 保存为 backups\V1_unlocked_PL120W.bin
3. 记下新的 SHA256
```

## 2. 如果 AMIBCP 找不到功耗墙菜单

可能原因：
1. 菜单被 OEM 深度隐藏（不是简单 suppress，而是 IFR 里直接删了）
2. 功耗墙在 FSP (Firmware Support Package) 里，不是 Setup 变量

**替代方案**：
1. **用 MMTool 5.x** 打开 V1，看 IFR 结构
2. **用 UEFITool NE** 找 FSP 里的功耗墙
3. **用 AMI Setup 编辑器**（更高级）
4. **直接改 NVRAM 变量**（进系统后用 GRUB shell / efivar 改）

## 3. 验证功耗墙是否解锁

### 3.1 刷写后验证

```
1. 用 FPT 写 backups\V1_unlocked_PL120W.bin
2. 重启进 BIOS
3. 看 Advanced → CPU Configuration → CPU Power Management
   - 应该能看到 Power Limit 1/2 菜单
   - 能改值
4. 进 Windows
5. 用 HWiNFO64 看 CPU Package Power
   - 跑 Cinebench R23
   - 看功耗是否超过 60W（应该能到 65W+）
```

### 3.2 验证指标

| 指标 | 解锁前 | 解锁后 |
| --- | --- | --- |
| PL1 | 60W | 65W |
| PL2 | 60W | 148W |
| Cinebench R23 单核 | 低 | 正常 |
| Cinebench R23 多核 | 受限 | 明显提升 |
| CPU 频率 | 降频 | 睿频正常 |

## 4. 风险提示

| 风险 | 等级 | 说明 |
| --- | --- | --- |
| 改错菜单 | 中 | 可能让 BIOS 不稳定 |
| 功耗墙太高 | 中 | 1.5L 机箱散热压不住，可能过热降频 |
| 刷写失败 | 中 | 用 CH341A 救回 |
| 改 PL4 太高 | 高 | 可能烧 VRM（H610 供电弱）|

**建议**：
- 先从 PL1=65W, PL2=148W 开始（i5-14400 官方值）
- **不要**一次拉到 253W（H610 供电可能扛不住）
- 1.5L 机箱散热有限，65W 已经是合理上限

## 5. 扫描脚本

`tools/scan_power_limit.py` — 扫描 V1 里的功耗墙相关字符串和值：

```bash
python tools/scan_power_limit.py backups/H610_full_32mb_V1.bin
```

输出：功耗墙关键词命中 + 60/65/120/125/148W 等功耗值位置。

## 6. 下一步

1. **打开 AMIBCP**（中文版）加载 V1
2. **找功耗墙菜单**（按上面路径）
3. **解锁 + 改值**（PL1=65W, PL2=148W）
4. **保存** 为新 bin
5. **用 FPT 刷写** + 验证

> ⚠️ 刷写前先备份当前 SPI（FPT -d），确保能救回。
