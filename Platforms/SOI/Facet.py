"""斜端面接入（RSOA 增益芯片 / 光纤）—— 器件级组件。

一段斜着离开芯片边缘的 SiN 波导：端面处窄（光斑小、和增益芯片的模场
匹配），往外先保持窄芯，再绝热展宽到标准单模 ``W_SIN``，最后用小角度
弯（与端面倾角相反）折回水平总线，正好停在给它的端口面上。

为什么是"斜"的
--------------
RSOA 的增益波导端面有约 13° 的倾角（抑制端面反射）。芯片这边的端面
必须同角度对接，光才不会在端面处被折弯；靠一个与倾角相反的弯把光轴
拉回水平，后面的总线、Trans、光栅都是水平摆放的。

为什么端面要窄
--------------
增益芯片的模场约 1~2 µm 宽、且偏心；这边先用 0.5 µm 窄芯让模场扩散
到端面，再在 70 µm 内展宽到 1.0 µm 交给标准单模走线。窄芯段也决定了
端面的有效反射率（越窄越不容易把光反射回增益腔）。

端口约定
--------
``port`` 是**本组件自己的端口**（SiN、朝外），也是走线的终点面；调用者
用 ``reference.connect`` 把上游总线接上来即可。``facet_x`` 是芯片端面
的 x 坐标（局部坐标原点在端面下方，端面在 ``facet_x`` 处）。

几何自检
--------
``run`` 由"弯结束点 -> 端口面"的水平距离自动求出，所以端面位置和端口
位置任何一个改动，中间直段都会自动变长/变短，不会出现台阶或折返。

迁移目标（见 `AGENTS.md` R11 与手册 §2.1）
------------------------------------------
本模块当下放在过渡壳里，因为它的依赖（FabBasic 层号、Geometry.Route、
Routing.add_sin_windows）还都在 `ICRDPhMTools`。迁移到
``AIPLPhMTools/GeneralTools/ICRD/Facet.py`` 时要和这些依赖一起搬，不要
只搬这一个文件（否则 AIPLPhMTools 会反向依赖过渡壳）。
"""
from __future__ import annotations

from .FabBasic import SIN, W_SIN, cosd, sind
from .Geometry import Route, add_width_strip
from .Routing import add_sin_windows


def add_angled_facet(c, port, facet_x: float = 2.0, facet_angle: float = 12.9,
                     bend_deg: float = -12.9, bend_r: float = 100.0,
                     l_facet: float = 40.0, l_taper: float = 30.0,
                     l_mid: float = 20.0, l_bend: float = 70.0,
                     w_facet: float = 0.50, w_mid: float = 0.28,
                     w_guide: float = W_SIN, layer=SIN,
                     mirror: bool = True):
    """在 ``c`` 上画斜端面接入，返回端面中心的世界坐标。

    参数（全部显式给出，单位 µm / 度）：

    ===========  ==========================================================
    port         走线终点：上游总线要接的 SiN 端口坐标 (x, y)
    facet_x      芯片端面的 x（通常贴着版图左边界）
    facet_angle  端面相对竖直方向的倾角（RSOA 用 12.9°）
    bend_deg     端面后第一个弯的角度（与 ``facet_angle`` 反号 -> 回水平）
    bend_r       这个弯的中心线半径（SiN NWG2 >= 50，这里用 100）
    l_facet      端面窄芯长度（``w_facet`` 保持段）
    l_taper      窄芯收到 ``w_mid`` 的锥长
    l_mid        ``w_mid`` 保持段
    l_bend       ``w_mid`` 展宽到 ``w_guide`` 的长度（含弯）
    w_facet      端面芯宽（0.5：和增益芯片模场匹配）
    w_mid        中间窄芯宽（0.28：偏振/单模滤波）
    w_guide      交出去的标准单模宽（W_SIN = 1.0）
    mirror       True 时以端口高度为轴上下镜像（端面在总线上方，
                 光是"往下折"进总线的，与左侧 RSOA 的接法一致）
    ===========  ==========================================================

    返回 ``(facet_x, y_facet)``，方便在外面放对准标记。
    """
    px, py = port

    # 1) 从端面往端口方向排：直段 + 锥 + 直段 + 小角度弯
    x_a = l_facet
    x_b = x_a + l_taper
    x_c = x_b + l_mid
    bend = Route(l_facet + l_taper + l_mid + l_bend, 0.0, 0.0)
    bend.turn(bend_deg, bend_r)
    ex, ey = bend.pts[-1]

    # 2) 端面沿 facet_angle 倾斜：反解端面中心的 y，使弯结束点正好落在
    #    "端面 + 旋转后的局部形状"上；run 由端口面反推，保证终点精确。
    dy = ex * sind(facet_angle) + ey * cosd(facet_angle)
    facet_y = py - dy
    dx = ex * cosd(facet_angle) - ey * sind(facet_angle)
    run = px - (facet_x + dx)

    local_end = (ex + run * cosd(bend_deg), ey + run * sind(bend_deg))
    local = [(0.0, 0.0), (x_a, 0.0), (x_b, 0.0), (x_c, 0.0)] \
        + list(bend.pts) + [local_end]
    # 宽度：端面窄芯 -> 收到 w_mid -> 在 l_bend 内展宽到 w_guide
    widths = [w_facet, w_facet, w_mid, w_mid] \
        + [w_guide] * len(bend.pts) + [w_guide]

    ca, sa = cosd(facet_angle), sind(facet_angle)
    pts = [(x * ca - y * sa + facet_x, x * sa + y * ca + facet_y)
           for x, y in local]
    if mirror:
        pts = [(x, 2.0 * py - y) for x, y in pts]

    add_width_strip(c, pts, widths, layer)
    # 三层开窗 + SINOP；端口端不加帽（要把 SiN 交给上游宏单元）
    add_sin_windows(c, pts, core_w=w_guide, sinop_caps=(True, False))

    return (facet_x, 2.0 * py - facet_y if mirror else facet_y)
