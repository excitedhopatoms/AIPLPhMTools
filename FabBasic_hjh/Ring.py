from gdsfactory.component import Component

from AIPLPhMTools.FabBasic_hjh import Heater
from .BasicDefine import *
from .Heater import SnakeHeater, DifferentHeater
from .SnapMerge import *

# %% RingPulley1:straight pulley
@gf.cell
def RingPulley(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        RadiusRing: float = 100,
        GapRing: float = 1,
        AngleCouple: float = 20,
        IsAD: bool = True,
        Name: str = "Ring_Pullry",
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
        RotationHeater: float = 0,
) -> Component:
    """
    滑轮耦合（Pulley Coupler）环形谐振器组件。
    此函数是 `RingPulleyT1` 的简化接口，支持添加加热器和 Add-Drop 端口。

    参数:
        WidthRing: 环形波导的宽度 (µm)。
        WidthNear: 耦合总线波导的宽度 (µm)。
        RadiusRing: 环的半径 (µm)。
        GapRing: 环与耦合总线之间的间隙 (µm)。
        AngleCouple: 滑轮耦合器的耦合角度 (度)。
        IsAD: 是否包含 Add/Drop 端口（四端口器件）。False 则为双端口（Input/Through）。
        Name: 组件的名称。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。
        RotationHeater: 加热器绕环中心旋转的角度 (度)。

    返回:
        Component: 生成的滑轮耦合环形谐振器组件。

    端口:
        Input: 输入端口。
        Through: 直通端口。
        Add: (IsAD=True 时) 增加端口。
        Drop: (IsAD=True 时) 下载端口。
        RingL, RingR, RingC: 环上的参考端口。
        HeatIn, HeatOut: (HeaterConfig 不为 None 时) 加热器电学端口。
    """
    c = RingPulleyT1(
        WidthRing=WidthRing,
        WidthNear=WidthNear,
        RadiusRing=RadiusRing,
        GapRing=GapRing,
        AngleCouple=AngleCouple,
        IsAD=IsAD,
        oplayer=oplayer,
        HeaterConfig=HeaterConfig,
        RotationHeater=RotationHeater,
    )
    return c


# %% RingPulley1DC: 不同耦合器
@gf.cell
def RingPulley1DC(
        WidthRing: float = 1,
        WidthNear1: float = 0.9,
        WidthNear2: float = 2,
        RadiusRing: float = 100,
        GapRing1: float = 1,
        GapRing2: float = 2,
        AngleCouple1: float = 20,
        AngleCouple2: float = 40,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
        RotationHeater: float = 0,
) -> Component:
    """
    非对称滑轮耦合环形谐振器，上下两侧可具有不同的耦合参数。
    此函数是对 `RingPulleyT1` 的封装，通过设置非对称耦合参数实现。

    参数:
        WidthRing: 环形波导宽度 (µm)。
        WidthNear1: 上侧（Input/Through）耦合总线的宽度 (µm)。
        WidthNear2: 下侧（Add/Drop）耦合总线的宽度 (µm)。
        RadiusRing: 环的半径 (µm)。
        GapRing1: 上侧耦合间隙 (µm)。
        GapRing2: 下侧耦合间隙 (µm)。
        AngleCouple1: 上侧滑轮耦合角度 (度)。
        AngleCouple2: 下侧滑轮耦合角度 (度)。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。
        RotationHeater: 加热器绕环中心旋转的角度 (度)。

    返回:
        Component: 具有非对称耦合参数的滑轮环谐振器。

    端口:
        Input, Through, Add, Drop: 光学端口。
        RingL, RingR, RingC: 环上的参考端口。
        HeatIn, HeatOut: (HeaterConfig 不为 None 时) 加热器电学端口。
    """
    c = RingPulleyT1(
        WidthRing=WidthRing,
        WidthNear=WidthNear1,
        WidthNear2=WidthNear2,
        RadiusRing=RadiusRing,
        GapRing=GapRing1,
        GapRing2=GapRing2,
        AngleCouple=AngleCouple1,
        AngleCouple2=AngleCouple2,
        oplayer=oplayer,
        HeaterConfig=HeaterConfig,
        RotationHeater=RotationHeater,
    )
    return c


# %% RingPulley1HS: 加热侧
@gf.cell
def RingPulley1HS(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        RadiusRing: float = 1000,
        GapRing: float = 1,
        AngleCouple: float = 20,
        IsAD: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
        RotationHeater: float = 0,
) -> Component:
    """
    滑轮耦合环形谐振器，集成侧边（side）类型加热器。
    此函数是对 `RingPulleyT1` 的封装，将加热器类型固定为 "side"。

    参数:
        WidthRing: 环形波导宽度 (µm)。
        WidthNear: 耦合总线波导的宽度 (µm)。
        RadiusRing: 环的半径 (µm)，默认值 1000µm 较大。
        GapRing: 环与耦合总线之间的间隙 (µm)。
        AngleCouple: 滑轮耦合器的耦合角度 (度)。
        IsAD: 是否包含 Add/Drop 端口。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，其 WidthHeat/DeltaHeat 等参数会被沿用。
        RotationHeater: 加热器绕环中心旋转的角度 (度)。

    返回:
        Component: 带侧边加热器的滑轮环谐振器。

    端口:
        Input, Through: 光学端口。
        Add, Drop: (IsAD=True 时) 光学端口。
        RingL, RingR, RingC: 环上的参考端口。
        HeatIn, HeatOut: 加热器电学端口。
    """
    Heater1 = HeaterConfigClass(
        TypeHeater = "side",
        WidthHeat = HeaterConfig.WidthHeat,
        WidthRoute = HeaterConfig.WidthRoute,
        WidthVia = HeaterConfig.WidthVia,
        Spacing = HeaterConfig.Spacing,
        DeltaHeat = HeaterConfig.DeltaHeat,
        GapHeat = HeaterConfig.GapHeat,
        LayerHeat = HeaterConfig.LayerHeat,
        LayerRoute = HeaterConfig.LayerRoute,
        LayerVia = HeaterConfig.LayerVia,
    )
    c = RingPulleyT1(
        WidthRing=WidthRing,
        WidthNear=WidthNear,
        RadiusRing=RadiusRing,
        GapRing=GapRing,
        AngleCouple=AngleCouple,
        IsAD=IsAD,
        oplayer=oplayer,
        HeaterConfig=Heater1,
        RotationHeater=RotationHeater,
    )
    return c


