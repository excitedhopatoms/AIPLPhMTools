# AIPLPhMTools.SOITools —— SOI 硅光版图子库

从 ICRD 项目（`202610_SOI_icrd`，12 英寸 SOI：220 nm Si + 双层 SiN + TiN +
M1/M2/M3 + ALPAD/COVER）提炼出的可复用部分。**层号与那套流片文件一致**，
所以这里的每个函数画出来的形状可以直接进 ICRD 的 GDS 且与
`ICRDPhMTools` 逐层完全一致。

## 1. 为什么是独立子包

AIPLPhMTools 主库用的是另一套层号（`WG 1/0`、`M1 10/0`、`M2 4/1`、SiN
`130/0` …）。SOI 的 `M1 = (641,1)`、`SIN = (631,1)` 如果 star-import 进主库
命名空间，会和主库的 `M1/M2/…` 互相覆盖。所以做**显式命名空间**：

```python
import AIPLPhMTools.SOITools as soi            # 推荐
from AIPLPhMTools.SOITools import Route, add_si_route, add_bond_pad, M1
```

**不要**在 `AIPLPhMTools/__init__.py` 里 `from .SOITools import *`。

## 2. 模块与来源

| 子库模块 | 来源（ICRDPhMTools） | 内容 | 相对来源的改动 |
|---|---|---|---|
| `FabBasic.py` | `FabBasic.py` | SOI 层号表（600/631/632/639/641..643/651/652/660..662/665/674…）、工艺常数（`W_SI/W_SIN/W_RING/W_RINGBUS/W_SPIRAL/W_PHASE`、`R_SI/R_SIN/R_*_MIN`、`SIN_CLD_W`、`SINOP_EXTRA`、`PAD_*`）、顶点采样（`ARC_STEP_DEG=0.2` 光路圆弧 / `ANNULUS_STEP_DEG=0.5` 金属环带 / `BUFFER_RES` / `SIMPLIFY_TOL` / `SPIRAL_N`）、`box/add_poly/cosd/sind` | PDK 宏目录改为可配置（环境变量 `SOI_PDK_DIR` 或 `soi.set_pdk_dir()`），不再绑定项目路径；文件头改成“子库”说明；采样常数与 ICRDPhMTools 同步（环带保持 0.5°，加密会暴露 1 nm 布尔台阶） |
| `Geometry.py` | 同名 | `Route`（`straight/turn/s_bend`，S 弯跨度 `√(4R·dy−dy²)`）、等宽/闭合/变宽条带、`add_annulus`、pulley 弧、`extend_ends` | 无 |
| `Routing.py` | 同名 | `add_si_route`（600/1 + 600/10）、`add_sin_route`（631/1 + 631/10/632/10/600/10 + SINOP）、`add_sin_route_taper`、`add_si_link`（直线/S 弯/掉头 C 形）、开窗与 SINOP 并集 | 无 |
| `Electrical.py` | 同名 | `via_array/contact_array`、`add_path`、`add_bond_pad(landing="M1"/"M2"/"M3")`、`add_heat_landing` | **`add_bond_pad` 新增 `landing`**（见 §4），旧的整叠行为保留为 `landing="M1"` 默认 |
| `Ring.py` | 同名 | `RingPulley` 单侧 pulley 耦合环；`RaceTrackPulley` 跑道腔（直段竖直、半圆弯段 pulley 耦合，带端口） | 新增 `RaceTrackPulley`（SINOP 带 + 耦合段补块，边界取自 `strip_sides`） |
| `Spiral.py` | 同名 | 闭合双螺旋腔中心线（长延迟线，`centerline()/circle()/curvature_radius()`） | 无 |
| `Facet.py` | 同名 | `add_angled_facet`：12.9° 斜端面 + 反角弯（RSOA / 光纤） | 无 |
| `Audit.py` | 同名 | `GdsAudit`、`nets`、`width_v/width_h`、`net_at/on`、`polygon_of`、`load_polygons` | 无 |
| `Assembly.py` | 同名 | 带端口组件包装、`reference.connect` 组装、PDK 宏加载 `pdk()` | `pdk()` 用的是 `FabBasic.PDK_DIR`（可配置） |

`ICRDPhMTools/PDKPorts.py`（Trans/GC/EC/MMI/PD 端口表）没有搬：它绑定 ICRD
那套 PDK 宏，等宏库进 AIPL 时再一起搬。

## 3. 复用清单（实际被反复用到的）

- **`Route`**：所有走线先用它把中心线走出来，再交给 `add_*_route`。
  `s_bend` 的跨度公式要用来反推下游器件位置（Trans/GC 的 x 就是这么来的）。
- **`add_sin_route`**：一次画全 SiN 芯 + 631/10 + 632/10 + 600/10 开窗 +
  SINOP。缺一层就是一次流片事故，所以永远调库、不手画。
- **`add_sin_route_taper`**：环总线（0.858）/ spiral 总线（1.0）→ 单模（1.0）
  的锥形入口。
- **`add_si_link`**：两个宏的 Si 端口之间自动选“直线 / S 弯 / 掉头 C 形”。
- **`add_bond_pad(landing=…)`**：探针焊盘 + 只画本端需要的落点（§4）。
- **`add_annulus` / `via_array` / `add_heat_landing`**：环形 TiN 加热器、
  过孔阵列、加热器落点。
- **`GdsAudit` + `nets/width_v/width_h`**：对写出的 GDS 做“按层连通网 / 线宽 /
  重叠”判据，而不是相信自己脑补的坐标。

