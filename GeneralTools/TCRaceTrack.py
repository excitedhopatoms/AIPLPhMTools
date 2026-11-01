"""TC 跑道环测试结构（test coupon）。

所有结构只在函数被调用时创建；旧版本在 import 阶段构造
``taper_in_DFB`` / ``taper_in_DFB_reverse`` 两个全局组件（且从未被引用），
已删除，避免导入副作用与 GDS 垃圾单元。
"""
from .BasicDefine import *
from .RaceTrack import *


@gf.cell
def TCRaceTrackP(
        r_ring: float = 2000,
        r_bend: float = 20,
        width_ring: float = 8,
        width_near: float = 4,
        width_route: float = 1,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 500,
        length_total: float = 10000,
        length_run: float = 1000,
        pos_ring: float = 5000,
        gap_rc: float = 1,
        tout: Component = None,
        tin: Component = None,
        oplayer: LayerSpec = "WG",
        heater_config:HeaterConfigClass = None,
        position_taper_in: str = "after_bend",   # 输入端 taper 位置
        position_taper_out: str = "before_bend",  # 输出端 taper 位置
) -> Component:
    """
    创建一个带有双端独立 taper 位置控制的滑轮耦合跑道环。
    耦合区域光传播的方向垂直光输入和输出的方向
    取代了原本的racetrack pulley耦合的总的腔的函数

    参数:
        position_taper_in:  输入端 taper 位置 ('before_bend' | 'after_bend' | 'no_bend')
        position_taper_out: 输出端 taper 位置 ('before_bend' | 'after_bend' | 'no_bend')

    三种选项定义:
        - 'before_bend': taper 在 bend 之前 (taper→bend)
        - 'after_bend':  taper 在 bend 之后 (bend→taper)
        - 'no_bend':     无弯曲，taper 直接连接
    """

    # 中间 core：跑道腔；外围 IO/taper/绕线/端口转发交给通用 Coupon 框架
    from .Coupon import Coupon

    ring = RaceTrackP(
        WidthRing=width_ring, WidthNear=width_near, GapCouple=gap_rc,
        oplayer=oplayer, RadiusRing=r_ring, AngleCouple=angle_rc,
        IsAD=False, LengthRun=length_run, HeaterConfig=heater_config,
    )
    return Coupon(
        core=ring,
        core_input="Input",
        core_output="Through",
        io_width=width_single,
        width_in=width_near,
        width_out=width_near,
        taper_length=length_taper,
        bend_radius=r_bend,
        position_taper_in=position_taper_in,
        position_taper_out=position_taper_out,
        length_total=length_total,
        core_x=pos_ring,
        core_rotation=90,
        tin=tin,
        tout=tout,
        tin_shift_x=-pos_ring,
        center_ports=("Rcen1", "Rcen2"),
        center_width=width_route,
        forward_ports=tuple(p.name for p in ring.ports),
        port_prefix="Ring",
        oplayer=oplayer,
    )

