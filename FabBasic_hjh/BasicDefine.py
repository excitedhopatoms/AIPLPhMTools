from collections.abc import Callable

import gdsfactory as gf
import numpy as np
from gdsfactory.component import Component,ComponentAllAngle
from gdsfactory.component_layout import rotate_points
from gdsfactory.generic_tech import get_generic_pdk
from gdsfactory.path import Path, _fresnel
from gdsfactory.pdk import get_active_pdk
from gdsfactory.technology.layer_map import LayerMap
from gdsfactory.typings import Layer, LayerSpec, LayerSpecs, CrossSectionSpec
from dataclasses import dataclass
from typing import Union, Sequence
PDK = get_generic_pdk()
PDK.activate()


# layer define
class LayerMapUserDef(LayerMap):
    WG:LayerSpec = (1,0)
    M1:LayerSpec = (10,0)
    OPEN:LayerSpec = (20,0)
    M2:LayerSpec = (4 , 1) # 高频电极
    SR1:LayerSpec = (216 , 0)
    SR2:LayerSpec = (217 , 0)
    AA:LayerSpec = (10 , 0)
    KV:LayerSpec = (9 , 0)
    P2:LayerSpec = (31 , 0)
    CPF:LayerSpec = (130 , 0)# 氮化硅波导层
    CAA:LayerSpec = (196 , 0)# 离子注入保护层
    TN:LayerSpec = (24 , 0)
    TP:LayerSpec = (15 , 0)
    NLH:LayerSpec = (36 , 0)
    PLH:LayerSpec = (37 , 0)
    NLL:LayerSpec = (35 , 0)
    PLL:LayerSpec = (38 , 0)
    SN:LayerSpec = (40 , 0)
    SP:LayerSpec = (43 , 0)
    P1:LayerSpec = (32 , 0)
    SAB:LayerSpec = (48 , 0)
    NONSAB:LayerSpec = (48 , 100)
    V0:LayerSpec = (219 , 0)
    CT:LayerSpec = (50 , 0)
    DT:LayerSpec = (51 , 0)
    LM1:LayerSpec = (125 , 0)
    SINEC:LayerSpec = (89 , 100)
    V1:LayerSpec = (70 , 0)
    VIA:LayerSpec=(70,0)
    TSW:LayerSpec = (159 , 100)
    V2:LayerSpec = (71 , 0)
    M6:LayerSpec = (66 , 0)
    MIM:LayerSpec = (58 , 0)
    TSW2:LayerSpec = (160 , 100)
    TV:LayerSpec = (78 , 0)
    TM:LayerSpec = (69 , 0)
    PA:LayerSpec = (80 , 0)
    DO1:LayerSpec = (55 , 100)
    HVO:LayerSpec = (111 , 0)
    WAFER:LayerSpec = (100,1)
LAYER = LayerMapUserDef

@dataclass(frozen=True)
class HeaterConfigClass:
    TypeHeater: str = "default"
    WidthHeat: Union[float, Sequence[float]] = 4
    WidthRoute: float = 1
    WidthVia: float = 0.26
    GapHeat: float = 3 # 两个heater的间隔
    DeltaHeat: Union[float, Sequence[float]] = 2 # 距离中心波导的距离
    Spacing: float = 1.1 # Via的spacing
    LayerHeat: tuple[int,int] = LAYER.M1
    LayerRoute: tuple[int,int] = LAYER.M2
    LayerVia: tuple[int,int] = LAYER.VIA
    LayerELE: tuple[int,int] = LAYER.M1
heaterconfig0 = HeaterConfigClass()
# %% section & crosssection
S_in_te0 = gf.Section(width=0.5, layer=LAYER.WG, port_names=("o1", "o2"))
S_in_te1 = gf.Section(width=1, layer=LAYER.WG, port_names=("o1", "o2"))
S_out_te0 = gf.Section(width=1, layer=LAYER.WG, port_names=("o1", "o2"))
S_out_te1 = gf.Section(width=1.5, layer=LAYER.WG, port_names=("o1", "o2"))
X_in0 = gf.CrossSection(sections=[S_in_te0])
X_in1 = gf.CrossSection(sections=[S_in_te1])
X_out0 = gf.CrossSection(sections=[S_out_te0])
X_out1 = gf.CrossSection(sections=[S_out_te1])
# %% test tpaer
taper_in = gf.Component("taper_in_test")
taper_in_te0 = taper_in << gf.c.taper(width1=0.5, width2=1, length=500 - 100, layer=LAYER.WG)
taper_in_tes0 = taper_in << gf.c.straight(length=100, cross_section=X_in0)
taper_in_tes1 = taper_in << gf.c.straight(length=100, cross_section=X_in1)
taper_in_te0.connect("o1", other=taper_in_tes0.ports["o2"])
taper_in_tes1.connect("o1", taper_in_te0.ports["o2"])
taper_in.add_port(name="o1", port=taper_in_tes0.ports["o1"])
taper_in.add_port(name="o2", port=taper_in_tes1.ports["o2"])