## 4. `add_bond_pad(..., landing=...)`：为什么要按端选层

旧实现每个焊盘都画 `M3 + ALPAD + COVER + RV + M1 板 + M2 板 + V1 阵列 + V2 阵列`，
等于把 M1/M2/M3 全短在焊盘里。后果有两个：

1. 多余的板/孔没有用处（M3 引线直接进焊盘时，M1/M2/V1/V2 全是浪费）；
2. 更糟的是**短路入口**：任何从焊盘下面经过的别的网络，只要和焊盘里某一层
   同层，就被短进来。

现在按这一端真正接的层画：

| `landing` | 画什么 | 适用 |
|---|---|---|
| `"M3"` | M3/ALPAD/COVER/RV | 引线本身是 M3 |
| `"M2"` | + M2 落点 + V2 | 引线是 M2 |
| `"M1"` | + M1 落点 + V1 + M2 + V2 | 引线是 M1（默认，兼容旧调用） |

ICRD 实测：10 个焊盘（8 个走本函数）改完后 M1 网 31→23、M2 网 38→35、
V1 622→230、V2 512→365，DRC 还少了 4 个焊盘角上的 M2 假报。

## 5. 版图经验（从这套流片里踩出来的，通用）

**几何**
1. 任何“派生位置”（外框、GC 端口、下游器件 x）必须由**画图用的同一组参数**
   算出来：锥长、S 弯跨度、lead 长度。手写常量一定会在某次改动后失效
   （ICRD 的环加 S 弯后，外框/端口全错，GC 端面量出 0）。
2. S 弯跨度 = `√(4R·|dy| − dy²)`；`dy` 为 0 时不要走 S 弯（退化成直线）。
3. 宽条（≥10 µm）切 2 µm 环带时，切点会留 <0.36 µm 楔形缝（M1/M2 space 假报）：
   先做 6 µm 宽的**径向短颈**跨过环带，再用宽条。
4. 宽引线要停在圆环**内沿以内**，而且按圆算：x = ±w/2 处的内沿比正下方低
   `r − √(r²−(w/2)²)`（r=104.5、w=20 时差 1.5 µm）。按正下方数值停，两个角
   会切进环带，同样留楔形缝。
5. 圆弧/环带的面积、周长用参数化算，不要用 bbox。

**电极**
6. 焊盘只画本端要接的层（§4）；焊盘会把画上的金属层彼此短在一起。
7. 把带孔的器件（环）套到别人的焊盘行上要当心：环内的分配环是 `ØR` 的整圆，
   100 µm/200 µm pitch 的焊盘必然插进环孔，和同层分配环短路（ICRD 实测
   TiN 445 + M2 227 + M3 233 µm²，A/B 两端一起短死）。两个解法：挪器件，
   或者**把电极换到对方没有的层**（ICRD 里把 B 分配环从 M3 换到 M1，
   M2 小岛 → 单孔 V1 → M1 环 → M1 引线到焊盘）。
8. TiN 只能经 V1 接 M2（工艺约定），所以 TiN 的电极第一跳一定是 M2；
   再往下换层要用第二个 V1（M2→M1）。
9. 换层过孔别贴着 TiN 边缘：V1 阵列（2×2）有 1.3 µm 高，单孔才 0.32 µm，
   窄缝里要用单孔。

**审计**
10. 同层重叠是短路，跨层重叠不是：Si/SiN 压在别人焊盘上没关系，但只要
    TiN/M1/M2/M3/ALPAD 和对方同层，就是死短路。判据要**按层**做。
11. 只按平面并集连网会把“叠在一起但层间无过孔”的金属判成短路；要用
    V1/V2/RV 建图（`_metal_graph` 那套）。
12. 每改一次都跑：build → 全审计 → DRC（两个 die）→ 渲染。渲染里肉眼看不出
    的层间短路，必须靠按层求交。

## 6. 用法

```python
import gdsfactory as gf
import AIPLPhMTools.SOITools as soi

soi.set_pdk_dir("S:/path/to/gdsPDK")     # 只在用到 pdk()/RingPulley 时才需要

c = gf.Component("demo")
# 1) Si 走线：中心线 -> 芯 + 开窗
p = soi.Route(0, 0, 0).straight(80).turn(-90, soi.R_SI).straight(40)
soi.add_si_route(c, p.pts)

# 2) SiN 走线（自带 631/10、632/10、600/10、SINOP）
q = soi.Route(0, 40, 0).straight(30).s_bend(-20, soi.R_SIN).straight(20)
soi.add_sin_route(c, q.pts)

# 3) 环形 TiN 加热条 + 过孔
soi.add_annulus(c, 200, 100, 110, 112, 0, 360, soi.TIN)

# 4) 探针焊盘：M2 引线 -> landing="M2"
soi.add_bond_pad(c, 260, 100, size=60, cover=40, landing="M2")
```

## 7. 与主库的关系 / 后续

- 主库 `AIPLPhMTools/__init__.py` **不导入**本子库（层号冲突）。
- ICRD 项目暂时仍用 `ICRDPhMTools`；等子库稳定后，把
  `ICRDPhMTools/*.py` 换成一行转发即可（`from AIPLPhMTools.SOITools.Routing import *`），
  避免两份实现漂移（skill 里的 P-B4）。
- 层号/工艺数字只应存在一处：`AIPLPhMTools/SOITools/FabBasic.py`。
  项目侧的 `FabDefine_SOI.py` 只放器件与布局参数。
