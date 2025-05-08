from collections.abc import Callable

import gdsfactory as gf
import numpy as np
from gdsfactory.component import Component
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
    DT: Layer = (157, 0)
    M2: Layer = (18, 0)
    VIA: Layer = (19, 0)
    OPEN: Layer = (9, 0)
    test: Layer = (1, 20)
    WG: Layer = (1, 0)
    CLD: Layer = (1, 1)
    M1: Layer = (10, 0)
    LABEL: Layer = (10, 0)
    WAFER: Layer = (20, 0)
    WRITEFIELD: Layer = (30, 0)


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
    从组件中删除指定层的所有多边形。

    参数：
        component: 目标组件。
        layer: 要删除的层号，例如 (1, 0)。
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
    """Add labels to component ports.

    Args:
        component: to add labels.
        label_layer: layer spec for the label.
        port_type: to select ports.

    keyword Args:
        layer: select ports with GDS layer.
        prefix: select ports with prefix in port name.
        orientation: select ports with orientation in degrees.
        width: select ports with port width.
        layers_excluded: List of layers to exclude.
        port_type: select ports with port_type (optical, electrical, vertical_te).
        clockwise: if True, sort ports clockwise, False: counter-clockwise.
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
    c = gf.Component()
    c.add_polygon([(0, -width/2), (length, -width/2), (length, width/2), (0, width/2)], layer=layer)
    c.add_port(
        name="o1", center=[0, 0], width=width, orientation=180, layer=layer
    )
    c.add_port(
        name="o2", center=[length, 0], width=width, orientation=0, layer=layer
    )
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
) -> Component:
    """Euler bend with changing bend radius.

    By default, `radius` corresponds to the minimum radius of curvature of the bend.
    However, if `with_arc_floorplan` is True, `radius` corresponds to the effective
    radius of curvature (making the curve a drop-in replacement for an arc). If
    p < 1.0, will create a "partial euler" curve as described in Vogelbacher et.
    al. https://dx.doi.org/10.1364/oe.27.031394

    default p = 0.5 based on this paper
    https://www.osapublishing.org/oe/fulltext.cfm?uri=oe-25-8-9150&id=362937

    Args:
        radius: in um. Defaults to cross_section_radius.
        angle: total angle of the curve.
        p: Proportion of the curve that is an Euler curve.
        with_arc_floorplan: If False: `radius` is the minimum radius of curvature
          If True: The curve scales such that the endpoints match a bend_circular
          with parameters `radius` and `angle`.
        npoints: Number of points used per 360 degrees.
        layer: layer to use. Defaults to cross_section.layer.
        width: width to use. Defaults to cross_section.width.
        cross_section: specification (CrossSection, string, CrossSectionFactory dict).
        allow_min_radius_violation: if True allows radius to be smaller than cross_section radius.
        all_angle: if True, the bend is drawn with a single euler curve.

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
        Name="taper_rsoa"
) -> Component:
    c = gf.Component(Name)
    layers = layers or [layer]
    ebend = c << gf.components.bend_euler(angle=-AngleRsoa, width=WidthWg, radius=RadiusBend, layer=layer)
    rtaper = c << gf.components.taper(length=LengthRsoa, width1=WidthWg, width2=WidthRsoa, layer=layer)
    rstr = c << gf.components.straight(length=LengthAdd, width=WidthRsoa, layer=layer)
    rtaper.connect(port="o1", other=ebend.ports["o2"])
    rstr.connect(port="o1", other=rtaper.ports["o2"])
    c.add_port("o1", port=rstr.ports["o2"])
    c.add_port("o2", port=ebend.ports["o1"])
    return c


# %% OffsetRamp
@gf.cell()
def OffsetRamp(
        length: float = 10.0,
        width1: float = 5.0,
        width2: float | None = 8.0,
        offset: float = 0,
        layer: LayerSpec = LAYER.WG,
) -> Component:
    """Return a offset ramp component.

    Based on phidl.

    Args:
        length: Length of the ramp section.
        width1: Width of the start of the ramp section.
        width2: Width of the end of the ramp section (defaults to width1).
        offset: Offset of the output center to input center
        layer: Specific layer to put polygon geometry on.
    """
    if width2 is None:
        width2 = width1
    xpts = [(0,width1/2), (length,width2/2+offset), (length,-width2 / 2 + offset),(0,-width1/2)]
    c = Component()
    c.add_polygon(xpts, layer=layer)
    c.add_port(
        name="o1", center=[0, width1 / 2], width=width1, orientation=180, layer=layer
    )
    c.add_port(
        name="o2",
        center=[length, width1 / 2 + offset],
        width=width2,
        orientation=0,
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
    c = gf.Component(Name)
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
    """Returns an euler bend that adiabatically transitions from  curved to straight

    `radius` is the minimum radius of curvature of the bend.
    However, if `use_eff` is set to True, `radius` corresponds to the effective
    radius of curvature (making the curve a drop-in replacement for an arc).
    If p < 1.0, will create a "partial euler" curve as described in Vogelbacher et. al.
    https://dx.doi.org/10.1364/oe.27.031394

    Args:
        radius: minimum radius of curvature.
        angle: total angle of the curve.
        p: Proportion of the curve that is an Euler curve.
        use_eff: If False: `radius` is the minimum radius of curvature of the bend. \
                If True: The curve will be scaled such that the endpoints match an \
                arc with parameters `radius` and `angle`.
        npoints: Number of points used per 360 degrees.

    .. plot::
        p = euler_Bend_Half(radius=10, angle=45, p=1, use_eff=True, npoints=720)
        p.plot()

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
    """Euler bend with curvature transitioning from radius1 to radius2.

    Args:
        radius1: Starting radius of curvature.
        radius2: Ending radius of curvature.
        angle: Total angle of the bend (degrees).
        p: Proportion of the curve using the Euler transition (0 ≤ p ≤ 1).
        use_eff: If True, scale to match effective radius of a circular arc.
        npoints: Number of points along the curve.

    Returns:
        Path: The generated Euler bend path.
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
    logo = gf.Component("logo")
    qrcode = logo << gf.c.qrcode(data='https://photonics.pku.edu.cn/', psize=Size, layer=lglayer)
    return logo


# %% Component shift
def shift_component(component: Component, dx: float, dy: float) -> Component:
    """Shifts all elements in the component by (dx, dy).

    Args:
        component: The component to shift.
        dx: The shift in the x-direction.
        dy: The shift in the y-direction.

    Returns:
        A new component with all elements shifted.
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
    if FLayer is None:
        FLayer = OLayer
    CompFinal = gf.Component(CompOriginal.name + "Layer=" + str(OLayer))
    pols = CompOriginal.get_polygons(by_spec=OLayer)
    for pol in pols:
        CompFinal.add_polygon(pol, layer=FLayer)
    for port in CompOriginal.ports:
        CompFinal.add_port(name=port, port=CompOriginal.ports[port])
    return CompFinal

# %% TotalComponent
r_euler_false = 500
r_euler_true = 500 * 1.5
