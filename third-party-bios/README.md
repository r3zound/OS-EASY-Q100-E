# 第三方 BIOS 目录

> ⚠️ **本目录下的 BIOS 文件是其他作者自行修改的，**不是本项目（OS-EASY-Q100-E 14 代 CPU 适配）生成的。
> 使用前请先看作者原版提示（见 `_notes/` 子目录），所有风险由使用者自负。

## 目录内容

| 文件 | 描述 | 大小 |
| --- | --- | --- |
| `bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin` | BIOS 作者改版 #2：关超线程 + 解锁 PL4 + 解锁 ICCmax + 修改 C-State | 32 MB |
| `bios_大佬改好的_没解锁PL4之类的选项 跑不满i9会严重降频.bin` | BIOS 作者改版：未解锁 PL4 等电源项 | 32 MB |

## 作者原版提示（保存在 `_notes/`）

1. [01-刷BIOS前请做好备份.md](_notes/01-刷BIOS前请做好备份.md)
2. [02-只建议用编程器刷.md](_notes/02-只建议用编程器刷.md)
3. [03-第三方机器的M.2和MINIPCIE情况.md](_notes/03-第三方机器的M.2和MINIPCIE情况.md)

## 与本项目的关系

- 本项目目标是 **适配 14 代 i5-14400**（RPL-R microcode 注入）
- 这两个第三方 BIOS 是 **12 代 / 13 代标压 U 的电源管理优化版**，方向与本项目不同
- 但本项目可能会参考它们的改法（在追加 14 代 microcode 的同时保留电源优化）
- 二次修改的具体方向见 [docs/bios-mod-history.md](../docs/bios-mod-history.md)

## ⚠️ 重要提示

- 第三方 BIOS 的 hash 未与本项目关联，请自行校验
- 第三方 BIOS 的 ME / Setup / microcode 状态未经本项目独立验证
- 使用第三方 BIOS 之前请确认：原厂 BIOS 已备份
- 第三方 BIOS 在你的机器上**可能**不工作（定制板有差异）
- 出现问题第一时间用编程器回滚原厂

## 命名建议

未来如果你（或别人）又改出新版本，建议按以下规则命名放进本目录：

```
bios_<作者或来源>_<改版号>_<主要修改>_<日期>.bin
```

例如：
```
bios_third-party_v1_PL4-ICC-CState_2026xxxx.bin
```

这样在 GitHub / 仓库里一目了然。
