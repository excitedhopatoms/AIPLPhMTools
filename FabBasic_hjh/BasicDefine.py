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

PDK = get_generic_pdk()
PDK.activate()


# layer define
class LayerMapUserDef(LayerMap):
    WG:Layer = (1,0)
    M1:Layer = (3, 0)# 高频电极
    M2:Layer = (4 , 0) # 加热电极
    VIA:Layer=(70,0)
    OPEN:Layer = (5 , 0)
    SR1:Layer = (216 , 0)
    NONSR1:Layer = (216 , 100)
    SR2:Layer = (217 , 0)
    NONSR2:Layer = (217 , 100)
    AA:Layer = (10 , 0)
    KV:Layer = (9 , 0)
    P2:Layer = (31 , 0)
    NONP2:Layer = (31 , 100)
    CPF:Layer = (130 , 0)# 氮化硅波导层
    CAA:Layer = (196 , 0)# 离子注入保护层
    TN:Layer = (24 , 0)
    TP:Layer = (15 , 0)
    NLH:Layer = (36 , 0)
    PLH:Layer = (37 , 0)
    NLL:Layer = (35 , 0)
    PLL:Layer = (38 , 0)
    SN:Layer = (40 , 0)
    SP:Layer = (43 , 0)
    P1:Layer = (32 , 0)
    SAB:Layer = (48 , 0)
    NONSAB:Layer = (48 , 100)
    V0:Layer = (219 , 0)
    CT:Layer = (50 , 0)
    DT:Layer = (51 , 0)
    LM1:Layer = (125 , 0)
    SINEC:Layer = (89 , 100)
    V1:Layer = (70 , 0)
    TSW:Layer = (159 , 100)
    V2:Layer = (71 , 0)
    M6:Layer = (66 , 0)
    MIM:Layer = (58 , 0)
    TSW2:Layer = (160 , 100)
    TV:Layer = (78 , 0)
    TM:Layer = (69 , 0)
    PA:Layer = (80 , 0)
    DO1:Layer = (55 , 100)
    HVO:Layer = (111 , 0)
    DUMBA:Layer = (120,0)
    DUMBN:Layer = (130,2)
    DUMBM:Layer = (121,0)
    WAFER:Layer = (1000,0)

