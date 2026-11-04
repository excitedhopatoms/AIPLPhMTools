# AIPLPhMTools 版图规则审计（2026-11-03）

> 范围：`AIPLPhMTools` 全部公共器件构造函数（`ap.list_components()`，96 个可默认构建的器件；6 个 CSV 驱动器件未纳入）。
> 判据：`202610_SOI_icrd#2/docs/DESIGN_MANUAL.md` §5.4 的通用规则（切向连续、波导交叉、端点重合、实际曲率、taper、IO 方向、悬空弯）。
> 方法：逐个默认参数构建；逐层 WG 重叠（polygon 面积与逐对求交）；递归收集 `info["min_bend_radius"]`；顶层端口方向；同位置端口朝向/宽度；顶层 bend 悬空端；源码静态扫描 `radius < 50`、`route_single_sbend`、`allow_width_mismatch`。
> 说明：这是**只读审计**，没有修改库代码。数值限值按 SiN 的 50/52 µm 从严判断；Si 平台可另按 10/11 µm 复核。

## 0. 结论摘要

- 默认构建失败：**0 / 96**。
- 存在**真实同层 WG 交叉/重叠**（>0.05 µm²，排除明显有意的光栅/实心结构）：修复前 **10 个**；**全部已修复**。
- 存在**实际曲率半径 <50 µm**：**4 个**（`GfCBendEuler`、`FeedbackRing`、`OptFeedbackRing`、`TCRaceTrackP`）；按用户要求，默认值暂不动，做实际版图时按最小曲率半径调整。
- 连接路由静默缺失：`route_off_grid` 及 5 个调用函数，**已修复**。
- IO 端口方向需要复核：**13 个**（多为组件局部竖直/斜向端口，放置到最终版图时可旋转；其中若干是真正的 Input/Through 非 0/180）。
- 默认构建无自动告警：**约 44 个**，仍需渲染复核（自动审计看不到无 `min_bend_radius` 的路径）。

### 2026-11-03 已修复

| 项 | 修复内容 | 验证 |
|---|---|---|
| `BasicDefine.route_off_grid`（已修复） | 去掉不存在的 `gf.routing.get_route`；平行端口用直段/双圆弧 S（R 由端点反算），其余用 `route_single` 并校验 bbox；失败直接抛错，不再静默返回 `None` | 5 个调用函数均能构建 |
| `SingleRingIsolator0`（已修复） | 删除 through 的重复回路；drop 改为 `Drop→bend_dr1→bend_dr2→taper→tout`；删除 add/drop/through 的同位置重复路由 | 0 WG overlap、0 悬空 |
| `SingleRingIsolator1`（已修复） | 同上；monitor 长度 `length_monicouple` 默认 100→**250**，给 90° 监控臂留出转弯空间 | 0 WG overlap；monitor 端由 `route_off_grid` bbox 校验（扁平化后无端口，自动悬空检查会误报 1 个） |
| `RingAndIsolator0`（已修复） | 同上去重/修正 drop 串接 | 0 WG overlap、0 悬空 |
| `TCRing1AD` / `TCRing1DC` | 修好 `route_off_grid` 后连接恢复 | 0 WG overlap、最小 R >100 |
| `TCRing4`（已修复） | 输入不再用“只按 x 差画水平直段”的旧写法（ring Input 有 y 偏移，直段横穿总线）；改为从 `tinring.o2` 路由到 taper 窄端 | 3.6 µm² → **0** |
| `TCRingDCouple`（已修复） | `r_euler_min` 默认 200→**80**（≥52） | 5.1 µm² → **0** |
| `TCFingerRing1`（已修复） | `r_side` 默认 120→**60**（≥52） | 11.8 µm² → **0** |
| 网页 2D 图 | 每个端口画一个朝外箭头 + `名字 角度°` 标签，直接看 IO 方向 | 107 页重新生成 |
| 3D 视图 | 增加 `panX/panY`；左键旋转、**右键/Shift 拖动平移**、滚轮缩放、双击复位（component3d.js + heaters3d.js） | 页面提示同步更新 |

**交叉修复记录**：
- `TCRaceTrackS2`：through 端从 `str_s2n.o1` 改为 `o2` 起弯，修正拼接方向。
- `TCRingDouBoomerangT1` / `TCRingTriBoomerangT1`：源函数 `Boomerang.RingDouBoomerang` 在 `connect` 后又 `move`，拉断 Lo2–Ro1 接缝；删除该 move，接缝恢复。
- `TCTaperRaceTrackS`：`r_bend` 默认 750→**200**（≥52），交叉消失。
- `TCCoupleDouRaceTrackT1/T2`：重写为直接调用 `CoupleDouRaceTrack` 并把四个端口接外部 taper；删除错误的 drop→o2 和回程 route。
- `ExtCavDouRaceTrack`：PMZI 上方端口改为 `route_off_grid` 绕行到 ring o2，不再走左侧 180° 弯。
- `TCRing4` / `TCRingDCouple` / `TCFingerRing1` 见上表。


