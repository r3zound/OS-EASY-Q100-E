# 14 代 CPU 适配方案（修订版）

> 适配目标：i5-14400（RPL-R）到 Q100-E 准系统 H610 定制板
> **本方案基于 [bios-analysis-2026-09-07.md](bios-analysis-2026-09-07.md) 的发现做了重大修订**

## 0. 关键发现

这块 H610 定制板的 microcode **不在传统 BIOS region 内的 microcode 文件**，而是在 **ME 区域的 PMCC000 容器**（Huffman 压缩）。

| 传统 H610 板 | Q100-E 这块定制板 |
| --- | --- |
| microcode 在 BIOS region 内的 microcode 文件 (FFS) | microcode 在 ME 区域的 PMCC000 容器 |
| 改 BIOS region 追加 microcode 即可 | 需要改 ME 区域（难度高很多） |
| ME 是相对独立的 blob | ME 16.x 与 microcode 紧耦合 |

**所以原"追加 microcode 到 BIOS region"方案不直接适用**。需要重新评估。

## 1. 推荐操作路径（按风险从低到高）

### 方案 A：直接装 i5-14400 试（最简、零风险）⭐

```
1. 装上 i5-14400
2. 上电
3. 预期（乐观）：
   - 屏幕亮 → BIOS 识别 "Intel Core i5-14400"
   - 进 Windows → HWiNFO64 看 microcode 加载版本
4. 实际：
   - 如果 ME 16.1.25.1917 已含 RPL-R microcode → 直接能用
   - 如果不亮 → 退回方案 B
```

**风险**：基本为零。最多就是"不亮"，回滚换回 i3-12100 即可。

**前提**：你手上有 i5-14400 CPU 和正确散热。

### 方案 B：分析原厂 bin，确认 microcode 情况（中等风险）

```
1. 用 CH341A + NeoProgrammer 备份原厂 32MB bin（保存 2 份以上）
2. 跑 tools/analyze.py <bin>
3. 看输出：
   - ME 版本（如果还是 16.1.25.1917，跟本项目第三方 bin 一致）
   - PMCC000 容器大小
   - 14 代 RPL-R 支持评估
4. 用更高级工具（huffman 解压）看 PMCC000 内具体 microcode 列表
```

**风险**：低（纯分析，不写回）。

**产出**：
- 知道原厂是否含 RPL-R microcode
- 知道需不需要升级 ME

### 方案 C：升级 ME 区域（含 RPL-R microcode）（高风险）⚠️

**这个方案**不在本项目初期目标。涉及：
- 找可信的 ME 16.x 镜像（含 14 代 microcode）
- ME 修补工具（MEBin、UEFITool NE）
- 重新计算 ME 签名 / checksum
- 完整的整片重做

**风险**：高，操作不慎整片变砖（需要编程器热救）。

### 方案 D：整片 BIOS 用 Jetway 等 H610 工业板替换（核弹级）💣

把 Jetway MM10-H610（已有 `[A03] Support 14th Gen Raptor Lake Refresh Processor. Update Microcode.`）的 BIOS 整体移植过来。

**风险**：极高——EC / GbE / 网卡 / 串口等周边可能不匹配，刷完必砖。

**不推荐**。仅在方案 A/B/C 都失败、且你有热救能力时考虑。

## 2. 实操参考

| 步骤 | 详细文档 |
| --- | --- |
| 备份原厂 BIOS | [flashing-guide.md](flashing-guide.md) |
| 跑分析脚本 | [tools.md](tools.md) |
| 刷写流程 | [flashing-guide.md](flashing-guide.md) |
| 改电源管理项 | AMIBCP（不是本项目的核心目标） |

## 3. 关键 hash 参考

```
bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin
SHA256: 50bf84a961e8cc861f6375e231a7e9723c8396c706d86a81f33befc5085b5b41

bios_大佬改好的_没解锁PL4之类的选项 跑不满i9会严重降频.bin
SHA256: bf0463f2378c53151aec19a8445c76098b46729c6cb2da7b19db4eda95949a45
```

两份第三方 bin 共享相同的 ME 16.1.25.1917，差异在 BIOS region 的电源管理项。

## 4. 完整决策树

```
开始
  │
  ├─ 你手上有 i5-14400？
  │   ├─ 是 → 方案 A：直接装上试
  │   │         │
  │   │         ├─ 亮了？ → 恭喜收工 🎉
  │   │         └─ 不亮？ → 方案 B/C
  │   │
  │   └─ 否 → 方案 B：先分析原厂 bin
  │             │
  │             └─ → 方案 C（如需要）：升级 ME
  │
  └─ 你有 Jetway 等 H610 参考 BIOS？
      └─ 是 → 方案 D（高风险）
```

## 5. 给同型号玩家的建议

- **别急着改 BIOS**——先装上 14 代 CPU 试（方案 A）
- **一定要先备份原厂 BIOS**——任何改之前
- **不要直接整片刷其他板的 BIOS**——风险极高

## 6. 下一步（项目计划）

- [ ] 等待 i5-14400 到货
- [ ] 执行方案 A
- [ ] 备份原厂 bin
- [ ] 跑 `tools/analyze.py` 分析原厂 bin
- [ ] 如果需要，写 Huffman 解压 PMCC000 的脚本
- [ ] 验证 12 代兼容性（i3-12100 仍能进系统）

## 7. 进阶参考资料

- Intel 官方 microcode 数据：https://github.com/intel/Intel-Linux-Processor-Microcode-Data-Files
- H610 + 14 代 BIOS 改写教程：见 [references.md](references.md)
- ME 修补工具：MEBin、UEFITool NE（GitHub 搜）
