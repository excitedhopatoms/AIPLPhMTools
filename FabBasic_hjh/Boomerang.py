# from Heater import SnakeHeater
import numpy as np

from .BasicDefine import *
from .Heater import *

LengthAllAround = [0, 0, 0]


@gf.cell(check_instances=False)
def Boomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        GapRR: float = 0.3,
        LengthBridge1: float = 100,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        IsHeatIn: bool = False,
        IsHeatOut: bool = False,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
) -> Component:
    """
    创建一个"回旋镖"形状的光学谐振腔或延迟线组件。
    该组件由两个对称的半结构组成，每个半结构包含内弯曲路径、外弯曲路径、
    连接它们的锥形波导以及一个桥形连接结构。可以选择性地为内部和外部路径添加加热器。

    参数:
        WidthRingIn: 内环部分的波导宽度 (µm)。
        WidthRingOut: 外环部分的波导宽度 (µm)。
        WidthStraight: 用于连接桥和锥形波导末端的直波导宽度 (µm)。
        RadiusRing: 环形部分的基础半径 (µm)。
        RadiusEuler: 连接桥中欧拉弯曲的半径 (µm)。
        GapRR: 内环波导与外环波导之间的间隙 (µm)。
        LengthBridge1: 连接桥中较长直波导段的长度 (µm)。
        LengthBridge2: 连接桥中较短直波导段的长度 (µm)。
        LengthTaper: 从环形宽度过渡到直波导宽度的锥形波导长度 (µm)。
        IsHeatIn: 是否为内环路径添加加热器。
        IsHeatOut: 是否为外环路径添加加热器。
        oplayer: 光学波导层定义。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。
                      包含 TypeHeater, WidthHeat, WidthRoute, GapHeat, DeltaHeat 等参数。

    返回:
        Component: 生成的"回旋镖"组件。

    端口:
        Lo1: 左半部分内环路径的输入/输出端口。
        Lo2: 左半部分外环路径的输入/输出端口。
        Ro1: 右半部分内环路径的输入/输出端口。
        Ro2: 右半部分外环路径的输入/输出端口。
        Lb1, Lb2: 左半部分桥接结构的端口。
        Rb1, Rb2: 右半部分桥接结构的端口。
        (HeaterConfig 不为 None 且 IsHeatIn/IsHeatOut 为 True 时) 相应的加热器电学端口。

    信息 (Info):
        length (float): 计算得到的整个回旋镖结构的光学路径长度。
    """
    c = gf.Component()
    Cring1 = gf.Component()
    Test = gf.Component()
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="linear")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="linear")
    path_circle_in = gf.path.arc(radius=RadiusRing, angle=30)
    path_circle_out = gf.path.arc(radius=RadiusRing + GapRR + WidthRingIn / 2 + WidthRingOut / 2, angle=30)
    path_euler_in = euler_Bend_Half(radius=RadiusRing, angle=15)
    path_euler_out = euler_Bend_Half(radius=RadiusRing + GapRR + WidthRingIn / 2 + WidthRingOut / 2, angle=15)
    path_euler_bridge = euler_Bend_Half(radius=RadiusEuler, angle=90)
    path_taper_in = gf.path.straight(length=LengthTaper)
    Cringhalf = gf.Component()
    cir_in = Cringhalf << gf.path.extrude(path_circle_in + path_euler_in, cross_section=X_in)
    cir_out = Cringhalf << gf.path.extrude(path_circle_out + path_euler_out, cross_section=X_out)
    TaperIn = gf.c.taper(width1=WidthRingIn, width2=WidthStraight, length=LengthTaper, layer=oplayer)
    TaperOut = gf.c.taper(width1=WidthRingOut, width2=WidthStraight, length=LengthTaper, layer=oplayer)
    taper_in = Cringhalf << TaperIn
    taper_out = Cringhalf << TaperOut
    c_euler_bridge = Test << gf.path.extrude(path_euler_bridge, cross_section=X_str)
    Deltaheight = (LengthBridge2 + 2 * (c_euler_bridge.ports["o2"].center[0] - c_euler_bridge.ports["o1"].center[0]))
    cir_out.move([-Deltaheight, Deltaheight])
    cir_in.rotate(45, cir_in.ports["o1"].center)
    cir_out.rotate(45, cir_out.ports["o1"].center)
    taper_in.connect("o1", cir_in.ports["o2"])
    taper_out.connect("o1", cir_out.ports["o2"])
    path_str_out = gf.path.straight(length=LengthBridge1)
    StrOut = gf.path.extrude(path_str_out, cross_section=X_str)
    str_out = Cringhalf << StrOut
    str_out.connect("o1", taper_out.ports["o2"])
    route = gf.routing.route_single(Cringhalf, str_out.ports["o2"], taper_in.ports["o2"], radius=RadiusEuler * 1.1,
                            cross_section=X_str)
    route_bend = gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=90)
    Cringhalf.add_port("o1", port=cir_in.ports["o1"])
    Cringhalf.add_port("o2", port=cir_out.ports["o1"])
    Cringhalf.add_port("o22", port=cir_out.ports["o2"])
    Cringhalf.add_port("Lb1", center=tuple(np.array(Cringhalf.ports["o22"].center) + np.array([0, LengthBridge1 + LengthTaper]) + (
                np.array(route_bend.ports["o2"].center) - np.array(route_bend.ports["o1"].center))),
                       orientation=0, cross_section=X_str)
    Cringhalf.add_port("Lb2", center=tuple(np.array(Cringhalf.ports["Lb1"].center) + np.array([LengthBridge2, 0])),
                       orientation=180, cross_section=X_str)
    if HeaterConfig and (IsHeatIn or IsHeatOut):
        boomerang_heater(Cringhalf, path_circle_in, path_euler_in, path_circle_out, path_euler_out,
                         path_taper_in, path_str_out, route, WidthStraight, RadiusEuler,
                         IsHeatIn, IsHeatOut, HeaterConfig)
    ringhalf1 = Cring1 << Cringhalf
    ringhalf2 = Cring1 << Cringhalf
    ringhalf2.mirror_x(ringhalf2.ports["o1"].center[0])
    ringhalf2.rotate(90, ringhalf2.ports["o1"].center)
    l1 = path_circle_in.length() + path_circle_out.length() + path_euler_out.length() + path_euler_in.length() + route.length + 2 * LengthTaper + LengthBridge1
    c << Cring1
    c.add_port("Lo1", port=ringhalf1.ports["o1"])
    c.add_port("Lo2", port=ringhalf1.ports["o2"])
    c.add_port("Ro1", port=ringhalf2.ports["o1"])
    c.add_port("Ro2", port=ringhalf2.ports["o2"])
    c.add_port("Lb1", port=ringhalf1.ports["Lb1"])
    c.add_port("Lb2", port=ringhalf1.ports["Lb2"])
    c.add_port("Rb1", port=ringhalf2.ports["Lb1"])
    c.add_port("Rb2", port=ringhalf2.ports["Lb2"])
    if HeaterConfig and IsHeatIn:
        if HeaterConfig.TypeHeater in ("bothside", "spilt"):
            c.add_port("HeatILIn", port=ringhalf1.ports["HeatIL"])
            c.add_port("HeatILOut", port=ringhalf1.ports["HeatIR"])
            c.add_port("HeatIRIn", port=ringhalf2.ports["HeatIL"])
            c.add_port("HeatIROut", port=ringhalf2.ports["HeatIR"])
        else:
            c.add_port("HeatILIn", port=ringhalf1.ports["HeatI1"])
            c.add_port("HeatILOut", port=ringhalf1.ports["HeatI2"])
            c.add_port("HeatIRIn", port=ringhalf2.ports["HeatI1"])
            c.add_port("HeatIROut", port=ringhalf2.ports["HeatI2"])
    if HeaterConfig and IsHeatOut:
        if HeaterConfig.TypeHeater in ("bothside", "spilt"):
            c.add_port("HeatOLIn", port=ringhalf1.ports["HeatOL"])
            c.add_port("HeatOLOut", port=ringhalf1.ports["HeatOR"])
            c.add_port("HeatORIn", port=ringhalf2.ports["HeatOL"])
            c.add_port("HeatOROut", port=ringhalf2.ports["HeatOR"])
        else:
            c.add_port("HeatOLIn", port=ringhalf1.ports["HeatO1"])
            c.add_port("HeatOLOut", port=ringhalf1.ports["HeatO2"])
            c.add_port("HeatORIn", port=ringhalf2.ports["HeatO1"])
            c.add_port("HeatOROut", port=ringhalf2.ports["HeatO2"])
    c.info['length'] = 2 * l1
    add_labels_to_ports(c)
    return c