# %% TCRaceTrack2_1: racetrack ring,straigh couple straight in
@gf.cell
def TCRaceTrackS(
        r_ring: float = 2000,
        r_bend: float = r_euler_true,
        width_ring: float = 8,
        width_single: float = 1,
        length_rc: float = 20,
        length_run: float = 500,
        length_taper: float = 500,
        length_updown: float = 1500,
        length_horizon: float = 1500,
        length_total: float = 10000,
        length_ele:float = None,
        pos_ring: float = 5000,
        gap_rc: float = 1,
        type_heat:str = 'default',
        tout: Component =None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
        heater_config : HeaterConfigClass=None,
) -> Component:
    """
    创建一个集成了单个 `RaceTrackS` (直线耦合跑道环) 的完整组件。
    核心跑道环为双端口（Input/Through）。输入直接连接，输出臂包含较长的直线和弯曲部分。
    此函数对应原代码中的 `TCRaceTrack2_1`。

    参数:
        (大部分参数与 TCRaceTrackP 类似，但核心是 RaceTrackS)
        length_rc (float): 传递给 `RaceTrackS` 的 `LengthCouple` 参数 (µm)。
        length_run (float): 传递给 `RaceTrackS` 的 `LengthRun` 参数 (µm)。
        length_updown (float): 输出引出臂中垂直（上下）走向的直线段长度 (µm)。
        length_horizon (float): 输出引出臂中水平走向的直线段长度 (µm)。
        type_heat (str): 传递给 `RaceTrackS` 的 `TypeHeater` 参数。

    返回:
        Component: 生成的集成直线耦合跑道环组件。

    端口:
        input: 组件的总光学输入端口。
        output: 组件的总光学输出端口。
        RingC: 跑道环中心的参考端口。
    """
    sr = gf.Component()
    width_near = width_ring
    ring = sr << RaceTrackS(
        WidthRing=width_ring, LengthRun=length_run, GapCouple=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        LengthCouple=length_rc, IsAD=False,HeaterConfig=heater_config
    )
    taper_s2n_1 = sr << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n_2 = sr << gf.c.taper(width2=width_single, width1=width_near, length=length_taper, layer=oplayer)
    ring.rotate(270).movex(pos_ring)
    taper_s2n_1.connect("o2", other=ring.ports["Input"])
    taper_s2n_2.connect("o1", other=ring.ports["Through"])
    str_s2n = sr << GfCStraight(width=width_single, length=length_horizon, layer=oplayer)
    str_s2n.connect("o1", other=taper_s2n_2.ports["o2"])
    bend_outsingle_1 = sr << gf.c.bend_euler(width=width_single, angle=-90, radius=r_bend, layer=oplayer)
    bend_outsingle_1.connect("o1", other=str_s2n.ports["o2"])
    str_outsingle_1 = sr << GfCStraight(width=width_single, length=length_updown, layer=oplayer)
    str_outsingle_1.connect("o1", other=bend_outsingle_1.ports["o2"])
    bend_outsingle_2 = sr << gf.c.bend_euler(width=width_single, angle=90, radius=r_bend, layer=oplayer)
    bend_outsingle_2.connect("o1", other=str_outsingle_1.ports["o2"])
    # input
    if tin != None:
        ctin = sr << tin
        ctin.connect("o2", taper_s2n_1.ports["o1"],allow_width_mismatch=True)
        ctin.movex(-pos_ring)
        route_in = gf.routing.route_single_sbend(sr,ctin.ports["o2"], taper_s2n_1.ports["o1"], cross_section=make_cs(width_single, oplayer))
        sr.add_port("input", port=ctin.ports["o1"])
        sr.add_port("inputo2", port=ctin.ports["o2"])
    else:
        sr.add_port("input", port=taper_s2n_1.ports["o1"])
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o1", other=bend_outsingle_2.ports['o2'],allow_width_mismatch=True)
        ctout.movex(length_total-(ctout.ports["o2"].center[0]-ctin.ports["o1"].center[0]))
        route_out = gf.routing.route_single_sbend(sr,ctout.ports["o1"], bend_outsingle_2.ports['o2'], cross_section=make_cs(width_single, oplayer))
        # sr.add(route_out.references)
        sr.add_port("output", port=ctout.ports["o2"])
        sr.add_port("outputo1", port=ctout.ports["o1"])

    sr.add_port("RingC", port=ring.ports["Input"],
                center = (np.array(ring.ports["Rcen1"].center) + np.array(ring.ports["Rcen2"].center)) / 2)
    # add_labels_to_ports(sr)
    CompOut = gf.Component()
    Csr = CompOut << sr
    Csr.movex(-sr.ports["input"].center[0])
    for port in Csr.ports:
        CompOut.add_port(port.name,port=port)
    return CompOut

