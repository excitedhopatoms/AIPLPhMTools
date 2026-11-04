# AIPLPhMTools 函数库重组方案（待确认，不执行）

> 目标：把当前 20+ 个平铺模块、100+ 个构造函数，整理成“核心 / 器件 / 装配 / 测试结构 / 电学 / 平台”六层；
> 统一重复的 ring / racetrack / test-structure 代码；保持公共 API 和用户已有版图几何不变。
> **状态：2026-11-03 已执行。** 实际目录：`Core/`、`Devices/`、`Assemblies/`、
> `TestStructures/`、`Electrical/`、`Platforms/SOI/`；旧 `GeneralTools/` 与
> `SOITools/` 保留 thin shim；顶层 `import AIPLPhMTools as ap` 不变。
> 10 个真实交叉已全部修复；剩余曲率默认值按用户要求留到实际版图任务调整。

## 1. 现状盘点

| 类别（现状） | 模块（行数 / 公共函数数） | 问题 |
|---|---|---|
| 核心与工具 | `BasicDefine.py` 1553/21、`LayerStack.py` 248、`SnapMerge.py` 263/4、`EulerConnection.py` 705/1 | `BasicDefine` 同时放层号、截面、图元、路由、标签、层操作；职责过重 |
| 环形器件 | `Ring.py` 1150/12 | `RingPulleyT1/T2/1DC/1HS/1HSn/2/2ES/3/4` 大量重复 |
| 跑道器件 | `RaceTrack.py` 641/5 | 与 Ring 的耦合/加热代码重复 |
| 耦合器/MZI | `CouplerMZI.py` 430/5 | `PulleyCoupler2X2`、`SagnacRing` 与反馈结构有重叠 |
| 耦合腔 | `CoupledCavity.py` 289/3、`Boomerang.py` 611/5、`GongCavity.py` 351/1、`memyshev.py` 152/1 | 腔体类型分散，boomerang 臂与测试结构共用代码 |
| 光栅 | `DBR.py` 1048/8、`DBR_inv.py` 597/5 | 普通/采样/倒置光栅分散；有重名 `EDBRStrRep` |
| 反馈/外腔 | `FeedbackCavity.py` 695/4、`ExtCav.py` 1099/7、`WangCavity.py` 672/2 | 外腔装配和器件几何混在一起；连接逻辑重复 |
| 多环/多跑道 | `MultiRing.py` 647/6、`MultiRaceTrack.py` 248/2 | 双环/三环的 Drop 串联与 IO 路由重复 |
| 隔离器 | `Isolator.py` 363/3 | 依赖 `route_off_grid`；本次已修连接，但函数仍偏长 |
| 测试结构 | `TCRing.py` 1474/15、`TCRaceTrack.py` 549/7、`TCCoupledCavity.py` 1117/6、`Coupon.py` 285/2、`TestRow.py` 328/3 | 测试结构混在器件层；`TC*` 包装重复；7 个真实交叉集中在这里 |
| 电学/热 | `Heater.py` 574/5、`ELE.py` 266/2 | 加热器、过孔、焊盘分界不清 |
| 平台库 | `SOITools/`（Assembly/Audit/Electrical/FabBasic/Facet/Geometry/Ring/Routing/Spiral） | 自己又有一套 Ring/Routing/Geometry，和 GeneralTools 概念重复 |

本次审计还发现：
- 7 个真实交叉集中在 `TCRaceTrack*` / `TCCoupledCavity*` / `Boomerang*` / `ExtCavDouRaceTrack`；
- `route_off_grid` 曾被 5 个函数使用，说明**连接/路由 helper 没有统一入口**；
- `GfCBendEuler` 的 `with_arc_floorplan` 语义、`route_single_sbend` 无半径保证，都是“没有统一 helper”造成的。

## 2. 目标分层（推荐方案 A：移动文件、保留文件名）

