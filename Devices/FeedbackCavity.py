"""微腔反馈结构：Add-Drop 环 + drop 端 Sagnac 回路反射镜。

对应论文 *Endlessly self-injection-locked photonic integrated lasers* 中的
“drop port + loop mirror” 结构：

* 主环通过两条切向耦合总线形成 Add-Drop 环；
* drop 总线接到一个 2×2 分束器的 Sagnac 回路反射镜；分束器可选
  MMI（``OptMMISagnacLoop``）或 pulley 耦合 DC（``OptPDCSagnacLoop``）；
* 反射镜的另外两个端口用闭环波导连接，形成真正的 loop mirror；
* ``AngleFeedback`` 改变 drop 耦合波导在环上的角位置，从而改变反馈
  相位色散；
* 主环带可选的 TiN/M1 环形加热器（复用库里的 ``DifferentHeater_local``）。

弯曲半径按设计手册的 SiN 下限选取：``RadiusMirror >= 50``。
"""
from __future__ import annotations

import numpy as np

from ..Core.BasicDefine import *
from .CouplerMZI import PulleyCoupler2X2
from .Ring import DifferentHeater_local

# 默认调谐结构：复用库里的环形 TiN 加热器配置。
_FEEDBACK_HEATER = heaterconfig0.with_changes(
    TypeHeater="default", WidthHeat=4, GapHeat=2, DeltaHeat=0,
    LayerHeat=LAYER.TN,
)


def _arc_coupler(radius: float, width: float, span: float,
                 center_angle: float, layer: LayerSpec) -> Component:
    """以原点为圆心的耦合圆弧，端口在弧的两端。"""
    comp = gf.Component()
    path = gf.path.arc(radius=radius, angle=span)
    ref = comp << gf.path.extrude(path, width=width, layer=layer)
    # arc 的圆心在 (0, radius)，先移到原点，再旋转到指定中心角。
    ref.movey(-radius)
    ref.rotate(center_angle - span / 2.0 + 90.0)
    comp.add_port("o1", port=ref.ports["o1"])
    comp.add_port("o2", port=ref.ports["o2"])
    return comp


def _full_ring(radius: float, width: float, layer: LayerSpec) -> Component:
    """圆心在原点的闭合圆环。"""
    comp = gf.Component()
    ref = comp << gf.path.extrude(
        gf.path.arc(radius=radius, angle=360), width=width, layer=layer
    )
    ref.movey(-radius)
    return comp


def _euler_sagnac_mirror(width: float, radius: float, layer: LayerSpec) -> Component:
    """旧版 Sagnac loop mirror：2×2 MMI + 4×90° Euler 路由。

    保留它是为了兼容 ``FeedbackRing(MirrorType="euler")``；
    新设计请用 ``_opt_mmi_sagnac_loop`` / ``_opt_pdc_sagnac_loop``。
    """
    comp = gf.Component()
    cross_section = make_cs(width, layer)
    mmi = comp << gf.c.mmi2x2(width=width, cross_section=cross_section)
    gf.routing.route_single(
        comp, mmi.ports["o3"], mmi.ports["o4"],
        cross_section=cross_section, radius=radius,
    )
    comp.add_port("In", port=mmi.ports["o1"])
    comp.add_port("Out", port=mmi.ports["o2"])
    return comp