taper_out = gf.Component("taper_out_test")
taper_out_te0 = taper_out << gf.c.taper(width2=1.5, width1=1, length=500 - 100, layer=LAYER.WG)
taper_out_tes1 = taper_out << gf.c.straight(length=100, cross_section=X_out1)
taper_out_tes0 = taper_out << gf.c.straight(length=100, cross_section=X_out0)
taper_out_te0.connect("o1", other=taper_out_tes0.ports["o2"])
taper_out_tes1.connect("o1", taper_out_te0.ports["o2"])
taper_out.add_port(name="o1", port=taper_out_tes0.ports["o1"])
taper_out.add_port(name="o2", port=taper_out_tes1.ports["o2"])
# remove layer
def remove_layer(
        component: Component = None,
        layer: LayerSpec = (1, 10)
) -> Component:
    """
    创建一个新的组件，该组件包含输入组件中除了指定图层之外的所有多边形。
    端口会被复制到新组件。

    参数:
        component (Component): 源 gdsfactory 组件。
        layer (LayerSpec): 要移除的 GDS 图层 (LayerSpec)。此图层上的多边形将不会被复制。
                           默认为 (1, 10)。

    返回:
        Component: 一个移除了指定图层多边形的新 gdsfactory 组件。
    """
    c = gf.Component()
    layers = component.layers
    for L in layers:
        if L != layer:
            polygons = component.get_polygons(by="tuple",layers=[L])
            for polygon in polygons[L]:
                c.add_polygon(polygon, layer=L)
    for port in component.ports:
        c.add_port(name=port.name, port=component.ports[port.name])
    return c
# %% add labels
'''add labels to optical ports'''
def add_labels_to_ports(
        component: Component,
        label_layer: LayerSpec = (512, 8),  # 指定文本标签的层次
        port_type: str = "optical",
        port_filter: str = None,
        label_on:bool = True,
        **kwargs,
):
    """
    为 gdsfactory 组件的端口添加文本标签。
    此函数会直接修改传入的组件。

    参数:
        component (Component): 需要添加标签的 gdsfactory 组件。
        label_layer (LayerSpec): 文本标签所在的 GDS 图层。默认为 (512, 8)。
        port_type (str): 根据端口类型筛选端口 (例如："optical", "electrical")。默认为 "optical"。
        port_filter (str | None): 用于筛选端口名称的字符串。如果端口名称包含此字符串，
                                 则会添加标签。如果为 None，则所有符合其他条件的端口都会被标记。
                                 默认为 None。
        **kwargs: 传递给 `component.get_ports_list()` 的其他关键字参数。
                  例如: layer, prefix, orientation, width, layers_excluded, clockwise。

    返回:
        None
    """
    # new_component = component.copy()  # 创建组件的副本
    # component = remove_layer(component, layer=label_layer)
    if label_on:
        ports = component.get_ports_list(port_type=port_type, **kwargs)
        for port in ports:
            if port_filter is None:
                component.add_label(text=port.name, position=port.center, layer=label_layer)
            else:
                portname = str(port)
                if port_filter in portname:
                    component.add_label(text=port.name, position=port.center, layer=label_layer)
    return

# %% original straight
@gf.cell
def GfCStraight(length=10, width=1, layer=(1, 0)):
    """
    创建一个简单的直波导组件。

    参数:
        length (float): 直波导的长度 (单位: um)。默认为 10.0 um。
        width (float): 直波导的宽度 (单位: um)。默认为 1.0 um。
        layer (LayerSpec): 波导所在的 GDS 图层。默认为 (1, 0)。

    返回:
        Component: 代表直波导的 gdsfactory 组件。

    端口:
        o1: 直波导一端的光学端口。
        o2: 直波导另一端的光学端口。
    """
    c = gf.Component()
    S = gf.Section(width = width,layer=layer,port_names=("o1","o2"))
    X = gf.CrossSection(sections=(S,))
    c=gf.c.straight(length=length, cross_section=X)
    return c


# %% gf.c.bend_euelr
def GfCBendEuler(
        radius: float | None = None,
        angle: float = 90.0,
        p: float = 0.5,
        with_arc_floorplan: bool = True,
        npoints: int | None = None,
        layer: LayerSpec | None = None,
        width: float | None = None,
        cross_section: CrossSectionSpec = "strip",
        allow_min_radius_violation: bool = False,
) -> ComponentAllAngle:
    """
    创建一个曲率半径变化的欧拉弯曲组件。
    此函数似乎是 gdsfactory 内置欧拉弯曲的一个封装或自定义实现。

    默认情况下，`radius` 对应于弯曲的最小曲率半径。
    但是，如果 `with_arc_floorplan` 为 True，`radius` 则对应于有效曲率半径
    （使得该曲线可以作为圆弧弯曲的直接替代品）。
    如果 p < 1.0，将创建一个 "部分欧拉" 曲线。

    参数:
        radius (float | None): 最小曲率半径 (单位: um)。默认为 `cross_section` 中定义的半径。
        angle (float): 曲线的总角度 (单位: 度)。默认为 90.0 度。
        p (float): 曲线中欧拉曲线部分的比例 (0 到 1)。默认为 0.5。
        with_arc_floorplan (bool): 如果为 False，`radius` 是最小曲率半径。
                                  如果为 True，曲线将被缩放，使得其端点与具有 `radius` 和 `angle`
                                  参数的圆弧弯曲相匹配。默认为 True。
        npoints (int | None): 用于路径每360度所使用的点数。默认为 None，由gdsfactory自动计算。
        layer (LayerSpec | None): 弯曲的特定 GDS 图层。如果提供，将覆盖 `cross_section` 的图层。
                               默认为 None。
        width (float | None): 弯曲的特定宽度。如果提供，将覆盖 `cross_section` 的宽度。
                             默认为 None。
        cross_section (CrossSectionSpec): 截面规格 (可以是 CrossSection 对象、字符串名称或字典)。
                                         默认为 "strip"。
        allow_min_radius_violation (bool): 如果为 True，则允许半径小于 `cross_section.min_radius`。
                                          默认为 False。

    返回:
        ComponentAllAngle: 代表欧拉弯曲的 gdsfactory 组件。

    端口:
        o1: 弯曲起始端的光学端口。
        o2: 弯曲结束端的光学端口。

    信息 (Info):
        length (float): 计算得到的弯曲长度。
        dx (float): 弯曲在水平方向上的跨度。
        dy (float): 弯曲在垂直方向上的跨度。
        min_bend_radius (float): 实现的最小弯曲半径。
        radius (float): 输入的半径参数。
        width (float): 弯曲的宽度。

    .. code::

                  o2
                  |
                 /
                /
               /
       o1_____/
    """
    x = gf.get_cross_section(cross_section)
    radius = radius or x.radius

    if radius is None:
        return gf.c.wire_corner(cross_section=x)

    if layer and width:
        x = gf.get_cross_section(
            cross_section, layer=layer or x.layer, width=width or x.width
        )
    elif layer:
        x = gf.get_cross_section(cross_section, layer=layer or x.layer)
    elif width:
        x = gf.get_cross_section(cross_section, width=width or x.width)

    path = gf.path.euler(
        radius=radius, angle=angle, p=p, use_eff=with_arc_floorplan, npoints=npoints
    )
    c = gf.path.extrude(p=path, cross_section=x)
    min_bend_radius = float(np.round(path.info["Rmin"], 3))
    c.info["length"] = float(np.round(path.length(), 3))
    c.info["dy"] = float(
        np.round(abs(float(path.points[0][0] - path.points[-1][0])), 3)
    )
    c.info["min_bend_radius"] = min_bend_radius
    c.info["radius"] = float(radius)
    c.info["width"] = width or x.width

    if not allow_min_radius_violation:
        x.validate_radius(radius)

    top = None if int(angle) in {180, -180, -90} else 0
    bottom = 0 if int(angle) in {-90} else None
    x.add_bbox(c, top=top, bottom=bottom)
    c.add_route_info(
        cross_section=x,
        length=c.info["length"],
        n_bend_90=abs(angle / 90.0),
        min_bend_radius=min_bend_radius,
    )
    return c


