"""器件级组件（AIPLPhMTools 风格）。

约定（与 AIPLPhMTools/GeneralTools/Ring.py 一致）：

* 函数名用大驼峰，参数用大驼峰且带默认值；
* 返回 ``gf.Component``，在组件上 ``add_port``；
* 中文 docstring 写清参数、端口和几何；
* 底层图元仍放在 ``Geometry`` / ``Routing`` / ``Electrical`` 的 ``add_*`` 函数里。

这里先放 pulley 耦合环；后续的 MMI 臂、相位段等也可以按同样方式加进来。
"""
from __future__ import annotations

import math

import gdsfactory as gf
from shapely.geometry import Polygon as sPolygon, box as sbox
from gdsfactory.component import Component

from .FabBasic import (LAYER, SINOP_EXTRA, SIN_CLD_W, W_SIN,W_RING,W_RINGBUS)
from .Geometry import (Route, add_annulus, add_closed_strip, add_strip,
                       pulley_bus_points, pulley_half, strip_sides)
from .Routing import add_shapely, add_sin_route


@gf.cell
def RingPulley(
        WidthRing: float = W_RING,
        WidthNear: float = W_RINGBUS,
        RadiusRing: float = 120.0,
        GapRing: float = 0.0,
        AngleCouple: float = 20.0,
        InputSide: str = "right",
        SinopGapDeg: float = 14.0,
        EndTrim: float = 0.0,
        Sides: str = "both",
        RingLayer=LAYER.NWG3,
        BusLayer=LAYER.NWG2,
        RingCLD=LAYER.NWG3_CLD,
        BusCLD=LAYER.NWG2_CLD,
) -> Component:
    """Pulley 耦合的 add-drop 环（环 NWG3，总线 NWG2）。

    环放在 NWG3（632/1），总线仍在 NWG2（631/1），两层 SiN 的垂直间距
    约 200 nm。``GapRing`` 是**总线中心线到环中心线**的径向间隙：
    ``GapRing = 0`` 时总线与环同心、在耦合弧上上下重叠（垂直耦合）；
    ``GapRing > 0`` 时总线在环外侧，两者横向错开，靠边缘倏逝场耦合。
    几何与 AIPLPhMTools 的 ``RingPulleyT1`` 同一套路：耦合弧半径
    ``RadiusRing + GapRing``，圆弧角度 ``AngleCouple``（±一半），
    两端半欧拉弯过渡到水平总线。

    参数：
        WidthRing: 环波导宽度 (µm)。
        WidthNear: 总线波导宽度 (µm)。
        RadiusRing: 环中心半径 (µm)。
        GapRing: 总线中心线与环中心线的径向间隙 (µm)。
        AngleCouple: 总耦合角 (度)，同心圆弧部分。
        InputSide: "right" 时 Input 在右上端；"left" 时 Input 在左上端。
        SinopGapDeg: 环 SINOP 在 0° 处为 TiN 引线留的缺口角度 (度)。
        Sides: "both" 画上下两条总线（add-drop）；"top" 只画上总线 ——
            用于"单侧耦合"的测试环（只有一条总线，做 through 谱）。
        EndTrim: **欧拉弯之后那段水平直段，两端各缩短多少**（µm）。
            总线端点 = ±(r_bus + ext − EndTrim)，四个端口跟着内移同样的量，
            所以外部接在端口上的走线会自动跟着变短（整体更紧凑）。
            上限由耦合弧 + 半欧拉弯的水平跨度 ``dx`` 决定（见下方断言）。
        RingLayer / BusLayer: 环 / 总线的光学芯层。
        RingCLD / BusCLD: 环 / 总线的 SiN 开窗层（两层互相覆盖对方核心）。

    端口：
        TopL / TopR：上总线的左右端（朝外）。
        BotL / BotR：下总线的左右端（朝外）。
        Input / Through：按 InputSide 映射到上总线两端。
        Add / Drop：按下总线两端映射（与 InputSide 相反）。
        RingL / RingR / RingC：环上的参考端口（供加热器/调试用）。
    """
    c = gf.Component()
    r_bus = RadiusRing + GapRing
    _, _, dy = pulley_half(r_bus, AngleCouple)

    # 环芯（NWG3）、两层的 17 um 窗口、Si 隔离窗口、SINOP
    add_annulus(c, 0.0, 0.0, RadiusRing - WidthRing / 2,
                RadiusRing + WidthRing / 2, 0.0, 360.0, RingLayer, step=0.25)
    add_annulus(c, 0.0, 0.0, RadiusRing - SIN_CLD_W / 2,
                RadiusRing + SIN_CLD_W / 2, 0.0, 360.0,
                RingCLD, step=0.25)
    add_annulus(c, 0.0, 0.0, RadiusRing - SIN_CLD_W / 2,
                RadiusRing + SIN_CLD_W / 2, 0.0, 360.0,
                BusCLD, step=0.25)
    add_annulus(c, 0.0, 0.0, RadiusRing - SIN_CLD_W / 2,
                RadiusRing + SIN_CLD_W / 2, 0.0, 360.0,
                LAYER.SIWG_CLD, step=0.25)
    add_annulus(c, 0.0, 0.0, RadiusRing - WidthRing / 2 - SINOP_EXTRA,
                RadiusRing + WidthRing / 2 + SINOP_EXTRA,
                SinopGapDeg / 2, 360.0 - SinopGapDeg / 2,
                LAYER.SINOP, step=0.25)

    # 上下两条 pulley 总线
    # 总线比接入它的走线窄（W_RINGBUS < W_SIN），SINOP 要按较宽的一条画，
    # 否则宽度台阶的拐角会露在 0.63 um 包边之外；总线两端再多画
    # sinop_extra + 0.05 um（NWG2.10 的端面余量），让 SINOP 与外部走线
    # 的 SINOP 互相搭接，避免出现发丝状缝隙。
    sinop_extra = SINOP_EXTRA + max(0.0, (W_RING - WidthNear) / 2.0)
    ext = sinop_extra + 0.05
    # 端口放在总线端点往内 ext 处（端面留一点搭接余量），
    # 再整体内移 EndTrim —— 两端直段各短 EndTrim，下游走线自动跟随。
    _, dx, _ = pulley_half(r_bus, AngleCouple)
    if EndTrim < 0.0 or r_bus + ext - EndTrim <= dx + 1.0:
        raise ValueError(
            f"RingPulley: EndTrim={EndTrim} 太大，欧拉弯需要 {dx:.2f} um "
            f"的水平跨度（端口 x 必须 > {dx:.2f}，且两端至少留 1 um 直段）")
    if Sides not in ("both", "top"):
        raise ValueError("Sides must be 'both' or 'top'")
    sides = (+1,) if Sides == "top" else (+1, -1)
    port_x = r_bus - EndTrim
    for side in sides:
        pts = pulley_bus_points(0.0, 0.0, r_bus, AngleCouple,
                                -r_bus - ext + EndTrim,
                                r_bus + ext - EndTrim, side=side)
        add_sin_route(c, pts, core_w=WidthNear,
                      sinop_extra=sinop_extra)  # NWG2 bus + 三层窗口

    # 耦合弧上把环/总线的 SINOP 开窗填成一块实心扇区，避免两个窗口
    # 以很小的夹角相交、留下 <1 um 的凹口（SINOP space/notch 假报）。
    # 扇区一直盖到「环 SINOP 外缘与总线 SINOP 内缘的竖直间隙 >= 1.5 um」
    # 处（角度由几何解出）：否则两条带在中段以 ~1° 收拢，留 0.01~0.3 um
    # 的楔形细缝（SINOP.2）。
    r_sinop_out = RadiusRing + WidthRing / 2.0 + SINOP_EXTRA
    y_bus_in = r_bus - dy - (WidthNear / 2.0 + sinop_extra)
    _margin = 1.5
    _h = max(0.0, y_bus_in - _margin)
    half = (math.degrees(math.atan2(math.sqrt(max(0.0,
                    r_sinop_out ** 2 - _h ** 2)), _h))
            if _h > 1e-9 else AngleCouple / 2.0 + 3.0)
    half = max(AngleCouple / 2.0 + 3.0, half)
    for a0 in ((90.0,) if Sides == "top" else (90.0, 270.0)):
        add_annulus(c, 0.0, 0.0,
                    RadiusRing - WidthRing / 2 - SINOP_EXTRA,
                    r_bus + WidthNear / 2 + SINOP_EXTRA,
                    a0 - half, a0 + half, LAYER.SINOP, step=0.25)


    y_top = r_bus - dy          # 水平总线端比耦合顶点更靠近环心
    y_bot = -(r_bus - dy)
    # 端口宽度必须落在偶数 DBU（0.002 um）上，否则 kfactory 无法对齐栅格；
    # 几何宽度仍按设计值画，端口只做 1 nm 的对齐。
    port_w = round(WidthNear / 0.002) * 0.002
    ends = [("TopL", -port_x, y_top, 180.0), ("TopR", port_x, y_top, 0.0)]
    if Sides == "both":
        ends += [("BotL", -port_x, y_bot, 180.0), ("BotR", port_x, y_bot, 0.0)]
    for nm, x, y, orient in ends:
        c.add_port(nm, center=(x, y), orientation=orient,
                   width=port_w, layer=BusLayer)

    if InputSide == "right":
        mapping = (("Input", "TopR"), ("Through", "TopL"),
                   ("Add", "BotL"), ("Drop", "BotR"))
    elif InputSide == "left":
        mapping = (("Input", "TopL"), ("Through", "TopR"),
                   ("Add", "BotR"), ("Drop", "BotL"))
    else:
        raise ValueError("InputSide must be 'left' or 'right'")
    for dst, src in mapping:
        if src in c.ports:            # 单侧总线时只有 Top*
            c.add_port(dst, port=c.ports[src])

    # 环上的参考端口（与 AIPLPhMTools RingPulleyT1 的命名一致）
    c.add_port("RingL", center=(-RadiusRing, RadiusRing), orientation=90.0,
               width=WidthRing, layer=RingLayer)
    c.add_port("RingR", center=(RadiusRing, RadiusRing), orientation=90.0,
               width=WidthRing, layer=RingLayer)
    c.add_port("RingC", center=(0.0, RadiusRing), orientation=90.0,
               width=WidthRing, layer=RingLayer)
    return c