def _opt_mmi_sagnac_loop(width: float, radius: float, radius_min: float,
                         layer: LayerSpec,
                         loop_shape: str = "circle") -> Component:
    """紧凑、无交叉的 MMI Sagnac loop mirror。

    路径（从 MMI o3 出发，回到 o4）：
    - 上臂：三次 Bezier S 弯，把 o3 平滑抬到 loop 的上端；
    - 主 loop：一条连续 180° 弯（默认半圆，可选 Euler）；
    - 下臂：镜像的 Bezier S 弯，平滑降到 o4。

    与旧版相比：主 loop 只有一条 180° 弯，不再用 4 个 90° Euler 拼接；
    两条 S 弯把上/下臂分开，设计中不产生中心线交叉，整体尺寸也更紧凑。
    """
    if radius < radius_min:
        raise ValueError(
            f"OptMMISagnacLoop: Radius={radius:.3f} um 小于 "
            f"RadiusMin={radius_min:.3f} um"
        )

    comp = gf.Component()
    cross_section = make_cs(width, layer)
    mmi = comp << gf.c.mmi2x2(width=width, cross_section=cross_section)

    o3 = mmi.ports["o3"]
    o4 = mmi.ports["o4"]
    port_sep = abs(float(o4.center[1]) - float(o3.center[1]))

    shape = str(loop_shape).lower()
    if shape.startswith("circle"):
        loop_path = gf.path.arc(radius=radius, angle=-180)
    else:
        loop_path = gf.path.euler(radius=radius, angle=-180)
    loop_sep = abs(float(loop_path.points[-1][1]))
    dy = (loop_sep - port_sep) / 2.0
    lead = max(2.12 * radius, 60.0)

    arm_top = comp << gf.c.bend_s(
        size=(lead, dy), cross_section=cross_section
    )
    arm_top.connect("o1", o3)
    loop = comp << gf.path.extrude(loop_path, width=width, layer=layer)
    loop.connect("o1", arm_top.ports["o2"])
    arm_bottom = comp << gf.c.bend_s(
        size=(lead, -dy), cross_section=cross_section
    )
    arm_bottom.connect("o2", loop.ports["o2"])

    # S 弯的实际最小半径也必须满足 RadiusMin。
    for label, arm in (("上臂", arm_top), ("下臂", arm_bottom)):
        r_arm = arm.cell.info.get("min_bend_radius")
        if r_arm is not None and float(r_arm) < radius_min - 1e-6:
            raise ValueError(
                f"OptMMISagnacLoop: {label}最小曲率半径 {float(r_arm):.2f} um "
                f"< RadiusMin={radius_min:.2f} um；请增大 Radius。"
            )

    comp.add_port("In", port=mmi.ports["o1"])
    comp.add_port("Out", port=mmi.ports["o2"])
    comp.info["splitter"] = "mmi"
    comp.info["loop_shape"] = shape
    comp.info["loop_radius"] = float(radius)
    comp.info["arm_lead"] = float(lead)
    comp.info["loop_sep"] = float(loop_sep)
    return comp


def _cubic_bezier_points(p0, c1, c2, p3, n: int = 300) -> np.ndarray:
    """三次 Bezier 的采样点（用于把多段曲线拼成一条连续中心线）。"""
    t = np.linspace(0.0, 1.0, int(n))[:, None]
    p0, c1, c2, p3 = (np.asarray(p, dtype=float) for p in (p0, c1, c2, p3))
    return ((1.0 - t) ** 3 * p0 + 3.0 * (1.0 - t) ** 2 * t * c1
            + 3.0 * (1.0 - t) * t ** 2 * c2 + t ** 3 * p3)


def _bezier_min_radius(p0, c1, c2, p3, n: int = 4000) -> float:
    """三次 Bezier 的最小曲率半径（解析曲率公式，包含两个端点）。"""
    t = np.linspace(0.0, 1.0, int(n))
    p0, c1, c2, p3 = (np.asarray(p, dtype=float) for p in (p0, c1, c2, p3))
    d1 = (3.0 * (1.0 - t)[:, None] ** 2 * (c1 - p0)
          + 6.0 * (1.0 - t)[:, None] * t[:, None] * (c2 - c1)
          + 3.0 * t[:, None] ** 2 * (p3 - c2))
    d2 = (6.0 * (1.0 - t)[:, None] * (c2 - 2.0 * c1 + p0)
          + 6.0 * t[:, None] * (p3 - 2.0 * c2 + c1))
    cross = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    speed = np.linalg.norm(d1, axis=1)
    kappa = np.abs(cross) / np.maximum(speed ** 3, 1e-30)
    return float(np.min(1.0 / np.maximum(kappa, 1e-12)))