# %% RingPulley1HSn: 加热蛇形
@gf.cell
def RingPulley1HSn(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        RadiusRing: float = 1000,
        GapRing: float = 1,
        AngleCouple: float = 20,
        IsAD: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
        RotationHeater: float = 0,
) -> Component:
    """
    滑轮耦合环形谐振器，集成蛇形（snake）类型加热器。
    此函数是对 `RingPulleyT1` 的封装，将加热器类型固定为 "snake"。

    参数:
        WidthRing: 环形波导宽度 (µm)。
        WidthNear: 耦合总线波导的宽度 (µm)。
        RadiusRing: 环的半径 (µm)，默认值 1000µm 较大。
        GapRing: 环与耦合总线之间的间隙 (µm)。
        AngleCouple: 滑轮耦合器的耦合角度 (度)。
        IsAD: 是否包含 Add/Drop 端口。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，其 GapHeat 控制蛇形加热器的间隙宽度。
        RotationHeater: 加热器绕环中心旋转的角度 (度)。

    返回:
        Component: 带蛇形加热器的滑轮环谐振器。

    端口:
        Input, Through: 光学端口。
        Add, Drop: (IsAD=True 时) 光学端口。
        RingL, RingR, RingC: 环上的参考端口。
        HeatIn, HeatOut: 加热器电学端口。
    """
    Heater1 = HeaterConfigClass(
        TypeHeater = "snake",
        WidthHeat = HeaterConfig.WidthHeat,
        WidthRoute = HeaterConfig.WidthRoute,
        WidthVia = HeaterConfig.WidthVia,
        Spacing = HeaterConfig.Spacing,
        DeltaHeat = HeaterConfig.DeltaHeat,
        GapHeat = HeaterConfig.GapHeat,
        LayerHeat = HeaterConfig.LayerHeat,
        LayerRoute = HeaterConfig.LayerRoute,
        LayerVia = HeaterConfig.LayerVia,
    )
    c = RingPulleyT1(
        WidthRing=WidthRing,
        WidthNear=WidthNear,
        RadiusRing=RadiusRing,
        GapRing=GapRing,
        AngleCouple=AngleCouple,
        IsAD=IsAD,
        oplayer=oplayer,
        HeaterConfig=Heater1,
        RotationHeater=RotationHeater,
    )
    return c


# %% RingPulley2: 滑轮输入输出
@gf.cell
def RingPulley2(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        RadiusRing: float = 100,
        GapRing: float = 1,
        AngleCouple: float = 20,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
        RotationHeater: float = 0,
) -> Component:
    """
    滑轮耦合环形谐振器，耦合臂具有特定弯曲形状，端口近似垂直引出。
    此函数是对 `RingPulleyT2` 的简化封装。

    参数:
        WidthRing: 环形波导宽度 (µm)。
        WidthNear: 耦合总线宽度 (µm)。
        RadiusRing: 环半径 (µm)。
        GapRing: 环与总线耦合间隙 (µm)。
        AngleCouple: 滑轮耦合器的耦合角度 (度)。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。
        RotationHeater: 加热器绕环中心旋转的角度 (度)。

    返回:
        Component: 特定耦合臂形状的滑轮环谐振器。

    端口:
        Input, Through: 光学输入和直通端口。
        RingL, RingR, RingD, RingU, RingC: 环上的参考端口。
        HeatIn, HeatOut: (HeaterConfig 不为 None 时) 加热器电学端口。
    """
    c = RingPulleyT2(WidthRing=WidthRing,WidthNear=WidthNear,RadiusRing=RadiusRing,GapRing=GapRing,AngleCouple=AngleCouple,
                     oplayer=oplayer,HeaterConfig=HeaterConfig,RotationHeater=RotationHeater,)
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
        oplayer: LayerSpec = LAYER.WG,
        elelayer: LayerSpec = LAYER.M1,
        RotationHeater: float = 0,
) -> Component:
    """
    `RingPulley2` 类型滑轮耦合环，集成双侧对称（bothside）加热器。
    此函数是对 `RingPulleyT2` 的特定配置封装。

    参数:
        WidthRing: 环形波导宽度 (µm)。
        WidthNear: 耦合总线宽度 (µm)。
        WidthEle: 单边加热条的宽度 (µm)。
        RadiusRing: 环半径 (µm)。
        GapRing: 环与总线耦合间隙 (µm)。
        DeltaEle: 加热条中心相对于环波导中心线的横向偏移量 (µm)。
        AngleCouple: 滑轮耦合器的耦合角度 (度)。
        oplayer: 光学波导层。
        elelayer: 加热电极层。
        RotationHeater: 加热器绕环中心旋转的角度 (度)。

    返回:
        Component: 带双侧对称加热器的滑轮环。

    端口:
        Input, Through: 光学端口。
        RingL, RingR, RingD, RingU, RingC: 环上的参考端口。
        HeatIn, HeatOut: 加热器电学端口。
    """
    Heater=HeaterConfigClass(
        WidthHeat=WidthEle,DeltaHeat=DeltaEle,LayerHeat=elelayer,TypeHeater='bothside',
    )
    c = RingPulleyT2(WidthRing=WidthRing,
                     WidthNear=WidthNear,
                     RadiusRing=RadiusRing,
                     GapRing=GapRing,
                     AngleCouple=AngleCouple,
                     oplayer=oplayer,
                     HeaterConfig=Heater,
                     RotationHeater=RotationHeater,)
    return c


# %% RingPulley3: 大角度耦合器
@gf.cell
def RingPulley3(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        RadiusRing: float = 100,
        GapRing: float = 1,
        AngleCouple: float = 90,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    大角度滑轮耦合环形谐振器，总线波导近似平行于环切线方向引出。
    耦合臂由短圆弧段和欧拉弯曲段组成。

    参数:
        WidthRing: 环形波导宽度 (µm)。
        WidthNear: 耦合总线宽度 (µm)。
        RadiusRing: 环半径 (µm)。
        GapRing: 环与总线耦合间隙 (µm)。
        AngleCouple: 耦合臂中圆弧段所占角度的一半 (度)，总线引出方向接近 180-AngleCouple 度。
        oplayer: 光学波导层。

    返回:
        Component: 大角度滑轮耦合环。

    端口:
        Input, Through: 光学输入和直通端口。
        RingL, RingR: 环左右两侧参考端口。
    """
    c = gf.Component()
    # 光学部分
    ring_path90 = gf.path.arc(radius=RadiusRing, angle=90)
    ring_path_all = ring_path90 + ring_path90 + ring_path90 + ring_path90
    ring_comp = c << gf.path.extrude(ring_path_all, width=WidthRing, layer=oplayer)
    couple_path_ring = gf.path.arc(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2, angle=AngleCouple / 2)
    couple_path_euler = euler_Bend_Half(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2,
                                        angle=(180 - AngleCouple) / 2, p=0.5)
    couple_path = couple_path_ring + couple_path_euler
    upcouple_comp1 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)
    upcouple_comp1.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
    upcouple_comp1.movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)
    upcouple_comp2.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
    upcouple_comp2.movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2.mirror_x(upcouple_comp2.ports["o1"].center[0])
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
        RadiusRing: float = 100,
        GapRing: float = 1,
        AngleCouple: float = 50,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    大角度滑轮耦合环形谐振器（变体），引出方向更偏向侧面。
    与 `RingPulley3` 类似，但欧拉弯曲角度为 (270-AngleCouple)/2。

    参数:
        WidthRing: 环形波导宽度 (µm)。
        WidthNear: 耦合总线宽度 (µm)。
        RadiusRing: 环半径 (µm)。
        GapRing: 环与总线耦合间隙 (µm)。
        AngleCouple: 耦合臂中圆弧段所占角度的一半 (度)。
        oplayer: 光学波导层。

    返回:
        Component: 大角度滑轮耦合环。

    端口:
        Input, Through: 光学输入和直通端口。
        RingL, RingR: 环左右两侧参考端口。
    """
    c = gf.Component()
    ring_path90 = gf.path.arc(radius=RadiusRing, angle=90)
    ring_path_all = ring_path90 + ring_path90 + ring_path90 + ring_path90
    ring_comp = c << gf.path.extrude(ring_path_all, width=WidthRing, layer=oplayer)
    couple_path_ring = gf.path.arc(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2, angle=AngleCouple / 2)
    couple_path_euler = euler_Bend_Half(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2,
                                        angle=(270 - AngleCouple) / 2, p=0.5)
    couple_path = couple_path_ring + couple_path_euler
    upcouple_comp1 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)
    upcouple_comp1.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
    upcouple_comp1.movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)
    upcouple_comp2.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
    upcouple_comp2.movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2.mirror_x(upcouple_comp2.ports["o1"].center[0])
    c.add_port(name="Input", port=upcouple_comp2.ports["o2"])
    c.add_port(name="Through", port=upcouple_comp1.ports["o2"])
    c.add_port(name="RingL", width=1, center=[-RadiusRing, RadiusRing], orientation=90, layer=oplayer)
    c.add_port(name="RingR", width=1, center=[RadiusRing, RadiusRing], orientation=90, layer=oplayer)
    return c


