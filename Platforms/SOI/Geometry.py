"""通用二维版图几何：切线连续中心线与等宽 / 变宽条带。

这里只放与工艺层无关的纯几何工具，Si / SiN / TiN / 金属都可以复用：

* ``Route`` —— 由直线段和圆弧拼出的切线连续中心线（gdsfactory 路径的
  轻量替代，直接输出 um 坐标，不依赖 KLayout 的路径栅格化）；
* ``add_strip`` / ``add_closed_strip`` —— 沿中心线做等宽偏移，生成
  开放或闭合条带；
* ``add_width_strip`` —— 逐点宽度，用于锥形过渡和混合截面；
* ``add_annulus`` —— 圆弧环带（可 360 度），单个简单多边形，无内孔；
* ``add_taper_h`` —— 水平线性锥；
* ``extend_ends`` —— 沿端点切向延长开放折线。
"""

from __future__ import annotations

import math

import numpy as np

from .FabBasic import (ANNULUS_STEP_DEG, ARC_STEP_DEG, add_poly, cosd,
                       sind)


def _fresnel(r0: float, s: float, n: int):
    """Fresnel 积分（欧拉弯曲用）；从 AIPLPhMTools/GeneralTools 改写。"""
    t = np.linspace(0, s, n)
    if n < 2:
        return np.array([0.0]), np.array([0.0])
    dt = t[1] - t[0]
    co = np.cos(t ** 2 / (2 * r0 ** 2))
    si = np.sin(t ** 2 / (2 * r0 ** 2))
    x = np.zeros(n)
    y = np.zeros(n)
    for i in range(1, n):
        x[i] = x[i - 1] + (co[i - 1] + co[i]) * dt / 2
        y[i] = y[i - 1] + (si[i - 1] + si[i]) * dt / 2
    return x, y


def euler_half(radius: float = 10.0, angle: float = -10.0,
               p: float = 0.5, npoints: int = 240):
    """半欧拉弯曲：起始曲率为 1/radius，末端曲率为 0。

    与 AIPLPhMTools/GeneralTools/BasicDefine.py 的 ``euler_Bend_Half``
    同一算法（Backward 方向）；返回 gdsfactory ``Path``，可直接与
    ``gf.path.arc`` 相加，用于 pulley 耦合总线的平滑过渡。
    """
    from gdsfactory.path import Path
    from gdsfactory.component_layout import rotate_points

    if not (0 < p <= 1):
        raise ValueError("p must be in (0, 1]")
    mirror = angle < 0
    ang = abs(angle)
    r0 = 1.0
    alpha = np.radians(ang * 2)
    rp = r0 / np.sqrt(p * alpha)
    sp = r0 * np.sqrt(p * alpha)
    s0 = 2 * sp + rp * alpha * (1 - p)

    npt = max(npoints, int(360 / ang) + 1)
    n_e = int(round(sp / (s0 / 2) * npt))
    n_a = npt - n_e
    if n_e > 0:
        xb, yb = _fresnel(r0, sp, n_e)
        dx = xb[-1] - rp * np.sin(p * alpha / 2)
        dy = yb[-1] - rp * (1 - np.cos(p * alpha / 2))
    else:
        xb = yb = np.empty(0)
        dx = dy = 0.0
    ss = np.linspace(sp, s0 / 2, n_a)
    xa = rp * np.sin((ss - sp) / rp + p * alpha / 2) + dx
    ya = rp * (1 - np.cos((ss - sp) / rp + p * alpha / 2)) + dy
    x = np.concatenate([xb, xa[1:]])
    y = np.concatenate([yb, ya[1:]])
    pts = np.flipud(np.array([x, -y]).T)
    pts = rotate_points(pts, ang - 180)
    pts += -pts[0, :]
    end_angle = ang
    dy_end = np.tan(np.radians(end_angle - 90)) * pts[-1][0]
    reff = pts[-1][1] - dy_end
    scale = radius / rp
    pts *= scale
    path = Path()
    path.points = pts
    path.start_angle = 0.0
    path.end_angle = end_angle
    if mirror:
        path.mirror((1, 0))
    return path


def pulley_half(r_bus: float, angle: float):
    """Pulley 耦合总线的半个中心线：耦合圆弧 + 半欧拉过渡。

    从环的耦合顶点（总线离环最近处）出发，先走 ``angle/2`` 的同心圆弧，
    再用同半径的半欧拉弯平滑过渡回水平；返回 (points, dx, dy)：
    终点相对起点水平前进 dx、远离环 dy。
    """
    import gdsfactory as gf
    arc = gf.path.arc(radius=r_bus, angle=angle / 2)
    eul = euler_half(radius=r_bus, angle=-angle / 2)
    half = arc + eul
    pts = np.asarray(half.points)
    return pts, abs(pts[-1, 0]), abs(pts[-1, 1])


