# from Heater import SnakeHeater
import numpy as np

from .BasicDefine import *
from .Heater import *

LengthAllAround = [0, 0, 0]  # 回旋镖腔


@gf.cell
def Boomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        WidthHeat: float = 4,
        WidthRoute: float = 20,
        WidthVia: float = 0.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        Spacing: float = 1,
        GapRR: float = 0.3,
        GapHeat: float = 80,
        DeltaHeat: float = 100,
        LengthBridge1: float = 100,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        IsHeatIn: bool = False,
        IsHeatOut: bool = False,
        TypeHeater: str = "default",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    c = gf.Component()
    Cring1 = gf.Component()
    Test = gf.Component()
    # sections
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="linear")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="linear")
    # paths
    path_circle_in = gf.path.arc(radius=RadiusRing, angle=30)
    path_circle_out = gf.path.arc(radius=RadiusRing + GapRR + WidthRingIn / 2 + WidthRingOut / 2, angle=30)
    path_euler_in = euler_Bend_Half(radius=RadiusRing, angle=15)
    path_euler_out = euler_Bend_Half(radius=RadiusRing + GapRR + WidthRingIn / 2 + WidthRingOut / 2, angle=15)
    path_euler_bridge = euler_Bend_Half(radius=RadiusEuler, angle=90)
    path_taper_in = gf.path.straight(length=LengthTaper)
    # components
    Cringhalf = gf.Component()
    cir_in = Cringhalf << gf.path.extrude(path_circle_in + path_euler_in, cross_section=X_in)
    cir_out = Cringhalf << gf.path.extrude(path_circle_out + path_euler_out, cross_section=X_out)
    # CompOut.connect("o1",CompIn.ports["o1"],allow_width_mismatch=True).mirror_x("o1").mirror_y("o1").movey(-(GapRR+WidthRingOut/2+WidthRingIn/2))
    TaperIn = gf.c.taper(width1=WidthRingIn, width2=WidthStraight, length=LengthTaper, layer=oplayer)
    TaperOut = gf.c.taper(width1=WidthRingOut, width2=WidthStraight, length=LengthTaper, layer=oplayer)
    taper_in = Cringhalf << TaperIn
    taper_out = Cringhalf << TaperOut
    c_euler_bridge = Test << gf.path.extrude(path_euler_bridge, cross_section=X_str)
    Deltaheight = (LengthBridge2 + 2 * (c_euler_bridge.ports["o2"].center[0] - c_euler_bridge.ports["o1"].center[0]))
    cir_out.move([-Deltaheight, Deltaheight])
    cir_in.rotate(45, cir_in.ports["o1"].center)
    cir_out.rotate(45, cir_out.ports["o1"].center)
    taper_in.connect("o1", cir_in.ports["o2"])
    taper_out.connect("o1", cir_out.ports["o2"])
    path_str_out = gf.path.straight(length=LengthBridge1)
    StrOut = gf.path.extrude(path_str_out, cross_section=X_str)
    str_out = Cringhalf << StrOut
    str_out.connect("o1", taper_out.ports["o2"])
    route = gf.routing.get_route(str_out.ports["o2"], taper_in.ports["o2"], radius=RadiusEuler * 1.1,
                                 cross_section=X_str, )
    route_bend = gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=90)
    Cringhalf.add_port("o1", port=cir_in.ports["o1"])
    Cringhalf.add_port("o2", port=cir_out.ports["o1"])
    Cringhalf.add_port("o22", port=cir_out.ports["o2"])
    Cringhalf.add_port("Lb1", center=Cringhalf.ports["o22"].center + [0, LengthBridge1 + LengthTaper] + (
                route_bend.ports["o2"].center - route_bend.ports["o1"].center),
                       orientation=0, cross_section=X_str)
    Cringhalf.add_port("Lb2", center=Cringhalf.ports["Lb1"].center + [LengthBridge2, 0],
                       orientation=180, cross_section=X_str)
    Cringhalf.add(route.references)
    ringhalf1 = Cring1 << Cringhalf
    ringhalf2 = Cring1 << Cringhalf
    ringhalf2.mirror_x(ringhalf2.ports["o1"].center[0])
    ringhalf2.rotate(90, ringhalf2.ports["o1"].center)
    # heat in
    if IsHeatIn:
        path_heat_in = path_circle_in + path_euler_in + path_taper_in
        path_heat_in.rotate(45)
        HeatInHalf = DifferentHeater(PathHeat=path_heat_in,
                                     WidthHeat=WidthHeat, WidthWG=WidthStraight, WidthRoute=WidthRoute,
                                     WidthVia=WidthVia, Spacing=Spacing,
                                     DeltaHeat=DeltaHeat, GapHeat=GapHeat, TypeHeater=TypeHeater,
                                     heatlayer=heatlayer, vialayer=vialayer, routelayer=routelayer)
        heat_in_l = c << HeatInHalf
        heat_in_r = c << HeatInHalf
        heat_in_l.connect('HeatIn', ringhalf1.ports["o1"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heat_in_r.connect('HeatIn', heat_in_l.ports["HeatIn"], mirror=True)
        heat_in_l.rotate(-90, heat_in_l.ports['HeatIn'].center)
        c.add_port("HeatILIn", port=heat_in_l.ports["HeatLOut"])
        c.add_port("HeatILOut", port=heat_in_r.ports["HeatLOut"])
        c.add_port("HeatIRIn", port=heat_in_l.ports["HeatROut"])
        c.add_port("HeatIROut", port=heat_in_r.ports["HeatROut"])
    if IsHeatOut:
        path_heat_out = path_circle_out + path_euler_out + path_taper_in
        path_heat_out.rotate(45)
        HeatOutHalf = DifferentHeater(PathHeat=path_heat_out,
                                      WidthHeat=WidthHeat, WidthWG=WidthStraight, WidthRoute=WidthRoute,
                                      WidthVia=WidthVia, Spacing=Spacing,
                                      DeltaHeat=DeltaHeat, GapHeat=GapHeat, TypeHeater=TypeHeater,
                                      heatlayer=heatlayer, vialayer=vialayer, routelayer=routelayer)
        heat_out_l = c << HeatOutHalf
        heat_out_r = c << HeatOutHalf
        heat_out_l.connect('HeatIn', ringhalf1.ports["o2"], allow_layer_mismatch=True, allow_width_mismatch=True)
        heat_out_r.connect('HeatIn', heat_out_l.ports["HeatIn"], mirror=True)
        heat_out_l.rotate(-90, heat_out_l.ports['HeatIn'].center)
        c.add_port("HeatOLIn", port=heat_out_l.ports["HeatLOut"])
        c.add_port("HeatOLOut", port=heat_out_r.ports["HeatLOut"])
        c.add_port("HeatORIn", port=heat_out_l.ports["HeatROut"])
        c.add_port("HeatOROut", port=heat_out_r.ports["HeatROut"])
    # caculate length
    l1 = path_circle_in.length() + path_circle_out.length() + path_euler_out.length() + path_euler_in.length() + route.length + 2 * LengthTaper + LengthBridge1
    # Cring0 = GetFromLayer(Cring1,OLayer=oplayer,FLayer=oplayer)
    # Cring2 = gf.geometry.offset(distance=0.05,elements=Cring0)
    # c << gf.geometry.offset(distance=-0.05,elements=Cring2)
    c << Cring1
    # add port
    c.add_port("Lo1", port=ringhalf1.ports["o1"])
    c.add_port("Lo2", port=ringhalf1.ports["o2"])
    c.add_port("Ro1", port=ringhalf2.ports["o1"])
    c.add_port("Ro2", port=ringhalf2.ports["o2"])
    c.add_port("Lb1", port=ringhalf1.ports["Lb1"])
    c.add_port("Lb2", port=ringhalf1.ports["Lb2"])
    c.add_port("Rb1", port=ringhalf2.ports["Lb1"])
    c.add_port("Rb2", port=ringhalf2.ports["Lb2"])
    c.info['length'] = 2 * l1
    add_labels_to_ports(c)
    return c


# 回旋镖腔
@gf.cell
def RingBoomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        WidthHeat: float = 4,
        WidthRoute: float = 20,
        WidthVia: float = 0.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        Spacing: float = 1,
        GapRR: float = 0.3,
        GapRB: float = 0.5,
        GapHeat: float = 80,
        DeltaHeat: float = 100,
        LengthBridge1: float = 100,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        LengthCouple: float = 10,
        IsHeatIn: bool = True,
        IsHeatOut: bool = True,
        TypeHeater: str = "default",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    c = gf.Component()
    # sections
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="sine")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="sine")
    # boomerang1
    Cring1 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2, LengthTaper,
                            IsHeatIn, IsHeatOut, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring1.rotate(90, Cring1.ports["Lo1"].center)
    # input-through
    sbend_in = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    sbend_out = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_in = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_in.connect("o1", Cring1.ports["Lb1"])
    str_couple_in.movex(-GapRB - WidthStraight).movey(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_in.connect("o2", str_couple_in.ports["o1"], mirror=True)
    sbend_out.connect("o1", str_couple_in.ports["o2"])
    # add drop
    sbend_add = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    sbend_drop = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_ad = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_ad.connect("o1", Cring1.ports["Rb1"])
    str_couple_ad.movey(-GapRB - WidthStraight).movex(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_add.connect("o2", str_couple_ad.ports["o1"])
    sbend_drop.connect("o1", str_couple_ad.ports["o2"], mirror=True)
    c.add_port("Input", port=sbend_in.ports["o1"])
    c.add_port("Through", port=sbend_out.ports["o2"])
    c.add_port("Add", port=sbend_add.ports["o1"])
    c.add_port("Drop", port=sbend_drop.ports["o2"])
    c.info['length'] = Cring1.info['length']
    return c


# 双回旋镖腔
@gf.cell
def RingDouBoomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        WidthHeat: float = 4,
        WidthRoute: float = 20,
        WidthVia: float = 0.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        Spacing: float = 1,
        GapRR: float = 0.3,
        GapRB: float = 0.5,
        GapHeat: float = 80,
        DeltaHeat: float = 100,
        DeltaLB2: float = 2,
        LengthBridge1: float = 10,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        LengthCouple: float = 10,
        IsHeat: bool = True,
        TypeHeater: str = "default",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    c = gf.Component()
    # sections
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="sine")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="sine")
    # boomerang1
    Cring1 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2, LengthTaper,
                            False, IsHeat, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring1.rotate(90, Cring1.ports["Lo1"].center)
    Cring2 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2 + DeltaLB2, LengthTaper,
                            IsHeat, False, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring2.connect("Lo2", Cring1.ports["Ro1"], allow_width_mismatch=True)
    Cring2.move(((WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2),
                 (WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2)))
    # add drop
    sbend_add = c << gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=90, cross_section=X_str)
    sbend_drop = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_ad = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_ad.connect("o1", Cring2.ports["Lb1"])
    str_couple_ad.movex(-GapRB - WidthStraight).movey(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_add.connect("o2", str_couple_ad.ports["o1"])
    sbend_drop.connect("o1", str_couple_ad.ports["o2"])
    c.add_port("Add", port=sbend_add.ports['o1'])
    c.add_port("Drop", port=sbend_drop.ports['o2'])
    c.info['R1length'] = Cring1.info['length']
    c.info['R2length'] = Cring2.info['length']
    # input through
    sbend_in = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    sbend_th = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_in = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_in.connect("o1", Cring1.ports["Rb1"])
    str_couple_in.movey(-GapRB - WidthStraight).movex(LengthBridge2 / 2 - LengthCouple / 2)
    sbend_in.connect("o2", str_couple_in.ports["o1"])
    sbend_th.connect("o1", str_couple_in.ports["o2"], mirror=True)
    c.add_port("Input", port=sbend_in.ports['o1'])
    c.add_port("Through", port=sbend_th.ports['o2'])
    for port in Cring1.ports:
        c.add_port("R1" + port, port=Cring1.ports[port])
    for port in Cring2.ports:
        c.add_port("R2" + port, port=Cring2.ports[port])
    return c


# 三回旋镖腔
@gf.cell
def RingTriBoomerang(
        WidthRingIn: float = 2,
        WidthRingOut: float = 1,
        WidthStraight: float = 1.5,
        WidthHeat: float = 4,
        WidthRoute: float = 20,
        WidthVia: float = 0.5,
        RadiusRing: float = 100,
        RadiusEuler: float = 100,
        Spacing: float = 1,
        GapRR: float = 0.3,
        GapRB: float = 0.5,
        GapHeat: float = 80,
        DeltaHeat: float = 100,
        DeltaLB2: float = 2,
        LengthBridge1: float = 10,
        LengthBridge2: float = 40,
        LengthTaper: float = 20,
        LengthCouple: float = 10,
        IsHeat: bool = True,
        TypeHeater: str = "default",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    c = gf.Component()
    # sections
    C_in = gf.Section(layer=oplayer, width=WidthRingIn, port_names=["o1", "o2"])
    C_out = gf.Section(layer=oplayer, width=WidthRingOut, port_names=["o1", "o2"])
    C_str = gf.Section(layer=oplayer, width=WidthStraight, port_names=["o1", "o2"])
    X_in = gf.CrossSection(sections=[C_in])
    X_out = gf.CrossSection(sections=[C_out])
    X_str = gf.CrossSection(sections=[C_str])
    XT_in2str = gf.path.transition(cross_section1=X_in, cross_section2=X_str, width_type="sine")
    XT_out2str = gf.path.transition(cross_section1=X_out, cross_section2=X_str, width_type="sine")
    # boomerang1
    Cring1 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2, LengthTaper,
                            False, False, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring1.rotate(90, Cring1.ports["Lo1"].center)
    Cring2 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2 + DeltaLB2, LengthTaper,
                            IsHeat, False, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring2.connect("Lo2", Cring1.ports["Ro1"], allow_width_mismatch=True)
    Cring2.move(((WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2),
                 (WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2)))
    Cring3 = c << Boomerang(WidthRingIn, WidthRingOut, WidthStraight, WidthHeat, WidthRoute, WidthVia,
                            RadiusRing, RadiusEuler, Spacing, GapRR, GapHeat, DeltaHeat,
                            LengthBridge1, LengthBridge2 - DeltaLB2, LengthTaper,
                            False, IsHeat, TypeHeater,
                            oplayer, heatlayer, routelayer, vialayer)
    Cring3.connect("Lo1", Cring1.ports["Ro2"], allow_width_mismatch=True)
    Cring3.move((-(WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2),
                 -(WidthRingIn / 2 + WidthRingOut / 2 + GapRR) / np.sqrt(2)))
    c.info['R1length'] = Cring1.info['length']
    c.info['R2length'] = Cring2.info['length']
    c.info['R3length'] = Cring3.info['length']
    # input-through
    sbend_in = c << gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=90, cross_section=X_str)
    sbend_out = c << gf.c.bend_s(size=[100, 10], cross_section=X_str)
    str_couple_in = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_in.connect("o1", Cring1.ports["Lb1"]).movex(-GapRB - WidthStraight).movey(
        LengthBridge2 / 2 - LengthCouple / 2)
    sbend_in.connect("o2", str_couple_in.ports["o1"])
    sbend_out.connect("o1", str_couple_in.ports["o2"])
    c.add_port("Input", port=sbend_in.ports['o1'])
    c.add_port("Through", port=sbend_out.ports['o2'])
    # add drop
    sbend_add = c << gf.c.bend_euler(radius=RadiusEuler * 1.1, angle=-90, cross_section=X_str)
    sbend_drop = c << gf.c.bend_s(size=[100, -10], cross_section=X_str)
    str_couple_ad = c << GfCStraight(width=WidthStraight, length=LengthCouple, layer=oplayer)
    str_couple_ad.connect("o1", Cring1.ports["Rb1"]).movey(-GapRB - WidthStraight).movex(
        LengthBridge2 / 2 - LengthCouple / 2)
    sbend_add.connect("o2", str_couple_ad.ports["o1"])
    sbend_drop.connect("o1", str_couple_ad.ports["o2"])
    c.add_port("Add", port=sbend_add.ports['o1'])
    c.add_port("Drop", port=sbend_drop.ports['o2'])
    for port in Cring1.ports:
        c.add_port("R1" + port, port=Cring1.ports[port])
    for port in Cring2.ports:
        c.add_port("R2" + port, port=Cring2.ports[port])
    for port in Cring3.ports:
        c.add_port("R3" + port, port=Cring3.ports[port])
    return c


# %% 导出所有函数
__all__ = [
    'Boomerang', 'RingBoomerang', 'RingDouBoomerang', 'RingTriBoomerang'
]
