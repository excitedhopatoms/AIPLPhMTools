from .BasicDefine import *
from .Heater import DifferentHeater


# %% pulley 2X2Direct Coupler
def PulleyCoupler2X2(
        WidthOut: float = 1.55,
        WidthIn: float = 2,
        AngleCouple: float = 11,
        AngleIn: float = None,
        RadiusIn: float = 200,
        GapCoup: float = 0.3,
        IsParallel: bool = False,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个 2x2 的pulley 定向耦合器（Direct Coupler）。

    Args:
        WidthOut: 耦合器宽度 (um)
        WidthIn: 环形波导宽度 (um)
        AngleCouple: 耦合角度 (度)
        AngleIn: 环形波导角度 (度)
        RadiusIn: 环形波导半径 (um)
        GapCoup: 耦合间隙 (um)
        IsParallel: 是否平行输入输出
        oplayer: 光学层
        Name: 组件名称

    Returns:
        包含 in1, in2, out1, out2 端口的 Component
    """
    c = gf.Component()
    r_in = RadiusIn
    r_out = r_in + WidthOut / 2 + WidthIn / 2 + GapCoup
    sout = gf.Section(width=WidthOut, offset=0, layer=oplayer, port_names=("in", "out"))
    sin = gf.Section(width=WidthIn, offset=0, layer=oplayer, port_names=("in", "out"))
    csout = gf.CrossSection(sections=[sout])
    csin = gf.CrossSection(sections=[sin])
    po_ring = gf.path.arc(radius=r_out, angle=AngleCouple / 2)
    po_euler = euler_Bend_Half(radius=r_out, angle=-AngleCouple / 2, p=0.5)
    po = po_euler + po_ring
    if AngleIn == None:
        AngleIn = AngleCouple * 2
    pi_euler = euler_Bend_Half(radius=r_in, angle=-AngleIn / 2, p=1)
    if IsParallel:
        pi_ring = gf.path.arc(radius=r_in, angle=AngleIn / 2)
        pi = pi_euler + pi_ring
    else:
        pi_ring = gf.path.arc(radius=r_in, angle=-AngleIn / 2)
        pi = pi_ring
    co = gf.path.extrude(po, cross_section=csout)
    ci = gf.path.extrude(pi, cross_section=csin)
    co1 = c << co
    co2 = c << co
    ci1 = c << ci
    ci2 = c << ci
    co1.mirror_y()
    co2.connect("in", other=co1.ports["in"])
    ci1.connect("in", other=co1.ports["in"], allow_width_mismatch=True)
    ci1.movey(WidthOut / 2 + WidthIn / 2 + GapCoup)
    ci2.connect("in", other=ci1.ports["in"], mirror=True)
    c.add_port("in1", port=ci1.ports["out"])
    c.add_port("out2", port=co1.ports["out"])
    c.add_port("out1", port=ci2.ports["out"])
    c.add_port("in2", port=co2.ports["out"])
    add_labels_to_ports(c)
    return c


# %% DMZI
@gf.cell
def DMZI(
        WidthWG: float = 0.8,
        WidthHeat: float = 8,
        LengthCoup: float = 100,
        LengthBridge:float =300,
        LengthBend:float =300,
        Radius:float =200,
        GapCoup:float =1,
        GapHeat=1,
        DeltaHeat=0,
        DeltaOut = -40,
        IsHeat: bool = True,
        TypeHeater: str = "default",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个 2x2 的直波导耦合器（Direct Coupler）的MZI。

    Args:
        WidthSingle: 单模波导宽度 (um)
        LengthCoup: 耦合去长度 (um)
        LengthBridge: 臂长 (um)
        Radius: 绕出波导半径 (um)
        GapCoup: 耦合间隙 (um)
        layer: 光学层
        Name: 组件名称

    Returns:
        包含 in1, in2, out1, out2 端口的 Component
    """
    c = gf.Component()
    DeltaC = GapCoup + WidthWG
    # path
    coups = gf.Section(width=WidthWG, offset=0, layer=oplayer, port_names=("in", "out"))
    coupcs = gf.CrossSection(sections=[coups])
    couppath = gf.path.straight(length=LengthCoup)
    coupbridge = gf.path.straight(length=LengthBridge)
    coupbend = gf.path.straight(length=LengthBend)
    cbpath1 = gf.path.euler(radius=Radius, angle=30, use_eff=True)
    cbpath2 = gf.path.euler(radius=Radius, angle=-30, use_eff=True)
    coup1 = couppath + cbpath1 +coupbend+ cbpath2 + coupbridge
    coupb1 = cbpath2 + coupbend +cbpath1
    coupbridge2 = gf.path.straight(length=LengthBridge/2)
    coupheat = coupbend+cbpath2+coupbridge2
    # coupler waveguide
    CW1 = c << gf.path.extrude(coup1, cross_section=coupcs)
    CW2 = c << gf.path.extrude(coup1, cross_section=coupcs)
    CW2.connect("out", other=CW1.ports["in"])
    CW2.movey(-DeltaC)
    CW2.rotate(180, center=CW2.ports["out"].center)
    CB1 = c << gf.path.extrude(coupb1, cross_section=coupcs)
    CB2 = c << gf.path.extrude(coupb1, cross_section=coupcs)
    CB1.connect("out", other=CW1.ports["in"])
    CB2.connect("in", other=CW2.ports["in"])
    CBs1 = c << GfCStraight(width=WidthWG, length=CW2.ports["out"].center[0]-CB1.ports["in"].center[0]+DeltaOut, layer=oplayer)
    CBs2 = c << GfCStraight(width=WidthWG, length=CW2.ports["out"].center[0]-CB1.ports["in"].center[0]+DeltaOut, layer=oplayer)
    CBs1.connect("o2", other=CW2.ports["out"])
    CBs2.connect("o1", other=CW1.ports["out"])
    # set port
    c.add_port(name="Input2", port=CB1.ports["in"])
    c.add_port(name="Input1", port=CBs1.ports["o1"])
    c.add_port(name="Output1", port=CB2.ports["out"])
    c.add_port(name="Output2", port=CBs2.ports["o2"])
    c.add_port(name="Bridge1", port=CW1.ports["out"])
    c.add_port(name="Bridge2", port=CW2.ports["out"])
    # if heater
    if IsHeat:
        heater = DifferentHeater(PathHeat=coupheat, WidthHeat=WidthHeat, DeltaHeat=DeltaHeat, GapHeat=GapHeat,
                                 WidthWG=WidthWG, WidthRoute=20,
                                 heatlayer=heatlayer, TypeHeater=TypeHeater, vialayer=vialayer, routelayer=routelayer)
        heaterL = c << heater
        heaterR = c << heater
        heaterL.connect("HeatOut", other=CBs1.ports["o2"], allow_width_mismatch=True, allow_layer_mismatch=True,
                        allow_type_mismatch=True)
        heaterL.movex(LengthBridge/2)
        heaterR.connect("HeatOut", other=CBs2.ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True,
                        allow_type_mismatch=True)
        heaterR.movex(-LengthBridge/2)
        for port in heaterL.ports:
            if "Heat" in port.name:
                c.add_port("L" + port.name, port=heaterL.ports[port.name])
        for port in heaterR.ports:
            if "Heat" in port.name:
                c.add_port("R" + port.name, port=heaterR.ports[port.name])
    c.flatten()
    return c


# %% PMZI:pulley coupler MZI
@gf.cell
def PMZI(
        WidthNear: float = 0.8,
        WidthRing: float = 1,
        WidthHeat: float = 8,
        AngleCouple: float = 20,
        AngleIn: float = 20,
        AngleBend: float = 90,
        AngleOut1: float = 90,
        AngleOut2: float = 90,
        LengthBridge=300,
        LengthBend=200,
        LengthTaper=200,
        Radius=200,
        r_radius_false=100,
        GapCoup=1,
        GapHeat=1,
        DeltaHeat=0,
        IsHeat: bool = True,
        TypeHeater: str = "default",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
     创建一个Pulley耦合 MZI 结构。

     Args:
         WidthNear: 近端波导宽度 (um)
         WidthRing: 环形波导宽度 (um)
         WidthHeat: 加热器宽度 (um)
         AngleCouple: 耦合角度 (度)
         AngleIn: 输入角度 (度)
         AngleBend: 弯曲角度 (度)
         AngleOut1: 输出角度 1 (度)
         AngleOut2: 输出角度 2 (度)
         LengthBridge: 桥接长度 (um)
         LengthBend: 弯曲长度 (um)
         LengthTaper: 锥形波导长度 (um)
         Radius: 弯曲半径 (um)
         r_radius_false: 假弯曲半径 (um)
         GapCoup: 耦合间隙 (um)
         GapHeat: 加热器间隙 (um)
         DeltaHeat: 加热器偏移 (um)
         oplayer: 光学层
         heatlayer: 加热层
         Name: 组件名称

     Returns:
         包含 Input1, Input2, Output1, Output2 端口的 Component
     """
    c = gf.Component()
    # Section and CrossSections
    S_near = gf.Section(width=WidthNear, offset=0, layer=oplayer, port_names=("in", "out"))
    S_ring = gf.Section(width=WidthRing, offset=0, layer=oplayer, port_names=("in", "out"))
    CS_near = gf.CrossSection(sections=[S_near])
    CS_ring = gf.CrossSection(sections=[S_ring])
    # coupler
    Coup = PulleyCoupler2X2(
        WidthIn=WidthRing, WidthOut=WidthNear, GapCoup=GapCoup, AngleIn=AngleIn, AngleCouple=AngleCouple,
        oplayer=oplayer,
    )
    Coup1 = c << Coup
    Coup2 = c << Coup
    # bridge waveguide
    ## bridgh path
    path_ringbend = euler_Bend_Half(radius=Radius, angle=-AngleBend / 2 + AngleIn / 2, use_eff=False)
    path_ringstr = gf.path.straight(length=LengthBend)
    path_bridgebend = gf.path.euler(radius=r_radius_false, angle=AngleBend / 2, use_eff=False)
    path_bridgestr = gf.path.straight(length=LengthBridge)
    path_total = path_ringbend + path_ringstr + path_bridgebend + path_bridgestr
    path_heat = path_bridgestr
    # taper in MZI
    bridgeL = c << gf.path.extrude(path_total, cross_section=CS_ring)
    bridgeR = c << gf.path.extrude(path_total, cross_section=CS_ring)
    taper_1 = c << gf.c.taper(width1=WidthNear, width2=WidthRing, length=LengthTaper, layer=oplayer)
    taper_2 = c << gf.c.taper(width1=WidthNear, width2=WidthRing, length=LengthTaper, layer=oplayer)
    taper_1.connect("o1", other=Coup1.ports["out2"], mirror=True)
    bridgeR.connect("out", other=taper_1.ports["o2"], mirror=True)
    Coup2.connect("out1", other=bridgeR.ports["in"])
    taper_2.connect("o1", other=Coup2.ports["out2"])
    bridgeL.connect("out", other=taper_2.ports["o2"], mirror=True)
    # coupler ring out
    path_ringout1 = gf.path.arc(radius=Radius, angle=-AngleOut1 + AngleIn / 2)
    path_ringout2 = gf.path.arc(radius=Radius, angle=-AngleOut2 + AngleIn / 2)
    ringout_1 = c << gf.path.extrude(path_ringout1, cross_section=CS_ring)
    ringout_2 = c << gf.path.extrude(path_ringout2, cross_section=CS_ring)
    ringout_1.connect("out", other=Coup1.ports["in1"], mirror=True)
    ringout_2.connect("out", other=Coup2.ports["in1"], mirror=True)
    # set port
    c.add_port(name="Input1", port=ringout_2.ports["in"])
    c.add_port(name="Input2", port=Coup2.ports["in2"])
    c.add_port(name="Output2", port=ringout_1.ports["in"])
    c.add_port(name="Output1", port=Coup1.ports["in2"])
    # if heater
    if IsHeat:
        heater = DifferentHeater(PathHeat=path_heat, WidthHeat=WidthHeat, DeltaHeat=DeltaHeat, GapHeat=GapHeat,
                                 WidthWG=WidthNear, WidthRoute=20,
                                 heatlayer=heatlayer, TypeHeater=TypeHeater, vialayer=vialayer, routelayer=routelayer)
        heaterL = c.add_ref(heater)
        heaterR = c.add_ref(heater)
        heaterL.connect("HeatOut", other=taper_2.ports["o2"], allow_width_mismatch=True, allow_layer_mismatch=True,
                        allow_type_mismatch=True)
        heaterR.connect("HeatOut", other=taper_1.ports["o2"], allow_width_mismatch=True, allow_layer_mismatch=True,
                        allow_type_mismatch=True)
        for port in heaterL.ports:
            if "Heat" in port.name:
                c.add_port("L" + port.name, port=heaterL.ports[port.name])
        for port in heaterR.ports:
            if "Heat" in port.name:
                c.add_port("R" + port.name, port=heaterR.ports[port.name])
    c.flatten()
    add_labels_to_ports(c)
    return c


# %% PMZIHSn:pulley coupler MZI width Snake Heater
@gf.cell
def PMZIHSn(
        WidthNear: float = 0.8,
        WidthRing: float = 1,
        WidthHeat: float = 8,
        AngleCouple: float = 20,
        AngleIn: float = 20,
        AngleBend: float = 30,
        AngleOut1: float = 90,
        AngleOut2: float = 90,
        LengthBridge=300,
        LengthBend=200,
        LengthTaper=200,
        Radius=200,
        r_radius_false=100,
        GapCoup=1,
        GapHeat=1,
        DeltaHeat=0,
        IsHeat=True,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个带有蛇形加热器的 Pulley 耦合 MZI 结构。

    Args:
        WidthNear: 近端波导宽度 (um)
        WidthRing: 环形波导宽度 (um)
        WidthHeat: 加热器宽度 (um)
        AngleCouple: 耦合角度 (度)
        AngleIn: 输入角度 (度)
        AngleBend: 弯曲角度 (度)
        AngleOut1: 输出角度 1 (度)
        AngleOut2: 输出角度 2 (度)
        LengthBridge: 桥接长度 (um)
        LengthBend: 弯曲长度 (um)
        LengthTaper: 锥形波导长度 (um)
        Radius: 弯曲半径 (um)
        r_radius_false: 假弯曲半径 (um)
        GapCoup: 耦合间隙 (um)
        GapHeat: 加热器间隙 (um)
        DeltaHeat: 加热器偏移 (um)
        IsHeat: 是否包含加热器
        oplayer: 光学层
        heatlayer: 加热层
        Name: 组件名称

    Returns:
        包含 Input1, Input2, Output1, Output2 端口的 Component 和加热器 Component
    """
    return PMZI(
        WidthNear=WidthNear,
        WidthRing=WidthRing,
        WidthHeat=WidthHeat,
        AngleCouple=AngleCouple,
        AngleIn=AngleIn,
        AngleBend=AngleBend,
        AngleOut1=AngleOut1,
        AngleOut2=AngleOut2,
        LengthBridge=LengthBridge,
        LengthBend=LengthBend,
        LengthTaper=LengthTaper,
        Radius=Radius,
        r_radius_false=r_radius_false,
        GapCoup=GapCoup,
        GapHeat=GapHeat,
        DeltaHeat=DeltaHeat,
        IsHeat=IsHeat,
        oplayer=oplayer,
        heatlayer=heatlayer,
        TypeHeater="snake",
    )


# %% SagnacRing
@gf.cell
def SagnacRing(
        WidthOut: float = 1.55,
        WidthIn: float = 2,
        WidthSingle: float = 2,
        LengthTaper: float = 200,
        AngleCouple=11,
        AngleIn=60,
        RadiusIn=200,
        RadiusBend=100,
        GapCoup=0.3,
        IsTaperIn: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,

) -> Component:
    """
    创建一个 Sagnac 环形结构。

    Args:
        WidthOut: 输出波导宽度 (um)
        WidthIn: 输入波导宽度 (um)
        LengthTaper: 锥形波导长度 (um)
        AngleCouple: 耦合角度 (度)
        RadiusIn: 环形波导半径 (um)
        RadiusBend: 弯曲半径 (um)
        GapCoup: 耦合间隙 (um)
        oplayer: 光学层
        Name: 组件名称

    Returns:
        包含 input 和 output 端口的 Component
    """
    c = gf.Component()
    PC = c << PulleyCoupler2X2(WidthIn=WidthIn, WidthOut=WidthOut, AngleCouple=AngleCouple, RadiusIn=RadiusIn,
                               GapCoup=GapCoup, oplayer=oplayer, IsParallel=False, AngleIn=AngleIn)
    taper_coup2ring = c << gf.c.taper(width1=WidthOut, width2=WidthIn, length=LengthTaper, layer=oplayer)
    taper_coup2ring.connect("o1", other=PC.ports["out2"])
    bendpath_ring2coup = euler_Bend_Half(angle=-AngleIn, radius=RadiusBend, p=1, use_eff=False)
    bend_ring2coup = c << gf.path.extrude(bendpath_ring2coup, width=WidthIn, layer=oplayer)
    bend_ring2coup.connect("o1", other=PC.ports["out1"])
    bendpath_ring2out = euler_Bend_Half(angle=AngleIn, radius=RadiusBend, p=1, use_eff=False)
    bend_ring2out = c << gf.path.extrude(bendpath_ring2out, width=WidthIn, layer=oplayer)
    bend_ring2out.connect("o1", other=PC.ports["in1"])
    routering = gf.routing.get_bundle([bend_ring2coup.ports["o2"]], [taper_coup2ring.ports["o2"]], width=WidthIn,
                                      layer=oplayer
                                      , bend=GfCBendEuler(width=WidthIn, radius=RadiusBend, with_arc_floorplan=False,
                                                          p=0.8), )
    for route in routering:
        c.add(route.references)
    bend = c << GfCBendEuler(angle=90, width=WidthIn, layer=oplayer, radius=RadiusBend, with_arc_floorplan=False, p=1)
    bend.connect("o1", bend_ring2out.ports["o2"])
    if IsTaperIn:
        taper_in = c << gf.c.taper(width1=WidthSingle, width2=WidthOut, length=LengthTaper, layer=oplayer)
        taper_in.connect("o2", PC.ports["in2"])
        c.add_port("input", port=taper_in.ports["o1"])
    else:
        c.add_port("input", port=PC.ports["in2"])
    c.add_port("output", port=bend.ports["o2"])
    c.add_port("o1", port=c.ports["input"])
    c.add_port("o2", port=bend.ports["o2"])
    return c


__all__ = ['PMZI', 'PMZIHSn', 'PulleyCoupler2X2', 'DMZI', 'SagnacRing']