## 1. P0 — 必须修（几何短路/交叉/断连）

| # | 函数 | 现象/证据 | 建议修法 |
|---|---|---|---|
| 1 | `BasicDefine.route_off_grid`（已修复） | 内部调用当前版本不存在的 `gf.routing.get_route`，异常被吞掉后返回 `None`；所有调用处实际**没有生成路由** | 改用 `gf.routing.route_single`（或 `_two_arc_s` 类半径受控 S），并在返回前断言路由端口与两端重合；失败必须报错，不得静默 |
| 2 | `SingleRingIsolator0`（已修复） | 依赖 `route_off_grid`；顶层 bend 端悬空 @ (763.679,-115.676) | 修 #1 后重跑；把每条 route 的端点断言加回 |
| 3 | `SingleRingIsolator1`（已修复） | 依赖 `route_off_grid`；悬空 bend @ (763.679,-115.676)、(650,-102) | 同上 |
| 4 | `RingAndIsolator0`（已修复） | 依赖 `route_off_grid`；悬空 bend @ (763.679,-115.676) | 同上 |
| 5 | `TCRing1AD`（已修复） | 使用 `route_off_grid` + `route_bundle_off_grid`，默认构建无重叠但连接路由缺失 | 修 #1 后检查每条总线/端口 |
| 6 | `TCRing1DC`（已修复） | 同上 | 同上 |
| 7 | `TCRaceTrackS2`（已修复） | WG 重叠 **128.0 µm²**；S 弯与直波导交叉 @ (11905.6..11908.4,-1796.6..-1788.2)；另有 x=10570.99 的 1 nm 边条 | through 端从 `str_s2n.o1` 改为 `o2` 起弯（原代码折回直段上）；已修 |
| 8 | `TCRingTriBoomerangT1`（已修复） | WG 重叠 **298.2 µm²**；长条重叠 @ (1098..1486,-1326/-1004) | 源函数 `RingDouBoomerang` 在 `connect` 后又 `move`，删除该 move，接缝恢复；已修 |
| 9 | `TCRingDouBoomerangT1`（已修复） | WG 重叠 **141.0 µm²**；长条重叠 @ (968..1117.5,-834.75..-834.26) | 同上 |
| 10 | `TCTaperRaceTrackS`（已修复） | WG 重叠 **52.7 µm²**；宽 taper 横穿总线 @ (5820.6..5839.6,-1624.1..-1620.2) | `r_bend` 默认 750→200（≥52）；已修 |
| 11 | `TCCoupleDouRaceTrackT2`（已修复） | WG 重叠 **18.2 µm²**；交叉 @ (1182,-2368)、(1423,-2368)、(1420,-2100) | 重写为直接调用 `CoupleDouRaceTrack` 并把四个端口接外部 taper；已修 |
| 12 | `TCCoupleDouRaceTrackT1`（已修复） | WG 重叠 **9.2 µm²**；交叉 @ (825,-91)、(1056,-82)、(1063,-171) | 同上 |
| 13 | `TCFingerRing1`（已修复） | WG 重叠 **11.8 µm²**；大圆弧横穿总线 @ (530..663,-483)、(506,0)、(267,0) | `r_side` 默认 120→60；已修 |
| 14 | `TCRingDCouple`（已修复） | WG 重叠 **5.1 µm²**；X 形交叉 @ (613.96..616.18,-561.2..-556.5) | `r_euler_min` 默认 200→80；已修 |
| 15 | `TCRing4`（已修复） | WG 重叠 **3.6 µm²**；竖直直波导横穿水平总线 @ (781.8..783.7,-0.95..0.95) | 输入改为从 `tinring.o2` 路由到 taper 窄端；已修 |
| 16 | `ExtCavDouRaceTrack`（已修复） | WG 重叠 **2.4 µm²**；两处交叉 @ (697,-86)、(706,-230) | PMZI 上方端口改用 `route_off_grid` 绕行到 ring o2；已修 |