```text
AIPLPhMTools/
├── Core/                      # 与具体器件无关
│   ├── BasicDefine.py         # 层号、截面、直/弯/锥、标签、层操作
│   ├── LayerStack.py
│   ├── Routing.py             # route_off_grid / 双圆弧 S / smooth join / 端点断言
│   ├── Geometry.py            # SnapMerge、waveguide_region、overlap/curvature 工具
│   └── EulerConnection.py
├── Devices/                   # 单器件/单元
│   ├── Ring.py                # RingPulley 基类 + 薄包装
│   ├── RaceTrack.py
│   ├── CouplerMZI.py
│   ├── CoupledCavity.py
│   ├── Boomerang.py
│   ├── GongCavity.py
│   ├── Memyshev.py
│   ├── DBR.py                 # 普通/采样/倒置光栅统一入口
│   └── FeedbackCavity.py      # FeedbackRing + OptMMI/PDC Sagnac
├── Assemblies/                # 多器件组合
│   ├── MultiRing.py           # DoubleRingPulley / ADRAPRADR / TriRingPulley
│   ├── MultiRaceTrack.py
│   ├── ExternalCavity.py      # ExtCavDouRing/TriRing/.../Wang
│   ├── Isolator.py
│   └── FeedbackAssemblies.py  # 需要时把 FeedbackRing 组合放这里
├── TestStructures/            # 只做测试/表征
│   ├── Coupon.py              # Coupon 框架 + TCRingCoupon
│   ├── Rings.py               # TCRing* / TCFingerRing1 / TCRingDCouple
│   ├── RaceTracks.py          # TCRaceTrack* / TCTaperRaceTrack*
│   ├── CoupledCavity.py       # TCCouple* / boomerang test
│   └── Rows.py                # RingCouponRow / DispersionRingRow
├── Electrical/
│   ├── Heaters.py             # DifferentHeater / SnakeHeater / configs
│   └── Pads.py                # ViaArray / GSGELE / OpenPad / landing pads
├── Platforms/
│   └── SOI/                   # 现 SOITools，作为独立平台命名空间
│       ├── Routing.py
│       ├── Geometry.py
│       ├── Ring.py
│       ├── Electrical.py
│       ├── Facet.py
│       ├── Spiral.py
│       ├── Audit.py
│       └── Assembly.py
├── _compat.py                 # 旧名字 → 新实现的 thin wrapper
└── __init__.py                # 只做 re-export + COMPONENTS 注册表
```

**保留旧 import 的兼容层**：
- `AIPLPhMTools.GeneralTools.Ring` → shim 到 `AIPLPhMTools.Devices.Ring`
- `AIPLPhMTools.GeneralTools.ExtCav` → shim 到 `AIPLPhMTools.Assemblies.ExternalCavity`
- `from AIPLPhMTools import RingPulley` 不变
- 所有旧函数名在 `_compat.py` 里保留 1~2 个版本周期；新代码只从新路径导入。

> 不推荐直接改模块名为小写（如 `ring.py`）：会破坏现有项目、文档和历史脚本的 import；先按子包移动，后续再决定是否重命名。

## 3. 归类映射（函数级）

| 新位置 | 包含的现有函数 |
|---|---|
| `Core/BasicDefine.py` | `LAYER`、`make_cs`、`GfCStraight`、`GfCBendEuler`、`Crossing_taper`、`OffsetRamp`、`cir2end`、`TaperRsoa`、`remove_layer`、`waveguide_region`、`check_waveguide_overlap`、`add_labels_to_ports` |
| `Core/Routing.py` | `route_off_grid`、`route_bundle_off_grid`、内部 `_two_arc_s`/`_route_arc_points`、`_smooth_join` |
| `Core/Geometry.py` | `SnapMerge` 的 4 个函数、`connect_ports_euler`（或留 `Core/EulerConnection.py`） |
| `Devices/Ring.py` | `RingPulley` 基类；`RingPulleyT1/T2/1DC/1HS/1HSn/2/2ES/3/4` 作为薄包装 |
| `Devices/RaceTrack.py` | `RaceTrackP/S/StrHC`、`TaperRaceTrackPulley` |
| `Devices/CouplerMZI.py` | `PulleyCoupler2X2`、`DMZI`、`PMZI`、`PMZIHSn`、`SagnacRing` |
| `Devices/CoupledCavity.py` | `CoupledRingFilter`、`CROW`、`SCISSOR` |
| `Devices/Boomerang.py` | `Boomerang`、`RingBoomerang`、`RingDouBoomerang`、`RingTriBoomerang`、`boomerang_heater` |
| `Devices/GongCavity.py` / `Memyshev.py` | `GongCavity` / `DoubleRingMemyshev` |
| `Devices/DBR.py` | `DBR`、`DBRFromCsv*`、`SGDBRFromCsvOffset`、`VSGDBRFromCsvOffset`、`EstrDBRFromCsvOffset`、`EDBRStrRep`、`EDBRFromCsv`、`EDBRStrRep_InvertTone*`、`Complete_Inverted_Device` |
| `Devices/FeedbackCavity.py` | `FeedbackRing`、`OptFeedbackRing`、`OptMMISagnacLoop`、`OptPDCSagnacLoop` |
| `Assemblies/MultiRing.py` | `DoubleRingPulley`、`DoubleRingPulley2HSn`、`DoubleRingPulley2_1HSn`、`ADRAPRADR`、`TriRingPulley`、`CoupleRingDRT1` |
| `Assemblies/MultiRaceTrack.py` | `DoubleRaceTrack`、`CoupleDouRaceTrack` |
| `Assemblies/ExternalCavity.py` | `ExtCavDouRing`、`ExtCavDouRing2/3`、`ExtCavTriRing`、`ExtCavTriRing2/2_2`、`ExtCavDouRaceTrack`、`ExtCavWang`、`WangCavity` |
| `Assemblies/Isolator.py` | `SingleRingIsolator0/1`、`RingAndIsolator0` |
| `TestStructures/Coupon.py` | `Coupon`、`TCRingCoupon` |
| `TestStructures/Rings.py` | `TCRing`、`TCRing1AD`、`TCRing1_3`、`TCRing1DC`、`TCRing2/2_2/2_3`、`TCRing3`、`TCRing4`、`TCRingDCouple`、`TCFingerRing1`、`TCRingT1/T2` |
| `TestStructures/RaceTracks.py` | `TCRaceTrackP/S/S2/S3/S3h`、`TCTaperRaceTrackP/S` |
| `TestStructures/CoupledCavity.py` | `TCRingBoomerangT1`、`TCRingDouBoomerangT1`、`TCRingTriBoomerangT1`、`TCCoupleDouRingT1`、`TCCoupleDouRaceTrackT1/T2` |
| `TestStructures/Rows.py` | `ring_coupon`、`RingCouponRow`、`DispersionRingRow` |
| `Electrical/Heaters.py` | `DifferentHeater`、`SnakeHeater`、`HeaterConfigClass`、`localheater` |
| `Electrical/Pads.py` | `ViaArray*`、`GSGELE`、`OpenPad` |
| `Platforms/SOI/*` | 现 `SOITools` 全部；`RingPulley`/`RaceTrackPulley` 与 GeneralTools 版本保持独立命名空间，避免同名覆盖 |

