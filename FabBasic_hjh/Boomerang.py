# from Heater import SnakeHeater
import numpy as np

from .BasicDefine import *
from .Heater import *

LengthAllAround = [0, 0, 0]  # 回旋镖腔


@gf.cell
def Boomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        WidthHeat: float = 4,
        WidthRoute: float = 20,
        WidthVia: float = 0.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        Spacing: float = 1,
        GapRR: float = 0.3,
        GapHeat: float = 80,
        DeltaHeat: float = 100,
        LengthBridge1: float = 100,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        IsHeatIn: bool = False,
        IsHeatOut: bool = False,
        TypeHeater: str = "default",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
     创建一个“回旋镖”形状的光学谐振腔或延迟线组件。
     该组件由两个对称的半结构组成，每个半结构包含内弯曲路径、外弯曲路径、
     连接它们的锥形波导以及一个桥形连接结构。可以选择性地为内部和外部路径添加加热器。

     参数:
         WidthRingIn (float): 内环部分的波导宽度 (单位: um)。
         WidthRingOut (float): 外环部分的波导宽度 (单位: um)。
         WidthStraight (float): 用于连接桥和锥形波导末端的直波导宽度 (单位: um)。
         WidthHeat (float): 加热器的宽度 (单位: um)。
         WidthRoute (float): 加热器引出线的宽度 (单位: um)。
         WidthVia (float): 加热器过孔的尺寸 (单位: um)。
         RadiusRing (float): 环形部分的基础半径，通常指内环圆弧段的半径 (单位: um)。
         RadiusEuler (float): 连接桥中欧拉弯曲的半径 (单位: um)。
         Spacing (float): 元素间距，常用于加热器设计中的过孔间距等 (单位: um)。
         GapRR (float): 内环波导与外环波导之间的间隙 (单位: um)。
         GapHeat (float): 波导与加热器之间的横向间隙 (单位: um)。
         DeltaHeat (float): 加热器的特定尺寸参数，如偏移量或长度，取决于加热器类型 (单位: um)。
         LengthBridge1 (float): 连接桥中较长直波导段的长度 (单位: um)。
         LengthBridge2 (float): 连接桥中较短直波导段的长度 (单位: um)。
         LengthTaper (float): 从环形宽度过渡到直波导宽度的锥形波导长度 (单位: um)。
         IsHeatIn (bool): 是否为内环路径添加加热器。
         IsHeatOut (bool): 是否为外环路径添加加热器。
         TypeHeater (str): 加热器的类型，例如 "default", "snake", "side"。
         oplayer (LayerSpec): 光学波导层定义。
         heatlayer (LayerSpec): 加热器层定义。
         routelayer (LayerSpec): 加热器布线层定义。
         vialayer (LayerSpec): 加热器过孔层定义。

     返回:
         Component: 生成的“回旋镖”组件。

     端口:
         Lo1: 左半部分内环路径的输入/输出端口。
         Lo2: 左半部分外环路径的输入/输出端口。
         Ro1: 右半部分内环路径的输入/输出端口。
         Ro2: 右半部分外环路径的输入/输出端口。
         Lb1, Lb2: 左半部分桥接结构的端口，用于可能的外部连接或测试。
         Rb1, Rb2: 右半部分桥接结构的端口。
         (如果添加加热器，还会有相应的加热器端口，例如 HeatILIn, HeatOLOut 等)

     信息 (Info):
         length (float): 计算得到的整个回旋镖结构的光学路径长度 (估算值)。
     """
    c = gf.Component()
    Cring1 = gf.Component()
    Test = gf.Component()
    # sections
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="linear")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="linear")
    # paths
    path_circle_in = gf.path.arc(radius=RadiusRing, angle=30)
    path_circle_out = gf.path.arc(radius=RadiusRing + GapRR + WidthRingIn / 2 + WidthRingOut / 2, angle=30)
    path_euler_in = euler_Bend_Half(radius=RadiusRing, angle=15)
    path_euler_out = euler_Bend_Half(radius=RadiusRing + GapRR + WidthRingIn / 2 + WidthRingOut / 2, angle=15)
    path_euler_bridge = euler_Bend_Half(radius=RadiusEuler, angle=90)
    path_taper_in = gf.path.straight(length=LengthTaper)
    # components
    Cringhalf = gf.Component()
    cir_in = Cringhalf << gf.path.extrude(path_circle_in + path_euler_in, cross_section=X_in)
    cir_out = Cringhalf << gf.path.extrude(path_circle_out + path_euler_out, cross_section=X_out)
    # CompOut.connect("o1",CompIn.ports["o1"],allow_width_mismatch=True).mirror_x("o1").mirror_y("o1").movey(-(GapRR+WidthRingOut/2+WidthRingIn/2))
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
    route = gf.routing.get_route(str_out.ports["o2"], taper_in.ports["o2"], radius=RadiusEuler * 1.1,
                                 cross_section=X_str, )
    route_bend = gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=90)
    Cringhalf.add_port("o1", port=cir_in.ports["o1"])
    Cringhalf.add_port("o2", port=cir_out.ports["o1"])
    Cringhalf.add_port("o22", port=cir_out.ports["o2"])
    Cringhalf.add_port("Lb1", center=Cringhalf.ports["o22"].center + [0, LengthBridge1 + LengthTaper] + (
                route_bend.ports["o2"].center - route_bend.ports["o1"].center),
                       orientation=0, cross_section=X_str)
    Cringhalf.add_port("Lb2", center=Cringhalf.ports["Lb1"].center + [LengthBridge2, 0],
                       orientation=180, cross_section=X_str)
    Cringhalf.add(route.references)
    ringhalf1 = Cring1 << Cringhalf
    ringhalf2 = Cring1 << Cringhalf
    ringhalf2.mirror_x(ringhalf2.ports["o1"].center[0])
    ringhalf2.rotate(90, ringhalf2.ports["o1"].center)
    # heat in
    if IsHeatIn:
        path_heat_in = path_circle_in + path_euler_in + path_taper_in
        path_heat_in.rotate(45)
        HeatInHalf = DifferentHeater(PathHeat=path_heat_in,
                                     WidthHeat=WidthHeat, WidthWG=WidthStraight, WidthRoute=WidthRoute,
                                     WidthVia=WidthVia, Spacing=Spacing,
                                     DeltaHeat=DeltaHeat, GapHeat=GapHeat, TypeHeater=TypeHeater,
                                     heatlayer=heatlayer, vialayer=vialayer, routelayer=routelayer)
        heat_in_l = c << HeatInHalf
        heat_in_r = c << HeatInHalf
        heat_in_l.connect('HeatIn', ringhalf1.ports["o1"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heat_in_r.connect('HeatIn', heat_in_l.ports["HeatIn"], mirror=True)
        heat_in_l.rotate(-90, heat_in_l.ports['HeatIn'].center)
        c.add_port("HeatILIn", port=heat_in_l.ports["HeatLOut"])
        c.add_port("HeatILOut", port=heat_in_r.ports["HeatLOut"])
        c.add_port("HeatIRIn", port=heat_in_l.ports["HeatROut"])
        c.add_port("HeatIROut", port=heat_in_r.ports["HeatROut"])
    if IsHeatOut:
        path_heat_out = path_circle_out + path_euler_out + path_taper_in
        path_heat_out.rotate(45)
        HeatOutHalf = DifferentHeater(PathHeat=path_heat_out,
                                      WidthHeat=WidthHeat, WidthWG=WidthStraight, WidthRoute=WidthRoute,
                                      WidthVia=WidthVia, Spacing=Spacing,
                                      DeltaHeat=DeltaHeat, GapHeat=GapHeat, TypeHeater=TypeHeater,
                                      heatlayer=heatlayer, vialayer=vialayer, routelayer=routelayer)
        heat_out_l = c << HeatOutHalf
        heat_out_r = c << HeatOutHalf
        heat_out_l.connect('HeatIn', ringhalf1.ports["o2"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heat_out_r.connect('HeatIn', heat_out_l.ports["HeatIn"], mirror=True)
        heat_out_l.rotate(-90, heat_out_l.ports['HeatIn'].center)
        c.add_port("HeatOLIn", port=heat_out_l.ports["HeatLOut"])
        c.add_port("HeatOLOut", port=heat_out_r.ports["HeatLOut"])
        c.add_port("HeatORIn", port=heat_out_l.ports["HeatROut"])
        c.add_port("HeatOROut", port=heat_out_r.ports["HeatROut"])
    # caculate length
    l1 = path_circle_in.length() + path_circle_out.length() + path_euler_out.length() + path_euler_in.length() + route.length + 2 * LengthTaper + LengthBridge1
    # Cring0 = GetFromLayer(Cring1,OLayer=oplayer,FLayer=oplayer)
    # Cring2 = gf.geometry.offset(distance=0.05,elements=Cring0)
    # c << gf.geometry.offset(distance=-0.05,elements=Cring2)
    c << Cring1
    # add port
    c.add_port("Lo1", port=ringhalf1.ports["o1"])
    c.add_port("Lo2", port=ringhalf1.ports["o2"])
    c.add_port("Ro1", port=ringhalf2.ports["o1"])
    c.add_port("Ro2", port=ringhalf2.ports["o2"])
    c.add_port("Lb1", port=ringhalf1.ports["Lb1"])
    c.add_port("Lb2", port=ringhalf1.ports["Lb2"])
    c.add_port("Rb1", port=ringhalf2.ports["Lb1"])
    c.add_port("Rb2", port=ringhalf2.ports["Lb2"])
    c.info['length'] = 2 * l1
    add_labels_to_ports(c)
    return c


# 回旋镖腔
@gf.cell
def RingBoomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        WidthHeat: float = 4,
        WidthRoute: float = 20,
        WidthVia: float = 0.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        Spacing: float = 1,
        GapRR: float = 0.3,
        GapRB: float = 0.5,
        GapHeat: float = 80,
        DeltaHeat: float = 100,
        LengthBridge1: float = 100,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        LengthCouple: float = 10,
        IsHeatIn: bool = True,
        IsHeatOut: bool = True,
        TypeHeater: str = "default",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个包含单个“回旋镖”谐振器并通过总线波导进行耦合的环形谐振器结构。
    “回旋镖”本身是一个具有特定路径的谐振单元。

    参数:
        (参数与 Boomerang 函数中的大部分相同，用于定义回旋镖单元的几何形状和加热器)
        WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
        RadiusRing, RadiusEuler (用于Boomerang内部和外部S弯), Spacing, GapRR, GapHeat, DeltaHeat,
        LengthBridge1, LengthBridge2, LengthTaper (Boomerang内部)。

        GapRB (float): 回旋镖的桥臂与外部总线波导之间的耦合间隙。
        LengthCouple (float): 总线波导上用于与回旋镖桥臂耦合的直波导段长度。
        IsHeatIn (bool): Boomerang单元内环是否加热。
        IsHeatOut (bool): Boomerang单元外环是否加热。
        TypeHeater (str): 加热器类型。
        oplayer, heatlayer, routelayer, vialayer: 相应的GDS图层定义。

    返回:
        Component: 生成的带耦合的单个回旋镖环形谐振器组件。

    端口:
        Input: 总线波导的输入端口。
        Through: 总线波导的直通端口。
        Add: (如果设计为四端口) 总线波导的增加端口。
        Drop: (如果设计为四端口) 总线波导的下载端口。
        (以及从 Boomerang 单元继承的加热器端口，如果启用)

    信息 (Info):
        length (float): Boomerang 单元的光学路径长度。
    """
    c = gf.Component()
    # sections
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="sine")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="sine")
    # boomerang1
    Cring1 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2, LengthTaper,
                            IsHeatIn, IsHeatOut, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring1.rotate(90, Cring1.ports["Lo1"].center)
    # input-through
    sbend_in = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    sbend_out = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_in = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_in.connect("o1", Cring1.ports["Lb1"])
    str_couple_in.movex(-GapRB - WidthStraight).movey(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_in.connect("o2", str_couple_in.ports["o1"], mirror=True)
    sbend_out.connect("o1", str_couple_in.ports["o2"])
    # add drop
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
    c.info['length'] = Cring1.info['length']
    return c


# 双回旋镖腔
@gf.cell
def RingDouBoomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        WidthHeat: float = 4,
        WidthRoute: float = 20,
        WidthVia: float = 0.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        Spacing: float = 1,
        GapRR: float = 0.3,
        GapRB: float = 0.5,
        GapHeat: float = 80,
        DeltaHeat: float = 100,
        DeltaLB2: float = 2,
        LengthBridge1: float = 10,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        LengthCouple: float = 10,
        IsHeat: bool = True,
        TypeHeater: str = "default",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个包含两个串联（或特定方式耦合）的“回旋镖”谐振器的组件。
    两个回旋镖单元可以通过 `DeltaLB2` 参数实现结构上的微小差异，从而可能导致谐振频率的失谐。
    外部通过总线波导进行整体的输入和输出。

    参数:
        (大部分参数与 RingBoomerang 相同，用于配置每个 Boomerang 单元)
        DeltaLB2 (float): 第二个 Boomerang 单元的 `LengthBridge2` 参数相对于第一个单元的增量。
                          例如，如果第一个 L_B2=40, DeltaLB2=2, 则第二个 L_B2=42。
                          用于在两个回旋镖之间引入细微的路径长度差异。
        IsHeat (bool): 控制两个 Boomerang 单元是否都启用其内部的加热器逻辑。
                       (注意：Boomerang 单元本身有 IsHeatIn, IsHeatOut 参数，
                        此处的 IsHeat 可能是一个总开关，或者需要更细致地传递给子单元。)
                       原代码中，Cring1 的 IsHeatIn=False, IsHeatOut=IsHeat。
                       Cring2 的 IsHeatIn=IsHeat, IsHeatOut=False。这是一种特定的加热配置。

    返回:
        Component: 生成的双回旋镖谐振器组件。

    端口:
        Input: 组件的总输入端口。
        Through: 组件的总直通端口。
        Add: 组件的总增加端口。
        Drop: 组件的总下载端口。
        R1Lo1, R1Lo2, ..., R2Ro1, R2Ro2, ...: 从两个 Boomerang 单元暴露出的原始端口，带R1/R2前缀。
        (以及可能的加热器端口)

    信息 (Info):
        R1length (float): 第一个 Boomerang 单元的光学路径长度。
        R2length (float): 第二个 Boomerang 单元的光学路径长度。
    """
    c = gf.Component()
    # sections
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="sine")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="sine")
    # boomerang1
    Cring1 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2, LengthTaper,
                            False, IsHeat, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring1.rotate(90, Cring1.ports["Lo1"].center)
    Cring2 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2 + DeltaLB2, LengthTaper,
                            IsHeat, False, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring2.connect("Lo2", Cring1.ports["Ro1"], allow_width_mismatch=True)
    Cring2.move(((WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2),
                 (WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2)))
    # add drop
    sbend_add = c << gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=90, cross_section=X_str)
    sbend_drop = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_ad = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_ad.connect("o1", Cring2.ports["Lb1"])
    str_couple_ad.movex(-GapRB - WidthStraight).movey(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_add.connect("o2", str_couple_ad.ports["o1"])
    sbend_drop.connect("o1", str_couple_ad.ports["o2"])
    c.add_port("Add", port=sbend_add.ports['o1'])
    c.add_port("Drop", port=sbend_drop.ports['o2'])
    c.info['R1length'] = Cring1.info['length']
    c.info['R2length'] = Cring2.info['length']
    # input through
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
        c.add_port("R1" + port, port=Cring1.ports[port])
    for port in Cring2.ports:
        c.add_port("R2" + port, port=Cring2.ports[port])
    return c


# 三回旋镖腔
@gf.cell
def RingTriBoomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        WidthHeat: float = 4,
        WidthRoute: float = 20,
        WidthVia: float = 0.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        Spacing: float = 1,
        GapRR: float = 0.3,
        GapRB: float = 0.5,
        GapHeat: float = 80,
        DeltaHeat: float = 100,
        DeltaLB2: float = 2,
        LengthBridge1: float = 10,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        LengthCouple: float = 10,
        IsHeat: bool = True,
        TypeHeater: str = "default",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    c = gf.Component()
    # sections
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="sine")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="sine")
    # boomerang1
    Cring1 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2, LengthTaper,
                            False, False, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring1.rotate(90, Cring1.ports["Lo1"].center)
    Cring2 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2 + DeltaLB2, LengthTaper,
                            IsHeat, False, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring2.connect("Lo2", Cring1.ports["Ro1"], allow_width_mismatch=True)
    Cring2.move(((WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2),
                 (WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2)))
    Cring3 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2 - DeltaLB2, LengthTaper,
                            False, IsHeat, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring3.connect("Lo1", Cring1.ports["Ro2"], allow_width_mismatch=True)
    Cring3.move((-(WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2),
                 -(WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2)))
    c.info['R1length'] = Cring1.info['length']
    c.info['R2length'] = Cring2.info['length']
    c.info['R3length'] = Cring3.info['length']
    # input-through
    sbend_in = c << gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=90, cross_section=X_str)
    sbend_out = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_in = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_in.connect("o1", Cring1.ports["Lb1"]).movex(-GapRB - WidthStraight).movey(
        LengthBridge2 / 2 - LengthCouple / 2)
    sbend_in.connect("o2", str_couple_in.ports["o1"])
    sbend_out.connect("o1", str_couple_in.ports["o2"])
    c.add_port("Input", port=sbend_in.ports['o1'])
    c.add_port("Through", port=sbend_out.ports['o2'])
    # add drop
    sbend_add = c << gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=-90, cross_section=X_str)
    sbend_drop = c << gf.c.bend_s(size=[100, -10], cross_section=X_str)
    str_couple_ad = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_ad.connect("o1", Cring1.ports["Rb1"]).movey(-GapRB - WidthStraight).movex(
        LengthBridge2 / 2 - LengthCouple / 2)
    sbend_add.connect("o2", str_couple_ad.ports["o1"])
    sbend_drop.connect("o1", str_couple_ad.ports["o2"])
    c.add_port("Add", port=sbend_add.ports['o1'])
    c.add_port("Drop", port=sbend_drop.ports['o2'])
    for port in Cring1.ports:
        c.add_port("R1" + port, port=Cring1.ports[port])
    for port in Cring2.ports:
        c.add_port("R2" + port, port=Cring2.ports[port])
    for port in Cring3.ports:
        c.add_port("R3" + port, port=Cring3.ports[port])
    return c


# %% 导出所有函数
__all__ = [
    'Boomerang', 'RingBoomerang', 'RingDouBoomerang', 'RingTriBoomerang'
]
