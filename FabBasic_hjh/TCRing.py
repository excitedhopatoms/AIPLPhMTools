from .BasicDefine import *
from .Heater import *
from .Ring import *

r_euler_false = 300
r_euler_true = 200

# %% defult in out taper
def create_taper(name, width1, width2, lengthleft=100, lengthtaper=100, lengthright=100, layer: LayerSpec = (1, 0)):
    taper = gf.Component(name)
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


# % TCRing: simple straight pulley
@gf.cell
def TCRing(
        r_ring: float = 120,
        r_euler_true: float = r_euler_true,
        width_ring: float = 1,
        width_near: float = 2,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 150,
        length_total: float = 10000,
        pos_ring: float = 500,
        length_th_vertical=100,
        gap_rc: float = 1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        is_ad: bool = False,
        oplayer: LayerSpec = LAYER.WG,
        heater_config:HeaterConfigClass=None,
) -> Component:
    """
    创建一个基础环形波导组件，支持加热器和输入输出锥形波导。
    环形波导可以配置为是否包含加热器和 Add/Drop 端口，并支持自定义几何参数。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_euler_true: 欧拉弯曲的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        delta_io: 输入输出端口的偏移量（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        is_heat: 是否添加加热器。
        is_ad: 是否添加 Add/Drop 端口。
        oplayer: 光学层定义。
        heatlayer: 加热层定义。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
        HeatIn: 加热输入端口（如果 is_heat 为 True）。
        HeatOut: 加热输出端口（如果 is_heat 为 True）。
    """
    sr = TCRingT1(
        r_ring=r_ring,
        r_euler_min=r_euler_true,
        width_ring=width_ring,
        width_near=width_near,
        width_single=width_single,
        angle_rc=angle_rc,
        length_taper=length_taper,
        length_total=length_total,
        length_th_vertical=length_th_vertical,
        pos_ring=pos_ring,
        gap_rc=gap_rc,
        tin=tin,
        tout=tout,
        is_ad=is_ad,
        oplayer=oplayer,
        heater_config_ring=heater_config,
    )
    return sr


# %% TCRing1_2: add-drop ring
@gf.cell
def TCRing1AD(
        r_ring: float = 120,
        width_ring: float = 1,
        width_near: float = 2,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 150,
        length_total: float = 2000,
        pos_ring: float = 500,
        gap_rc: float = 1,
        tout: Component = taper_out,
        tin: Component = taper_in,
        oplayer: LayerSpec = LAYER.WG,
        heater_config:HeaterConfigClass=None,
) -> Component:
    """
    创建一个支持 Add/Drop 端口的环形波导组件。
    该组件包含输入、输出、Through、Add 和 Drop 端口。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        tout: 输出锥形波导组件。
        tin: 输入锥形波导组件。
        oplayer: 光学层定义。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        through: Through 端口。
        drop: Drop 端口。
        add: Add 端口。
        RingC: 环形波导的中心端口。
    """
    sr = gf.Component()
    # Section CrossSection
    S_near = gf.Section(width=width_near, layer=oplayer, port_names=("o1", "o2"))
    CS_near = gf.CrossSection(sections=[S_near])
    # component
    tinring = sr << tin
    toutring_th = sr << tout
    toutring_ad = sr << tout
    toutring_dr = sr << tout
    taper_s2n = gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n_in = sr << taper_s2n
    taper_s2n_th = sr << taper_s2n
    taper_s2n_ad = sr << taper_s2n
    taper_s2n_dr = sr << taper_s2n
    ring = sr << RingPulley(
        WidthRing=width_ring, WidthNear=width_near, GapRing=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        AngleCouple=angle_rc, HeaterConfig=heater_config, IsAD=True
    )
    taper_s2n_in.movex(pos_ring - length_taper).movey(
        tinring.ports['o1'].center[1] - taper_s2n_in.ports['o1'].center[1])
    ring.connect("Input", other=taper_s2n_in.ports["o2"], mirror=True)
    length_tout = abs(toutring_th.ports["o1"].center[0] - toutring_th.ports["o2"].center[0])
    # add
    taper_s2n_ad.connect("o2", other=ring.ports["Add"])
    toutring_ad.connect("o1", other=taper_s2n_ad.ports["o1"])
    toutring_ad.movex(length_total - length_tout - taper_s2n_ad.ports["o1"].center[0])
    # through
    bend_th1 = sr << GfCBendEuler(width=width_near, layer=oplayer, angle=-90,
                                  radius=r_euler_false / 2 + r_ring * np.sin((20 - angle_rc / 2) * 3.14 / 180))
    bend_th2 = sr << GfCBendEuler(width=width_near, layer=oplayer, angle=90,
                                  radius=r_euler_false / 2 + r_ring * np.sin((10 - angle_rc / 2) * 3.14 / 180))
    bend_th1.connect("o1", other=ring.ports["Through"])
    delta = bend_th1.ports["o2"].center[1] - taper_s2n_ad.ports["o2"].center[1]
    bend_th2.connect("o1", other=bend_th1.ports["o2"])
    bend_th2.movey(-delta + r_ring / 2 + r_euler_false / 2 + 15 + +r_ring * np.sin((10 - angle_rc / 2) * 3.14 / 180))
    route = gf.routing.route_single(sr, bend_th2.ports["o1"], bend_th1.ports["o2"], route_width=width_near,
                                    layer=oplayer)
    taper_s2n_th.connect("o2", other=bend_th2.ports["o2"])
    toutring_th.connect("o1", other=taper_s2n_th.ports["o1"])
    toutring_th.movex(length_total - length_tout - taper_s2n_th.ports["o1"].center[0])
    # drop
    taper_s2n_dr.connect("o2", other=ring.ports["Drop"], mirror=True)
    taper_s2n_dr.mirror_x(taper_s2n_dr.ports["o2"].center[0])
    taper_s2n_dr.movey(-35 - r_ring * (1 - np.cos(angle_rc / 2 * 3.14 / 180)))
    bend_dr1 = sr << GfCBendEuler(width=width_near, layer=oplayer, angle=-30, radius=r_euler_false * 3)
    bend_dr1.connect("o1", other=ring.ports["Drop"])
    bend_dr2 = sr << GfCBendEuler(width=width_near, layer=oplayer, angle=210, radius=r_euler_false * 2 / 3)
    bend_dr2.connect("o1", other=bend_dr1.ports["o2"])
    route = gf.routing.route_single_sbend(sr, bend_dr2.ports["o2"], taper_s2n_dr.ports["o2"], cross_section=CS_near)
    # sr.add(route.references)
    toutring_dr.connect("o1", other=taper_s2n_dr.ports["o1"])
    toutring_dr.movex(length_total - length_tout - taper_s2n_dr.ports["o1"].center[0])
    # route io
    route_io = gf.routing.route_bundle(
        sr,
        [tinring.ports["o2"], taper_s2n_ad.ports["o1"], taper_s2n_dr.ports["o1"], taper_s2n_th.ports["o1"]],
        [taper_s2n_in.ports["o1"], toutring_ad.ports["o1"], toutring_dr.ports["o1"], toutring_th.ports["o1"]],
        route_width=width_single, layer=oplayer
    )
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("through", port=toutring_th.ports["o2"])
    sr.add_port("drop", port=toutring_dr.ports["o2"])
    sr.add_port("add", port=toutring_ad.ports["o2"])
    sr.add_port("RingC", width=width_single,layer=oplayer,
                center=np.array(ring.ports["RingL"].center) / 2 + np.array(ring.ports["RingR"].center) / 2)
    sr = remove_layer(sr, layer=(512, 8))
    add_labels_to_ports(sr)
    sr.flatten()
    return sr