def pulley_bus_points(cx: float, cy: float, r_bus: float, angle: float,
                      x_left: float, x_right: float, side: int = 1):
    """Pulley 耦合环总线的完整中心线，从 x_left 水平进、x_right 水平出。

    side=+1：总线在环上方（top bus），耦合圆弧在 y=cy+r_bus；
    side=-1：总线在环下方（bottom bus）。
    外端总线高度 = 耦合顶点 ∓ dy（朝环心一侧），x 端口仍为 x_left/x_right。
    """
    half, dx, dy = pulley_half(r_bus, angle)
    if x_left > cx - dx or x_right < cx + dx:
        raise ValueError("bus ports are too close to the ring for this pulley")
    y_top = cy + side * r_bus          # coupling vertex (nearest to ring)
    y_out = y_top - side * dy          # outer horizon, towards the ring centre
    right = [(cx + x, y_top - side * y) for x, y in half]
    left = [(cx - x, y_top - side * y) for x, y in half]
    pts = [(x_left, y_out)] + left[::-1] + right[1:] + [(x_right, y_out)]
    return pts


class Route:
    """切线连续中心线：直线 + 圆弧。

    ``x, y, h`` 是当前画笔位置和航向（度，逆时针为正）。所有方法原地修改
    并返回 ``self``，便于链式调用::

        p = Route(x0, y0, 0)
        p.straight(100).turn(-90, 11).straight(50)
    """

    def __init__(self, x: float, y: float, heading: float):
        self.pts = [(float(x), float(y))]
        self.x, self.y, self.h = float(x), float(y), float(heading)

    def straight(self, length: float):
        """沿当前航向前进 ``length``（可为负）。"""
        if abs(length) < 1e-12:
            return self
        self.x += length * cosd(self.h)
        self.y += length * sind(self.h)
        self.pts.append((self.x, self.y))
        return self

    def s(self, length: float):
        """``straight`` 的简写。"""
        return self.straight(length)

    def turn(self, delta: float, radius: float, step: float = ARC_STEP_DEG):
        """转过 ``delta`` 度（逆时针为正），圆弧半径 ``radius``。"""
        if abs(delta) < 1e-12:
            return self
        sign = 1.0 if delta > 0 else -1.0
        cx = self.x + radius * cosd(self.h + 90.0 * sign)
        cy = self.y + radius * sind(self.h + 90.0 * sign)
        a0 = self.h - 90.0 if sign > 0 else self.h + 90.0
        a1 = a0 + delta
        n = max(2, int(abs(delta) / step) + 1)
        for i in range(1, n + 1):
            a = a0 + (a1 - a0) * i / n
            self.pts.append((cx + radius * cosd(a), cy + radius * sind(a)))
        self.x, self.y = self.pts[-1]
        self.h += delta
        return self

    def t(self, delta: float, radius: float, step: float = ARC_STEP_DEG):
        """``turn`` 的简写。"""
        return self.turn(delta, radius, step)

    def s_bend(self, rise: float, radius: float, step: float = ARC_STEP_DEG):
        """两段反向圆弧：保持航向，横向偏移 ``rise``。"""
        c = 1.0 - abs(rise) / (2.0 * radius)
        theta = math.degrees(math.acos(max(-1.0, min(1.0, c))))
        if rise >= 0:
            self.turn(theta, radius, step)
            self.turn(-theta, radius, step)
        else:
            self.turn(-theta, radius, step)
            self.turn(theta, radius, step)
        return self


def _normals(pts):
    """折线每个顶点的单位左法向。"""
    n = len(pts)
    out = []
    for i in range(n):
        if i == 0:
            tx, ty = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        elif i == n - 1:
            tx, ty = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
        else:
            tx = pts[i + 1][0] - pts[i - 1][0]
            ty = pts[i + 1][1] - pts[i - 1][1]
        ln = math.hypot(tx, ty)
        if ln < 1e-12:
            tx, ty, ln = 1.0, 0.0, 1.0
        out.append((-ty / ln, tx / ln))
    return out