> 渲染证据：[TCRaceTrackS2](audit/crop_TCRaceTrackS2.png)、[ExtCavDouRaceTrack](audit/crop_ExtCavDouRaceTrack.png)、[TCRing4](audit/crop_TCRing4.png)、[TCTaperRaceTrackS](audit/crop2_TCTaperRaceTrackS.png)、[TCFingerRing1](audit/crop2_TCFingerRing1.png)、[TCRingDCouple](audit/crop3_TCRingDCouple.png)、[TCCoupleDouRaceTrackT1](audit/crop3_TCCoupleDouRaceTrackT1.png)、[TCRingDouBoomerangT1](audit/crop_TCRingDouBoomerangT1.png)。原始逐器件数据见 [audit/aipl_audit.md](audit/aipl_audit.md) 与 [audit/aipl_audit.json](audit/aipl_audit.json)（修复前基线；修复项的当前状态以本文件的“已修复”表和直接构建复核为准）。

## 2. P1 — 曲率/连接/代码缺陷

| # | 函数 | 现象/证据 | 建议修法 |
|---|---|---|---|
| 1 | `GfCBendEuler` | 默认 `radius=None` + `with_arc_floorplan=True`，默认构建实际 `min_bend_radius=7.06 µm` | 默认半径改为 ≥52 µm，或 `radius=None` 时直接报错；明确 `with_arc_floorplan=False` 才是“最小半径”语义 |
| 2 | `FeedbackRing` | `_add_io_port` 的 `GfCBendEuler(radius=52, with_arc_floorplan=True)` 实际最小半径 **34.69/36.72 µm** | 该处传 `with_arc_floorplan=False`（或把名义半径按 1/0.71 放大）；修后重跑端口位置 |
| 3 | `OptFeedbackRing` | 同上，实际 **34.69 µm** | 同上 |
| 4 | `TCRaceTrackP` | 默认 `r_bend=20`，Coupon 的 IO 弯实际 **20 µm** | 默认改为 ≥52（建议 `r_euler_true`），并让 `RadiusMin` 参与校验 |
| 5 | `Coupon` / `TCRaceTrackS` / `TCRaceTrackS2` / `TCRaceTrackS3` / `TCRaceTrackS3h` / `DoubleRaceTrack` | 使用 `gf.routing.route_single_sbend`，该函数**不保证半径**（ExtCavDouRing 曾出现 2.37 µm） | 统一换成 `_two_arc_s`（由端点反算 R，R<下限直接报错）或显式 radius 的 Euler S |
| 6 | `TCRaceTrackS` | 只传 `tout` 不传 `tin` 时 `UnboundLocalError: ctin`（输出分支引用了未定义的 `ctin`） | 输出分支用 `in_x = ... if ctin is not None else 0.0`，与 `Coupon` 一致 |
| 7 | `TCRaceTrackS2`（已修复） | 同位置出现两个同向 `o2` 端口 @ (12632.126,-2223.354)，朝向 0°/0° | 检查是否是重复实例/重复 add_port；修完交叉后一并清理 |

## 3. P2 — IO 端口方向复核

> 非 90° 光端口本身允许（Add/Drop 可切向）；这里只列 **Input/Through 不是 0°/180°** 或最终 IO 需要旋转的情况。

| 函数 | 端口 | 当前朝向 | 判断 |
|---|---|---|---|
| `ExtCavTriRing2` | `input` | 135° | 最终输入为斜向；若作最终 IO，需加 45° 校直或旋转 |
| `RingPulley2` / `RingPulley2ES` / `RingPulleyT2` | Input/Through | 315°/225° | 斜向总线；最终放置需旋转或加 45° 校直 |
| `RingPulley4` | Input/Through | 225°/315° | 同上 |
| `RingPulley3` | Input/Through | 270°/270° | 两端同向，疑似端口朝向/镜像错误，优先核对 |
| `RaceTrackS` / `RaceTrackStrHC` | Input/Through | 270°/90° | 竖直 IO；最终版图需旋转到水平或加弯 |
| `RingBoomerang` | Input/Through | 270°/90° | 同上 |
| `RingTriBoomerang` | Through | 90° | 同上 |
| `TCCoupleDouRaceTrackT2`（已修复） | `input` | 90° | 同上 |
| `TCRingCoupon` | `input` | 90° | 同上 |
| `OptPDCSagnacLoop` | `Out` | 160° | 这是 PDC 的自然端口角；Add/Drop 允许，但若当光纤口用建议加 20° 校直到 180° |

> `PMZI` / `PMZIHSn` 的 `Input1=270°`、`Output2=90°` 是内部 MZI 臂端口，不是最终 IO，不列为问题。

### 3b. 非 90° 光端口（手册允许，确认用途即可）

这些端口是监控口、环中心参考口或 pulley 耦合器的自然端口；手册允许非 90° 光端口。只要不作为最终水平 IO，直接保留；若当光纤口用，按最终方向加校直弯：

