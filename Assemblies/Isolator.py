"""环形隔离器原型（单环 Add-Drop + 监视支路，ComponentAllAngle 版）。
"""
from ..Core.BasicDefine import *
from ..Devices.Ring import *


# %% SingleRingIsolator0: SingleRingIsolator:ADD-DROP ring + monitor
@gf.vcell
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
创建"单 Add-Drop 环 + 三条输出支路"的隔离器原型（ComponentAllAngle 版）。

结构：输入 tin → 主总线 → RingPulley1DC（上下耦合参数不同）
      → through / drop / add 三路输出，各接 tout；length_total 只用于把
      三路输出拉到统一长度，方便拼测试小片。

端口:
    input, through, drop, add: 光学端口。
    RingC: 环中心参考点（仅定位用）。
"""
    if tin is None:
        tin = GfCStraight(width=width_single, length=10, layer=oplayer)
    if tout is None:
        tout = GfCStraight(width=width_single, length=10, layer=oplayer)
    sr = ComponentAllAngle()
    # Section CrossSection
    S_near1 = gf.Section(width=width_near1, layer=oplayer, port_names=("o1", "o2"))
    CS_near1 = gf.CrossSection(sections=[S_near1])
    S_near2 = gf.Section(width=width_near2, layer=oplayer, port_names=("o1", "o2"))
    CS_near2 = gf.CrossSection(sections=[S_near2])
    # component
    tinring = sr.create_vinst(tin)
    toutring_th = sr.create_vinst(tout)
    toutring_ad = sr.create_vinst(tout)
    toutring_dr = sr.create_vinst(tout)
    taper_s2n1 = gf.c.taper(width1=width_single, width2=width_near1, length=length_taper, layer=oplayer)
    taper_s2n2 = gf.c.taper(width1=width_single, width2=width_near2, length=length_taper, layer=oplayer)
    taper_s2n_in = sr.create_vinst(taper_s2n1)
    taper_s2n_th = sr.create_vinst(taper_s2n1)
    taper_s2n_ad = sr.create_vinst(taper_s2n2)
    taper_s2n_dr = sr.create_vinst(taper_s2n2)
    ring = sr.create_vinst(RingPulley1DC(
        WidthRing=width_ring, oplayer=oplayer, RadiusRing=r_ring,
        WidthNear1=width_near1, GapRing1=gap_rc1, AngleCouple1=angle_rc1,
        WidthNear2=width_near2, GapRing2=gap_rc2, AngleCouple2=angle_rc2,
        HeaterConfig=HeaterConfigClass(WidthHeat=width_heat)
    ))
    taper_s2n_in.movex(pos_ring - length_taper)
    ring.connect("Input", other=taper_s2n_in.ports["o2"], mirror=True)
    length_tout = abs(toutring_th.ports["o1"].center[0] - toutring_th.ports["o2"].center[0])
    # add
    taper_s2n_ad.connect("o2", other=ring.ports["Add"])
    toutring_ad.connect("o1", other=taper_s2n_ad.ports["o1"])
    toutring_ad.movex(length_total - length_tout - taper_s2n_ad.ports["o1"].center[0])
    # through
    bend_th1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=-angle_th1,
                                    radius=r_euler_false * 1.2))
    bend_th2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=angle_th1,
                                    radius=r_euler_false * 1.2))
    str_th1 = sr.create_vinst(GfCStraight(width=width_near1, layer=oplayer, length=length_thadd))
    bend_th1.connect("o1", other=ring.ports["Through"])
    str_th1.connect("o1", other=bend_th1.ports["o2"])
    bend_th2.connect("o1", other=str_th1.ports["o2"])
    # 旧版这里再把 bend_th2.o1 路由回 bend_th1.o2，和 str_th1 重复；
    # 直接删掉，避免多画一条与已有波导重合的回路。
    taper_s2n_th.connect("o2", other=bend_th2.ports["o2"])
    toutring_th.connect("o1", other=taper_s2n_th.ports["o1"])
    toutring_th.movex(length_total - length_tout - taper_s2n_th.ports["o1"].center[0])
    # drop：Ring Drop -> bend_dr1 -> bend_dr2 -> taper -> toutring
    bend_dr1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=-angle_dr,
                                    radius=r_euler_false * 1.2))
    bend_dr2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=angle_dr,
                                    radius=r_euler_false * 1.2))
    bend_dr1.connect("o1", other=ring.ports["Drop"])
    bend_dr2.connect("o1", other=bend_dr1.ports["o2"])
    # 旧版把 taper_s2n_dr 也接在 Drop 上，再把它的 o2 路由回 bend_dr2.o2，
    # 形成一个闭合回路；正确接法是 taper 直接串在 bend_dr2 之后。
    taper_s2n_dr.connect("o2", other=bend_dr2.ports["o2"])
    toutring_dr.connect("o1", other=taper_s2n_dr.ports["o1"])
    toutring_dr.movex(length_total - length_tout - taper_s2n_dr.ports["o1"].center[0])
    # route io
    route_off_grid(sr, tinring.ports["o2"], taper_s2n_in.ports["o1"], width=width_single, layer=oplayer, radius=r_euler_false)
    # add/drop/through 的 taper 与 tout 已在上面直接 connect，旧版又各画了一条
    # 同位置路由，属于重复几何，删除。
    # add_port
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("through", port=toutring_th.ports["o2"])
    sr.add_port("drop", port=toutring_dr.ports["o2"])
    sr.add_port("add", port=toutring_ad.ports["o2"])
    Rcenter = [ring.ports["RingL"].center[i] / 2 + ring.ports["RingR"].center[i] / 2 for i in range(2)]
    sr.add_port("RingC", port=sr.ports["input"], center=Rcenter)
    add_labels_to_ports(sr)
    return sr


# %% SingleRingIsolator1: SingleRingIsolator:ADD-DROP ring + monitor
@gf.vcell
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
        length_monicouple=250,
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
第二个隔离器原型：与 ``SingleRingIsolator0`` 相同的单环 Add-Drop 结构，
但耦合间隙/角度不同，用于对比不同 gap 下的隔离比。

端口: input, through, drop, add, RingC。
"""
    if tin is None:
        tin = GfCStraight(width=width_single, length=10, layer=oplayer)
    if tout is None:
        tout = GfCStraight(width=width_single, length=10, layer=oplayer)
    sr = ComponentAllAngle()
    # Section CrossSection
    S_near1 = gf.Section(width=width_near1, layer=oplayer, port_names=("o1", "o2"))
    CS_near1 = gf.CrossSection(sections=[S_near1])
    S_near2 = gf.Section(width=width_near2, layer=oplayer, port_names=("o1", "o2"))
    CS_near2 = gf.CrossSection(sections=[S_near2])
    # component
    tinring = sr.create_vinst(tin)
    toutring_th = sr.create_vinst(tout)
    toutring_ad = sr.create_vinst(tout)
    toutring_dr = sr.create_vinst(tout)
    taper_s2n1 = gf.c.taper(width1=width_single, width2=width_near1, length=length_taper, layer=oplayer)
    taper_s2n2 = gf.c.taper(width1=width_single, width2=width_near2, length=length_taper, layer=oplayer)
    taper_s2n_in = sr.create_vinst(taper_s2n1)
    taper_s2n_th = sr.create_vinst(taper_s2n1)
    taper_s2n_ad = sr.create_vinst(taper_s2n2)
    taper_s2n_dr = sr.create_vinst(taper_s2n2)
    ring = sr.create_vinst(RingPulley1DC(
        WidthRing=width_ring, oplayer=oplayer, RadiusRing=r_ring,
        WidthNear1=width_near1, GapRing1=gap_rc1, AngleCouple1=angle_rc1,
        WidthNear2=width_near2, GapRing2=gap_rc2, AngleCouple2=angle_rc2,
        HeaterConfig=HeaterConfigClass(WidthHeat=width_heat)
    ))
    taper_s2n_in.movex(pos_ring - length_taper)
    ring.connect("Input", other=taper_s2n_in.ports["o2"], mirror=True)
    length_tout = abs(toutring_th.ports["o1"].center[0] - toutring_th.ports["o2"].center[0])
    # add
    taper_s2n_ad.connect("o2", other=ring.ports["Add"])
    toutring_ad.connect("o1", other=taper_s2n_ad.ports["o1"])
    toutring_ad.movex(length_total - length_tout - taper_s2n_ad.ports["o1"].center[0])
    # through
    bend_th1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=-angle_th1,
                                    radius=r_euler_false * 1.2))
    bend_th2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=angle_th1,
                                    radius=r_euler_false * 1.2))
    bend_th1.connect("o1", other=ring.ports["Through"])
    bend_th2.connect("o1", other=bend_th1.ports["o2"])
    # 旧版把 bend_th2.o1 路由回 bend_th1.o2，和 bend_th1->bend_th2 直连重复，删除。
    taper_s2n_th.connect("o2", other=bend_th2.ports["o2"])
    toutring_th.connect("o1", other=taper_s2n_th.ports["o1"])
    toutring_th.movex(length_total - length_tout - taper_s2n_th.ports["o1"].center[0])
    # drop：Ring Drop -> bend_dr1 -> bend_dr2 -> taper -> toutring
    bend_dr1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=-angle_th2,
                                    radius=r_euler_false * 1.2))
    bend_dr2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=angle_th2,
                                    radius=r_euler_false * 1.2))
    bend_dr1.connect("o1", other=ring.ports["Drop"])
    bend_dr2.connect("o1", other=bend_dr1.ports["o2"])
    # 旧版 taper 也接在 Drop 上，再与 bend_dr2 路由成环；改为直接串接。
    taper_s2n_dr.connect("o2", other=bend_dr2.ports["o2"])
    toutring_dr.connect("o1", other=taper_s2n_dr.ports["o1"])
    toutring_dr.movex(length_total - length_tout - taper_s2n_dr.ports["o1"].center[0])
    # monitor
    str_moni = sr.create_vinst(GfCStraight(length=length_monicouple, width=width_single, layer=oplayer))
    str_moni.connect("o1", other=taper_s2n_in.ports["o1"])
    str_moni.movey(-width_single - gap_mc)
    taper_moni = sr.create_vinst(OffsetRamp(width1=width_single, width2=0.002, offset=width_single / 2, length=50, layer=oplayer))
    taper_moni.connect("o1", other=str_moni.ports["o1"])
    bend_moni = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_single, radius=r_euler_moni, layer=oplayer, angle=90))
    bend_moni.connect("o1", other=str_moni.ports["o2"])
    toutring_mn = sr.create_vinst(tout)
    toutring_mn.connect("o1", other=toutring_dr.ports["o1"], mirror=True)
    toutring_mn.movey(-127)
    str_moni_out = sr.create_vinst(GfCStraight(width=width_single,
                                    length=toutring_mn.ports["o1"].center[0] - taper_s2n_dr.ports["o1"].center[0]))
    str_moni_out.connect("o2", other=toutring_mn.ports["o1"])
    # route io
    CS_single = gf.CrossSection(sections=[gf.Section(width=width_single, layer=oplayer, port_names=("o1", "o2"))])
    route_off_grid(sr, tinring.ports["o2"], taper_s2n_in.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    # add/drop/through 的 taper 与 tout 已直接 connect，旧版的同位置路由删除。
    route_off_grid(sr, bend_moni.ports["o2"], str_moni_out.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    # add_port
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("through", port=toutring_th.ports["o2"])
    sr.add_port("drop", port=toutring_dr.ports["o2"])
    sr.add_port("add", port=toutring_ad.ports["o2"])
    Rcenter = [ring.ports["RingL"].center[i] / 2 + ring.ports["RingR"].center[i] / 2 for i in range(2)]
    sr.add_port("RingC", port=sr.ports["input"], center=Rcenter)
    add_labels_to_ports(sr)
    return sr


# %% RingAndIsolator0:Ring and SingleRingIsolator0: ring for comb and ADD-DROP ring
@gf.vcell
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
参考环 + 隔离器串联：先放一个普通环，再串 ``SingleRingIsolator0`` 的核心，
用于在同一测试结构里同时测滤波与方向性。

端口: input 及随输出组件一起导出的光学端口。
"""
    if tin is None:
        tin = GfCStraight(width=width_single, length=10, layer=oplayer)
    if tout is None:
        tout = GfCStraight(width=width_single, length=10, layer=oplayer)
    sr = ComponentAllAngle()
    if width_Cring == None:
        width_Cring = width_ring
    # Section CrossSection
    S_near1 = gf.Section(width=width_near1, layer=oplayer, port_names=("o1", "o2"))
    CS_near1 = gf.CrossSection(sections=[S_near1])
    S_near2 = gf.Section(width=width_near2, layer=oplayer, port_names=("o1", "o2"))
    CS_near2 = gf.CrossSection(sections=[S_near2])
    # component
    tinring = sr.create_vinst(tin)
    toutring_th = sr.create_vinst(tout)
    toutring_ad = sr.create_vinst(tout)
    toutring_dr = sr.create_vinst(tout)
    taper_s2n1 = gf.c.taper(width1=width_single, width2=width_near1, length=length_taper, layer=oplayer)
    taper_s2n2 = gf.c.taper(width1=width_single, width2=width_near2, length=length_taper, layer=oplayer)
    taper_s2n_in = sr.create_vinst(taper_s2n1)
    taper_s2n_th = sr.create_vinst(taper_s2n1)
    taper_s2n_ad = sr.create_vinst(taper_s2n2)
    taper_s2n_dr = sr.create_vinst(taper_s2n2)
    ring_comb = sr.create_vinst(RingPulley(
        WidthRing=width_Cring, WidthNear=width_nearC,
        RadiusRing=r_ring, GapRing=gap_Cring, AngleCouple=angle_Cring,
        IsAD=False, oplayer=oplayer,
    ))
    ring_iso = sr.create_vinst(RingPulley1DC(
        WidthRing=width_ring, oplayer=oplayer, RadiusRing=r_ring,
        WidthNear1=width_near1, GapRing1=gap_rc1, AngleCouple1=angle_rc1,
        WidthNear2=width_near2, GapRing2=gap_rc2, AngleCouple2=angle_rc2,
        HeaterConfig=HeaterConfigClass(WidthHeat=width_heat)
    ))
    taper_s2n_in.movex(pos_ring - length_taper)
    ring_iso.connect("Input", other=taper_s2n_in.ports["o2"], mirror=True)
    ring_comb.connect("Input", other=taper_s2n_in.ports["o2"], allow_width_mismatch=True, mirror=True)
    ring_comb.movex(pos_Cring - pos_ring)
    length_tout = abs(toutring_th.ports["o1"].center[0] - toutring_th.ports["o2"].center[0])
    # comb ring taper
    taper_s2CRin = sr.create_vinst(gf.c.taper(width2=width_nearC, width1=width_single, length=length_taper, layer=oplayer))
    taper_CRout2s = sr.create_vinst(gf.c.taper(width2=width_single, width1=width_nearC, length=length_taper, layer=oplayer))
    taper_s2CRin.connect("o2", ring_comb.ports["Input"])
    taper_CRout2s.connect("o1", ring_comb.ports["Through"])

    # add
    taper_s2n_ad.connect("o2", other=ring_iso.ports["Add"])
    toutring_ad.connect("o1", other=taper_s2n_ad.ports["o1"])
    toutring_ad.movex(length_total - length_tout - taper_s2n_ad.ports["o1"].center[0])
    # through
    bend_th1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=-angle_th1,
                                     radius=r_euler_false * 1.2))
    bend_th2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=angle_th1,
                                     radius=r_euler_false * 1.2))
    str_th1 = sr.create_vinst(GfCStraight(width=width_near1, layer=oplayer, length=length_thadd))
    bend_th1.connect("o1", other=ring_iso.ports["Through"])
    str_th1.connect("o1", other=bend_th1.ports["o2"])
    bend_th2.connect("o1", other=str_th1.ports["o2"])
    # 旧版把 bend_th2.o1 路由回 bend_th1.o2，与 str_th1 重复，删除。
    taper_s2n_th.connect("o2", other=bend_th2.ports["o2"])
    toutring_th.connect("o1", other=taper_s2n_th.ports["o1"])
    toutring_th.movex(length_total - length_tout - taper_s2n_th.ports["o1"].center[0])
    # drop：Ring Drop -> bend_dr1 -> bend_dr2 -> taper -> toutring
    bend_dr1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=-angle_dr,
                                     radius=r_euler_false * 1.2))
    bend_dr2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=angle_dr,
                                     radius=r_euler_false * 1.2))
    bend_dr1.connect("o1", other=ring_iso.ports["Drop"])
    bend_dr2.connect("o1", other=bend_dr1.ports["o2"])
    # 旧版 taper 也接在 Drop 上，再与 bend_dr2 路由成环；改为直接串接。
    taper_s2n_dr.connect("o2", other=bend_dr2.ports["o2"])
    toutring_dr.connect("o1", other=taper_s2n_dr.ports["o1"])
    toutring_dr.movex(length_total - length_tout - taper_s2n_dr.ports["o1"].center[0])
    # route io
    CS_single = gf.CrossSection(sections=[gf.Section(width=width_single, layer=oplayer, port_names=("o1", "o2"))])
    route_off_grid(sr, tinring.ports["o2"], taper_s2CRin.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    route_off_grid(sr, taper_CRout2s.ports["o2"], taper_s2n_in.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    # add/drop/through 的 taper 与 tout 已直接 connect，旧版的同位置路由删除。
    # add_port
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("through", port=toutring_th.ports["o2"])
    sr.add_port("drop", port=toutring_dr.ports["o2"])
    sr.add_port("add", port=toutring_ad.ports["o2"])
    Rcenter = [ring_iso.ports["RingL"].center[i] / 2 + ring_iso.ports["RingR"].center[i] / 2 for i in range(2)]
    sr.add_port("RingC", port=sr.ports["input"], center=Rcenter)
    add_labels_to_ports(sr)
    return sr


__all__ = ['SingleRingIsolator0', 'SingleRingIsolator1', 'RingAndIsolator0']