# %% TCRaceTrack2_2: racetrack ring,straigh couple straight out
@gf.cell
def TCRaceTrackS2(
        r_ring: float = 2000,
        r_bend: float = r_euler_true,
        width_ring: float = 8,
        width_single: float = 1,
        length_rc: float = 20,
        length_run: float = 200,
        length_taper: float = 500,
        length_horizon: float = 1500,
        length_updown: float = 1500,
        length_total: float = 10000,
        pos_ring: float = 5000,
        gap_rc: float = 1,
        tout: Component =None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
        heater_config:HeaterConfigClass=None,
) -> Component:
    """
    创建集成了单个 `RaceTrackS` (直线耦合跑道环) 的完整组件。
    与 `TCRaceTrackS` (原TCRaceTrack2_1) 的主要区别在于输入端口的引出臂结构，
    输出端口直接从环的Through端通过Taper引出。
    此函数对应原代码中的 `TCRaceTrack2_2`。

    参数:
        (大部分参数与 TCRaceTrackS 类似)
        length_run (float): 跑道环直线段长度，默认为200µm。
        length_horizon (float): 输入引出臂的水平段长度 (µm)。
        length_updown (float): 输入引出臂的垂直段长度 (µm)。

    返回:
        Component: 生成的集成直线耦合跑道环组件。

    端口: (与TCRaceTrackS类似)
    """
    sr = gf.Component()
    width_near = width_ring
    ring = sr << RaceTrackS(
        WidthRing=width_ring, LengthRun=length_run, GapCouple=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        LengthCouple=length_rc, IsAD=False,HeaterConfig=heater_config
    )
    taper_s2n_1 = sr << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n_2 = sr << gf.c.taper(width2=width_single, width1=width_near, length=length_taper, layer=oplayer)
    ring.rotate(90).mirror_x(ring.ports["Input"].center[0]).movex(pos_ring)
    taper_s2n_1.connect("o2", other=ring.ports["Input"])
    taper_s2n_2.connect("o1", other=ring.ports["Through"])
    str_s2n = sr << GfCStraight(width=width_single, length=length_horizon, layer=oplayer)
    str_s2n.connect("o1", other=taper_s2n_2.ports["o2"])
    bend_insingle_1 = sr << gf.c.bend_euler(width=width_single, angle=90, radius=r_bend, layer=oplayer)
    bend_insingle_1.connect("o2", other=str_s2n.ports["o1"])
    str_insingle_1 = sr << GfCStraight(width=width_single, length=length_updown, layer=oplayer)
    str_insingle_1.connect("o2", other=bend_insingle_1.ports["o1"])
    bend_insingle_2 = sr << gf.c.bend_euler(width=width_single, angle=-90, radius=r_bend, layer=oplayer)
    bend_insingle_2.connect("o2", other=str_insingle_1.ports["o1"])
    # input
    if tin != None:
        ctin = sr << tin
        ctin.connect("o2", bend_insingle_2.ports["o1"],allow_width_mismatch=True)
        ctin.movex(-pos_ring)
        route_in = gf.routing.route_single_sbend(sr,ctin.ports["o2"], bend_insingle_2.ports["o1"], cross_section=make_cs(width_single, oplayer))
        # sr.add(route_in.references)
        sr.add_port("input", port=ctin.ports["o1"])
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"],allow_width_mismatch=True)
        ctout.movex(length_total)
        delta = ctout.ports["o1"].center[1] - taper_s2n_2.ports["o2"].center[1]
        ctout.movey(-delta)
        route_out = gf.routing.route_single_sbend(sr,ctout.ports["o1"], taper_s2n_2.ports["o2"], cross_section=make_cs(width_single, oplayer))
        # sr.add(route_out.references)
        sr.add_port("output", port=ctout.ports["o1"])
    sr.add_port("RingC", port=ring.ports["Input"],
                center = (np.array(ring.ports["Rcen1"].center) + np.array(ring.ports["Rcen2"].center)) / 2)
    add_labels_to_ports(sr)
    return sr


