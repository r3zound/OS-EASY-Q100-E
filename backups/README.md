# BIOS 备份目录

## 目录结构

```
backups/
├── README.md                # 本文件
├── original/                # 原厂未改备份
│   └── (待组织)
├── modified/                # 改过的版本
│   ├── (已存在) bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin
│   └── (已存在) bios_大佬改好的_没解锁PL4之类的选项 跑不满i9会严重降频.bin
└── experiments/             # 失败案例留档
```

## 当前已有备份（从工作目录根复制过来）

| 文件 | 描述 | 是否用于本项目 |
| --- | --- | --- |
| `bios_2改关闭超线程解锁PL4解锁icc修改cstate.bin` | 改 BIOS 第二版：关闭超线程 + 解锁 PL4 + 解锁 ICCmax + 修改 C-State | ❌ 性能优化向，不直接用于 14 代适配（但可参考改法） |
| `bios_大佬改好的_没解锁PL4之类的选项 跑不满i9会严重降频.bin` | 大佬改好的 BIOS，未解锁 PL4 | ❌ 同上 |

## 命名规范

建议文件命名格式：

```
原厂：Q100E_original_YYYYMMDD_HHMM.bin
改版：Q100E_v版本号_说明_YYYYMMDD.bin
```

每个 .bin 配一个同名 .sha256 文件：

```
Q100E_original_20260907_1630.bin
Q100E_original_20260907_1630.sha256
```

## 待办

- [ ] 用 CH341A + NeoProgrammer 备份当前机器原厂 BIOS
- [ ] 把现存的两个 .bin 移到 backups/modified/ 子目录
- [ ] 每个 .bin 生成 .sha256
