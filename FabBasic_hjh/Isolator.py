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
    '''

    Args:
        r_ring:
        r_euler_false:
        width_ring:isolator ring width
        width_Cring: Comb Ring Width: if None,width_Cring = width_ring
        width_near1:
        width_near2:
        width_heat:
        width_single:
        angle_rc1:angle of isolator ring input-pass
        angle_rc2:angle of isolator ring add-drop
        angle_th1:
        angle_th2:
        angle_Cring: Comb Ring coupler angle
        length_taper:
        length_total:
        pos_ring: isolator ring position
        pos_Cring: Comb Ring position
        gap_rc1:
        gap_rc2:
        gap_ad:
        gap_Cring: Comb Ring coupler gap
        tout:
        tin:
        oplayer:

    Returns:
        Ring and SingleRingIsolator0: ring for comb and ADD-DROP ring
    '''
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
