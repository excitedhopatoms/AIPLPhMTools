from .BasicDefine import *


# %% RaceTrackPulley
@gf.cell
def RaceTrackPulley(
        WidthRing: float = 8,
        WidthNear: float = 5,
        WidthHeat: float = 10,
        LengthRun: float = 200,
        RadiusRing: float = 100,
        GapRing: float = 1,
        AngleCouple: float = 20,
        GapHeat: float = 10,
        DeltaHeat: float = 0,
        IsAD: bool = True,
        IsHeat: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        Name: str = "RaceTrack_Pulley"
) -> Component:
    """
    创建一个环形跑道波导组件，支持输入、输出、添加和丢弃端口。

    参数：
        WidthRing: 环形波导的宽度（单位：um）。
        WidthNear: 耦合波导的宽度（单位：um）。
        LengthRun: 直线部分的长度（单位：um）。
        RadiusRing: 环形波导的半径（单位：um）。
        GapRing: 环形波导与耦合波导之间的间距（单位：um）。
        AngleCouple: 耦合角度（单位：度）。
        IsAD: 是否添加添加和丢弃端口。
        oplayer: 波导层的定义。
        Name: 组件名称。

    返回：
        Component: 生成的环形跑道波导组件。

    端口：
        Input: 输入端口。
        Through: 直通端口。
        Add: 添加端口（如果 IsAD 为 True）。
        Drop: 丢弃端口（如果 IsAD 为 True）。
        Rcen1, Rcen2: 环形波导的中心端口。
    """
    c = gf.Component()
    layer = oplayer
    secring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("in", "out"))
    secnring = gf.Section(width=WidthNear, offset=0, layer=layer, port_names=("in", "out"))
    wgring = gf.CrossSection(sections=[secring])
    wgnear = gf.CrossSection(sections=[secnring])
    # run ring path
    rrun1 = gf.path.straight(length=LengthRun / 2)
    rring1 = gf.path.arc(radius=RadiusRing, angle=70)
    rring2 = gf.path.arc(radius=RadiusRing, angle=-70)
    rb1 = euler_Bend_Half(radius=RadiusRing, angle=20, p=0.5)
    rb2 = euler_Bend_Half(radius=RadiusRing, angle=-20, p=0.5)
    RingPath1 = rring1 + rb1 + rrun1
    RingPath2 = rring2 + rb2 + rrun1
    RP1 = c << gf.path.extrude(RingPath1, cross_section=wgring)
    RP2 = c << gf.path.extrude(RingPath2, cross_section=wgring)
    RP3 = c << gf.path.extrude(RingPath1, cross_section=wgring)
    RP4 = c << gf.path.extrude(RingPath2, cross_section=wgring)
    RP1.connect("out", other=RP4.ports["out"])
    RP2.connect("in", other=RP1.ports["in"])
    RP3.connect("out", other=RP2.ports["out"])
    RP4.connect("in", other=RP3.ports["in"])
    # out port
    r_delta = WidthRing / 2 + GapRing + WidthNear / 2
    rcoup1 = gf.path.arc(radius=RadiusRing + r_delta, angle=-AngleCouple / 2)
    rcoup2 = gf.path.arc(radius=RadiusRing + r_delta, angle=AngleCouple / 2)
    rcb1 = euler_Bend_Half(radius=RadiusRing + r_delta, angle=-AngleCouple / 2, p=0.5)
    rcb2 = euler_Bend_Half(radius=RadiusRing + r_delta, angle=AngleCouple / 2, p=0.5)
    RingCoup1 = rcoup1 + rcb2
    RingCoup2 = rcoup2 + rcb1
    # input through
    RC1 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
    RC2 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
    RC1.connect("in", other=RP3.ports["in"], allow_width_mismatch=True)
    RC1.movey(r_delta)
    RC2.connect("in", other=RC1.ports["in"])
    # ports:
    c.add_port(name="Input", port=RC1.ports["out"], orientation=0)
    c.add_port(name="Through", port=RC2.ports["out"])
    # add drop
    if IsAD:
        RC3 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
        RC4 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
        RC3.connect("in", other=RP1.ports["in"], allow_width_mismatch=True)
        RC3.movey(-r_delta)
        RC4.connect("in", other=RC3.ports["in"])
        c.add_port(name="Add", port=RC3.ports["out"], orientation=180)
        c.add_port(name="Drop", port=RC4.ports["out"])
    c.add_port(name="Rcen1", port=RP1.ports["out"])
    c.add_port(name="Rcen2", port=RP3.ports["out"])
    return c