def _tangent_offsets(pts, width, closed=False):
    """返回等宽条带的 (左, 右) 偏移折线。"""
    pts = [(float(x), float(y)) for x, y in pts]
    if closed:
        if math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) < 1e-9:
            pts = pts[:-1]
        n = len(pts)
        left, right = [], []
        for i in range(n):
            x0, y0 = pts[(i - 1) % n]
            x1, y1 = pts[(i + 1) % n]
            tx, ty = x1 - x0, y1 - y0
            ln = math.hypot(tx, ty)
            nx, ny = -ty / ln, tx / ln
            x, y = pts[i]
            left.append((x + nx * width / 2, y + ny * width / 2))
            right.append((x - nx * width / 2, y - ny * width / 2))
        # 闭合环不能留缝：采样中心线在接缝前就结束了，最后一对偏移点若
        # 保持原样会在环上留下两个相距零点几微米的平行端帽（真实的缺口）。
        # 把最后一对钉到接缝偏移点上，闭合处退化为一条零宽径向切口。
        left[-1] = left[0]
        right[-1] = right[0]
        return left, right

    nrm = _normals(pts)
    left, right = [], []
    for (x, y), (nx, ny) in zip(pts, nrm):
        left.append((x + nx * width / 2, y + ny * width / 2))
        right.append((x - nx * width / 2, y - ny * width / 2))
    return left, right


def strip_sides(pts, width: float, closed: bool = False):
    """返回等宽条带的两条偏移折线 ``(left, right)``（与 ``add_strip`` 同源）。

    ``left`` 是沿行进方向的左法向一侧。闭合环按 ``add_closed_strip`` 的
    方式收口（首尾钉在一起）。给「两条带要拼成一块」的场合用：直接拿同一
    次偏移算出的边界去拼，边界逐点重合，不会留下 nm 级缝。
    """
    return _tangent_offsets(pts, width, closed=closed)


def add_disk(c, cx: float, cy: float, r: float, layer, n: int = 96) -> None:
    """实心圆（填充/补丁用）。``n`` 是圆周采样点数，默认每圈 96 点。

    用来堵「两条开窗以极小夹角收拢」留下的楔口：圆没有直边，不会像方形
    补丁那样和旁边近乎平行的边界再夹出新的发丝缝。
    """
    pts = [(cx + r * math.cos(2.0 * math.pi * i / n),
            cy + r * math.sin(2.0 * math.pi * i / n)) for i in range(n)]
    add_poly(c, pts, layer)


def add_strip(c, pts, width: float, layer) -> None:
    """等宽条带，端面平齐（开放）。"""
    left, right = _tangent_offsets(pts, width, closed=False)
    add_poly(c, left + right[::-1], layer)


def add_closed_strip(c, pts, width: float, layer) -> None:
    """等宽闭合环带（螺旋腔等）。"""
    left, right = _tangent_offsets(pts, width, closed=True)
    add_poly(c, left + right[::-1], layer)


def add_width_strip(c, pts, widths, layer) -> None:
    """逐顶点宽度的条带：分段线性锥 / 混合截面。"""
    pts = [(float(x), float(y)) for x, y in pts]
    nrm = _normals(pts)
    left, right = [], []
    for (x, y), (nx, ny), w in zip(pts, nrm, widths):
        left.append((x + nx * w / 2, y + ny * w / 2))
        right.append((x - nx * w / 2, y - ny * w / 2))
    add_poly(c, left + right[::-1], layer)