# %% TCRaceTrack2_3: racetrack ring,straight couple straight in & out
@gf.cell
def TCRaceTrackS3(
        r_ring: float = 2000,
        width_ring: float = 8,
        width_single: float = 1,
        length_rc: float = 20,
        length_run: float = 400,
        length_taper: float = 500,
        length_total: float = 10000,
        pos_ring: float = 5000,
        gap_rc: float = 1,
        tout: Component =None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
        heater_config:HeaterConfigClass=None,
) -> Component:
    """
    创建集成了单个 `RaceTrackS` (直线耦合跑道环) 的完整组件。
    此版本具有最简化的输入/输出引出臂，基本上是直接通过锥形波导连接到
    核心跑道环的Input和Through端口。
    此函数对应原代码中的 `TCRaceTrack2_3`。

    参数:
        (大部分参数与 TCRaceTrackS 类似)
        IsLabels (bool): 是否为最终组件的端口添加标签。

    返回:
        Component: 生成的集成直线耦合跑道环组件（简化IO）。

    端口: (与TCRaceTrackS类似)
    """
    sr = gf.Component()
    width_near = width_ring
    Cring = RaceTrackS(
        WidthRing=width_ring, LengthRun=length_run, GapCouple=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        LengthCouple=length_rc, IsAD=False, HeaterConfig=heater_config
    )
    ring = sr << Cring
    taper_s2n_1 = sr << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n_2 = sr << gf.c.taper(width2=width_single, width1=width_near, length=length_taper, layer=oplayer)
    ring.rotate(90).mirror_x(ring.ports["Input"].center[0]).movex(pos_ring)
    taper_s2n_1.connect("o2", other=ring.ports["Input"])
    taper_s2n_2.connect("o1", other=ring.ports["Through"])
    # input
    if tin != None:
        ctin = sr << tin
        ctin.connect("o2", taper_s2n_1.ports["o1"],allow_width_mismatch=True)
        ctin.movex(-pos_ring)
        route_in = gf.routing.route_single_sbend(sr,ctin.ports["o2"], taper_s2n_1.ports["o1"], cross_section=make_cs(width_single, oplayer))
        # sr.add(route_in.references)
        sr.add_port("input", port=ctin.ports["o1"])
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"],allow_width_mismatch=True)
        ctout.movex(length_total)
        route_out = gf.routing.route_single_sbend(sr,ctout.ports["o1"], taper_s2n_2.ports["o2"], cross_section=make_cs(width_single, oplayer))
        # sr.add(route_out.references)
        sr.add_port("output", port=ctout.ports["o1"])
    sr.add_port("RingC", port=ring.ports["Input"],
                center = (np.array(ring.ports["Rcen1"].center) + np.array(ring.ports["Rcen2"].center)) / 2)
    return sr


@gf.cell
def TCRaceTrackS3h(
        r_ring: float = 2000,
        width_ring: float = 8,
        width_single: float = 1,
        length_rc: float = 20,
        length_run: float = 400,
        length_taper: float = 500,
        length_total: float = 10000,
        pos_ring: float = 5000,
        gap_rc: float = 1,
        gap_route: float = 100,
        tout: Component =None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
        heater_config: HeaterConfigClass=None,
) -> Component:
    """
    创建集成了单个 `RaceTrackS` (直线耦合跑道环) 的完整组件，并明确启用加热功能。
    此版本与 `TCRaceTrackS3` 结构类似，但确保 `RaceTrackS` 内部的加热器被激活，
    并继承加热器端口。

    参数:
        (与 TCRaceTrackS3 类似，增加了加热相关参数的明确传递)
        delta_heat (float): 传递给 `RaceTrackS` 的 `DeltaHeat` 参数 (µm)。
        gap_route (float): 传递给 `RaceTrackS` 的参数，可能用于加热器引出间距 (µm)。
                           (注意：`RaceTrackS` 的参数列表可能用 `GapHeat`)
        type_heat (str): 传递给 `RaceTrackS` 的加热器类型。
        width_heat (float): 传递给 `RaceTrackS` 的加热器宽度。

    返回:
        Component: 生成的带加热的集成直线耦合跑道环组件。

    端口:
        input, output, RingC
        HeatIn, HeatOut: (如果RaceTrackS正确生成并暴露了它们) 加热器电学端口。
    """
    sr = gf.Component()
    width_near = width_ring
    Cring = RaceTrackS(
        WidthRing=width_ring, LengthRun=length_run, GapCouple=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        LengthCouple=length_rc, IsAD=False, HeaterConfig=heater_config
    )
    ring = sr << Cring
    taper_s2n_1 = sr << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n_2 = sr << gf.c.taper(width2=width_single, width1=width_near, length=length_taper, layer=oplayer)
    ring.rotate(90).mirror_x(ring.ports["Input"].center[0]).movex(pos_ring)
    # heat.connect("HeatIn", other=ring.ports["HeatIn"])
    taper_s2n_1.connect("o2", other=ring.ports["Input"])
    taper_s2n_2.connect("o1", other=ring.ports["Through"])
    # input
    if tin != None:
        ctin = sr << tin
        ctin.connect("o2", taper_s2n_1.ports["o1"],allow_width_mismatch=True)
        ctin.movex(-pos_ring)
        route_in = gf.routing.route_single_sbend(sr,ctin.ports["o2"], taper_s2n_1.ports["o1"], cross_section=make_cs(width_single, oplayer))
        # sr.add(route_in.references)
        sr.add_port("input", port=ctin.ports["o1"])
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"],allow_width_mismatch=True)
        ctout.movex(length_total)
        route_out = gf.routing.route_single_sbend(sr,ctout.ports["o1"], taper_s2n_2.ports["o2"], cross_section=make_cs(width_single, oplayer))
        # sr.add(route_out.references)
        sr.add_port("output", port=ctout.ports["o1"])
    sr.add_port("RingC", port=ring.ports["Input"],
                center = (np.array(ring.ports["Rcen1"].center) + np.array(ring.ports["Rcen2"].center)) / 2)
    add_labels_to_ports(sr)
    if "HeatIn" in ring.ports:
        sr.add_port("HeatIn", port=ring.ports["HeatIn"])
    return sr


