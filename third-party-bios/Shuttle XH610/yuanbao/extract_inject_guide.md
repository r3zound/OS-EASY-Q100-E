# 从 XH610 提取 14 代微码 → 注入 JHS65F：操作指南

> ⚠️ **高风险操作预警**：跨主板移植微码属于硬改，存在变砖风险。**务必先备份原厂 BIOS、准备 SPI 编程器救砖**。以下方案仅供具备硬件刷机经验的用户参考。

---

## 一、核心原理

| 项目 | 说明 |
|------|------|
| **目标** | 让噢易云 JHS65F（H610）在保持原有 EC/ME/Setup 不变的前提下，获得 i5-14400（14代）的微码支持 |
| **方法** | 从 Shuttle XH610 BIOS 中提取 14 代微码块 → 用 MMTOOL 注入到 JHS65F 的 BIOS 镜像中 |
| **关键前提** | 两份 BIOS 均为 AMI Aptio UEFI、同芯片组（H610）、同平台（Alder Lake + Raptor Lake），微码卷结构兼容 |

**为什么只移植微码（而非整包刷写）？**
- XH610 与 JHS65F 是**不同厂商**主板：EC、Super I/O（ITE IT8613）、GPIO、板载设备映射完全不同
- 整包刷写 → 外设失灵 / 无法点亮 / 变砖
- **仅补充微码** → 最小改动，保留 JHS65F 原有硬件初始化链，只新增 CPU 识别能力

---

## 二、准备工作

### 1. 所需文件
- `XH610000.211.bin` — Shuttle XH610 源 BIOS（提取微码用）
- `JHS65F_original.bin` — 噢易云 JHS65F **原厂** BIOS（**务必先备份**）
- `MCExtractor`（https://github.com/platomav/MCExtractor）
- `MMTOOL`（AMI 官方，对应 Aptio V/4）

### 2. 所需硬件
- **SPI 编程器 + SOIC-8 夹**（如 CH341A）— **救砖必备**
- 螺丝刀（拆机箱、取下主板电池）

### 3. 环境
- Windows 10/11（MMTOOL 为 Windows 程序）
- Python 3（运行 MCExtractor）

---

## 三、操作步骤

### 步骤 1：校验两份 BIOS 的微码现状

```bash
# 扫描 XH610（应看到大量 0x12B、0x11D 等 14 代微码）
python MCExtractor.py XH610000.211.bin

# 扫描 JHS65F 原厂（确认是否真的缺 14 代微码 0x00B067）
python MCExtractor.py JHS65F_original.bin
```

**判定标准：**
- XH610 输出含 `CPUID 000B067x`（14代）→ ✅ 可作为提取源
- JHS65F **不含** `000B067x` → 需要注入（继续下一步）
- JHS65F **已含** `000B067x` → **无需操作**，直接换 CPU 即可

---

### 步骤 2：从 XH610 提取 14 代微码

使用 MCExtractor 提取为独立 `.bin` 文件：

```bash
# 提取全部微码（含 14 代）
python MCExtractor.py XH610000.211.bin -o extracted_microcodes
```

从输出目录中**筛选 14 代微码**（CPUID 以 `000B067` 开头的文件），例如：
- `cpu000B0670_ver0000000E_date20220220.bin`
- `cpu000B0671_ver0000012B_date20240829.bin` ← **重点，0x12B 稳定版**
- `cpu000B0672_ver00000037_date20240529.bin`

> 💡 **推荐只提取 `000B0671`（rev 0x12B）这一个**，它是 14 代最稳定的修复版本，减少兼容风险。

---

### 步骤 3：用 MMTOOL 注入到 JHS65F

1. 打开 MMTOOL → `File` → `Open` → 选择 `JHS65F_original.bin`
2. 在左侧树中找到 **`CPU Microcode`** 卷（通常位于某个 FV 下）
3. 点击菜单 `Add` / `Insert` → 选择步骤 2 提取的 14 代微码 `.bin`
4. MMTOOL 会自动校验 CPUID / 版本号，**若提示冲突（已有同名微码）则先删除旧条目**
5. `File` → `Save` → 另存为 `JHS65F_with_14gen.bin`

**校验要点：**
- 注入后重新用 MCExtractor 扫描 `JHS65F_with_14gen.bin`，确认 `000B0671` 出现
- 文件大小、校验和无异常

---

### 步骤 4：刷写（先备份！）

#### 方案 A：软件刷写（推荐，前提是能点亮）
1. 用 i5-12400 点亮进 BIOS → 导出当前 BIOS 作为**最终备份**
2. 使用内置工具（AMI Flash / EZ Flash）刷入 `JHS65F_with_14gen.bin`
3. 刷完 **Load Optimized Defaults** → 保存退出

#### 方案 B：硬件编程器（救砖 / 无法点亮时）
1. 拆下主板 BIOS 芯片（SOIC-8）
2. CH341A + 夹子 → 读取原片 → 保存为 `.bin`（**第二次备份**）
3. 擦除 → 写入 `JHS65F_with_14gen.bin` → 校验
4. 焊回 → 上机测试

---

### 步骤 5：验证

1. 装回 i5-12400 → 点亮 → 进系统 → CPU-Z 看"微码版本"正常 → ✅ 原 CPU 仍可用
2. 关机 → 换 i5-14400 → 点亮 → CPU-Z 显示 i5-14400、微码加载成功 → 🎉 **成功**

---

## 四、风险与注意事项

| 风险 | 说明 | 应对 |
|------|------|------|
| **微码卷结构不兼容** | JHS65F 微码卷可能被压缩/加密，MMTOOL 无法直接插入 | 先尝试；不行则需在压缩卷内替换（更复杂）|
| **签名冲突** | 同一 CPUID 已有旧微码 → 需先删旧条目 | MMTOOL 内手动删除 |
| **刷砖** | 任何误操作可能导致无法点亮 | **必须备份 + 准备编程器** |
| **点亮但降频** | H610 供电限制 65W，14400 可能跑不满 | 这是硬件天花板，微码解决不了 |
| **关超线程影响** | 若沿用"改版 BIOS"的关 HT 设置，多线程性能下降 | 按需调整 Setup |

---

## 五、决策树（简化版）

```
1. JHS65F 原厂 BIOS 已含 000B067x？
   ├─ 是 → 直接换 i5-14400，结束 ✅
   └─ 否 ↓
2. 用 MMTOOL 注入 000B0671(0x12B) → 校验
3. 备份原厂 → 刷写 → 点亮验证
4. 成功 → 换 14400 🎉
   失败 → 编程器恢复备份 → 联系噢易云官方
```

---

## 六、一键验证脚本（Windows）

将以下脚本保存为 `check_microcode.bat`，放在 BIOS 文件同目录：

```batch
@echo off
REM 一键扫描并显示 14 代微码（000B067x）是否存在
echo 正在扫描 14 代微码（CPUID 000B067x）...
python MCExtractor.py %1 2>&1 | findstr /C:"000B067"
echo.
echo 若上方出现 "000B067" 开头的行 → 已支持 14 代 ✅
echo 若无任何输出 → 缺失 14 代微码 ❌
pause
```

用法：`check_microcode.bat JHS65F_original.bin`

---

> 📌 **最后提醒**：本方案是"最坏情况下的兜底手段"。**优先尝试联系噢易云官方（4001-027-580）索要正式 14 代 BIOS**——官方支持永远比硬改安全可靠。
