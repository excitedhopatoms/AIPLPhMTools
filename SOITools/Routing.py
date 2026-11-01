"""Si / SiN 波导走线：核心、隔离开窗与 SINOP 保护岛。

ICRD 的 vfab 极性要求（NWG2.18）：

* Si 核心（600/1）两侧必须有 600/10 隔离开窗，设计宽度 8.45 um；
* SiN 核心（631/1）必须同时被 631/10 与 600/10 的 17 um 窗口包围；
* SiN 核心外还要有 665/1 SINOP 保护岛，单边余量 0.65 um。

本模块把「核心 + 三层窗口」封装成一次调用，避免每个器件重复计算偏移。
"""

from __future__ import annotations

from shapely.geometry import LineString

from .FabBasic import (
    BUFFER_RES,
    CLD_END_EXT,
    CLD_HALF,
    SI_CLD_HALF,
    SI_CLD_W,
    SIN_CLD_W,
    SINOP_EXTRA,
    SIWG,
    SIWG_CLD,
    SIN,
    SIN3,
    SIN3_CLD,
    SINOP,
    W_SIN,
    W_SI,
    R_SI,
    SIMPLIFY_TOL,
    SIN_CLD,
    add_poly,
    box,
    cosd,
)
from .Geometry import (
    Route,
    add_closed_strip,
    add_strip,
    add_width_strip,
    extend_ends,
)


# --------------------------------------------------------------------------- #
# SiN 走线
# --------------------------------------------------------------------------- #
def add_buffered_strip(c, pts, width: float, layer) -> None:
    """以中心线圆角 buffer 生成条带（用于曲率半径很小的 S 形连接）。

    偏移条带在拐折处会自交形成窄缝，buffer 不会；代价是轮廓是圆角
    多边形而不是严格等宽。
    """
    line = LineString([(float(x), float(y)) for x, y in pts])
    geom = line.buffer(width / 2.0, cap_style=2, join_style=1, resolution=BUFFER_RES)
    geom = geom.simplify(SIMPLIFY_TOL, preserve_topology=True)
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    for p in polys:
        add_poly(c, list(p.exterior.coords)[:-1], layer)


def add_shapely(c, geom, layer) -> None:
    """把一个 shapely 几何（允许多边形带孔）写到 ``layer``。

    ``add_poly`` 只能写顶点列表；17 um 窗 / SINOP 这种「环形 + 并集」的
    结果是带孔多边形，这里直接写 KLayout 的 ``DPolygon``（GDS 写出时会
    自动切成带零宽缝的简单多边形，孔洞的**面积**保持不变）。
    """
    import klayout.db as kdb

    if geom.is_empty:
        return
    parts = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    shapes = c.shapes(layer)
    for p in parts:
        if p.is_empty or p.area <= 0:
            continue
        rings = list(p.exterior.coords)[:-1]
        if len(rings) < 3:
            continue
        dp = kdb.DPolygon([kdb.DPoint(float(x), float(y)) for x, y in rings])
        for hole in p.interiors:
            hr = list(hole.coords)[:-1]
            if len(hr) >= 3:
                dp.insert_hole([kdb.DPoint(float(x), float(y)) for x, y in hr])
        shapes.insert(dp)


def buffer_union_geom(paths, width: float):
    """多条中心线的圆角 buffer 求并集（孔洞填实），返回 shapely 几何。"""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    polys = []
    for pts in paths:
        line = LineString([(float(x), float(y)) for x, y in pts])
        geom = line.buffer(width / 2.0, cap_style=2, join_style=1,
                           resolution=BUFFER_RES)
        geom = geom.simplify(SIMPLIFY_TOL, preserve_topology=True)
        parts = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
        polys.extend(Polygon(p.exterior) for p in parts)
    return unary_union(polys)