# %% RingFinger: 山形环形结构
@gf.cell
def RingFinger(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        RadiusCouple: float = 150,
        RadiusSide: float = 100,
        LengthCouple: float = 100,
        LengthSide: float = 100,
        LengthConnect: float = 180,
        GapRing: float = 1,
        AngleCouple: float = 20,
        AngleSide: float = 180,
        Name: str = "RingFinger",
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = heaterconfig0
) -> Component:
    """
    手指形（梳状）多弯曲环形谐振器，由两个对称半结构通过中间直波导连接。
    每个半结构包含多个弯曲和直线段，通过外部总线进行滑轮型耦合。

    参数:
        WidthRing: 环主体波导宽度 (µm)。
        WidthNear: 外部耦合总线波导宽度 (µm)。
        RadiusCouple: 耦合区域弯曲半径 (µm)。
        RadiusSide: 侧向突出部分弯曲半径 (µm)。
        LengthCouple: 耦合区域直线段长度 (µm)。
        LengthSide: 侧向突出部分直线段长度 (µm)。
        LengthConnect: 连接两个半结构的直波导长度 (µm)。
        GapRing: 环与耦合总线之间的间隙 (µm)。
        AngleCouple: 滑轮耦合臂的角度参数 (度)。
        AngleSide: 侧向突出部分弯曲总角度 (度)，180 度形成 U 型弯。
        Name: 组件名称。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象。

    返回:
        Component: 手指形环谐振器组件。

    端口:
        Input, Through: 光学输入和直通端口。
        Con1, Con2: 中间直波导两端参考端口。
        HeatIn, HeatOut: (HeaterConfig 不为 None 时) 加热器电学端口。
    """
    c = gf.Component()
    # 定义波导截面
    S_ring = gf.Section(width=WidthRing, layer=oplayer, port_names=["o1", "o2"])
    S_couple = gf.Section(width=WidthNear, layer=oplayer, port_names=["o1", "o2"])
    CS_ring = gf.CrossSection(sections=[S_ring])
    CS_couple = gf.CrossSection(sections=[S_couple])
    # 构建各路径段
    path_arc_ring = gf.path.arc(radius=RadiusCouple, angle=45)
    path_str_ring = gf.path.straight(length=LengthCouple)
    path_euler_ring = euler_Bend_Half(radius=RadiusCouple, angle=45)
    path_arc_couple = gf.path.arc(radius=RadiusCouple + WidthRing / 2 + GapRing + WidthNear / 2, angle=AngleCouple / 2)
    path_euler_couple = gf.path.euler(radius=RadiusCouple + WidthRing / 2 + GapRing + WidthNear / 2,
                                      angle=-AngleCouple / 2)
    path_euler_side = gf.path.euler(radius=RadiusSide, angle=-AngleSide)
    path_euler_side2 = gf.path.euler(radius=RadiusSide, angle=AngleSide)
    path_str_side = gf.path.straight(length=LengthSide)
    path_arc_connect = gf.path.arc(radius=RadiusSide, angle=90)
    path_str_connect = gf.path.straight(length=LengthConnect)
    # 组合路径
    path_ring = path_arc_ring + path_euler_ring + path_str_ring
    path_side = path_euler_side + path_str_side
    path_side2 = path_euler_side2 + path_str_side
    path_couple = path_arc_couple + path_euler_couple
    path_connect = path_str_connect + path_arc_connect
    path_half = path_ring + path_side + path_side2 + path_connect
    # 创建耦合总线
    CcoupleL = c << gf.path.extrude(path_couple, cross_section=CS_couple)
    CcoupleR = c << gf.path.extrude(path_couple, cross_section=CS_couple)
    # 创建左右半结构
    ChalfL = c << gf.path.extrude(path_half, cross_section=CS_ring)
    ChalfL.mirror_y(ChalfL.ports["o1"].center[1])
    ChalfR = c << gf.path.extrude(path_half, cross_section=CS_ring)
    ChalfR.connect("o1", other=ChalfL.ports["o1"])
    # 计算并创建中间连接直波导
    length_con = round(abs(ChalfL.ports["o2"].center[0] - ChalfR.ports["o2"].center[0]), 3)
    str_connect = c << GfCStraight(width=WidthRing, length=length_con, layer=oplayer)
    str_connect.connect("o1", other=ChalfL.ports["o2"])
    # 放置耦合总线
    CcoupleL.connect("o1", other=ChalfR.ports["o1"], allow_width_mismatch=True)
    CcoupleL.movey(GapRing + WidthNear / 2 + WidthRing / 2).mirror_y(CcoupleL.ports["o1"].center[1])
    CcoupleR.connect("o1", other=ChalfL.ports["o1"], allow_width_mismatch=True)
    CcoupleR.movey(GapRing + WidthNear / 2 + WidthRing / 2)
    print(Name + " " + str(path_half.length() * 2 + length_con))
    # 添加光学端口
    c.add_port(name="Input", port=CcoupleL.ports["o2"])
    c.add_port(name="Through", port=CcoupleR.ports["o2"])
    c.add_port(name="Con1", port=str_connect.ports["o1"])
    c.add_port(name="Con2", port=str_connect.ports["o2"])
    # 加热器部分
    if HeaterConfig:
        path_half_heat = path_side + path_side2 + path_connect
        HeatL = c << DifferentHeater(path_half_heat,WidthWG=WidthRing,HeaterConfig=HeaterConfig)
        HeatR = c << DifferentHeater(path_half_heat,WidthWG=WidthRing,HeaterConfig=HeaterConfig)
        HeatL.connect('HeatOut',ChalfL.ports["o2"],allow_width_mismatch=True,allow_layer_mismatch=True)
        HeatL.mirror_x(ChalfL.ports["o2"].center[0])
        HeatR.connect('HeatOut',ChalfR.ports["o2"],allow_width_mismatch=True,allow_layer_mismatch=True)
        HeatR.rotate(180,ChalfR.ports["o2"].center)
        path_con_heat = gf.path.straight(length_con)
        HeatCon = c << DifferentHeater(path_con_heat,WidthWG=WidthRing,HeaterConfig=HeaterConfig)
        HeatCon.connect('HeatIn',HeatL.ports["HeatOut"],allow_width_mismatch=True,allow_layer_mismatch=True)
        HeatCon.mirror_y(HeatL.ports["HeatOut"].center[1])
        c.add_port(name="HeatIn", port=HeatL.ports["HeatIn"])
        c.add_port(name="HeatOut", port=HeatR.ports["HeatIn"])
    return c


