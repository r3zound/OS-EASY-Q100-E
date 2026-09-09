# ⚠️ 测试 BIOS 文件目录 ⚠️

> **🚨 重大警告：本目录下所有 .bin 文件都是「未测试的移植实验品」，仅供有硬件救砖经验的用户参考。**
> **🚨 在刷写前，请务必阅读完整个 README，并准备好 SPI 编程器（CH341A + SOIC-8 夹）。**

## 1. 目录内容

| 文件 | 大小 | 来源 | 状态 | 移植版本 |
| --- | --- | --- | --- | --- |
| `Q100E_with_14th_from_ShuttleXH610.bin` | 32 MB | Shuttle XH610 v2.11 提取的 14代 microcode | ⚠️ **未测试** | V1（直接覆盖，截断 24KB）|

V2 版本（元宝 AI 风格"提取+注入"方案）即将添加，请持续关注 git 提交。

## 2. 移植历史

### V1（已完成，**已上传本目录**）

- **目标**：在 `third-party-bios/bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin` 的 90671 microcode 容器（0x1D90D18, 188KB）注入 14代 RPL-S Refresh microcode
- **来源**：Shuttle XH610 v2.11 BIOS（Asia 版）0x1ECB000 处的 B0671 microcode（212KB）
- **方法**：直接覆盖，188KB → 212KB
- **结果**：
  - ✅ 头格式正确（B0671, rev 0x12B, 2024-08-29）
  - ⚠️ **MCExtractor 警告 "Microcode #1 is corrupted"**（数据被截断 24KB）
  - 理论可点亮 i5-14400（CPU 内置 microcode fallback 兜底）

### V2（待做——按 yuanbao 思路的"安全提取+注入"）

- **思路**：用 MCExtractor + MMTOOL 在不截断情况下注入完整 microcode
- **优势**：不破坏原 90671 容器，新 microcode 作为独立 FFS 条目加入
- **状态**：🟡 文档+脚本计划中

## 3. ⚠️ 刷写前的强制清单

**如果你打算把本目录下的 .bin 刷到 Q100-E H610 主板，请先确认：**

```
✅ 已买 CH341A 编程器（30-50 元）+ SOIC-8 烧录夹
✅ 已下载 NeoProgrammer 软件
✅ 已用 i3-12100 备份当前 SPI flash 2 份以上（救命用）
✅ 备份的 .bin 已算 SHA256 + 保存到至少 2 个独立位置
✅ 知道怎么用编程器烧回备份
✅ 已拔掉所有外设（显示器/USB 设备/网线）以减少风险
✅ 主板接上电（不必开机）+ 编程器夹好
✅ 测试电脑有 i3-12100（12代）备份 CPU + i5-14400（14代）目标 CPU
✅ 心里有数：黑了先烧回，**不要连续刷坏两次**（会失信心）
```

## 4. 测试流程（推荐）

```
1. 拔电
2. CH341A 夹到 SPI flash
3. NeoProgrammer 读当前 SPI flash
4. 验证读取正确（计算 SHA256 对比）
5. NeoProgrammer 打开 .bin 测试文件
6. Erase → Blank Check → Program → Verify
7. 装 i5-14400
8. 上电
9. 观察：
   - 黑屏/灯长亮 → 烧回备份
   - 进 BIOS → 完美！可继续测试
10. 进 Windows 用 HWiNFO / CPU-Z 验证：
    - CPU 识别 i5-14400
    - microcode 加载 rev 0x12B
    - 频率正常
```

## 5. 预期风险与缓解

| 风险 | 概率 | 缓解 |
| --- | --- | --- |
| 24KB 截断导致 i5-14400 不亮 | 中 | V2（不截断）方案 / CH341A 烧回备份 |
| 文件写入失败 | 低 | 编程器重试 |
| 容量计算错误 | 低 | 验证步骤 |
| ME 签名影响 | **0** | 没动 ME 区域 |
| 第三方内容破坏 | **0** | 只动 microcode 容器 |

## 6. 重要提醒

- **本目录所有 .bin 都没有经过真实硬件测试**——理论分析成立但**实际刷写**需要你确认效果
- **强烈建议**先做完整备份，再尝试刷写
- **如果失败**，用备份救回（CH341A 编程器）
- **如果多次失败**，停止尝试，联系官方支持（4001-027-580 武汉噢易云）

## 7. 相关文档

- `docs/14th-gen-microcode-port-report-2026-09-08.md` — 完整移植报告
- `docs/cross-vendor-bios-ports-2026-09-08.md` — 跨板移植方案
- `docs/shuttle-xh610-specs.md` — Shuttle XH610 完整规格
- `docs/official-support-contacts.md` — 4001-027-580 话术
- `docs/tools.md` — 工具使用
- `third-party-bios/Shuttle XH610/yuanbao/` — 元宝 AI 的"先兼容预检，再只移植微码"思路

## 8. 引用工具

- `tools/port_microcode_v2.py` — 自动扫描 + 替换（用了 0x8 步进扫描）
- `tools/port_microcode.py` — 第一版（用 EFI FFS GUID）
- `tools/MCExtractor/MCExtractor-r352/MCE.py` — 提取 + 验证
- `tools/full_analyze.sh` / `tools/analyze.bat` — 一键分析

## 9. ⚠️⚠️⚠️ 最终警告 ⚠️⚠️⚠️

> **本目录下所有 .bin 都是「未测试的实验品」**
>
> - 没有任何人实际在 Q100-E 主板上刷过
> - 没有任何人验证过 i5-14400 是否能正常点亮
> - 没有任何人验证过 14代 microcode 是否完整加载
>
> **刷写风险完全由你承担**
>
> **再次强调：刷前必备份！**

最后更新：2026-09-09
