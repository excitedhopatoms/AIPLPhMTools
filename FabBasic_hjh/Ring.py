from gdsfactory.component import Component

from .BasicDefine import *
from .Heater import SnakeHeater, DifferentHeater
from .SnapMerge import *

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
    创建一个通用的滑轮耦合（Pulley Coupler）环形谐振器组件。
    此函数是 `RingPulleyT1` 的一个简化接口，默认使用 "default" 类型的加热器。
    支持添加Add-Drop端口和加热器。

    参数:
        WidthRing (float): 环形波导的宽度 (µm)。
        WidthNear (float): 耦合总线波导的宽度 (µm)。
        WidthHeat (float): 加热器的宽度 (µm)。
        RadiusRing (float): 环的半径 (µm)。
        GapRing (float): 环与耦合总线之间的间隙 (µm)。
        AngleCouple (float): 滑轮耦合器的耦合角度 (度)。
        IsHeat (bool): 是否为环添加加热器。
        IsAD (bool): 是否包含Add/Drop端口 (即四端口器件)。如果False，则为双端口（Input/Through）。
        Name (str): 组件的名称。
        oplayer (LayerSpec): 光学波导层。
        heatlayer (LayerSpec): 加热器层。
        routelayer (LayerSpec): (传递给内部组件) 加热器布线层。
        vialayer (LayerSpec): (传递给内部组件) 过孔层。

    返回:
        Component: 生成的滑轮耦合环形谐振器组件。

    端口:
        Input: 输入端口。
        Through: 直通端口。
        RingL: 左侧环对称轴上的参考点/端口。
        RingR: 右侧环对称轴上的参考点/端口。
        RingC: 环中心上方的参考点/端口。
        Add: (如果 IsAD=True) 增加端口。
        Drop: (如果 IsAD=True) 下载端口。
        (如果 IsHeat=True，还会包含由 `RingPulleyT1` 生成的加热器电学端口)
    """
    c = RingPulleyT1(
        WidthRing=WidthRing,
        WidthNear=WidthNear,
        WidthHeat=WidthHeat,
        RadiusRing=RadiusRing,
        GapRing=GapRing,
        AngleCouple=AngleCouple,
        IsHeat=IsHeat,
        IsAD=IsAD,
        Name=Name,
        oplayer=oplayer,
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
    创建一个滑轮耦合环形谐振器，其上下两侧（或Input/Through侧与Add/Drop侧）
    可以具有不同的耦合参数（总线宽度、间隙、耦合角）。
    此函数是对 `RingPulleyT1` 的封装，通过设置 `RingPulleyT1` 的非对称耦合参数实现。

    参数:
        WidthRing (float): 环形波导宽度 (µm)。
        WidthNear1 (float): 上侧（或Input/Through）耦合总线的宽度 (µm)。
        WidthNear2 (float): 下侧（或Add/Drop）耦合总线的宽度 (µm)。
        WidthHeat (float): 加热器宽度 (µm)。
        RadiusRing (float): 环的半径 (µm)。
        GapRing1 (float): 上侧耦合间隙 (µm)。
        GapRing2 (float): 下侧耦合间隙 (µm)。
        AngleCouple1 (float): 上侧滑轮耦合角度 (度)。
        AngleCouple2 (float): 下侧滑轮耦合角度 (度)。
        IsHeat (bool): 是否为环添加加热器。
        Name (str): 组件名称。
        oplayer (LayerSpec): 光学波导层。
        heatlayer (LayerSpec): 加热器层。
        routelayer (LayerSpec): (传递给内部组件) 加热器布线层。
        vialayer (LayerSpec): (传递给内部组件) 过孔层。

    返回:
        Component: 生成的具有非对称耦合参数的滑轮环谐振器。

    端口: (与 RingPulley / RingPulleyT1 类似)
    """
    c = RingPulleyT1(
        WidthRing=WidthRing,
        WidthNear=WidthNear1,
        WidthNear2=WidthNear2,
        WidthHeat=WidthHeat,
        RadiusRing=RadiusRing,
        GapRing=GapRing1,
        GapRing2=GapRing2,
        AngleCouple=AngleCouple1,
        AngleCouple2=AngleCouple2,
        IsHeat=IsHeat,
        Name=Name,
        oplayer=oplayer,
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
    创建一个滑轮耦合环形谐振器，并集成一个“侧边”类型的加热器。
    此函数是对 `RingPulleyT1` 的封装，将 `TypeHeater` 固定为 "side"。

    参数:
        (大部分参数与 RingPulley 类似)
        WidthRoute (float): 侧边加热器引出线的宽度 (µm)。
        DeltaHeat (float): 侧边加热器中心相对于环波导中心线的横向偏移量 (µm)。
                           正值或负值决定加热器在环的哪一侧或具体偏移方式。
        GapRoute (float): (当前未直接使用) 可能用于定义加热器引出结构之间的间隙 (µm)。
        RadiusRing (float): 环半径，注意默认值为1000µm，较大。

    返回:
        Component: 生成的带侧边加热器的滑轮环谐振器。

    端口: (与 RingPulley / RingPulleyT1 类似)
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
        IsHeat=True,
        Name=Name,
        oplayer=oplayer,
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
    创建一个滑轮耦合环形谐振器，并集成一个“蛇形”类型的加热器。
    此函数是对 `RingPulleyT1` 的封装，将 `TypeHeater` 固定为 "snake"。

    参数:
        (大部分参数与 RingPulley 类似)
        GapHeat (float): 蛇形加热器中切割部分的间隙宽度 (µm)。这是蛇形加热器的关键参数。
        WidthRoute, DeltaHeat: (当前未直接传递或使用对蛇形加热器有直接影响的方式)
        RadiusRing (float): 环半径，注意默认值为1000µm。

    返回:
        Component: 生成的带蛇形加热器的滑轮环谐振器。

    端口: (与 RingPulley / RingPulleyT1 类似)
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
    """
    创建一个滑轮耦合环形谐zh振器，其输入/输出耦合臂具有特定的弯曲形状（由 `RingPulleyT2` 定义）。
    此函数是对 `RingPulleyT2` 的简化封装，通常用于实现端口垂直于环对称轴引出的设计。

    参数:
        WidthRing (float): 环形波导宽度 (µm)。
        WidthNear (float): 耦合总线宽度 (µm)。
        WidthHeat (float): (如果RingPulleyT2支持) 加热器宽度 (µm)。
        RadiusRing (float): 环半径 (µm)。
        GapRing (float): 环与总线耦合间隙 (µm)。
        AngleCouple (float): 滑轮耦合器的耦合角度 (度)。
        IsHeat (bool): 是否为环添加加热器 (传递给 `RingPulleyT2`)。
        Name (str): 组件名称。
        oplayer (LayerSpec): 光学波导层。
        heatlayer (LayerSpec): 加热器层。
        routelayer (LayerSpec): (传递给内部组件) 加热器布线层。
        vialayer (LayerSpec): (传递给内部组件) 过孔层。

    返回:
        Component: 生成的特定耦合臂形状的滑轮环谐振器。

    端口: (由 RingPulleyT2 定义)
        通常包括 Input, Through, 和环的参考端口。
        如果 `RingPulleyT2` 支持 Add/Drop 和加热，则也会有相应端口。
    """
    c = RingPulleyT2(WidthRing, WidthNear, WidthHeat, RadiusRing, 0, GapRing, 0, AngleCouple, IsHeat, "default", Name,
                     oplayer, heatlayer)
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
    """
    创建 `RingPulley2` 类型的滑轮耦合环，并集成 "bothside" (双侧对称) 类型的加热器/电极。
    此函数是对 `RingPulleyT2` 的特定配置封装。

    参数:
        (大部分参数与 RingPulley2 类似)
        WidthEle (float): 双侧对称加热器中，单边加热条的宽度 (µm)。
                          (传递给 `RingPulleyT2` 的 `WidthHeat` 参数)。
        DeltaEle (float): 双侧对称加热器中，单边加热条中心相对于环波导中心线的横向偏移量 (µm)。
                          (传递给 `RingPulleyT2` 的 `DeltaHeat` 参数)。

    返回:
        Component: 生成的带双侧对称加热器的滑轮环。

    端口: (由 RingPulleyT2 定义，并包含 "bothside" 加热器的特定端口)
    """
    c = RingPulleyT2(WidthRing, WidthNear, WidthEle, RadiusRing, DeltaEle, GapRing, 0, AngleCouple, True, "bothside",
                     Name, oplayer, heatlayer)
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
    """
    创建一个具有大角度（接近180度）滑轮型耦合的环形谐振器。
    耦合臂由一个短圆弧段和一个较长的欧拉弯曲段组成，使得总线波导几乎与环的切线方向平行引出。

    参数:
        WidthRing (float): 环形波导宽度 (µm)。
        WidthNear (float): 耦合总线宽度 (µm)。
        WidthHeat (float): (当前版本未使用) 加热器宽度 (µm)。
        RadiusRing (float): 环半径 (µm)。
        GapRing (float): 环与总线耦合间隙 (µm)。
        AngleCouple (float): 耦合臂中圆弧段所占的角度的一半 (度)。
                           总线引出方向接近 (180 - AngleCouple) 度。
        IsHeat (bool): (当前版本未使用) 是否添加加热器。
        Name (str): 组件名称。
        oplayer (LayerSpec): 光学波导层。
        heatlayer, routelayer, vialayer: (当前版本未使用) GDS图层。

    返回:
        Component: 生成的大角度滑轮耦合环。

    端口:
        Input, Through: 光学输入和直通端口。
        RingL, RingR: 环左右两侧对称轴上的参考点/端口。
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
    upcouple_comp2.rotate(center=upcouple_comp2.ports["o1"].center, angle=180).mirror_y(
        upcouple_comp2.ports["o1"].center[1])
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
    """
    创建另一种具有大角度滑轮型耦合的环形谐振器。
    与 `RingPulley3` 类似，但耦合臂中欧拉弯曲的角度参数不同，
    可能导致不同的引出轨迹。

    参数: (与 RingPulley3 类似)
        AngleCouple (float): 耦合臂中圆弧段所占的角度的一半 (度)。
                           欧拉弯的角度将是 (270 - AngleCouple)/2，这与RingPulley3的(180-AngleCouple)/2不同，
                           意味着引出方向更偏向侧面。

    返回:
        Component: 生成的大角度滑轮耦合环。

    端口: (与 RingPulley3 类似)
    """
    c = gf.Component()
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
    upcouple_comp1.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
    upcouple_comp1.movey(
        2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2 = c << gf.path.extrude(couple_path_up, width=WidthNear, layer=oplayer)
    upcouple_comp2.connect("o1", other=ring_comp.ports["o1"], allow_width_mismatch=True)
    upcouple_comp1.movey(
        2 * RadiusRing + GapRing + WidthNear / 2 + WidthRing / 2)
    upcouple_comp2.rotate(center=upcouple_comp2.ports["o1"].center, angle=180).mirror_y(
        upcouple_comp2.ports["o1"].center[1])
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
    """
    创建一个“手指”形或梳状的多弯曲环形谐振器结构。
    该结构由两个对称的半部分组成，每个半部分包含多个弯曲和直线段，
    形成类似手指或梳齿的形状，并通过中间的直波导连接闭合。
    通过外部总线进行滑轮型耦合。

    参数:
        WidthRing (float): 构成环主体（手指部分）的波导宽度 (µm)。
        WidthNear (float): 外部耦合总线的波导宽度 (µm)。
        RadiusCouple (float): 靠近耦合区域的“指关节”弯曲半径 (µm)。
        RadiusSide (float): “手指”侧向突出部分的弯曲半径 (µm)。
        LengthCouple (float): “指关节”处的直线段长度 (µm)。
        LengthSide (float): “手指”侧向突出部分的直线段长度 (µm)。
        LengthConnect (float): 连接两个对称半结构中心的直波导长度 (µm)。
        GapRing (float): 环与外部耦合总线之间的间隙 (µm)。
        AngleCouple (float): 外部滑轮耦合臂的角度参数 (度)。
        AngleSide (float): “手指”侧向突出部分弯曲的总角度 (度)，例如180度形成U型弯。
        Name (str): 组件名称。
        oplayer (LayerSpec): 光学波导层。

    返回:
        Component: 生成的“手指”环谐振器组件。

    端口:
        Input: 输入端口。
        Through: 直通端口。
        Con1, Con2: 连接两个半结构的中间直波导的两端端口（作为参考）。
    """
    c = gf.Component()
    # 光学部分
    S_ring = gf.Section(width=WidthRing, layer=oplayer, port_names=["o1", "o2"])
    S_couple = gf.Section(width=WidthNear, layer=oplayer, port_names=["o1", "o2"])
    CS_ring = gf.CrossSection(sections=[S_ring])
    CS_couple = gf.CrossSection(sections=[S_couple])
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
    path_ring = path_arc_ring + path_euler_ring + path_str_ring
    path_side = path_euler_side + path_str_side
    path_side2 = path_euler_side2 + path_str_side
    path_couple = path_arc_couple + path_euler_couple
    path_connect = path_str_connect + path_arc_connect
    path_half = path_ring + path_side + path_side2 + path_connect
    CcoupleL = c << gf.path.extrude(path_couple, cross_section=CS_couple)
    CcoupleR = c << gf.path.extrude(path_couple, cross_section=CS_couple)
    ChalfL = c << gf.path.extrude(path_half, cross_section=CS_ring)
    ChalfL.mirror_y(ChalfL.ports["o1"].center[1])
    ChalfR = c << gf.path.extrude(path_half, cross_section=CS_ring)
    ChalfR.connect("o1", other=ChalfL.ports["o1"])
    length_con = abs(ChalfL.ports["o2"].center[0] - ChalfR.ports["o2"].center[0])
    str_connect = c << GfCStraight(width=WidthRing, length=length_con, layer=oplayer)
    str_connect.connect("o1", other=ChalfL.ports["o2"])
    CcoupleL.connect("o1", other=ChalfR.ports["o1"], allow_width_mismatch=True)
    CcoupleL.movey(GapRing + WidthNear / 2 + WidthRing / 2).mirror_y(CcoupleL.ports["o1"].center[1])
    CcoupleR.connect("o1", other=ChalfL.ports["o1"], allow_width_mismatch=True)
    CcoupleR.movey(GapRing + WidthNear / 2 + WidthRing / 2)
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
    创建一个通用的、可配置性强的滑轮耦合环形谐振器。
    这是本模块中其他几种 `RingPulley` 变体的核心构建单元。
    支持对称或非对称的Add/Drop端口耦合参数，多种类型的加热器，以及可选的热隔离槽。

    参数:
        WidthRing (float): 环波导宽度 (µm)。
        WidthNear (float): Input/Through侧耦合总线的宽度 (µm)。
        WidthHeat (float): 加热器宽度 (µm)。
        WidthTrench (float): 热隔离槽的宽度 (µm)。
        WidthRoute (float): 加热器引出线的宽度 (µm)。
        RadiusRing (float): 环的半径 (µm)。
        WidthNear2 (float | None): Add/Drop侧耦合总线的宽度 (µm)。如果为None，则使用 `WidthNear`。
        GapRing2 (float | None): Add/Drop侧的耦合间隙 (µm)。如果为None，则使用 `GapRing`。
        AngleCouple2 (float | None): Add/Drop侧的耦合角度 (度)。如果为None，则使用 `AngleCouple`。
        DeltaHeat (float): 加热器的几何调整参数 (µm)，如偏移量。
        GapRing (float): Input/Through侧的耦合间隙 (µm)。
        GapHeat (float): 波导与加热器（特别是snake或side类型）的间隙 (µm)。
        GapTrench (float): 波导边缘与热隔离槽内边缘的间隙 (µm)。
        AngleCouple (float): Input/Through侧的滑轮耦合角度 (度)。
        IsHeat (bool): 是否添加加热器。
        TypeHeater (str): 加热器类型 ("default", "snake", "side", "bothside", "spilt")。
        IsAD (bool): 是否构建为四端口Add-Drop器件。如果False，则只有Input和Through端口。
        IsTrench (bool): 是否在环周围添加热隔离槽。
        DirectionHeater (str): 加热器的主要方向或位置（例如 "up", "down"）。
        Name (str): 组件名称。
        oplayer (LayerSpec): 光学波导层。
        heatlayer (LayerSpec): 加热器层。
        routelayer (LayerSpec): 加热器布线层。
        vialayer (LayerSpec): 过孔层。
        trelayer (LayerSpec): 热隔离槽层。

    返回:
        Component: 生成的通用滑轮环谐振器组件。

    端口: (根据IsAD和IsHeat参数动态生成)
        Input, Through
        Add, Drop (如果 IsAD=True)
        RingL, RingR, RingC (环的参考端口)
        HeatIn, HeatOut (或更具体的加热器端口，如果IsHeat=True)
    """
    c = gf.Component()  # 创建一个组件实例
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
    if IsHeat:
        DifferentHeater_local(c, WidthHeat, WidthRing, DeltaHeat, GapHeat, RadiusRing, heatlayer, TypeHeater,
                              DirectionHeater=DirectionHeater, Name=Name + "Heater", WidthRoute=WidthRoute)
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
        WidthHeat: float = 2.0,
        RadiusRing: float = 100.0,
        DeltaHeat: float = 0,
        GapRing: float = 1.0,
        GapHeat: float = 2.0,
        AngleCouple: float = 20.0,
        IsHeat: bool = True,
        TypeHeater: str = "default",
        Name: str = "Ring_Pullry",
        DirectionHeater: str = "up",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一种特定几何形状的滑轮耦合环形谐振器。
    其耦合臂由一个短圆弧段和较长的欧拉弯曲段组成，使得总线波导的引出方向
    接近于垂直于环的对称轴（即端口近似90度引出）。
    支持添加加热器。此组件不包含Add/Drop端口。

    参数:
        WidthRing (float): 环波导宽度 (µm)。
        WidthNear (float): 耦合总线宽度 (µm)。
        WidthHeat (float): 加热器宽度 (µm)。
        RadiusRing (float): 环半径 (µm)。
        DeltaHeat (float): 加热器的几何调整参数 (µm)。
        GapRing (float): 环与总线耦合间隙 (µm)。
        GapHeat (float): 波导与加热器间隙 (µm)。
        AngleCouple (float): 耦合臂中圆弧段所占的角度 (度)。
                           欧拉弯的角度将是 (90 - AngleCouple)/2。
        IsHeat (bool): 是否添加加热器。
        TypeHeater (str): 加热器类型。
        Name (str): 组件名称。
        oplayer (LayerSpec): 光学波导层。
        heatlayer (LayerSpec): 加热器层。
        routelayer (LayerSpec): 加热器布线层。
        vialayer (LayerSpec): 过孔层。

    返回:
        Component: 生成的特定耦合臂滑轮环。

    端口:
        Input, Through: 光学输入和直通端口。
        RingL, RingR, RingD, RingU, RingC: 环上的参考端口。
        (如果IsHeat=True，还有加热器端口)
    """
    c = gf.Component()

    # 光学部分：创建环形波导
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
    if IsHeat:
        DifferentHeater_local(c, WidthHeat, WidthRing, DeltaHeat, GapHeat, RadiusRing, heatlayer, TypeHeater,
                              DirectionHeater=DirectionHeater, Name=Name + "Heater")
    add_labels_to_ports(c)
    return c


# %% different heater
@gf.cell
def DifferentHeater_local(
        c: Component = None,
        WidthHeat: float = 1,
        WidthRing: float = 1,
        DeltaHeat: float = 2,
        GapHeat: float = 3,
        RadiusRing: float = 100.0,
        heatlayer: LayerSpec = LAYER.M1,
        TypeHeater: str = "default",
        DirectionHeater: str = "down",
        Name: str = "Heater",
        WidthRoute:float =20,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    （局部辅助函数）创建一个加热电极子组件，支持多种类型和方向。
    此函数设计为在另一个组件（父组件 `parent_component`）的上下文中被调用和添加。
    加热器路径基于父组件中已定义的环的参考端口（如 "RingL", "RingR", "RingC"）。

    重要: 此函数依赖于 `parent_component` 中已存在名为 "RingL", "RingR", "RingC" 的端口。
           在 `RingPulleyT1` 和 `RingPulleyT2` 的当前实现中，这些端口是在加热器逻辑之后添加的，
           或者其位置可能与此函数预期的不同。这可能导致连接错误。
           建议：要么确保父组件先定义这些参考端口，要么将加热器路径的生成独立于父组件的端口。

    参数:
        parent_component (Component): 将要添加此加热器作为子组件的父级gdsfactory组件。
                                      用于获取环的参考端口。
        WidthHeat (float): 加热条宽度 (µm)。
        WidthRing (float): 被加热环的波导宽度 (µm)。
        DeltaHeat (float): 加热器的几何调整参数 (µm)。
        GapHeat (float): 加热器与波导或自身结构之间的间隙 (µm)。
        RadiusRing (float): 被加热环的半径 (µm)。
        heatlayer (LayerSpec): 加热器层。
        TypeHeater (str): 加热器类型 ("default", "snake", "side", "bothside", "spilt")。
        DirectionHeater (str): 加热器相对于环的位置 ("up" 或 "down")。
        Name (str): 生成的加热器组件的名称。
        WidthRoute (float): 加热器引出线的宽度 (µm)。
        routelayer (LayerSpec): 加热器布线层。
        vialayer (LayerSpec): 过孔层。

    返回:
        Component: 生成的加热器子组件。调用者负责将其添加到父组件并进行连接。
                   (原代码直接修改父组件c，已改为返回新组件)

    端口: (根据TypeHeater生成)
        HeatIn, HeatOut (或更具体的，如 HeatIntIn, HeatExtOut 等)
        RingL (概念性，用于对齐)
    """
    h = gf.Component()
    if TypeHeater == "default":
        # 默认加热电极
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
        h.add_port(name="HeatIn", port=heatL_comp1.ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=heatR_comp1.ports["o2"])  # 添加加热输出端口
        h.add_port(name="RingL", port=heatL_comp1.ports["o1"])
        heater = c << h
        if DirectionHeater == "down":
            heater.mirror_y(heater.ports["RingL"].center[1])
        c.add_port(name="HeatIn", port=heater.ports["HeatIn"])  # 添加加热输入端口
        c.add_port(name="HeatOut", port=heater.ports["HeatOut"])  # 添加加热输出端口
    elif TypeHeater == "snake":
        # 蛇形加热电极
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
        h.add_port(name="HeatIn", port=HeatLR[0].ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=HeatLR[2].ports["o2"])  # 添加加热输出端口
        h.add_port(name="RingL", port=HeatLR[2].ports["o1"])
        heater = c << h
        if DirectionHeater == "down":
            heater.mirror_y(heater.ports["RingL"].center[1])
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
        h.add_port(name="HeatIn", port=heatL_comp1.ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=heatR_comp1.ports["o2"])  # 添加加热输出端口
        h.add_port(name="RingL", port=c.ports["RingL"])
        heater = c << h
        if DirectionHeater == "down":
            heater.mirror_y(heater.ports["RingL"].center[1])
        c.add_port(name="HeatIn", port=heater.ports["HeatIn"])  # 添加加热输入端口
        c.add_port(name="HeatOut", port=heater.ports["HeatOut"])  # 添加加热输出端口
    elif TypeHeater == "inside":
        # 内部加热电极
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
        h.add_port(name="HeatIn", port=heatL_comp1.ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=heatR_comp1.ports["o2"])  # 添加加热输出端口
        h.add_port(name="RingL", port=c.ports["RingL"])
        heater = c << h
        if DirectionHeater == "down":
            heater.mirror_y(heater.ports["RingL"].center[1])
        c.add_port(name="HeatIn", port=heater.ports["HeatIn"])  # 添加加热输入端口
        c.add_port(name="HeatOut", port=heater.ports["HeatOut"])  # 添加加热输出端口
    elif TypeHeater == "bothside":
        DeltaHeat = abs(DeltaHeat)
        # 侧边加热电极
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
        h.add_port(name="HeatIntIn", port=heatLint_comp1.ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatIntOut", port=heatRint_comp1.ports["o2"])  # 添加加热输出端口
        h.add_port(name="HeatExtIn", port=heatLext_comp1.ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatExtOut", port=heatRext_comp1.ports["o2"])  # 添加加热输出端口
        h.add_port(name="RingC", port=c.ports["RingC"])
        heater = c << h
        if DirectionHeater == "down":
            heater.mirror_y(heater.ports["RingC"].center[1])
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
        out_path = gf.path.euler(radius=20, angle=60)
        out_path2 = gf.path.euler(radius=20, angle=-60)
        heat_path.rotate(-60)
        heatL_comp = h << DifferentHeater(heat_path, WidthHeat=WidthHeat, heatlayer=heatlayer, routelayer=routelayer,
                                          vialayer=vialayer, TypeHeater='spilt', GapHeat=GapHeat, DeltaHeat=DeltaHeat,
                                          WidthRoute=WidthRoute, Padding=GapHeat
                                          )  # 创建左侧加热电极
        heatL_comp.connect("HeatIn", c.ports["RingL"], allow_layer_mismatch=True, mirror=True,
                           allow_width_mismatch=True)  # 连接并镜像
        heatL_comp.rotate(60, center=c.ports["RingC"].center)
        heatR_comp = h << DifferentHeater(heat_path, WidthHeat=WidthHeat, heatlayer=heatlayer, routelayer=routelayer,
                                          vialayer=vialayer, TypeHeater='spilt', GapHeat=GapHeat, DeltaHeat=DeltaHeat,
                                          WidthRoute=WidthRoute, Padding=GapHeat
                                          )  # 创建左侧加热电极
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
        heater = c << h
        if DirectionHeater == "down":
            heater.mirror_y(heater.ports['RingC'].center[1])
        c.add_port(name="HeatOut", port=heater.ports["HeatL"])  # 添加加热输入端口
        c.add_port(name="HeatIn", port=heater.ports["HeatR"])  # 添加加热输出端口
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