# %% RaceTrackPulley2
@gf.cell
def RaceTrackStr(
        WidthRing: float = 8,
        WidthHeat: float = 10,
        WidthRoute: float = 20,
        LengthRun: float = 200,
        RadiusRing: float = 100,
        GapRun: float = 1,
        LengthCouple: float = 200,
        GapHeat: float = 10,
        DeltaHeat: float = 0,
        IsAD: bool = True,
        IsHeat: bool = True,
        TypeHeater: str = "center",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        Name: str = "RaceTrack_Pulley"
) -> Component:
    """
    创建一个环形跑道波导组件，支持输入、输出、添加和丢弃端口，并可选添加标签。

    参数：
        WidthRing: 环形波导的宽度（单位：um）。
        LengthRun: 直线部分的长度（单位：um）。
        RadiusRing: 环形波导的半径（单位：um）。
        GapRun: 环形波导与耦合波导之间的间距（单位：um）。
        LengthCouple: 耦合部分的长度（单位：um）。
        IsAD: 是否添加添加和丢弃端口。
        IsLabels: 是否添加端口标签。
        oplayer: 波导层的定义。
        heatlayer: 加热层的定义。
        Name: 组件名称。

    返回：
        Component: 生成的环形跑道波导组件。

    端口：
        Input: 输入端口。
        Through: 直通端口。
        Add: 添加端口（如果 IsAD 为 True）。
        Drop: 丢弃端口（如果 IsAD 为 True）。
        Rcen1, Rcen2: 环形波导的中心端口。
    """
    if TypeHeater == "center":
        return RaceTrackStrH2(
            WidthRing=WidthRing,
            WidthHeat=WidthHeat,
            WidthRoute = WidthRoute,
            LengthRun=LengthRun,
            RadiusRing=RadiusRing,
            GapRun=GapRun,
            GapRoute=GapHeat,
            DeltaHeat=DeltaHeat,
            LengthCouple=LengthCouple,
            IsAD=True,
            IsHeat=IsHeat,
            oplayer=oplayer,
            heatlayer=heatlayer,
            vialayer=vialayer,
            routelayer=routelayer,
        )
    c = gf.Component()
    layer = oplayer
    secring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("in", "out"))
    secnring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("in", "out"))
    wgring = gf.CrossSection(sections=[secring])
    wgnear = gf.CrossSection(sections=[secnring])
    # run ring path
    CRaceTrack = gf.Component()
    rrun1 = gf.path.straight(length=LengthRun / 2)
    rring1 = gf.path.arc(radius=RadiusRing, angle=60)
    rring2 = gf.path.arc(radius=RadiusRing, angle=-60)
    rb1 = euler_Bend_Half(radius=RadiusRing, angle=30, p=0.5)
    rb2 = euler_Bend_Half(radius=RadiusRing, angle=-30, p=0.5)
    RingPath1 = rring1 + rb1 + rrun1
    RingPath2 = rring2 + rb2 + rrun1
    RP1 = CRaceTrack << gf.path.extrude(RingPath1, cross_section=wgring)
    RP2 = CRaceTrack << gf.path.extrude(RingPath2, cross_section=wgring)
    RP3 = CRaceTrack << gf.path.extrude(RingPath1, cross_section=wgring)
    RP4 = CRaceTrack << gf.path.extrude(RingPath2, cross_section=wgring)
    RP1.connect("out", other=RP4.ports["out"])
    RP2.connect("in", other=RP1.ports["in"])
    RP3.connect("out", other=RP2.ports["out"])
    RP4.connect("in", other=RP3.ports["in"])
    c << CRaceTrack
    # out port
    rcoup1 = gf.path.straight(length=LengthCouple / 2)
    rcoup2 = gf.path.straight(length=LengthCouple / 2)
    rcb1 = euler_Bend_Half(radius=RadiusRing, angle=15, p=0.5)
    rcb2 = euler_Bend_Half(radius=RadiusRing, angle=-15, p=0.5)
    RingCoup1 = rcb2 + rcb1 + rcoup1
    RingCoup2 = rcoup2 + rcb1 + rcb2
    # input through
    RC1 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
    RC2 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
    RC1.connect("out", other=RP3.ports["out"], allow_width_mismatch=True)
    RC1.movex(-GapRun - WidthRing)
    RC2.connect("in", other=RC1.ports["out"])
    # ports:
    c.add_port(name="Input", port=RC1.ports["in"])
    c.add_port(name="Through", port=RC2.ports["out"])
    # add drop
    if IsAD:
        RC3 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
        RC4 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
        RC3.connect("out", other=RP1.ports["out"], allow_width_mismatch=True)
        RC3.movex(GapRun + WidthRing)
        RC4.connect("in", other=RC3.ports["out"])
        c.add_port(name="Add", port=RC3.ports["in"])
        c.add_port(name="Drop", port=RC4.ports["out"])
    c.add_port(name="Rcen1", port=RP1.ports["out"])
    c.add_port(name="Rcen2", port=RP3.ports["out"])
    # if IsLabels:
    add_labels_to_ports(c)
    return c