def add_taper_strip(c, pts, w_base, w_start=None, w_end=None,
                    taper_start=0.0, taper_end=0.0, layer=None,
                    hold_start=0.0, hold_end=0.0) -> None:
    """宽度渐变的条带（耦合波导与标准单模波导宽度不同时的过渡）。

    主体宽 ``w_base``。起点一侧：前 ``hold_start`` µm 保持 ``w_start``，
    其后 ``taper_start`` µm 内线性变到 ``w_base``；终点一侧对称：后
    ``hold_end`` µm 保持 ``w_end``，其前 ``taper_end`` µm 内从
    ``w_base`` 线性变到 ``w_end``。``w_start`` / ``w_end`` 为 None 时
    该端保持 ``w_base``。

    过渡长度按**中心线弧长**定义，与折线顶点的疏密无关：锥形段的边界
    会在中心线上补一个插值顶点，所以「10 µm 锥形」就是真的 10 µm，
    不会因为折线只有两个端点而把锥形摊到整条走线上。插值是线性的，
    因此锥形段最好落在直线段上（弯道里会切掉一点弦高）。
    """
    pts = [(float(x), float(y)) for x, y in pts]
    n = len(pts)
    if n < 2:
        return
    s = [0.0] * n
    for i in range(1, n):
        s[i] = s[i - 1] + math.hypot(pts[i][0] - pts[i - 1][0],
                                     pts[i][1] - pts[i - 1][1])
    total = s[-1]

    # ---- 断点（弧长, 宽度） ----------------------------------------- #
    bps: list[tuple[float, float]] = []

    def push(sv: float, w: float) -> None:
        if sv < -1e-9 or sv > total + 1e-9:
            return
        sv = min(max(sv, 0.0), total)
        if bps and abs(sv - bps[-1][0]) < 1e-9:
            return
        bps.append((sv, w))

    if w_start is not None and taper_start > 0.0:
        push(0.0, w_start)
        push(hold_start, w_start)
        push(hold_start + taper_start, w_base)
    if w_end is not None and taper_end > 0.0:
        push(total - hold_end - taper_end, w_base)
        push(total - hold_end, w_end)
        push(total, w_end)
    bps.sort(key=lambda t: t[0])

    def width_at(sv: float) -> float:
        if not bps:
            return w_base
        if sv <= bps[0][0]:
            return bps[0][1]
        for (s0, w0), (s1, w1) in zip(bps, bps[1:]):
            if sv <= s1:
                if s1 - s0 < 1e-12:
                    return w1
                return w0 + (w1 - w0) * (sv - s0) / (s1 - s0)
        return bps[-1][1]

    # ---- 在断点处补顶点（线性插值） --------------------------------- #
    def point_at(sv: float):
        for i in range(1, n):
            if sv <= s[i] + 1e-9:
                seg = s[i] - s[i - 1]
                t = 0.0 if seg < 1e-12 else (sv - s[i - 1]) / seg
                return (pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t,
                        pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t)
        return pts[-1]

    samples: list[tuple[float, tuple[float, float]]] = [
        (s[i], pts[i]) for i in range(n)]
    for sv, _w in bps:
        if sv <= 1e-9 or sv >= total - 1e-9:
            continue
        samples.append((sv, point_at(sv)))
    samples.sort(key=lambda t: t[0])

    widths = [width_at(sv) for sv, _p in samples]
    add_width_strip(c, [p for _sv, p in samples], widths, layer)


def add_annulus(c, cx: float, cy: float, r_in: float, r_out: float,
                a0: float, a1: float, layer,
                step: float = ANNULUS_STEP_DEG) -> None:
    """圆弧环带，画成一个简单多边形（无内孔）。

    整 360 度环带用两段重叠圆弧拼出：单个闭合圆环需要一条零宽径向缝，
    在最小宽度检查中会被读成细颈。1 度重叠在同层合并时自动消失。
    """
    span = abs(a1 - a0)
    if span >= 360.0 - 1e-9:
        add_annulus(c, cx, cy, r_in, r_out, a0, a0 + 180.5, layer, step)
        add_annulus(c, cx, cy, r_in, r_out, a0 + 179.5, a0 + 360.5, layer, step)
        return
    n = max(8, int(span / step) + 1)
    ang = [math.radians(a0 + (a1 - a0) * i / (n - 1)) for i in range(n)]
    outer = [(cx + r_out * math.cos(a), cy + r_out * math.sin(a)) for a in ang]
    inner = [(cx + r_in * math.cos(a), cy + r_in * math.sin(a))
             for a in reversed(ang)]
    add_poly(c, outer + inner, layer)


def add_taper_h(c, x0: float, x1: float, y: float, w0: float, w1: float,
                layer) -> None:
    """水平线性锥。"""
    add_poly(
        c,
        [(x0, y - w0 / 2), (x1, y - w1 / 2), (x1, y + w1 / 2), (x0, y + w0 / 2)],
        layer,
    )


def extend_ends(pts, first: float = 0.0, last: float = 0.0):
    """沿首 / 尾端点切向延长开放折线（0 表示保持原样）。"""
    pts = [(float(x), float(y)) for x, y in pts]
    if len(pts) < 2:
        return pts
    out = list(pts)
    if first > 0.0:
        x0, y0 = pts[0]
        x1, y1 = pts[1]
        ln = math.hypot(x1 - x0, y1 - y0)
        if ln > 1e-12:
            out[0] = (x0 - first * (x1 - x0) / ln,
                      y0 - first * (y1 - y0) / ln)
    if last > 0.0:
        xa, ya = pts[-2]
        xb, yb = pts[-1]
        ln = math.hypot(xb - xa, yb - ya)
        if ln > 1e-12:
            out[-1] = (xb + last * (xb - xa) / ln,
                       yb + last * (yb - ya) / ln)
    return out