# %% RingPulleyT1: 通用环形耦合器
@gf.cell
def RingPulleyT1(
        WidthRing: float = 1.0,
        WidthNear: float = 0.9,
        WidthTrench: float = 2,
        RadiusRing: float = 100.0,
        WidthNear2: float = None,
        GapRing2: float = None,
        AngleCouple2: float = None,
        GapRing: float = 1.0,
        GapTrench: float = 10,
        AngleCouple: float = 20.0,
        IsAD: bool = True,
        IsTrench: bool = False,
        DirectionHeater: str = "up",
        RotationHeater: float = 0,
        HeaterConfig: HeaterConfigClass = None,
        oplayer: LayerSpec = LAYER.WG,
        trelayer: LayerSpec = (3, 0)
) -> Component:
    """
    通用滑轮耦合环形谐振器，本模块的核心构建单元。
    支持对称/非对称 Add-Drop 端口耦合参数、多种加热器类型及可选热隔离槽。

    参数:
        WidthRing: 环波导宽度 (µm)。
        WidthNear: Input/Through 侧耦合总线宽度 (µm)。
        WidthTrench: 热隔离槽宽度 (µm)。
        RadiusRing: 环半径 (µm)。
        WidthNear2: Add/Drop 侧耦合总线宽度 (µm)，None 则使用 WidthNear。
        GapRing2: Add/Drop 侧耦合间隙 (µm)，None 则使用 GapRing。
        AngleCouple2: Add/Drop 侧耦合角度 (度)，None 则使用 AngleCouple。
        GapRing: Input/Through 侧耦合间隙 (µm)。
        GapTrench: 波导边缘与热隔离槽内边缘的间隙 (µm)。
        AngleCouple: Input/Through 侧滑轮耦合角度 (度)。
        IsAD: 是否构建四端口 Add-Drop 器件，False 则仅 Input/Through。
        IsTrench: 是否在环周围添加热隔离槽。
        DirectionHeater: 加热器方向 ("up" 或 "down")。
        RotationHeater: 加热器绕环中心旋转角度 (度)，正值逆时针。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。
        oplayer: 光学波导层。
        trelayer: 热隔离槽层。

    返回:
        Component: 通用滑轮环谐振器组件。

    端口:
        Input, Through: 光学端口。
        Add, Drop: (IsAD=True 时) 光学端口。
        RingL, RingR, RingC: 环上的参考端口。
        HeatIn, HeatOut: (HeaterConfig 不为 None 时) 加热器电学端口。
    """
    c = gf.Component()
    # 处理非对称耦合参数
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
        IsAD = True
    # 光学部分：创建环形波导
    ring_path90 = gf.path.arc(radius=RadiusRing, angle=90)  # 创建 90 度的圆弧路径
    ring_path_all = ring_path90 + ring_path90 + ring_path90 + ring_path90  # 拼接成完整的环形路径
    ring_comp = c << gf.path.extrude(ring_path_all, width=WidthRing, layer=oplayer)  # 将路径转换为波导

    # 创建耦合波导
    couple_path_ring = gf.path.arc(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2,
                                   angle=AngleCouple / 2)  # 创建耦合圆弧路径
    couple_path_euler = euler_Bend_Half(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2,
                                        angle=-AngleCouple / 2)  # 创建欧拉弯曲路径
    couple_path = couple_path_ring + couple_path_euler  # 拼接成完整的耦合路径

    # 上耦合波导
    upcouple_comp1 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)  # 创建上耦合波导
    upcouple_comp1.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
    upcouple_comp1.movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)  # 连接并移动
    upcouple_comp2 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)  # 创建上耦合波导
    upcouple_comp2.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
    upcouple_comp2.movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)  # 连接并移动
    upcouple_comp2.rotate(angle=180, center=upcouple_comp2.ports["o1"].center)
    upcouple_comp2.mirror_y(upcouple_comp2.ports["o1"].center[1])  # 旋转和镜像
    c.add_port(name="Input", port=upcouple_comp2.ports["o2"])  # 添加输入端口
    c.add_port(name="Through", port=upcouple_comp1.ports["o2"])  # 添加直通端口

    # 环形波导端口
    c.add_port(name="RingL", center=[-RadiusRing, RadiusRing], orientation=90, width=WidthRing,
               layer=oplayer)  # 添加左侧环形端口
    c.add_port(name="RingR", center=[RadiusRing, RadiusRing], orientation=90, width=WidthRing,
               layer=oplayer)  # 添加右侧环形端口
    c.add_port(name="RingC", center=[0, RadiusRing], orientation=90, width=WidthRing, layer=oplayer)  # 添加中间环形端口
    # Add-Drop 端口
    if IsAD:
        couple_path_ring2 = gf.path.arc(radius=RadiusRing + GapRing2 + WidthNear2 / 2 + WidthRing / 2,
                                        angle=AngleCouple2 / 2)  # 创建耦合圆弧路径
        couple_path_euler2 = euler_Bend_Half(radius=RadiusRing + GapRing2 + WidthNear2 / 2 + WidthRing / 2,
                                             angle=-AngleCouple2 / 2)  # 创建欧拉弯曲路径
        couple_path2 = couple_path_ring2 + couple_path_euler2  # 拼接成完整的耦合路径
        downcouple_comp1 = c << gf.path.extrude(couple_path2, width=WidthNear2, layer=oplayer)  # 创建下耦合波导
        downcouple_comp1.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
        downcouple_comp1.movey(-GapRing2 - WidthNear2 / 2 - WidthRing / 2)  # 连接并移动
        downcouple_comp1.mirror_y(downcouple_comp1.ports["o1"].center[1])  # 镜像
        downcouple_comp2 = c << gf.path.extrude(couple_path2, width=WidthNear2, layer=oplayer)  # 创建下耦合波导
        downcouple_comp2.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
        downcouple_comp2.movey(-GapRing2 - WidthNear2 / 2 - WidthRing / 2)  # 连接并移动
        downcouple_comp2.rotate(center=downcouple_comp2.ports["o1"].center, angle=180)  # 旋转
        c.add_port(name="Add", port=downcouple_comp1.ports["o2"])  # 添加 Add 端口
        c.add_port(name="Drop", port=downcouple_comp2.ports["o2"])  # 添加 Drop 端口

    # 加热部分
    if HeaterConfig:
        DifferentHeater_local(c, WidthRing=WidthRing,RadiusRing=RadiusRing,HeaterConfig=HeaterConfig,DirectionHeater=DirectionHeater,RotationHeater=RotationHeater)
    if IsTrench:
        ring_tr = c << gf.c.ring(width=WidthTrench, layer=trelayer,
                                 radius=RadiusRing - WidthRing / 2 - WidthTrench / 2 - GapTrench)
        ring_tr.movey(RadiusRing)
    # c=snap_all_polygons_iteratively(c)
    add_labels_to_ports(c)
    return c