# %% RaceTrackStrH2
def RaceTrackStrH2(
        WidthRing: float = 8,
        WidthHeat: float = 8,
        WidthRoute: float = 50,
        DeltaHeat: float = -10,
        GapRoute: float = 50,
        LengthRun: float = 200,
        RadiusRing: float = 500,
        GapRun: float = 1,
        LengthCouple: float = 200,
        IsAD: bool = True,
        IsHeat: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        Name: str = "RaceTrack_Pulley"
) -> Component:
    """
     创建一个带有加热电极的环形跑道波导组件，支持输入、输出、添加和丢弃端口。

     参数：
         WidthRing: 环形波导的宽度（单位：um）。
         WidthHeat: 加热电极的宽度（单位：um）。
         WidthRoute: 加热电极路径的宽度（单位：um）。
         DeltaHeat: 加热电极中心距离波导中心的偏移量（单位：um）。
         GapRoute: 加热电极之间的间距（单位：um）。
         LengthRun: 直线部分的长度（单位：um）。
         RadiusRing: 环形波导的半径（单位：um）。
         GapRun: 环形波导与耦合波导之间的间距（单位：um）。
         LengthCouple: 耦合部分的长度（单位：um）。
         IsAD: 是否添加添加和丢弃端口。
         IsLabels: 是否添加端口标签。
         IsHeat: 是否添加加热电极。
         oplayer: 波导层的定义。
         heatlayer: 加热层的定义。
         Name: 组件名称。

     返回：
         Component: 生成的环形跑道波导组件。

     端口：
         Input: 输入端口。
         Through: 直通端口。
         Add: 添加端口（如果 IsAD 为 True）。
         Drop: 丢弃端口（如果 IsAD 为 True）。
         Rcen1, Rcen2: 环形波导的中心端口。
         HeatIn: 加热输入端口（如果 IsHeat 为 True）。
     """
    c = gf.Component()
    # h = gf.Component(Name + "heat")
    layer = oplayer
    secring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("in", "out"))
    secnring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("in", "out"))
    wgring = gf.CrossSection(sections=[secring])
    wgnear = gf.CrossSection(sections=[secnring])
    # run ring path
    CRaceTrack = gf.Component()
    rrun1 = gf.path.straight(length=LengthRun / 2)
    rring1 = gf.path.arc(radius=RadiusRing, angle=60)
    rring2 = gf.path.arc(radius=RadiusRing, angle=-60)
    rb1 = euler_Bend_Half(radius=RadiusRing, angle=30, p=0.5)
    rb2 = euler_Bend_Half(radius=RadiusRing, angle=-30, p=0.5)
    RingPath1 = rring1 + rb1 + rrun1
    RingPath2 = rring2 + rb2 + rrun1
    RP1 = CRaceTrack << gf.path.extrude(RingPath1, cross_section=wgring)
    RP2 = CRaceTrack << gf.path.extrude(RingPath2, cross_section=wgring)
    RP3 = CRaceTrack << gf.path.extrude(RingPath1, cross_section=wgring)
    RP4 = CRaceTrack << gf.path.extrude(RingPath2, cross_section=wgring)
    RP2.connect("in", other=RP1.ports["in"])
    RP3.connect("out", other=RP2.ports["out"])
    RP4.connect("in", other=RP3.ports["in"])
    c << CRaceTrack
    # out port
    rcoup1 = gf.path.straight(length=LengthCouple / 2)
    rcoup2 = gf.path.straight(length=LengthCouple / 2)
    rcb1 = euler_Bend_Half(radius=RadiusRing, angle=15, p=0.5)
    rcb2 = euler_Bend_Half(radius=RadiusRing, angle=-15, p=0.5)
    RingCoup1 = rcb2 + rcb1 + rcoup1
    RingCoup2 = rcoup2 + rcb1 + rcb2
    # input through
    RC1 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
    RC2 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
    RC1.connect("out", other=RP3.ports["out"])
    RC1.movex(-GapRun - WidthRing)
    RC2.connect("in", other=RC1.ports["out"])
    # ports:
    c.add_port(name="Input", port=RC1.ports["in"])
    c.add_port(name="Through", port=RC2.ports["out"])
    # add drop
    if IsAD:
        RC3 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
        RC4 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
        RC3.connect("out", other=RP1.ports["out"])
        RC3.movex(GapRun + WidthRing)
        RC4.connect("in", other=RC3.ports["out"])
        c.add_port(name="Add", port=RC3.ports["in"])
        c.add_port(name="Drop", port=RC4.ports["out"])
    c.add_port(name="Rcen1", port=RP1.ports["out"])
    c.add_port(name="Rcen2", port=RP3.ports["out"])

    # heat part
    if IsHeat:
        h_plus = gf.Component()
        h_minus = gf.Component()
        secheat1 = gf.Section(width=WidthHeat, offset=-DeltaHeat, layer=heatlayer, port_names=("in", "out"))
        secheatout1 = gf.Section(width=RadiusRing, offset=-(DeltaHeat + WidthHeat / 2 + RadiusRing / 2), layer=heatlayer,
                                 port_names=("in", "out"))
        secheatpad1 = gf.Section(width=RadiusRing - (WidthHeat / 2 - DeltaHeat + GapRoute),
                                 offset=RadiusRing - (RadiusRing - WidthHeat / 2 + DeltaHeat - GapRoute) / 2,
                                 layer=heatlayer, port_names=("r_in", "r_out"))
        heatring1 = gf.CrossSection(sections=[secheat1, secheatpad1])
        heatout1 = gf.CrossSection(sections=[secheatout1])
        secheat2 = gf.Section(width=WidthHeat, offset=DeltaHeat, layer=heatlayer, port_names=("in", "out"))
        secheatout2 = gf.Section(width=RadiusRing, offset=(DeltaHeat + WidthHeat / 2 + RadiusRing / 2), layer=heatlayer,
                                 port_names=("in", "out"))
        secheatpad2 = gf.Section(width=RadiusRing - WidthHeat / 2 + DeltaHeat - GapRoute,
                                 offset=-RadiusRing + (RadiusRing - WidthHeat / 2 + DeltaHeat - GapRoute) / 2,
                                 layer=heatlayer, port_names=("r_in", "r_out"))
        heatring2 = gf.CrossSection(sections=[secheat2, secheatpad2])
        heatout2 = gf.CrossSection(sections=[secheatout2])
        S_mout1 = gf.Section(width = WidthHeat ,offset = -DeltaHeat-WidthHeat,layer=heatlayer, port_names=("in", "out"))
        heatmout1 = gf.CrossSection(sections=[S_mout1])
        S_mout2 = gf.Section(width = WidthHeat ,offset = DeltaHeat+WidthHeat,layer=heatlayer, port_names=("in", "out"))
        heatmout2 = gf.CrossSection(sections=[S_mout2])
        # Heat Path
        HP1 = h_plus << gf.path.extrude(RingPath1, cross_section=heatring2)
        HP2 = h_plus << gf.path.extrude(RingPath2, cross_section=heatring1)
        HP3 = h_plus << gf.path.extrude(RingPath1, cross_section=heatring2)
        HP4 = h_plus << gf.path.extrude(RingPath2, cross_section=heatring1)
        # HP1.connect("in",other=RP1.ports["in"]).mirror_y("in")
        HP2.connect("in", other=HP1.ports["in"])
        HP3.connect("out", other=HP2.ports["out"])
        HP4.connect("in", other=HP3.ports["in"])
        # Heat
        HO1 = h_minus << gf.path.extrude(RingPath1, cross_section=heatout2)
        HO2 = h_minus << gf.path.extrude(RingPath2, cross_section=heatout1)
        HO3 = h_minus << gf.path.extrude(RingPath1, cross_section=heatout2)
        HO4 = h_minus << gf.path.extrude(RingPath2, cross_section=heatout1)
        HO2.connect("in", other=HO1.ports["in"])
        HO3.connect("out", other=HO2.ports["out"])
        HO4.connect("in", other=HO3.ports["in"])
        delta = RP3.ports["in"].center[1] - RP1.ports["in"].center[1]
        HR1 = h_plus << GfCStraight(width=WidthRoute * 2 + 2 * GapRoute,
                                    length=(RadiusRing - WidthRing / 2 - WidthHeat + DeltaHeat - GapRoute),
                                    layer=heatlayer)
        HR2 = h_minus << GfCStraight(width=2 * GapRoute, length=delta-GapRoute+WidthHeat,
                                     layer=heatlayer)
        # HR3 = h_minus << GfCStraight(width=2 * GapRoute,)
        HR1.connect("o1", other=HP1.ports["in"],allow_width_mismatch=True,allow_layer_mismatch=True)
        HR1.rotate(-90, HR1.ports["o1"].center)
        HR2.connect("o1", other=HP1.ports["in"],allow_width_mismatch=True,allow_layer_mismatch=True)
        HR2.rotate(-90, HR2.ports["o1"].center)
        HR2.movey( - WidthHeat/2 )

        Htotal = c << gf.boolean(A=h_plus, B=h_minus, operation="not", layer=heatlayer)
        c.add_port(name="HeatIn", port=HP1.ports["in"], orientation=0)
        c.add_port(name="HeatOut", port=HP2.ports["out"])
    remove_layer(c,layer=(512,8))
    add_labels_to_ports(c)
    return c