`Boomerang（Lo1/Lo2 225°, Ro1 45°）、CoupleRingDRT1（Ring2C 30°）、PulleyCoupler2X2（in1 169°, out1 11°）、RingDouBoomerang（315/135°）、TCCoupleDouRingT1（Ring2C 150°）、TCRing2/2_2/2_3/T2（RingC 135°）、TaperRsoa（o1 347°）`。

## 4. 判定为有意 / 需人工确认

| 函数 | 现象 | 判断 |
|---|---|---|
| `DBR` | 每个周期 1.0↔2.0 µm 宽度“台阶” | **有意**：Bragg 光栅的宽度调制，不是 taper 缺失 |
| `EDBRStrRep` / `EDBRStrRep_InvertTone` | WG 重叠 42.35 µm² | 采样光栅/重叠周期，**很可能是设计意图**；需看渲染确认不是误重合 |
| `Complete_Inverted_Device` | WG 重叠 42.35 µm² | 倒置器件/实心填充，**很可能有意**；确认填充区不是意外短路 |
| `TCRingBoomerangT1` 等 | M1 金属重叠 1127 µm² | 加热器/引线连接，**金属层允许有意重叠**；只查是否短到不该短的网 |
| 多个器件 | WG 重叠 0.001–0.03 µm² | 多为 butt joint 的 1 DBU 舍入条，不是真实短路；<0.05 µm² 未列入 P0 |

## 5. 默认构建无自动告警的函数（约 44 个）

`ADRAPRADR, CROW, CoupleDouRaceTrack, CoupledRingFilter, Crossing_taper, DMZI, DispersionRingRow, DoubleRingMemyshev, DoubleRingPulley, DoubleRingPulley2HSn, DoubleRingPulley2_1HSn, EDBRStrRep_InvertTone_Full, ExtCavDouRing, ExtCavDouRing2, ExtCavDouRing3, ExtCavTriRing, ExtCavTriRing2_2, ExtCavWang, GSGELE, GfCStraight, GongCavity, OffsetRamp, OpenPad, OptMMISagnacLoop, RaceTrackP, RingCouponRow, RingFinger, RingPulley, RingPulley1DC, RingPulley1HS, RingPulley1HSn, RingPulleyT1, SCISSOR, SagnacRing, TCRing, TCRing1_3, TCRing3, TCRingT1, TCTaperRaceTrackP, TaperRaceTrackPulley, TriRingPulley, WangCavity, cir2end, ring_coupon`

> 这些函数默认构建没有触发本轮自动检查；不代表 100% 合规。无 `min_bend_radius` 的手工挤出路径、内部嵌套路由仍需渲染/中心线复核。

## 6. 审计方法与局限

- 重叠：`get_polygons(by="tuple")` 后逐层 `sum(area) - merged(area)`，并对 ≤500 个多边形的层做逐对求交，记录 bbox。负值/极小值是 DBU 舍入，不判红。
- 曲率：递归读取所有嵌套 cell 的 `info["min_bend_radius"]`。**盲区**：`gf.path.extrude` 手工路径、`route_single_sbend` 的内部 cell 可能没有 info；因此 P1 的 `route_single_sbend` 是静态扫描补的。
- 端口：顶层端口方向；顶层实例端口的同位置朝向/宽度。耦合间隙（如 ring-bus 0.3 µm）不会被误判，因为阈值是 1.5 nm。
- 悬空弯：只查顶层 bend 实例；嵌套 bend 由它所属的公共函数单独审计。
- 未做：DRC（没有对应平台的 `drc.py` 规则文件）、中心线 shapely 交点（重叠已能捕获大部分交叉）、渲染逐图人工复核（本轮只做了关键红项的局部裁剪）。

## 7. 建议修复顺序

1. **先修 `route_off_grid`**（P0 #1）→ 解除 5 个 Isolator/TCRing 函数的断连。
2. **修 10 个真实交叉/重叠**（P0 #7–#16），每修一个跑“中心线交点 + 同层求交 + 渲染”。
3. **修曲率**：`GfCBendEuler` 默认、`FeedbackRing`/`OptFeedbackRing` 的 IO 弯、`TCRaceTrackP` 的 `r_bend`，并把所有 `route_single_sbend` 换成半径受控 S。
4. **修 `TCRaceTrackS` 的 `tout` 分支 UnboundLocalError**。
5. **IO 方向**：按最终摆放决定旋转/校直；优先处理 `RingPulley3` 的 270/270 同向端口。
6. 对“有意重叠”三类（DBR/EDBR/Complete_Inverted_Device）做一次渲染确认，避免把设计意图误修。
