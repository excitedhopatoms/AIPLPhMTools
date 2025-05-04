import gdsfactory as gf
import numpy as np
import csv
from gdsfactory.typings import Layer
from gdsfactory.component import Component
from gdsfactory.path import Path, _fresnel, _rotate_points
from gdsfactory.typings import LayerSpec
from gdsfactory.cross_section import cross_section
from gdsfactory.generic_tech import get_generic_pdk
from gdsfactory.pdk import get_active_pdk
from gdsfactory.typings import Layer, LayerSpec, LayerSpecs, Optional, Callable
from .BasicDefine import *
from .Ring import *
from .RaceTrack import *

# %% DoubleRingPulley
@gf.cell
def DoubleRingPulley(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        LengthR2R: float = 150,
        RadiusRing: float = 100,
        RadiusR2R: float = None,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        GapHeat: float = 10,
        DeltaHeat: float = 0,
        AngleCouple: float = 20,
        IsHeat: bool = False,
        TypeHeater:str = "default",
        TypeR2R:str = "strsight",
        DirectionsHeater:[str] = ["up","up"],
        DirectionsRing:[str] = ["up","up"],
        Name: str = "Ring_Pulley",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个双环形谐振器组件，支持加热电极和环形波导的连接。
    双环形谐振器由两个环形波导组成，可以通过参数调整环的尺寸、间距和加热电极的配置。

    参数：
        WidthRing: 环形波导的宽度（单位：um）。
        WidthNear: 靠近环形波导的波导宽度（单位：um）。
        WidthHeat: 加热电极的宽度（单位：um）。
        WidthEnd: 末端波导的宽度（单位：um）。
        Pitch: 结构的间距（单位：um）。
        Period: 结构的周期（单位：um）。
        LengthTaper: 锥形波导的长度（单位：um）。
        LengthR2R: 环形波导之间的连接长度（单位：um）。
        RadiusRing: 环形波导的半径（单位：um）。
        RadiusBend0: 弯曲波导的半径（单位：um）。
        DeltaRadius: 两个环形波导的半径差（单位：um）。
        GapRing: 环形波导之间的间隙（单位：um）。
        EndPort: 需要连接的端口列表。
        AngleCouple: 耦合角度（单位：度）。
        IsHeat: 是否包含加热电极。
        Name: 组件名称。
        oplayer: 光学波导层的定义。
        heatlayer: 加热层的定义。

    返回：
        Component: 包含双环形谐振器的组件。

    端口：
        o1: 第一个环形波导的输入端口。
        o2: 第二个环形波导的输入端口。
        r2ro1: 环形波导之间的连接端口。
        r1A: 第一个环形波导的 Add 端口。
        r1D: 第一个环形波导的 Drop 端口。
        r1I: 第一个环形波导的 Input 端口。
        r1T: 第一个环形波导的 Through 端口。
        r2A: 第二个环形波导的 Add 端口。
        r2D: 第二个环形波导的 Drop 端口。
        r2I: 第二个环形波导的 Input 端口。
        r2T: 第二个环形波导的 Through 端口。
        R1HeatIn: 第一个环形波导的加热输入端口（如果包含加热电极）。
        R1HeatOut: 第一个环形波导的加热输出端口（如果包含加热电极）。
        R2HeatIn: 第二个环形波导的加热输入端口（如果包含加热电极）。
        R2HeatOut: 第二个环形波导的加热输出端口（如果包含加热电极）。
    """
    c = gf.Component(Name)
    ring1 = c << RingPulleyT1(
        WidthRing=WidthRing, WidthNear=WidthNear, WidthHeat=WidthHeat,
        RadiusRing=RadiusRing, GapRing=GapRing, GapHeat=GapHeat,DeltaHeat=DeltaHeat,
        AngleCouple=AngleCouple,
        oplayer=oplayer, heatlayer=heatlayer,TypeHeater=TypeHeater,IsHeat=IsHeat,DirectionHeater=DirectionsHeater[0]
    )
    ring2 = c << RingPulleyT1(
        WidthRing=WidthRing, WidthNear=WidthNear, WidthHeat=WidthHeat,
        RadiusRing=RadiusRing+DeltaRadius, GapRing=GapRing, GapHeat=GapHeat,DeltaHeat=DeltaHeat,
        AngleCouple=AngleCouple,
        oplayer=oplayer, heatlayer=heatlayer,TypeHeater=TypeHeater,IsHeat=IsHeat,DirectionHeater=DirectionsHeater[1]
    )
    if TypeR2R == "straight":
        str_R2R = c << gf.c.straight(width=WidthNear, length=LengthR2R, layer=oplayer)
        str_R2R.connect("o1", ring1.ports["Drop"])
        ring2.connect("Drop", str_R2R.ports["o2"], allow_width_mismatch=True)
    elif TypeR2R == "bend":
        if RadiusR2R is None:
            RadiusR2R = RadiusRing-10
        str_R2R = c << gf.c.straight(width=WidthNear, length=LengthR2R, layer=oplayer)
        str_R2R.connect("o1", ring1.ports["Drop"])
        ring2.connect("Drop", str_R2R.ports["o2"], allow_width_mismatch=True)
        # Add circular bends for ring-to-ring connection
        bendl1 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=90, layer=oplayer)
        bendr1 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=90, layer=oplayer)
        bendl2 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=-90, layer=oplayer)
        bendr2 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=-90, layer=oplayer)
        bendl1.connect("o1", ring1.ports["Drop"])
        bendl2.connect("o1", bendl1.ports["o2"])
        bendr1.connect("o2", ring2.ports["Drop"])
        bendr2.connect("o2", bendr1.ports["o1"])
        route = gf.routing.get_route(bendl2.ports["o2"], bendr2.ports["o1"], width=WidthNear, layer=oplayer)
        c.add(route.references)
        c.remove(str_R2R)

    if DirectionsRing[0] == "down":
        ring1.mirror_y("Drop")
    if DirectionsRing[1] == "up":
        ring2.mirror_y("Drop")
    c.add_port(name="o1", port=ring1.ports["Input"])
    c.add_port(name="o2", port=ring2.ports["Input"])
    c.add_port(name="R2Ro1", port=str_R2R.ports["o1"])
    c.add_port(name="R1Add", port=ring1.ports["Add"])
    c.add_port(name="R1Drop", port=ring1.ports["Drop"])
    c.add_port(name="R1Input", port=ring1.ports["Input"])
    c.add_port(name="R1Through", port=ring1.ports["Through"])
    c.add_port(name="R2Add", port=ring2.ports["Add"])
    c.add_port(name="R2Drop", port=ring2.ports["Drop"])
    c.add_port(name="R2Input", port=ring2.ports["Input"])
    c.add_port(name="R2Through", port=ring2.ports["Through"])

    if IsHeat:
        for port in ring1.ports:
            if "Heat" in port:
                c.add_port(name="R1"+port, port=ring1.ports[port])
        for port in ring2.ports:
            if "Heat" in port:
                c.add_port(name="R2"+port, port=ring2.ports[port])
    add_labels_to_ports(c,label_layer=(512,8))
    return c


# %% DoubleRingPulley2：Snake Heater
@gf.cell
def DoubleRingPulley2HSn(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        LengthR2R: float = 150,
        RadiusRing: float = 100,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        GapHeat: float = 1,
        AngleCouple: float = 20,
        IsHeat: bool = True,
        TypeHeater:str = "snake",
        Name: str = "Ring_Pulley_Snake_Heater",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个带有蛇形加热电极的双环形谐振器组件。

    参数：
        WidthRing: 环形波导的宽度（单位：um）。
        WidthNear: 靠近环形波导的波导宽度（单位：um）。
        WidthHeat: 加热电极的宽度（单位：um）。
        LengthR2R: 环形波导之间的连接长度（单位：um）。
        RadiusRing: 环形波导的半径（单位：um）。
        DeltaRadius: 两个环形波导的半径差（单位：um）。
        GapRing: 环形波导之间的间隙（单位：um）。
        GapHeat: 加热电极的间隙（单位：um）。
        AngleCouple: 耦合角度（单位：度）。
        IsHeat: 是否包含加热电极。
        Name: 组件名称。
        oplayer: 光学波导层的定义。
        heatlayer: 加热层的定义。

    返回：
        Component: 包含双环形谐振器和加热电极的组件。

    端口：
        o1: 第一个环形波导的输入端口。
        o2: 第二个环形波导的 Through 端口。
        r2ro1: 环形波导之间的连接端口。
        R1A: 第一个环形波导的 Add 端口。
        r1D: 第一个环形波导的 Drop 端口。
        r1I: 第一个环形波导的 Input 端口。
        r1T: 第一个环形波导的 Through 端口。
        r2A: 第二个环形波导的 Add 端口。
        r2D: 第二个环形波导的 Drop 端口。
        r2I: 第二个环形波导的 Input 端口。
        r2T: 第二个环形波导的 Through 端口。
        R1HeatIn: 第一个环形波导的加热输入端口（如果包含加热电极）。
        R1HeatOut: 第一个环形波导的加热输出端口（如果包含加热电极）。
        R2HeatIn: 第二个环形波导的加热输入端口（如果包含加热电极）。
        R2HeatOut: 第二个环形波导的加热输出端口（如果包含加热电极）。
    """
    c = DoubleRingPulley(
        WidthRing=WidthRing,
        WidthNear=WidthNear,
        WidthHeat=WidthHeat,
        LengthR2R=LengthR2R,
        RadiusRing=RadiusRing,
        DeltaRadius=DeltaRadius,
        GapRing=GapRing,
        GapHeat=GapHeat,
        AngleCouple=AngleCouple,
        IsHeat=IsHeat,
        Name=Name,
        oplayer=oplayer,
        heatlayer=heatlayer,
        TypeHeater=TypeHeater,
    )
    add_labels_to_ports(c)
    return c


# %% DoubleRingPulley2：Snake Heater & ring to ring round
@gf.cell
def DoubleRingPulley2_1HSn(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        LengthR2R: float = 700,
        RadiusRing: float = 100,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        GapHeat: float = 1,
        AngleCouple: float = 20,
        Name: str = "Ring_Pulley_Snake_Heater_Round",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个带有蛇形加热电极和环形波导之间圆形连接的双环形谐振器组件。

    参数：
        WidthRing: 环形波导的宽度（单位：um）。
        WidthNear: 靠近环形波导的波导宽度（单位：um）。
        WidthHeat: 加热电极的宽度（单位：um）。
        LengthR2R: 环形波导之间的连接长度（单位：um）。
        RadiusRing: 环形波导的半径（单位：um）。
        DeltaRadius: 两个环形波导的半径差（单位：um）。
        GapRing: 环形波导之间的间隙（单位：um）。
        GapHeat: 加热电极的间隙（单位：um）。
        AngleCouple: 耦合角度（单位：度）。
        IsHeat: 是否包含加热电极。
        Name: 组件名称。
        oplayer: 光学波导层的定义。
        heatlayer: 加热层的定义。

    返回：
        Component: 包含双环形谐振器和加热电极的组件。

    端口：
        o1: 第一个环形波导的输入端口。
        o2: 第二个环形波导的 Through 端口。
        r2ro1: 环形波导之间的连接端口。
        r1A: 第一个环形波导的 Add 端口。
        r1D: 第一个环形波导的 Drop 端口。
        r1I: 第一个环形波导的 Input 端口。
        r1T: 第一个环形波导的 Through 端口。
        r2A: 第二个环形波导的 Add 端口。
        r2D: 第二个环形波导的 Drop 端口。
        r2I: 第二个环形波导的 Input 端口。
        r2T: 第二个环形波导的 Through 端口。
        1HeatIn: 第一个环形波导的加热输入端口（如果包含加热电极）。
        1HeatOut: 第一个环形波导的加热输出端口（如果包含加热电极）。
        2HeatIn: 第二个环形波导的加热输入端口（如果包含加热电极）。
        2HeatOut: 第二个环形波导的加热输出端口（如果包含加热电极）。
    """
    c = DoubleRingPulley(
        WidthRing=WidthRing,
        WidthNear=WidthNear,
        WidthHeat=WidthHeat,
        LengthR2R=LengthR2R,
        RadiusRing=RadiusRing,
        DeltaRadius=DeltaRadius,
        GapRing=GapRing,
        GapHeat=GapHeat,
        AngleCouple=AngleCouple,
        IsHeat=True,
        Name=Name,
        oplayer=oplayer,
        heatlayer=heatlayer,
        TypeHeater="snake",
        TypeR2R="bend",
    )
    return c


# %% ADRAPRADR: ADRing + APRing + ADRing (with crossing ?)
@gf.cell
def ADRAPRADR(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        WidthSingle: float = 0.45,
        LengthTaper: float = 100,
        LengthR2R: float = 50,
        LengthR2C: float = 2,
        RadiusRing: float = 100,
        RadiusCrossBend: float = 100,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        AngleCouple: float = 20,
        AngleCouple3: float = 40,
        IsHeat: bool = False,
        IsSquare: bool = True,
        Name: str = "ADRAPRADR",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        CrossComp: Component = None,
) -> Component:
    """
    创建一个包含三个环形谐振器和交叉波导的组件。

    参数：
        WidthRing: 环形波导的宽度（单位：um）。
        WidthNear: 靠近环形波导的波导宽度（单位：um）。
        WidthHeat: 加热电极的宽度（单位：um）。
        WidthSingle: 单模波导的宽度（单位：um）。
        LengthTaper: 锥形波导的长度（单位：um）。
        LengthR2R: 环形波导之间的连接长度（单位：um）。
        LengthR2C: 环形波导与交叉波导的连接长度（单位：um）。
        RadiusRing: 环形波导的半径（单位：um）。
        RadiusCrossBend: 交叉波导的弯曲半径（单位：um）。
        DeltaRadius: 环形波导的半径差（单位：um）。
        GapRing: 环形波导之间的间隙（单位：um）。
        AngleCouple: 耦合角度（单位：度）。
        AngleCouple3: 第三个环形谐振器的耦合角度（单位：度）。
        IsHeat: 是否包含加热电极。
        IsSquare: 是否使用方形布局。
        Name: 组件名称。
        oplayer: 光学波导层的定义。
        heatlayer: 加热层的定义。
        CrossComp: 交叉波导组件。

    返回：
        Component: 包含三个环形谐振器和交叉波导的组件。

    端口：
        r1Th: 第一个环形波导的 Through 端口。
        r1Ad: 第一个环形波导的 Add 端口。
        r2Th: 第二个环形波导的 Through 端口。
        r2Ad: 第二个环形波导的 Add 端口。
        r1L: 第一个环形波导的 RingL 端口。
        r1R: 第一个环形波导的 RingR 端口。
        r2L: 第二个环形波导的 RingL 端口。
        r2R: 第二个环形波导的 RingR 端口。
        r3L: 第三个环形波导的 RingL 端口。
        r3R: 第三个环形波导的 RingR 端口。
        co2: 交叉波导的输出端口 2。
        co3: 交叉波导的输出端口 3。
    """
    TriRing = gf.Component(Name)
    ring1 = TriRing << RingPulley(
        IsAD=True, WidthRing=WidthRing, RadiusRing=RadiusRing, oplayer=oplayer, GapRing=GapRing,
        WidthNear=WidthNear, AngleCouple=AngleCouple, IsHeat=IsHeat, heatlayer=heatlayer, WidthHeat=WidthHeat
    )
    ring2 = TriRing << RingPulley(
        IsAD=True, WidthRing=WidthRing, RadiusRing=RadiusRing + DeltaRadius, oplayer=oplayer, GapRing=GapRing,
        WidthNear=WidthNear, AngleCouple=AngleCouple, IsHeat=IsHeat, heatlayer=heatlayer, WidthHeat=WidthHeat
    )
    ring3 = TriRing << RingPulley2(
        WidthRing=WidthRing, RadiusRing=RadiusRing + DeltaRadius / 2, oplayer=oplayer, GapRing=GapRing,
        WidthNear=WidthNear, AngleCouple=AngleCouple3, IsHeat=IsHeat, heatlayer=heatlayer, WidthHeat=WidthHeat
    )
    str_r1r3 = TriRing << gf.c.straight(length=LengthR2R, width=WidthNear, layer=oplayer)
    str_r2r3 = TriRing << gf.c.straight(length=LengthR2R, width=WidthNear, layer=oplayer)
    str_r1r3.connect("o1", ring1.ports["Drop"])
    ring3.connect("Input", str_r1r3.ports["o2"]).mirror_y("Input")
    str_r2r3.connect("o1", ring3.ports["Through"])
    ring2.connect("Drop", str_r2r3.ports["o2"])

    if IsSquare and CrossComp:
        crossing = TriRing << CrossComp
        str_r12c = TriRing << gf.c.straight(length=LengthR2C, width=WidthNear, layer=oplayer)
        str_r22c = TriRing << gf.c.straight(length=LengthR2C, width=WidthNear, layer=oplayer)
        str_r12c.connect("o2", ring1.ports["Input"])
        str_r22c.connect("o1", ring2.ports["Input"])
        bend_r12c = TriRing << gf.c.bend_euler(width=WidthNear, radius=RadiusCrossBend, angle=-90, layer=oplayer)
        bend_r22c = TriRing << gf.c.bend_euler(width=WidthNear, radius=RadiusCrossBend, angle=-90, layer=oplayer)
        bend_r12c.connect("o2", str_r12c.ports["o1"])
        bend_r22c.connect("o1", str_r22c.ports["o2"])
        crossing.connect("o1", bend_r12c.ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True)
        crossing.movey(bend_r22c.ports["o2"].center[1] - crossing.ports["o4"].center[1])
        route_cr1 = gf.routing.get_route(crossing.ports["o1"], bend_r12c.ports["o1"], width=WidthNear, layer=oplayer)
        route_cr2 = gf.routing.get_route(crossing.ports["o4"], bend_r22c.ports["o2"], width=WidthNear, layer=oplayer)
        TriRing.add(route_cr1.references)
        TriRing.add(route_cr2.references)
        TriRing.add_port(name="co2", port=crossing.ports["o2"])
        TriRing.add_port(name="co3", port=crossing.ports["o3"])

    TriRing.add_port("r1Th", port=ring1.ports["Through"])
    TriRing.add_port("r1Ad", port=ring1.ports["Add"])
    TriRing.add_port("r2Th", port=ring2.ports["Through"])
    TriRing.add_port("r2Ad", port=ring2.ports["Add"])
    TriRing.add_port("r1L", port=ring1.ports["RingL"])
    TriRing.add_port("r1R", port=ring1.ports["RingR"])
    TriRing.add_port("r2L", port=ring2.ports["RingL"])
    TriRing.add_port("r2R", port=ring2.ports["RingR"])
    TriRing.add_port("r3L", port=ring3.ports["RingL"])
    TriRing.add_port("r3R", port=ring3.ports["RingR"])
    add_labels_to_ports(TriRing)
    return TriRing


# %% DoubleRaceTrackPulley
@gf.cell
def DoubleRaceTrackPulley(
        WidthRing: float = 8,
        WidthNear: float = 5,
        LengthRun: float = 200,
        LengthTaper: float = 100,
        LengthR2R: float = 300,
        DeltaLength: float = 2,
        RadiusRing: float = 100,
        GapRing: float = 1,
        AngleCouple: float = 20,
        IsSameSide: bool = True,
        layer: LayerSpec = LAYER.WG,
        Name: str = "Double_Race_Track_Pulley",
) -> Component:
    """
    创建一个双跑道形谐振器组件。

    参数：
        WidthRing: 跑道形波导的宽度（单位：um）。
        WidthNear: 靠近跑道形波导的波导宽度（单位：um）。
        WidthEnd: 末端波导的宽度（单位：um）。
        LengthRun: 跑道形波导的直线长度（单位：um）。
        LengthTaper: 锥形波导的长度（单位：um）。
        LengthR2R: 跑道形波导之间的连接长度（单位：um）。
        DeltaLength: 两个跑道形波导的直线长度差（单位：um）。
        RadiusRing: 跑道形波导的半径（单位：um）。
        RadiusBend0: 弯曲波导的半径（单位：um）。
        GapRing: 跑道形波导之间的间隙（单位：um）。
        AngleCouple: 耦合角度（单位：度）。
        Pitch: 结构的间距（单位：um）。
        Period: 结构的周期（单位：um）。
        IsSameSide: 是否在同一侧连接。
        layer: 波导层的定义。
        layers: 多波导层的定义。
        Name: 组件名称。

    返回：
        Component: 包含双跑道形谐振器的组件。

    端口：
        o1: 第一个跑道形波导的输入端口。
        o2: 第二个跑道形波导的输入端口。
        R1cen1: 第一个跑道形波导的中心端口 1。
        R1cen2: 第一个跑道形波导的中心端口 2。
        R2cen1: 第二个跑道形波导的中心端口 1。
        R2cen2: 第二个跑道形波导的中心端口 2。
    """
    c = gf.Component(Name)
    layer = gf.get_layer(layer)
    ring1 = c << RaceTrackPulley(
        WidthRing=WidthRing, WidthNear=WidthNear, GapRing=GapRing,
        LengthRun=LengthRun, RadiusRing=RadiusRing, AngleCouple=AngleCouple, layer=layer
    )
    ring2 = c << RaceTrackPulley(
        WidthRing=WidthRing, WidthNear=WidthNear, GapRing=GapRing,
        LengthRun=LengthRun + DeltaLength, RadiusRing=RadiusRing, AngleCouple=AngleCouple, layer=layer
    )
    str_r2r = c << gf.c.straight(width=WidthNear, length=LengthR2R, layer=layer)
    str_r2r.connect("o1", ring1.ports["Drop"])
    ring2.connect("Drop", str_r2r.ports["o2"])
    if IsSameSide:
        ring2.mirror_y(port_name="Drop")

    c.add_port(name="o1", port=ring1.ports["Input"])
    c.add_port(name="o2", port=ring2.ports["Input"])
    c.add_port(name="R1cen1", port=ring1.ports["Rcen1"])
    c.add_port(name="R1cen2", port=ring1.ports["Rcen2"])
    c.add_port(name="R2cen1", port=ring2.ports["Rcen1"])
    c.add_port(name="R2cen2", port=ring2.ports["Rcen2"])
    return c

# %% CoupleCavity

@gf.cell
def CoupleRingDRT1(
        WidthRing1: float = 1,
        WidthNear1: float = 0.9,
        WidthHeat1: float = 2,
        RadiusRing1: float = 100,
        GapRB1:float = 2,
        GapHeat1:float = 1,
        DeltaHeat1: float = 0,
        AngleCouple1: float = 20,
        WidthRing2: float = None,
        WidthNear2: float = None,
        WidthHeat2: float = None,
        LengthNear2: float = 110,
        RadiusRing2: float = None,
        GapRB2:float = 3,
        GapHeat2: float = None,
        DeltaHeat2: float = 0,
        AngleR12:float = 30,
        GapRR: float = 1,
        GapHeat: float = 10,
        IsHeat: bool = True,
        TypeHeaterR1:str = "default",
        TypeHeaterR2:str = "default",
        TypeR2R:str = "strsight",
        DirectionsHeater:[str] = ["up","down"],
        Name: str = "Ring_Pulley",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个双环形谐振器组件，支持加热电极和环形波导的连接。
    双环形谐振器由两个环形波导组成，可以通过参数调整环的尺寸、间距和加热电极的配置。

    参数：
        WidthRing: 环形波导的宽度（单位：um）。
        WidthNear: 靠近环形波导的波导宽度（单位：um）。
        WidthHeat: 加热电极的宽度（单位：um）。
        WidthEnd: 末端波导的宽度（单位：um）。
        Pitch: 结构的间距（单位：um）。
        Period: 结构的周期（单位：um）。
        LengthTaper: 锥形波导的长度（单位：um）。
        LengthR2R: 环形波导之间的连接长度（单位：um）。
        RadiusRing: 环形波导的半径（单位：um）。
        RadiusBend0: 弯曲波导的半径（单位：um）。
        DeltaRadius: 两个环形波导的半径差（单位：um）。
        GapRing: 环形波导之间的间隙（单位：um）。
        EndPort: 需要连接的端口列表。
        AngleCouple: 耦合角度（单位：度）。
        IsHeat: 是否包含加热电极。
        Name: 组件名称。
        oplayer: 光学波导层的定义。
        heatlayer: 加热层的定义。

    返回：
        Component: 包含双环形谐振器的组件。

    端口：
        o1: 第一个环形波导的输入端口。
        o2: 第二个环形波导的输入端口。
        r2ro1: 环形波导之间的连接端口。
        r1A: 第一个环形波导的 Add 端口。
        r1D: 第一个环形波导的 Drop 端口。
        r1I: 第一个环形波导的 Input 端口。
        r1T: 第一个环形波导的 Through 端口。
        r2A: 第二个环形波导的 Add 端口。
        r2D: 第二个环形波导的 Drop 端口。
        r2I: 第二个环形波导的 Input 端口。
        r2T: 第二个环形波导的 Through 端口。
        R1HeatIn: 第一个环形波导的加热输入端口（如果包含加热电极）。
        R1HeatOut: 第一个环形波导的加热输出端口（如果包含加热电极）。
        R2HeatIn: 第二个环形波导的加热输入端口（如果包含加热电极）。
        R2HeatOut: 第二个环形波导的加热输出端口（如果包含加热电极）。
    """
    if WidthRing2 is None:
        WidthRing2=WidthRing1
    if WidthHeat2 is None:
        WidthHeat2=WidthHeat1
    if RadiusRing2 is None:
        RadiusRing2 = RadiusRing1
    if WidthNear2 is None:
        WidthNear2= WidthNear1
    if GapHeat2 is None:
        GapHeat2 = GapHeat1
    if DeltaHeat2 is None:
        DeltaHeat2 = DeltaHeat1
    c = gf.Component(Name)
    ring1 = c << RingPulleyT1(
        WidthRing=WidthRing1, WidthNear=WidthNear1, WidthHeat=WidthHeat1,
        RadiusRing=RadiusRing1, GapRing=GapRB1, GapHeat=GapHeat1,DeltaHeat=DeltaHeat1,
        AngleCouple=AngleCouple1,IsAD=False,
        oplayer=oplayer, heatlayer=heatlayer,TypeHeater=TypeHeaterR1,IsHeat=IsHeat,DirectionHeater=DirectionsHeater[0]
    )
    ring2_c = gf.Component('ring2_c')
    ring2_c << gf.c.ring(width=WidthRing2,radius=RadiusRing2,layer=oplayer)
    ring2_c.add_port("RingC",center=[0,0],layer=oplayer,width=1)
    ring2 = c << ring2_c
    ring2.move(ring1.ports['RingC'].center+[0,-(RadiusRing1+RadiusRing2+WidthRing1/2+WidthRing2/2+GapRR)])
    ring2.rotate(AngleR12,ring1.ports['RingC'].center)
    str_ring2_1 = c << gf.c.straight(width=WidthNear2,length=LengthNear2/2,layer=oplayer)
    str_ring2_1.move(ring2.ports["RingC"].center+[0,-WidthRing2/2-WidthNear2/2-RadiusRing2-GapRB2])
    str_ring2_2 = c << gf.c.straight(width=WidthNear2, length=LengthNear2/2, layer=oplayer)
    str_ring2_2.connect('o2',str_ring2_1.ports['o1'])
    ring2_hc = RingPulleyT1(
        WidthRing=WidthRing2, WidthNear=WidthNear2, WidthHeat=WidthHeat2,
        RadiusRing=RadiusRing2, GapRing=GapRB2, GapHeat=GapHeat2,DeltaHeat=DeltaHeat2,
        AngleCouple=AngleCouple1,IsAD=False,
        oplayer=oplayer, heatlayer=heatlayer,TypeHeater=TypeHeaterR2,IsHeat=IsHeat,DirectionHeater=DirectionsHeater[1]
    )
    ring2h = c << GetFromLayer(ring2_hc,OLayer=heatlayer)
    ring2h.move(ring2.ports["RingC"].center-ring2h.ports["RingC"].center)

    # c.add_port(name="R1Add", port=ring1.ports["Add"])
    # c.add_port(name="R1Drop", port=ring1.ports["Drop"])
    c.add_port(name="Input", port=ring1.ports["Input"])
    c.add_port(name="Through", port=ring1.ports["Through"])
    c.add_port(name="Add", port=str_ring2_2.ports["o1"])
    c.add_port(name="Drop", port=str_ring2_1.ports["o2"])
    c.add_port(name="Ring1C", port=ring1.ports["RingC"])
    c.add_port(name="Ring2C", port=ring2.ports["RingC"])
    # c.add_port(name="R2Input", port=ring2.ports["Input"])
    # c.add_port(name="R2Through", port=ring2.ports["Through"])

    if IsHeat:
        for port in ring1.ports:
            if "Heat" in port:
                c.add_port(name="R1"+port, port=ring1.ports[port])
        for port in ring2h.ports:
            if "Heat" in port:
                c.add_port(name="R2"+port, port=ring2h.ports[port])
    # add_labels_to_ports(c,label_layer=(412,8))
    return c

if __name__ == "__main__":
    test = gf.Component("test")
    test << DoubleRingPulley2_1HSn()
    test.show()

__all__ = ['DoubleRingPulley', 'DoubleRaceTrackPulley', 'DoubleRingPulley2HSn', 'ADRAPRADR', 'DoubleRingPulley2_1HSn','CoupleRingDRT1']