# %% RingPulleyT2: 通用环形耦合器2
@gf.cell
def RingPulleyT2(
        WidthRing: float = 1.0,
        WidthNear: float = 0.9,
        RadiusRing: float = 100.0,
        GapRing: float = 1.0,
        AngleCouple: float = 20.0,
        DirectionHeater: str = "up",
        RotationHeater: float = 0,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
) -> Component:
    """
    滑轮耦合环形谐振器，端口近似 90 度引出，不含 Add/Drop 端口。
    耦合臂由短圆弧段和欧拉弯曲段组成，欧拉弯角度为 (90-AngleCouple)/2。

    参数:
        WidthRing: 环波导宽度 (µm)。
        WidthNear: 耦合总线宽度 (µm)。
        RadiusRing: 环半径 (µm)。
        GapRing: 环与总线耦合间隙 (µm)。
        AngleCouple: 耦合臂中圆弧段所占角度 (度)。
        DirectionHeater: 加热器方向 ("up" 或 "down")。
        RotationHeater: 加热器绕环中心旋转角度 (度)。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。

    返回:
        Component: 特定耦合臂滑轮环。

    端口:
        Input, Through: 光学输入和直通端口。
        RingL, RingR, RingD, RingU, RingC: 环上的参考端口。
        HeatIn, HeatOut: (HeaterConfig 不为 None 时) 加热器电学端口。
    """
    c = gf.Component()
    # 创建环形波导
    ring_path90 = gf.path.arc(radius=RadiusRing, angle=90)
    ring_path_all = ring_path90 + ring_path90 + ring_path90 + ring_path90
    ring_comp = c << gf.path.extrude(ring_path_all, width=WidthRing, layer=oplayer)

    # 光学部分：创建耦合波导
    couple_path_ring = gf.path.arc(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2, angle=AngleCouple / 2)
    couple_path_euler = euler_Bend_Half(radius=RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2,
                                        angle=(90 - AngleCouple) / 2, p=1)
    couple_path = couple_path_ring + couple_path_euler
    upcouple_comp1 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)
    upcouple_comp1.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
    upcouple_comp1.movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2 = c << gf.path.extrude(couple_path, width=WidthNear, layer=oplayer)
    upcouple_comp2.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
    upcouple_comp2.movey(2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2.rotate(center=upcouple_comp2.ports["o1"].center, angle=180).mirror_y(upcouple_comp2.ports["o1"].center[1])

    # 添加光学端口
    c.add_port(name="Input", port=upcouple_comp2.ports["o2"])
    c.add_port(name="Through", port=upcouple_comp1.ports["o2"])
    c.add_port(name="RingL", width=1, center=[-RadiusRing, RadiusRing], orientation=90,layer=oplayer)
    c.add_port(name="RingR", width=1, center=[RadiusRing, RadiusRing], orientation=90,layer=oplayer)
    c.add_port(name="RingD", width=1, center=[0, 0],orientation=0,layer=oplayer)
    c.add_port(name="RingU", width=1, center=[0, 2 * RadiusRing],layer=oplayer)
    c.add_port(name="RingC", width=1, center=[0, RadiusRing],layer=oplayer)
    # 添加加热电极
    if HeaterConfig:
        DifferentHeater_local(c, WidthRing=WidthRing,RadiusRing=RadiusRing,HeaterConfig=HeaterConfig,DirectionHeater=DirectionHeater,RotationHeater=RotationHeater)
    add_labels_to_ports(c)
    return c


# %% different heater
@gf.cell
def DifferentHeater_local(
        c: Component = None,
        WidthRing: float = 1,
        RadiusRing: float = 100.0,
        DirectionHeater: str = "down",
        RotationHeater: float = 0,
        HeaterConfig: HeaterConfigClass = HeaterConfigClass(),
) -> Component:
    """
    局部辅助函数，在父组件中创建并添加加热器子组件，支持多种类型和方向。
    加热器路径基于父组件中已定义的环参考端口（RingL, RingR, RingC）。

    参数:
        c: 父级 Component，加热器将作为子组件添加到此组件中。
        WidthRing: 被加热环的波导宽度 (µm)。
        RadiusRing: 被加热环的半径 (µm)。
        DirectionHeater: 加热器相对于环的位置 ("up" 或 "down")。
        RotationHeater: 加热器绕环中心旋转的角度 (度)，正值逆时针。
        HeaterConfig: 加热器配置对象，包含 TypeHeater/WidthHeat/DeltaHeat 等参数。

    返回:
        Component: 父组件 c（原地修改后返回）。

    端口: (添加到父组件 c)
        HeatIn, HeatOut: 加热器电学端口。
    """
    h = gf.Component()
    # 提取加热器配置参数
    TypeHeater = HeaterConfig.TypeHeater
    WidthHeat = HeaterConfig.WidthHeat
    WidthRoute = HeaterConfig.WidthRoute
    WidthVia = HeaterConfig.WidthVia
    Spacing = HeaterConfig.Spacing
    DeltaHeat = HeaterConfig.DeltaHeat
    GapHeat = HeaterConfig.GapHeat
    heatlayer = HeaterConfig.LayerHeat
    routelayer = HeaterConfig.LayerRoute
    vialayer = HeaterConfig.LayerVia
    if TypeHeater == "default":
        # ===== 默认加热电极 =====
        heat_path = gf.path.arc(radius=RadiusRing, angle=60)  # 创建加热电极路径
        heatout_path1 = euler_Bend_Half(radius=RadiusRing / 2, angle=30)  # 创建欧拉弯曲路径
        heatout_path2 = euler_Bend_Half(radius=20, angle=-60)  # 创建欧拉弯曲路径
        heatL_comp1 = h << gf.path.extrude(heat_path + heatout_path2, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp1.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True,
                            mirror=True)  # 连接并镜像
        # heatL_comp1.mirror_x(heatL_comp1.ports["o1"].center[0])
        heatL_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp2.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heatL_comp2.rotate(180, heatL_comp2.ports["o1"].center)  # 连接并旋转
        heatR_comp1 = h << gf.path.extrude(heat_path + heatout_path2, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp1.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True)  # 连接
        heatR_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp2.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, mirror=True,
                            allow_width_mismatch=True)  # 连接并镜像
        heatR_comp2.rotate(180, heatR_comp2.ports["o1"].center)
        length = abs(heatL_comp2.ports["o2"].center[0]-heatR_comp2.ports["o2"].center[0])
        routepath_straight = gf.path.straight(length=length+0.001)
        route_straight = h << gf.path.extrude(routepath_straight, width=WidthHeat, layer=heatlayer)
        route_straight.connect("o1",heatL_comp2.ports["o2"])
        h.add_port(name="HeatIn", port=heatL_comp1.ports["o2"])
        h.add_port(name="HeatOut", port=heatR_comp1.ports["o2"])
        h.add_port(name="RingL", port=heatL_comp1.ports["o1"])
        if DirectionHeater == "down":
            h.mirror_y(c.ports["RingL"].center[1])
        if RotationHeater != 0:
            h.rotate(RotationHeater, center=c.ports["RingC"].center)
        h.flatten()
        h = snap_all_polygons_iteratively(h)
        heater = c << h
        c.add_port(name="HeatIn", port=heater.ports["HeatIn"])
        c.add_port(name="HeatOut", port=heater.ports["HeatOut"])
    elif TypeHeater == "snake":
        # ===== 蛇形加热电极 =====
        heat_path = gf.path.arc(radius=RadiusRing + DeltaHeat, angle=60)  # 创建加热电极路径
        heatout_path1 = euler_Bend_Half(radius=20, angle=30, use_eff=True)  # 创建欧拉弯曲路径
        heatout_path2 = euler_Bend_Half(radius=20, angle=-60, use_eff=True)  # 创建欧拉弯曲路径
        HPart = [
            SnakeHeater(WidthHeat, WidthRing, GapHeat, heat_path + heatout_path1, ["o1", "o2"], heatlayer) if i % 2 == 1
            else SnakeHeater(WidthHeat, WidthRing, GapHeat, heat_path + heatout_path2, ["o1", "o2"], heatlayer) for i in
            range(4)]  # 创建蛇形加热电极
        HeatLR = [h << HPart[i] for i in range(4)]  # 将蛇形加热电极添加到组件
        for i, comp in enumerate(HeatLR):
            if i == 0:
                comp.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True,
                             mirror=True)  # 连接并镜像
            elif i == 1:
                comp.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True,
                             mirror=True)  # 连接并旋转
                comp.mirror_y(comp.ports["o1"].center[1])
            elif i == 2:
                comp.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True, )  # 连接
            elif i == 3:
                comp.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True)  # 连接并镜像
                comp.mirror_y(comp.ports["o1"].center[1])
            comp.movex((i // 2 * 2 - 1) * DeltaHeat)
        # heatRing_route = gf.routing.route_single(h, HeatLR[1].ports["o2"], HeatLR[3].ports["o2"], layer=heatlayer,
        #                                          route_width=WidthHeat)  # 创建加热电极之间的路由
        length = abs(HeatLR[1].ports["o2"].center[0]-HeatLR[3].ports["o2"].center[0])
        routepath_straight = gf.path.straight(length=length+0.001)
        route_straight = h << gf.path.extrude(routepath_straight, width=WidthHeat, layer=heatlayer)
        route_straight.connect("o1",HeatLR[3].ports["o2"])
        h.add_port(name="HeatIn", port=HeatLR[0].ports["o2"])
        h.add_port(name="HeatOut", port=HeatLR[2].ports["o2"])
        h.add_port(name="RingL", port=HeatLR[2].ports["o1"])
        if DirectionHeater == "down":
            h.mirror_y(c.ports["RingL"].center[1])
        if RotationHeater != 0:
            h.rotate(RotationHeater, center=c.ports["RingC"].center)
        h.flatten()
        h = snap_all_polygons_iteratively(h)
        heater = c << h
        c.add_port(name="HeatIn", port=heater.ports["HeatIn"])
        c.add_port(name="HeatOut", port=heater.ports["HeatOut"])
    elif TypeHeater == "side":
        # ===== 侧边加热电极 =====
        heat_path = gf.path.arc(radius=RadiusRing + DeltaHeat, angle=60)  # 创建加热电极路径
        heatout_path1 = euler_Bend_Half(radius=RadiusRing / 2, angle=30)  # 创建欧拉弯曲路径
        heatout_path2 = euler_Bend_Half(radius=RadiusRing / 2, angle=-30)  # 创建欧拉弯曲路径
        heatout_path3 = euler_Bend_Half(radius=RadiusRing / 4, angle=60)  # 创建欧拉弯曲路径
        heatout_path4 = euler_Bend_Half(radius=RadiusRing / 4, angle=-60)  # 创建欧拉弯曲路径
        heatL_comp1 = h << gf.path.extrude(heat_path + heatout_path4, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp1.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True,
                            mirror=True)  # 连接并镜像
        heatL_comp1.movex(-DeltaHeat)
        heatL_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp2.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heatL_comp2.rotate(180, heatL_comp2.ports["o1"].center)  # 连接并旋转
        heatL_comp2.movex(-DeltaHeat)
        heatR_comp1 = h << gf.path.extrude(heat_path + heatout_path4, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp1.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True)  # 连接
        heatR_comp1.movex(DeltaHeat)
        heatR_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp2.connect("o1", heatR_comp1.ports["o1"], allow_layer_mismatch=True, allow_width_mismatch=True,
                            mirror=True)  # 连接并镜像
        length = abs(heatL_comp2.ports["o2"].center[0]-heatR_comp2.ports["o2"].center[0])
        routepath_straight = gf.path.straight(length=length+0.001)
        route_straight = h << gf.path.extrude(routepath_straight, width=WidthHeat, layer=heatlayer)
        route_straight.connect("o1",heatL_comp2.ports["o2"])
        h.add_port(name="HeatIn", port=heatL_comp1.ports["o2"])
        h.add_port(name="HeatOut", port=heatR_comp1.ports["o2"])
        h.add_port(name="RingL", port=c.ports["RingL"])
        if DirectionHeater == "down":
            h.mirror_y(c.ports["RingL"].center[1])
        if RotationHeater != 0:
            h.rotate(RotationHeater, center=c.ports["RingC"].center)
        h.flatten()
        h = snap_all_polygons_iteratively(h)
        heater = c << h
        c.add_port(name="HeatIn", port=heater.ports["HeatIn"])
        c.add_port(name="HeatOut", port=heater.ports["HeatOut"])
    elif TypeHeater == "inside":
        # ===== 内部加热电极 =====
        DeltaHeat=-abs(DeltaHeat)
        heat_path = gf.path.arc(radius=RadiusRing + DeltaHeat, angle=60)  # 创建加热电极路径
        heatout_path1 = euler_Bend_Half(radius=RadiusRing / 2, angle=30)  # 创建欧拉弯曲路径
        heatout_path2 = euler_Bend_Half(radius=RadiusRing / 2, angle=-30)  # 创建欧拉弯曲路径
        heatout_path3 = euler_Bend_Half(radius=RadiusRing / 4, angle=75)  # 创建欧拉弯曲路径
        heatout_path4 = euler_Bend_Half(radius=RadiusRing / 4, angle=-60)  # 创建欧拉弯曲路径
        heatL_comp1 = h << gf.path.extrude(heat_path + heatout_path3, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp1.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True,
                            mirror=True)  # 连接并镜像
        heatL_comp1.movex(-DeltaHeat)
        heatL_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp2.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heatL_comp2.rotate(180, heatL_comp2.ports["o1"].center)  # 连接并旋转
        heatL_comp2.movex(-DeltaHeat)
        heatR_comp1 = h << gf.path.extrude(heat_path + heatout_path3, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp1.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True)  # 连接
        heatR_comp1.movex(DeltaHeat)
        heatR_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp2.connect("o1", heatR_comp1.ports["o1"], allow_layer_mismatch=True, allow_width_mismatch=True,
                            mirror=True)  # 连接并镜像
        length = abs(heatL_comp2.ports["o2"].center[0]-heatR_comp2.ports["o2"].center[0])
        routepath_straight = gf.path.straight(length=length+0.001)
        route_straight = h << gf.path.extrude(routepath_straight, width=WidthHeat, layer=heatlayer)
        route_straight.connect("o1",heatL_comp2.ports["o2"])
        h.add_port(name="HeatIn", port=heatL_comp1.ports["o2"])
        h.add_port(name="HeatOut", port=heatR_comp1.ports["o2"])
        h.add_port(name="RingL", port=c.ports["RingL"])
        if DirectionHeater == "down":
            h.mirror_y(c.ports["RingL"].center[1])
        if RotationHeater != 0:
            h.rotate(RotationHeater, center=c.ports["RingC"].center)
        h.flatten()
        h = snap_all_polygons_iteratively(h)
        heater = c << h
        c.add_port(name="HeatIn", port=heater.ports["HeatIn"])
        c.add_port(name="HeatOut", port=heater.ports["HeatOut"])
    elif TypeHeater == "insideP":
        # ===== 内部加热电极（平行出） =====
        DeltaHeat=-abs(DeltaHeat)
        heat_path = gf.path.arc(radius=RadiusRing + DeltaHeat, angle=60)  # 创建加热电极路径
        heatout_path1 = euler_Bend_Half(radius=RadiusRing / 2, angle=30)  # 创建欧拉弯曲路径
        heatout_path2 = euler_Bend_Half(radius=RadiusRing / 2, angle=-30)  # 创建欧拉弯曲路径
        heatout_path3 = euler_Bend_Half(radius=RadiusRing / 4, angle=30)  # 创建欧拉弯曲路径
        heatout_path4 = euler_Bend_Half(radius=RadiusRing / 4, angle=-60)  # 创建欧拉弯曲路径
        heatL_comp1 = h << gf.path.extrude(heat_path + heatout_path3, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp1.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True,
                            mirror=True)  # 连接并镜像
        heatL_comp1.movex(-DeltaHeat)
        heatL_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatL_comp2.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heatL_comp2.rotate(180, heatL_comp2.ports["o1"].center)  # 连接并旋转
        heatL_comp2.movex(-DeltaHeat)
        heatR_comp1 = h << gf.path.extrude(heat_path + heatout_path3, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp1.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True)  # 连接
        heatR_comp1.movex(DeltaHeat)
        heatR_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatR_comp2.connect("o1", heatR_comp1.ports["o1"], allow_layer_mismatch=True, allow_width_mismatch=True,
                            mirror=True)  # 连接并镜像
        length = abs(heatL_comp2.ports["o2"].center[0]-heatR_comp2.ports["o2"].center[0])
        routepath_straight = gf.path.straight(length=length+0.001)
        route_straight = h << gf.path.extrude(routepath_straight, width=WidthHeat, layer=heatlayer)
        route_straight.connect("o1",heatL_comp2.ports["o2"])
        h.add_port(name="HeatIn", port=heatL_comp1.ports["o2"])
        h.add_port(name="HeatOut", port=heatR_comp1.ports["o2"])
        h.add_port(name="RingL", port=c.ports["RingL"])
        if DirectionHeater == "down":
            h.mirror_y(c.ports["RingL"].center[1])
        if RotationHeater != 0:
            h.rotate(RotationHeater, center=c.ports["RingC"].center)
        h.flatten()
        h = snap_all_polygons_iteratively(h)
        heater = c << h
        c.add_port(name="HeatIn", port=heater.ports["HeatIn"])
        c.add_port(name="HeatOut", port=heater.ports["HeatOut"])
    elif TypeHeater == "bothside":
        # ===== 双侧对称加热电极 =====
        DeltaHeat = abs(DeltaHeat)
        heat_path_int1 = gf.path.arc(radius=RadiusRing - DeltaHeat, angle=90)  # 创建加热电极路径
        heat_path_ext1 = gf.path.arc(radius=RadiusRing + DeltaHeat, angle=90)  # 创建加热电极路径
        heat_path_int2 = gf.path.arc(radius=RadiusRing - DeltaHeat, angle=60)  # 创建加热电极路径
        heat_path_ext2 = gf.path.arc(radius=RadiusRing + DeltaHeat, angle=60)  # 创建加热电极路径
        heatout_path1 = euler_Bend_Half(radius=RadiusRing / 5, angle=-60)  # 创建欧拉弯曲路径
        heatLint_comp1 = h << gf.path.extrude(heat_path_int2 + heatout_path1, width=WidthHeat,
                                              layer=heatlayer)  # 创建左侧加热电极
        heatLint_comp1.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True)  # 连接并镜像
        heatLint_comp1.mirror_x(heatLint_comp1.ports["o1"].center[0])
        heatLint_comp1.movex(DeltaHeat)
        heatLint_comp2 = h << gf.path.extrude(heat_path_int1, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatLint_comp2.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heatLint_comp2.rotate(180, heatLint_comp2.ports["o1"].center)  # 连接并旋转
        heatLint_comp2.movex(DeltaHeat)
        heatLext_comp1 = h << gf.path.extrude(heat_path_ext2 + heatout_path1, width=WidthHeat,
                                              layer=heatlayer)  # 创建左侧加热电极
        heatLext_comp1.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, mirror=True,
                               allow_width_mismatch=True)  # 连接并镜像
        heatLext_comp1.movex(-DeltaHeat)
        heatLext_comp2 = h << gf.path.extrude(heat_path_ext1, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        heatLext_comp2.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heatLext_comp2.rotate(180, heatLext_comp2.ports["o1"].center)  # 连接并旋转
        heatLext_comp2.movex(-DeltaHeat)
        heatRint_comp1 = h << gf.path.extrude(heat_path_int2 + heatout_path1, width=WidthHeat,
                                              layer=heatlayer)  # 创建右侧加热电极
        heatRint_comp1.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True)  # 连接
        heatRint_comp1.movex(-DeltaHeat)
        heatRint_comp2 = h << gf.path.extrude(heat_path_int1, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatRint_comp2.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heatRint_comp2.mirror_y(heatRint_comp2.ports["o1"].center[1])  # 连接并镜像
        heatRint_comp2.movex(-DeltaHeat)
        heatRext_comp1 = h << gf.path.extrude(heat_path_ext2 + heatout_path1, width=WidthHeat,
                                              layer=heatlayer)  # 创建右侧加热电极
        heatRext_comp1.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True)  # 连接
        heatRext_comp1.movex(DeltaHeat)
        heatRext_comp2 = h << gf.path.extrude(heat_path_ext1, width=WidthHeat, layer=heatlayer)  # 创建右侧加热电极
        heatRext_comp2.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heatRext_comp2.mirror_y(heatRext_comp2.ports["o1"].center[1])  # 连接并镜像
        heatRext_comp2.movex(DeltaHeat)
        h.add_port(name="HeatIntIn", port=heatLint_comp1.ports["o2"])
        h.add_port(name="HeatIntOut", port=heatRint_comp1.ports["o2"])
        h.add_port(name="HeatExtIn", port=heatLext_comp1.ports["o2"])
        h.add_port(name="HeatExtOut", port=heatRext_comp1.ports["o2"])
        h.add_port(name="RingC", port=c.ports["RingC"])
        if DirectionHeater == "down":
            h.mirror_y(h.ports["RingC"].center[1])
        if RotationHeater != 0:
            h.rotate(RotationHeater, center=c.ports["RingC"].center)
        h.flatten()
        h = snap_all_polygons_iteratively(h)
        heater = c << h
        c.add_port(name="HeatIntIn", port=heater.ports["HeatIntIn"])
        c.add_port(name="HeatIntOut", port=heater.ports["HeatIntOut"])
        c.add_port(name="HeatExtIn", port=heater.ports["HeatExtIn"])
        c.add_port(name="HeatExtOut", port=heater.ports["HeatExtOut"])
    elif TypeHeater == "multi":
        # ===== 多层加热电极 =====
        if isinstance(WidthHeat, (list, tuple)) or hasattr(WidthHeat, "__iter__"):
            noh = len(WidthHeat)
        else:
            noh = 1
            WidthHeat = [WidthHeat]
        if isinstance(DeltaHeat, (list, tuple)) or hasattr(DeltaHeat, "__iter__"):
            nod = len(DeltaHeat)
        else:
            nod = 1
            DeltaHeat = [DeltaHeat]
        if noh != nod:
            raise ValueError(
                "Number of WidthHeat != Number of DeltaHeat"
            )
        widthheat = []
        deltaheat = []
        for i in range(noh):
            if isinstance(WidthHeat, (list, tuple)):
                widthheat.append(WidthHeat[i])
            elif hasattr(WidthHeat, "__iter__"):
                WidthHeat = list(WidthHeat)
                widthheat.append(WidthHeat[i])
            if isinstance(DeltaHeat, (list, tuple)):
                deltaheat.append(DeltaHeat[i])
            elif hasattr(DeltaHeat, "__iter__"):
                DeltaHeat = list(DeltaHeat)
                deltaheat.append(DeltaHeat[i])
        for i in range(noh):
            wh = widthheat[i]
            dh = deltaheat[i]
            heat_path = gf.path.arc(radius=RadiusRing + dh, angle=60)
            heatout_path1 = euler_Bend_Half(radius=RadiusRing / 2, angle=30)
            heatout_path2 = euler_Bend_Half(radius=RadiusRing / 2, angle=-30)
            heatout_path3 = euler_Bend_Half(radius=RadiusRing / 4, angle=60)
            heatout_path4 = euler_Bend_Half(radius=RadiusRing / 4, angle=-60)
            heatL_comp1 = h << gf.path.extrude(heat_path + heatout_path4, width=wh, layer=heatlayer)
            heatL_comp1.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True,
                                mirror=True)
            heatL_comp1.movex(-dh)
            heatL_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=wh, layer=heatlayer)
            heatL_comp2.connect("o1", c.ports["RingL"], allow_layer_mismatch=True, allow_width_mismatch=True)
            heatL_comp2.rotate(180, heatL_comp2.ports["o1"].center)
            heatL_comp2.movex(-dh)
            heatR_comp1 = h << gf.path.extrude(heat_path + heatout_path4, width=wh, layer=heatlayer)
            heatR_comp1.connect("o1", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True)
            heatR_comp1.movex(dh)
            heatR_comp2 = h << gf.path.extrude(heat_path + heatout_path1, width=wh, layer=heatlayer)
            heatR_comp2.connect("o1", heatR_comp1.ports["o1"], allow_layer_mismatch=True, allow_width_mismatch=True,
                                mirror=True)
            length = abs(heatL_comp2.ports["o2"].center[0] - heatR_comp2.ports["o2"].center[0])
            routepath_straight = gf.path.straight(length=length + 0.001)
            route_straight = h << gf.path.extrude(routepath_straight, width=wh, layer=heatlayer)
            route_straight.connect("o1", heatL_comp2.ports["o2"])
            h.add_port(name="Heat" + str(i) + "In", port=heatL_comp1.ports["o2"])
            h.add_port(name="Heat" + str(i) + "Out", port=heatR_comp1.ports["o2"])
        h.add_port(name="RingL", port=c.ports["RingL"])
        if DirectionHeater == "down":
            h.mirror_y(c.ports["RingL"].center[1])
        if RotationHeater != 0:
            h.rotate(RotationHeater, center=c.ports["RingC"].center)
        h.flatten()
        h = snap_all_polygons_iteratively(h)
        heater = c << h
        for port in heater.ports:
            if port.name != "RingL" and port.name != "RingC":
                c.add_port(name=port.name, port=port)
    elif TypeHeater == "spilt":
        # ===== 分裂式加热电极 =====
        S_route1 = gf.Section(width=WidthRoute, offset=DeltaHeat, layer=routelayer, port_names=("r1o1", "r1o2"))
        S_route2 = gf.Section(width=WidthRoute, offset=-(DeltaHeat), layer=routelayer, port_names=("r2o1", "r2o2"))
        X_Heat = gf.CrossSection(sections=[S_route1, S_route2])
        # 默认加热电极
        heat_path = gf.path.arc(radius=RadiusRing, angle=120)  # 创建加热电极路径
        route_path = gf.path.arc(radius=RadiusRing, angle=60)
        out_path = gf.path.euler(radius=20, angle=60)
        out_path2 = gf.path.euler(radius=20, angle=-60)
        heat_path.rotate(-60)
        heatL_comp = h << DifferentHeater(heat_path, WidthWG=WidthRing,HeaterConfig=HeaterConfig)  # 创建左侧加热电极
        heatL_comp.connect("HeatIn", c.ports["RingL"], allow_layer_mismatch=True, mirror=True,
                           allow_width_mismatch=True)  # 连接并镜像
        heatL_comp.rotate(60, center=c.ports["RingC"].center)
        heatR_comp = h << DifferentHeater(heat_path, WidthWG=WidthRing,HeaterConfig=HeaterConfig)  # 创建左侧加热电极
        heatR_comp.connect("HeatIn", c.ports["RingR"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heatR_comp.rotate(-60, center=c.ports["RingC"].center)
        Hp1 = h << gf.path.extrude(route_path, cross_section=X_Heat)
        Hp1.connect("r1o1", heatL_comp.ports["HeatLIn"])
        r_out_output = h << gf.path.extrude(out_path, width=WidthRoute, layer=routelayer)
        r_out_output.connect("o1", heatL_comp.ports['HeatLOut'])
        r_in_output = h << gf.path.extrude(out_path2, width=WidthRoute, layer=routelayer)
        r_in_output.connect("o1", heatR_comp.ports['HeatROut'])
        h.add_port(name="HeatL", port=r_out_output.ports["o2"])
        h.add_port(name="HeatR", port=r_in_output.ports["o2"])
        h.add_port(name="RingC", port=c.ports["RingC"])
        add_labels_to_ports(h)
        if DirectionHeater == "down":
            h.mirror_y(h.ports['RingC'].center[1])
        if RotationHeater != 0:
            h.rotate(RotationHeater, center=c.ports["RingC"].center)
        h.flatten()
        h = snap_all_polygons_iteratively(h)
        heater = c << h
        c.add_port(name="HeatOut", port=heater.ports["HeatL"])
        c.add_port(name="HeatIn", port=heater.ports["HeatR"])
    h.flatten()
    h=snap_all_polygons_iteratively(h)
    return h


# %% 导出所有函数
__all__ = [
    'RingPulley', 'RingPulley1DC', 'RingPulley1HS', 'RingPulley1HSn', 'RingFinger', 'RingPulley2', 'RingPulley3',
    'RingPulley4', 'RingPulley2ES', 'RingPulleyT1', 'RingPulleyT2',
]
if __name__ == '__main__':
    test = gf.Component("test")
    test = RingPulleyT1(TypeHeater='spilt')