# %% TCRing: simple straight pulley
@gf.cell
def TCRing1_3(
        r_ring: float = 120,
        width_ring: float = 1,
        width_near: float = 2,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 150,
        length_total: float = 10000,
        pos_ring: float = 500,
        gap_rc: float = 1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        oplayer: LayerSpec = LAYER.WG,
        heater_config:HeaterConfigClass=None,
) -> Component:
    """
    ---不建议使用---
    创建一个简单的环形波导组件，支持输入输出锥形波导。
    该组件不包含 Add/Drop 端口。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        oplayer: 光学层定义。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
    """
    sr = TCRingT1(
        r_ring=r_ring,
        width_ring=width_ring,
        width_near=width_near,
        width_single=width_single,
        angle_rc=angle_rc,
        length_taper=length_taper,
        length_total=length_total,
        pos_ring=pos_ring,
        gap_rc=gap_rc,
        tin=tin,
        tout=tout,
        heater_config_ring=heater_config,
        oplayer=oplayer,
        position_taper="no_bend"
    )
    return sr


# %% TCRing1DC: RingPulley1 different coupling
@gf.cell
def TCRing1DC(
        r_ring: float = 120,
        r_euler_false: float = r_euler_false,
        width_ring: float = 1,
        width_near1: float = 2,
        width_near2: float = 3,
        width_single: float = 1,
        angle_rc1: float = 20,
        angle_rc2: float = 30,
        angle_th: float = 60,
        length_taper: float = 150,
        length_total: float = 3000,
        pos_ring: float = 2000,
        gap_rc1: float = 1,
        gap_rc2: float = 4,
        tout: Component = taper_out,
        tin: Component = taper_in,
        oplayer: LayerSpec = LAYER.WG,
        heater_config:HeaterConfigClass=None,
) -> Component:
    """
    创建一个支持不同耦合参数的环形波导组件。
    该组件包含输入、输出、Through、Add 和 Drop 端口。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_euler_false: 欧拉弯曲的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near1: 第一个耦合波导的宽度（单位：um）。
        width_near2: 第二个耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc1: 第一个耦合角度（单位：度）。
        angle_rc2: 第二个耦合角度（单位：度）。
        angle_th: Through 端口的弯曲角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc1: 第一个耦合波导与环形波导的间距（单位：um）。
        gap_rc2: 第二个耦合波导与环形波导的间距（单位：um）。
        tout: 输出锥形波导组件。
        tin: 输入锥形波导组件。
        oplayer: 光学层定义。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        through: Through 端口。
        drop: Drop 端口。
        add: Add 端口。
        RingC: 环形波导的中心端口。
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
        HeaterConfig=heater_config,
    )
    taper_s2n_in.movex(pos_ring - length_taper).movey(
        tinring.ports['o1'].center[1] - taper_s2n_in.ports['o1'].center[1])
    ring.connect("Input", other=taper_s2n_in.ports["o2"], mirror=True)
    length_tout = abs(toutring_th.ports["o1"].center[0] - toutring_th.ports["o2"].center[0])
    # add
    taper_s2n_ad.connect("o2", other=ring.ports["Add"])
    toutring_ad.connect("o1", other=taper_s2n_ad.ports["o1"])
    toutring_ad.movex(length_total - length_tout - taper_s2n_ad.ports["o1"].center[0])
    # through
    bend_th1 = sr << GfCBendEuler(width=width_near1, layer=oplayer, angle=-angle_th,
                                  radius=r_euler_false * 1.5)
    bend_th2 = sr << GfCBendEuler(width=width_near1, layer=oplayer, angle=angle_th,
                                  radius=r_euler_false * 1.5)
    bend_th1.connect("o1", other=ring.ports["Through"])
    bend_th2.connect("o1", other=bend_th1.ports["o2"])
    # bend_th2.movey(0)
    gf.routing.route_single(sr, bend_th2.ports["o1"], bend_th1.ports["o2"], route_width=width_near1, layer=oplayer,
                            radius=150)
    taper_s2n_th.connect("o2", other=bend_th2.ports["o2"])
    toutring_th.connect("o1", other=taper_s2n_th.ports["o1"])
    toutring_th.movex(length_total - length_tout - taper_s2n_th.ports["o1"].center[0])
    # drop
    taper_s2n_dr.connect("o2", other=ring.ports["Drop"], mirror=True)
    taper_s2n_dr.mirror_x(taper_s2n_dr.ports["o2"].center[0])
    taper_s2n_dr.move([300, -30])
    bend_dr1 = sr << GfCBendEuler(width=width_near2, layer=oplayer, angle=-angle_th,
                                  radius=r_euler_false)
    bend_dr2 = sr << GfCBendEuler(width=width_near2, layer=oplayer, angle=angle_th + 180,
                                  radius=r_euler_false)
    bend_dr1.connect("o1", other=ring.ports["Drop"])
    bend_dr2.connect("o1", other=bend_dr1.ports["o2"])
    route_drop = gf.routing.route_single_sbend(sr, taper_s2n_dr.ports["o2"], bend_dr2.ports["o2"],
                                               cross_section=CS_near2)
    toutring_dr.connect("o1", other=taper_s2n_dr.ports["o1"])
    toutring_dr.movex(length_total - length_tout - taper_s2n_dr.ports["o1"].center[0])
    # route io
    route_io = gf.routing.route_bundle(sr,
                                       [tinring.ports["o2"], taper_s2n_ad.ports["o1"], taper_s2n_dr.ports["o1"],
                                        taper_s2n_th.ports["o1"]],
                                       [taper_s2n_in.ports["o1"], toutring_ad.ports["o1"], toutring_dr.ports["o1"],
                                        toutring_th.ports["o1"]],
                                       route_width=width_single, layer=oplayer, radius=150,
                                       )
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("through", port=toutring_th.ports["o2"])
    sr.add_port("drop", port=toutring_dr.ports["o2"])
    sr.add_port("add", port=toutring_ad.ports["o2"])
    Rcenter = [ring.ports["RingL"].center[i] / 2 + ring.ports["RingR"].center[i] / 2 for i in range(2)]
    sr.add_port("RingC", port=ring.ports["RingC"])
    sr.flatten()
    sr = remove_layer(sr,layer=(512,8))
    add_labels_to_ports(sr)
    return sr


# %% TCRing2: bend PulleyRing
@gf.cell
def TCRing2(
        r_ring: float = 120,
        width_ring: float = 1,
        width_near: float = 2,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 150,
        length_total: float = 10000,
        length_th_vertical: float = 101,
        pos_ring: float = 500,
        gap_rc: float = 1,
        tout: Component = taper_out,
        tin: Component = taper_in,
        oplayer: LayerSpec = LAYER.WG,
        heater_config:HeaterConfigClass=None,
) -> Component:
    """
    ---不建议使用---
    创建一个支持弯曲耦合的环形波导组件。
    该组件包含输入输出锥形波导。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        delta_io: 输入输出端口的偏移量（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        tout: 输出锥形波导组件。
        tin: 输入锥形波导组件。
        oplayer: 光学层定义。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
    """
    sr = TCRingT2(
        r_ring=r_ring,
        width_ring=width_ring,
        width_near=width_near,
        width_single=width_single,
        angle_rc=angle_rc,
        length_taper=length_taper,
        length_total=length_total,
        length_th_vertical=length_th_vertical,
        pos_ring=pos_ring,
        gap_rc=gap_rc,
        tin=tin,
        tout=tout,
        oplayer=oplayer,
        heater_config=heater_config,
    )
    return sr


# # %% TCRing2ES: bend PulleyRing + side ele
# def TCRing2ES(
#         r_ring: float = 120,
#         width_ring: float = 1,
#         width_near: float = 2,
#         width_ele: float = 5,
#         width_single: float = 1,
#         angle_rc: float = 20,
#         length_taper: float = 150,
#         length_total: float = 10000,
#         pos_ring: float = 500,
#         length_th_vertical=500,
#         delta_ele=5,
#         gap_rc: float = 1,
#         tout: Component = taper_out,
#         tin: Component = taper_in,
#         oplayer: LayerSpec = LAYER.WG,
#         elelayer: LayerSpec = LAYER.M1,
# ) -> [Component]:
#     """
#     创建一个支持侧边电极的环形波导组件。
#     该组件包含输入输出锥形波导和侧边电极。
#
#     参数：
#         r_ring: 环形波导的半径（单位：um）。
#         width_ring: 环形波导的宽度（单位：um）。
#         width_near: 耦合波导的宽度（单位：um）。
#         width_ele: 电极的宽度（单位：um）。
#         width_single: 输入输出波导的宽度（单位：um）。
#         angle_rc: 耦合角度（单位：度）。
#         length_taper: 锥形波导的长度（单位：um）。
#         length_total: 总长度（单位：um）。
#         pos_ring: 环形波导的位置（单位：um）。
#         delta_io: 输入输出端口的偏移量（单位：um）。
#         delta_ele: 电极与波导的间距（单位：um）。
#         gap_rc: 耦合波导与环形波导的间距（单位：um）。
#         tout: 输出锥形波导组件。
#         tin: 输入锥形波导组件。
#         oplayer: 光学层定义。
#         elelayer: 电极层定义。
#
#     返回：
#         [Component]: 生成的环形波导组件和电极组件。
#
#     端口：
#         input: 输入端口。
#         output: 输出端口。
#         RingC: 环形波导的中心端口。
#         EleLin: 左侧电极输入端口。
#         EleLout: 左侧电极输出端口。
#         EleRin: 右侧电极输入端口。
#         EleRout: 右侧电极输出端口。
#     """
#     s0 = TCRingT2(
#         r_ring=r_ring,
#         width_ring=width_ring,
#         width_near=width_near,
#         width_single=width_single,
#         angle_rc=angle_rc,
#         length_taper=length_taper,
#         length_total=length_total,
#         length_th_vertical=length_th_vertical,
#         pos_ring=pos_ring,
#         gap_rc=gap_rc,
#         tin=tin,
#         tout=tout,
#
#         oplayer=oplayer,
#         heatlayer=elelayer,
#     )
#     sr = GetFromLayer(CompOriginal=s0, OLayer=oplayer)
#     se = GetFromLayer(CompOriginal=s0, OLayer=elelayer)
#     return [sr, se]
#

