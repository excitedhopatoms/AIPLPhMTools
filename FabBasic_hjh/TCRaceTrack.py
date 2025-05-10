from .BasicDefine import *
from .RaceTrack import *

width_single = 1
taper_in_DFB = gf.Component()
taper_in_te0 = taper_in_DFB << gf.c.taper(width1=0.15, width2=width_single, length=200, layer=LAYER.WG)
taper_in_tes0 = taper_in_DFB << GfCStraight(width=0.15, length=50, layer=LAYER.WG)
taper_in_tes1 = taper_in_DFB << GfCStraight(width=width_single, length=50, layer=LAYER.WG)
taper_in_te0.connect("o1", taper_in_tes0.ports["o2"])
taper_in_tes1.connect("o1",taper_in_te0.ports["o2"])
taper_in_DFB.add_port(name="o1", port=taper_in_tes0.ports["o1"])
taper_in_DFB.add_port(name="o2", port=taper_in_tes1.ports["o2"])

taper_in_DFB_reverse = gf.Component()
taper_in_te0 = taper_in_DFB_reverse << gf.c.taper(width1=0.15, width2=width_single, length=200, layer=LAYER.WG)
taper_in_tes0 = taper_in_DFB_reverse << GfCStraight(width=0.15, length=50, layer=LAYER.WG)
taper_in_tes1 = taper_in_DFB_reverse << GfCStraight(width=width_single, length=50, layer=LAYER.WG)
taper_in_te0.connect("o1", taper_in_tes0.ports["o2"])
taper_in_tes1.connect("o1",taper_in_te0.ports["o2"])
taper_in_DFB_reverse.add_port(name="o1", port=taper_in_tes0.ports["o2"])
taper_in_DFB_reverse.add_port(name="o2", port=taper_in_tes1.ports["o1"])