# %% TaperRsoa
@gf.cell()
def Crossing_taper(
        WidthCross: float = 1,
        WidthWg: float = 0.45,
        LengthTaper: float = 100,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个四端口交叉结构，每个臂上都带有锥形波导。
    一个中心的方形波导区域连接到四个锥形波导，形成输入/输出端口。

    参数:
        WidthCross (float): 锥形波导连接到中心方形区域的宽度 (锥形的较宽端)。默认为 1.0 um。
        WidthWg (float): 输入/输出端口处的波导宽度 (锥形的较窄端)，也用作中心方形区域的边长。
                         默认为 0.45 um。
        LengthTaper (float): 每个锥形波导的长度。默认为 100.0 um。
        oplayer (LayerSpec): 波导和锥形所在的 GDS 图层。默认为 LAYER.WG。

    返回:
        Component: 生成的带锥形臂的交叉组件。

    端口:
        o1: 光学端口1。
        o2: 光学端口2。
        o3: 光学端口3。
        o4: 光学端口4。
    """
    Crossing = gf.Component()
    center = Crossing << GfCStraight(width=WidthWg, length=WidthWg, layer=oplayer)
    center.movex(-WidthWg / 2)
    taper0 = gf.c.taper(width2=WidthCross, width1=WidthWg, layer=oplayer, length=LengthTaper)
    taper = list(range(4))
    for i in range(4):
        taper[i] = Crossing << taper0
        taper[i].connect("o2", other=center.ports["o1"], allow_width_mismatch=True)
        # taper[i].move([WidthWg/2*np.cos(90*i),WidthWg/2*np.sin(90*i)])
        taper[i].rotate(-90 * i)
        Crossing.add_port("o" + str(i + 1), port=taper[i].ports["o1"])
    add_labels_to_ports(Crossing)
    return Crossing


@gf.cell()
def TaperRsoa(
        AngleRsoa: float = 13,
        WidthRsoa: float = 8,
        WidthWg: float = 0.8,
        LengthRsoa: float = 200,
        LengthAdd: float = 100,
        RadiusBend: float = 50,
        layer: LayerSpec = LAYER.WG,
        layers: LayerSpecs | None = None,
) -> Component:
    """
    创建一个锥形波导组件，可能用于反射型半导体光放大器 (RSOA) 的端面。
    该组件由一个欧拉弯曲、一个锥形波导和一个直波导段组成。

    参数:
        AngleRsoa (float): 初始欧拉弯曲的角度 (单位: 度)。默认为 13.0 度。
        WidthRsoa (float): 锥形波导较宽端的宽度 (也是末端直波导的宽度)。默认为 8.0 um。
        WidthWg (float): 锥形波导较窄端的宽度 (也是欧拉弯曲的宽度)。默认为 0.8 um。
        LengthRsoa (float): 锥形部分的长度。默认为 200.0 um。
        LengthAdd (float): 宽端额外直波导部分的长度。默认为 100.0 um。
        RadiusBend (float): 初始欧拉弯曲的半径。默认为 50.0 um。
        layer (LayerSpec): 所有波导组件的 GDS 图层。默认为 LAYER.WG。
        Name (str): 组件的名称。默认为 "taper_rsoa"。

    返回:
        Component: 生成的 RSOA 锥形结构组件。

    端口:
        o1: 位于宽直波导段末端的光学端口。
        o2: 位于欧拉弯曲起始端的光学端口。
    """
    c = gf.Component()
    ebend = c << gf.components.bend_euler(angle=-AngleRsoa, width=WidthWg, radius=RadiusBend, layer=layer)
    rtaper = c << gf.components.taper(length=LengthRsoa, width1=WidthWg, width2=WidthRsoa, layer=layer)
    rstr = c << gf.components.straight(length=LengthAdd, width=WidthRsoa, layer=layer)
    rtaper.connect(port="o1", other=ebend.ports["o2"])
    rstr.connect(port="o1", other=rtaper.ports["o2"])
    c.add_port("o1", port=rstr.ports["o2"])
    c.add_port("o2", port=ebend.ports["o1"])
    return c


# %% OffsetRamp: 定义一个带有偏移的锥形渐变波导组件
@gf.cell  # 使用 gf.cell 装饰器，使其成为一个可缓存的 gdsfactory 单元
def OffsetRamp(
    length: float = 10.0,  # 渐变区域的长度，单位：um
    width1: float = 5.0,  # 输入端的宽度，单位：um
    width2: float | None = None,  # 输出端的宽度，单位：um (如果为None，则等于width1)
    offset: float = 0,  # 输出端中心相对于输入端中心的垂直偏移量，单位：um
    layer: LayerSpec = LAYER.WG,  # 波导层的定义
) -> Component:
    """
    创建一个带有偏移的锥形渐变波导组件 (Offset Ramp Component)。
    该组件用于连接两个不同宽度或在垂直方向上有所偏移的波导。
    它通过一个线性渐变的区域实现宽度的平滑过渡和位置的偏移。

    参数:
        length (float): 渐变区域的长度 (单位: um)。默认值为 10.0 um。
        width1 (float): 输入端的波导宽度 (单位: um)。默认值为 5.0 um。
        width2 (float | None): 输出端的波导宽度 (单位: um)。如果为 None，则输出宽度等于输入宽度 (width1)。
                               默认为 None。
        offset (float): 输出端中心相对于输入端中心的垂直偏移量 (单位: um)。
                        正值表示输出端向上偏移，负值表示向下偏移。默认值为 0 um。
        layer (LayerSpec): 定义波导的 GDS 图层。默认为 LAYER.WG。

    返回:
        Component: 生成的偏移渐变波导组件。

    端口:
        "o1": 输入端口，位于渐变区域的起始端 (左侧，x=0)。
        "o2": 输出端口，位于渐变区域的终止端 (右侧，x=length)。
    """
    # 如果未指定 width2，则使其等于 width1，创建一个等宽但可能有偏移的连接
    if width2 is None:
        width2 = width1

    c = gf.Component()  # 创建一个新的组件实例

    # 定义多边形的顶点坐标
    # (x, y) 坐标点列表，顺序定义了多边形的轮廓
    # (0, width1/2)          (length, width2/2 + offset)
    #   ____________________
    #  /                    \
    # /______________________\
    # (0, -width1/2)         (length, -width2/2 + offset)
    #
    points = [
        (0, width1 / 2),
        (length, width2 / 2 + offset),
        (length, -width2 / 2 + offset),
        (0, -width1 / 2),
    ]
    c.add_polygon(points, layer=layer)  # 添加多边形到组件中

    # 添加输入端口 "o1"
    c.add_port(
        name="o1",
        center=(0, 0),  # 端口中心位于 (0,0)
        width=width1,  # 端口宽度
        orientation=180,  # 端口方向指向左侧 (180度)
        layer=layer,
    )

    # 添加输出端口 "o2"
    c.add_port(
        name="o2",
        center=(length, offset),  # 端口中心位于 (length, offset)
        width=width2,  # 端口宽度
        orientation=0,  # 端口方向指向右侧 (0度)
        layer=layer,
    )
    return c


# %% cir2end
@gf.cell()
def cir2end(
        WidthNear: float = 1,
        WidthEnd: float = 0.5,
        LengthTaper: float = 100,
        Pitch: float = 10,
        RadiusBend0: float = 50,
        Period: float = 5.5,
        oplayer: LayerSpec = LAYER.WG,
        layers: LayerSpecs | None = None,
        Name="cir2end"
) -> Component:
    """
    创建一个从锥形波导过渡到一系列半径递减的180度圆弧弯曲的组件。
    这可能用于实现一个紧凑的延迟线、螺旋结构或者特定的模式转换器。

    参数:
        WidthNear (float): 靠近输入端的波导宽度 (锥形的较宽端)。默认为 1.0 um。
        WidthEnd (float): 末端波导宽度 (锥形的较窄端，也是所有圆弧部分的宽度)。默认为 0.5 um。
        LengthTaper (float): 初始锥形波导的长度。默认为 100.0 um。
        Pitch (float): 相邻180度圆弧对（一个完整周期）的半径减小量。
                       或者说，每经过一个180度弯曲，下一个同向180度弯曲的半径减小 Pitch。
                       原代码中 `RadiusBend0 - (i + 1) * Pitch / 2` 暗示 Pitch 是直径相关的变化，
                       或者每个半圆半径减小 Pitch/2。这里假设 Pitch 是指每个完整周期（两个180度弯）的半径差。
                       为了清晰，这里将 Pitch 理解为每个180度弯曲半径相对于前一个同方向弯曲的减小量。
                       默认为 10.0 um。
        RadiusBend0 (float): 第一个 (最外层) 180度圆弧弯曲的半径。默认为 50.0 um。
        Period (float): 定义了180度圆弧弯曲的对数 (或周期数)。总共会产生 `2 * int(Period)` 个180度弯曲。
                        原代码 Period=5.5 可能会导致非整数个弯曲，这里会取整。默认为 5.5。
        oplayer (LayerSpec): 光学波导层。默认为 LAYER.WG。
        Name (str): 组件名称。默认为 "cir2end"。

    返回:
        Component: 生成的 "cir2end" 组件。

    端口:
        o1: 组件的输入端口，位于初始锥形波导的宽端。
        (注意：原代码没有明确定义输出端口，最后一个圆弧的o2端口未导出。
         如果需要输出端口，应在最后一个圆弧后添加。)
    """
    c = gf.Component()
    taper = c << gf.c.taper(width1=WidthNear, width2=WidthEnd, length=LengthTaper, layer=oplayer)
    if RadiusBend0 - Period * Pitch < 10:
        Period = (2 * RadiusBend0 - 10) // Pitch / 2  # avoid minus radius
    # circle
    bendcir = list(range(int(2 * Period)))
    bendcir[0] = c << gf.c.bend_circular180(width=WidthEnd, radius=RadiusBend0, layer=oplayer)
    bendcir[0].connect("o1", other=taper.ports["o2"])
    for i in range(int(2 * Period - 1)):
        bendcir[i + 1] = c << gf.c.bend_circular180(width=WidthEnd, radius=RadiusBend0 - (i + 1) * Pitch / 2,
                                                    layer=oplayer)
        bendcir[i + 1].connect("o1", other=bendcir[i].ports["o2"])
    # setports
    c.add_port(name="o1", port=taper.ports["o1"])
    return c


# %% euler_Bend_Half
def euler_Bend_Half(
        radius: float = 10,
        angle: float = 90,
        p: float = 0.5,
        flip: bool = False,
        use_eff: bool = False,
        npoints: int | None = None,
        direction: str = "Backward",  # "Backward": euler→straight; "Forward": straight→euler
) -> Path:
    """
    生成一个半欧拉弯曲（Euler Bend Half）路径。

    根据 `direction` 参数控制弯曲方向：
    - "Forward": 从直线逐渐过渡到圆弧；
    - "Backward": 从圆弧逐渐过渡到直线。

    当 `use_eff=True` 时，`radius` 表示等效曲率半径，使得该曲线与具有相同
    半径和角度的理想圆弧端点一致，可直接替代圆弧弯曲；
    当 `use_eff=False` 时，`radius` 表示最小曲率半径。

    参数:
        radius (float): 最小曲率半径（或有效半径）。单位 μm，默认 10。
        angle (float): 总弯曲角度（度），默认 90。
        p (float): 欧拉过渡部分占比，范围 (0, 1]，默认 0.5。
        flip (bool): 是否上下翻转曲线（y 取负）。默认 False。
        use_eff (bool): 是否使用等效半径匹配端点。默认 False。
        npoints (int | None): 每 360° 弯曲的采样点数，None 表示自动估算。
        direction (str): 曲线方向，可选 "Forward" 或 "Backward"。默认 "Backward"。

    返回:
        Path: 表示半欧拉弯曲的路径对象。

    异常:
        ValueError: 若 `p` 不在 (0, 1] 或 `direction` 非法。

    示例:
        >>> path = euler_Bend_Half(radius=10, angle=45, p=0.7, use_eff=True, direction="Forward")
        >>> path.plot()
    """

    if direction == "Backward":
        return euler_Bend_Half_Backward(radius,angle,p,flip,use_eff,npoints,)
    elif direction == "Forward":
        return euler_Bend_Half_Forward(radius,angle,p,flip,use_eff,npoints,)
    else:
        raise ValueError("direction must be 'Forward' or 'Backward'")
# %% euler_Bend_Half：从圆弧过渡到直线的欧拉路径
def euler_Bend_Half_Backward(
        radius: float = 10,
        angle: float = 90,
        p: float = 0.5,
        flip: bool = False,
        use_eff: bool = False,
        npoints: int | None = None,
) -> Path:
    """
    生成一个从圆弧逐渐过渡到直线的半欧拉弯曲路径（Euler Bend Half, Backward）。

    该函数生成的路径代表完整欧拉弯曲的一半：起始曲率最大（即圆弧部分），
    最终逐渐过渡为直线。常用于波导弯曲端或耦合器平滑过渡。

    当 `use_eff=True` 时，`radius` 表示等效曲率半径，曲线端点与同半径圆弧一致；
    当 `use_eff=False` 时，`radius` 表示最小曲率半径。

    参数:
        radius (float): 最小或有效曲率半径。单位 μm。
        angle (float): 弯曲总角度（度）。
        p (float): 欧拉部分占比，范围 (0, 1]。
        flip (bool): 是否上下翻转曲线（y 取负）。
        use_eff (bool): 是否使用等效半径匹配端点。
        npoints (int | None): 每 360° 弯曲的采样点数，None 自动计算。

    返回:
        Path: 半欧拉弯曲路径对象。

    异常:
        ValueError: 若 `p` 不在 (0, 1]。

    示例:
        >>> path = euler_Bend_Half_Backward(radius=10, angle=90, p=0.5)
        >>> path.plot()
    """

    if (p <= 0) or (p > 1):
        raise ValueError("euler requires argument `p` be between 0 and 1")

    if angle < 0:
        mirror = True
        angle = np.abs(angle)
    else:
        mirror = False

    R0 = 1
    alpha = np.radians(angle * 2)
    Rp = R0 / (np.sqrt(p * alpha))
    sp = R0 * np.sqrt(p * alpha)
    s0 = 2 * sp + Rp * alpha * (1 - p)

    pdk = get_active_pdk()
    npoints = npoints or abs(int(angle / 360 * radius / pdk.bend_points_distance / 2))
    npoints = max(npoints, int(360 / angle) + 1)

    num_pts_euler = int(np.round(sp / (s0 / 2) * npoints))
    num_pts_arc = npoints - num_pts_euler

    # Ensure a minimum of 2 points for each euler/arc section
    if npoints <= 2:
        num_pts_euler = 0
        num_pts_arc = 2

    if num_pts_euler > 0:
        xbend1, ybend1 = _fresnel(R0, sp, num_pts_euler)
        xp, yp = xbend1[-1], ybend1[-1]
        dx = xp - Rp * np.sin(p * alpha / 2)
        dy = yp - Rp * (1 - np.cos(p * alpha / 2))
    else:
        xbend1 = ybend1 = np.asfarray([])
        dx = 0
        dy = 0

    s = np.linspace(sp, s0 / 2, num_pts_arc)
    xbend2 = Rp * np.sin((s - sp) / Rp + p * alpha / 2) + dx
    ybend2 = Rp * (1 - np.cos((s - sp) / Rp + p * alpha / 2)) + dy

    x = np.concatenate([xbend1, xbend2[1:]])
    y = np.concatenate([ybend1, ybend2[1:]])

    points1 = np.array([x, y]).T
    points2 = np.flipud(np.array([x, -y]).T)

    points2 = rotate_points(points2, angle - 180)
    points2 += -points2[0, :]

    points = points2

    # Find y-axis intersection point to compute Reff
    start_angle = 180 * (angle < 0)
    end_angle = start_angle + angle
    dy = np.tan(np.radians(end_angle - 90)) * points[-1][0]
    Reff = points[-1][1] - dy
    Rmin = Rp

    # Fix degenerate condition at angle == 180
    if np.abs(180 - angle) < 1e-3:
        Reff = points[-1][1] / 2

    # Scale curve to either match Reff or Rmin
    scale = radius / Reff if use_eff else radius / Rmin
    points *= scale

    P = Path()

    # Manually add points & adjust start and end angles
    P.points = points
    P.start_angle = start_angle
    P.end_angle = end_angle
    P.info["Reff"] = Reff * scale
    P.info["Rmin"] = Rmin * scale
    if mirror:
        P.mirror((1, 0))
    return P
# 从直线过渡到圆弧的欧拉路径
def euler_Bend_Half_Forward(
        radius: float = 10,
        angle: float = 90,
        p: float = 0.5,
        flip: bool = False,
        use_eff: bool = False,
        npoints: int | None = None,
) -> Path:
    """
    生成一个从直线逐渐过渡到圆弧的半欧拉弯曲路径（Euler Bend Half, Forward）。

    该函数生成的路径表示欧拉弯曲的前半段：
    起始为直线（曲率为零），沿程曲率逐渐增大，最终过渡为半径为 `radius` 的圆弧。
    该形式常用于波导从直线进入弯曲段的平滑连接。

    当 `use_eff=True` 时，`radius` 表示等效曲率半径，端点与同半径圆弧一致；
    当 `use_eff=False` 时，`radius` 表示最小曲率半径。

    参数:
        radius (float): 最小或有效曲率半径。单位 μm。
        angle (float): 弯曲总角度（度）。
        p (float): 欧拉部分占比，范围 (0, 1]。
        flip (bool): 是否上下翻转曲线（y 取负）。
        use_eff (bool): 是否使用等效半径匹配端点。
        npoints (int | None): 每 360° 弯曲的采样点数，None 自动计算。

    返回:
        Path: 半欧拉弯曲路径对象。

    异常:
        ValueError: 若 `p` 不在 (0, 1]。

    示例:
        >>> path = euler_Bend_Half_Forward(radius=10, angle=45, p=0.8, use_eff=False)
        >>> path.plot()
    """
    if (p <= 0) or (p > 1):
        raise ValueError("`p` 必须在 (0, 1] 之间")

    if angle < 0:
        mirror = True
        angle = np.abs(angle)
    else:
        mirror = False

    R0 = 1
    alpha = np.radians(angle * 2)
    Rp = R0 / np.sqrt(p * alpha)
    sp = R0 * np.sqrt(p * alpha)
    s0 = 2 * sp + Rp * alpha * (1 - p)

    # 自动确定采样点数
    pdk = get_active_pdk()
    npoints = npoints or abs(int(angle / 360 * radius / pdk.bend_points_distance / 2))
    npoints = max(npoints, int(360 / angle) + 1)

    num_pts_euler = int(np.round(sp / (s0 / 2) * npoints))
    num_pts_arc = npoints - num_pts_euler
    num_pts_euler = max(num_pts_euler, 2)

    # --- 生成欧拉曲线前半段（从直线 → 弯曲）
    xbend1, ybend1 = _fresnel(R0, sp, num_pts_euler)
    # 缩放使得终点曲率=1/Rp
    xbend1 *= R0
    ybend1 *= R0

    # --- 生成纯圆弧段
    s = np.linspace(sp, s0 / 2, num_pts_arc)
    xbend2 = Rp * np.sin((s - sp) / Rp + p * alpha / 2) + xbend1[-1] - Rp * np.sin(p * alpha / 2)
    ybend2 = Rp * (1 - np.cos((s - sp) / Rp + p * alpha / 2)) + ybend1[-1] - Rp * (1 - np.cos(p * alpha / 2))

    # 合并坐标
    x = np.concatenate([xbend1, xbend2[1:]])
    y = np.concatenate([ybend1, ybend2[1:]])

    points = np.array([x, y]).T

    # 缩放匹配真实半径
    Rmin = Rp
    Reff = points[-1][1] / (1 - np.cos(np.radians(angle)))
    scale = radius / (Reff if use_eff else Rmin)
    points *= scale

    # 若 flip，则翻转曲线方向
    if flip:
        points[:, 1] *= -1

    # 输出 Path
    P = Path()
    P.points = points
    P.start_angle = 0
    P.end_angle = angle
    P.info["Rmin"] = Rmin * scale
    P.info["Reff"] = Reff * scale
    # 若 angle 为负，则镜像
    if mirror:
        P.mirror((1, 0))
    return P

# 部分欧拉弯曲的路径
def euler_Bend_Part(
        radius1: float = 10.0,
        radius2: float = 20.0,
        angle: float = 90.0,
        p: float = 0.5,
        use_eff: bool = False,
        npoints: int | None = None,
) -> Path:
    """
    生成一段“线性曲率过渡 + 固定半径圆弧”组合弯曲路径。

    说明：
      - 前 p*angle 的角度使用线性曲率过渡（曲率在弧长上线性插值，从 1/radius1 -> 1/radius2）。
      - 剩余 (1-p)*angle 为曲率 1/radius2 的圆弧。
      - 该实现保证位置和切线连续（曲率在连接点处连续）。
      - 注：这是“线性曲率过渡”模型，不是严格数学意义上的 Clothoid（如果需要严格 clothoid，请告知）。

    参数与返回见原始函数。若输入 angle < 0，则生成的路径将关于 x 轴镜像。
    """
    if radius1 <= 0 or radius2 <= 0:
        raise ValueError("Radius values must be positive")
    if (p <= 0) or (p > 1):
        raise ValueError("euler requires argument `p` be between 0 and 1")

    # 规范化角度
    mirror = angle < 0
    angle_abs = abs(float(angle))
    alpha = np.radians(angle_abs)  # total angle in radians

    # 划分欧拉段角度与圆弧段角度 (radians)
    alpha_euler = p * alpha
    alpha_arc = alpha - alpha_euler  # 可能为 0

    # 若 alpha_euler 非零，则基于线性曲率变化推导 s_total：
    # 对于 kappa(s) = k1 + (k2-k1)*(s/s_total)
    # alpha_euler = ∫_0^{s_total} kappa(s) ds = s_total*(k1 + k2)/2
    k1 = 1.0 / radius1
    k2 = 1.0 / radius2

    if alpha_euler > 0:
        s_total = 2 * alpha_euler / (k1 + k2)  # 自洽解
    else:
        s_total = 0.0

    # 动态曲率函数（线性随 s）
    def dynamic_curvature(s: float) -> float:
        if s_total == 0:
            return k2
        return k1 + (k2 - k1) * (s / s_total)

    # 计算点数
    pdk = get_active_pdk()
    # 若 pdk 未设置 bend_points_distance，则退回到一个默认值保护
    try:
        base_dist = float(pdk.bend_points_distance)
        if base_dist <= 0:
            base_dist = 0.5
    except Exception:
        base_dist = 0.5

    if npoints is None:
        # 依据最大半径近似估计点数（保守估计）
        est_len = max(radius1, radius2) * alpha / 1.0
        npoints = max(6, int(np.ceil(est_len / base_dist)))
    else:
        npoints = max(6, int(npoints))

    # 分配欧拉段、圆弧段点数（都至少 2）
    num_pts_euler = max(2, int(round(npoints * p)))
    num_pts_arc = max(2, npoints - num_pts_euler)
    # 若 alpha_arc == 0，则全部给欧拉段
    if alpha_arc <= 1e-12:
        num_pts_euler = npoints
        num_pts_arc = 0

    # ---------------------------
    # 1) 生成欧拉（线性曲率）段
    # ---------------------------
    x_euler = np.zeros(0)
    y_euler = np.zeros(0)
    theta = 0.0
    if num_pts_euler >= 2 and s_total > 0:
        s_vals = np.linspace(0.0, s_total, num_pts_euler)
        ds = s_total / (num_pts_euler - 1)
        xs = []
        ys = []
        cur_x = 0.0
        cur_y = 0.0
        cur_theta = 0.0
        for i, s in enumerate(s_vals):
            # 在每一步使用当前曲率近似（用 s 或 s-ds/2 中点也可）
            kappa = dynamic_curvature(s)
            # 对角度增量积分
            if i == 0:
                dtheta = 0.0
            else:
                dtheta = kappa * ds
            cur_theta += dtheta
            # 小步位移
            cur_x += ds * np.cos(cur_theta)
            cur_y += ds * np.sin(cur_theta)
            xs.append(cur_x)
            ys.append(cur_y)
        x_euler = np.array(xs)
        y_euler = np.array(ys)
        theta = cur_theta  # 欧拉段末端切线角（rad）
    else:
        # 没有欧拉段 => 起点位于原点，theta 初始为 0
        x_euler = np.array([0.0])
        y_euler = np.array([0.0])
        theta = 0.0

    # ---------------------------
    # 2) 生成圆弧段（基于 radius2，且与欧拉段末端切线对齐）
    # ---------------------------
    x_arc = np.zeros(0)
    y_arc = np.zeros(0)
    if num_pts_arc > 0 and alpha_arc > 0:
        R = radius2
        # arc angles从 theta 到 theta + alpha_arc
        phi_vals = np.linspace(theta, theta + alpha_arc, num_pts_arc)

        # 计算圆心位置： center = end_point + R * (-sin(theta), cos(theta))
        end_x = x_euler[-1]
        end_y = y_euler[-1]
        cx = end_x + R * (-np.sin(theta))
        cy = end_y + R * ( np.cos(theta))

        # 点坐标 param: (cx + R*sin(phi), cy - R*cos(phi))
        xs = cx + R * np.sin(phi_vals)
        ys = cy - R * np.cos(phi_vals)
        # 为避免重复首点，首点与欧拉段末点重复，后续合并时会剔除
        x_arc = np.array(xs)
        y_arc = np.array(ys)
    elif num_pts_arc > 0 and alpha_arc <= 0:
        # alpha_arc == 0: no arc; handled above
        x_arc = np.zeros(0)
        y_arc = np.zeros(0)

    # ---------------------------
    # 3) 合并并处理重复首点
    # ---------------------------
    if x_arc.size == 0:
        x = x_euler
        y = y_euler
    else:
        # 避免重复欧拉末点与弧首点
        x = np.concatenate([x_euler, x_arc[1:]])
        y = np.concatenate([y_euler, y_arc[1:]])

    points = np.column_stack([x, y])

    # ---------------------------
    # 4) 可选缩放（use_eff）
    #    说明：此处将路径缩放使其“等效半径(Reff)”接近中间半径 (radius1+radius2)/2
    # ---------------------------
    end_x, end_y = points[-1]
    # 保护：若 alpha 非零，计算等效半径（基于圆弧几何的近似）
    if alpha > 1e-12:
        Reff = np.sqrt(end_x ** 2 + end_y ** 2) / (2 * np.sin(alpha / 2))
    else:
        Reff = (radius1 + radius2) / 2.0

    if use_eff and Reff > 0:
        target_Reff = (radius1 + radius2) / 2.0
        scale_factor = target_Reff / Reff
        points = points * scale_factor
        Reff = Reff * scale_factor
    else:
        scale_factor = 1.0

    # ---------------------------
    # 5) 创建 Path 并记录信息
    # ---------------------------
    # 使用 Path(points) 构造（更符合 gdsfactory）
    path = Path(points.tolist())
    # 记录一些信息
    path.info.update({
        "R_start": radius1,
        "R_end": radius2,
        "curvature_start": k1,
        "curvature_end": k2,
        "alpha_total_deg": angle_abs,
        "alpha_total_rad": alpha,
        "alpha_euler_deg": np.degrees(alpha_euler),
        "alpha_arc_deg": np.degrees(alpha_arc),
        "s_total_euler": s_total,
        "Reff_used": Reff,
        "scale_factor": scale_factor,
        "p": p,
    })

    # 如果原始 angle 为负数，镜像 x 轴（与原函数行为一致）
    if mirror:
        path.mirror((1, 0))

    return path


# %% QRcode of team website
@gf.cell()
def TWQRcode(
        Size: float = 10,
        lglayer: LayerSpec = (10, 0)
) -> Component:
    """
    创建一个包含指定网站URL的QR码组件。

    参数:
        Size (float): QR码中每个像素点 (小方块) 的尺寸 (单位: um)。默认为 10.0 um。
        lglayer (LayerSpec): QR码图形所在的 GDS 图层。默认为 (10, 0)。

    返回:
        Component: 生成的QR码组件。
                   组件名为 "logo" (可以考虑改为更具描述性的名称，如 "team_website_qrcode")。
    """
    logo = gf.Component("logo")
    qrcode = logo << gf.c.qrcode(data='https://photonics.pku.edu.cn/', psize=Size, layer=lglayer)
    return logo


# %% Component shift
def shift_component(component: Component, dx: float, dy: float) -> Component:
    """
    创建一个新组件，其中包含原始组件所有元素平移 (dx, dy)后的副本。
    原始组件保持不变。

    参数:
        component (Component): 需要平移的源组件。
        dx (float): 在 x 方向上的平移量。
        dy (float): 在 y 方向上的平移量。

    返回:
        Component: 一个包含平移后所有元素的新组件。
    """
    new_component = Component()  # 创建一个新的组件实例

    # 将原始组件的所有元素平移并添加到新组件中
    for ref in component.references:
        new_component.add_ref(ref.parent).move([dx, dy])

    for polygon in component.polygons:
        new_component.add_polygon(polygon.points + (dx, dy), layer=polygon.layer)

    for label in component.labels:
        new_component.add_label(
            text=label.text,
            position=(label.origin[0] + dx, label.origin[1] + dy),
            layer=label.layer,
            magnification=label.magnification,
            rotation=label.rotation,
        )

    # 平移所有端口
    for port in component.ports.values():
        new_component.add_port(port=port.copy().move([dx, dy]))

    return new_component


# %% Get gds from layer
def GetFromLayer(
        CompOriginal: Component = None,
        OLayer: LayerSpec = (1, 0),
        FLayer: LayerSpec = None,
) -> Component:
    """
    从原始组件 (CompOriginal) 中提取指定原始图层 (OLayer) 上的所有多边形，
    并将这些多边形放置到一个新的组件中，可以指定一个新的最终图层 (FLayer)。
    原始组件的端口会被复制到新组件。

    参数:
        CompOriginal (Component): 要从中提取图层的原始组件。
        OLayer (LayerSpec): 要从原始组件中提取的多边形所在的图层。默认为 (1, 0)。
        FLayer (LayerSpec | None): 提取出的多边形在新组件中要赋予的图层。
                                   如果为 None，则使用与 OLayer 相同的图层。默认为 None。

    返回:
        Component: 一个新的组件，仅包含从原始组件的 OLayer 上提取并在 FLayer 上重绘的多边形，
                   以及复制的端口。
    """
    if FLayer is None:
        FLayer = OLayer
    CompFinal = gf.Component()
    pols = CompOriginal.get_polygons_points(layers=[OLayer],by="tuple")
    for pol in pols[OLayer]:
        CompFinal.add_polygon(points=pol, layer=FLayer)
    for port in CompOriginal.ports:
        CompFinal.add_port(name=port.name, port=port)
    return CompFinal

# %% TotalComponent
r_euler_false = 500
r_euler_true = 500 * 1.5