# %% TCTaperRaceTrack1: racetrack ring pulley coupling ring coupler + ring + bend
@gf.cell
def TCTaperRaceTrackP(
        r_ring: float = 2000,
        r_bend: float = r_euler_true,
        width_ring: float = 8,
        width_near: float = 4,
        width_run: float = 4,
        width_single: float = 1,
        angle_rc: float = 20,
        length_racetaper: float = 150,
        length_run: float = 300,
        length_taper: float = 500,
        length_total: float = 10000,
        pos_ring: float = 5000,
        gap_rc: float = 1,
        tout: Component =None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个集成了 `TaperRaceTrackPulley` (带锥形直线段的滑轮耦合跑道环) 的完整组件。
    包含标准的输入/输出接口，并通过弯曲和锥形波导连接到核心环的端口。

    参数:
        (大部分参数用于配置内部的 `TaperRaceTrackPulley` 单元及其引出臂)
        width_ring (float): `TaperRaceTrackPulley` 中环弯曲部分及直线锥形始末端的宽度 (µm)。
        width_run (float): `TaperRaceTrackPulley` 中跑道直线段（可能是最宽处）的宽度 (µm)。
        length_racetaper (float): `TaperRaceTrackPulley` 内部直线段单边锥形的长度 (µm)。
        length_run (float): `TaperRaceTrackPulley` 内部直线段的总长度 (µm)。

    返回:
        Component: 生成的集成带锥形跑道环的组件。

    端口: (与TCRaceTrackP类似)
    """
    sr = gf.Component()
    S_wg = gf.Section(width=width_single, offset=0, layer=oplayer, port_names=("o1", "o2"))
    CS_wg = gf.CrossSection(sections=[S_wg])
    ring = sr << TaperRaceTrackPulley(
        WidthRing=width_ring, WidthNear=width_near, WidthRun=width_run,
        LengthRun=length_run, LengthTaper=length_racetaper,
        GapCouple=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        AngleCouple=angle_rc, IsAD=False
    )
    taper_s2n_1 = sr << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n_2 = sr << gf.c.taper(width2=width_single, width1=width_near, length=length_taper, layer=oplayer)
    ring.rotate(90).movex(pos_ring)
    taper_s2n_1.connect("o2", other=ring.ports["Input"])
    taper_s2n_2.connect("o1", other=ring.ports["Through"])
    bend_single_1 = sr << gf.c.bend_euler(width=width_single, angle=-90, radius=r_bend, layer=oplayer)
    bend_single_2 = sr << gf.c.bend_euler(width=width_single, angle=90, radius=r_bend, layer=oplayer)
    bend_single_1.connect("o2", other=taper_s2n_1.ports["o1"])
    bend_single_2.connect("o1", other=taper_s2n_2.ports["o2"])
    # input
    if tin != None:
        ctin = sr << tin
        ctin.connect("o2", bend_single_1.ports["o1"], allow_width_mismatch=True)
        ctin.movex(-pos_ring)
        route_in = gf.routing.route_single_sbend(sr,ctin.ports["o2"], bend_single_1.ports["o1"], cross_section=make_cs(width_single, oplayer))
        # sr.add(route_in.references)
        sr.add_port("input", port=ctin.ports["o1"])
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"], allow_width_mismatch=True)
        ctout.movex(length_total)
        delta = ctout.ports["o1"].center[1] - bend_single_2.ports["o2"].center[1]
        ctout.movey(-delta)
        route_out = gf.routing.route_single_sbend(sr,ctout.ports["o1"], bend_single_2.ports["o2"], cross_section=make_cs(width_single, oplayer))
        # sr.add(route_out.references)
        sr.add_port("output", port=ctout.ports["o1"])
    sr.add_port("RingC", port=ring.ports["Input"],
                center = (np.array(ring.ports["Rcen1"].center) + np.array(ring.ports["Rcen2"].center)) / 2)
    return sr


# %% TCTaperRaceTrack2: racetrack ring pulley coupling ring coupler + bend + taper
@gf.cell
def TCTaperRaceTrackS(
        r_ring: float = 2000,
        r_bend: float = r_euler_true,
        width_ring: float = 8,
        width_near: float = 4,
        width_run: float = 4,
        width_single: float = 1,
        angle_rc: float = 20,
        length_racetaper: float = 150,
        length_run: float = 300,
        length_taper: float = 500,
        length_total: float = 10000,
        pos_ring: float = 5000,
        gap_rc: float = 1,
        tout: Component =None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个集成了带锥形直线段的跑道环谐振器的完整组件，并采用直线耦合方式。
    (注意：原函数名 `TCTaperRaceTrack2` 和内部调用的 `TaperRaceTrackPulley` 可能存在命名或类型上的不匹配，
     因为 `TaperRaceTrackPulley` 是滑轮耦合。这里假设存在一个直线耦合版本的带锥形跑道环，
     或者 `TaperRaceTrackPulley` 的耦合方式可以被覆盖为直线型，但这不常见。)
    为清晰起见，假设目标是直线耦合一个带有内部锥形直线段的跑道环。

    参数:
        (大部分参数与 TCTaperRaceTrackP 类似，但耦合方式应为直线型)
        gap_rc (float): 直线耦合的间隙 (µm)。
        width_near (float): (对于直线耦合，此参数可能不直接使用，总线宽度通常等于环宽)

    返回:
        Component: 生成的集成带锥形跑道环（直线耦合）的组件。

    端口: (与TCRaceTrackP类似)
    """
    sr = gf.Component()
    S_wg = gf.Section(width=width_single, offset=0, layer=oplayer, port_names=("o1", "o2"))
    CS_wg = gf.CrossSection(sections=[S_wg])
    ring = sr << TaperRaceTrackPulley(
        WidthRing=width_ring, WidthNear=width_near, WidthRun=width_run,
        LengthRun=length_run, LengthTaper=length_racetaper,
        GapCouple=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        AngleCouple=angle_rc, IsAD=False
    )
    taper_s2n_1 = sr << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n_2 = sr << gf.c.taper(width2=width_single, width1=width_near, length=length_taper, layer=oplayer)
    bend_single_1 = sr << gf.c.bend_euler(width=width_near, angle=-90, radius=r_bend, layer=oplayer)
    bend_single_2 = sr << gf.c.bend_euler(width=width_near, angle=90, radius=r_bend, layer=oplayer)
    ring.rotate(90).movex(pos_ring)
    bend_single_1.connect("o2", other=ring.ports["Input"])
    bend_single_2.connect("o1", other=ring.ports["Through"])
    taper_s2n_1.connect("o2", other=bend_single_1.ports["o1"])
    taper_s2n_2.connect("o1", other=bend_single_2.ports["o2"])

    # input
    if tin != None:
        ctin = sr << tin
        ctin.connect("o2", taper_s2n_1.ports["o1"], allow_width_mismatch=True)
        ctin.movex(-pos_ring)
        route_in = gf.routing.route_single_sbend(sr,ctin.ports["o2"], taper_s2n_1.ports["o1"], cross_section=make_cs(width_single, oplayer))
        # sr.add(route_in.references)
        sr.add_port("input", port=ctin.ports["o1"])
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"], allow_width_mismatch=True)
        ctout.movex(length_total)
        delta = ctout.ports["o1"].center[1] - taper_s2n_2.ports["o2"].center[1]
        ctout.movey(-delta)
        route_out = gf.routing.route_single_sbend(sr,ctout.ports["o1"], taper_s2n_2.ports["o2"], cross_section=make_cs(width_single, oplayer))
        # sr.add(route_out.references)
        sr.add_port("output", port=ctout.ports["o1"])
    sr.add_port("RingC", port=ring.ports["Input"], 
                center = (np.array(ring.ports["Rcen1"].center) + np.array(ring.ports["Rcen2"].center)) / 2)
    return sr
if __name__ == '__main__':
    test = TCRaceTrackP()
    # test.show()


__all__ = ['TCRaceTrackP', 'TCRaceTrackS', 'TCRaceTrackS2', 'TCRaceTrackS3', 'TCRaceTrackS3h', 'TCTaperRaceTrackP', 'TCTaperRaceTrackS']