def add_buffered_union(c, paths, width: float, layers) -> None:
    """把几条中心线的圆角 buffer **合并成一个多边形**后写入各层。

    多个 buffer 互相重叠时如果分别画多边形，同一层内部会出现它们之间
    的拼接线（版图里看到的“接缝”）。这里先在 shapely 里求并集，再写
    一个多边形，内部没有接缝。孔洞被填实（对刻蚀 / 保护窗口无害）。
    """
    merged = buffer_union_geom(paths, width)
    parts = ([merged] if merged.geom_type == "Polygon"
             else list(merged.geoms))
    for layer in layers:
        for p in parts:
            add_poly(c, list(p.exterior.coords)[:-1], layer)


def add_sin_route_taper(c, pts, w_base, w_start=None, w_end=None,
                        taper_start=0.0, taper_end=0.0,
                        sinop_extra=SINOP_EXTRA, sinop: bool = True,
                        hold_start=0.0, hold_end=0.0) -> None:
    """SiN 走线，两端可带锥形过渡。

    耦合波导（比如环上的 0.858 µm 总线）和标准单模波导（1.0 µm）宽度
    不一样时，接缝处要加一段锥形过渡，否则会有宽度台阶。

    芯层用逐点宽度（``add_taper_strip``）画；17 µm 窗口和 SINOP 仍按整条
    中心线画，宽度按最宽的一段给，所以锥形段完全被覆盖。``hold_start``
    / ``hold_end`` 是两端保持恒定宽度（不参与过渡）的长度，用来让锥形
    从真正的接缝面开始、到接缝面结束。
    """
    from .Geometry import add_taper_strip

    add_taper_strip(c, pts, w_base, w_start, w_end,
                    taper_start, taper_end, SIN,
                    hold_start=hold_start, hold_end=hold_end)
    widths = [w_base] + [w for w in (w_start, w_end) if w is not None]
    add_sin_windows(c, pts, core_w=max(widths),
                    sinop_extra=sinop_extra, sinop=sinop)


def add_sin_windows(c, pts, closed: bool = False, core_w: float = W_SIN,
                    sinop_extra: float = SINOP_EXTRA,
                    sinop_caps=(False, False), sinop: bool = True,
                    cld_ext=(CLD_END_EXT, CLD_END_EXT)) -> None:
    """沿 SiN 中心线画 631/10、600/10 和 SINOP 三层窗口。

    ``sinop_caps`` 沿首 / 尾端切向延长 SINOP 岛（NWG2.10 要求终止的核心
    外再包 0.65 um）。只在芯片端面或自由监测尖端使用；在 PDK 端口处
    加帽会把氮化硅从宏单元体内挖掉。
    """
    if closed:
        add_closed_strip(c, pts, SIN_CLD_W, SIN_CLD)
        add_closed_strip(c, pts, SIN_CLD_W, SIN3_CLD)
        add_closed_strip(c, pts, SIN_CLD_W, SIWG_CLD)
        if sinop:
            add_closed_strip(c, pts, core_w + 2 * sinop_extra, SINOP)
    else:
        # 端面各多伸 cld_ext：让芯的端头被开窗包住（见 FabBasic 注释）
        pts_w = extend_ends(pts, cld_ext[0], cld_ext[1])
        add_strip(c, pts_w, SIN_CLD_W, SIN_CLD)
        add_strip(c, pts_w, SIN_CLD_W, SIN3_CLD)
        add_strip(c, pts_w, SIN_CLD_W, SIWG_CLD)
        if sinop:
            cap = sinop_extra + 0.05
            add_strip(c, extend_ends(pts,
                                     cap if sinop_caps[0] else 0.0,
                                     cap if sinop_caps[1] else 0.0),
                      core_w + 2 * sinop_extra, SINOP)


def add_buffered_windows(c, pts, core_w: float = W_SIN,
                         sinop_extra: float = SINOP_EXTRA) -> None:
    """以中心线圆角 buffer 的方式生成窗口。

    中心线偏移会自交的场合使用：17 um 窗宽大于 2R 的紧凑螺旋、入口 /
    出口腿间距小于窗宽的光延迟线。buffer 保证把核心完整包住；把内部
    孔洞填实对刻蚀 / 保护窗口没有影响。
    """
    line = LineString([(float(x), float(y)) for x, y in pts])
    for width, layer in ((SIN_CLD_W, SIN_CLD), (SIN_CLD_W, SIN3_CLD),
                         (SIN_CLD_W, SIWG_CLD),
                         (core_w + 2 * sinop_extra, SINOP)):
        geom = line.buffer(width / 2.0, cap_style=2, join_style=1, resolution=BUFFER_RES)
        geom = geom.simplify(SIMPLIFY_TOL, preserve_topology=True)
        polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
        for p in polys:
            add_poly(c, list(p.exterior.coords)[:-1], layer)