# 回旋镖腔
@gf.cell
def RingBoomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        GapRR: float = 0.3,
        GapRB: float = 0.5,
        LengthBridge1: float = 100,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        LengthCouple: float = 10,
        IsHeatIn: bool = True,
        IsHeatOut: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
) -> Component:
    """
    包含单个回旋镖谐振器并通过总线波导耦合的环形谐振器结构。

    参数:
        WidthRingIn, WidthRingOut, WidthStraight: 回旋镖单元波导宽度 (µm)。
        RadiusRing, RadiusEuler: 回旋镖内外 S 弯弯曲半径 (µm)。
        GapRR: 内环与外环波导之间的间隙 (µm)。
        GapRB: 回旋镖桥臂与外部总线波导之间的耦合间隙 (µm)。
        LengthBridge1, LengthBridge2, LengthTaper: 回旋镖内部结构参数 (µm)。
        LengthCouple: 总线波导上耦合直波导段长度 (µm)。
        IsHeatIn: Boomerang 单元内环是否加热。
        IsHeatOut: Boomerang 单元外环是否加热。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。

    返回:
        Component: 带耦合的回旋镖环形谐振器组件。

    端口:
        Input, Through, Add, Drop: 光学端口。
        (从 Boomerang 单元继承的加热器端口)

    信息 (Info):
        length (float): Boomerang 单元的光学路径长度。
    """
    c = gf.Component()
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="sine")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="sine")
    Cring1 = c << Boomerang(
        WidthRingIn=WidthRingIn, WidthRingOut=WidthRingOut, WidthStraight=WidthStraight,
        RadiusRing=RadiusRing, RadiusEuler=RadiusEuler, GapRR=GapRR,
        LengthBridge1=LengthBridge1, LengthBridge2=LengthBridge2, LengthTaper=LengthTaper,
        IsHeatIn=IsHeatIn, IsHeatOut=IsHeatOut, oplayer=oplayer, HeaterConfig=HeaterConfig,
    )
    Cring1.rotate(90, Cring1.ports["Lo1"].center)
    sbend_in = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    sbend_out = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_in = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_in.connect("o1", Cring1.ports["Lb1"])
    str_couple_in.movex(-GapRB - WidthStraight).movey(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_in.connect("o2", str_couple_in.ports["o1"], mirror=True)
    sbend_out.connect("o1", str_couple_in.ports["o2"])
    sbend_add = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    sbend_drop = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_ad = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_ad.connect("o1", Cring1.ports["Rb1"])
    str_couple_ad.movey(-GapRB - WidthStraight).movex(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_add.connect("o2", str_couple_ad.ports["o1"])
    sbend_drop.connect("o1", str_couple_ad.ports["o2"], mirror=True)
    c.add_port("Input", port=sbend_in.ports["o1"])
    c.add_port("Through", port=sbend_out.ports["o2"])
    c.add_port("Add", port=sbend_add.ports["o1"])
    c.add_port("Drop", port=sbend_drop.ports["o2"])
    c.info['length'] = Cring1.cell.info['length']
    return c


# 双回旋镖腔
@gf.cell
def RingDouBoomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        GapRR: float = 0.3,
        GapRB: float = 0.5,
        DeltaLB2: float = 2,
        LengthBridge1: float = 10,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        LengthCouple: float = 10,
        IsHeat: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
) -> Component:
    """
    包含两个串联回旋镖谐振器的组件。
    两个回旋镖单元通过 DeltaLB2 实现结构上的微小差异以引入失谐。

    参数:
        WidthRingIn, WidthRingOut, WidthStraight: 回旋镖单元波导宽度 (µm)。
        RadiusRing, RadiusEuler: 回旋镖内外 S 弯弯曲半径 (µm)。
        GapRR: 内环与外环波导间隙 (µm)。
        GapRB: 回旋镖桥臂与总线波导耦合间隙 (µm)。
        DeltaLB2: 第二个 Boomerang 的 LengthBridge2 增量 (µm)。
        LengthBridge1, LengthBridge2, LengthTaper: 回旋镖内部结构参数 (µm)。
        LengthCouple: 总线波导耦合段长度 (µm)。
        IsHeat: 控制两个 Boomerang 的加热器总开关。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。

    返回:
        Component: 双回旋镖谐振器组件。

    端口:
        Input, Through, Add, Drop: 光学端口。
        R1Lo1, R1Lo2, ..., R2Ro1, R2Ro2, ...: 各单元原始端口。

    信息 (Info):
        R1length, R2length: 各单元光学路径长度。
    """
    c = gf.Component()
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="sine")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="sine")
    boomerang1 = Boomerang(
        WidthRingIn=WidthRingIn, WidthRingOut=WidthRingOut, WidthStraight=WidthStraight,
        RadiusRing=RadiusRing, RadiusEuler=RadiusEuler, GapRR=GapRR,
        LengthBridge1=LengthBridge1, LengthBridge2=LengthBridge2, LengthTaper=LengthTaper,
        IsHeatIn=False, IsHeatOut=IsHeat, oplayer=oplayer, HeaterConfig=HeaterConfig,
    )
    Cring1 = c << boomerang1
    Cring1.rotate(90, Cring1.ports["Lo1"].center)
    boomerang2 = Boomerang(
        WidthRingIn=WidthRingIn, WidthRingOut=WidthRingOut, WidthStraight=WidthStraight,
        RadiusRing=RadiusRing, RadiusEuler=RadiusEuler, GapRR=GapRR,
        LengthBridge1=LengthBridge1, LengthBridge2=LengthBridge2 + DeltaLB2, LengthTaper=LengthTaper,
        IsHeatIn=IsHeat, IsHeatOut=False, oplayer=oplayer, HeaterConfig=HeaterConfig,
    )
    Cring2 = c << boomerang2
    Cring2.connect("Lo2", Cring1.ports["Ro1"], allow_width_mismatch=True)
    Cring2.move(((WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2),
                 (WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2)))
    sbend_add = c << gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=90, cross_section=X_str)
    sbend_drop = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_ad = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_ad.connect("o1", Cring2.ports["Lb1"])
    str_couple_ad.movex(-GapRB - WidthStraight).movey(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_add.connect("o2", str_couple_ad.ports["o1"])
    sbend_drop.connect("o1", str_couple_ad.ports["o2"])
    c.add_port("Add", port=sbend_add.ports['o1'])
    c.add_port("Drop", port=sbend_drop.ports['o2'])
    c.info['R1length'] = boomerang1.info['length']
    c.info['R2length'] = boomerang2.info['length']
    sbend_in = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    sbend_th = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_in = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_in.connect("o1", Cring1.ports["Rb1"])
    str_couple_in.movey(-GapRB - WidthStraight).movex(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_in.connect("o2", str_couple_in.ports["o1"])
    sbend_th.connect("o1", str_couple_in.ports["o2"], mirror=True)
    c.add_port("Input", port=sbend_in.ports['o1'])
    c.add_port("Through", port=sbend_th.ports['o2'])
    for port in Cring1.ports:
        c.add_port("R1" + port.name, port=Cring1.ports[port.name])
    for port in Cring2.ports:
        c.add_port("R2" + port.name, port=Cring2.ports[port.name])
    return c


# 三回旋镖腔
@gf.cell
def RingTriBoomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        GapRR: float = 0.3,
        GapRB: float = 0.5,
        DeltaLB2: float = 2,
        LengthBridge1: float = 10,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        LengthCouple: float = 10,
        IsHeat: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
) -> Component:
    """
    包含三个串联回旋镖谐振器的组件。

    参数:
        WidthRingIn, WidthRingOut, WidthStraight: 回旋镖单元波导宽度 (µm)。
        RadiusRing, RadiusEuler: 回旋镖内外 S 弯弯曲半径 (µm)。
        GapRR: 内环与外环波导间隙 (µm)。
        GapRB: 回旋镖桥臂与总线波导耦合间隙 (µm)。
        DeltaLB2: 第二个/第三个 Boomerang 的 LengthBridge2 增量/减量 (µm)。
        LengthBridge1, LengthBridge2, LengthTaper: 回旋镖内部结构参数 (µm)。
        LengthCouple: 总线波导耦合段长度 (µm)。
        IsHeat: 控制回旋镖加热器总开关。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。

    返回:
        Component: 三回旋镖谐振器组件。

    端口:
        Input, Through, Add, Drop: 光学端口。
        R1*, R2*, R3*: 各单元原始端口。

    信息 (Info):
        R1length, R2length, R3length: 各单元光学路径长度。
    """
    c = gf.Component()
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="sine")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="sine")
    boomerang1 = Boomerang(
        WidthRingIn=WidthRingIn, WidthRingOut=WidthRingOut, WidthStraight=WidthStraight,
        RadiusRing=RadiusRing, RadiusEuler=RadiusEuler, GapRR=GapRR,
        LengthBridge1=LengthBridge1, LengthBridge2=LengthBridge2, LengthTaper=LengthTaper,
        IsHeatIn=False, IsHeatOut=False, oplayer=oplayer, HeaterConfig=HeaterConfig,
    )
    Cring1 = c << boomerang1
    Cring1.rotate(90, Cring1.ports["Lo1"].center)
    boomerang2 = Boomerang(
        WidthRingIn=WidthRingIn, WidthRingOut=WidthRingOut, WidthStraight=WidthStraight,
        RadiusRing=RadiusRing, RadiusEuler=RadiusEuler, GapRR=GapRR,
        LengthBridge1=LengthBridge1, LengthBridge2=LengthBridge2 + DeltaLB2, LengthTaper=LengthTaper,
        IsHeatIn=IsHeat, IsHeatOut=False, oplayer=oplayer, HeaterConfig=HeaterConfig,
    )
    Cring2 = c << boomerang2
    Cring2.connect("Lo2", Cring1.ports["Ro1"], allow_width_mismatch=True)
    Cring2.move(((WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2),
                 (WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2)))
    boomerang3 = Boomerang(
        WidthRingIn=WidthRingIn, WidthRingOut=WidthRingOut, WidthStraight=WidthStraight,
        RadiusRing=RadiusRing, RadiusEuler=RadiusEuler, GapRR=GapRR,
        LengthBridge1=LengthBridge1, LengthBridge2=LengthBridge2 - DeltaLB2, LengthTaper=LengthTaper,
        IsHeatIn=False, IsHeatOut=IsHeat, oplayer=oplayer, HeaterConfig=HeaterConfig,
    )
    Cring3 = c << boomerang3
    Cring3.connect("Lo1", Cring1.ports["Ro2"], allow_width_mismatch=True)
    Cring3.move((-(WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2),
                 -(WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2)))
    c.info['R1length'] = boomerang1.info['length']
    c.info['R2length'] = boomerang2.info['length']
    c.info['R3length'] = boomerang3.info['length']
    sbend_in = c << gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=90, cross_section=X_str)
    sbend_out = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_in = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_in.connect("o1", Cring1.ports["Lb1"])
    str_couple_in.movex(-GapRB - WidthStraight).movey(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_in.connect("o2", str_couple_in.ports["o1"])
    sbend_out.connect("o1", str_couple_in.ports["o2"])
    c.add_port("Input", port=sbend_in.ports['o1'])
    c.add_port("Through", port=sbend_out.ports['o2'])
    sbend_add = c << gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=-90, cross_section=X_str)
    sbend_drop = c << gf.c.bend_s(size=[100, -10], cross_section=X_str)
    str_couple_ad = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_ad.connect("o1", Cring1.ports["Rb1"])
    str_couple_ad.movey(-GapRB - WidthStraight).movex(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_add.connect("o2", str_couple_ad.ports["o1"])
    sbend_drop.connect("o1", str_couple_ad.ports["o2"])
    c.add_port("Add", port=sbend_add.ports['o1'])
    c.add_port("Drop", port=sbend_drop.ports['o2'])
    for port in Cring1.ports:
        c.add_port("R1" + port.name, port=Cring1.ports[port.name])
    for port in Cring2.ports:
        c.add_port("R2" + port.name, port=Cring2.ports[port.name])
    for port in Cring3.ports:
        c.add_port("R3" + port.name, port=Cring3.ports[port.name])
    return c


def _backbone_to_smooth_path(backbone_um, radius):
    """将 Manhattan backbone 点转换为平滑路径，在拐角处插入欧拉弯。

    路径方向: backbone[-1] → backbone[0]（与 route.instances 的放置方向一致）
    在每个拐角处，欧拉弯的起始端口位于 corner - d_in * radius。

    Args:
        backbone_um: backbone 点数组 (N, 2)，单位 µm
        radius: 欧拉弯半径

    Returns:
        平滑路径点数组 (M, 2)，单位 µm，方向为 backbone[-1] → backbone[0]
    """
    if len(backbone_um) < 2:
        return backbone_um

    rev_backbone = backbone_um[::-1]

    bend_path = gf.path.euler(radius=radius, angle=90)
    bend_pts = bend_path.points.copy()

    all_segments = []
    prev_bend_end = None

    for i in range(len(rev_backbone) - 1):
        p_curr = rev_backbone[i]
        p_next = rev_backbone[i + 1]

        if i == 0:
            seg_start = p_curr
        else:
            seg_start = prev_bend_end

        if i == len(rev_backbone) - 2:
            seg_end = p_next
            if np.linalg.norm(seg_end - seg_start) > 0.001:
                all_segments.append(np.array([seg_start, seg_end]))
            break

        p_after = rev_backbone[i + 2]

        d_in = p_next - p_curr
        d_in_len = np.linalg.norm(d_in)
        if d_in_len < 1e-9:
            continue
        d_in_norm = d_in / d_in_len

        corner = p_next
        bend_start = corner - d_in_norm * radius

        if np.linalg.norm(bend_start - seg_start) > 0.001:
            all_segments.append(np.array([seg_start, bend_start]))

        angle_in = np.arctan2(d_in_norm[1], d_in_norm[0])
        cos_a = np.cos(angle_in)
        sin_a = np.sin(angle_in)
        rotated_bend = np.column_stack([
            bend_pts[:, 0] * cos_a - bend_pts[:, 1] * sin_a,
            bend_pts[:, 0] * sin_a + bend_pts[:, 1] * cos_a
        ])

        translated_bend = rotated_bend + bend_start
        all_segments.append(translated_bend)

        prev_bend_end = translated_bend[-1]

    if len(all_segments) == 0:
        return rev_backbone

    result = all_segments[0]
    for seg in all_segments[1:]:
        result = np.vstack([result, seg[1:]])

    return result


def boomerang_heater(
        c: Component,
        path_circle_in,
        path_euler_in,
        path_circle_out,
        path_euler_out,
        path_taper_in,
        path_str_out,
        route,
        WidthStraight: float,
        RadiusEuler: float,
        IsHeatIn: bool,
        IsHeatOut: bool,
        HeaterConfig: HeaterConfigClass,
) -> None:
    """
    统一的回旋镖加热器放置函数，将加热器直接添加到目标组件 c（Cringhalf）上。
    加热器路径沿波导构建，包含圆弧段、欧拉弯段、锥形过渡段、桥接直波导段和路由弯段。
    加热器放置在 Cringhalf 中，当 Cringhalf 被放置为 ringhalf1 和 ringhalf2 时，
    左右两半会自动获得各自的加热器副本。

    参数:
        c: 待添加加热器的目标组件（Cringhalf）。
        path_circle_in, path_euler_in: 内环路径的圆弧和欧拉弯段。
        path_circle_out, path_euler_out: 外环路径的圆弧和欧拉弯段。
        path_taper_in: 锥形过渡段路径。
        path_str_out: 桥接直波导段路径。
        route: 连接内外环的路由对象（ManhattanRoute），从中提取 backbone 构建加热器路径。
        WidthStraight: 直波导宽度，用于加热器参考。
        RadiusEuler: 欧拉弯半径，用于从 backbone 构建平滑路径。
        IsHeatIn: 是否为内环路径添加加热器。
        IsHeatOut: 是否为外环路径添加加热器。
        HeaterConfig: 加热器配置对象。
    """
    dbu = gf.kcl.dbu
    backbone_um = np.array([(p.x * dbu, p.y * dbu) for p in route.backbone])

    def _rotate_pts(pts, angle_deg, center):
        angle_rad = np.radians(angle_deg)
        cos_a, sin_a = np.cos(angle_rad), np.sin(angle_rad)
        t = pts - center
        r = np.column_stack([t[:, 0] * cos_a - t[:, 1] * sin_a,
                             t[:, 0] * sin_a + t[:, 1] * cos_a])
        return r + center

    if IsHeatIn:
        route_points_um = _backbone_to_smooth_path(backbone_um, RadiusEuler * 1.1)
        path_segments = path_circle_in + path_euler_in + path_taper_in
        start_local = path_segments.points[0].copy()
        translated = path_segments.points - start_local
        rotated = _rotate_pts(translated, 45, np.array([0.0, 0.0]))
        seg_points = rotated + start_local
        route_pts = route_points_um.copy()
        all_points = np.vstack([seg_points, route_pts[1:]])
        path_heat_in = gf.path.Path(all_points)
        HeatIn = DifferentHeater(PathHeat=path_heat_in, WidthWG=WidthStraight, HeaterConfig=HeaterConfig)
        heat_in = c << HeatIn
        if HeaterConfig.TypeHeater in ("bothside", "spilt"):
            c.add_port("HeatIL", port=heat_in.ports["HeatLOut"])
            c.add_port("HeatIR", port=heat_in.ports["HeatROut"])
        else:
            c.add_port("HeatI1", port=heat_in.ports["HeatIn"])
            c.add_port("HeatI2", port=heat_in.ports["HeatOut"])

    if IsHeatOut:
        backbone_out = backbone_um[::-1].copy()
        route_points_um_out = _backbone_to_smooth_path(backbone_out, RadiusEuler * 1.1)
        center_out = np.array(c.ports["o2"].center)
        path_segments = path_circle_out + path_euler_out + path_taper_in + path_str_out
        start_local = path_segments.points[0].copy()
        translated = path_segments.points - start_local
        rotated = _rotate_pts(translated, 45, np.array([0.0, 0.0]))
        seg_points = rotated + center_out
        route_pts = route_points_um_out.copy()
        all_points = np.vstack([seg_points, route_pts[1:]])
        path_heat_out = gf.path.Path(all_points)
        HeatOut = DifferentHeater(PathHeat=path_heat_out, WidthWG=WidthStraight, HeaterConfig=HeaterConfig)
        heat_out = c << HeatOut
        if HeaterConfig.TypeHeater in ("bothside", "spilt"):
            c.add_port("HeatOL", port=heat_out.ports["HeatLOut"])
            c.add_port("HeatOR", port=heat_out.ports["HeatROut"])
        else:
            c.add_port("HeatO1", port=heat_out.ports["HeatIn"])
            c.add_port("HeatO2", port=heat_out.ports["HeatOut"])


__all__ = [
    'Boomerang', 'RingBoomerang', 'RingDouBoomerang', 'RingTriBoomerang', 'boomerang_heater'
]
