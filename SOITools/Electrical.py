"""电学结构：过孔 / 接触孔阵列、金属引线、探针焊盘与加热器落点。

ICRD 的电学设计规则在封装里固定为：

* V1 / V2 为 0.324 um 方孔，间距 0.81 um；
* CT 为 0.30 um 方孔，间距 0.90 um；
* Mx 引线按矩形叠加绘制（避免圆弧端头，满足 Mx.8）；
* 小焊盘 70 um，COVER 55 um，RV 20 um，M1/M2 转接板 9.6 um（Mx.5）。
"""

from __future__ import annotations

from .FabBasic import (
    ALPAD,
    COVER,
    COVER_SMALL,
    CT,
    M1,
    M2,
    M3,
    PAD_METAL,
    PAD_SMALL,
    RV,
    RV_PAD,
    V1,
    V2,
    box,
    cosd,
    sind,
)


def via_array(c, cx: float, cy: float, layer, n: int = 12,m :int= None,
              pitch: float = 0.81, size: float = 0.324) -> None:
    """n x m 方形过孔阵列，以 (cx, cy) 为中心。

    ``m`` 为 None 时取 n（正方阵列）。阵列**以 (cx, cy) 为中心**：行方向
    用 m 居中，列方向用 n 居中（早期版本两处都用了 n，m != n 时阵列会
    整体偏出中心 m 与 n 的差值的一半）。
    """
    if m is None:
        m = n
    for i in range(n):
        for j in range(m):
            x = cx + (i - (n - 1) / 2) * pitch
            y = cy + (j - (m - 1) / 2) * pitch
            box(c, x - size / 2, y - size / 2, x + size / 2, y + size / 2,
                layer)


def contact_array(c, x0: float, x1: float, y: float, layer=CT,
                  pitch: float = 0.9, size: float = 0.30) -> None:
    """在 [x0, x1] 内居中排布一行 CT（固定 0.30 um 方孔）。"""
    n = max(1, int((x1 - x0 - size) / pitch) + 1)
    span = (n - 1) * pitch + size
    xc = 0.5 * (x0 + x1)
    xs = xc - span / 2 + size / 2
    for i in range(n):
        x = xs + i * pitch
        box(c, x - size / 2, y - size / 2, x + size / 2, y + size / 2, layer)


def add_path(c, pts, width: float, layer) -> None:
    """正交金属引线：矩形叠加，端头为直角（Mx.8）。"""
    pts = [(float(x), float(y)) for x, y in pts]
    h = width / 2.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        box(c, min(x0, x1) - h, min(y0, y1) - h,
            max(x0, x1) + h, max(y0, y1) + h, layer)
    for x, y in pts:
        box(c, x - h, y - h, x + h, y + h, layer)


def add_bond_pad(c, cx: float, cy: float, size: float = PAD_SMALL,
                 cover: float = COVER_SMALL, landing: str = "M1") -> None:
    """M3/ALPAD 探针焊盘 + 到焊盘的落点（按需画转接板/过孔）。

    RV.1 宽 >= 3、RV.2 间距 >= 3、RV.4/6 包覆 >= 1.5。单块 RV 板比阵列
    更简单，也与焊盘叠层示意一致。M1/M2 落点固定 9.6 um，满足 Mx.5
    （<= 10 um）；宽大的 M3/ALPAD 是焊盘，不是走线。

    ``landing`` 指定本焊盘要接到哪一层，决定画哪些层：
      * ``"M3"``：M3 就是落点（M3 引线直接进焊盘），不再画 M1/M2/过孔；
      * ``"M2"``：M2 落点 + V2（M2 -> M3）；
      * ``"M1"``：M1 落点 + V1 + M2 + V2（M1 -> M2 -> M3），默认，兼容旧调用。

    焊盘会把画上去的金属层彼此短在一起，所以**只画这一端真正要接的层**：
    多余的转接板/过孔既浪费面积，又会让从焊盘下面经过的其它网络被短进来。
    """
    box(c, cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2, M3)
    box(c, cx - size / 2, cy - size / 2, cx + size / 2, cy + size / 2, ALPAD)
    box(c, cx - cover / 2, cy - cover / 2,
        cx + cover / 2, cy + cover / 2, COVER)
    box(c, cx - RV_PAD / 2, cy - RV_PAD / 2,
        cx + RV_PAD / 2, cy + RV_PAD / 2, RV)
    if landing == "M3":
        return
    box(c, cx - PAD_METAL / 2, cy - PAD_METAL / 2,
        cx + PAD_METAL / 2, cy + PAD_METAL / 2, M2)
    via_array(c, cx, cy, V2)
    if landing == "M2":
        return
    box(c, cx - PAD_METAL / 2, cy - PAD_METAL / 2,
        cx + PAD_METAL / 2, cy + PAD_METAL / 2, M1)
    via_array(c, cx, cy, V1)


def add_heat_landing(c, cx: float, cy: float, ang: float,
                     r_in: float, r_out: float, via=V1,
                     size: float = 2.0, n: int = 2,
                     pitch: float = 0.81):
    """在环带加热器上做 M1 -> V1 -> M2 落点，返回落点中心。

    ``ang`` 是环带上的极角（度）；落点取环带径向中线的位置。
    """
    rr = 0.5 * (r_in + r_out)
    x = cx + rr * cosd(ang)
    y = cy + rr * sind(ang)
    box(c, x - size / 2, y - size / 2, x + size / 2, y + size / 2, M1)
    via_array(c, x, y, via, n=n, pitch=pitch)
    box(c, x - size / 2, y - size / 2, x + size / 2, y + size / 2, M2)
    return x, y