def _opt_pdc_sagnac_loop(width: float, width_loop: float, radius: float,
                         radius_min: float, angle_couple: float,
                         radius_in: float, gap_coup: float,
                         length_taper: float, layer: LayerSpec,
                         loop_shape: str = "circle") -> Component:
    """紧凑、无交叉的 pulley 耦合 DC Sagnac loop mirror。

    与 ``_opt_mmi_sagnac_loop`` 使用同一套泪滴形 loop 优化，但 loop 的
    中心线由一条连续曲线构成：

    - 2×2 分束器用 ``PulleyCoupler2X2``；保持 ``IsParallel=False``
      （``IsParallel=True`` 会让两条耦合臂在耦合区产生同层小面积重叠）；
    - 从 out1 的圆弧切向直接起弯（三次 Bezier 上臂），不先转成直波导；
    - 接单条 180° Euler 主 loop；
    - 再用一条 Bezier 下臂直接绕回 out2 的耦合波导；
    - 三段在端点处切向相同，整体挤出为**一条**波导多边形，内部没有
      butt joint，不会产生 1 DBU 的接头 sliver。

    端口 ``In``（in2，180°）/``Out``（in1，180°-AngleCouple）。
    """
    if width <= 0 or width_loop <= 0:
        raise ValueError("OptPDCSagnacLoop: Width / WidthLoop 必须大于 0")
    if radius < radius_min:
        raise ValueError(
            f"OptPDCSagnacLoop: Radius={radius:.3f} um 小于 "
            f"RadiusMin={radius_min:.3f} um"
        )
    if radius_in < radius_min:
        raise ValueError(
            f"OptPDCSagnacLoop: RadiusIn={radius_in:.3f} um 小于 "
            f"RadiusMin={radius_min:.3f} um"
        )
    if not 0.0 < angle_couple < 90.0:
        raise ValueError("OptPDCSagnacLoop: AngleCouple 必须在 (0, 90) 度之间")
    if gap_coup < 0:
        raise ValueError("OptPDCSagnacLoop: GapCoup 不能为负")
    if length_taper <= 0:
        raise ValueError("OptPDCSagnacLoop: LengthTaper 必须大于 0")

    comp = gf.Component()
    pc = comp << PulleyCoupler2X2(
        WidthIn=width_loop, WidthOut=width,
        AngleCouple=angle_couple, AngleIn=2.0 * angle_couple,
        RadiusIn=radius_in, GapCoup=gap_coup, IsParallel=False,
        oplayer=layer,
    )

    # 下臂终点：默认就是 out2；若 loop 更宽，先接一段 taper 再做曲线。
    lower_port = pc.ports["out2"]
    lower_pos = np.asarray(lower_port.center, dtype=float)
    if abs(float(width_loop) - float(width)) > 1e-12:
        taper = comp << gf.c.taper(
            width1=width, width2=width_loop,
            length=length_taper, layer=layer,
        )
        taper.connect("o1", lower_port)
        lower_pos = np.asarray(taper.ports["o2"].center, dtype=float)

    # ---- 连续泪滴中心线：out1 -> 上臂 -> 180° loop -> 下臂 -> out2 ----
    p1 = np.asarray(pc.ports["out1"].center, dtype=float)
    th1 = float(pc.ports["out1"].orientation)
    p2 = lower_pos
    th2 = 180.0  # 进入 out2 / taper 的切向
    shape = str(loop_shape).lower()

    # circle：半圆，垂直跨度 2R、横向外凸 R，是最紧凑的 180° 回转；
    # euler：两端曲率为零、过渡更柔，但垂直跨度约 2.2R、外凸约 1.8R。
    if shape.startswith("circle"):
        loop_path = gf.path.arc(radius=radius, angle=-180)
        lead_factor = 1.0
    else:
        loop_path = gf.path.euler(radius=radius, angle=-180)
        lead_factor = 0.95
    loop_sep = abs(float(loop_path.points[-1][1]))

    # loop 垂直居中于两个端口，水平留出足够的上/下臂长度。
    loop_start = np.array([
        max(p1[0], p2[0]) + lead_factor * loop_sep,
        0.5 * (p1[1] + p2[1]) + 0.5 * loop_sep,
    ])
    loop_end = loop_start + np.array([0.0, -loop_sep])

    # 上臂：从 out1 的圆弧切向直接起弯，不先转成直波导。
    # circle 模式下把上臂终点曲率校到半圆的 1/R，使连接处曲率连续。
    dir1 = np.array([np.cos(np.radians(th1)), np.sin(np.radians(th1))])
    chord_up = float(np.linalg.norm(loop_start - p1))
    if shape.startswith("circle"):
        a_up = 0.40 * chord_up
        b2 = (2.0 * radius / 3.0) * (
            (loop_start[1] - p1[1]) - a_up * dir1[1]
        )
        if b2 <= 0.0:
            raise ValueError(
                "OptPDCSagnacLoop: 上臂无法与半圆 loop 曲率匹配，请增大 Radius"
            )
        b_up = float(np.sqrt(b2))
    else:
        a_up = b_up = 0.45 * chord_up
    c1 = p1 + a_up * dir1
    c2 = loop_start - np.array([b_up, 0.0])
    upper_pts = _cubic_bezier_points(p1, c1, c2, loop_start)

    # 下臂：一条水平 S 直接绕回耦合波导，不再插直波导。
    lead = float(loop_start[0] - p2[0])
    if lead <= 0.0:
        raise ValueError(
            "OptPDCSagnacLoop: 下臂水平长度必须大于 0，请检查 Radius/AngleCouple"
        )
    c3 = loop_end - np.array([0.5 * lead, 0.0])
    c4 = p2 + np.array([0.5 * lead, 0.0])
    lower_pts = _cubic_bezier_points(loop_end, c3, c4, p2)

    # 两条 Bezier 臂的实际最小曲率半径都必须满足 RadiusMin。
    arm_radii = {}
    for label, pts4 in (("上臂", (p1, c1, c2, loop_start)),
                        ("下臂", (loop_end, c3, c4, p2))):
        r_arm = _bezier_min_radius(*pts4)
        arm_radii[label] = r_arm
        if r_arm < radius_min - 1e-6:
            raise ValueError(
                f"OptPDCSagnacLoop: {label}最小曲率半径 {r_arm:.2f} um "
                f"< RadiusMin={radius_min:.2f} um；请增大 Radius。"
            )

    # 拼成一条连续中心线。首尾各加 1 nm 精确切向点，保证挤出端面
    # 与 PDC 的 out1/out2 端面严格共面，不留 sliver。
    loop_pts = loop_path.points + loop_start
    pts = np.vstack([upper_pts, loop_pts[1:], lower_pts[1:]])
    dir1 = np.array([np.cos(np.radians(th1)), np.sin(np.radians(th1))])
    dir2 = np.array([np.cos(np.radians(th2)), np.sin(np.radians(th2))])
    pts[1] = p1 + 1e-3 * dir1
    pts[-2] = p2 - 1e-3 * dir2

    path = gf.Path(pts, start_angle=th1, end_angle=th2)
    comp << gf.path.extrude(path, width=width_loop, layer=layer)

    comp.add_port("In", port=pc.ports["in2"])
    comp.add_port("Out", port=pc.ports["in1"])
    comp.info["splitter"] = "pulley"
    comp.info["loop_shape"] = shape
    comp.info["loop_radius"] = float(radius)
    comp.info["radius_min"] = float(radius_min)
    comp.info["arm_min_radius"] = float(min(arm_radii.values()))
    comp.info["arm_lead"] = float(lead)
    comp.info["loop_sep"] = float(loop_sep)
    comp.info["angle_couple"] = float(angle_couple)
    comp.info["radius_in"] = float(radius_in)
    return comp