def add_sin_route(c, pts, closed: bool = False, core_w: float = W_SIN,
                  buffered: bool = False,
                  sinop_extra: float = SINOP_EXTRA, sinop: bool = True) -> None:
    """SiN 走线 = 核心 + 窗口（普通偏移或 buffer）。"""
    if closed:
        add_closed_strip(c, pts, core_w, SIN)
    else:
        add_strip(c, pts, core_w, SIN)
    if buffered:
        add_buffered_windows(c, pts, core_w=core_w, sinop_extra=sinop_extra)
    else:
        add_sin_windows(c, pts, closed=closed, core_w=core_w,
                        sinop_extra=sinop_extra, sinop=sinop)


def add_sin3_route(c, pts, closed: bool = False, core_w: float = W_SIN) -> None:
    """NWG3 走线：632/1 芯 + 632/10 + 631/10 + 600/10 + SINOP。

    NWG2/NWG3 是上下两层 SiN；按 NWG3.15/16，两层的开窗要互相覆盖
    对方的核心，所以 NWG3 走线同时画 631/10 和 632/10。
    """
    if closed:
        add_closed_strip(c, pts, core_w, SIN3)
    else:
        add_strip(c, pts, core_w, SIN3)
    pts_w = pts if closed else extend_ends(pts, CLD_END_EXT, CLD_END_EXT)
    for layer in (SIN3_CLD, SIN_CLD, SIWG_CLD):
        if closed:
            add_closed_strip(c, pts, SIN_CLD_W, layer)
        else:
            add_strip(c, pts_w, SIN_CLD_W, layer)
    if closed:
        add_closed_strip(c, pts, core_w + 2 * SINOP_EXTRA, SINOP)
    else:
        add_strip(c, pts, core_w + 2 * SINOP_EXTRA, SINOP)


def add_sin_taper_end(c, x0: float, y0: float, dx: float,
                      w0: float = W_SIN, w1: float = 0.15) -> None:
    """短锥形开放监测端口，沿 x 方向延长 ``dx``（可带符号）。

    SINOP 岛也跟着收窄：固定 1.45 um 宽的矩形在 1.0 um 端只剩 0.225 um
    余量，会违反 0.65 um 规则。
    """
    pts = [(x0, y0), (x0 + dx, y0)]
    add_width_strip(c, pts, [w0, w1], SIN)
    xs = sorted((x0, x0 + dx))
    box(c, xs[0] - 0.1, y0 - CLD_HALF, xs[1] + 0.1, y0 + CLD_HALF, SIN_CLD)
    box(c, xs[0] - 0.1, y0 - CLD_HALF, xs[1] + 0.1, y0 + CLD_HALF, SIWG_CLD)
    sgn = 1.0 if dx > 0 else -1.0
    add_width_strip(c, [(x0, y0), (x0 + dx + (SINOP_EXTRA + 0.05) * sgn, y0)],
                    [w0 + 2 * SINOP_EXTRA, w1 + 2 * SINOP_EXTRA], SINOP)


# --------------------------------------------------------------------------- #
# Si 走线
# --------------------------------------------------------------------------- #
def add_si_windows(c, pts, closed: bool = False,
                   cld_ext=(CLD_END_EXT, CLD_END_EXT)) -> None:
    """600/10 Si 隔离开窗（核心本身是 600/1）。"""
    if closed:
        add_closed_strip(c, pts, SI_CLD_W, SIWG_CLD)
    else:
        add_strip(c, extend_ends(pts, *cld_ext), SI_CLD_W, SIWG_CLD)