## 4. 去重与统一接口（重组时一并做）

1. **Ring 家族统一**：`RingPulley` 作为唯一参数化实现，`T1/T2/1DC/1HS/1HSn/2/2ES/3/4` 只保留参数预设的 thin wrapper；统一 `IsAD`、`Sides`、`HeaterConfig`、`DirectionHeater`。
2. **测试结构统一**：所有 `TC*` 使用同一套 `add_io_taper` / `add_monitor_arm` / `add_coupon` / `route_to_ring` helper；7 个真实交叉在迁移时逐个修，不再各写一套路由。
3. **外腔统一**：`ExtCav*`、`WangCavity`、`FeedbackCavity` 共用一个 `place_pmzi_and_ring` + `connect_ring_inputs` 装配函数；PMZI 两臂到两个 Ring Input 的连接只写一次。
4. **DBR 统一**：普通/采样/倒置光栅共用一个 `GratingBase`；`EDBRStrRep` 只保留一个公共入口。
5. **路由统一**：所有连接走 `Core/Routing.py` 的 `route_off_grid` / `two_arc_s` / `smooth_join`；禁止再直接调用 `route_single_sbend`。
6. **曲率策略统一**：器件函数暴露 `RadiusMin`（默认 50/52），实际绘图按 `RadiusMin` 校验；`GfCBendEuler` 的 `with_arc_floorplan` 语义在 Core 层统一说明。

## 5. 迁移步骤（每步都可回退）

| 阶段 | 内容 | 验收 |
|---|---|---|
| 0 | 冻结当前 96 个组件的 `bbox/ports/层网数/几何哈希` 基线 | 基线文件入库 |
| 1 | 建新子包 + `_compat.py` shim，不移动实现 | 旧 import 全部可用；selftest 全绿 |
| 2 | 移动 `Core/*`，更新 import；`GeneralTools` 保留 shim | 96 组件 build 成功；bbox/ports 不变 |
| 3 | 移动 `Devices/*`，合并 Ring 家族；保留旧名字 wrapper | 同上；对比几何哈希 |
| 4 | 移动 `Assemblies/*` + `TestStructures/*`；引入统一路由/coupon helper；逐个修 7 个交叉 | 交叉 0；DRC/渲染复核 |
| 5 | 移动 `Electrical/*`、`Platforms/SOI/*`；更新 docs 分类和 import | 文档 107 页、0 缺失；selftest 全绿 |
| 6 | 删除 `GeneralTools` 物理目录（保留 shim 一个版本） | 用户确认后再删 |

**每阶段必须跑**：`selftest/run_all` + 96 组件逐层 overlap/端口表 + 文档构建 + 关键局部渲染。
**几何不变的证明**：逐组件 bbox/ports/层网数/几何哈希对比；任何变化必须解释（本方案只允许 7 个交叉修复和默认值调整）。

## 6. 需要你确认的决策

1. **目录命名**：用 `Core/Devices/Assemblies/TestStructures/Electrical/Platforms`（推荐，保留原文件名）还是直接改成小写模块名？
2. **兼容层**：`GeneralTools` 是否保留一个版本周期（推荐）还是直接删除？
3. **SOITools**：保持独立 `Platforms/SOI` 命名空间（推荐），还是合并进 Devices 的同名接口？
4. **旧函数**：`RingPulleyT1/T2/...`、`TCRing*` 旧名字是否保留 thin wrapper（推荐），还是只保留新基类？
5. **7 个剩余交叉**：在重组阶段 4 一起修（推荐），还是先单独修完再重组？
6. **P1 默认曲率**：`GfCBendEuler`/FeedbackRing 的默认半径现在先不动、做实际版图时按 `RadiusMin` 调整，是否认可？

> 你确认以上方案后，我再按阶段 0→6 开始移动文件；在阶段 4 会把剩余 7 个交叉作为“统一路由 helper”的第一批验收用例。