LAYER = LayerMapUserDef
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
) -> Path:
    """
    返回一个欧拉弯曲路径，该路径从弯曲状态逐渐过渡到直线状态 (或者说，是完整欧拉弯曲的一半)。

    如果 `use_eff` 为 True，`radius` 参数对应于有效曲率半径，使得该曲线
    可以作为具有相同 `radius` 和 `angle` 的圆弧弯曲的直接替代品。
    如果 `use_eff` 为 False (默认)，`radius` 参数对应于弯曲的最小曲率半径。
    参数 `p` 控制曲线中纯欧拉过渡部分的比例。

    参数:
        radius (float): 最小曲率半径 (如果 use_eff=False) 或有效半径 (如果 use_eff=True)。
                        默认为 10.0 um。
        angle (float): 曲线的总角度 (单位: 度)。默认为 90.0 度。
        p (float): 曲线中欧拉部分的比例 (0 < p <= 1)。默认为 0.5。
        use_eff (bool): 如果为 False，`radius` 是最小曲率半径。
                        如果为 True，曲线将被缩放以匹配具有 `radius` 和 `angle` 参数的圆弧的端点。
                        默认为 False。
        npoints (int | None): 用于生成路径每360度的点数。默认为 None (由gdsfactory自动计算)。

    返回:
        Path: 生成的半欧拉弯曲路径对象。

    异常:
        ValueError: 如果 `p` 不在 (0, 1] 范围内。

    示例:
        >>> path = euler_Bend_Half(radius=10, angle=45, p=1, use_eff=True)
        >>> # path.plot() # 在Jupyter等环境中可以绘图查看
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


# %% euler_Bend_Half
def euler_Bend_Part(
        radius1: float = 10.0,
        radius2: float = 20.0,
        angle: float = 90.0,
        p: float = 0.5,
        use_eff: bool = False,
        npoints: int | None = None,
) -> Path:
    """
    创建一个欧拉弯曲路径，其曲率从 1/radius1 平滑过渡到 1/radius2。

    参数:
        radius1 (float): 起始曲率半径 (单位: um)。默认为 10.0 um。
        radius2 (float): 结束曲率半径 (单位: um)。默认为 20.0 um。
        angle (float): 弯曲的总角度 (单位: 度)。默认为 90.0 度。
        p (float): 欧拉过渡段所占总角度的比例 (0 < p <= 1)。
                   p=1 表示整个弯曲都是动态曲率过渡。
                   p<1 表示前 p*angle 的角度是动态曲率过渡，
                   剩余 (1-p)*angle 的角度是一个曲率为 1/radius2 的圆弧。
                   默认为 0.5。
        use_eff (bool): 如果为 True，则尝试缩放路径，使其端点行为类似于某个“有效半径”的圆弧。
                        此处的“有效半径”可能基于 radius1 或 (radius1+radius2)/2。默认为 False。
        npoints (int | None): 生成路径的总点数。默认为 None (由gdsfactory自动计算)。

    返回:
        Path: 生成的欧拉弯曲路径对象。

    异常:
        ValueError: 如果 radius1 或 radius2 非正，或者 p 不在 (0, 1] 范围内。
    """
    if radius1 <= 0 or radius2 <= 0:
        raise ValueError("Radius values must be positive")
    if (p <= 0) or (p > 1):
        raise ValueError("euler requires argument `p` be between 0 and 1")
    angle = float(angle)
    alpha = np.radians(abs(angle))  # Total angle in radians
    mirror = angle < 0
    angle = abs(angle)

    # =========================================================================
    # 核心修改1: 支持任意半径方向变化的曲率计算
    # =========================================================================
    def dynamic_curvature(s: float, s_total: float) -> float:
        """曲率从 1/radius1 线性过渡到 1/radius2"""
        return 1 / radius1 + (1 / radius2 - 1 / radius1) * (s / s_total)

    # =========================================================================
    # 计算欧拉曲线部分参数
    # =========================================================================

    # 计算欧拉曲线总弧长（基于起始曲率radius1）
    s_total = radius1 * np.sqrt(p * alpha)  # 欧拉部分总弧长

    # =========================================================================
    # 核心修改2: 通用化积分过程（支持曲率增加或减少）
    # =========================================================================
    def generate_euler_curve(num_pts: int) -> tuple[np.ndarray, np.ndarray]:
        """动态曲率积分（自动处理正反向变化）"""
        s_values = np.linspace(0, s_total, num_pts)
        x, y = [], []
        current_theta = 0.0
        current_x = 0.0
        current_y = 0.0

        for s in s_values:
            curvature = dynamic_curvature(s, s_total)
            ds = s_total / (num_pts - 1) if num_pts > 1 else 0

            # 始终正向积分，曲率变化方向由dynamic_curvature自动处理
            dtheta = ds * curvature
            current_theta += dtheta
            dx = ds * np.cos(current_theta)
            dy = ds * np.sin(current_theta)
            current_x += dx
            current_y += dy

            x.append(current_x)
            y.append(current_y)

        return np.array(x), np.array(y)

    # =========================================================================
    # 生成路径点
    # =========================================================================
    pdk = get_active_pdk()
    npoints = npoints or int(abs(angle / 360 * max(radius1, radius2) / pdk.bend_points_distance))
    npoints = max(npoints, 5)

    # 分割欧拉曲线和圆弧部分
    num_pts_euler = int(npoints * p)
    num_pts_arc = npoints - num_pts_euler

    # 生成动态曲率的欧拉曲线部分
    x_euler, y_euler = generate_euler_curve(num_pts_euler)

    # 生成圆弧部分（使用radius2作为最终曲率）
    theta_arc = alpha * (1 - p)
    theta_values = np.linspace(0, theta_arc, num_pts_arc)
    R_arc = radius2  # 圆弧部分曲率固定为radius2

    # 计算圆弧部分坐标（与欧拉曲线终点平滑连接）
    x_arc = R_arc * np.sin(theta_values) + x_euler[-1] - R_arc * np.sin(theta_arc)
    y_arc = R_arc * (1 - np.cos(theta_values)) + y_euler[-1] - R_arc * (1 - np.cos(theta_arc))

    # 合并坐标点
    x = np.concatenate([x_euler, x_arc[1:]])
    y = np.concatenate([y_euler, y_arc[1:]])

    # =========================================================================
    # 路径后处理
    # =========================================================================
    points = np.column_stack([x, y])

    # 计算有效半径（基于终点位置）
    end_x, end_y = points[-1]
    Reff = np.sqrt(end_x ** 2 + end_y ** 2) / (2 * np.sin(alpha / 2))

    # 缩放处理（根据use_eff决定是否匹配等效半径）
    scale_factor = radius1 / Reff if use_eff else 1.0
    points *= scale_factor

    # 创建Path对象
    path = Path()
    path.points = points
    path.start_angle = 0.0
    path.end_angle = np.degrees(theta_arc)

    # 存储物理参数
    path.info.update({
        "Reff": Reff * scale_factor,
        "R_start": radius1,
        "R_end": radius2,
        "curvature_start": 1 / radius1,
        "curvature_end": 1 / radius2
    })

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
    CompFinal = gf.Component(CompOriginal.name + "Layer=" + str(OLayer))
    pols = CompOriginal.get_polygons_points(layers=[OLayer])
    for pol in pols[OLayer]:
        CompFinal.add_polygon(points=pol, layer=FLayer)
    for port in CompOriginal.ports:
        CompFinal.add_port(name=port.name, port=port)
    return CompFinal

# %% TotalComponent
r_euler_false = 500
r_euler_true = 500 * 1.5
