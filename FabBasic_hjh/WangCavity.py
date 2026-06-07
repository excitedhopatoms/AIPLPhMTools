"""
WangCavity - 王字形微腔（单条闭合曲线）
======================================
类似汉字"王"的结构，由一条连续的闭合波导曲线构成。

波导沿着"王"字的外轮廓走线，形成单条闭合谐振腔：
    ┌──────────────────────────┐  ← 上横（顶部）
    │                          │
    │   ┌──────────────────┐   │  ← 中横
    │   │                  │   │
    │   │   ┌──────────┐   │   │  ← 下横
    │   │   │          │   │   │
    │   │   └──────────┘   │   │
    │   │                  │   │
    │   └──────────────────┘   │
    │                          │
    └──────────────────────────┘

耦合结构仿照 RaceTrackS 的直线耦合：
- 上侧水平总线（在上横上方，与之平行），通过 S-bend 靠近腔体
- 下侧水平总线（在下横下方，与之平行），通过 S-bend 靠近腔体
- Input/Through 端口在上侧总线两端，Add/Drop 在下侧总线两端
"""

from .BasicDefine import *
from .Heater import DifferentHeater
from .CouplerMZI import PMZI


def _build_wang_outline_path(LengthHoriz, LengthVert, RadiusBend):
    """
    构建"王"字外轮廓的闭合路径。

    路径沿"王"字外轮廓顺时针走一圈。
    外框转角处右转(-90°)，凹陷处左转(+90°)。

    参数:
        LengthHoriz: 总宽度
        LengthVert: 总高度
        RadiusBend: 弯角半径

    返回:
        gf.Path: 闭合轮廓路径
    """
    bar_h = LengthVert / 5.0
    gap_h = bar_h
    w_stem = min(LengthHoriz / 6.0, 50.0)

    # 验证几何约束
    min_straight = bar_h - 2 * RadiusBend
    min_gap = gap_h - 2 * RadiusBend
    min_half = LengthHoriz / 2.0 - w_stem / 2.0 - 2 * RadiusBend

    if min_straight <= 0 or min_gap <= 0 or min_half <= 0:
        raise ValueError(
            f"RadiusBend ({RadiusBend}) too large. "
            f"bar_h={bar_h:.1f} need >{2*RadiusBend}, "
            f"gap_h={gap_h:.1f} need >{2*RadiusBend}, "
            f"half_width={LengthHoriz/2 - w_stem/2:.1f} need >{2*RadiusBend}"
        )

    path = gf.Path()
    R = RadiusBend
    half_to_stem = LengthHoriz / 2.0 - w_stem / 2.0 - 2 * R
    bar_straight = bar_h - 2 * R
    gap_straight = gap_h - 2 * R

    def S(length):
        """添加直线段"""
        if length > 0:
            path.append(gf.path.straight(length=length))

    def R90():
        """右转90°（顺时针，外框转角）"""
        path.append(gf.path.arc(radius=R, angle=-90))

    def L90():
        """左转90°（逆时针，凹陷转角）"""
        path.append(gf.path.arc(radius=R, angle=90))

    # ============================================================
    # 顺时针遍历"王"字外轮廓，从左上角开始
    # 方向序列: → ↓ ← ↓ → ↓ ← ↓ → ↓ ← ↑ → ↑ ← ↑ → ↑ ← ↑ (闭合)
    # ============================================================

    # 1. 上横顶部: → (0°)
    S(LengthHoriz)
    # 2. 右上角: 右转 → ↓
    R90()
    # 3. 上横右侧边: ↓
    S(bar_straight)
    # 4. 上横右下角: 右转 → ←
    R90()
    # 5. 上横底部(右半): ← 到茎
    S(half_to_stem)
    # 6. 茎右侧顶部: 左转 → ↓ (进入凹陷)
    L90()
    # 7. 茎右侧(上间隙): ↓
    S(gap_straight)
    # 8. 茎右侧中横顶部: 左转 → → (出凹陷到中横)
    L90()
    # 9. 中横顶部(右半): →
    S(half_to_stem)
    # 10. 中横右上角: 右转 → ↓
    R90()
    # 11. 中横右侧边: ↓
    S(bar_straight)
    # 12. 中横右下角: 右转 → ←
    R90()
    # 13. 中横底部(右半): ← 到茎
    S(half_to_stem)
    # 14. 茎右侧中横底部: 左转 → ↓ (进入凹陷)
    L90()
    # 15. 茎右侧(下间隙): ↓
    S(gap_straight)
    # 16. 茎右侧下横顶部: 左转 → → (出凹陷到下横)
    L90()
    # 17. 下横顶部(右半): →
    S(half_to_stem)
    # 18. 下横右上角: 右转 → ↓
    R90()
    # 19. 下横右侧边: ↓
    S(bar_straight)
    # 20. 右下角: 右转 → ←
    R90()
    # 21. 底部边: ←
    S(LengthHoriz)
    # 22. 左下角: 右转 → ↑
    R90()
    # 23. 下横左侧边: ↑
    S(bar_straight)
    # 24. 下横左上角: 右转 → →
    R90()
    # 25. 下横顶部(左半): → 到茎
    S(half_to_stem)
    # 26. 茎左侧下横顶部: 左转 → ↑ (进入凹陷)
    L90()
    # 27. 茎左侧(下间隙): ↑
    S(gap_straight)
    # 28. 茎左侧中横底部: 左转 → ← (出凹陷到中横)
    L90()
    # 29. 中横底部(左半): ←
    S(half_to_stem)
    # 30. 中横左下角: 右转 → ↑
    R90()
    # 31. 中横左侧边: ↑
    S(bar_straight)
    # 32. 中横左上角: 右转 → →
    R90()
    # 33. 中横顶部(左半): → 到茎
    S(half_to_stem)
    # 34. 茎左侧中横顶部: 左转 → ↑ (进入凹陷)
    L90()
    # 35. 茎左侧(上间隙): ↑
    S(gap_straight)
    # 36. 茎左侧上横底部: 左转 → ← (出凹陷到上横)
    L90()
    # 37. 上横底部(左半): ←
    S(half_to_stem)
    # 38. 上横左下角: 右转 → ↑
    R90()
    # 39. 上横左侧边: ↑
    S(bar_straight)
    # 40. 左上角: 右转 → → (闭合)
    R90()

    return path