# %% TaperRaceTrackPulley:ringcouple +taper straight
@gf.cell
def TaperRaceTrackPulley(
        WidthRing: float = 4,
        WidthNear: float = 3,
        WidthRun: float = 8,
        LengthRun: float = 300,
        LengthTaper: float = 200,
        RadiusRing: float = 150,
        GapRing: float = 1,
        AngleCouple: float = 20,
        IsAD: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        Name: str = "TaperRaceTrack_Pulley"
) -> Component:
    """
    创建一个带有锥形耦合的环形跑道波导组件，支持输入、输出、添加和丢弃端口。

    参数：
        WidthRing: 环形波导的宽度（单位：um）。
        WidthNear: 耦合波导的宽度（单位：um）。
        WidthRun: 直线部分的宽度（单位：um）。
        LengthRun: 直线部分的长度（单位：um）。
        LengthTaper: 锥形部分的长度（单位：um）。
        RadiusRing: 环形波导的半径（单位：um）。
        GapRing: 环形波导与耦合波导之间的间距（单位：um）。
        AngleCouple: 耦合角度（单位：度）。
        IsAD: 是否添加添加和丢弃端口。
        oplayer: 波导层的定义。
        Name: 组件名称。

    返回：
        Component: 生成的环形跑道波导组件。

    端口：
        Input: 输入端口。
        Through: 直通端口。
        Add: Add端口（如果 IsAD 为 True）。
        Drop: Drop端口（如果 IsAD 为 True）。
        Rcen1, Rcen2: 环形波导的中心端口。
    """
    c = gf.Component()
    layer = oplayer
    secring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("in", "out"))
    secnring = gf.Section(width=WidthNear, offset=0, layer=layer, port_names=("in", "out"))
    wgring = gf.CrossSection(sections=[secring])
    wgnear = gf.CrossSection(sections=[secnring])
    LengthRun = (LengthRun - LengthTaper >= 0) * (LengthRun - LengthTaper) + LengthTaper
    # run ring path
    rring1 = gf.path.arc(radius=RadiusRing, angle=60)
    rring2 = gf.path.arc(radius=RadiusRing, angle=-60)
    rb1 = euler_Bend_Half(radius=RadiusRing, angle=30, p=0.5)
    rb2 = euler_Bend_Half(radius=RadiusRing, angle=-30, p=0.5)
    RingPath = list(range(2))
    RingPath[0] = rring1 + rb1
    RingPath[1] = rring2 + rb2
    # print("length="+str(RingPath[0].length()*4))
    race = gf.Component()
    racetaper = race << gf.c.taper(width1=WidthRing, width2=WidthRun, length=LengthTaper)
    racestraight = race << GfCStraight(length=(LengthRun - LengthTaper) / 2, width=WidthRun)
    racestraight.connect("o1", other=racetaper.ports["o2"])
    race.add_port("out", port=racestraight.ports["o2"])
    race.add_port("in", port=racetaper.ports["o1"])
    RP = list(range(4))
    RPr = list(range(4))
    RPc = list(range(4))
    for i in range(4):
        RP0 = gf.Component()
        RPr[i] = RP0 << gf.path.extrude(RingPath[i % 2], cross_section=wgring)
        RPc[i] = RP0 << race
        RPc[i].connect("in", other=RPr[i].ports["out"])
        RP0.add_port("in", port=RPr[i].ports["in"])
        RP0.add_port("out", port=RPc[i].ports["out"])
        RP[i] = c << RP0
    RP[0].connect("out", other=RP[3].ports["out"])
    RP[1].connect("in", other=RP[0].ports["in"])
    RP[2].connect("out", other=RP[1].ports["out"])
    RP[3].connect("in", other=RP[2].ports["in"])
    # out port
    r_delta = WidthRing / 2 + GapRing + WidthNear / 2
    rcoup1 = gf.path.arc(radius=RadiusRing + r_delta, angle=-AngleCouple / 2)
    rcoup2 = gf.path.arc(radius=RadiusRing + r_delta, angle=AngleCouple / 2)
    rcb1 = euler_Bend_Half(radius=RadiusRing + r_delta, angle=-AngleCouple / 2, p=0.5)
    rcb2 = euler_Bend_Half(radius=RadiusRing + r_delta, angle=AngleCouple / 2, p=0.5)
    RingCoup1 = rcoup1 + rcb2
    RingCoup2 = rcoup2 + rcb1
    # input through
    RC1 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
    RC2 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
    RC1.connect("in", other=RP[2].ports["in"], allow_width_mismatch=True)
    RC1.movey(r_delta)
    RC2.connect("in", other=RC1.ports["in"])
    # ports:
    c.add_port(name="Input", port=RC1.ports["out"], orientation=0)
    c.add_port(name="Through", port=RC2.ports["out"])
    # add dropd
    if IsAD:
        RC3 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
        RC4 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
        RC3.connect("in", other=RP[0].ports["in"], allow_width_mismatch=True)
        RC3.movey(-r_delta)
        RC4.connect("in", other=RC3.ports["in"])
        c.add_port(name="Add", port=RC3.ports["out"], orientation=180)
        c.add_port(name="Drop", port=RC4.ports["out"])
    c.add_port(name="Rcen1", port=RP[0].ports["out"])
    c.add_port(name="Rcen2", port=RP[2].ports["out"])
    return c


__all__ = ['RaceTrackStr', 'RaceTrackPulley', 'RaceTrackStrH2', 'TaperRaceTrackPulley']