# %% TCRing5: racetrack ring
@gf.cell
def TCRaceTrackP(
        r_ring: float = 2000,
        r_bend: float = r_euler_true,
        width_ring: float = 8,
        width_near: float = 4,
        width_heat: float = 5,
        width_single: float = 1,
        angle_rc: float = 20,
        length_taper: float = 500,
        length_total: float = 10000,
        length_run: float = 1000,
        pos_ring: float = 5000,
        gap_rc: float = 1,
        tout: Component =taper_in_DFB_reverse,
        tin: Component = taper_in_DFB,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    sr = gf.Component("RaceTrack")
    ring = sr << RaceTrackPulley(
        WidthRing=width_ring, WidthNear=width_near, GapRing=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        AngleCouple=angle_rc, IsAD=False,LengthRun=length_run,
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
        ctin.connect("o2", bend_single_1.ports["o1"])
        ctin.movex(-pos_ring)
        route_in = gf.routing.route_single(sr,ctin.ports["o2"], bend_single_1.ports["o1"], layer=oplayer, route_width=width_single)
        # sr.add(route_in.references)
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"],allow_width_mismatch=True)
        ctout.movex(length_total)
        delta = ctout.ports["o1"].center[1] - bend_single_2.ports["o2"].center[1]
        ctout.movey(-delta)
        route_out = gf.routing.route_single(sr,ctout.ports["o1"], bend_single_2.ports["o2"], layer=oplayer,
                                         route_width=width_single)
        # sr.add(route_out.references)
    sr.add_port("input", port=ctin.ports["o1"])
    sr.add_port("output", port=ctout.ports["o2"])
    sr.add_port("inputo2", port=ctin.ports["o2"])
    sr.add_port("outputo1", port=ctout.ports["o1"])
    sr.add_port("RingC", port=ring.ports["Input"],
                center = (np.array(ring.ports["Rcen1"].center) + np.array(ring.ports["Rcen2"].center)) / 2)
    add_labels_to_ports(sr)
    return sr


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
        type_heat:str = 'none',
        tout: Component =taper_in_DFB_reverse,
        tin: Component = taper_in_DFB,
        oplayer: LayerSpec = LAYER.WG,
        **kwargs,
) -> Component:
    sr = gf.Component("RaceTrack")
    width_near = width_ring
    ring = sr << RaceTrackStr(
        WidthRing=width_ring, LengthRun=length_run, GapRun=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        LengthCouple=length_rc, IsAD=False,TypeHeater=type_heat
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
        ctin.connect("o2", ring.ports["Input"],allow_width_mismatch=True)
        ctin.movex(-pos_ring)
        route_in = gf.routing.route_single(sr,ctin.ports["o2"], taper_s2n_1.ports["o1"], layer=oplayer, route_width=width_single)
        # sr.add(route_in.references)
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"],allow_width_mismatch=True)
        ctout.movex(length_total)
        delta = ctout.ports["o1"].center[1] - bend_outsingle_2.ports["o2"].center[1]
        ctout.movey(-delta)
        route_out = gf.routing.route_single(sr,ctout.ports["o1"], bend_outsingle_2.ports["o2"], layer=oplayer,
                                         route_width=width_single)
        # sr.add(route_out.references)
    sr.add_port("input", port=ctin.ports["o1"])
    sr.add_port("output", port=ctout.ports["o1"])
    sr.add_port("RingC", port=ring.ports["Input"],
                center = (np.array(ring.ports["Rcen1"].center) + np.array(ring.ports["Rcen2"].center)) / 2
                )
    add_labels_to_ports(sr)
    return sr


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
        tout: Component =taper_in_DFB_reverse,
        tin: Component = taper_in_DFB,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    sr = gf.Component("RaceTrack")
    width_near = width_ring
    ring = sr << RaceTrackStr(
        WidthRing=width_ring, LengthRun=length_run, GapRun=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        LengthCouple=length_rc, IsAD=False
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
        route_in = gf.routing.route_single(sr,ctin.ports["o2"], bend_insingle_2.ports["o1"], layer=oplayer,
                                        route_width=width_single)
        # sr.add(route_in.references)
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"],allow_width_mismatch=True)
        ctout.movex(length_total)
        delta = ctout.ports["o1"].center[1] - taper_s2n_2.ports["o2"].center[1]
        ctout.movey(-delta)
        route_out = gf.routing.route_single(sr,ctout.ports["o1"], taper_s2n_2.ports["o2"], layer=oplayer, route_width=width_single)
        # sr.add(route_out.references)
    sr.add_port("input", port=ctin.ports["o1"])
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
        IsLabels: float = True,
        tout: Component =taper_in_DFB_reverse,
        tin: Component = taper_in_DFB,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    sr = gf.Component()
    width_near = width_ring
    Cring = RaceTrackStr(
        WidthRing=width_ring, LengthRun=length_run, GapRun=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        LengthCouple=length_rc, IsAD=False, IsLabels=False,
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
        route_in = gf.routing.route_single(sr,ctin.ports["o2"], taper_s2n_1.ports["o1"], layer=oplayer, route_width=width_single)
        # sr.add(route_in.references)
        sr.add_port("input", port=ctin.ports["o1"])
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"],allow_width_mismatch=True)
        ctout.movex(length_total)
        route_out = gf.routing.route_single(sr,ctout.ports["o1"], taper_s2n_2.ports["o2"], layer=oplayer, route_width=width_single)
        # sr.add(route_out.references)
        sr.add_port("output", port=ctout.ports["o1"])
    sr.add_port("RingC", port=ring.ports["Input"],
                center = (np.array(ring.ports["Rcen1"].center) + np.array(ring.ports["Rcen2"].center)) / 2)
    if IsLabels:
        add_labels_to_ports(sr)
    return sr


def TCRaceTrackS3h(
        r_ring: float = 2000,
        delta_heat: float = 10,
        width_ring: float = 8,
        width_single: float = 1,
        length_rc: float = 20,
        length_run: float = 400,
        length_taper: float = 500,
        length_total: float = 10000,
        pos_ring: float = 5000,
        gap_rc: float = 1,
        gap_route: float = 100,
        IsLabels: float = True,
        tout: Component =taper_in_DFB_reverse,
        tin: Component = taper_in_DFB,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
) -> [Component]:
    sr = gf.Component("RaceTrack")
    sh = gf.Component("RaceTrackHeat")
    width_near = width_ring
    Cring = RaceTrackStr(
        WidthRing=width_ring, LengthRun=length_run, GapRun=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
        GapRoute=gap_route,
        LengthCouple=length_rc, IsAD=False, IsLabels=False, DeltaHeat=delta_heat, heatlayer=heatlayer
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
        route_in = gf.routing.route_single(sr,ctin.ports["o2"], taper_s2n_1.ports["o1"], layer=oplayer, route_width=width_single)
        # sr.add(route_in.references)
        sr.add_port("input", port=ctin.ports["o1"])
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"],allow_width_mismatch=True)
        ctout.movex(length_total)
        route_out = gf.routing.route_single(sr,ctout.ports["o1"], taper_s2n_2.ports["o2"], layer=oplayer, route_width=width_single)
        # sr.add(route_out.references)
        sr.add_port("output", port=ctout.ports["o1"])
    sr.add_port("RingC", port=ring.ports["Input"],
                center = (np.array(ring.ports["Rcen1"].center) + np.array(ring.ports["Rcen2"].center)) / 2)
    add_labels_to_ports(sr)
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
        width_heat: float = 5,
        width_single: float = 1,
        angle_rc: float = 20,
        length_racetaper: float = 150,
        length_run: float = 300,
        length_taper: float = 500,
        length_total: float = 10000,
        pos_ring: float = 5000,
        gap_rc: float = 1,
        tout: Component =taper_in_DFB_reverse,
        tin: Component = taper_in_DFB,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    sr = gf.Component("RaceTrack")
    S_wg = gf.Section(width=width_single, offset=0, layer=oplayer, port_names=("o1", "o2"))
    CS_wg = gf.CrossSection(sections=[S_wg])
    ring = sr << TaperRaceTrackPulley(
        WidthRing=width_ring, WidthNear=width_near, WidthRun=width_run,
        LengthRun=length_run, LengthTaper=length_racetaper,
        GapRing=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
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
        route_in = gf.routing.route_single(sr,ctin.ports["o2"], bend_single_1.ports["o1"], layer=oplayer,
                                        route_width=width_single, radius=r_bend)
        # sr.add(route_in.references)
        sr.add_port("input", port=ctin.ports["o1"])
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"], allow_width_mismatch=True)
        ctout.movex(length_total)
        delta = ctout.ports["o1"].center[1] - bend_single_2.ports["o2"].center[1]
        ctout.movey(-delta)
        route_out = gf.routing.route_single(sr,ctout.ports["o1"], bend_single_2.ports["o2"], layer=oplayer,
                                         route_width=width_single, radius=r_bend)
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
        width_heat: float = 5,
        width_single: float = 1,
        angle_rc: float = 20,
        length_racetaper: float = 150,
        length_run: float = 300,
        length_taper: float = 500,
        length_total: float = 10000,
        pos_ring: float = 5000,
        gap_rc: float = 1,
        tout: Component =taper_in_DFB_reverse,
        tin: Component = taper_in_DFB,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    sr = gf.Component("RaceTrack")
    S_wg = gf.Section(width=width_single, offset=0, layer=oplayer, port_names=("o1", "o2"))
    CS_wg = gf.CrossSection(sections=[S_wg])
    ring = sr << TaperRaceTrackPulley(
        WidthRing=width_ring, WidthNear=width_near, WidthRun=width_run,
        LengthRun=length_run, LengthTaper=length_racetaper,
        GapRing=gap_rc, oplayer=oplayer, RadiusRing=r_ring,
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
        route_in = gf.routing.route_single(sr,ctin.ports["o2"], taper_s2n_1.ports["o1"], layer=oplayer,
                                        route_width=width_single, radius=r_bend)
        # sr.add(route_in.references)
        sr.add_port("input", port=ctin.ports["o1"])
    # output
    if tout != None:
        ctout = sr << tout
        ctout.connect("o2", other=ctin.ports["o1"], allow_width_mismatch=True)
        ctout.movex(length_total)
        delta = ctout.ports["o1"].center[1] - taper_s2n_2.ports["o2"].center[1]
        ctout.movey(-delta)
        route_out = gf.routing.route_single(sr,ctout.ports["o1"], taper_s2n_2.ports["o2"], layer=oplayer,
                                         route_width=width_single, radius=r_bend)
        # sr.add(route_out.references)
        sr.add_port("output", port=ctout.ports["o1"])
    sr.add_port("RingC", port=ring.ports["Input"], 
                center = (np.array(ring.ports["Rcen1"].center) + np.array(ring.ports["Rcen2"].center)) / 2)
    return sr
if __name__ == '__main__':
    test = TCRaceTrackP()
    # test.show()