def _build_wang_heater_path(LengthHoriz, LengthVert, RadiusBend):
    """
    构建"王"字外轮廓的**开口**加热器路径。

    与 _build_wang_outline_path 的 segments 2-40 完全一致，
    即去掉 segment 1（上横顶部直波导 = 耦合区）。
    路径从右上角开始，顺时针覆盖右侧边、底部边、左侧边，
    在左上角结束。

    起点 (o1) → HeatIn（右上角，耦合区右侧），
    终点 (o2) → HeatOut（左上角，耦合区左侧）。
    断口 = 整个上横顶部（耦合区），加热器不覆盖耦合区波导。
    """
    bar_h = LengthVert / 5.0
    gap_h = bar_h
    w_stem = min(LengthHoriz / 6.0, 50.0)

    R = RadiusBend
    half_to_stem = LengthHoriz / 2.0 - w_stem / 2.0 - 2 * R
    bar_straight = bar_h - 2 * R
    gap_straight = gap_h - 2 * R

    path = gf.Path()

    def S(length):
        if length > 0:
            path.append(gf.path.straight(length=length))

    def R90():
        path.append(gf.path.arc(radius=R, angle=-90))

    def L90():
        path.append(gf.path.arc(radius=R, angle=90))

    # 起点: 右上角（segment 1 终点），先右转进入右侧边
    # segment 2
    R90()
    # segment 3
    S(bar_straight)
    # segment 4
    R90()
    # segment 5
    S(half_to_stem)
    # segment 6
    L90()
    # segment 7
    S(gap_straight)
    # segment 8
    L90()
    # segment 9
    S(half_to_stem)
    # segment 10
    R90()
    # segment 11
    S(bar_straight)
    # segment 12
    R90()
    # segment 13
    S(half_to_stem)
    # segment 14
    L90()
    # segment 15
    S(gap_straight)
    # segment 16
    L90()
    # segment 17
    S(half_to_stem)
    # segment 18
    R90()
    # segment 19
    S(bar_straight)
    # segment 20
    R90()
    # segment 21
    S(LengthHoriz)
    # segment 22
    R90()
    # segment 23
    S(bar_straight)
    # segment 24
    R90()
    # segment 25
    S(half_to_stem)
    # segment 26
    L90()
    # segment 27
    S(gap_straight)
    # segment 28
    L90()
    # segment 29
    S(half_to_stem)
    # segment 30
    R90()
    # segment 31
    S(bar_straight)
    # segment 32
    R90()
    # segment 33
    S(half_to_stem)
    # segment 34
    L90()
    # segment 35
    S(gap_straight)
    # segment 36
    L90()
    # segment 37
    S(half_to_stem)
    # segment 38
    R90()
    # segment 39
    S(bar_straight)
    # segment 40
    R90()
    # 终点: 左上角，断口 = 整个上横顶部（耦合区）

    return path


