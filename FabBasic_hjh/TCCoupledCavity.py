from .BasicDefine import *
from .Boomerang import *
from .MultiRing import *
from .MultiRaceTrack import *
from .SnapMerge import snap_all_polygons_iteratively


# %% defult in out taper
@gf.cell
def create_taper(width1, width2, lengthleft=20, lengthtaper=200, lengthright=20, layer: LayerSpec = LAYER.WG):
    taper = gf.Component("taper")
    taper_te = taper << gf.c.taper(width1=width1, width2=width2, length=lengthtaper, layer=layer)
    taper_straight1 = taper << GfCStraight(width=width1, length=lengthleft, layer=layer)
    taper_straight2 = taper << GfCStraight(width=width2, length=lengthright, layer=layer)
    taper_te.connect("o1", other=taper_straight1.ports["o2"])
    taper_straight2.connect("o1", taper_te.ports["o2"])
    taper.add_port(name="o1", port=taper_straight1.ports["o1"])
    taper.add_port(name="o2", port=taper_straight2.ports["o2"])
    return taper


taper_in = create_taper("taper_in", width1=0.3, width2=1, layer=LAYER.WG)
taper_out = create_taper("taper_out", width1=1, width2=0.2, layer=LAYER.WG)


# TCRingBoomerangT1: Total singleBoomerang Ring
@gf.cell
def TCRingBoomerangT1(
        r_ring: float = 120,
        r_euler_min: float = 100,
        r_euler_boom: float = 100,
        width_ringin: float = 1,
        width_ringout: float = 2,
        width_straight: float = 3,
        width_heat: float = 5,
        width_route: float = 20,
        width_single: float = 1,
        width_via: float = 0.5,
        length_bridge1: float = 100,
        length_bridge2: float = 100,
        length_couple: float = 100,
        length_taper: float = 150,
        length_total: float = 10000,
        length_th_horizontal: float = 10,
        length_th_vertical: float = 10,
        pos_ring: float = 700,
        gap_rr: float = 1,
        gap_rb: float = 2,
        gap_heat: float = 1,
        delta_heat: float = 20,
        spacing: float = 1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        is_heat: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        type_heater: str = "default",  # 控制加热器类型
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个集成了单个 `RingBoomerang` 谐振器的完整组件。
    该组件包含标准的输入/输出锥形波导（`tin`, `tout`），并将它们连接到
    `RingBoomerang` 单元的Input/Through及Add/Drop端口。
    提供了复杂的路由以将所有端口引出到芯片边缘或测试焊盘。

    参数:
        (大部分参数用于配置内部的 `RingBoomerang` 单元及其引出臂的几何形状)
        r_ring, r_euler_min, r_euler_boom: 各种弯曲半径 (µm)。
        width_ringin, width_ringout, width_straight, width_heat, width_route, width_single, width_via: 各种宽度 (µm)。
        length_bridge1, length_bridge2, length_couple, length_taper, length_total, length_th_horizontal, length_th_vertical: 各种长度 (µm)。
        pos_ring: 核心 `RingBoomerang` 组件的大致X轴放置位置 (µm)。
        gap_rr, gap_rb, gap_heat: 各种间隙 (µm)。
        delta_heat, spacing: 加热器相关几何参数 (µm)。
        tin (ComponentSpec): 输入锥形波导的组件规格。默认为全局定义的 `taper_in`。
        tout (ComponentSpec): 输出锥形波导的组件规格。默认为全局定义的 `taper_out`。
        is_heat (bool): 是否为内部的 `RingBoomerang` 添加加热器。
        oplayer, heatlayer, routelayer, vialayer (LayerSpec): GDS图层定义。
        type_heater (str): 传递给 `RingBoomerang` 的加热器类型。

    返回:
        Component: 生成的集成单Boomerang环组件。

    端口:
        input: 组件的总光学输入端口。
        through: 组件的总光学直通端口。
        add: (如果RingBoomerang有Add口并被引出) 组件的增加端口。
        drop: (如果RingBoomerang有Drop口并被引出) 组件的下载端口。
        (以及从 `RingBoomerang` 继承的加热器端口和可能的其他参考端口)
    """
    sr = gf.Component()
    ring = gf.Component("Ring")
    ring0 = ring << RingBoomerang(
        WidthRingIn=width_ringin, WidthRingOut=width_ringout, WidthHeat=width_heat, WidthStraight=width_straight,
        WidthRoute=width_route, WidthVia=width_via,
        LengthTaper=length_taper, LengthBridge2=length_bridge2, LengthBridge1=length_bridge1,
        LengthCouple=length_couple,
        GapRR=gap_rr, GapRB=gap_rb, GapHeat=gap_heat, DeltaHeat=delta_heat, Spacing=spacing,
        RadiusRing=r_ring, RadiusEuler=r_euler_boom, IsHeatIn=is_heat, IsHeatOut=is_heat,
        oplayer=oplayer, heatlayer=heatlayer, TypeHeater=type_heater
    )
    # input through
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring0.ports["Input"])
    taper_s2n2 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_thr1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer, angle=-90,
                                        with_arc_floorplan=False)
    bend_thr2 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer, angle=90,
                                        with_arc_floorplan=False)
    str_th_horizontal = ring << GfCStraight(width=width_straight, length=length_th_horizontal, layer=oplayer)
    str_th_vertical = ring << GfCStraight(width=width_single, length=length_th_vertical, layer=oplayer)
    str_th_horizontal.connect("o1", ring0.ports["Through"])
    bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
    taper_s2n2.connect("o1", other=bend_thr1.ports["o2"])
    str_th_vertical.connect("o1", other=taper_s2n2.ports["o2"])
    bend_thr2.connect("o1", other=str_th_vertical.ports["o2"])
    ring.add_port("o1", port=taper_s2n1.ports["o1"])
    ring.add_port("o2", port=bend_thr2.ports["o2"])
    # add drop
    taper_s2n3 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    taper_s2n3.connect("o2", ring0.ports["Add"])
    taper_s2n4 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_dp1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer, angle=90,
                                       with_arc_floorplan=False)
    bend_dp1.connect('o1', ring0.ports["Drop"])
    taper_s2n4.connect('o1', bend_dp1.ports['o2'])
    ring.add_port('o3', port=taper_s2n3.ports['o1'])
    ring.add_port('o4', port=taper_s2n4.ports['o2'])
    # add port
    ring.add_port("RingInput", port=ring0.ports["Input"])
    for port in ring0.ports:
        if "Heat" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Add" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Drop" in port:
            ring.add_port(port, port=ring0.ports[port])
    comp_Ring = sr << ring

    # input
    tinring = sr << tin
    comp_Ring.connect("o1", other=tinring.ports["o2"], allow_width_mismatch=True, mirror=True)
    comp_Ring.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])

    # add
    tadring = sr << tin
    tadring.movey(tinring.ports['o1'].center[1] - tadring.ports['o1'].center[1] + 30)
    tadring.movex(- tadring.ports['o1'].center[0])
    # drop
    tdpring = sr << tout
    tdpring.movey(comp_Ring.ports['o4'].center[1] - tdpring.ports['o1'].center[1])
    tdpring.movex(length_total - tdpring.ports['o2'].center[0])
    # through
    toutring = sr << tout
    delta = toutring.ports["o2"].center - toutring.ports["o1"].center
    toutring.connect("o1", other=comp_Ring.ports["o2"])
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("through", port=toutring.ports["o2"])
    # route
    str_tout2r = gf.routing.get_bundle([toutring.ports["o1"], comp_Ring.ports["o1"], tdpring.ports['o1']],
                                       [comp_Ring.ports["o2"], tinring.ports["o2"], comp_Ring.ports['o4']],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    str_tout2r = gf.routing.get_bundle([comp_Ring.ports["o3"]], [tadring.ports["o2"]],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    # add port

    for port in comp_Ring.ports:
        if "Heat" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Add" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Drop" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
    add_labels_to_ports(sr)
    return sr


# TCRingDouBoomerangT1: Total singleBoomerang Ring
@gf.cell
def TCRingDouBoomerangT1(
        r_ring: float = 120,
        r_euler_min: float = 100,
        r_euler_boom: float = 100,
        width_ringin: float = 1,
        width_ringout: float = 2,
        width_straight: float = 3,
        width_heat: float = 5,
        width_route: float = 20,
        width_single: float = 1,
        width_via: float = 0.5,
        length_bridge1: float = 100,
        length_bridge2: float = 100,
        length_couple: float = 10,
        length_taper: float = 150,
        length_total: float = 10000,
        length_th_horizontal: float = 10,
        length_th_vertical: float = 780,
        pos_ring: float = 700,
        gap_rr: float = 1,
        gap_rb: float = 2,
        gap_heat: float = 1,
        delta_heat: float = 20,
        delta_lb2: float = 20,
        spacing: float = 1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        is_heat: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        type_heater: str = "default",  # 控制加热器类型
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个集成了 `RingDouBoomerang` 双回旋镖谐振器的完整组件。
    包含标准的输入/输出锥形波导，并将它们连接到双回旋镖单元的
    Input/Through及Add/Drop端口，具有复杂的引出臂路由。

    参数:
        (大部分参数与 TCRingBoomerangT1 类似，用于配置内部的 `RingDouBoomerang` 单元
         及其引出臂的几何形状)
        delta_lb2 (float): `RingDouBoomerang` 内部两个Boomerang单元的 `LengthBridge2` 差异 (µm)。
        length_th_vertical (float): Through端口引出臂的垂直段长度，默认值较大 (780 µm)。

    返回:
        Component: 生成的集成双Boomerang环组件。

    端口: (与 TCRingBoomerangT1 类似，但基于双Boomerang核心)
        input, through, add, drop
        (以及从 `RingDouBoomerang` 继承的加热器和参考端口，如 R1Heat..., R2Heat...)

    信息 (Info):
        R1length, R2length: (如果RingDouBoomerang提供) 两个Boomerang单元的路径长度。
    """
    sr = gf.Component()
    ring = gf.Component("Ring")
    ring0 = ring << RingDouBoomerang(
        WidthRingIn=width_ringin, WidthRingOut=width_ringout, WidthHeat=width_heat, WidthStraight=width_straight,
        WidthRoute=width_route, WidthVia=width_via,
        LengthTaper=length_taper, LengthBridge2=length_bridge2, LengthBridge1=length_bridge1,
        LengthCouple=length_couple,
        GapRR=gap_rr, GapRB=gap_rb, GapHeat=gap_heat, DeltaHeat=delta_heat, Spacing=spacing,
        RadiusRing=r_ring, RadiusEuler=r_euler_boom, DeltaLB2=delta_lb2,
        oplayer=oplayer, heatlayer=heatlayer, TypeHeater=type_heater
    )
    # input
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring0.ports["Input"])
    # through
    taper_s2n2 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_thr1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer, angle=90,
                                        with_arc_floorplan=False)
    str_th_horizontal = ring << GfCStraight(width=width_straight,
                                            length=length_th_horizontal + r_euler_boom * 2 + length_bridge2,
                                            layer=oplayer)
    str_th_horizontal.connect("o1", ring0.ports["Through"])
    bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
    taper_s2n2.connect("o1", other=bend_thr1.ports["o2"])
    ring.add_port("o1", port=taper_s2n1.ports["o1"])
    ring.add_port("o2", port=taper_s2n2.ports["o2"])
    # add drop
    str_ad = ring << GfCStraight(width=width_straight, length=length_bridge2, layer=oplayer)
    bend_ad = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer, angle=-90,
                                      with_arc_floorplan=False)
    taper_s2n3 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    str_ad.connect('o2', ring0.ports["Add"])
    bend_ad.connect('o2', str_ad.ports["o1"])
    taper_s2n3.connect("o2", bend_ad.ports['o1'])
    taper_s2n4 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_dp1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer, angle=-90,
                                       with_arc_floorplan=False)
    bend_dp1.connect('o1', ring0.ports["Drop"])
    taper_s2n4.connect('o1', bend_dp1.ports['o2'])
    ring.add_port('o3', port=taper_s2n3.ports['o1'])
    ring.add_port('o4', port=taper_s2n4.ports['o2'])
    # add port
    ring.add_port("RingInput", port=ring0.ports["Input"])
    for port in ring0.ports:
        if "Heat" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Add" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Drop" in port:
            ring.add_port(port, port=ring0.ports[port])
    comp_Ring = sr << ring

    # input
    tinring = sr << tin
    comp_Ring.connect("o1", other=tinring.ports["o2"], allow_width_mismatch=True, mirror=True)
    comp_Ring.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])

    # add
    tadring = sr << tin
    tadring.movey(tinring.ports['o1'].center[1] - tadring.ports['o1'].center[1] - 30)
    tadring.movex(- tadring.ports['o1'].center[0])
    sr.add_port("add", port=tadring.ports['o1'])
    # drop
    tdpring = sr << tout
    tdpring.movey(comp_Ring.ports['o4'].center[1] - tdpring.ports['o1'].center[1])
    tdpring.movex(length_total - tdpring.ports['o2'].center[0])
    sr.add_port("drop", port=tdpring.ports['o2'])
    # through
    toutring = sr << tout
    toutring.movey(tdpring.ports['o1'].center[1] - toutring.ports['o1'].center[1] + 30)
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("through", port=toutring.ports["o2"])
    # route
    str_tout2r = gf.routing.get_bundle([comp_Ring.ports["o1"], tdpring.ports['o1']],
                                       [tinring.ports["o2"], comp_Ring.ports['o4']],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    str_tout2r = gf.routing.get_bundle([toutring.ports["o1"]], [comp_Ring.ports["o2"]],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    str_tout2r = gf.routing.get_bundle([tadring.ports["o2"]], [comp_Ring.ports["o3"]],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    # add port

    for port in comp_Ring.ports:
        if "Heat" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Add" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Drop" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
    add_labels_to_ports(sr)
    sr.info['R1length'] = ring0.info['R1length']
    sr.info['R2length'] = ring0.info['R2length']
    return sr


# TCRingTriBoomerangT1: Total singleBoomerang Ring
@gf.cell
def TCRingTriBoomerangT1(
        r_ring: float = 120,
        r_euler_min: float = 100,
        r_euler_boom: float = 100,
        width_ringin: float = 1,
        width_ringout: float = 2,
        width_straight: float = 3,
        width_heat: float = 5,
        width_route: float = 20,
        width_single: float = 1,
        width_via: float = 0.5,
        length_bridge1: float = 100,
        length_bridge2: float = 100,
        length_couple: float = 10,
        length_taper: float = 200,
        length_total: float = 4000,
        length_th_horizontal: float = 10,
        length_th_vertical: float = 780,
        pos_ring: float = 1100,
        gap_rr: float = 1,
        gap_rb: float = 2,
        gap_heat: float = 1,
        delta_heat: float = 20,
        delta_lb2: float = 20,
        spacing: float = 1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        type_heater: str = "default",  # 控制加热器类型
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个集成了 `RingTriBoomerang` 三回旋镖谐振器的完整组件。
    包含标准的输入/输出锥形波导，并将它们连接到三回旋镖单元的
    Input/Through及Add/Drop端口，具有复杂的引出臂路由。

    参数:
        (大部分参数与 TCRingDouBoomerangT1 类似，用于配置内部的 `RingTriBoomerang` 单元
         及其引出臂的几何形状)
        length_taper (float): 锥形波导长度，默认为200µm。
        length_total (float): 组件目标总长度，默认为4000µm。
        pos_ring (float): 核心 `RingTriBoomerang` 组件的大致X轴放置位置，默认为1100µm。

    返回:
        Component: 生成的集成三Boomerang环组件。

    端口: (与 TCRingDouBoomerangT1 类似，但基于三Boomerang核心)
        input, through, add, drop
        (以及从 `RingTriBoomerang` 继承的加热器和参考端口，如 R1Heat..., R2Heat..., R3Heat...)

    信息 (Info):
        R1length, R2length, R3length: (如果RingTriBoomerang提供) 三个Boomerang单元的路径长度。
    """
    sr = gf.Component()
    ring = gf.Component("Ring")
    ring0 = ring << RingTriBoomerang(
        WidthRingIn=width_ringin, WidthRingOut=width_ringout, WidthHeat=width_heat, WidthStraight=width_straight,
        WidthRoute=width_route, WidthVia=width_via,
        LengthTaper=length_taper, LengthBridge2=length_bridge2, LengthBridge1=length_bridge1,
        LengthCouple=length_couple,
        GapRR=gap_rr, GapRB=gap_rb, GapHeat=gap_heat, DeltaHeat=delta_heat, Spacing=spacing,
        RadiusRing=r_ring, RadiusEuler=r_euler_boom, DeltaLB2=delta_lb2,
        oplayer=oplayer, heatlayer=heatlayer, TypeHeater=type_heater
    )
    # input
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring0.ports["Input"])
    # through
    taper_s2n2 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_thr1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer, angle=-90,
                                        with_arc_floorplan=False)
    str_th_horizontal = ring << GfCStraight(width=width_straight,
                                            length=length_th_horizontal + r_euler_boom * 2 + length_bridge2,
                                            layer=oplayer)
    str_th_vertical = ring << GfCStraight(width=width_single, length=length_th_vertical, layer=oplayer)
    str_th_horizontal.connect("o1", ring0.ports["Through"])
    bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
    taper_s2n2.connect("o1", other=bend_thr1.ports["o2"])
    str_th_vertical.connect("o1", other=taper_s2n2.ports["o2"])
    ring.add_port("o1", port=taper_s2n1.ports["o1"])
    ring.add_port("o2", port=str_th_vertical.ports["o2"])
    # add
    taper_s2n3 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    taper_s2n3.connect("o2", ring0.ports["Add"])
    bend_ad = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer, angle=90,
                                      with_arc_floorplan=False)
    bend_ad.connect('o2', taper_s2n3.ports["o1"])
    ring.add_port('o3', port=bend_ad.ports['o1'])
    # drop
    str_dr = ring << GfCStraight(width=width_straight, length=length_bridge2 + 2 * r_euler_boom, layer=oplayer)
    taper_s2n4 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_dp1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer, angle=90,
                                       with_arc_floorplan=False)
    str_dr.connect('o1', ring0.ports["Drop"])
    bend_dp1.connect('o1', str_dr.ports['o2'])
    taper_s2n4.connect('o1', bend_dp1.ports['o2'])
    ring.add_port('o4', port=taper_s2n4.ports['o2'])
    # add port
    ring.add_port("RingInput", port=ring0.ports["Input"])
    for port in ring0.ports:
        if "Heat" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Add" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Drop" in port:
            ring.add_port(port, port=ring0.ports[port])
    comp_Ring = sr << ring

    # port edge io
    ## input
    tinring = sr << tin
    comp_Ring.connect("o3", other=tinring.ports["o2"], allow_width_mismatch=True, mirror=True)
    comp_Ring.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])

    ## add
    tadring = sr << tin
    tadring.movey(tinring.ports['o1'].center[1] - tadring.ports['o1'].center[1] - 30)
    tadring.movex(- tadring.ports['o1'].center[0])
    sr.add_port("add", port=tadring.ports['o1'])
    ## drop
    tdpring = sr << tout
    tdpring.movey(comp_Ring.ports['o2'].center[1] - tdpring.ports['o1'].center[1])
    tdpring.movex(length_total - tdpring.ports['o2'].center[0])
    sr.add_port("drop", port=tdpring.ports['o2'])
    ## through
    toutring = sr << tout
    toutring.movey(tdpring.ports['o1'].center[1] - toutring.ports['o1'].center[1] + 30)
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("through", port=toutring.ports["o2"])
    # # route
    str_tout2r = gf.routing.get_bundle([toutring.ports["o1"], comp_Ring.ports["o3"], tdpring.ports['o1']],
                                       [comp_Ring.ports["o4"], tinring.ports["o2"], comp_Ring.ports['o2']],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    str_tout2r = gf.routing.get_bundle([tadring.ports["o2"]], [comp_Ring.ports["o1"]],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    # add port
    for port in comp_Ring.ports:
        if "Heat" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Add" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Drop" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
    add_labels_to_ports(sr)
    sr.info['R1length'] = ring0.info['R1length']
    sr.info['R2length'] = ring0.info['R2length']
    sr.info['R3length'] = ring0.info['R3length']
    return sr


# TCRingT1: TCRing use RingPulleyT1
@gf.cell
def TCCoupleDouRingT1(
        r_ring1: float = 120,
        width_ring1: float = 1,
        width_near1: float = 2,
        width_heat1: float = 5,
        gap_rc1: float = 1,
        angle_rc1: float = 20,
        type_heater1: str = "default",  # 控制加热器类型
        gap_heat1: float = 1,
        delta_heat1: float = 1,
        r_ring2: float = None,
        width_ring2: float = None,
        width_near2: float = None,
        width_heat2: float = None,
        length_near2: float = 130,
        gap_rc2: float = 1,
        type_heater2: str = "default",  # 控制加热器类型
        gap_heat2: float = 0,
        delta_heat2: float = 0,
        gap_rr: float = 1,
        angle_rr: float = 30,
        width_single: float = 1,
        r_euler_min: float = 100,
        length_taper: float = 150,
        length_total: float = 10000,
        length_th_horizontal: float = 10,
        length_th_vertical: float = 10,
        length_ad_horizontal: float = 10,
        length_ad_vertical: float = 10,
        pos_ring: float = 500,
        tin: Component = taper_in,
        tout: Component = taper_out,
        is_heat: bool = True,
        is_ad: bool = False,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        position_taper: str = "before_bend",  # 控制锥形波导的位置

) -> Component:
    """
    创建一个集成了 `CoupleRingDRT1`（耦合双普通环，T1型）谐振器的完整组件。
    包含标准的输入/输出锥形波导，并将它们连接到核心双环单元的端口。
    `position_taper` 参数允许灵活配置Through端口引出臂上锥形波导的位置。

    参数:
        (大部分参数用于配置内部的 `CoupleRingDRT1` 单元及其引出臂的几何形状)
        r_ring1, width_ring1, ... delta_heat1: 第一个环及其耦合的参数。
        r_ring2, width_ring2, ... delta_heat2: 第二个环及其耦合的参数 (如果为None，则通常与第一个环对称或相关)。
        gap_rr, angle_rr: 两个环之间的直接耦合参数。
        width_single, r_euler_min, length_taper, ...: IO、路由和布局参数。
        position_taper (str): 控制Through端口引出臂上锥形波导的位置。可选值:
                              "before_bend" (弯曲前), "after_bend" (弯曲后),
                              "between_bend" (两段弯曲之间), "no_bend" (无额外弯曲，直接引出)。
        is_ad (bool): 此总组件是否将 `CoupleRingDRT1` 的Add/Drop端口作为外部端口引出。
                      `CoupleRingDRT1` 本身可能是四端口的。

    返回:
        Component: 生成的集成耦合双环组件。

    端口:
        input: 组件的总光学输入。
        output: 组件的总光学输出 (通常是Through端口)。
        add: (如果is_ad=True) 组件的增加端口。
        drop: (如果is_ad=True) 组件的下载端口。
        Ring1C, Ring2C: 两个环中心的参考端口。
        (以及从 `CoupleRingDRT1` 继承的加热器端口)
    """
    sr = gf.Component()
    ring = gf.Component("Ring")
    if width_ring2 is None:
        width_ring2 = width_ring1
    if width_heat2 is None:
        width_heat2 = width_heat1
    if r_ring2 is None:
        r_ring2 = r_ring1
    if width_near2 is None:
        width_near2 = width_near1
    S_single = gf.Section(width=width_single, layer=oplayer, port_names=['o1', 'o2'])
    X_single = gf.CrossSection(sections=[S_single])
    ring0 = ring << CoupleRingDRT1(
        RadiusRing1=r_ring1, WidthRing1=width_ring1, WidthNear1=width_near1, WidthHeat1=width_heat1, GapRB1=gap_rc1,
        DeltaHeat1=delta_heat1,
        AngleCouple1=angle_rc1,
        RadiusRing2=r_ring2, WidthRing2=width_ring2, WidthNear2=width_near2, WidthHeat2=width_heat2, GapRB2=gap_rc2,
        DeltaHeat2=delta_heat2, LengthNear2=length_near2,
        GapRR=gap_rr, AngleR12=angle_rr,
        TypeHeaterR1=type_heater1, TypeHeaterR2=type_heater2, GapHeat1=gap_heat1,
        IsHeat=is_heat, oplayer=oplayer, heatlayer=heatlayer, DirectionsHeater=['down', 'down']
    )
    # input through
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_near1, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring0.ports["Input"])
    taper_s2n2 = ring << gf.c.taper(width1=width_near1, width2=width_single, length=length_taper, layer=oplayer)
    ## 根据 position_taper 参数调整锥形波导的位置（input through）
    if position_taper == "before_bend":
        bend_thr1 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer, angle=90,
                                            with_arc_floorplan=False)
        bend_thr2 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer, angle=-90,
                                            with_arc_floorplan=False)
        str_th_horizontal = ring << GfCStraight(width=width_single, length=length_th_horizontal, layer=oplayer)
        str_th_vertical = ring << GfCStraight(width=width_single, length=length_th_vertical, layer=oplayer)
        taper_s2n2.connect("o1", ring0.ports["Through"])
        str_th_horizontal.connect("o1", other=taper_s2n2.ports["o2"])
        bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
        str_th_vertical.connect("o1", other=bend_thr1.ports["o2"])
        bend_thr2.connect("o1", other=str_th_vertical.ports["o2"])
        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=bend_thr2.ports["o2"])
    elif position_taper == "after_bend":
        bend_thr1 = ring << gf.c.bend_euler(width=width_near1, radius=r_euler_min, layer=oplayer, angle=90,
                                            with_arc_floorplan=False)
        bend_thr2 = ring << gf.c.bend_euler(width=width_near1, radius=r_euler_min, layer=oplayer, angle=-90,
                                            with_arc_floorplan=False)
        str_th_horizontal = ring << GfCStraight(width=width_near1, length=length_th_horizontal, layer=oplayer)
        str_th_vertical = ring << GfCStraight(width=width_near1, length=length_th_vertical, layer=oplayer)

        str_th_horizontal.connect("o1", ring0.ports["Through"])
        bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
        str_th_vertical.connect("o1", other=bend_thr1.ports["o2"])
        bend_thr2.connect("o1", other=str_th_vertical.ports["o2"])
        taper_s2n2.connect("o1", other=bend_thr2.ports["o2"])

        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=taper_s2n2.ports["o2"])
    elif position_taper == "between_bend":
        bend_thr1 = ring << gf.c.bend_euler(width=width_near1, radius=r_euler_min, layer=oplayer, angle=90,
                                            with_arc_floorplan=False)
        bend_thr2 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer, angle=-90,
                                            with_arc_floorplan=False)
        str_th_horizontal = ring << GfCStraight(width=width_near1, length=length_th_horizontal, layer=oplayer)
        str_th_vertical = ring << GfCStraight(width=width_single, length=length_th_vertical, layer=oplayer)
        str_th_horizontal.connect("o1", ring0.ports["Through"])
        bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
        taper_s2n2.connect("o1", other=bend_thr1.ports["o2"])
        str_th_vertical.connect("o1", other=taper_s2n2.ports["o2"])
        bend_thr2.connect("o1", other=str_th_vertical.ports["o2"])
        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=bend_thr2.ports["o2"])
    elif position_taper == "no_bend":
        taper_s2n2.connect("o1", other=ring0.ports["Through"])
        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=taper_s2n2.ports["o2"])
    else:
        raise ValueError("position_taper 必须是 'before_bend' 或 'after_bend' 或 'between_bend' 或 'no_bend'")
    # add drop
    taper_s2n3 = ring << gf.c.taper(width1=width_single, width2=width_near2, length=length_taper, layer=oplayer)
    taper_s2n4 = ring << gf.c.taper(width1=width_near2, width2=width_single, length=length_taper, layer=oplayer)
    taper_s2n4.connect("o1", ring0.ports["Add"])
    ## add drop bend out
    bend_ad1 = ring << gf.c.bend_euler(width=width_near2, radius=r_euler_min, layer=oplayer, angle=-90,
                                       with_arc_floorplan=False)
    bend_ad2 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer, angle=90,
                                       with_arc_floorplan=False)
    str_ad = ring << GfCStraight(width=width_single, length=length_ad_vertical, layer=oplayer)
    str_ad0 = ring << GfCStraight(width=width_near2, length=length_ad_horizontal, layer=oplayer)
    str_ad0.connect("o2", other=ring0.ports["Drop"])
    bend_ad1.connect("o2", other=str_ad0.ports["o1"])
    taper_s2n3.connect("o2", other=bend_ad1.ports["o1"])
    str_ad.connect("o2", other=taper_s2n3.ports["o1"])
    bend_ad2.connect("o2", other=str_ad.ports["o1"])
    ring.add_port("o3", port=taper_s2n4.ports["o2"])
    ring.add_port("o4", port=bend_ad2.ports["o1"])
    ring.add_port("RingInput", port=ring0.ports["Input"])
    ring.add_port("Ring1C", port=ring0.ports["Ring1C"])
    ring.add_port("Ring2C", port=ring0.ports["Ring2C"])
    for port in ring0.ports:
        if "Heat" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Add" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Drop" in port:
            ring.add_port(port, port=ring0.ports[port])
    # add_labels_to_ports(ring,(412,8))
    CCRing = sr << ring

    ## input
    tinring = sr << tin
    CCRing.connect("o1", other=tinring.ports["o2"], allow_width_mismatch=True, mirror=True)
    CCRing.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])
    ## add
    tadring = sr << tin
    tadring.connect('o2', CCRing.ports['o4'])
    tadring.movex(tinring.ports['o1'].center[0] - tadring.ports['o1'].center[0])
    sr.add_port("add", port=tadring.ports["o1"])
    ## output
    toutring = sr << tout
    toutring.connect("o1", other=CCRing.ports["o2"])
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("output", port=toutring.ports["o2"])
    ## drop
    tdpring = sr << tout
    tdpring.movey(-tdpring.ports['o1'].center[1] + CCRing.ports["o3"].center[1])
    tdpring.movex(length_total - tdpring.ports["o2"].center[0])
    bend_s_dp = sr << gf.c.bend_s(cross_section=X_single, size=[10, 0])
    bend_s_dp.connect("o1", other=CCRing.ports["o3"])
    sr.add_port("drop", port=tdpring.ports["o2"])
    ## route
    str_tout2r = gf.routing.get_bundle(
        [toutring.ports["o1"], CCRing.ports["o1"], tdpring.ports['o1'], CCRing.ports["o4"]],
        [CCRing.ports["o2"], tinring.ports["o2"], bend_s_dp.ports["o2"], tadring.ports['o2']],
        layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    sr.add_port("Ring1C", port=CCRing.ports["Ring1C"])
    sr.add_port("Ring2C", port=CCRing.ports["Ring2C"])

    for port in CCRing.ports:
        if "Heat" in port:
            sr.add_port(port, port=CCRing.ports[port])
        if "Add" in port:
            sr.add_port(port, port=CCRing.ports[port])
        if "Drop" in port:
            sr.add_port(port, port=CCRing.ports[port])
    # add_labels_to_ports(ring, (612, 8))
    return sr
# TCCoupleDouRaceTrackST1: Total component Coupled racetrack cavity use Coupled RaceTrack
@gf.cell
def TCCoupleDouRaceTrackT1(
        r_ring: float = 120,
        width_ring: float = 1,
        width_heat: float = 5,
        gap_rc: float = 1,
        angle_rc: float = 20,
        type_heater: str = "default",  # 控制加热器类型
        gap_heat: float = 1,
        delta_heat: float = 1,
        gap_rr: float = 1,
        length_rr: float = 30,
        width_single: float = 1,
        r_euler_min: float = 100,
        length_taper: float = 150,
        length_total: float = 10000,
        length_th_horizontal: float = 10,
        length_th_vertical: float = 10,
        length_ad_horizontal: float = 10,
        length_ad_vertical: float = 10,
        pos_ring: float = 500,
        tin: Component = taper_in,
        tout: Component = taper_out,
        is_heat: bool = True,
        is_ad: bool = False,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        position_taper: str = ["before_bend","before_bend"],  # 控制锥形波导的位置
        direction_io: str = [""]
) -> Component:
    """
    创建一个集成了 `CoupleDouRaceTrack`（耦合双跑道环）谐振器的完整组件 (ST1型配置)。
    包含标准的输入/输出锥形波导，并将它们连接到核心双跑道环单元的对应端口。
    通过 `position_taper` 控制两个Through端口引出臂上锥形波导的位置。

    参数:
        (大部分参数用于配置内部的 `CoupleDouRaceTrack` 单元及其引出臂)
        r_ring, width_ring, ... delta_run, length_run: 跑道环几何参数。
        type_couple: 跑道环与外部总线的耦合类型 ('S'或'P')。
        position_taper (list[str]): 长度为2的列表，分别控制R1Through和R2Through引出臂上
                                     锥形波导的位置 ("before_bend", "after_bend", etc.)。

    返回:
        Component: 生成的集成耦合双跑道环组件 (ST1型)。

    端口:
        input: (连接到R1Input) 总输入。
        output: (连接到R1Through) 总直通输出。
        add: (连接到R2Input) 第二个环的输入，作为Add。
        drop: (连接到R2Through) 第二个环的直通，作为Drop。
        (以及从 `CoupleDouRaceTrack` 继承的加热器端口)
    """
    sr = gf.Component()
    ring = gf.Component("Ring")
    S_single = gf.Section(width=width_single, layer=oplayer, port_names=['o1', 'o2'])
    X_single = gf.CrossSection(sections=[S_single])
    ring0 = ring << CoupleDouRaceTrack(
        RadiusRing=r_ring, WidthRing=width_ring,
        GapCoupleOut=gap_rc,GapCoupleIn=gap_rr,
        DeltaHeat=delta_heat,WidthHeat=width_heat, GapHeat=gap_heat,
        TypeHeater=type_heater,
        IsHeat=is_heat, oplayer=oplayer, heatlayer=heatlayer, DirectionsHeater=['down', 'down']
    )
    ring0.mirror_y(ring0.ports["R1Input"].center[1])
    # input through
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_ring, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring0.ports["R1Input"])
    taper_s2n2 = ring << gf.c.taper(width1=width_ring, width2=width_single, length=length_taper, layer=oplayer)
    ## 根据 position_taper 参数调整锥形波导的位置（input through）
    if position_taper[0] == "before_bend":
        bend_thr1 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer, angle=90,
                                            with_arc_floorplan=False)
        bend_thr2 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer, angle=-90,
                                            with_arc_floorplan=False)
        str_th_horizontal = ring << GfCStraight(width=width_single, length=length_th_horizontal, layer=oplayer)
        str_th_vertical = ring << GfCStraight(width=width_single, length=length_th_vertical, layer=oplayer)
        taper_s2n2.connect("o1", ring0.ports["R1Through"])
        str_th_horizontal.connect("o1", other=taper_s2n2.ports["o2"])
        bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
        str_th_vertical.connect("o1", other=bend_thr1.ports["o2"])
        bend_thr2.connect("o1", other=str_th_vertical.ports["o2"])
        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=bend_thr2.ports["o2"])
    elif position_taper[0] == "after_bend":
        bend_thr1 = ring << gf.c.bend_euler(width=width_ring, radius=r_euler_min, layer=oplayer, angle=90,
                                            with_arc_floorplan=False)
        bend_thr2 = ring << gf.c.bend_euler(width=width_ring, radius=r_euler_min, layer=oplayer, angle=-90,
                                            with_arc_floorplan=False)
        str_th_horizontal = ring << GfCStraight(width=width_ring, length=length_th_horizontal, layer=oplayer)
        str_th_vertical = ring << GfCStraight(width=width_ring, length=length_th_vertical, layer=oplayer)

        str_th_horizontal.connect("o1", ring0.ports["R1Through"])
        bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
        str_th_vertical.connect("o1", other=bend_thr1.ports["o2"])
        bend_thr2.connect("o1", other=str_th_vertical.ports["o2"])
        taper_s2n2.connect("o1", other=bend_thr2.ports["o2"])

        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=taper_s2n2.ports["o2"])
    elif position_taper[0] == "between_bend":
        bend_thr1 = ring << gf.c.bend_euler(width=width_ring, radius=r_euler_min, layer=oplayer, angle=90,
                                            with_arc_floorplan=False)
        bend_thr2 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer, angle=-90,
                                            with_arc_floorplan=False)
        str_th_horizontal = ring << GfCStraight(width=width_ring, length=length_th_horizontal, layer=oplayer)
        str_th_vertical = ring << GfCStraight(width=width_single, length=length_th_vertical, layer=oplayer)
        str_th_horizontal.connect("o1", ring0.ports["R1Through"])
        bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
        taper_s2n2.connect("o1", other=bend_thr1.ports["o2"])
        str_th_vertical.connect("o1", other=taper_s2n2.ports["o2"])
        bend_thr2.connect("o1", other=str_th_vertical.ports["o2"])
        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=bend_thr2.ports["o2"])
    elif position_taper[0] == "no_bend":
        taper_s2n2.connect("o1", other=ring0.ports["R1Through"])
        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=taper_s2n2.ports["o2"])
    else:
        raise ValueError("position_taper 必须是 'before_bend' 或 'after_bend' 或 'between_bend' 或 'no_bend'")
    # add drop
    taper_s2n3 = ring << gf.c.taper(width1=width_single, width2=width_ring, length=length_taper, layer=oplayer)
    taper_s2n4 = ring << gf.c.taper(width1=width_ring, width2=width_single, length=length_taper, layer=oplayer)
    taper_s2n4.connect("o1", ring0.ports["R2Input"])
    ## add drop bend out
    bend_ad1 = ring << gf.c.bend_euler(width=width_ring, radius=r_euler_min, layer=oplayer, angle=-90,
                                       with_arc_floorplan=False)
    bend_ad2 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer, angle=90,
                                       with_arc_floorplan=False)
    str_ad = ring << GfCStraight(width=width_single, length=length_ad_vertical, layer=oplayer)
    str_ad0 = ring << GfCStraight(width=width_ring, length=length_ad_horizontal, layer=oplayer)

    str_ad0.connect("o2", other=ring0.ports["R2Through"])
    bend_ad1.connect("o2", other=str_ad0.ports["o1"])
    taper_s2n3.connect("o2", other=bend_ad1.ports["o1"])
    str_ad.connect("o2", other=taper_s2n3.ports["o1"])
    bend_ad2.connect("o2", other=str_ad.ports["o1"])
    ring.add_port("o3", port=taper_s2n4.ports["o2"])
    ring.add_port("o4", port=bend_ad2.ports["o1"])
    ring.add_port("RingInput", port=ring0.ports["R1Input"])
    # ring.add_port("Ring1C", port=ring0.ports["Ring1C"])
    # ring.add_port("Ring2C", port=ring0.ports["Ring2C"])
    for port in ring0.ports:
        if "Heat" in port.name:
            ring.add_port(port.name, port=port)
        if "R1" in port.name:
            ring.add_port(port.name, port=port)
        if "R2" in port.name:
            ring.add_port(port.name, port=port)
    # add_labels_to_ports(ring,(412,8))
    CCRing = sr << ring

    ## input
    tinring = sr << tin
    CCRing.connect("o1", other=tinring.ports["o2"], allow_width_mismatch=True, mirror=True)
    CCRing.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])
    ## add
    tadring = sr << tin
    tadring.connect('o2', CCRing.ports['o4'])
    tadring.movex(tinring.ports['o1'].center[0] - tadring.ports['o1'].center[0])
    sr.add_port("add", port=tadring.ports["o1"])
    ## output
    toutring = sr << tout
    toutring.connect("o1", other=CCRing.ports["o2"])
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("output", port=toutring.ports["o2"])
    ## drop
    tdpring = sr << tout
    tdpring.movey(-tdpring.ports['o1'].center[1] + CCRing.ports["o3"].center[1])
    tdpring.movex(length_total - tdpring.ports["o2"].center[0])
    bend_s_dp = sr << gf.c.bend_s(cross_section=X_single, size=[10, 0])
    bend_s_dp.connect("o1", other=CCRing.ports["o3"])
    sr.add_port("drop", port=tdpring.ports["o2"])
    ## route
    gf.routing.route_bundle(sr,
        [toutring.ports["o1"], CCRing.ports["o1"], tdpring.ports['o1'], CCRing.ports["o4"]],
        [CCRing.ports["o2"], tinring.ports["o2"], bend_s_dp.ports["o2"], tadring.ports['o2']],
        layer=oplayer, route_width=width_single, radius=r_euler_min)

    for port in CCRing.ports:
        sr.add_port(port.name, port=port)
    snap_all_polygons_iteratively(sr)
    add_labels_to_ports(sr, (512, 8))
    return sr
# TCCoupleDouRaceTrackT2: Total component Coupled racetrack cavity use CoupledRaceTrack
@gf.cell
def TCCoupleDouRaceTrackT2(
        r_ring: float = 120,
        r_euler_min: float = 100,
        width_ring: float = 1,
        width_near: float = 2,
        width_heat: float = 5,
        width_single: float = 1,
        width_total: float = 5000,
        gap_rc: float = 1,
        angle_rc: float = 20,
        gap_rr: float = 1,
        gap_heat: float = 1,
        delta_heat: float = 1,
        delta_run: float = 1,
        length_rr: float = 30,
        length_rc: float = 10,
        length_taper: float = 150,
        length_total: float = 10000,
        length_run: float = 400,
        length_taper2ring: float = 600,
        pos_ring= [500,2000],
        tin: Component = taper_in,
        tout: Component = taper_out,
        is_heat: bool = True,
        type_heater: str = "default",  # 控制加热器类型
        type_couple: str = "P",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        position_taper: str = ["before_bend","before_bend"],  # 控制锥形波导的位置
) -> Component:
    """
    创建集成了 `CoupleDouRaceTrack` 的完整组件 (ST2型配置)。
    此版本具有与ST1不同的输入/输出端口布局和路由策略，
    通常IO会分布在芯片的不同侧面或位置。

    参数:
        (大部分参数与 TCCoupleDouRaceTrackST1 类似)
        width_total (float): 芯片的总宽度，用于IO组件的右侧对齐 (µm)。
        length_taper2ring (float): 从IO taper到核心环器件的连接路径的特定长度 (µm)。
        pos_ring (list[float]): 核心 `CoupleDouRaceTrack` 组件的中心 (或参考点) 的 [x, y] 坐标 (µm)。

    返回:
        Component: 生成的集成耦合双跑道环组件 (ST2型)。

    端口:
        input, output, add, drop: 组件的四个主要光学IO端口。
        (以及从 `CoupleDouRaceTrack` 继承的加热器和其他参考端口)
    """
    sr = gf.Component()
    ring = gf.Component()
    if type_couple == "s" or type_couple == "S":
        width_near = width_ring
    S_single = gf.Section(width=width_single, layer=oplayer, port_names=('o1', 'o2'))
    X_single = gf.CrossSection(sections=(S_single,),radius_min=r_euler_min,radius=r_ring)
    S_ring = gf.Section(width=width_near, layer=oplayer, port_names=('o1', 'o2'))
    X_ring = gf.CrossSection(sections=(S_ring,),radius_min=r_euler_min,radius=r_ring-10)
    ring0 = ring << CoupleDouRaceTrack(
        RadiusRing=r_ring, WidthRing=width_ring,WidthNear=width_near,AngleCouple=angle_rc,
        GapCoupleOut=gap_rc,GapCoupleIn=gap_rr,
        LengthRun=length_run,LengthCoupleIn=length_rr,LengthCoupleOut=length_rc,DeltaRun=delta_run,
        DeltaHeat=delta_heat,WidthHeat=width_heat, GapHeat=gap_heat,
        TypeHeater=type_heater,TypeCouple=type_couple,
        IsHeat=is_heat, oplayer=oplayer, heatlayer=heatlayer, DirectionsHeater=['down', 'down']
    )

    # ring0.mirror_y(ring0.ports["R1Input"].center[1])
    # R1 input R2 through
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    ring0.connect("R1Input", taper_s2n1.ports["o2"])
    ring0.movex(length_taper2ring)
    taper_s2n2 = ring << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n2.movey(-20)
    # R2 input R1 through
    taper_s2n3 = ring << gf.c.taper(width1=width_near, width2=width_single, length=length_taper, layer=oplayer)
    taper_s2n4 = ring << gf.c.taper(width1=width_near, width2=width_single, length=length_taper, layer=oplayer)
    taper_s2n3.connect("o1", ring0.ports["R2Input"])
    taper_s2n3.movex(length_taper2ring)
    taper_s2n4.move(taper_s2n3.ports["o1"].center).movey(20)
    # route: R1 R2 to raper
    gf.routing.route_single(ring,taper_s2n1.ports["o2"],ring0.ports["R1Input"],cross_section=X_ring)
    gf.routing.route_single(ring, taper_s2n2.ports["o2"], ring0.ports["R2Through"], cross_section=X_ring)
    gf.routing.route_single(ring, taper_s2n3.ports["o1"], ring0.ports["R2Input"], cross_section=X_ring)
    gf.routing.route_single(ring, taper_s2n4.ports["o1"], ring0.ports["R1Through"], cross_section=X_ring)
    # ## add drop bend out
    ring.add_port("o1", port=taper_s2n1.ports["o1"])
    ring.add_port("o2", port=taper_s2n2.ports["o1"])
    ring.add_port("o3", port=taper_s2n3.ports["o2"])
    ring.add_port("o4", port=taper_s2n4.ports["o2"])
    ring.add_port("RingInput", port=ring0.ports["R1Input"])
    # # ring.add_port("Ring1C", port=ring0.ports["Ring1C"])
    # # ring.add_port("Ring2C", port=ring0.ports["Ring2C"])
    for port in ring0.ports:
        if "R1" in port.name:
            ring.add_port(port.name, port=port)
        if "R2" in port.name:
            ring.add_port(port.name, port=port)
    # # add_labels_to_ports(ring,(412,8))
    CCRing = sr << ring
    CCRing.move((pos_ring[0],-pos_ring[1]))
    ## input
    tinring = sr << tin
    tinring.rotate(-90)
    # tinring.movey(tinring.ports["o2"].center[1]-tinring.ports["o1"].center[1])
    sr.add_port("input", port=tinring.ports["o1"])
    ## add
    tadring = sr << tin
    tadring.connect("o1",tinring.ports["o1"])
    tadring.rotate(180,tadring.ports["o1"].center).movex(-20)
    # tadring.connect('o2', CCRing.ports['o4'])
    # tadring.movex(tinring.ports['o1'].center[0] - tadring.ports['o1'].center[0])
    sr.add_port("add", port=tadring.ports["o1"])
    ## output
    toutring = sr << tout
    toutring.connect("o1",tinring.ports["o2"])
    toutring.movex(width_total - toutring.ports["o2"].center[0])
    toutring.movey(-length_total -toutring.ports["o2"].center[1])
    sr.add_port("output", port=toutring.ports["o2"])
    ## drop
    tdpring = sr << tout
    tdpring.connect("o2",toutring.ports["o2"])
    tdpring.rotate(180,tdpring.ports["o2"].center).movex(-20)
    # bend_s_dp = sr << gf.c.bend_s(cross_section=X_single, size=[10, 0])
    # bend_s_dp.connect("o1", other=CCRing.ports["o3"])
    sr.add_port("drop", port=tdpring.ports["o2"])
    ## route
    gf.routing.route_bundle(sr,
        [ CCRing.ports["o1"], CCRing.ports["o2"]],
        [ tinring.ports["o2"], tadring.ports['o2']],
        layer=oplayer, route_width=width_single, radius=r_euler_min)
    gf.routing.route_bundle(sr,
        [ CCRing.ports["o4"], CCRing.ports["o3"]],
        [ toutring.ports["o1"], tdpring.ports['o1']],
        layer=oplayer, route_width=width_single, radius=r_euler_min)
    # snap_all_polygons_iteratively(sr)
    for port in CCRing.ports:
        sr.add_port(port.name, port=port)
    add_labels_to_ports(sr, (512, 8))
    return sr
__all__ = ['TCRingBoomerangT1', 'TCRingDouBoomerangT1', 'TCRingTriBoomerangT1', 'TCCoupleDouRingT1',
           'TCCoupleDouRaceTrackT1','TCCoupleDouRaceTrackT2']