@gf.cell
def OptMMISagnacLoop(
        Width: float = 0.9,
        Radius: float | None = None,
        RadiusMin: float = 50.0,
        LoopShape: str = "circle",
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """优化版 MMI Sagnac 回路反射器（2×2 MMI + 180° 主 loop + Bezier S 弯）。

    端口 ``In`` / ``Out``。

    参数:
        Width: 波导宽度 (µm)。
        Radius: loop 实际使用的弯曲半径 (µm)；``None`` 表示取
            ``1.04 × RadiusMin``（留 4% 设计余量）。
        RadiusMin: 设计允许的最小曲率半径 (µm)，默认 50；改它即可切换平台
            （如 Si 用 10/11），两条 S 弯的实际最小半径也按它校验。
        LoopShape: ``"circle"``（默认，半圆，最紧凑）或 ``"euler"``
            （两端曲率为零，过渡更柔，但占地更大）。
        oplayer: 光学层。
    """
    radius = 1.04 * float(RadiusMin) if Radius is None else float(Radius)
    if radius < RadiusMin:
        raise ValueError(
            f"OptMMISagnacLoop: Radius={radius:.3f} um 小于 "
            f"RadiusMin={RadiusMin:.3f} um"
        )
    return _opt_mmi_sagnac_loop(Width, radius, RadiusMin, oplayer, LoopShape)


# 20° 校弯使用 with_arc_floorplan=False 的 Euler，实例允许落在非整数网格上。
@gf.cell(check_instances=False)
def OptPDCSagnacLoop(
        Width: float = 0.9,
        WidthLoop: float | None = None,
        AngleCouple: float = 20.0,
        RadiusIn: float = 100.0,
        GapCoup: float = 0.3,
        Radius: float | None = None,
        RadiusMin: float = 50.0,
        LoopShape: str = "circle",
        LengthTaper: float = 20.0,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """优化版 pulley 耦合 DC Sagnac 回路反射器。

    用 ``PulleyCoupler2X2`` 做 2×2 分束器。loop 不再“先转直再弯”，
    而是从 out1 的圆弧切向直接起弯，经一条连续 180° 主 loop，
    再直接绕回 out2 的耦合波导；整条中心线一次挤出，没有内部接头。

    参数:
        Width: 分束器窄臂 / 外部 In 端口宽度 (µm)。
        WidthLoop: loop 内波导宽度 (µm)，也是 ``Out`` 端口宽度；
            ``None`` 表示与 ``Width`` 相同。
        AngleCouple: pulley 耦合区张角 (度)。
        RadiusIn: pulley 输入/输出臂半径 (µm)，必须 ≥ ``RadiusMin``。
        GapCoup: pulley 耦合间隙 (µm)。
        Radius: loop 实际使用的弯曲半径 (µm)；``None`` 表示取
            ``1.04 × RadiusMin``（留 4% 设计余量）。
        RadiusMin: 设计允许的最小曲率半径 (µm)，默认 50；改它即可切换平台
            （如 Si 用 10/11），用于校验 loop、pulley 臂和两条过渡 Bezier。
        LoopShape: ``"circle"``（默认，半圆，最紧凑）或 ``"euler"``
            （两端曲率为零，过渡更柔，但占地更大）。
        LengthTaper: ``Width``→``WidthLoop`` 过渡长度 (µm)。
        oplayer: 光学层。

    返回:
        Component，端口 ``In``（in2，180°）/``Out``（in1，180°-AngleCouple）。
    """
    width_loop = float(Width) if WidthLoop is None else float(WidthLoop)
    radius = 1.04 * float(RadiusMin) if Radius is None else float(Radius)
    return _opt_pdc_sagnac_loop(
        float(Width), width_loop, radius, float(RadiusMin),
        float(AngleCouple), float(RadiusIn), float(GapCoup),
        float(LengthTaper), oplayer, LoopShape,
    )


def _add_io_port(c, port, target_orientation: float, width: float,
                 width_io: float | None, length_taper: float,
                 length_lead: float, radius_bend: float,
                 layer: LayerSpec, name: str):
    """在 port 后加转角/直段/taper，并把最终端面暴露为 name。

    ``target_orientation`` 只对 Input/Through 使用，保证它们最终是
    0°/180°；Add/Drop 保持切向角度。
    """
    node = port
    refs = []
    turn = (target_orientation - float(port.orientation) + 180.0) % 360.0 - 180.0
    if abs(turn) > 1e-9:
        bend = c << GfCBendEuler(
            radius=radius_bend, angle=turn, width=width, layer=layer
        )
        bend.connect("o1", node)
        node = bend.ports["o2"]
        refs.append(bend)
    if length_lead > 0:
        lead = c << GfCStraight(width=width, length=length_lead, layer=layer)
        lead.connect("o1", node)
        node = lead.ports["o2"]
        refs.append(lead)
    if width_io is not None and abs(float(width_io) - width) > 1e-12:
        taper = c << gf.c.taper(
            width1=width, width2=float(width_io),
            length=length_taper, layer=layer,
        )
        taper.connect("o1", node)
        node = taper.ports["o2"]
        refs.append(taper)
    c.add_port(name, port=node)
    return refs


def _add_ring_heater(c, radius: float, width: float,
                     heater_config: HeaterConfigClass,
                     direction: str, rotation: float):
    """用库里的 DifferentHeater_local 给主环加调谐结构。

    DifferentHeater_local 以 RingPulley 的坐标约定构造（环心在 (0,R)），
    这里建一个只含 RingL/RingR/RingC 的 frame，加完 heater 后整体下移 R。
    """
    if heater_config is None or str(heater_config.TypeHeater).lower() == "none":
        return None
    frame = gf.Component()
    frame.add_port("RingL", center=(-radius, radius), orientation=90,
                   width=width, layer=LAYER.WG)
    frame.add_port("RingR", center=(radius, radius), orientation=90,
                   width=width, layer=LAYER.WG)
    frame.add_port("RingC", center=(0.0, radius), orientation=90,
                   width=width, layer=LAYER.WG)
    DifferentHeater_local(
        frame, WidthRing=width, RadiusRing=radius,
        DirectionHeater=direction, RotationHeater=rotation,
        HeaterConfig=heater_config,
    )
    heater_ref = c << frame
    heater_ref.movey(-radius)
    for port_name in ("HeatIn", "HeatOut"):
        if port_name in heater_ref.ports:
            c.add_port(port_name, port=heater_ref.ports[port_name])
    return heater_ref


@gf.cell(check_instances=False)
def FeedbackRing(
        RadiusRing: float = 100.0,
        WidthRing: float = 1.0,
        WidthBus: float = 0.9,
        WidthDrop: float = 0.9,
        GapBus: float = 0.3,
        GapDrop: float = 0.3,
        AngleBus: float = -90.0,
        AngleFeedback: float = 90.0,
        AngleCoupleBus: float = 20.0,
        AngleCoupleDrop: float = 20.0,
        LengthBusArm: float = 60.0,
        LengthDropArm: float = 80.0,
        RadiusMirror: float | None = None,
        RadiusMin: float = 50.0,
        MirrorType: str = "euler",
        MirrorAngleCouple: float = 20.0,
        MirrorRadiusIn: float = 100.0,
        MirrorGapCoup: float = 0.3,
        RadiusPortBend: float | None = None,
        LengthPortLead: float = 20.0,
        WidthIO: float | None = 1.0,
        LengthTaper: float = 20.0,
        HeaterConfig: HeaterConfigClass = _FEEDBACK_HEATER,
        DirectionHeater: str = "up",
        RotationHeater: float = 0.0,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """Add-Drop 微环，drop 端带 2×2 Sagnac 回路反射镜和环形加热器。

    结构：
    - 主环：半径 ``RadiusRing``；
    - bus 总线：在 ``AngleBus`` 方向切向耦合，端口 ``Input/Through``；
    - drop 总线：在 ``AngleFeedback`` 方向切向耦合，端口 ``Add``；
    - drop 总线末端接 2×2 Sagnac loop mirror（MMI、pulley DC 或旧版 Euler），
      反射端口 ``Drop``；
    - 主环由 ``DifferentHeater_local`` 加环形加热器，端口
      ``HeatIn/HeatOut``（``HeaterConfig=None`` 或 ``TypeHeater='none'``
      时不加）。

    ``AngleFeedback``：0° 在 +x 侧，90° 在 +y 侧，180° 在 -x 侧。
    Input/Through 会通过小角度 Euler 弯校到 0°/180°；Add/Drop 保持切向角度，
    以保留反馈相位位置调节自由度。

    参数:
        RadiusRing: 主环半径 (µm)。
        WidthRing: 主环宽度 (µm)。
        WidthBus: bus 总线宽度 (µm)。
        WidthDrop: drop 总线宽度 (µm)。
        GapBus: 主环-bus 边到边间隙 (µm)。
        GapDrop: 主环-drop 边到边间隙 (µm)。
        AngleBus: bus 角位置 (度)，默认 -90°。
        AngleFeedback: drop 耦合区角位置 (度)，默认 90°。
        AngleCoupleBus: bus 耦合弧张角 (度)。
        AngleCoupleDrop: drop 耦合弧张角 (度)。
        LengthBusArm: bus 直臂长度 (µm)。
        LengthDropArm: drop 直臂长度 (µm)。
        RadiusMirror: Sagnac 回路弯曲半径 (µm)；``None`` 表示取
            ``1.04 × RadiusMin``。
        RadiusMin: 设计允许的最小曲率半径 (µm)，默认 50；改它即可切换平台
            （如 Si 用 10/11），同时约束主环、Sagnac 回路和 Input/Through 校弯。
        MirrorType: ``"euler"``（旧版 4×90° Euler）、``"mmi"``/``"optimized"``
            （OptMMISagnacLoop）或 ``"pdc"``（OptPDCSagnacLoop）。
        MirrorAngleCouple: pulley DC 分束器的耦合区张角 (度)，仅 ``"pdc"`` 使用。
        MirrorRadiusIn: pulley DC 分束器的输入臂半径 (µm)，仅 ``"pdc"`` 使用。
        MirrorGapCoup: pulley DC 分束器的耦合间隙 (µm)，仅 ``"pdc"`` 使用。
        RadiusPortBend: Input/Through 校 0°/180° 的小弯半径 (µm)；
            ``None`` 表示取 ``1.04 × RadiusMin``。
        LengthPortLead: 转角后的平行直段长度 (µm)。
        WidthIO: 四个外部端口的 taper 外宽；None 表示不加 taper。
        LengthTaper: IO taper 长度 (µm)。
        HeaterConfig: 加热器配置；默认加 TiN (TN) 环形加热器。
        DirectionHeater / RotationHeater: 加热器方向和旋转角。
        oplayer: 光学层。

    返回:
        Component，端口 ``Input/Through/Add/Drop``，可选 ``HeatIn/HeatOut``。
    """
    if RadiusRing <= 0:
        raise ValueError("FeedbackRing: RadiusRing 必须大于 0")
    RadiusMirror = (1.04 * float(RadiusMin) if RadiusMirror is None
                    else float(RadiusMirror))
    RadiusPortBend = (1.04 * float(RadiusMin) if RadiusPortBend is None
                      else float(RadiusPortBend))
    if RadiusRing < RadiusMin:
        raise ValueError(
            f"FeedbackRing: RadiusRing={RadiusRing:.3f} um 小于 "
            f"RadiusMin={RadiusMin:.3f} um"
        )
    if RadiusMirror < RadiusMin:
        raise ValueError(
            f"FeedbackRing: RadiusMirror={RadiusMirror:.3f} um 小于 "
            f"RadiusMin={RadiusMin:.3f} um"
        )
    if RadiusPortBend < RadiusMin:
        raise ValueError(
            f"FeedbackRing: RadiusPortBend={RadiusPortBend:.3f} um 小于 "
            f"RadiusMin={RadiusMin:.3f} um"
        )
    if LengthBusArm <= 0 or LengthDropArm <= 0:
        raise ValueError("FeedbackRing: 直臂长度必须大于 0")
    for name, gap in (("GapBus", GapBus), ("GapDrop", GapDrop)):
        if gap < 0:
            raise ValueError(f"FeedbackRing: {name} 不能为负")

    c = gf.Component()

    # 1) 主环
    ring_ref = c << _full_ring(RadiusRing, WidthRing, oplayer)

    # 2) bus 耦合弧 + 两端直臂 + 90° 端面
    bus_radius = RadiusRing + (WidthRing + WidthBus) / 2.0 + GapBus
    bus_arc = c << _arc_coupler(bus_radius, WidthBus, AngleCoupleBus,
                                AngleBus, oplayer)
    bus_arm1 = c << GfCStraight(width=WidthBus, length=LengthBusArm, layer=oplayer)
    bus_arm1.connect("o1", bus_arc.ports["o1"])
    bus_arm2 = c << GfCStraight(width=WidthBus, length=LengthBusArm, layer=oplayer)
    bus_arm2.connect("o1", bus_arc.ports["o2"])
    bus_refs = [bus_arc, bus_arm1, bus_arm2]
    bus_refs += _add_io_port(
        c, bus_arm1.ports["o2"], 180.0, WidthBus, WidthIO,
        LengthTaper, LengthPortLead, RadiusPortBend, oplayer, "Input",
    )
    bus_refs += _add_io_port(
        c, bus_arm2.ports["o2"], 0.0, WidthBus, WidthIO,
        LengthTaper, LengthPortLead, RadiusPortBend, oplayer, "Through",
    )

    # 3) drop 耦合弧 + 两端直臂
    drop_radius = RadiusRing + (WidthRing + WidthDrop) / 2.0 + GapDrop
    drop_arc = c << _arc_coupler(drop_radius, WidthDrop, AngleCoupleDrop,
                                 AngleFeedback, oplayer)
    drop_arm1 = c << GfCStraight(width=WidthDrop, length=LengthDropArm, layer=oplayer)
    drop_arm1.connect("o1", drop_arc.ports["o1"])
    drop_arm2 = c << GfCStraight(width=WidthDrop, length=LengthDropArm, layer=oplayer)
    drop_arm2.connect("o1", drop_arc.ports["o2"])
    drop_refs = [drop_arc, drop_arm1, drop_arm2]
    # Add 端保留切向角度，只加 taper
    drop_refs += _add_io_port(
        c, drop_arm1.ports["o2"], float(drop_arm1.ports["o2"].orientation),
        WidthDrop, WidthIO, LengthTaper, 0.0, RadiusPortBend, oplayer, "Add",
    )

    # 4) drop 总线末端接 Sagnac loop mirror
    mirror_key = str(MirrorType).lower()
    if mirror_key.startswith("pdc"):
        mirror = c << _opt_pdc_sagnac_loop(
            WidthDrop, WidthDrop, RadiusMirror, RadiusMin,
            MirrorAngleCouple, MirrorRadiusIn, MirrorGapCoup,
            LengthTaper, oplayer,
        )
    elif mirror_key.startswith("opt") or mirror_key.startswith("mmi"):
        mirror = c << _opt_mmi_sagnac_loop(
            WidthDrop, RadiusMirror, RadiusMin, oplayer
        )
    else:
        mirror = c << _euler_sagnac_mirror(WidthDrop, RadiusMirror, oplayer)
    mirror.connect("In", drop_arm2.ports["o2"])
    drop_refs.append(mirror)
    # 反射端口 Drop（保留切向角度，只加 taper）
    drop_refs += _add_io_port(
        c, mirror.ports["Out"], float(mirror.ports["Out"].orientation),
        WidthDrop, WidthIO, LengthTaper, 0.0, RadiusPortBend, oplayer, "Drop",
    )

    # 5) 主环调谐结构（复用库里的环加热器方法）
    heater_ref = _add_ring_heater(
        c, RadiusRing, WidthRing, HeaterConfig,
        DirectionHeater, RotationHeater,
    )

    # 6) 几何自检（只检查光学层；加热器在金属层）
    c.info["angle_bus"] = float(AngleBus)
    c.info["angle_feedback"] = float(AngleFeedback)
    c.info["gap_bus"] = float(GapBus)
    c.info["gap_drop"] = float(GapDrop)
    c.info["radius_mirror"] = float(RadiusMirror)
    return c


@gf.cell(check_instances=False)
def OptFeedbackRing(
        RadiusRing: float = 100.0,
        WidthRing: float = 1.0,
        WidthBus: float = 0.9,
        WidthDrop: float = 0.9,
        GapBus: float = 0.3,
        GapDrop: float = 0.3,
        AngleBus: float = -90.0,
        AngleFeedback: float = 90.0,
        AngleCoupleBus: float = 20.0,
        AngleCoupleDrop: float = 20.0,
        LengthBusArm: float = 60.0,
        LengthDropArm: float = 80.0,
        RadiusMirror: float | None = None,
        RadiusMin: float = 50.0,
        MirrorType: str = "mmi",
        MirrorAngleCouple: float = 20.0,
        MirrorRadiusIn: float = 100.0,
        MirrorGapCoup: float = 0.3,
        RadiusPortBend: float | None = None,
        LengthPortLead: float = 20.0,
        WidthIO: float | None = 1.0,
        LengthTaper: float = 20.0,
        HeaterConfig: HeaterConfigClass = _FEEDBACK_HEATER,
        DirectionHeater: str = "up",
        RotationHeater: float = 0.0,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """优化版 FeedbackRing：Sagnac 回路改用紧凑泪滴形 loop mirror。

    参数与 ``FeedbackRing`` 相同；区别是 loop mirror 的回路采用
    “180° Euler 主弯 + 连续 Bezier S 弯”，而不是 4 个 90° Euler 拼接。
    ``MirrorType="mmi"`` 用 ``OptMMISagnacLoop``；
    ``MirrorType="pdc"`` 用 ``OptPDCSagnacLoop``（pulley 耦合 DC 分束器）。
    """
    return FeedbackRing(
        RadiusRing=RadiusRing, WidthRing=WidthRing,
        WidthBus=WidthBus, WidthDrop=WidthDrop,
        GapBus=GapBus, GapDrop=GapDrop,
        AngleBus=AngleBus, AngleFeedback=AngleFeedback,
        AngleCoupleBus=AngleCoupleBus, AngleCoupleDrop=AngleCoupleDrop,
        LengthBusArm=LengthBusArm, LengthDropArm=LengthDropArm,
        RadiusMirror=RadiusMirror, MirrorType=MirrorType,
        RadiusMin=RadiusMin,
        MirrorAngleCouple=MirrorAngleCouple,
        MirrorRadiusIn=MirrorRadiusIn, MirrorGapCoup=MirrorGapCoup,
        RadiusPortBend=RadiusPortBend, LengthPortLead=LengthPortLead,
        WidthIO=WidthIO, LengthTaper=LengthTaper,
        HeaterConfig=HeaterConfig, DirectionHeater=DirectionHeater,
        RotationHeater=RotationHeater, oplayer=oplayer,
    )


__all__ = [
    "FeedbackRing", "OptFeedbackRing",
    "OptMMISagnacLoop", "OptPDCSagnacLoop",
]