@gf.cell
def WangCavity(
        WidthRing: float = 1.0,
        WidthNear: float = 0.9,
        RadiusBend: float = 30.0,
        LengthHoriz: float = 300.0,
        LengthVert: float = 350.0,
        GapRing: float = 0.2,
        AngleCouple: float = 20.0,
        Name: str = "WangCavity",
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None
) -> Component:
    """
    创建一个王字形微腔组件（单条闭合曲线），带 RaceTrackS 式直线耦合。

    结构类似汉字"王"，由一条连续闭合波导构成。
    波导沿着"王"字的外轮廓走线，形成单条闭合谐振腔。

    耦合结构仿照 RaceTrackS 的直线耦合：
    在左右两个竖直边各放置一条耦合总线，通过 S-bend（欧拉半弯 ±15°）
    靠近腔体进行直线耦合。

    参数:
        WidthRing (float): 主体波导宽度 (um)。
        WidthNear (float): 外部耦合总线波导宽度 (um)。
        RadiusBend (float): 拐角弯曲半径 (um)。
        LengthHoriz (float): 水平总宽度 (um)。
        LengthVert (float): 垂直总高度 (um)。
        GapRing (float): 环与外部耦合总线之间的间隙 (um)。
        AngleCouple (float): （保留参数，直线耦合模式下未使用）。
        Name (str): 组件名称。
        oplayer (LayerSpec): 光学波导层。
        HeaterConfig (HeaterConfigClass): 加热器配置，默认None不添加。

    返回:
        Component: 生成的王字形微腔组件。

    端口:
        TopCenter: 上横波导正中心（参考端口，朝上90°）。
        BottomCenter: 下横波导正中心（参考端口，朝下-90°）。
        Input: 上侧耦合总线左端输入端口。
        Through: 上侧耦合总线右端直通端口。
        Add: 下侧耦合总线左端加入端口。
        Drop: 下侧耦合总线右端下载端口。
        HeatIn, HeatOut: 加热器端口（如有 HeaterConfig）。
    """
    c = gf.Component()

    S_ring = gf.Section(width=WidthRing, layer=oplayer, port_names=["o1", "o2"])
    S_couple = gf.Section(width=WidthNear, layer=oplayer, port_names=["o1", "o2"])
    CS_ring = gf.CrossSection(sections=[S_ring])
    CS_couple = gf.CrossSection(sections=[S_couple])

    # 构建"王"字外轮廓闭合路径
    path = _build_wang_outline_path(LengthHoriz, LengthVert, RadiusBend)

    # 将路径挤出为波导
    C_ring = c << gf.path.extrude(path, cross_section=CS_ring)
    C_ring.move((0, LengthVert))

    # ---- 参考端口：上横/下横波导正中心 ----
    c.add_port(
        name="TopCenter",
        center=(LengthHoriz / 2.0, LengthVert),
        orientation=90,
        width=WidthRing,
        layer=oplayer,
        port_type="optical",
    )
    c.add_port(
        name="BottomCenter",
        center=(LengthHoriz / 2.0, 0.0),
        orientation=-90,
        width=WidthRing,
        layer=oplayer,
        port_type="optical",
    )

    # ---- 耦合总线（仿照 RaceTrackS 的直线耦合结构） ----
    # 耦合波导水平走向（左右），分别与上横、下横平行，通过间隙控制耦合。
    #
    # RaceTrackS 核心逻辑:
    #   rcb1 = euler_Bend_Half(angle=+15°) → 向上弯 (+y)
    #   rcb2 = euler_Bend_Half(angle=-15°) → 向下弯 (-y)
    #   RingCoup1 = rcb2 + rcb1 + rcoup1  → 先下后上 = 净偏移: 向下
    #   RingCoup2 = rcoup2 + rcb1 + rcb2  → 先上后下 = 净偏移: 向上
    #   完整总线: o1 → [S-bend靠近腔] → [直线耦合段] → [S-bend远离腔] → o2
    #
    # 上侧总线 (腔上横在 y=LengthVert, 总线在上方):
    #   耦合段需向下偏移靠近腔 → RingCoup1 = rcb2 + rcb1 + rcoup1
    # 下侧总线 (腔下横在 y=0, 总线在下方):
    #   耦合段需向上偏移靠近腔 → RingCoup1 = rcb1 + rcb2 + rcoup1
    couple_offset = WidthRing / 2 + GapRing + WidthNear / 2
    couple_radius = RadiusBend + couple_offset

    rcoup1 = gf.path.straight(length=LengthHoriz / 2)
    rcoup2 = gf.path.straight(length=LengthHoriz / 2)
    rcb1 = euler_Bend_Half(radius=couple_radius, angle=15, p=0.5)
    rcb2 = euler_Bend_Half(radius=couple_radius, angle=-15, p=0.5)

    # 上侧: S-bend向下偏移 → 耦合段靠近上横
    RingCoup1T = rcb2 + rcb1 + rcoup1
    RingCoup2T = rcoup2 + rcb1 + rcb2

    # 下侧: S-bend向上偏移 → 耦合段靠近下横
    RingCoup1B = rcb1 + rcb2 + rcoup1
    RingCoup2B = rcoup2 + rcb2 + rcb1

    # ---- 上侧耦合总线（水平，在上横上方，与之平行） ----
    RC1T = c << gf.path.extrude(RingCoup1T, cross_section=CS_couple)
    RC2T = c << gf.path.extrude(RingCoup2T, cross_section=CS_couple)
    RC2T.connect("o1", other=RC1T.ports["o2"])
    centerT = RC1T.ports["o2"].center
    targetT = np.array([LengthHoriz / 2.0, LengthVert + couple_offset])
    deltaT = targetT - centerT
    RC1T.move(deltaT)
    RC2T.move(deltaT)

    # ---- 下侧耦合总线（水平，在下横下方，与之平行） ----
    RC1B = c << gf.path.extrude(RingCoup1B, cross_section=CS_couple)
    RC2B = c << gf.path.extrude(RingCoup2B, cross_section=CS_couple)
    RC2B.connect("o1", other=RC1B.ports["o2"])
    centerB = RC1B.ports["o2"].center
    targetB = np.array([LengthHoriz / 2.0, -couple_offset])
    deltaB = targetB - centerB
    RC1B.move(deltaB)
    RC2B.move(deltaB)

    c.add_port(name="Input", port=RC1T.ports["o1"])
    c.add_port(name="Through", port=RC2T.ports["o2"])
    c.add_port(name="Add", port=RC1B.ports["o1"])
    c.add_port(name="Drop", port=RC2B.ports["o2"])

    if HeaterConfig:
        heat_path = _build_wang_heater_path(LengthHoriz, LengthVert, RadiusBend)
        HeatCavity = c << DifferentHeater(heat_path, WidthWG=WidthRing, HeaterConfig=HeaterConfig)
        HeatCavity.move((LengthHoriz, LengthVert))
        for port in HeatCavity.ports:
            if 'Heat' in port.name:
                c.add_port(name=port.name, port=port)

    total_length = path.length()
    print(Name + " " + str(total_length))

    return c


