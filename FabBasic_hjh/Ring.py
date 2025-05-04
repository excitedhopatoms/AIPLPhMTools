import gdsfactory as gf
from gdsfactory.typings import LayerSpec, Component
from .BasicDefine import euler_Bend_Half, add_labels_to_ports,LAYER
from .Heater import SnakeHeater,DifferentHeater

import numpy as np

# %% RingPulley1:straight pulley
@gf.cell
def RingPulley(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        RadiusRing: float = 100,
        GapRing: float = 1,
        AngleCouple: float = 20,
        IsHeat: bool = False,
        IsAD: bool = True,
        Name: str = "Ring_Pullry",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个通用环形耦合器，支持加热电极和 Add-Drop 端口。

    参数：
        WidthRing: 环形波导的宽度。
        WidthNear: 耦合波导的宽度。
        WidthHeat: 加热电极的宽度。
        RadiusRing: 环形波导的半径。
        GapRing: 环形波导与耦合波导之间的间距。
        AngleCouple: 耦合角度。
        IsHeat: 是否添加加热电极。
        IsAD: 是否添加 Add-Drop 端口。
        Name: 组件的名称。
        oplayer: 光学层的定义。
        heatlayer: 加热层的定义。

    返回：
        Component: 生成的环形耦合器组件。

    端口：
        Input: 输入端口。
        Through: 直通端口。
        RingL: 左侧环形端口。
        RingR: 右侧环形端口。
        Add: Add 端口（仅在 IsAD=True 时存在）。
        Drop: Drop 端口（仅在 IsAD=True 时存在）。
        HeatIn: 加热输入端口（仅在 IsHeat=True 时存在）。
        HeatOut: 加热输出端口（仅在 IsHeat=True 时存在）。
    """
    c = RingPulleyT1(
        WidthRing= WidthRing,
        WidthNear= WidthNear,
        WidthHeat = WidthHeat,
        RadiusRing= RadiusRing,
        GapRing= GapRing,
        AngleCouple= AngleCouple,
        IsHeat= IsHeat,
        IsAD= IsAD,
        Name= Name,
        oplayer= oplayer,
        heatlayer=heatlayer,
        TypeHeater="default",
    )
    return c

# %% RingPulley1DC: 不同耦合器
@gf.cell
def RingPulley1DC(
        WidthRing: float = 1,
        WidthNear1: float = 0.9,
        WidthNear2: float = 2,
        WidthHeat: float = 2,
        RadiusRing: float = 100,
        GapRing1: float = 1,
        GapRing2: float = 2,
        AngleCouple1: float = 20,
        AngleCouple2: float = 40,
        IsHeat: bool = False,
        Name: str = "Ring_Pullry",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个具有不同耦合器的环形结构。

    参数：
        WidthRing: 环形波导的宽度。
        WidthNear1: 上耦合波导的宽度。
        WidthNear2: 下耦合波导的宽度。
        WidthHeat: 加热电极的宽度。
        RadiusRing: 环形波导的半径。
        GapRing1: 上耦合波导与环形波导之间的间距。
        GapRing2: 下耦合波导与环形波导之间的间距。
        AngleCouple1: 上耦合角度。
        AngleCouple2: 下耦合角度。
        IsHeat: 是否添加加热电极。
        Name: 组件的名称。
        oplayer: 光学层的定义。
        heatlayer: 加热层的定义。

    返回：
        Component: 生成的环形耦合器组件。

    端口：
        Input: 输入端口。
        Through: 直通端口。
        RingL: 左侧环形端口。
        RingR: 右侧环形端口。
        Add: Add 端口。
        Drop: Drop 端口。
        HeatIn: 加热输入端口（仅在 IsHeat=True 时存在）。
        HeatOut: 加热输出端口（仅在 IsHeat=True 时存在）。
    """
    c = RingPulleyT1(
        WidthRing= WidthRing,
        WidthNear= WidthNear1,
        WidthNear2=WidthNear2,
        WidthHeat = WidthHeat,
        RadiusRing= RadiusRing,
        GapRing= GapRing1,
        GapRing2=GapRing2,
        AngleCouple= AngleCouple1,
        AngleCouple2=AngleCouple2,
        IsHeat= IsHeat,
        Name= Name,
        oplayer= oplayer,
        heatlayer=heatlayer,
        TypeHeater="default",
    )
    return c

# %% RingPulley1HS: 加热侧
@gf.cell
def RingPulley1HS(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        WidthRoute: float = 30,
        DeltaHeat: float = -10,
        GapRoute: float = 50,
        RadiusRing: float = 1000,
        GapRing: float = 1,
        AngleCouple: float = 20,
        IsAD: bool = True,
        Name: str = "Ring_Pullry",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个带有加热侧的环形结构。

    参数：
        WidthRing: 环形波导的宽度。
        WidthNear: 耦合波导的宽度。
        WidthHeat: 加热电极的宽度。
        WidthRoute: 加热电极路由的宽度。
        DeltaHeat: 加热电极的偏移量。
        GapRoute: 加热电极路由的间距。
        RadiusRing: 环形波导的半径。
        GapRing: 环形波导与耦合波导之间的间距。
        AngleCouple: 耦合角度。
        IsAD: 是否添加 Add-Drop 端口。
        Name: 组件的名称。
        oplayer: 光学层的定义。
        heatlayer: 加热层的定义。

    返回：
        Component: 生成的环形耦合器组件。

    端口：
        Input: 输入端口。
        Through: 直通端口。
        RingL: 左侧环形端口。
        RingR: 右侧环形端口。
        Add: Add 端口（仅在 IsAD=True 时存在）。
        Drop: Drop 端口（仅在 IsAD=True 时存在）。
        HeatIn: 加热输入端口。
        HeatOut: 加热输出端口。
    """
    c = RingPulleyT1(
        WidthRing= WidthRing,
        WidthNear= WidthNear,
        WidthHeat = WidthHeat,
        RadiusRing= RadiusRing,
        GapRing= GapRing,
        GapHeat= DeltaHeat,
        AngleCouple= AngleCouple,
        IsAD= IsAD,
        IsHeat=True,
        Name= Name,
        oplayer= oplayer,
        heatlayer=heatlayer,
        TypeHeater="side",
    )
    return c

# %% RingPulley1HSn: 加热蛇形
@gf.cell
def RingPulley1HSn(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        WidthRoute: float = 30,
        DeltaHeat: float = 0,
        GapHeat: float = 1,
        RadiusRing: float = 1000,
        GapRing: float = 1,
        AngleCouple: float = 20,
        IsAD: bool = True,
        Name: str = "Ring_Pullry",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个带有蛇形加热器的环形结构。

    参数：
        WidthRing: 环形波导的宽度。
        WidthNear: 耦合波导的宽度。
        WidthHeat: 加热电极的宽度。
        WidthRoute: 加热电极路由的宽度。
        DeltaHeat: 加热电极的偏移量。
        GapHeat: 加热电极与环形波导之间的间距。
        RadiusRing: 环形波导的半径。
        GapRing: 环形波导与耦合波导之间的间距。
        AngleCouple: 耦合角度。
        IsAD: 是否添加 Add-Drop 端口。
        Name: 组件的名称。
        oplayer: 光学层的定义。
        heatlayer: 加热层的定义。

    返回：
        Component: 生成的环形耦合器组件。

    端口：
        Input: 输入端口。
        Through: 直通端口。
        RingL: 左侧环形端口。
        RingR: 右侧环形端口。
        Add: Add 端口（仅在 IsAD=True 时存在）。
        Drop: Drop 端口（仅在 IsAD=True 时存在）。
        HeatIn: 加热输入端口。
        HeatOut: 加热输出端口。
    """
    c = RingPulleyT1(
        WidthRing=WidthRing,
        WidthNear=WidthNear,
        WidthHeat=WidthHeat,
        RadiusRing=RadiusRing,
        GapRing=GapRing,
        GapHeat=DeltaHeat,
        AngleCouple=AngleCouple,
        IsAD=IsAD,
        Name=Name,
        oplayer=oplayer,
        heatlayer=heatlayer,
        TypeHeater="snake",
        IsHeat=True,
    )
    return c


# %% RingPulley2: 滑轮输入输出
@gf.cell
def RingPulley2(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        RadiusRing: float = 100,
        GapRing: float = 1,
        AngleCouple: float = 20,
        IsHeat: bool = False,
        Name: str = "Ring_Pullry2",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """创建一个带有滑轮输入输出的环形结构。"""
    c = RingPulleyT2(WidthRing,WidthNear,WidthHeat,RadiusRing,0,GapRing,0,AngleCouple,IsHeat,"default",Name,oplayer,heatlayer)
    return c

# %% RingPulley2ES: 滑轮输入输出 + 电子线路
@gf.cell
def RingPulley2ES(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthEle: float = 8,
        RadiusRing: float = 100,
        GapRing: float = 1,
        DeltaEle: float = 6,
        AngleCouple: float = 20,
        Name: str = "Ring_Pullry2",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """创建一个带有滑轮输入输出和电子线路的环形结构。"""
    c = RingPulleyT2(WidthRing, WidthNear, WidthEle, RadiusRing, DeltaEle, GapRing, 0, AngleCouple, True, "bothside", Name,oplayer, heatlayer)
    return c

# %% RingPulley3: 大角度耦合器
@gf.cell
def RingPulley3(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        RadiusRing: float = 100,
        GapRing: float = 1,
        AngleCouple: float = 20,
        IsHeat: bool = False,
        Name: str = "Ring_Pullry2",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """创建一个带有大角度耦合器的环形结构。"""
    c = gf.Component(Name)
    # 光学部分
    ring_path90 = gf.path.arc(radius=RadiusRing, angle=90)
    ring_path_all = ring_path90 + ring_path90 + ring_path90 + ring_path90
    ring_comp = c << gf.path.extrude(ring_path_all, width=WidthRing, layer=oplayer)
    couple_path_ring = gf.path.arc(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2, angle=AngleCouple / 2)
    couple_path_euler = euler_Bend_Half(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2, angle=(180 - AngleCouple) / 2, p=0.5)
    couple_path = couple_path_ring + couple_path_euler
    upcouple_comp1 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)
    upcouple_comp1.connect("o1", destination=ring_comp.ports["o1"], allow_width_mismatch=True).movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)
    upcouple_comp2.connect("o1", destination=ring_comp.ports["o1"], allow_width_mismatch=True).movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2.rotate(center="o1", angle=180).mirror_y(port_name="o1")
    c.add_port(name="Input", port=upcouple_comp2.ports["o2"])
    c.add_port(name="Through", port=upcouple_comp1.ports["o2"])
    c.add_port(name="RingL", port=ring_comp.ports["o1"], center=[-RadiusRing, RadiusRing], orientation=90)
    c.add_port(name="RingR", port=ring_comp.ports["o1"], center=[RadiusRing, RadiusRing], orientation=90)
    return c

# %% RingPulley4: 大角度耦合器
@gf.cell
def RingPulley4(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        RadiusRing: float = 100,
        GapRing: float = 1,
        AngleCouple: float = 20,
        IsHeat: bool = False,
        Name: str = "Ring_Pullry2",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """创建一个带有大角度耦合器的环形结构。"""
    c = gf.Component(Name)
    # 光学部分
    ring_path90 = gf.path.arc(radius=RadiusRing, angle=90)
    ring_path_all = ring_path90 + ring_path90 + ring_path90 + ring_path90
    ring_comp = c << gf.path.extrude(ring_path_all, width=WidthRing, layer=oplayer)
    couple_path_ring = gf.path.arc(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2, angle=AngleCouple / 2)
    couple_path_euler_up = euler_Bend_Half(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2,
                                           angle=(270 - AngleCouple) / 2, p=1)
    couple_path_euler_down = euler_Bend_Half(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2,
                                             angle=(270 - AngleCouple) / 2 - 270, p=0.5)
    couple_path_up = couple_path_ring + couple_path_euler_up
    couple_path_down = couple_path_ring + couple_path_euler_down
    upcouple_comp1 = c << gf.path.extrude(couple_path_down, width=WidthNear, layer=oplayer)
    upcouple_comp1.connect("o1", destination=ring_comp.ports["o1"], allow_width_mismatch=True).movey(
        2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2 = c << gf.path.extrude(couple_path_up, width=WidthNear, layer=oplayer)
    upcouple_comp2.connect("o1", destination=ring_comp.ports["o1"], allow_width_mismatch=True).movey(
        2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2.rotate(center="o1", angle=180).mirror_y(port_name="o1")
    c.add_port(name="Input", port=upcouple_comp2.ports["o2"])
    c.add_port(name="Through", port=upcouple_comp1.ports["o2"])
    c.add_port(name="RingL", port=ring_comp.ports["o1"], center=[-RadiusRing, RadiusRing], orientation=90)
    c.add_port(name="RingR", port=ring_comp.ports["o1"], center=[RadiusRing, RadiusRing], orientation=90)
    return c

# %% RingFinger: 山形环形结构
@gf.cell
def RingFinger(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        RadiusCouple: float = 150,
        RadiusSide: float = 100,
        LengthCouple: float = 100,
        LengthSide: float = 100,
        LengthConnect: float = 180,
        GapRing: float = 1,
        AngleCouple: float = 20,
        AngleSide: float = 180,
        IsHeat: bool = False,
        Name: str = "RingFinger",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """创建一个山形环形结构。"""
    c = gf.Component(Name)
    # 光学部分
    S_ring = gf.Section(width=WidthRing, layer=oplayer, port_names=["o1", "o2"])
    S_couple = gf.Section(width=WidthNear, layer=oplayer, port_names=["o1", "o2"])
    CS_ring = gf.CrossSection(sections=[S_ring])
    CS_couple = gf.CrossSection(sections=[S_couple])
    path_arc_ring = gf.path.arc(radius=RadiusCouple, angle=45)
    path_str_ring = gf.path.straight(length=LengthCouple)
    path_euler_ring = euler_Bend_Half(radius=RadiusCouple, angle=45)
    path_arc_couple = gf.path.arc(radius=RadiusCouple + WidthRing / 2 + GapRing + WidthNear / 2, angle=AngleCouple / 2)
    path_euler_couple = gf.path.euler(radius=RadiusCouple + WidthRing / 2 + GapRing + WidthNear / 2, angle=-AngleCouple / 2)
    path_euler_side = gf.path.euler(radius=RadiusSide, angle=-AngleSide)
    path_euler_side2 = gf.path.euler(radius=RadiusSide, angle=AngleSide)
    path_str_side = gf.path.straight(length=LengthSide)
    path_arc_connect = gf.path.arc(radius=RadiusSide, angle=90)
    path_str_connect = gf.path.straight(length=LengthConnect)
    path_ring = path_arc_ring + path_euler_ring + path_str_ring
    path_side = path_euler_side + path_str_side
    path_side2 = path_euler_side2 + path_str_side
    path_couple = path_arc_couple + path_euler_couple
    path_connect = path_str_connect + path_arc_connect
    path_half = path_ring + path_side + path_side2 + path_connect
    CcoupleL = c << gf.path.extrude(path_couple, cross_section=CS_couple)
    CcoupleR = c << gf.path.extrude(path_couple, cross_section=CS_couple)
    ChalfL = c << gf.path.extrude(path_half, cross_section=CS_ring)
    ChalfL.mirror_y("o1")
    ChalfR = c << gf.path.extrude(path_half, cross_section=CS_ring)
    ChalfR.connect("o1", destination=ChalfL.ports["o1"])
    length_con = abs(ChalfL.ports["o2"].center[0] - ChalfR.ports["o2"].center[0])
    str_connect = c << gf.c.straight(width=WidthRing, length=length_con, layer=oplayer)
    str_connect.connect("o1", destination=ChalfL.ports["o2"])
    CcoupleL.connect("o1", destination=ChalfR.ports["o1"], allow_width_mismatch=True).movey(GapRing + WidthNear / 2 + WidthRing / 2).mirror_y("o1")
    CcoupleR.connect("o1", destination=ChalfL.ports["o1"], allow_width_mismatch=True).movey(GapRing + WidthNear / 2 + WidthRing / 2)
    print(Name + " " + str(path_half.length() * 2 + length_con))
    c.add_port(name="Input", port=CcoupleL.ports["o2"])
    c.add_port(name="Through", port=CcoupleR.ports["o2"])
    c.add_port(name="Con1", port=str_connect.ports["o1"])
    c.add_port(name="Con2", port=str_connect.ports["o2"])
    return c

# %% RingPulleyT1: 通用环形耦合器
@gf.cell
def RingPulleyT1(
        WidthRing: float = 1.0,
        WidthNear: float = 0.9,
        WidthHeat: float = 2.0,
        WidthTrench: float = 2,
        WidthRoute: float = 20,
        RadiusRing: float = 100.0,
        WidthNear2: float = None,
        GapRing2: float = None,
        AngleCouple2: float = None,
        DeltaHeat: float = 0,
        GapRing: float = 1.0,
        GapHeat: float = 2.0,
        GapTrench: float = 10,
        AngleCouple: float = 20.0,
        IsHeat: bool = True,
        TypeHeater: str = "default",
        IsAD: bool = True,
        IsTrench: bool = False,
        DirectionHeater: str = "up",
        Name: str = "Ring_Pullry",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        trelayer: LayerSpec = (3, 0)
) -> Component:
    """
    创建一个通用环形耦合器，支持不同类型的加热电极和 Add-Drop 端口。
    耦合为pulley耦合，且左右为同一水平出射（直pulley耦合）

    参数：
        WidthRing: 环形波导的宽度。（单位：um）
        WidthNear: 耦合波导的宽度。（单位：um）
        WidthHeat: 加热电极的宽度。（单位：um）
        RadiusRing: 环形波导的半径。（单位：um）
        DeltaHeat: 加热电极中心距离波导中心，正在外，负在内（单位：um）
        GapRing: 环形波导与耦合波导之间的间距。（单位：um）
        GapHeat: 加热电极间隔，对蛇形而言是弯过来的差别（单位：um）
        AngleCouple: 耦合角度。
        IsHeat: 是否添加加热电极。
        TypeHeater: 加热电极类型，支持 "default"（默认）、"snake"（蛇形）、"side"（侧边）、"bothside"（两侧）
        IsAD: 是否添加 Add-Drop 端口。
        DirectionHeater: Heater 出口的方向，向上或者向下
        Name: 组件的名称。
        oplayer: 光学层的定义。
        heatlayer: 加热层的定义。
        trelayer: 热隔离刻蚀层的定义。
        WidthNear2: 如果两侧的耦合不同，则可以用此参数指定另一侧的耦合波导宽度。（单位：um）
        GapRing2: 如果两侧的耦合不同，则可以用此参数指定另一侧的环形波导与耦合波导之间的间距。（单位：um）
        AngleCouple2: 如果两侧的耦合不同，则可以用此参数指定另一侧的耦合角度。
    返回：
        Component: 生成的环形耦合器组件。
    端口：
        Input: 输入端口。
        Through: 直通端口。
        RingL: 左侧环形端口。
        RingR: 右侧环形端口。
        Add: Add 端口（仅在 IsAD=True 时存在）。
        Drop: Drop 端口（仅在 IsAD=True 时存在）。
        HeatIn: 加热输入端口（仅在 IsHeat=True 时存在）。
        HeatOut: 加热输出端口（仅在 IsHeat=True 时存在）。
    """
    c = gf.Component(Name)  # 创建一个组件实例
    # 考虑是否对称耦合
    if WidthNear2 is None and GapRing2 is None and AngleCouple2 is None:
        WidthNear2 = WidthNear
        GapRing2 = GapRing
        AngleCouple2 = AngleCouple
    else:
        if WidthNear2 is None:
            WidthNear2 = WidthNear
        if GapRing2 is None:
            GapRing2 = GapRing
        if AngleCouple2 is None:
            AngleCouple2 = AngleCouple
        IsAD=True
    # 光学部分：创建环形波导
    ring_path90 = gf.path.arc(radius=RadiusRing, angle=90)  # 创建 90 度的圆弧路径
    ring_path_all = ring_path90 + ring_path90 + ring_path90 + ring_path90  # 拼接成完整的环形路径
    ring_comp = c << gf.path.extrude(ring_path_all, width=WidthRing, layer=oplayer)  # 将路径转换为波导

    # 创建耦合波导
    couple_path_ring = gf.path.arc(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2, angle=AngleCouple / 2)  # 创建耦合圆弧路径
    couple_path_euler = euler_Bend_Half(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2, angle=-AngleCouple / 2)  # 创建欧拉弯曲路径
    couple_path = couple_path_ring + couple_path_euler  # 拼接成完整的耦合路径

    # 上耦合波导
    upcouple_comp1 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)  # 创建上耦合波导
    upcouple_comp1.connect("o1", destination=ring_comp.ports["o1"], allow_width_mismatch=True).movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)  # 连接并移动
    upcouple_comp2 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)  # 创建上耦合波导
    upcouple_comp2.connect("o1", destination=ring_comp.ports["o1"], allow_width_mismatch=True).movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)  # 连接并移动
    upcouple_comp2.rotate(center="o1", angle=180).mirror_y(port_name="o1")  # 旋转和镜像
    c.add_port(name="Input", port=upcouple_comp2.ports["o2"])  # 添加输入端口
    c.add_port(name="Through", port=upcouple_comp1.ports["o2"])  # 添加直通端口

    # 环形波导端口
    c.add_port(name="RingL", port=ring_comp.ports["o1"], center=[-RadiusRing, RadiusRing], orientation=90)  # 添加左侧环形端口
    c.add_port(name="RingR", port=ring_comp.ports["o1"], center=[RadiusRing, RadiusRing], orientation=90)  # 添加右侧环形端口
    c.add_port(name="RingC", port=ring_comp.ports["o1"], center=[0, RadiusRing], orientation=90)  # 添加中间环形端口
    # Add-Drop 端口
    if IsAD:
        couple_path_ring2 = gf.path.arc(radius=RadiusRing + GapRing2 + WidthNear2 / 2 + WidthRing / 2,
                                       angle=AngleCouple2 / 2)  # 创建耦合圆弧路径
        couple_path_euler2 = euler_Bend_Half(radius=RadiusRing + GapRing2 + WidthNear2 / 2 + WidthRing / 2,
                                            angle=-AngleCouple2 / 2)  # 创建欧拉弯曲路径
        couple_path2 = couple_path_ring2 + couple_path_euler2  # 拼接成完整的耦合路径
        downcouple_comp1 = c << gf.path.extrude(couple_path2, width=WidthNear2, layer=oplayer)  # 创建下耦合波导
        downcouple_comp1.connect("o1", destination=ring_comp.ports["o1"], allow_width_mismatch=True).movey(-GapRing2 - WidthNear2 / 2 - WidthRing / 2)  # 连接并移动
        downcouple_comp1.mirror_y(port_name="o1")  # 镜像
        downcouple_comp2 = c << gf.path.extrude(couple_path2, width=WidthNear2, layer=oplayer)  # 创建下耦合波导
        downcouple_comp2.connect("o1", destination=ring_comp.ports["o1"], allow_width_mismatch=True).movey(-GapRing2 - WidthNear2 / 2 - WidthRing / 2)  # 连接并移动
        downcouple_comp2.rotate(center="o1", angle=180)  # 旋转
        c.add_port(name="Add", port=downcouple_comp1.ports["o2"])  # 添加 Add 端口
        c.add_port(name="Drop", port=downcouple_comp2.ports["o2"])  # 添加 Drop 端口

    # 加热部分
    if IsHeat:
        DifferentHeater_local(c,WidthHeat,WidthRing,DeltaHeat,GapHeat,RadiusRing,heatlayer,TypeHeater,DirectionHeater=DirectionHeater,Name = Name + "Heater",WidthRoute=WidthRoute)
    if IsTrench:
        ring_tr = c << gf.c.ring(width=WidthTrench,layer=trelayer,radius=RadiusRing-WidthRing/2-WidthTrench/2-GapTrench)
        ring_tr.movey(RadiusRing)
    add_labels_to_ports(c)
    return c
# %% RingPulleyT2: 通用环形耦合器2
@gf.cell
def RingPulleyT2(
        WidthRing: float = 1.0,
        WidthNear: float = 0.9,
        WidthHeat: float = 2.0,
        RadiusRing: float = 100.0,
        DeltaHeat: float = 0,
        GapRing: float = 1.0,
        GapHeat: float = 2.0,
        AngleCouple: float = 20.0,
        IsHeat: bool = True,
        TypeHeater: str = "default",
        Name: str = "Ring_Pullry",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个带有滑轮输入输出的环形结构，支持热电极和 Add-Drop 端口。
    耦合为pulley耦合，且左右为垂直的出射（弯曲pulley耦合）

    参数：
        WidthRing: 环形波导的宽度。（单位：um）
        WidthNear: 耦合波导的宽度。（单位：um）
        WidthHeat: 加热电极的宽度。（单位：um）
        RadiusRing: 环形波导的半径。（单位：um）
        GapRing: 环形波导与耦合波导之间的间距。（单位：um）
        AngleCouple: 耦合角度。
        IsHeat: 是否添加加热电极。
        TypeHeater: 加热电极类型，支持 "default"（默认）、"snake"（蛇形）、"side"（侧边）、"bothside"（两侧）
        IsAD: 是否添加 Add-Drop 端口。
        Name: 组件的名称。
        oplayer: 光学层的定义。
        heatlayer: 加热层的定义。

    返回：
        Component: 生成的环形滑轮组件。
    端口：
        Input: 输入端口。
        Through: 直通端口。
        RingL: 左侧环形端口。
        RingR: 右侧环形端口。
        Add: Add 端口（仅在 IsAD=True 时存在）。
        Drop: Drop 端口（仅在 IsAD=True 时存在）。
        HeatIn: 加热输入端口（仅在 IsHeat=True 时存在）。
        HeatOut: 加热输出端口（仅在 IsHeat=True 时存在）。
    """
    c = gf.Component(Name)

    # 光学部分：创建环形波导
    ring_path90 = gf.path.arc(radius=RadiusRing, angle=90)
    ring_path_all = ring_path90 + ring_path90 + ring_path90 + ring_path90
    ring_comp = c << gf.path.extrude(ring_path_all, width=WidthRing, layer=oplayer)

    # 光学部分：创建耦合波导
    couple_path_ring = gf.path.arc(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2, angle=AngleCouple / 2)
    couple_path_euler = euler_Bend_Half(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2, angle=(90 - AngleCouple) / 2, p=1)
    couple_path = couple_path_ring + couple_path_euler
    upcouple_comp1 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)
    upcouple_comp1.connect("o1", destination=ring_comp.ports["o1"], allow_width_mismatch=True).movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)
    upcouple_comp2.connect("o1", destination=ring_comp.ports["o1"], allow_width_mismatch=True).movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2.rotate(center="o1", angle=180).mirror_y(port_name="o1")

    # 添加光学端口
    c.add_port(name="Input", port=upcouple_comp2.ports["o2"])
    c.add_port(name="Through", port=upcouple_comp1.ports["o2"])
    c.add_port(name="RingL", port=ring_comp.ports["o1"], center=[-RadiusRing, RadiusRing], orientation=90)
    c.add_port(name="RingR", port=ring_comp.ports["o1"], center=[RadiusRing, RadiusRing], orientation=90)
    c.add_port(name="RingD", port=ring_comp.ports["o1"],orientation=0)
    c.add_port(name="RingU", port=ring_comp.ports["o1"], center=[0, 2*RadiusRing])
    c.add_port(name="RingC", port=ring_comp.ports["o1"], center=[0, RadiusRing])
    # 添加加热电极
    if IsHeat:
        DifferentHeater_local(c,WidthHeat,WidthRing,DeltaHeat,GapHeat,RadiusRing,heatlayer,TypeHeater,DirectionHeater="up",Name = Name + "Heater")
    add_labels_to_ports(c)
    return c

# %% different heater
@gf.cell
def DifferentHeater_local(
        c:Component = None,
        WidthHeat:float = 1,
        WidthRing:float = 1,
        DeltaHeat:float = 2,
        GapHeat:float = 3,
        RadiusRing: float = 100.0,
        heatlayer:LayerSpec = LAYER.M1,
        TypeHeater:str = "default",
        DirectionHeater: str = "down",
        Name:str = "Heater",
        WidthRoute = 20,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
)->Component:
    """
    创建一个加热电极组件，支持多种加热电极类型和方向。
    加热电极可以添加到环形波导的左侧或右侧，并根据类型生成不同的形状。

    参数：
        c: 父组件，加热电极将添加到该组件中。
        WidthHeat: 加热电极的宽度（单位：um）。
        WidthRing: 环形波导的宽度（单位：um）。
        DeltaHeat: 加热电极中心距离波导中心的偏移量（单位：um）。
        GapHeat: 加热电极之间的间距（单位：um）。
        RadiusRing: 环形波导的半径（单位：um）。
        heatlayer: 加热层的定义。
        TypeHeater: 加热电极类型，支持 "default"（默认）、"snake"（蛇形）、"side"（侧边）、"bothside"（两侧）。
        DirectionHeater: 加热电极出口的方向，支持 "up"（向上）或 "down"（向下）。
        Name: 组件名称。

    返回：
        Component: 生成的加热电极组件。

    端口：
        HeatIn: 加热输入端口。
        HeatOut: 加热输出端口。
        RingL: 左侧环形端口（仅在某些加热类型中存在）。
    """
    h = gf.Component(Name + "Heater")
    if TypeHeater == "default":
        # 默认加热电极
        heat_path = gf.path.arc(radius=RadiusRing, angle=60)  # 创建加热电极路径
        heatout_path1 = euler_Bend_Half(radius=RadiusRing / 2, angle=30)  # 创建欧拉弯曲路径
        heatout_path2 = euler_Bend_Half(radius=20, angle=-60)  # 创建欧拉弯曲路径
        heatL_comp1 = h << gf.path.extrude(heat_path + heatout_path2, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp1.connect("o1", c.ports["RingL"], allow_layer_mismatch=True).mirror_x("o1")  # 连接并镜像
        heatL_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp2.connect("o1", c.ports["RingL"], allow_layer_mismatch=True).rotate(180, "o1")  # 连接并旋转
        heatR_comp1 = h << gf.path.extrude(heat_path + heatout_path2, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp1.connect("o1", c.ports["RingR"], allow_layer_mismatch=True)  # 连接
        heatR_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp2.connect("o1", c.ports["RingR"], allow_layer_mismatch=True).mirror_y("o1")  # 连接并镜像
        heatRing_route = gf.routing.get_bundle([heatL_comp2.ports["o2"]], [heatR_comp2.ports["o2"]], layer=heatlayer,
                                               width=WidthHeat)  # 创建加热电极之间的路由
        for route in heatRing_route:
            h.add(route.references)  # 添加路由到组件
        h.add_port(name="HeatIn", port=heatL_comp1.ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=heatR_comp1.ports["o2"])  # 添加加热输出端口
        h.add_port(name="RingL", port=heatL_comp1.ports["o1"])
        heater = c << h
        if DirectionHeater == "down":
            heater.mirror_y("RingL")
        c.add_port(name="HeatIn", port=heater.ports["HeatIn"])  # 添加加热输入端口
        c.add_port(name="HeatOut", port=heater.ports["HeatOut"])  # 添加加热输出端口
    elif TypeHeater == "snake":
        # 蛇形加热电极
        heat_path = gf.path.arc(radius=RadiusRing + DeltaHeat, angle=45)  # 创建加热电极路径
        heatout_path1 = euler_Bend_Half(radius=RadiusRing / 2, angle=45)  # 创建欧拉弯曲路径
        heatout_path2 = euler_Bend_Half(radius=RadiusRing / 2, angle=-45)  # 创建欧拉弯曲路径
        HPart = [
            SnakeHeater(WidthHeat, WidthRing, GapHeat, heat_path + heatout_path1, ["o1", "o2"], heatlayer) if i % 2 == 1
            else SnakeHeater(WidthHeat, WidthRing, GapHeat, heat_path + heatout_path2, ["o1", "o2"], heatlayer) for i in
            range(4)]  # 创建蛇形加热电极
        HeatLR = [h << HPart[i] for i in range(4)]  # 将蛇形加热电极添加到组件
        for i, comp in enumerate(HeatLR):
            if i == 0:
                comp.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True).mirror_x(
                    "o1")  # 连接并镜像
            elif i == 1:
                comp.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True).rotate(180,
                                                                                                                  "o1")  # 连接并旋转
            elif i == 2:
                comp.connect("o1", c.ports["RingR"], allow_layer_mismatch=True)  # 连接
            elif i == 3:
                comp.connect("o1", c.ports["RingR"], allow_layer_mismatch=True).mirror_y("o1")  # 连接并镜像
        heatRing_route = gf.routing.get_bundle([HeatLR[1].ports["o2"]], [HeatLR[3].ports["o2"]], layer=heatlayer,
                                               width=WidthHeat)  # 创建加热电极之间的路由
        for route in heatRing_route:
            h.add(route.references)  # 添加路由到组件
        h.add_port(name="HeatIn", port=HeatLR[0].ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=HeatLR[2].ports["o2"])  # 添加加热输出端口
        h.add_port(name="RingL", port=HeatLR[2].ports["o1"])
        heater = c << h
        if DirectionHeater == "down":
            heater.mirror_y("RingL")
        c.add_port(name="HeatIn", port=heater.ports["HeatIn"])  # 添加加热输入端口
        c.add_port(name="HeatOut", port=heater.ports["HeatOut"])  # 添加加热输出端口
    elif TypeHeater == "side":
        # 侧边加热电极
        heat_path = gf.path.arc(radius=RadiusRing + DeltaHeat, angle=60)  # 创建加热电极路径
        heatout_path1 = euler_Bend_Half(radius=RadiusRing / 2, angle=30)  # 创建欧拉弯曲路径
        heatout_path2 = euler_Bend_Half(radius=RadiusRing / 2, angle=-30)  # 创建欧拉弯曲路径
        heatout_path3 = euler_Bend_Half(radius=RadiusRing / 4, angle=60)  # 创建欧拉弯曲路径
        heatout_path4 = euler_Bend_Half(radius=RadiusRing / 4, angle=-60)  # 创建欧拉弯曲路径
        heatL_comp1 = h << gf.path.extrude(heat_path + heatout_path4, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp1.connect("o1", c.ports["RingL"], allow_layer_mismatch=True).mirror_x("o1")  # 连接并镜像
        heatL_comp1.movex(-GapHeat)
        heatL_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp2.connect("o1", c.ports["RingL"], allow_layer_mismatch=True).rotate(180, "o1")  # 连接并旋转
        heatL_comp2.movex(-GapHeat)
        heatR_comp1 = h << gf.path.extrude(heat_path + heatout_path4, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp1.connect("o1", c.ports["RingR"], allow_layer_mismatch=True)  # 连接
        heatR_comp1.movex(GapHeat)
        heatR_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp2.connect("o1", c.ports["RingR"], allow_layer_mismatch=True).mirror_y("o1")  # 连接并镜像
        heatR_comp2.movex(GapHeat)
        heatRing_route = gf.routing.get_bundle([heatL_comp2.ports["o2"]], [heatR_comp2.ports["o2"]], layer=heatlayer,
                                               width=WidthHeat)  # 创建加热电极之间的路由
        for route in heatRing_route:
            h.add(route.references)  # 添加路由到组件
        h.add_port(name="HeatIn", port=heatL_comp1.ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=heatR_comp1.ports["o2"])  # 添加加热输出端口
        h.add_port(name="RingL", port=c.ports["RingL"])
        heater = c << h
        if DirectionHeater == "down":
            heater.mirror_y("RingL")
        c.add_port(name="HeatIn", port=heater.ports["HeatIn"])  # 添加加热输入端口
        c.add_port(name="HeatOut", port=heater.ports["HeatOut"])  # 添加加热输出端口
    elif TypeHeater == "bothside":
        GapHeat = abs(GapHeat)
        # 侧边加热电极
        heat_path_int1 = gf.path.arc(radius=RadiusRing - GapHeat, angle=90)  # 创建加热电极路径
        heat_path_ext1 = gf.path.arc(radius=RadiusRing + GapHeat, angle=90)  # 创建加热电极路径
        heat_path_int2 = gf.path.arc(radius=RadiusRing - GapHeat, angle=45)  # 创建加热电极路径
        heat_path_ext2 = gf.path.arc(radius=RadiusRing + GapHeat, angle=45)  # 创建加热电极路径
        heatLint_comp1 = h << gf.path.extrude(heat_path_int2, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatLint_comp1.connect("o1", c.ports["RingL"], allow_layer_mismatch=True).mirror_x("o1")  # 连接并镜像
        heatLint_comp1.movex(GapHeat)
        heatLint_comp2 = h << gf.path.extrude(heat_path_int1, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatLint_comp2.connect("o1", c.ports["RingL"], allow_layer_mismatch=True).rotate(180, "o1")  # 连接并旋转
        heatLint_comp2.movex(GapHeat)
        heatLext_comp1 = h << gf.path.extrude(heat_path_ext2, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatLext_comp1.connect("o1", c.ports["RingL"], allow_layer_mismatch=True).mirror_x("o1")  # 连接并镜像
        heatLext_comp1.movex(-GapHeat)
        heatLext_comp2 = h << gf.path.extrude(heat_path_ext1, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatLext_comp2.connect("o1", c.ports["RingL"], allow_layer_mismatch=True).rotate(180, "o1")  # 连接并旋转
        heatLext_comp2.movex(-GapHeat)
        heatRint_comp1 = h << gf.path.extrude(heat_path_int2, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatRint_comp1.connect("o1", c.ports["RingR"], allow_layer_mismatch=True)  # 连接
        heatRint_comp1.movex(-GapHeat)
        heatRint_comp2 = h << gf.path.extrude(heat_path_int1, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatRint_comp2.connect("o1", c.ports["RingR"], allow_layer_mismatch=True).mirror_y("o1")  # 连接并镜像
        heatRint_comp2.movex(-GapHeat)
        heatRext_comp1 = h << gf.path.extrude(heat_path_ext2, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatRext_comp1.connect("o1", c.ports["RingR"], allow_layer_mismatch=True)  # 连接
        heatRext_comp1.movex(GapHeat)
        heatRext_comp2 = h << gf.path.extrude(heat_path_ext1, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatRext_comp2.connect("o1", c.ports["RingR"], allow_layer_mismatch=True).mirror_y("o1")  # 连接并镜像
        heatRext_comp2.movex(GapHeat)
        h.add_port(name="HeatIntIn", port=heatLint_comp1.ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatIntOut", port=heatRint_comp1.ports["o2"])  # 添加加热输出端口
        h.add_port(name="HeatExtIn", port=heatLext_comp1.ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatExtOut", port=heatRext_comp1.ports["o2"])  # 添加加热输出端口
        h.add_port(name="RingC", port=c.ports["RingC"])
        heater = c << h
        if DirectionHeater == "down":
            heater.mirror_y("RingC")
        c.add_port(name="HeatIntIn", port=heater.ports["HeatIntIn"])  # 添加加热输入端口
        c.add_port(name="HeatIntOut", port=heater.ports["HeatIntOut"])  # 添加加热输出端口
        c.add_port(name="HeatExtIn", port=heater.ports["HeatExtIn"])  # 添加加热输入端口
        c.add_port(name="HeatExtOut", port=heater.ports["HeatExtOut"])  # 添加加热输出端口
    elif TypeHeater == "spilt":
        S_route1 = gf.Section(width=WidthRoute, offset=DeltaHeat, layer=routelayer, port_names=("r1o1", "r1o2"))
        S_route2 = gf.Section(width=WidthRoute, offset=-(DeltaHeat), layer=routelayer, port_names=("r2o1", "r2o2"))
        X_Heat = gf.CrossSection(sections=[S_route1, S_route2])
        # 默认加热电极
        heat_path = gf.path.arc(radius=RadiusRing, angle=120)  # 创建加热电极路径
        route_path = gf.path.arc(radius=RadiusRing, angle=60)
        out_path = gf.path.arc(radius=20,angle=60)
        out_path2 = gf.path.arc(radius=20,angle=-60)
        heat_path.rotate(-60)
        heatL_comp = h << DifferentHeater(heat_path, WidthHeat=WidthHeat, heatlayer=heatlayer,routelayer=routelayer,
                                          vialayer=vialayer,TypeHeater='spilt',GapHeat=GapHeat,DeltaHeat=DeltaHeat,
                                          WidthRoute=20,Padding=GapHeat
                                          )  # 创建左侧加热电极
        heatL_comp.connect("HeatIn", c.ports["RingL"], allow_layer_mismatch=True).mirror_x("HeatIn")  # 连接并镜像
        heatL_comp.rotate(60,center=c.ports["RingC"])
        heatR_comp = h << DifferentHeater(heat_path, WidthHeat=WidthHeat, heatlayer=heatlayer,routelayer=routelayer,
                                          vialayer=vialayer,TypeHeater='spilt',GapHeat=GapHeat,DeltaHeat=DeltaHeat,
                                          WidthRoute=20,Padding=GapHeat
                                          )  # 创建左侧加热电极
        heatR_comp.connect("HeatIn", c.ports["RingR"], allow_layer_mismatch=True)
        heatR_comp.rotate(-60, center=c.ports["RingC"])
        Hp1 = h << gf.path.extrude(route_path, cross_section=X_Heat)
        Hp1.connect("r1o1",heatL_comp.ports["HeatLIn"])
        r_out_output = h << gf.path.extrude(out_path,width=WidthRoute,layer=routelayer)
        r_out_output.connect("o1",heatL_comp.ports['HeatLOut'])
        r_in_output = h << gf.path.extrude(out_path2, width=WidthRoute, layer=routelayer)
        r_in_output.connect("o1",heatR_comp.ports['HeatROut'])
        h.add_port(name="HeatL", port=r_out_output.ports["o2"])
        h.add_port(name="HeatR", port=r_in_output.ports["o2"])
        h.add_port(name="RingC", port=c.ports["RingC"])
        add_labels_to_ports(h)
        heater =c << h
        if DirectionHeater == "down":
            heater.mirror_y('RingC')
        c.add_port(name="HeatOut", port=heater.ports["HeatL"])  # 添加加热输入端口
        c.add_port(name="HeatIn", port=heater.ports["HeatR"])  # 添加加热输出端口
    return h

# %% 导出所有函数
__all__ = [
    'RingPulley', 'RingPulley1DC', 'RingPulley1HS', 'RingPulley1HSn', 'RingFinger', 'RingPulley2', 'RingPulley3',
    'RingPulley4', 'RingPulley2ES','RingPulleyT1','RingPulleyT2',
]
if __name__ == '__main__':
    test = gf.Component("test")
    test = RingPulleyT1(TypeHeater='spilt')