def _mean_y(arr) -> float:
    """折线的平均 y（用来判断偏移折线在环的上方还是下方）。"""
    return sum(p[1] for p in arr) / max(1, len(arr))


@gf.cell
def RaceTrackPulley(
        WidthRing: float = W_RING,
        WidthNear: float = W_SIN,
        RadiusRing: float = 50.0,
        LengthRun: float = 20.0,
        GapRing: float = W_RING / 2.0 + 1.5 + W_SIN / 2.0,
        AngleCouple: float = 9.0,
        BusLength: float | None = None,
        Sides: str = "top",
        SinopFillX: float | None = None,
        StepDeg: float = 0.1,
        RingLayer=LAYER.NWG2,
        BusLayer=LAYER.NWG2,
) -> Component:
    """跑道腔（stadium）pulley 耦合器件：直段竖直，总线耦合在**半圆的弯段**。

    几何
    ----
    闭环中心线 = ``straight(LengthRun)`` + ``turn(-180°, RadiusRing)`` 交替两段，
    直段沿 **y 方向**，所以两个半圆在上、下两侧。耦合发生在其中一个（或两个）
    半圆的弯曲段：总线沿半径 ``RadiusRing + GapRing`` 的同心弧走
    ``AngleCouple`` 度，再用半欧拉弯回到水平（``pulley_half``），水平段比
    耦合顶点下沉 ``dy``。因此腔与总线的**中心线间距处处等于 GapRing**，
    边到边间隙 = ``GapRing - WidthRing/2 - WidthNear/2``。

    层：芯画在 ``RingLayer`` / ``BusLayer``（默认都 NWG2 = 631/1，共面侧向
    耦合）；17 um 开窗三层一次画全（632/10 + 631/10 + 600/10，NWG3.15 要求
    NWG2 芯也被 632/10 覆盖），SINOP 按芯宽 + 2*SINOP_EXTRA。腔带与总线带只搭 0.1 um，耦合段另加一块补块
    （边界取自同一次 ``strip_sides`` 偏移，逐点重合），否则并集在分离点会留
    ~3.6° 的零宽凹口，DRC 会报几十个 SINOP space/notch。

    参数
    ----
    WidthRing: 腔芯宽（默认 W_RING = 1.5）。
    WidthNear: 总线芯宽（默认 W_SIN = 1.0，与 PDK Trans 的 SiN 端口同宽）。
    RadiusRing: 半圆半径（默认 50；SiN 曲率规则 >= 50）。
    LengthRun: 直段长度（默认 20，左、右各一段）。
    GapRing: **中心线**间距（默认 = 半宽和 + 1.5 边到边间隙 = 2.75，
        与 ``RingPulley`` 的 GapRing 同义）。
    AngleCouple: 同心耦合弧总角（默认 9，与主片环的 PULLEY_ANGLE 一致）。
    BusLength: 总线水平段半长（默认 ``RadiusRing + 10``）；必须盖过半欧拉弯。
    Sides: ``"top"`` 只在上半圆耦合（all-pass）；``"both"`` 上下各一条（add-drop）。
    SinopFillX: 耦合段 SINOP 补块的 x 半长（默认 ``0.6*RadiusRing``，要
        超过两条带分开到 1 um 的位置）。
    StepDeg: 圆弧采样角步长（度，默认 0.1，与 RingPulley 的开窗采样一致）。
    RingLayer / BusLayer: 芯层（默认都 NWG2）。

    端口
    ----
    TopL / TopR: 上总线的左右端（朝外，宽 ``WidthNear``）。
    BotL / BotR: ``Sides="both"`` 时下总线的左右端。
    RingT / RingB: 上 / 下半圆顶点（朝外）；RingL / RingR: 左右直段中点。
    """
    if Sides not in ("both", "top"):
        raise ValueError("Sides must be 'both' or 'top'")
    c = Component()

    r_bus = RadiusRing + GapRing
    _, dx, dy = pulley_half(r_bus, AngleCouple)
    if BusLength is None:
        BusLength = RadiusRing + 10.0
    if BusLength <= dx + 1.0:
        raise ValueError(
            f"RaceTrackPulley: BusLength={BusLength} 太短，半欧拉弯需要 "
            f"{dx:.2f} um 的水平跨度")
    fill_x = 0.6 * RadiusRing if SinopFillX is None else SinopFillX
    sides = (+1,) if Sides == "top" else (+1, -1)

    # 1. 闭环中心线：左直段(向上) -> 上半个圆 -> 右直段(向下) -> 下半个圆
    loop = Route(-RadiusRing, -LengthRun / 2.0, 90.0)
    loop.straight(LengthRun)
    loop.turn(-180.0, RadiusRing, StepDeg)
    loop.straight(LengthRun)
    loop.turn(-180.0, RadiusRing, StepDeg)
    pts = [(float(x), float(y)) for x, y in loop.pts]
    if math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1]) < 1e-6:
        pts = pts[:-1]              # 闭合环：去掉与首点重合的尾点

    # 2. 腔芯 + 三层 17 um 开窗（632/10、631/10、600/10 一次画全）
    add_closed_strip(c, pts, WidthRing, RingLayer)
    for layer in (LAYER.NWG3_CLD, LAYER.NWG2_CLD, LAYER.SIWG_CLD):
        add_closed_strip(c, pts, SIN_CLD_W, layer)

    # 3. pulley 总线（每条半圆一条）：同心弧 + 半欧拉弯 + 水平段
    buses = {}
    for side in sides:
        bpts = pulley_bus_points(0.0, side * LengthRun / 2.0, r_bus,
                                 AngleCouple, -BusLength, BusLength, side=side)
        add_sin_route(c, bpts, core_w=WidthNear, sinop=False)
        buses[side] = bpts

    # 4. SINOP：腔带 + 总线带 + 耦合段补块（边界同源，逐点重合）
    add_closed_strip(c, pts, WidthRing + 2 * SINOP_EXTRA, LAYER.SINOP)
    c1, c2 = strip_sides(pts, WidthRing + 2 * SINOP_EXTRA, closed=True)
    for side in sides:
        add_strip(c, buses[side], WidthNear + 2 * SINOP_EXTRA, LAYER.SINOP)
        b1, b2 = strip_sides(buses[side], WidthNear + 2 * SINOP_EXTRA)
        # 腔：靠环心一侧的边界（上半圆取下沿、下半圆取上沿）
        inner = min(([p for p in arr if side * p[1] > 0] for arr in (c1, c2)),
                    key=lambda a: side * _mean_y(a))
        inner = sorted((p for p in inner if abs(p[0]) <= fill_x),
                       key=lambda p: p[0])
        # 总线：远离环心一侧的边界
        outer = max((b1, b2), key=lambda a: side * _mean_y(a))
        outer = sorted(outer, key=lambda p: p[0])
        patch = sPolygon(inner + outer[::-1]).buffer(0).intersection(
            sbox(-fill_x, -10.0 * RadiusRing, fill_x, 10.0 * RadiusRing))
        add_shapely(c, patch, LAYER.SINOP)

    # 5. 端口
    port_w = round(WidthNear / 0.002) * 0.002
    y_out = r_bus - dy
    for side, names in ((+1, ("TopL", "TopR")), (-1, ("BotL", "BotR"))):
        if side not in sides:
            continue
        y = side * (LengthRun / 2.0 + y_out)
        c.add_port(names[0], center=(-BusLength, y), orientation=180.0,
                   width=port_w, layer=BusLayer)
        c.add_port(names[1], center=(BusLength, y), orientation=0.0,
                   width=port_w, layer=BusLayer)
    c.add_port("RingT", center=(0.0, LengthRun / 2.0 + RadiusRing),
               orientation=90.0, width=WidthRing, layer=RingLayer)
    c.add_port("RingB", center=(0.0, -(LengthRun / 2.0 + RadiusRing)),
               orientation=270.0, width=WidthRing, layer=RingLayer)
    c.add_port("RingL", center=(-RadiusRing, 0.0), orientation=180.0,
               width=WidthRing, layer=RingLayer)
    c.add_port("RingR", center=(RadiusRing, 0.0), orientation=0.0,
               width=WidthRing, layer=RingLayer)
    return c