# %% TCRing2_2: pulleyRing taper_s2n after output bend
@gf.cell
def TCRing2_2(
        r_ring: float = 120,
        width_ring: float = 1,
        width_near: float = 2,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 150,
        length_total: float = 10000,
        pos_ring: float = 500,
        gap_rc: float = 1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个支持弯曲耦合的环形波导组件，锥形波导位于弯曲后。
    该组件包含输入输出锥形波导。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        oplayer: 光学层定义。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
    """
    sr = TCRingT2(
        r_ring=r_ring,
        width_ring=width_ring,
        width_near=width_near,
        width_single=width_single,
        angle_rc=angle_rc,
        length_taper=length_taper,
        length_total=length_total,
        pos_ring=pos_ring,
        gap_rc=gap_rc,
        tin=tin,
        tout=tout,
        oplayer=oplayer,
        position_taper="after_bend"
    )
    return sr


# %% TCRing2_3: pulleyRing taper_s2n before output bend
@gf.cell
def TCRing2_3(
        r_ring: float = 120,
        width_ring: float = 1,
        width_near: float = 2,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 200,
        length_total: float = 10000,
        pos_ring: float = 500,
        gap_rc: float = 1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个支持弯曲耦合的环形波导组件，锥形波导位于弯曲前。
    该组件包含输入输出锥形波导。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_bend: 弯曲半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        oplayer: 光学层定义。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
    """
    sr = TCRingT2(
        r_ring=r_ring,
        width_ring=width_ring,
        width_near=width_near,
        width_single=width_single,
        angle_rc=angle_rc,
        length_taper=length_taper,
        length_total=length_total,
        pos_ring=pos_ring,
        gap_rc=gap_rc,
        tin=tin,
        tout=tout,
        oplayer=oplayer,
        position_taper="before_bend"
    )
    return sr


# %% TCRing3:couple angle could lager than 90,less than 180
@gf.cell
def TCRing3(
        r_ring: float = 120,
        r_bend: float = r_euler_true,
        width_ring: float = 1,
        width_near: float = 2,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 150,
        length_total: float = 10000,
        pos_ring: float = 500,
        gap_rc: float = 1,
        tout: Component = taper_out,
        tin: Component = taper_in,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个支持大角度耦合的环形波导组件。
    该组件包含输入输出锥形波导。
    耦合角度大于90 小于180
    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_bend: 弯曲半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        tout: 输出锥形波导组件。
        tin: 输入锥形波导组件。
        oplayer: 光学层定义。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
    """
    sr = gf.Component()
    tinring = sr << tin
    toutring = sr << tout
    ring = sr << RingPulley3(
        WidthRing=width_ring, WidthNear=width_near, GapRing=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        AngleCouple=angle_rc,
    )
    ring.connect("Input", other=tinring.ports["o2"], mirror=True)
    ring.movex(pos_ring)
    delta = toutring.ports["o2"].center - toutring.ports["o1"].center
    # input
    toutring.connect("o1", tinring.ports["o1"], mirror=True)
    toutring.movex(length_total - delta[0])
    taper_s2n1 = sr << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring.ports["Input"])
    delta = taper_s2n1.ports["o1"].center - tinring.ports["o2"].center
    str_tin2r = sr << GfCStraight(length=delta[0], layer=oplayer, width=width_single)
    str_tin2r.connect("o1", tinring.ports["o2"])
    # output
    taper_s2n2 = sr << gf.c.taper(width1=width_near, width2=width_single, length=length_taper, layer=oplayer)
    taper_s2n2.connect("o1", ring.ports["Through"])
    bend_out2 = sr << GfCBendEuler(width=width_single, layer=oplayer, angle=180, radius=r_bend, p=1)
    bend_out2.connect("o1", taper_s2n2.ports["o2"])
    delta = bend_out2.ports["o2"].center - toutring.ports["o2"].center
    toutring.movey(delta[1])
    str_tout2r = gf.routing.get_bundle(bend_out2.ports["o2"], toutring.ports["o1"], layer=oplayer, width=width_single
                                       , radius=r_euler_false)
    for route in str_tout2r:
        sr.add(route.references)
    # sr_cld1 = gf.geometry.offset(sr, distance=width_cld, layer=LAYER.CLD2)
    # sr_cld2 = gf.geometry.offset(sr_cld1, distance=-0.8, layer=LAYER.CLD2)
    # sr.add_ref(sr_cld2)
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("output", port=toutring.ports["o1"])
    sr.add_port("RingC", port=toutring.ports["o1"],
                center=ring.ports["RingL"].center / 2 + ring.ports["RingR"].center / 2)
    return sr


# %% TCRing4: couple angle could lager than 180
@gf.cell
def TCRing4(
        r_ring: float = 120,
        width_ring: float = 1,
        width_near: float = 2,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 150,
        length_total: float = 10000,
        pos_ring: float = 500,
        gap_rc: float = 1,
        tout: Component = taper_out,
        tin: Component = taper_in,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个支持超大角度耦合的环形波导组件。
    该组件包含输入输出锥形波导。
    耦合角度大于180
    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_bend: 弯曲半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        tout: 输出锥形波导组件。
        tin: 输入锥形波导组件。
        oplayer: 光学层定义。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
    """
    sr = gf.Component()
    tinring = sr << tin
    toutring = sr << tout
    ring = sr << RingPulley4(
        WidthRing=width_ring, WidthNear=width_near, GapRing=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        AngleCouple=angle_rc,
    )
    ring.connect("Input", other=tinring.ports["o2"], mirror=True)
    ring.movex(pos_ring)
    delta = toutring.ports["o2"].center - toutring.ports["o1"].center
    # input
    toutring.connect("o1", tinring.ports["o1"], mirror=True)
    toutring.movex(length_total - delta[0])
    taper_s2n1 = sr << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring.ports["Input"])
    delta = taper_s2n1.ports["o1"].center - tinring.ports["o2"].center
    str_tin2r = sr << GfCStraight(length=delta[0], layer=oplayer, width=width_single)
    str_tin2r.connect("o1", tinring.ports["o2"])
    # output
    taper_s2n2 = sr << gf.c.taper(width1=width_near, width2=width_single, length=length_taper, layer=oplayer)
    taper_s2n2.connect("o1", ring.ports["Through"])
    delta = taper_s2n2.ports["o2"].center - toutring.ports["o2"].center
    toutring.movey(delta[1])
    str_tout2r = gf.routing.get_bundle(taper_s2n2.ports["o2"], toutring.ports["o1"], layer=oplayer, width=width_single
                                       , radius=r_euler_false)
    for route in str_tout2r:
        sr.add(route.references)
    # sr_cld1 = gf.geometry.offset(sr, distance=width_cld, layer=LAYER.CLD2)
    # sr_cld2 = gf.geometry.offset(sr_cld1, distance=-0.8, layer=LAYER.CLD2)
    # sr.add_ref(sr_cld2)
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("output", port=toutring.ports["o1"])
    sr.add_port("RingC", port=toutring.ports["o1"],
                center=ring.ports["RingL"].center / 2 + ring.ports["RingR"].center / 2)
    return sr


# % TCFingerRing1: taper before bend out
@gf.cell
def TCFingerRing1(
        r_ring: float = 120,
        r_side: float = 120,
        r_euler_true: float = r_euler_true,
        width_ring: float = 1,
        width_near: float = 2,
        width_single: float = 1,
        angle_rc: float = 20,
        angle_side: float = 190,
        length_taper: float = 150,
        length_total: float = 10000,
        length_th: float = 10,
        length_side: float = 120,
        length_couple: float = 120,
        length_connect: float = 120,
        pos_ring: float = 500,
        gap_rc: float = 1,
        heaterconfig: HeaterConfigClass = None,
        tin: Component = taper_in,
        tout: Component = taper_out,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个支持手指耦合的环形波导组件。
    该组件包含输入输出锥形波导和手指耦合结构。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_side: 侧边弯曲的半径（单位：um）。
        r_euler_true: 欧拉弯曲的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        angle_side: 侧边弯曲角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        length_th: 直波导的长度（单位：um）。
        length_side: 侧边波导的长度（单位：um）。
        length_couple: 耦合波导的长度（单位：um）。
        length_connect: 连接波导的长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        delta_io: 输入输出端口的偏移量（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        is_heat: 是否添加加热器。
        is_ad: 是否添加 Add/Drop 端口。
        oplayer: 光学层定义。
        heatlayer: 加热层定义。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
    """
    sr = gf.Component()
    ring = gf.Component()
    ## ring
    ring0 = ring << RingFinger(
        WidthRing=width_ring, WidthNear=width_near, LengthSide=length_side, LengthCouple=length_couple,
        LengthConnect=length_connect,
        GapRing=gap_rc, AngleCouple=angle_rc, AngleSide=angle_side, RadiusCouple=r_ring, RadiusSide=r_side,
        oplayer=oplayer,HeaterConfig=heaterconfig,
    )
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n2 = ring << gf.c.taper(width1=width_near, width2=width_single, length=length_taper, layer=oplayer)
    bend_thr1 = ring << GfCBendEuler(width=width_single, radius=r_euler_true, layer=oplayer, angle=90, )
    str_thr = ring << GfCStraight(width=width_single, length=length_th, layer=oplayer)
    bend_thr2 = ring << GfCBendEuler(width=width_single, radius=r_euler_true, layer=oplayer, angle=-90)
    ## input & output near ring
    taper_s2n1.connect("o2", ring0.ports["Input"])
    taper_s2n2.connect("o1", other=ring0.ports["Through"])
    bend_thr1.connect("o1", other=taper_s2n2.ports["o2"])
    str_thr.connect("o1", other=bend_thr1.ports["o2"])
    bend_thr2.connect("o1", other=str_thr.ports["o2"])

    ring.add_port("Input", port=ring0.ports["Input"])
    ring.add_port("Con1", port=ring0.ports["Con1"])
    ring.add_port("Con2", port=ring0.ports["Con2"])
    ring.add_port("Ts2n1_o1", port=taper_s2n1.ports["o1"])
    ring.add_port("Ts2n2_o2", port=bend_thr2.ports["o2"])
    for port in ring0.ports:
        if "Heat" in port.name:
            ring.add_port(port.name, port=port)
    Ring = sr << ring
    if tin != None:
        tinring = sr << tin
        Ring.connect("Input", other=tinring.ports["o2"], allow_width_mismatch=True, mirror=True)
        Ring.movex(pos_ring)
        delta = Ring.ports["Ts2n1_o1"].center[0] - tinring.ports["o2"].center[0]
        str_tin2r = sr << GfCStraight(length=delta, layer=oplayer, width=width_single)
        str_tin2r.connect("o1", tinring.ports["o2"])
        sr.add_port("input", port=tinring.ports["o1"])
    if tout != None:
        toutring = sr << tout
        toutring.connect("o1", other=Ring.ports["Ts2n2_o2"], allow_width_mismatch=True, mirror=True)
        toutring.movex(length_total - toutring.ports["o2"].center[0])
        str_tout2r = gf.routing.route_single(sr,toutring.ports["o1"], Ring.ports["Ts2n2_o2"], layer=oplayer,
                                           route_width=width_single, radius=r_euler_true)
        sr.add_port("output", port=toutring.ports["o2"])

    sr.add_port("RingC",
                center=[Ring.ports["Con1"].center[0] / 2 + ring.ports["Con2"].center[0] / 2,Ring.ports["Con1"].center[1] / 2 + ring.ports["Con2"].center[1] / 2],
                layer=oplayer,width=1,
                )
    for port in Ring.ports:
        if "Heat" in port.name:
            sr.add_port(port.name, port=port)
    return sr

# TCRingT1: TCRing use RingPulleyT1
@gf.cell
def TCRingT1(
        r_ring: float = 120,
        r_euler_min: float = r_euler_true,
        width_ring: float = 1,
        width_near: float = 2,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 150,
        length_total: float = 10000,
        length_th_horizontal: float = 10,
        length_th_vertical: float = 10,
        length_busheater: float = 1,
        pos_ring: float = 500,
        gap_rc: float = 1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        is_ad: bool = False,
        oplayer: LayerSpec = LAYER.WG,
        direction_heater: str = "up",
        position_taper: str = "before_bend",  # 控制锥形波导的位置
        heater_config_ring: HeaterConfigClass = None,  # 控制加热器类型
        heater_config_bus: HeaterConfigClass = None,
) -> Component:
    """
    创建一个环形波导组件，支持通过 position_taper 参数控制锥形波导的位置，并通过 type_heater 参数控制加热器类型。
    使用 RingPulleyT1 型的微环结构。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_euler_min: 欧拉弯曲的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        length_th_horizontal: 水平直波导的长度（单位：um）。
        length_th_vertical: 垂直直波导的长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        gap_heat: 加热器与波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        is_heat: 是否添加加热器。
        is_ad: 是否添加 Add/Drop 端口。
        oplayer: 光学层定义。
        heatlayer: 加热层定义。
        position_taper: 锥形波导的位置，支持 "before_bend"（默认）、"after_bend"、"between_bend"、"no_bend"。
        type_heater: 加热器类型，支持 "default"（默认）、"side"（侧边加热）、"bothside"（两侧加热）。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
        RingInput: 环形波导的输入端口。
        RingL: 环形波导的左侧端口。
        RingR: 环形波导的右侧端口。
    """
    sr = gf.Component()
    ring = gf.Component()
    ring0 = ring << RingPulleyT1(
        WidthRing=width_ring, WidthNear=width_near, GapRing=gap_rc,
        RadiusRing=r_ring, AngleCouple=angle_rc, DirectionHeater=direction_heater,
        IsAD=is_ad, oplayer=oplayer,HeaterConfig=heater_config_ring,
    )
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring0.ports["Input"])
    taper_s2n2 = ring << gf.c.taper(width1=width_near, width2=width_single, length=length_taper, layer=oplayer)

    # 根据 position_taper 参数调整锥形波导的位置
    if position_taper == "before_bend":
        bend_thr1 = ring << GfCBendEuler(width=width_single, radius=r_euler_min, layer=oplayer, angle=90,
                                         with_arc_floorplan=False)
        bend_thr2 = ring << GfCBendEuler(width=width_single, radius=r_euler_min, layer=oplayer, angle=-90,
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
        bend_thr1 = ring << GfCBendEuler(width=width_near, radius=r_euler_min, layer=oplayer, angle=90,
                                         with_arc_floorplan=False)
        bend_thr2 = ring << GfCBendEuler(width=width_near, radius=r_euler_min, layer=oplayer, angle=-90,
                                         with_arc_floorplan=False)
        str_th_horizontal = ring << GfCStraight(width=width_near, length=length_th_horizontal, layer=oplayer)
        str_th_vertical = ring << GfCStraight(width=width_near, length=length_th_vertical, layer=oplayer)

        str_th_horizontal.connect("o1", ring0.ports["Through"])
        bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
        str_th_vertical.connect("o1", other=bend_thr1.ports["o2"])
        bend_thr2.connect("o1", other=str_th_vertical.ports["o2"])
        taper_s2n2.connect("o1", other=bend_thr2.ports["o2"])

        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=taper_s2n2.ports["o2"])
    elif position_taper == "between_bend":
        bend_thr1 = ring << GfCBendEuler(width=width_near, radius=r_euler_min, layer=oplayer, angle=90,
                                         with_arc_floorplan=False)
        bend_thr2 = ring << GfCBendEuler(width=width_single, radius=r_euler_min, layer=oplayer, angle=-90,
                                         with_arc_floorplan=False)
        str_th_horizontal = ring << GfCStraight(width=width_near, length=length_th_horizontal, layer=oplayer)
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

    ring.add_port("RingInput", port=ring0.ports["Input"])
    ring.add_port("RingL", port=ring0.ports["RingL"])
    ring.add_port("RingR", port=ring0.ports["RingR"])
    for port in ring0.ports:
        if "Heat" in port.name:
            ring.add_port(port.name, port=ring0.ports[port.name])
        if "Add" in port.name:
            ring.add_port(port.name, port=ring0.ports[port.name])
        if "Drop" in port.name:
            ring.add_port(port.name, port=ring0.ports[port.name])
    Ring = sr << ring

    # input
    tinring = sr << tin
    Ring.connect("o1", other=tinring.ports["o2"], allow_width_mismatch=True, mirror=True)
    Ring.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])

    # output
    toutring = sr << tout
    delta = np.array(toutring.ports["o2"].center) - np.array(toutring.ports["o1"].center)
    toutring.connect("o1", other=Ring.ports["o2"])
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("output", port=toutring.ports["o2"])

    # route
    gf.routing.route_single(sr, toutring.ports["o1"],Ring.ports["o2"],
                                         layer=oplayer, route_width=width_single, radius=r_euler_min)
    gf.routing.route_single(sr, Ring.ports["o1"],tinring.ports["o2"],
                                         layer=oplayer, route_width=width_single, radius=r_euler_min)
    sr.add_port("RingC", width=width_single, layer=oplayer,
                center=np.array(Ring.ports["RingL"].center) / 2 + np.array(Ring.ports["RingR"].center) / 2)
    for port in Ring.ports:
        if "Heat" in port.name:
            sr.add_port("Ring"+port.name, port=Ring.ports[port.name])
        if "Add" in port.name:
            sr.add_port(port.name, port=Ring.ports[port.name])
        if "Drop" in port.name:
            sr.add_port(port.name, port=Ring.ports[port.name])
    if heater_config_bus:
        pbusheat = gf.path.straight(length=length_busheater)
        cbusheat = sr << DifferentHeater(pbusheat,WidthWG=width_single,HeaterConfig=heater_config_bus)
        cbusheat.connect("HeatIn",other=Ring.ports["o1"],allow_width_mismatch=True, allow_layer_mismatch=True)
        for port in cbusheat.ports:
            if "Heat" in port.name:
                sr.add_port("Bus"+port.name, port=port)
    sr = remove_layer(sr, layer=(512, 8))
    add_labels_to_ports(sr)
    return sr


# TCRingT2
@gf.cell
def TCRingT2(
        r_ring: float = 120,
        r_euler_min: float = r_euler_true,
        width_ring: float = 1,
        width_near: float = 10,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 150,
        length_total: float = 2000,
        length_th_horizontal: float = 10,
        length_th_vertical: float = 10,
        length_busheater: float = 100,
        pos_ring: float = 500,
        gap_rc: float = 1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        oplayer: LayerSpec = LAYER.WG,
        position_taper: str = "before_bend",  # 控制锥形波导的位置
        heater_config_ring: HeaterConfigClass = None,  # 控制加热器类型
        heater_config_bus: HeaterConfigClass = None,
        direction_heater: str = "up",
) -> Component:
    """
    创建一个环形波导组件，支持通过 position_taper 参数控制锥形波导的位置，并通过 type_heater 参数控制加热器类型。
    使用 RingPulleyT2 型的微环结构。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        length_th_horizontal: 水平直波导的长度（单位：um）。
        length_th_vertical: 垂直直波导的长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        delta_io: 输入输出端口的偏移量（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        gap_heat: 加热器与波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        is_heat: 是否添加加热器。
        is_ad: 是否添加 Add/Drop 端口。
        oplayer: 光学层定义。
        heatlayer: 加热层定义。
        position_taper: 锥形波导的位置，支持 "before_bend"（默认）、"after_bend"、"between_bend"。
        type_heater: 加热器类型，支持 "default"（默认）、"side"（侧边加热）、"bothside"（两侧加热）、"snake"（蛇形加热）

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
        RingInput: 环形波导的输入端口。
        RingL: 环形波导的左侧端口。
        RingR: 环形波导的右侧端口。
    """
    sr = gf.Component()
    ring = gf.Component()
    ring0 = ring << RingPulleyT2(
        WidthRing=width_ring, WidthNear=width_near, GapRing=gap_rc,
        RadiusRing=r_ring, AngleCouple=angle_rc, oplayer=oplayer, HeaterConfig=heater_config_ring,DirectionHeater=direction_heater,
    )
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_near, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring0.ports["Input"])
    taper_s2n2 = ring << gf.c.taper(width1=width_near, width2=width_single, length=length_taper, layer=oplayer)

    # 根据 position_taper 参数调整锥形波导的位置
    if position_taper == "before_bend":
        bend_thr1 = ring << GfCBendEuler(width=width_single, radius= r_euler_min,
                                         layer=oplayer, angle=-90, with_arc_floorplan=False)
        str_th_vertical = ring << GfCStraight(width=width_single, length=length_th_vertical, layer=oplayer)
        taper_s2n2.connect("o1", other=ring0.ports["Through"])
        str_th_vertical.connect("o1", other=taper_s2n2.ports["o2"])
        bend_thr1.connect("o1", other=str_th_vertical.ports["o2"])
        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=bend_thr1.ports["o2"])

    elif position_taper == "after_bend":
        bend_thr1 = ring << GfCBendEuler(width=width_near, radius= r_euler_min,
                                         layer=oplayer, angle=-90, with_arc_floorplan=False)
        str_th_vertical = ring << GfCStraight(width=width_near, length=length_th_vertical, layer=oplayer)
        str_th_vertical.connect("o1", other=ring0.ports["Through"])
        bend_thr1.connect("o1", other=str_th_vertical.ports["o2"])
        taper_s2n2.connect("o1", other=bend_thr1.ports["o2"])
        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=taper_s2n2.ports["o2"])
    else:
        raise ValueError("position_taper 必须是 'before_bend' 或 'after_bend'")

    ring.add_port("Input", port=ring0.ports["Input"])
    ring.add_port("RingL", port=ring0.ports["RingL"])
    ring.add_port("RingR", port=ring0.ports["RingR"])
    ring.add_port("RingC", port=ring0.ports["RingC"])
    for port in ring0.ports:
        if "Heat" in port.name:
            ring.add_port(port.name, port=ring0.ports[port.name])
    Ring = sr << ring

    # input
    tinring = sr << tin
    Ring.connect("o1", other=tinring.ports["o2"], allow_width_mismatch=True, mirror=True)
    Ring.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])
    gf.routing.route_single(sr,tinring.ports["o2"],Ring.ports["o1"],layer=oplayer, route_width=width_single,radius = r_ring)
    # output
    toutring = sr << tout
    # delta = toutring.ports["o2"].center - toutring.ports["o1"].center
    toutring.connect("o1", other=Ring.ports["o2"])
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("output", port=toutring.ports["o2"])

    # route
    gf.routing.route_single(sr,toutring.ports["o1"],Ring.ports["o2"],
                                       layer=oplayer, route_width=width_single,radius = r_ring)
    sr.add_port("RingC", port=Ring.ports["RingC"])
    sr.add_port("RingInput", port=Ring.ports["o1"])
    for port in Ring.ports:
        if "Heat" in port.name:
            sr.add_port(port.name, port=Ring.ports[port.name])
    if heater_config_bus:
        pbusheat = gf.path.straight(length=length_busheater)
        cbusheat = sr << DifferentHeater(pbusheat,WidthWG=width_single, HeaterConfig=heater_config_bus)
        cbusheat.connect("HeatIn", other=Ring.ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True)
        for port in cbusheat.ports:
            if "Heat" in port.name:
                sr.add_port("Bus" + port.name, port=port)
    sr = remove_layer(sr,layer=(512,8))
    add_labels_to_ports(sr)
    return sr


@gf.cell
def TCRingDCouple(
        r_ring: float = 120,
        r_euler_min: float = r_euler_true,
        width_ring: float = 1,
        width_near: float = 2,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 200,
        length_total: float = 10000,
        length_th_horizontal: float = 20,
        pos_ring: float = 500,
        gap_rc: float = 1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        oplayer: LayerSpec = LAYER.WG,
        heater_config_ring: HeaterConfigClass = None,
        heater_config_couple: HeaterConfigClass = None,
) -> Component:
    """
    创建一个二次耦合的环形波导组件，支持通过 position_taper 参数控制锥形波导的位置，并通过 type_heater 参数控制加热器类型。
    使用 RingPulleyT1 型的微环结构。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_euler_min: 欧拉弯曲的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        length_th_horizontal: 水平直波导的长度（单位：um）。
        length_th_vertical: 垂直直波导的长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        gap_heat: 加热器与波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        is_heat: 是否添加加热器。
        is_ad: 是否添加 Add/Drop 端口。
        oplayer: 光学层定义。
        heatlayer: 加热层定义。
        position_taper: 锥形波导的位置，支持 "before_bend"（默认）、"after_bend"、"between_bend"、"no_bend"。
        type_heater: 加热器类型，支持 "default"（默认）、"side"（侧边加热）、"bothside"（两侧加热）。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
        RingInput: 环形波导的输入端口。
        RingL: 环形波导的左侧端口。
        RingR: 环形波导的右侧端口。
    """
    sr = gf.Component()
    ring = gf.Component("Ring")
    ring0 = ring << RingPulleyT1(
        WidthRing=width_ring, WidthNear=width_near, GapRing=gap_rc,
        RadiusRing=r_ring, AngleCouple=angle_rc,
        IsAD=True, oplayer=oplayer, HeaterConfig=heater_config_ring,
    )

    # bend 2 bend
    str_i2b = ring << GfCStraight(width=width_near, length=length_th_horizontal, layer=oplayer)
    str_d2b = ring << GfCStraight(width=width_near, length=length_th_horizontal, layer=oplayer)
    str_i2b.connect("o1", other=ring0.ports["Input"])
    str_d2b.connect("o1", other=ring0.ports["Drop"])
    bend_input = ring << gf.c.bend_euler(width=width_near, radius=r_euler_min, layer=oplayer, angle=-90,
                                      with_arc_floorplan=False)
    bend_drop = ring << gf.c.bend_euler(width=width_near, radius=r_euler_min, layer=oplayer, angle=90,
                                     with_arc_floorplan=False)
    bend_input.connect("o1", other=str_i2b.ports["o2"])
    bend_drop.connect("o1", other=str_d2b.ports["o2"])
    path_near = gf.path.straight(abs(bend_input.ports["o2"].center[1] - bend_drop.ports["o2"].center[1]))
    str_near = ring << gf.path.extrude(p=path_near, width=width_near, layer=oplayer)
    heat_near = ring << DifferentHeater(path_near, WidthWG=width_near,HeaterConfig=heater_config_couple)
    heat_near.connect('HeatIn', bend_input.ports['o2'], allow_width_mismatch=True, allow_layer_mismatch=True)
    str_near.connect('o1', bend_input.ports['o2'])

    bend_through = ring << gf.c.bend_euler(width=width_near, radius=r_euler_min, layer=oplayer, angle=-180,
                                        with_arc_floorplan=False)
    bend_through.connect("o1", ring0.ports["Through"])
    taper_through = ring << gf.c.taper(width1=width_near, width2=width_single, layer=oplayer, length=length_taper)
    taper_through.connect("o1", bend_through.ports["o2"])
    taper_add = ring << gf.c.taper(width1=width_near, width2=width_single, layer=oplayer, length=length_taper)
    taper_add.connect("o1", ring0.ports["Add"])
    ring.add_port("RingIn", port=taper_through.ports["o2"])
    ring.add_port("RingOut", port=taper_add.ports["o2"])
    ring.add_port("RingL", port=ring0.ports["RingL"])
    ring.add_port("RingR", port=ring0.ports["RingR"])
    # ring.show()
    for port in ring0.ports:
        if "Heat" in port.name:
            ring.add_port("R" + port.name, port=port)
    for port in heat_near.ports:
        if "Heat" in port.name:
            ring.add_port("N" + port.name, port=port)
    Ring = sr << ring

    # input
    tinring = sr << tin
    Ring.connect("RingIn", other=tinring.ports["o2"], allow_width_mismatch=True, mirror=True)
    Ring.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])

    # output
    toutring = sr << tout
    toutring.connect("o1", other=Ring.ports["RingOut"])
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("output", port=toutring.ports["o2"])

    # route
    str_tout2r = gf.routing.route_bundle(sr,[tinring.ports["o2"]],[Ring.ports["RingIn"]],
                                       layer=oplayer, route_width=width_single, radius=r_euler_min)
    str_tout2r = gf.routing.route_bundle(sr,[Ring.ports["RingOut"]],[toutring.ports["o1"]],
                                       layer=oplayer, route_width=width_single, radius=r_euler_min)
    sr.add_port("RingC", width=width_single, layer=oplayer,
                center=np.array(Ring.ports["RingL"].center) / 2 + np.array(Ring.ports["RingR"].center) / 2)
    for port in Ring.ports:
        if "Heat" in port.name:
            sr.add_port(port.name, port=port)
    # sr = remove_layer(sr, layer=(512, 8))
    # add_labels_to_ports(sr)
    return sr


__all__ = ['TCRing', 'TCRing2', 'TCRing3', 'TCRing4', 'TCRing1DC', 'TCRing2_2', 'TCRing2_3',
           'TCRing1AD', 'TCRing1_3', 'TCFingerRing1', 'TCRingT1',
           'TCRingT2', 'TCRingDCouple']
