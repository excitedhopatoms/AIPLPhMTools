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
    创建一个 2x2 的 "Pulley" 型定向耦合器。
    "Pulley" 通常指弯曲的耦合区域，类似于滑轮的形状。

    参数:
        WidthOut (float): 耦合器输出臂的波导宽度 (单位: um)。默认为 1.55 um。
        WidthIn (float): 耦合器输入臂（或弯曲部分）的波导宽度 (单位: um)。默认为 2.0 um。
        AngleCouple (float): 定义耦合区域弯曲程度的角度。这通常是构成耦合器的一个弯曲段的角度。默认为 11.0 度。
        AngleIn (float | None): 输入端口处弯曲波导的角度。如果为 None，则会根据 AngleCouple 计算（通常 AngleCouple*2）。默认为 None。
        RadiusIn (float): 输入端口处弯曲波导的半径 (单位: um)。默认为 200.0 um。
        GapCoup (float): 两个耦合波导之间的最小间隙 (单位: um)。默认为 0.3 um。
        IsParallel (bool): 如果为 True，则调整输入弯曲使得输出端口与输入端口平行。默认为 False。
        oplayer (LayerSpec): 光学波导层定义。默认为 LAYER.WG。

    返回:
        Component: 生成的 2x2 Pulley 耦合器组件。

    端口:
        in1: 第一个输入端口。
        in2: 第二个输入端口。
        out1: 第一个输出端口。
        out2: 第二个输出端口。
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
    创建一个基于直波导定向耦合器的 2x2 马赫-曾德干涉仪 (MZI) 组件。
    MZI 的两个臂可以带有加热器用于相位调制。

    参数:
        WidthWG (float): MZI 波导宽度。默认为 0.8 um。
        WidthHeat (float): 加热器宽度。默认为 8.0 um。
        LengthCoup (float): 定向耦合器的耦合段长度。默认为 100.0 um。
        LengthBridge (float): MZI 臂长 (两个耦合器之间的主要直波导段)。默认为 300.0 um。
        LengthBend (float): MZI 臂中用于展开并放置加热器的额外直波导段长度。默认为 300.0 um。
        Radius (float): MZI 臂中S弯或欧拉弯的半径。默认为 200.0 um。
        GapCoup (float): 定向耦合器的耦合间隙。默认为 1.0 um。
        GapHeat (float): 波导与加热器之间的间隙。默认为 1.0 um。
        DeltaHeat (float): 加热器的偏移或尺寸参数。默认为 0。
        DeltaOut (float): 输出端口的额外水平偏移调整。默认为 -40.0 um。
        IsHeat (bool): 是否在MZI臂上添加加热器。默认为 True。
        TypeHeater (str): 加热器类型 (例如 "default", "snake")。默认为 "default"。
        oplayer (LayerSpec): 光学波导层。
        heatlayer (LayerSpec): 加热器层。
        routelayer (LayerSpec): 加热器布线层。
        vialayer (LayerSpec): 加热器过孔层。

    返回:
        Component: 生成的 DMZI 组件。

    端口:
        Input1, Input2: MZI 的两个输入端口。
        Output1, Output2: MZI 的两个输出端口。
        Bridge1, Bridge2: MZI 两个臂上特定位置的参考端口 (可能用于监控或调试)。
        (如果 IsHeat=True, 还会有 LHeatIn, LHeatOut, RHeatIn, RHeatOut 等加热器端口)
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
     创建一个基于 Pulley 型耦合器的马赫-曾德干涉仪 (MZI) 结构。
     MZI 的两个臂可以带有加热器用于相位调制。

     参数:
         WidthNear (float): Pulley耦合器中总线波导的宽度。默认为 0.8 um。
         WidthRing (float): Pulley耦合器中弯曲/环形部分的波导宽度。默认为 1.0 um。
         WidthHeat (float): 加热器宽度。默认为 8.0 um。
         AngleCouple (float): Pulley耦合器的耦合区域角度。默认为 20.0 度。
         AngleIn (float): Pulley耦合器输入臂的弯曲角度。默认为 20.0 度。
         AngleBend (float): MZI臂中主导弯曲的角度 (用于分开两臂)。默认为 90.0 度。
         AngleOut1 (float): MZI第一个输出端口的引出弯曲角度。默认为 90.0 度。
         AngleOut2 (float): MZI第二个输出端口的引出弯曲角度。默认为 90.0 度。
         LengthBridge (float): MZI臂的平行直波导段长度。默认为 300.0 um。
         LengthBend (float): MZI臂中弯曲后的直波导段长度 (常用于放置加热器)。默认为 200.0 um。
         LengthTaper (float): MZI臂中连接耦合器和主臂的锥形波导长度。默认为 200.0 um。
         Radius (float): MZI臂和输出引出弯的主要弯曲半径。默认为 200.0 um。
         r_radius_false (float): MZI臂中某些辅助或过渡弯曲的半径。默认为 100.0 um。
         GapCoup (float): Pulley耦合器的耦合间隙。默认为 1.0 um。
         GapHeat (float): 波导与加热器之间的间隙。默认为 1.0 um。
         DeltaHeat (float): 加热器的偏移或尺寸参数。默认为 0。
         IsHeat (bool): 是否在MZI臂上添加加热器。默认为 True。
         TypeHeater (str): 加热器类型。默认为 "default"。
         oplayer (LayerSpec): 光学波导层。
         heatlayer (LayerSpec): 加热器层。
         routelayer (LayerSpec): 加热器布线层。
         vialayer (LayerSpec): 加热器过孔层。

     返回:
         Component: 生成的 PMZI 组件。

     端口:
         Input1, Input2: MZI 的两个输入端口。
         Output1, Output2: MZI 的两个输出端口。
        (如果 IsHeat=True, 还会有 LHeatIn, LHeatOut, RHeatIn, RHeatOut 等加热器端口)
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
    创建一个带有蛇形加热器的 Pulley 型耦合马赫-曾德干涉仪 (MZI) 组件。
    此函数是 `PMZI` 组件的一个特例，其中加热器类型被固定为 "snake"。

    参数:
        (与 `PMZI` 函数的参数基本一致，但 `TypeHeater` 被内部设置为 "snake")
        AngleBend (float): MZI臂中主导弯曲的角度。默认为 30.0 度 (与PMZI默认值90不同)。

    返回:
        Component: 生成的带有蛇形加热器的 PMZI 组件。
                   (注意：原代码中其他类似的 HSn 函数返回 (Component, HeaterComponent)，
                    但此函数直接调用 PMZI，PMZI 返回单个 Component。行为可能需要统一。)
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
    创建一个 Sagnac 环形干涉仪结构。
    该结构通常使用一个耦合器将光分束送入一个环形路径，并在同一点将两束反向传播的光重新耦合。

    参数:
        WidthOut (float): Pulley耦合器中连接到Sagnac环的臂的宽度。默认为 1.55 um。
        WidthIn (float): Pulley耦合器中另一组臂及Sagnac环主体部分的宽度。默认为 2.0 um。
        WidthSingle (float): 组件外部输入/输出端口的单模波导宽度。默认为 1.0 um。
        LengthTaper (float): 用于宽度过渡的锥形波导长度。默认为 200.0 um。
        AngleCouple (float): Pulley耦合器的耦合区域角度。默认为 11.0 度。
        AngleIn (float): Pulley耦合器内部弯曲臂的角度。默认为 60.0 度。
        RadiusIn (float): Pulley耦合器内部弯曲臂的半径。默认为 200.0 um。
        RadiusBend (float): Sagnac环路中主要弯曲（如引出弯）的半径。默认为 100.0 um。
        GapCoup (float): Pulley耦合器的耦合间隙。默认为 0.3 um。
        IsTaperIn (bool): 是否在组件的 "input" 端口处添加一个从 WidthSingle 到 WidthOut 的锥形。默认为 True。
        oplayer (LayerSpec): 光学波导层。
        heatlayer, routelayer, vialayer: (未在当前光学路径中使用) 可能用于未来的加热器等扩展。

    返回:
        Component: 生成的 Sagnac 环组件。

    端口:
        input: Sagnac环的输入端口。
        output: Sagnac环的输出端口。
        o1: 等同于 input 端口。
        o2: 等同于 output 端口。
    """
    c = gf.Component()
    PC = c << PulleyCoupler2X2(WidthIn=WidthIn, WidthOut=WidthOut, AngleCouple=AngleCouple, RadiusIn=RadiusIn,
                               GapCoup=GapCoup, oplayer=oplayer, IsParallel=False, AngleIn=AngleIn)
    taper_coup2ring = c << gf.c.taper(width1=WidthOut, width2=WidthIn, length=LengthTaper, layer=oplayer)
    taper_coup2ring.connect("o1", other=PC.ports["out2"],mirror=True)
    bendpath_ring2coup = euler_Bend_Half(angle=-AngleIn, radius=RadiusBend, p=1, use_eff=False)
    bend_ring2coup = c << gf.path.extrude(bendpath_ring2coup, width=WidthIn, layer=oplayer)
    bend_ring2coup.connect("o1", other=PC.ports["out1"],mirror=True)
    bendpath_ring2out = euler_Bend_Half(angle=AngleIn, radius=RadiusBend, p=1, use_eff=False)
    bend_ring2out = c << gf.path.extrude(bendpath_ring2out, width=WidthIn, layer=oplayer)
    bend_ring2out.connect("o1", other=PC.ports["in1"],mirror=True)
    gf.routing.route_single(c,bend_ring2coup.ports["o2"], taper_coup2ring.ports["o2"], route_width=WidthIn,radius=RadiusBend*1.5,
                                      layer=oplayer)
    # for route in routering:
    #     c.add(route.references)
    bend = c << GfCBendEuler(angle=90, width=WidthIn, layer=oplayer, radius=RadiusBend, p=1,with_arc_floorplan=False)
    bend.connect("o1", bend_ring2out.ports["o2"],mirror=True)
    if IsTaperIn:
        taper_in = c << gf.c.taper(width1=WidthSingle, width2=WidthOut, length=LengthTaper, layer=oplayer)
        taper_in.connect("o2", PC.ports["in2"])
        c.add_port("input", port=taper_in.ports["o1"])
    else:
        c.add_port("input", port=PC.ports["in2"])
    c.add_port("output", port=bend.ports["o2"])
    c.add_port("o1", port=c.ports["input"])
    c.add_port("o2", port=bend.ports["o2"])
    c.flatten()
    return c


__all__ = ['PMZI', 'PMZIHSn', 'PulleyCoupler2X2', 'DMZI', 'SagnacRing']
