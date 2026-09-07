# 参考资料

## 1. 官方资料

- [噢易云官网 - X86 云终端乾 Q100-E](https://www.os-easy.com/a/359.html) — 官方规格
- [噢易云官网 - 乾 Q100-AI 云终端](https://www.os-easy.com/a/765.html) — 同系列对照
- [湖北省政府采购网 - 台式计算机 Q100-E10](https://wssc.hubeigp.gov.cn/upgrade/products/354305.html) — 早期 H310 批次规格

## 2. 14 代 CPU 适配相关（最相关）

- [Intel 官方 microcode 数据](https://github.com/intel/Intel-Linux-Processor-Microcode-Data-Files) — **必看**：RPL-R microcode 源文件
- [Intel CPU 微码下载](https://downloadcenter.intel.com/) — 官方 CPU 微码下载页
- [Jetway MM10-H610 BIOS](https://jetwaycomputer.com/MM10-H610.html) — **参考价值高**：工业 H610 板的 BIOS changelog 显示 `[A03] Support 14th Gen Raptor Lake Refresh Processor. Update Microcode.`
- [Jetway MI23-H610 BIOS](https://jetwaycomputer.com/MI23-H610.html) — 同上，工业 H610 ITX
- [evezone - i5-14400F Not Detected by BIOS Fix Guide](https://evezone.evetech.co.za/quick-bytes/i5-14400f-not-detected-by-bios-fix-guide/) — 14 代不上点亮的诊断流程

## 3. 13/14 代 Vmin 不稳定问题（微码 0x12x）

- [positioniseverything - Gigabyte 0x12B 微码](https://www.positioniseverything.net?p=663525/) — Gigabyte 确认 0x12B 为 13/14 代最终修复微码
- [techbloat - Intel 0x12F 微码更新](https://www.techbloat.com/raptor-lake-instability-saga-continues-as-intel-releases-0x12f-update-to-fix-vmin-instability.html) — 0x12F 进一步修复
- [positioniseverything - Intel 又一版 RPL 微码](https://www.positioniseverything.net/intel-is-releasing-another-microcode-update-to-protect-crashing-raptor-lake-cpus) — 微码更新对稳定性的影响

> i5-14400 是非 K，Vmin 问题影响小，但建议使用最新 0x12x 微码以防万一。

## 4. 工具链

- [UEFITool 源码](https://github.com/LongSoft/UEFITool) — UEFI/BIOS 镜像解析
- [MMTool（Aptio）](https://www.win-raid.com/t596f39-AMI-Aptio-MMTool.html) — 改 AMI BIOS microcode
- [ME Analyzer](https://github.com/LongSoft/MEAnalyzer) — 解析 Intel ME 区域
- [CH341A 编程器 + NeoProgrammer](https://github.com/LongSoft/CH341A-programmer-software-collection) — SPI Flash 刷写

## 5. 第三方评测与改装实战

1. [什么值得买 - 270元噢易12代准系统迷你主机 乾Q100-E 搭配EScpu踩坑实录](https://post.smzdm.com/p/a70dvggg/) — **重要参考**：改 BIOS 实操 + 解锁前后性能对比
2. [什么值得买 - 350元噢易12代小主机](https://post.smzdm.com/p/anvxv0d2/) — 全方位评测
3. [今日头条 - 咸鱼150台旧电脑](https://www.toutiao.com/article/7675341496362549783) — 机器背景
4. [今日头条 - 350元12代准系统](https://www.toutiao.com/article/7676381846574219811) — 散热与性能评估
5. [什么值得买 - M2+MSATA双盘位](https://post.m.smzdm.com/p/a030p3v0/) — 早期开箱
6. [什么值得买 - 海鲜市场399元](https://post.m.smzdm.com/p/anvd87e7/) — 提到官网有 BIOS 设置手册

## 6. 关键事实出处速查

| 事实 | 出处 |
| --- | --- |
| H610 板可支持 14 代（通过 BIOS 更新） | Jetway MM10-H610 / MI23-H610 |
| i5-14400 = RPL-R, 65W, 10核 6P+4E | 多篇 Intel 规格表 |
| 14 代 RPL-R CPUID 编码 | Intel microcode 包 |
| 0x12B / 0x12F 微码是 13/14 代 Vmin 修复 | Gigabyte / Intel 公告 |
| 主板基于 H610 / H510 定制板 | SMZDM 全方位评测 |
| LGA1700 插座、支持 12/13/14 代 | 官网 + 多篇评测 |
| DDR4 SODIMM ×2、最大 64GB | 官网 |
| M.2 2280 NVMe + mSATA + M.2 2230 E Key | 多篇评测 |
| mPCIE 丝印实际是 mSATA | 270元ES踩坑实录 |
| M.2 失效与 WIFI 转 M.2 方案 | 270元ES踩坑实录 |
| 1.5L 散热上限 45-65W | 350元政企淘汰准系统评测 |
| NeoProgrammer 优于 CH341A编程器.exe | 270元ES踩坑实录 |
| 改 BIOS 前后 CPU-Z 跑分对比 | 270元ES踩坑实录 |

## 7. 待补充

- [ ] 噢易云官网 BIOS 设置手册 PDF（需注册或代理访问）
- [ ] 拆机 / 主板芯片图（用户实测后补）
- [ ] 第一次 UEFITool 解析报告（待用户备份后补）
- [ ] 第一次 microcode 注入实验报告（待操作后补）
