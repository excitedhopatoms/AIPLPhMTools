from .BasicDefine import *
from .Ring import *


# %% SingleRingIsolator0: SingleRingIsolator:ADD-DROP ring + monitor
@gf.cell
def SingleRingIsolator0(
        r_ring: float = 120,
        r_euler_false: float = 90,
        width_ring: float = 1,
        width_near1: float = 2,
        width_near2: float = 3,
        width_heat: float = 5,
        width_single: float = 1,
        angle_rc1: float = 20,
        angle_rc2: float = 30,
        angle_th1: float = 60,
        angle_dr: float = 60,
        length_taper: float = 150,
        length_total: float = 3000,
        length_thadd: float = 100,
        pos_ring: float = 1000,
        gap_rc1: float = 1,
        gap_rc2: float = 4,
        gap_ad: float = 30,
        tout: Component = None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个基于单 Add-Drop 环形谐振器（使用RingPulley1DC）的隔离器原型组件。
    包含输入（tin）和三个输出（tout）组件，通常用于连接光栅耦合器等IO结构。
    通过调整环的参数和耦合，可以实现特定波长的隔离或滤波功能。

    参数:
        r_ring (float): 核心环谐振器的半径 (µm)。
        r_euler_false (float): 用于连接路径的欧拉弯曲半径 (µm)。
        width_ring (float): 环内波导的宽度 (µm)。
        width_near1 (float): 主输入/直通总线在耦合区的宽度 (µm)。
        width_near2 (float): Add/Drop总线在耦合区的宽度 (µm)。
        width_heat (float): （如果RingPulley1DC支持）加热器的宽度 (µm)。
        width_single (float): 外部单模波导的宽度 (µm)。
        angle_rc1 (float): 主总线与环的耦合角度 (度)。
        angle_rc2 (float): Add/Drop总线与环的耦合角度 (度)。
        angle_th1 (float): Through端口引出路径的弯曲角度 (度)。
        angle_dr (float): Drop端口引出路径的弯曲角度 (度)。
        length_taper (float): 从单模波导到耦合总线宽度的锥形渐变长度 (µm)。
        length_total (float): 组件的总目标布局长度，用于对齐最右端的IO组件 (µm)。
        length_thadd (float): Through端口路径上的额外直线波导长度 (µm)。
        pos_ring (float): 环的输入耦合点的大致X轴坐标 (µm)。
        gap_rc1 (float): 主总线与环的耦合间隙 (µm)。
        gap_rc2 (float): Add/Drop总线与环的耦合间隙 (µm)。
        gap_ad (float): Drop端口相对于Through端口的垂直间隔 (µm)，主要影响布局。
        tout (ComponentSpec | None): 用于输出端口（Through, Add, Drop）的组件规格（例如光栅）。
                                     如果为 None，则不添加特定的输出终端组件。
        tin (ComponentSpec | None): 用于输入端口的组件规格（例如光栅）。
                                    如果为 None，则不添加特定的输入终端组件。
        oplayer (LayerSpec): 光学波导层。

    返回:
        Component: 生成的单环隔离器原型组件。

    端口:
        input: 组件的总光学输入端口。
        through: 组件的直通光学端口。
        drop: 组件的下载光学端口。
        add: 组件的增加光学端口。
        RingC: 环中心的参考点（概念性端口，不用于连接）。
    """
    sr = gf.Component()
    # Section CrossSection
    S_near1 = gf.Section(width=width_near1, layer=oplayer, port_names=("o1", "o2"))
    CS_near1 = gf.CrossSection(sections=[S_near1])
    S_near2 = gf.Section(width=width_near2, layer=oplayer, port_names=("o1", "o2"))
    CS_near2 = gf.CrossSection(sections=[S_near2])
    # component
    tinring = sr << tin
    toutring_th = sr << tout
    toutring_ad = sr << tout
    toutring_dr = sr << tout
    taper_s2n1 = gf.c.taper(width1=width_single, width2=width_near1, length=length_taper, layer=oplayer)
    taper_s2n2 = gf.c.taper(width1=width_single, width2=width_near2, length=length_taper, layer=oplayer)
    taper_s2n_in = sr << taper_s2n1
    taper_s2n_th = sr << taper_s2n1
    taper_s2n_ad = sr << taper_s2n2
    taper_s2n_dr = sr << taper_s2n2
    ring = sr << RingPulley1DC(
        WidthRing=width_ring, oplayer=oplayer, RadiusRing=r_ring,
        WidthNear1=width_near1, GapRing1=gap_rc1, AngleCouple1=angle_rc1,
        WidthNear2=width_near2, GapRing2=gap_rc2, AngleCouple2=angle_rc2,
        WidthHeat=width_heat
    )
    taper_s2n_in.movex(pos_ring - length_taper)
    ring.connect("Input", other=taper_s2n_in.ports["o2"], mirror=True)
    length_tout = abs(toutring_th.ports["o1"].center[0] - toutring_th.ports["o2"].center[0])
    # add
    taper_s2n_ad.connect("o2", other=ring.ports["Add"])
    toutring_ad.connect("o1", other=taper_s2n_ad.ports["o1"])
    toutring_ad.movex(length_total - length_tout - taper_s2n_ad.ports["o1"].center[0])
    # through
    bend_th1 = sr << gf.c.bend_euler(width=width_near1, layer=oplayer, angle=-angle_th1,
                                     radius=r_euler_false * 1.2)
    bend_th2 = sr << gf.c.bend_euler(width=width_near1, layer=oplayer, angle=angle_th1,
                                     radius=r_euler_false * 1.2)
    str_th1 = sr << GfCStraight(width=width_near1, layer=oplayer, length=length_thadd)
    bend_th1.connect("o1", other=ring.ports["Through"])
    str_th1.connect("o1", other=bend_th1.ports["o2"])
    bend_th2.connect("o1", other=str_th1.ports["o2"])
    # bend_th2.movey(0)
    gf.routing.get_route(bend_th2.ports["o1"], bend_th1.ports["o2"], width=width_near1, layer=oplayer, radius=150)
    taper_s2n_th.connect("o2", other=bend_th2.ports["o2"])
    toutring_th.connect("o1", other=taper_s2n_th.ports["o1"])
    toutring_th.movex(length_total - length_tout - taper_s2n_th.ports["o1"].center[0])
    # drop
    taper_s2n_dr.connect("o2", other=ring.ports["Drop"], mirror=True)
    taper_s2n_dr.move([-100, -gap_ad])
    bend_dr1 = sr << gf.c.bend_euler(width=width_near2, layer=oplayer, angle=-angle_dr,
                                     radius=r_euler_false * 1.2)
    bend_dr2 = sr << gf.c.bend_euler(width=width_near2, layer=oplayer, angle=angle_dr,
                                     radius=r_euler_false * 1.2)
    bend_dr1.connect("o1", other=ring.ports["Drop"])
    bend_dr2.connect("o1", other=bend_dr1.ports["o2"])
    route_drop = gf.routing.get_route(taper_s2n_dr.ports["o2"], bend_dr2.ports["o2"], radius=120,
                                      cross_section=CS_near2)
    toutring_dr.connect("o1", other=taper_s2n_dr.ports["o1"])
    toutring_dr.movex(length_total - length_tout - taper_s2n_dr.ports["o1"].center[0])
    # route io
    route_io = gf.routing.get_bundle(
        [tinring.ports["o2"], taper_s2n_ad.ports["o1"], taper_s2n_dr.ports["o1"], taper_s2n_th.ports["o1"]],
        [taper_s2n_in.ports["o1"], toutring_ad.ports["o1"], toutring_dr.ports["o1"], toutring_th.ports["o1"]],
        width=width_single, layer=oplayer
    )
    for route in route_io:
        sr.add(route.references)
    sr.add(route_drop.references)
    # add_port
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("through", port=toutring_th.ports["o2"])
    sr.add_port("drop", port=toutring_dr.ports["o2"])
    sr.add_port("add", port=toutring_ad.ports["o2"])
    Rcenter = [ring.ports["RingL"].center[i] / 2 + ring.ports["RingR"].center[i] / 2 for i in range(2)]
    sr.add_port("RingC", port=sr.ports["input"], center=Rcenter)
    sr.flatten()
    add_labels_to_ports(sr)
    return sr


# %% SingleRingIsolator1: SingleRingIsolator:ADD-DROP ring + monitor
@gf.cell
def SingleRingIsolator1(
        r_ring: float = 120,
        r_euler_false: float = 100,
        r_euler_moni: float = 100,
        width_ring: float = 1,
        width_near1: float = 2,
        width_near2: float = 3,
        width_heat: float = 5,
        width_single: float = 1,
        angle_rc1: float = 20,
        angle_rc2: float = 30,
        angle_th1: float = 60,
        angle_th2: float = 60,
        length_taper: float = 150,
        length_total: float = 3000,
        length_monicouple=100,
        length_thadd: float = 100,
        pos_ring: float = 1000,
        pos_monitor: float = 500,
        gap_rc1: float = 1,
        gap_rc2: float = 4,
        gap_mc: float = 1,
        tout: Component = None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个带监控端口的单 Add-Drop 环形谐振器隔离器原型。
    除了 `SingleRingIsolator0` 的功能外，此版本在主输入路径旁增加了一个浅耦合的监控路径，
    用于引出部分光信号进行功率监控或反馈。监控路径末端可以连接到探测器或另一个IO组件。

    参数:
        (大部分参数与 `SingleRingIsolator0` 相同)
        r_euler_moni (float): 监控路径中弯曲波导的半径 (µm)。
        angle_th2 (float): Drop端口引出路径的弯曲角度 (度)。 (原参数名，建议改为 angle_dr)
        length_monicouple (float): 监控路径与主输入路径平行耦合的直线段长度 (µm)。
        pos_monitor (float): 监控耦合器相对于整体输入起点的大致X轴位置 (µm)。
        gap_mc (float): 主输入路径与监控路径之间的耦合间隙 (µm)。

    返回:
        Component: 生成的带监控端口的单环隔离器原型组件。

    端口:
        (与 `SingleRingIsolator0` 类似，额外增加)
        monitor_out: 监控路径的输出端口。
    """
    sr = gf.Component()
    # Section CrossSection
    S_near1 = gf.Section(width=width_near1, layer=oplayer, port_names=("o1", "o2"))
    CS_near1 = gf.CrossSection(sections=[S_near1])
    S_near2 = gf.Section(width=width_near2, layer=oplayer, port_names=("o1", "o2"))
    CS_near2 = gf.CrossSection(sections=[S_near2])
    # component
    tinring = sr << tin
    toutring_th = sr << tout
    toutring_ad = sr << tout
    toutring_dr = sr << tout
    taper_s2n1 = gf.c.taper(width1=width_single, width2=width_near1, length=length_taper, layer=oplayer)
    taper_s2n2 = gf.c.taper(width1=width_single, width2=width_near2, length=length_taper, layer=oplayer)
    taper_s2n_in = sr << taper_s2n1
    taper_s2n_th = sr << taper_s2n1
    taper_s2n_ad = sr << taper_s2n2
    taper_s2n_dr = sr << taper_s2n2
    ring = sr << RingPulley1DC(
        WidthRing=width_ring, oplayer=oplayer, RadiusRing=r_ring,
        WidthNear1=width_near1, GapRing1=gap_rc1, AngleCouple1=angle_rc1,
        WidthNear2=width_near2, GapRing2=gap_rc2, AngleCouple2=angle_rc2,
        WidthHeat=width_heat
    )
    taper_s2n_in.movex(pos_ring - length_taper)
    ring.connect("Input", other=taper_s2n_in.ports["o2"], mirror=True)
    length_tout = abs(toutring_th.ports["o1"].center[0] - toutring_th.ports["o2"].center[0])
    # add
    taper_s2n_ad.connect("o2", other=ring.ports["Add"])
    toutring_ad.connect("o1", other=taper_s2n_ad.ports["o1"])
    toutring_ad.movex(length_total - length_tout - taper_s2n_ad.ports["o1"].center[0])
    # through
    bend_th1 = sr << gf.c.bend_euler(width=width_near1, layer=oplayer, angle=-angle_th1,
                                     radius=r_euler_false * 1.2)
    bend_th2 = sr << gf.c.bend_euler(width=width_near1, layer=oplayer, angle=angle_th1,
                                     radius=r_euler_false * 1.2)
    bend_th1.connect("o1", other=ring.ports["Through"])
    bend_th2.connect("o1", other=bend_th1.ports["o2"])
    # bend_th2.movey(0)
    gf.routing.get_route(bend_th2.ports["o1"], bend_th1.ports["o2"], width=width_near1, layer=oplayer, radius=150)
    taper_s2n_th.connect("o2", other=bend_th2.ports["o2"])
    toutring_th.connect("o1", other=taper_s2n_th.ports["o1"])
    toutring_th.movex(length_total - length_tout - taper_s2n_th.ports["o1"].center[0])
    # drop
    taper_s2n_dr.connect("o2", other=ring.ports["Drop"], mirror=True)
    taper_s2n_dr.move([-100, -30])
    bend_dr1 = sr << gf.c.bend_euler(width=width_near2, layer=oplayer, angle=-angle_th2,
                                     radius=r_euler_false * 1.2)
    bend_dr2 = sr << gf.c.bend_euler(width=width_near2, layer=oplayer, angle=angle_th2,
                                     radius=r_euler_false * 1.2)
    bend_dr1.connect("o1", other=ring.ports["Drop"])
    bend_dr2.connect("o1", other=bend_dr1.ports["o2"])
    route_drop = gf.routing.get_route(taper_s2n_dr.ports["o2"], bend_dr2.ports["o2"], radius=120,
                                      cross_section=CS_near2)
    toutring_dr.connect("o1", other=taper_s2n_dr.ports["o1"])
    toutring_dr.movex(length_total - length_tout - taper_s2n_dr.ports["o1"].center[0])
    # monitor
    str_moni = sr << GfCStraight(length=length_monicouple, width=width_single, layer=oplayer)
    str_moni.connect("o1", other=taper_s2n_in.ports["o1"])
    str_moni.movey(-width_single - gap_mc)
    taper_moni = sr << OffsetRamp(width1=width_single, width2=0, offset=width_single / 2, length=50, layer=oplayer)
    taper_moni.connect("o1", other=str_moni.ports["o1"])
    bend_moni = sr << gf.c.bend_euler(width=width_single, radius=r_euler_moni, layer=oplayer, angle=90)
    bend_moni.connect("o1", other=str_moni.ports["o2"])
    toutring_mn = sr << tout
    toutring_mn.connect("o1", other=toutring_dr.ports["o1"], mirror=True)
    toutring_mn.movey(-127)
    str_moni_out = sr << GfCStraight(width=width_single,
                                     length=toutring_mn.ports["o1"].center[0] - taper_s2n_dr.ports["o1"].center[0])
    str_moni_out.connect("o2", other=toutring_mn.ports["o1"])
    # route io
    route_io = gf.routing.get_bundle(
        [tinring.ports["o2"], taper_s2n_ad.ports["o1"], taper_s2n_dr.ports["o1"], taper_s2n_th.ports["o1"]],
        [taper_s2n_in.ports["o1"], toutring_ad.ports["o1"], toutring_dr.ports["o1"], toutring_th.ports["o1"]],
        width=width_single, layer=oplayer
    )
    for route in route_io:
        sr.add(route.references)
    sr.add(route_drop.references)

    route_mn = gf.routing.get_bundle(
        ports1=bend_moni.ports["o2"], ports2=str_moni_out.ports["o1"], width=width_single, radius=r_euler_false,
        layer=oplayer
    )
    for route in route_mn:
        sr.add(route.references)
    # add_port
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("through", port=toutring_th.ports["o2"])
    sr.add_port("drop", port=toutring_dr.ports["o2"])
    sr.add_port("add", port=toutring_ad.ports["o2"])
    Rcenter = [ring.ports["RingL"].center[i] / 2 + ring.ports["RingR"].center[i] / 2 for i in range(2)]
    sr.add_port("RingC", port=sr.ports["input"], center=Rcenter)
    sr.flatten()
    add_labels_to_ports(sr)
    return sr


# %% RingAndIsolator0:Ring and SingleRingIsolator0: ring for comb and ADD-DROP ring
@gf.cell
def RingAndIsolator0(
        r_ring: float = 120,
        r_euler_false: float = 100,
        width_ring: float = 1,
        width_Cring: float = None,
        width_near1: float = 2,
        width_near2: float = 3,
        width_nearC: float = 4,
        width_heat: float = 5,
        width_single: float = 1,
        angle_rc1: float = 20,
        angle_rc2: float = 30,
        angle_th1: float = 60,
        angle_dr: float = 60,
        angle_Cring: float = 20,
        length_taper: float = 150,
        length_total: float = 3000,
        length_thadd: float = 100,
        pos_ring: float = 1000,
        pos_Cring: float = 300,
        gap_rc1: float = 1,
        gap_rc2: float = 4,
        gap_ad: float = 30,
        gap_Cring: float = 1,
        tout: Component = None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个集成组件，包含一个用于光梳生成的环形谐振器（梳状环）和一个
    `SingleRingIsolator0` 类型的单环隔离器原型。两者通常串联在同一光路中，
    先经过梳状环，再进入隔离器。

    参数:
        (大部分参数与 `SingleRingIsolator0` 相同，用于配置隔离器部分)
        width_Cring (float | None): 梳状环的波导宽度 (µm)。如果为 None，则使用与隔离器环相同的宽度 (`width_ring`)。
        width_nearC (float): 梳状环耦合区域的总线波导宽度 (µm)。
        angle_Cring (float): 梳状环的耦合角度 (度)。
        pos_Cring (float): 梳状环输入耦合点的大致X轴坐标 (µm)。
        gap_Cring (float): 梳状环与总线的耦合间隙 (µm)。

    返回:
        Component: 生成的梳状环+隔离器集成组件。

    端口: (与 `SingleRingIsolator0` 类似)
        input, through, drop, add: 组件的主要光学端口。
        RingC_iso: 隔离器环中心的参考点。
        RingC_comb: 梳状环中心的参考点。
    """
    sr = gf.Component()
    if width_Cring == None:
        width_Cring = width_ring
    # Section CrossSection
    S_near1 = gf.Section(width=width_near1, layer=oplayer, port_names=("o1", "o2"))
    CS_near1 = gf.CrossSection(sections=[S_near1])
    S_near2 = gf.Section(width=width_near2, layer=oplayer, port_names=("o1", "o2"))
    CS_near2 = gf.CrossSection(sections=[S_near2])
    # component
    tinring = sr << tin
    toutring_th = sr << tout
    toutring_ad = sr << tout
    toutring_dr = sr << tout
    taper_s2n1 = gf.c.taper(width1=width_single, width2=width_near1, length=length_taper, layer=oplayer)
    taper_s2n2 = gf.c.taper(width1=width_single, width2=width_near2, length=length_taper, layer=oplayer)
    taper_s2n_in = sr << taper_s2n1
    taper_s2n_th = sr << taper_s2n1
    taper_s2n_ad = sr << taper_s2n2
    taper_s2n_dr = sr << taper_s2n2
    ring_comb = sr << RingPulley(
        WidthRing=width_Cring, WidthNear=width_nearC,
        RadiusRing=r_ring, GapRing=gap_Cring, AngleCouple=angle_Cring,
        IsHeat=False, IsAD=False, oplayer=oplayer,
    )
    ring_iso = sr << RingPulley1DC(
        WidthRing=width_ring, oplayer=oplayer, RadiusRing=r_ring,
        WidthNear1=width_near1, GapRing1=gap_rc1, AngleCouple1=angle_rc1,
        WidthNear2=width_near2, GapRing2=gap_rc2, AngleCouple2=angle_rc2,
        WidthHeat=width_heat
    )
    taper_s2n_in.movex(pos_ring - length_taper)
    ring_iso.connect("Input", other=taper_s2n_in.ports["o2"], mirror=True)
    ring_comb.connect("Input", other=taper_s2n_in.ports["o2"], allow_width_mismatch=True, mirror=True)
    ring_comb.movex(pos_Cring - pos_ring)
    length_tout = abs(toutring_th.ports["o1"].center[0] - toutring_th.ports["o2"].center[0])
    # comb ring taper
    taper_s2CRin = sr << gf.c.taper(width2=width_nearC, width1=width_single, length=length_taper, layer=oplayer)
    taper_CRout2s = sr << gf.c.taper(width2=width_single, width1=width_nearC, length=length_taper, layer=oplayer)
    taper_s2CRin.connect("o2", ring_comb.ports["Input"])
    taper_CRout2s.connect("o1", ring_comb.ports["Through"])

    # add
    taper_s2n_ad.connect("o2", other=ring_iso.ports["Add"])
    toutring_ad.connect("o1", other=taper_s2n_ad.ports["o1"])
    toutring_ad.movex(length_total - length_tout - taper_s2n_ad.ports["o1"].center[0])
    # through
    bend_th1 = sr << gf.c.bend_euler(width=width_near1, layer=oplayer, angle=-angle_th1,
                                     radius=r_euler_false * 1.2)
    bend_th2 = sr << gf.c.bend_euler(width=width_near1, layer=oplayer, angle=angle_th1,
                                     radius=r_euler_false * 1.2)
    str_th1 = sr << GfCStraight(width=width_near1, layer=oplayer, length=length_thadd)
    bend_th1.connect("o1", other=ring_iso.ports["Through"])
    str_th1.connect("o1", other=bend_th1.ports["o2"])
    bend_th2.connect("o1", other=str_th1.ports["o2"])
    # bend_th2.movey(0)
    gf.routing.get_route(bend_th2.ports["o1"], bend_th1.ports["o2"], width=width_near1, layer=oplayer, radius=150)
    taper_s2n_th.connect("o2", other=bend_th2.ports["o2"])
    toutring_th.connect("o1", other=taper_s2n_th.ports["o1"])
    toutring_th.movex(length_total - length_tout - taper_s2n_th.ports["o1"].center[0])
    # drop
    taper_s2n_dr.connect("o2", other=ring_iso.ports["Drop"], mirror=True)
    taper_s2n_dr.move([-100, -gap_ad])
    bend_dr1 = sr << gf.c.bend_euler(width=width_near2, layer=oplayer, angle=-angle_dr,
                                     radius=r_euler_false * 1.2)
    bend_dr2 = sr << gf.c.bend_euler(width=width_near2, layer=oplayer, angle=angle_dr,
                                     radius=r_euler_false * 1.2)
    bend_dr1.connect("o1", other=ring_iso.ports["Drop"])
    bend_dr2.connect("o1", other=bend_dr1.ports["o2"])
    route_drop = gf.routing.get_route(taper_s2n_dr.ports["o2"], bend_dr2.ports["o2"], radius=120,
                                      cross_section=CS_near2)
    toutring_dr.connect("o1", other=taper_s2n_dr.ports["o1"])
    toutring_dr.movex(length_total - length_tout - taper_s2n_dr.ports["o1"].center[0])
    # route io
    route_io = gf.routing.get_bundle(
        [tinring.ports["o2"], taper_CRout2s.ports["o2"], taper_s2n_ad.ports["o1"], taper_s2n_dr.ports["o1"],
         taper_s2n_th.ports["o1"]],
        [taper_s2CRin.ports["o1"], taper_s2n_in.ports["o1"], toutring_ad.ports["o1"], toutring_dr.ports["o1"],
         toutring_th.ports["o1"]],
        width=width_single, layer=oplayer
    )
    for route in route_io:
        sr.add(route.references)
    sr.add(route_drop.references)
    # add_port
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("through", port=toutring_th.ports["o2"])
    sr.add_port("drop", port=toutring_dr.ports["o2"])
    sr.add_port("add", port=toutring_ad.ports["o2"])
    Rcenter = [ring_iso.ports["RingL"].center[i] / 2 + ring_iso.ports["RingR"].center[i] / 2 for i in range(2)]
    sr.add_port("RingC", port=sr.ports["input"], center=Rcenter)
    sr.flatten()
    add_labels_to_ports(sr)
    return sr