@gf.cell
def ExtCavWang(
        r_euler_false: float = 100,
        r_mzi: float = 100,
        width_ring: float = 1,
        width_single: float = 1,
        width_near: float = 0.91,
        width_mzi_near: float = 1.2,
        width_mzi_ring: float = 2,
        angle_rc: float = 20,
        angle_pmzi: float = 20,
        angle_m2r: float = 45,
        length_bend: float = 50,
        length_t_s2n: float = 200,
        length_taper: float = 200,
        length_bridge: float = 300,
        length_input: float = 230,
        length_cr1: float = 1,
        length_cr2: float = 20,
        gap_rc: float = 0.3,
        gap_mzi: float = 0.5,
        radius_bend: float = 30.0,
        length_horiz: float = 300.0,
        length_vert: float = 350.0,
        direction_io: str = "LR",
        oplayer: LayerSpec = LAYER.WG,
        heater_config_ring: HeaterConfigClass = None,
        heater_config_mzi: HeaterConfigClass = None,
        heater_config_bus: HeaterConfigClass = None,
) -> Component:
    """
    创建一个基于王字形微腔的外腔激光器组件。

    仿照 ExtCavDouRing 结构：
    - PMZI 作为 2x2 耦合器（端口：Input1, Input2, Output1, Output2）
    - WangCavity 替代 DoubleRing 作为频率选择性反射器
    - WangCavity 连接在 PMZI 的 Output2 → Output1 反馈回路中
    - 光路: o1(Input2) → PMZI → Output2 → WangCavity.Input → 谐振 →
            WangCavity.Through → Output1 → PMZI干涉 → Input1 → o2

    参数:
        r_euler_false: 辅助欧拉弯曲半径 (um)。
        r_mzi: MZI弯曲半径 (um)。
        width_ring: 王字形腔波导宽度 (um)。
        width_single: 输入/输出单模波导宽度 (um)。
        width_near: 王字形腔耦合总线宽度 (um)。
        width_mzi_near: MZI耦合器总线宽度 (um)。
        width_mzi_ring: MZI耦合器环宽度 (um)。
        angle_rc: 王字形腔耦合角度 (度，保留参数)。
        angle_pmzi: PMZI耦合角度 (度)。
        angle_m2r: MZI到腔的连接弯曲角度 (度)。
        length_bend: MZI臂弯曲段长度 (um)。
        length_t_s2n: 锥形波导长度 (um)。
        length_taper: 输入/输出锥形波导长度 (um)。
        length_bridge: MZI桥接段长度 (um)。
        length_input: 输入直波导长度 (um)。
        length_cr1: 耦合器到环连接段1长度 (um)。
        length_cr2: 耦合器到环连接段2长度 (um)。
        gap_rc: 王字形腔耦合间隙 (um)。
        gap_mzi: MZI耦合间隙 (um)。
        radius_bend: 王字形腔拐角弯曲半径 (um)。
        length_horiz: 王字形腔水平总宽度 (um)。
        length_vert: 王字形腔垂直总高度 (um)。
        direction_io: 输入输出方向 ("LR" 或 "RL")。
        oplayer: 光学波导层。
        heater_config_ring: 王字形腔加热器配置。
        heater_config_mzi: PMZI加热器配置。
        heater_config_bus: 总线加热器配置。

    返回:
        Component: 生成的王字形外腔激光器组件。

    端口:
        o1, o2: 主光学输入和输出端口。
        WangInput, WangThrough: 王字形腔的上侧耦合端口。
        WangAdd, WangDrop: 王字形腔的下侧耦合端口（监控用）。
        WangHeatIn, WangHeatOut: 王字形腔加热器端口（如有）。
        PMZI*: PMZI加热器端口（如有）。
        Bus*: 总线加热器端口（如有）。
    """
    ec_ref = gf.Component()

    S_near = gf.Section(width=width_near, offset=0, layer=oplayer, port_names=("o1", "o2"))
    CS_near = gf.CrossSection(sections=(S_near,))
    S_NM = gf.Section(width=width_mzi_near, layer=oplayer, port_names=("o1", "o2"))
    S_N = gf.Section(width=width_near, layer=oplayer, port_names=("o1", "o2"))
    X_NM = gf.CrossSection(sections=(S_NM,))
    X_N = gf.CrossSection(sections=(S_N,))

    coupler2x2 = ec_ref << PMZI(
        WidthNear=width_mzi_near, WidthRing=width_mzi_ring, Radius=r_mzi,
        AngleCouple=angle_pmzi, LengthTaper=length_taper, LengthBend=length_bend,
        LengthBridge=length_bridge,
        GapCoup=gap_mzi, oplayer=oplayer, HeaterConfig=heater_config_mzi
    )

    bend_cr1_1 = ec_ref.add_ref_off_grid(GfCBendEuler(radius=r_euler_false, angle=-angle_m2r, cross_section=X_NM))
    bend_cr1_2 = ec_ref.add_ref_off_grid(GfCBendEuler(radius=r_euler_false, angle=angle_m2r, cross_section=X_N))
    str_cr1_1 = ec_ref << GfCStraight(width=width_mzi_near, length=length_cr1, layer=oplayer)
    str_cr1_1.connect("o1", other=coupler2x2.ports["Output1"])
    bend_cr1_1.connect("o1", other=str_cr1_1.ports["o2"])

    tapercoupler1 = ec_ref << gf.c.taper(
        width1=width_mzi_near, width2=width_near,
        length=min(length_t_s2n, 500 * abs(width_mzi_near - width_near) + 1),
        layer=oplayer
    )
    tapercoupler1.connect("o1", other=bend_cr1_1.ports["o2"])

    tapercoupler2 = ec_ref << gf.c.taper(
        width1=width_mzi_ring, width2=width_near,
        length=min(length_t_s2n, 500 * abs(width_mzi_ring - width_near) + 1),
        layer=oplayer
    )
    bend_c2r_path = euler_Bend_Half(angle=-90, radius=r_mzi)
    bend_c2r = ec_ref << gf.path.extrude(bend_c2r_path, width=width_mzi_ring, layer=oplayer)
    bend_c2r.connect("o1", coupler2x2.ports["Output2"])
    tapercoupler2.connect("o1", bend_c2r.ports["o2"])

    wang_ref = WangCavity(
        WidthRing=width_ring, WidthNear=width_near,
        RadiusBend=radius_bend,
        LengthHoriz=length_horiz, LengthVert=length_vert,
        GapRing=gap_rc, AngleCouple=angle_rc,
        oplayer=oplayer, HeaterConfig=heater_config_ring
    )
    wang = ec_ref << wang_ref

    wang.connect("Input", tapercoupler2.ports["o2"])
    wang.movex(length_cr2)

    str_cr2_1 = ec_ref << GfCStraight(width=width_near, length=length_cr2, layer=oplayer)
    str_cr2_1.connect("o1", tapercoupler2.ports["o2"])

    delta1 = np.array(bend_cr1_1.ports["o1"].center) - np.array(bend_cr1_1.ports["o2"].center)
    delta2 = np.array(tapercoupler1.ports["o2"].center) - np.array(wang.ports["Through"].center)
    addlength = abs(delta1[1] - delta2[1]) / np.sin(angle_m2r * np.pi / 180)
    str_tapercoupler = ec_ref << GfCStraight(width=width_near, length=addlength, layer=oplayer)
    str_tapercoupler.connect("o1", other=tapercoupler1.ports["o2"])
    bend_cr1_2.connect("o1", other=str_tapercoupler.ports["o2"])

    str_cr1_2 = ec_ref << GfCStraight(
        width=width_near, layer=oplayer,
        length=abs(-wang.ports["Through"].center[0] + bend_cr1_2.ports["o2"].center[0])
    )
    str_cr1_2.move(bend_cr1_2.ports["o2"].center)

    str_input = list(range(30))
    str_input[0] = ec_ref << gf.c.taper(
        width1=width_mzi_near, width2=width_single,
        length=min(length_taper, abs(width_near - width_single) * 500, 50),
        layer=oplayer
    )
    str_input[0].connect("o1", coupler2x2.ports["Input2"], mirror=True)

    str_output = list(range(30))
    bend_output = list(range(30))
    path_bend_output = euler_Bend_Half(angle=-90, radius=r_mzi)
    bend_output[0] = ec_ref << gf.path.extrude(path_bend_output, layer=oplayer, width=width_mzi_ring)
    bend_output[0].connect("o1", coupler2x2.ports["Input1"])
    str_output[0] = ec_ref << gf.c.taper(
        width1=width_mzi_ring, width2=width_single,
        length=min(length_taper, abs(width_near - width_single) * 500, 50),
        layer=oplayer
    )
    str_output[0].connect("o1", bend_output[0].ports["o2"])

    str_input[1] = ec_ref << GfCStraight(width=width_single, length=length_input, layer=oplayer)
    path_input = gf.path.straight(length=length_input)
    inputh = ec_ref << DifferentHeater(PathHeat=path_input, WidthWG=width_single, HeaterConfig=heater_config_bus)

    if direction_io == "LR":
        str_input[1].connect("o1", str_input[0].ports["o2"])
        ec_ref.add_port("o1", port=str_input[1].ports["o2"])
        ec_ref.add_port("o2", port=str_output[0].ports["o2"])
    elif direction_io == "RL":
        str_input[1].connect("o1", str_output[0].ports["o2"])
        ec_ref.add_port("o1", port=str_input[0].ports["o2"])
        ec_ref.add_port("o2", port=str_input[1].ports["o2"])

    if heater_config_bus is not None and (heater_config_bus.TypeHeater != "None") and (heater_config_bus.TypeHeater != "none"):
        inputh.connect("HeatIn", str_input[1].ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True, allow_type_mismatch=True)
        inputh.mirror_x(inputh.ports["HeatIn"].center[0])

    ec_ref.add_port("WangInput", port=wang.ports["Input"])
    ec_ref.add_port("WangThrough", port=wang.ports["Through"])
    ec_ref.add_port("WangAdd", port=wang.ports["Add"])
    ec_ref.add_port("WangDrop", port=wang.ports["Drop"])

    for port in wang.ports:
        if "Heat" in port.name:
            ec_ref.add_port("Wang" + port.name, port=wang.ports[port.name])
    for port in coupler2x2.ports:
        if "Heat" in port.name:
            ec_ref.add_port("PMZI" + port.name, port=coupler2x2.ports[port.name])
    for port in inputh.ports:
        if "Heat" in port.name:
            ec_ref.add_port("Bus" + port.name, port=inputh.ports[port.name])

    ec_ref = remove_layer(ec_ref, layer=(512, 8))
    add_labels_to_ports(ec_ref)
    return ec_ref