def add_si_route(c, pts, core_w: float = W_SI, closed: bool = False) -> None:
    """Si 走线 = 600/1 核心 + 8.45 um 600/10 隔离开窗。"""
    if closed:
        add_closed_strip(c, pts, core_w, SIWG)
    else:
        add_strip(c, pts, core_w, SIWG)
    add_si_windows(c, pts, closed=closed)


def add_si_port_overlap(c, x: float, y: float, length: float = 0.45) -> None:
    """跨接过渡器 / PD 宏的 0.45 um Si 短桩（端口两侧各延伸 ``length``）。

    版图走线与 PDK 短桩在端口处对接。对称延长（而不是只伸进宏单元）
    可以消除弯道首段斜边在接缝处留下的亚 0.4 um 楔形。
    """
    box(c, x - length, y - W_SI / 2, x + length, y + W_SI / 2, SIWG)
    box(c, x - length, y - SI_CLD_HALF, x + length, y + SI_CLD_HALF,
        SIWG_CLD)


# --------------------------------------------------------------------------- #
# Si 链路：宏端口 -> 宏端口
# --------------------------------------------------------------------------- #
def add_si_link(c, a_port, b_port, a_dir: float = 0.0, b_dir: float = 180.0,
                radius: float = R_SI) -> None:
    """Si 走线：``a_port`` -> ``b_port``，两端朝向由宏端口决定。

    ``a_dir`` / ``b_dir`` 是**链路自己**的端口朝向（指向链路外侧，所以与
    相邻宏的端口反平行，``reference.connect`` 才能对齐）。由此推出走向：

    * 起点行进方向 = ``a_dir`` + 180（链路从 a 往它的身体一侧走）；
    * 终点行进方向 = ``b_dir``（链路沿这个方向插进 b）。

    两种拓扑，按走向自动选：

    * **目标在前方**（``b_dir`` == 起点行进方向）：直线；两端高度不同时
      先走一段 S 弯吃掉高度差，再直线插进 b。
    * **目标在背后**（``b_dir`` == ``a_dir``，即要掉头）：走一个 "C" 形 ——
      直行、90° 弯、竖直段、再一个同向 90° 弯，合计 180°，正好从 b 的
      朝向插进端口。两段弯同向，所以不会出现反向折返段；首段长度由
      "竖直段落在 b 的哪一侧"自动求出。

    只用于非谐振 Si 走线（环监视口、spiral 测试口），默认半径
    ``R_SI = 11`` um（SIWG 规则 >= 10）。
    """
    x0, y0 = a_port
    x1, y1 = b_port
    R = radius
    h0 = (a_dir + 180.0) % 360.0          # 起点行进方向
    s2 = cosd(b_dir)                       # 终点行进方向（+1 东 / -1 西）

    if abs((b_dir - h0) % 360.0) < 1e-6:
        # ---------------- 目标在前方：直线 / S 弯 -------------------- #
        p = Route(x0, y0, h0)
        if abs(y1 - y0) > 1e-6:
            p.s_bend(y1 - y0, R)
        p.straight((x1 - p.x) * s2)
        add_si_route(c, p.pts)
        return

    # ---------------- 目标在背后：C 形掉头 ------------------------ #
    dy = y1 - y0
    vlen = abs(dy) - 2.0 * R
    if vlen < 0.0:
        raise ValueError(
            f"add_si_link: 两端高差 {dy:.2f} um 放不下两个 "
            f"R={R} 的 90 度弯")
    # 第一个 90° 弯必须朝 b 所在的一侧转
    ccw = 1.0 if ((h0 == 0.0) == (dy > 0.0)) else -1.0

    def _c_shape(lead: float):
        p = Route(x0, y0, h0)
        p.straight(lead)
        p.turn(ccw * 90.0, R)
        p.straight(vlen)
        p.turn(ccw * 90.0, R)
        return p

    # C 形本身的 x 位移为 0（两段弯相互抵消）。首段和末段各留 >= 1 um，
    # 否则端面落在圆弧起点上，偏移多边形会在端帽处挤出小尖角。
    lead = max(1.0, 1.0 - (x1 - x0) * s2)
    p = _c_shape(lead)
    p.straight(max(1e-9, (x1 - p.x) * s2))
    add_si_route(c, p.pts)
