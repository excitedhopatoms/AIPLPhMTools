"""
工字形微腔组件（GongCavity）。

结构类似汉字"工"，由一条连续闭合波导构成。
波导沿着"工"字的外轮廓走线，形成单条闭合谐振腔。

耦合结构仿照 RaceTrackS 的直线耦合：
在上横顶部放置一条耦合总线，通过 S-bend 靠近腔体进行直线耦合。
"""

import numpy as np
import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec

from .BasicDefine import *
from .Heater import DifferentHeater


def _build_gong_outline_path(LengthHoriz, LengthVert, RadiusBend):
    """
    构建"工"字外轮廓的闭合路径。

    路径从左上角开始，顺时针走完整个外轮廓后闭合。

    几何参数:
        bar_h = LengthVert / 3  （上下横条高度）
        gap_h = LengthVert - 2*bar_h = LengthVert/3  （竖茎高度）
        w_stem = min(LengthHoriz/6, 50)  （竖茎宽度）

    共 24 段:
        segment 1:  上横顶部 (→)
        segment 2:  右上角 (R90 ↓)
        segment 3:  上横右侧边 (↓)
        segment 4:  上横右下角 (R90 ←)
        segment 5:  上横底部右半 (← 到茎)
        segment 6:  茎右侧顶部 (L90 ↓ 进入凹陷)
        segment 7:  茎右侧 (↓)
        segment 8:  茎右侧底部 (L90 → 出凹陷到下横)
        segment 9:  下横顶部右半 (→)
        segment 10: 下横右上角 (R90 ↓)
        segment 11: 下横右侧边 (↓)
        segment 12: 右下角 (R90 ←)
        segment 13: 底部边 (←)
        segment 14: 左下角 (R90 ↑)
        segment 15: 下横左侧边 (↑)
        segment 16: 下横左上角 (R90 →)
        segment 17: 下横顶部左半 (→ 到茎)
        segment 18: 茎左侧底部 (L90 ↑ 进入凹陷)
        segment 19: 茎左侧 (↑)
        segment 20: 茎左侧顶部 (L90 ← 出凹陷到上横)
        segment 21: 上横底部左半 (←)
        segment 22: 上横左下角 (R90 ↑)
        segment 23: 上横左侧边 (↑)
        segment 24: 左上角 (R90 → 闭合)
    """
    bar_h = LengthVert / 3.0
    gap_h = LengthVert - 2 * bar_h
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

    # segment 1: 上横顶部 →
    S(LengthHoriz)
    # segment 2: 右上角 R90 ↓
    R90()
    # segment 3: 上横右侧边 ↓
    S(bar_straight)
    # segment 4: 上横右下角 R90 ←
    R90()
    # segment 5: 上横底部右半 ← 到茎
    S(half_to_stem)
    # segment 6: 茎右侧顶部 L90 ↓ 进入凹陷
    L90()
    # segment 7: 茎右侧 ↓
    S(gap_straight)
    # segment 8: 茎右侧底部 L90 → 出凹陷到下横
    L90()
    # segment 9: 下横顶部右半 →
    S(half_to_stem)
    # segment 10: 下横右上角 R90 ↓
    R90()
    # segment 11: 下横右侧边 ↓
    S(bar_straight)
    # segment 12: 右下角 R90 ←
    R90()
    # segment 13: 底部边 ←
    S(LengthHoriz)
    # segment 14: 左下角 R90 ↑
    R90()
    # segment 15: 下横左侧边 ↑
    S(bar_straight)
    # segment 16: 下横左上角 R90 →
    R90()
    # segment 17: 下横顶部左半 → 到茎
    S(half_to_stem)
    # segment 18: 茎左侧底部 L90 ↑ 进入凹陷
    L90()
    # segment 19: 茎左侧 ↑
    S(gap_straight)
    # segment 20: 茎左侧顶部 L90 ← 出凹陷到上横
    L90()
    # segment 21: 上横底部左半 ←
    S(half_to_stem)
    # segment 22: 上横左下角 R90 ↑
    R90()
    # segment 23: 上横左侧边 ↑
    S(bar_straight)
    # segment 24: 左上角 R90 → 闭合
    R90()

    return path


def _build_gong_heater_path(LengthHoriz, LengthVert, RadiusBend):
    """
    构建"工"字外轮廓的**开口**加热器路径。

    与 _build_gong_outline_path 的 segments 2-24 完全一致，
    即去掉 segment 1（上横顶部直波导 = 耦合区）。
    路径从右上角开始，顺时针覆盖右侧边、底部边、左侧边，
    在左上角结束。

    起点 (o1) → HeatIn（右上角，耦合区右侧），
    终点 (o2) → HeatOut（左上角，耦合区左侧）。
    断口 = 整个上横顶部（耦合区），加热器不覆盖耦合区波导。
    """
    bar_h = LengthVert / 3.0
    gap_h = LengthVert - 2 * bar_h
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
    S(LengthHoriz)
    # segment 14
    R90()
    # segment 15
    S(bar_straight)
    # segment 16
    R90()
    # segment 17
    S(half_to_stem)
    # segment 18
    L90()
    # segment 19
    S(gap_straight)
    # segment 20
    L90()
    # segment 21
    S(half_to_stem)
    # segment 22
    R90()
    # segment 23
    S(bar_straight)
    # segment 24
    R90()
    # 终点: 左上角，断口 = 整个上横顶部（耦合区）

    return path


@gf.cell
def GongCavity(
        WidthRing: float = 1.0,
        WidthNear: float = 0.9,
        RadiusBend: float = 30.0,
        LengthHoriz: float = 300.0,
        LengthVert: float = 350.0,
        GapRing: float = 0.2,
        AngleCouple: float = 20.0,
        Name: str = "GongCavity",
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None
) -> Component:
    """
    创建一个工字形微腔组件（单条闭合曲线），带 RaceTrackS 式直线耦合。

    结构类似汉字"工"，由一条连续闭合波导构成。
    波导沿着"工"字的外轮廓走线，形成单条闭合谐振腔。

    耦合结构仿照 RaceTrackS 的直线耦合：
    在上横顶部放置一条耦合总线，通过 S-bend（欧拉半弯 ±15°）
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
        Component: 生成的工字形微腔组件。

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

    # 构建"工"字外轮廓闭合路径
    path = _build_gong_outline_path(LengthHoriz, LengthVert, RadiusBend)

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

    # ---- 上侧耦合总线 ----
    RC1T = c << gf.path.extrude(RingCoup1T, cross_section=CS_couple)
    RC2T = c << gf.path.extrude(RingCoup2T, cross_section=CS_couple)
    RC2T.connect("o1", other=RC1T.ports["o2"])
    centerT = RC1T.ports["o2"].center
    targetT = np.array([LengthHoriz / 2.0, LengthVert + couple_offset])
    deltaT = targetT - centerT
    RC1T.move(deltaT)
    RC2T.move(deltaT)

    # ---- 下侧耦合总线 ----
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
        heat_path = _build_gong_heater_path(LengthHoriz, LengthVert, RadiusBend)
        HeatCavity = c << DifferentHeater(heat_path, WidthWG=WidthRing, HeaterConfig=HeaterConfig)
        HeatCavity.move((LengthHoriz, LengthVert))
        for port in HeatCavity.ports:
            if 'Heat' in port.name:
                c.add_port(name=port.name, port=port)

    total_length = path.length()
    print(Name + " " + str(total_length))

    return c
