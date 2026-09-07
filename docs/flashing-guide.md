# 刷写流程

## 0. 安全第一

⚠️ **刷 BIOS 有变砖风险，操作前请确认你已经准备好以下条件**：

- [ ] 编程器（CH341A + 烧录夹）已测试可用
- [ ] 备份了原厂 bin，存 2 份以上
- [ ] 备份和待刷的 .bin 都已校验 hash
- [ ] 你有热救方案（编程器能再次读写）
- [ ] 主板断电、电源拔掉

## 1. 完整流程图

```
[拆机找到 BIOS 芯片]
       ↓
[CH341A + 烧录夹接上]
       ↓
[NeoProgrammer 读原厂] → 保存 2 份 bin + .sha256
       ↓
[UEFITool 解析，确认结构]
       ↓
[MMTool 追加 RPL-R microcode] → 保存新 bin
       ↓
[UEFITool 重新打开新 bin，确认其他 region 没动]
       ↓
[ME Analyzer 对比 ME 区域 hash，确认未变]
       ↓
[NeoProgrammer 写新 bin 到芯片]
       ↓
[断开编程器，上电测试 i3-12100] → 确认 12 代仍可亮
       ↓
[关机换 i5-14400，上电] → 确认 14 代点亮
       ↓
[进 BIOS 识别 CPU 型号 + HWiNFO 看 microcode 加载版本]
```

## 2. Step 1：拆机与定位 BIOS 芯片

1. 拆开 Q100-E 底盖（一般 4 颗螺丝）
2. 找到 SPI Flash 芯片（通常在内存槽附近、CPU 座旁边）
3. 芯片典型外观：8-pin SOIC 贴片，丝印 25Q256（Winbond）、MX25L（Macronix）、GD25Q（GigaDevice）等
4. 拍照记录芯片位置（万一刷坏了好找）
5. 红线对 1 脚（芯片小圆点标识 1 脚）
6. 夹子夹紧，确认不会移动

## 3. Step 2：读原厂 BIOS

```
NeoProgrammer 操作：
1. 选择芯片类型（先 Detect，不行手动选）
2. Read（完整读出，约 30 秒 - 1 分钟）
3. 保存为：original_2026xxxx.bin
4. 复制 2 份
5. Get-FileHash -Algorithm SHA256 → 保存 .sha256
6. Blank Check（验证没坏块）
7. 再 Read 一遍 → 对比 hash 一致（验证读取稳定）
```

**重要**：如果两次 Read hash 不一致，说明接触不良，重新夹。

## 4. Step 3：分析原厂 bin

```
UEFITool 操作：
1. 打开 original_2026xxxx.bin
2. 记录：
   - BIOS region 起始 / 结束地址
   - Microcode region 起始 / 结束地址
   - 已有 microcode 列表（CPUID + 版本）
3. 导出 microcode 列表到文本（方便对比）

ME Analyzer 操作：
1. 打开 same .bin
2. 记录：
   - ME 区域起始 / 结束地址
   - ME 大小
   - ME 版本
   - ME 区域 SHA256（要留给 Step 6 对比用）
```

## 5. Step 4：追加 RPL-R microcode

### 5.1 准备 microcode 文件

来源（任选）：

- Intel GitHub：`Intel-Linux-Processor-Microcode-Data-Files/intel-ucode/06-97-05/`
- 直接用现成的 microcode 文件

### 5.2 MMTool 操作

```
1. 打开 working copy（原厂 bin 的副本，不要直接改原厂 bin）
2. 切到 "CPU Patch" tab
3. CPU Patch List 看到所有已有 microcode
4. "Load Patch" → 选 RPL-R microcode 文件
5. 选择插入位置（第一个空位最安全）
6. Apply → 保存为 modified_v1.0.bin
```

**容量不够怎么办**：

- 看 MMTool 报错信息
- 选项 A：删除重复 stepping 的旧 microcode
- 选项 B：把新 microcode 替换掉用不到的 stepping（极不推荐，可能影响兼容性）

### 5.3 改完立即验证

```
UEFITool 打开 modified_v1.0.bin：
1. 确认 ME / FD / GbE region 都还在
2. 确认新 microcode 已加入列表
3. 与 original 对比：只有 microcode region 变化，其他一致

ME Analyzer 打开 modified_v1.0.bin：
1. 对比 ME 区域 SHA256
2. 必须与原厂一致
3. 不一致说明误改了 ME，需要回滚
```

## 6. Step 5：写回芯片

```
NeoProgrammer 操作：
1. Open → modified_v1.0.bin
2. Erase（约 30 秒）
3. Blank Check（确认擦干净）
4. Program（约 1-2 分钟）
5. Verify（自动验证）
6. 完成后断开夹子，恢复主板
```

**重要**：

- 写过程中**绝对不能断电**或动夹子
- 写完先不要装盖子，上电测试通过了再装

## 7. Step 6：上电测试

### 7.1 兼容性测试（必须）

```
1. 保持 i3-12100
2. 上电
3. 预期：屏幕亮 → BIOS 看到 CPU 型号 → 进系统
4. HWiNFO64 看 microcode 加载版本
5. 跑几分钟压力测试
6. 通过 → 进入 7.2
   失败 → 立即用编程器回滚到 original.bin
```

### 7.2 14 代点亮测试

```
1. 关机 → 拆 CPU 散热器 → 换 i5-14400
2. 上电
3. 预期：
   - 风扇转
   - 屏幕亮
   - BIOS 看到 "Intel Core i5-14400"
4. 进 Windows
5. HWiNFO64：
   - CPU 名称正确
   - 核心数：10 (6P+4E)
   - 线程数：16
   - Microcode Update Revision 加载正确
6. 跑 CPU-Z / Cinebench R23 基准测试
7. 通过 → 大功告成 🎉
   失败 → 立即用编程器回滚，分析原因
```

## 8. 失败急救

### 8.1 写完直接不亮

```
1. 断电
2. 检查夹子是否接触不良
3. NeoProgrammer 重新 Read 芯片内容
4. 对比 hash，确认芯片内容是改后 bin
5. 如果 hash 不对 → 重新 Program
6. 如果 hash 对还黑屏 → ME / RC 不兼容，进入 Step 8.2
```

### 8.2 改 microcode 仍不亮

按可能性排查：

```
1. ME 不兼容 → 备份当前状态，考虑升级 ME（高风险）
2. RC 不支持 → 移植其他 H610 板的 RC
3. Boot Guard 阻挡 → 关闭 Boot Guard
4. PMC 固件旧 → 注入新版 PMC
```

具体见 [14th-gen-adaptation.md](14th-gen-adaptation.md) 第 4 节。

## 9. 成功后的工作

- [ ] 把 modified bin 命名为带日期的版本
- [ ] 记录最终 hash 到 bios-mod-history.md
- [ ] 整理备份目录（backups/original/、backups/modified/）
- [ ] 写"实测结果"到 docs/
- [ ] git commit 记录
- [ ] （可选）刷写教程发给同型号玩家
