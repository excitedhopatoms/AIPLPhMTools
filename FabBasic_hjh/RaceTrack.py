from .BasicDefine import *
from .ELE import *
from .Heater import DifferentHeater
from .SnapMerge import *
# %% RaceTrackPulley: 滑轮耦合跑道环谐振器
@gf.cell
def RaceTrackP(
        WidthRing: float = 8,
        WidthNear: float = 5,
        LengthRun: float = 200,
        RadiusRing: float = 100,
        GapCouple: float = 1,
        AngleCouple: float = 20,
        IsAD: bool = True,
        DirectionHeater: str = "down",
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
) -> Component:
    """
    滑轮耦合（Pulley Coupler）跑道环谐振器。
    环由两段圆弧 + 欧拉弯曲 + 直波导组成跑道形状，输入/输出总线通过滑轮耦合段与环耦合。
    支持 Add/Drop 端口和可配置的加热器。

    参数:
        WidthRing: 跑道环波导的宽度 (µm)。
        WidthNear: 耦合总线波导的宽度 (µm)。
        LengthRun: 跑道环直线部分的长度 (µm)。
        RadiusRing: 跑道环弯曲部分的半径 (µm)。
        GapCouple: 环与耦合总线之间的最小间隙 (µm)。
        AngleCouple: 滑轮耦合器弯曲耦合段的角度 (度)。
        IsAD: 是否包含 Add/Drop 端口（四端口器件）。False 则为双端口（Input/Through）。
        DirectionHeater: 加热器相对于环的放置方向，"up" 或 "down"。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。
                      其 Coverage 字段控制加热器覆盖范围 ("half" 或 "full")。

    返回:
        Component: 生成的滑轮耦合跑道环谐振器组件。

    端口:
        Input: 输入端口。
        Through: 直通端口。
        Add: (IsAD=True 时) 增加端口。
        Drop: (IsAD=True 时) 下载端口。
        RingSmid1, RingSmid2: 跑道环直线段中点上方参考端口。
        RingBmid1, RingBmid2: 跑道环直线段中点下方参考端口。
        Rcen1, Rcen2: 跑道环两个弯曲部分的中心参考端口。
        Rcenter, RingC: 跑道环几何中心参考端口。
        (HeaterConfig 不为 None 时) 相应的加热器电学端口。
    """
    c = gf.Component()
    layer = oplayer
    secring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("o1", "o2"))
    secnring = gf.Section(width=WidthNear, offset=0, layer=layer, port_names=("o1", "o2"))
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
    RP1.connect("o2", other=RP4.ports["o2"])
    RP2.connect("o1", other=RP1.ports["o1"])
    RP3.connect("o2", other=RP2.ports["o2"])
    RP4.connect("o1", other=RP3.ports["o1"])
    c.add_port("RingSmid1", port=RP4.ports["o1"])
    c.add_port("RingSmid2", port=RP2.ports["o1"])
    c.add_port("RingBmid1", port=RP1.ports["o1"])
    c.add_port("RingBmid2", port=RP3.ports["o1"])
    # out port
    r_delta = WidthRing / 2 + GapCouple + WidthNear / 2
    rcoup1 = gf.path.arc(radius=RadiusRing + r_delta, angle=-AngleCouple / 2)
    rcoup2 = gf.path.arc(radius=RadiusRing + r_delta, angle=AngleCouple / 2)
    rcb1 = euler_Bend_Half(radius=RadiusRing + r_delta, angle=-AngleCouple / 2, p=0.5)
    rcb2 = euler_Bend_Half(radius=RadiusRing + r_delta, angle=AngleCouple / 2, p=0.5)
    RingCoup1 = rcoup1 + rcb2
    RingCoup2 = rcoup2 + rcb1
    # input through
    RC1 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
    RC2 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
    RC1.connect("o1", other=RP3.ports["o1"], allow_width_mismatch=True)
    RC1.movey(r_delta)
    RC2.connect("o1", other=RC1.ports["o1"])
    # ports:
    c.add_port(name="Input", port=RC1.ports["o2"], orientation=0)
    c.add_port(name="Through", port=RC2.ports["o2"])
    # add drop
    if IsAD:
        RC3 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
        RC4 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
        RC3.connect("o1", other=RP1.ports["o1"], allow_width_mismatch=True)
        RC3.movey(-r_delta)
        RC4.connect("o1", other=RC3.ports["o1"])
        c.add_port(name="Add", port=RC3.ports["o2"], orientation=180)
        c.add_port(name="Drop", port=RC4.ports["o2"])
    c.add_port(name="Rcen1", port=RP1.ports["o2"])
    c.add_port(name="Rcen2", port=RP3.ports["o2"])
    c.add_port(name="Rcenter", center=np.array(RP1.ports["o2"].center)/2+np.array(RP3.ports["o2"].center)/2,
               width=WidthRing, orientation=180,layer=oplayer)
    c.add_port(name="RingC", center=np.array(RP1.ports["o2"].center)/2+np.array(RP3.ports["o2"].center)/2,
               width=WidthRing, orientation=180,layer=oplayer)
    print("length="+str(RingPath1.length()*4))
    if HeaterConfig:
        localheater(c, WidthRing=WidthRing, LengthRun=LengthRun, RadiusRing=RadiusRing,
                    HeaterConfig=HeaterConfig, coverage=HeaterConfig.Coverage, DirectionHeater=DirectionHeater)
    return c


# %% RaceTrackPulley2: 直线耦合跑道环谐振器
@gf.cell
def RaceTrackS(
        WidthRing: float = 2,
        LengthRun: float = 200,
        RadiusRing: float = 100,
        GapCouple: float = 1,
        LengthCouple: float = 200,
        IsAD: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        DirectionHeater: str = "down",
        HeaterConfig: HeaterConfigClass = heaterconfig0,
) -> Component:
    """
    直线耦合跑道环谐振器。
    耦合通过环的直线段与平行总线波导之间的近场相互作用实现。
    支持 Add/Drop 端口和多种加热器类型。

    参数:
        WidthRing: 跑道环波导宽度 (µm)。
        LengthRun: 跑道环直线段长度 (µm)。
        RadiusRing: 跑道环弯曲半径 (µm)。
        GapCouple: 环的直线段与耦合总线之间的间隙 (µm)。
        LengthCouple: 直线耦合段的长度 (µm)。
        IsAD: 是否包含 Add/Drop 端口（四端口器件）。False 则为双端口（Input/Through）。
        oplayer: 光学波导层。
        DirectionHeater: 加热器相对于环的放置方向，"up" 或 "down"。
        HeaterConfig: 加热器配置对象。其 Coverage 字段控制加热器覆盖范围 ("half" 或 "full")。
                      TypeHeater="center" 时委托给 RaceTrackStrHC。
                      TypeHeater="ELE" 时使用 GSG 电极。

    返回:
        Component: 生成的直线耦合跑道环谐振器组件。

    端口:
        Input: 输入端口。
        Through: 直通端口。
        Add: (IsAD=True 时) 增加端口。
        Drop: (IsAD=True 时) 下载端口。
        RingSmid1, RingSmid2: 环上方直线段中点参考端口。
        RingBmid1, RingBmid2: 环下方直线段中点参考端口。
        Rcen1, Rcen2: 弯曲中心参考端口。
        (HeaterConfig 不为 None 时) 相应的加热器电学端口。
    """
    if HeaterConfig:
        if HeaterConfig.TypeHeater == "center":
            return RaceTrackStrHC(
                WidthRing=WidthRing,
                LengthRun=LengthRun,
                RadiusRing=RadiusRing,
                GapCouple=GapCouple,
                LengthCouple=LengthCouple,
                IsAD=IsAD,
                oplayer=oplayer,
            )
    c = gf.Component()
    layer = oplayer
    secring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("o1", "o2"))
    secnring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("o1", "o2"))
    wgring = gf.CrossSection(sections=[secring])
    wgnear = gf.CrossSection(sections=[secnring])
    # run ring path
    CRaceTrack = gf.Component()
    rrun1 = gf.path.straight(length=LengthRun / 2)
    rring1 = gf.path.arc(radius=RadiusRing, angle=70)
    rring2 = gf.path.arc(radius=RadiusRing, angle=-70)
    rring3 = gf.path.arc(radius=RadiusRing, angle=-20)
    rb1 = euler_Bend_Half(radius=RadiusRing, angle=20, p=0.5)
    rb2 = euler_Bend_Half(radius=RadiusRing, angle=-20, p=0.5)
    RingPath1 = rring1 + rb1 + rrun1
    RingPath2 = rring2 + rb2 + rrun1
    RP1 = CRaceTrack << gf.path.extrude(RingPath1, cross_section=wgring)
    RP2 = CRaceTrack << gf.path.extrude(RingPath2, cross_section=wgring)
    RP3 = CRaceTrack << gf.path.extrude(RingPath1, cross_section=wgring)
    RP4 = CRaceTrack << gf.path.extrude(RingPath2, cross_section=wgring)
    RP1.connect("o2", other=RP4.ports["o2"])
    RP2.connect("o1", other=RP1.ports["o1"])
    RP3.connect("o2", other=RP2.ports["o2"])
    RP4.connect("o1", other=RP3.ports["o1"])
    c << CRaceTrack
    c.add_port("RingSmid1", port=RP1.ports["o2"])
    c.add_port("RingSmid2", port=RP3.ports["o2"])
    c.add_port("RingBmid1", port=RP1.ports["o1"])
    c.add_port("RingBmid2", port=RP3.ports["o1"])
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
    RC1.connect("o2", other=RP3.ports["o2"], allow_width_mismatch=True)
    RC1.movex(-GapCouple - WidthRing)
    RC2.connect("o1", other=RC1.ports["o2"])
    # ports:
    c.add_port(name="Input", port=RC1.ports["o1"])
    c.add_port(name="Through", port=RC2.ports["o2"])
    # add drop
    if IsAD:
        RC3 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
        RC4 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
        RC3.connect("o2", other=RP1.ports["o2"], allow_width_mismatch=True)
        RC3.movex(GapCouple + WidthRing)
        RC4.connect("o1", other=RC3.ports["o2"])
        c.add_port(name="Add", port=RC3.ports["o1"])
        c.add_port(name="Drop", port=RC4.ports["o2"])
    c.add_port(name="Rcen1", port=RP1.ports["o2"])
    c.add_port(name="Rcen2", port=RP3.ports["o2"])
    # heat part
    if HeaterConfig:
        localheater(c, WidthRing=WidthRing, LengthRun=LengthRun, RadiusRing=RadiusRing,
                    HeaterConfig=HeaterConfig, coverage=HeaterConfig.Coverage,DirectionHeater=DirectionHeater)
    print("length="+str(RingPath1.length()*4))
    # if IsLabels:
    # add_labels_to_ports(c)
    return c

# %% RaceTrackStrHC: 中心加热直线耦合跑道环
def RaceTrackStrHC(
        WidthRing: float = 8,
        LengthRun: float = 200,
        RadiusRing: float = 500,
        GapCouple: float = 1,
        LengthCouple: float = 200,
        IsAD: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None
) -> Component:
    """
    直线耦合跑道环谐振器，加热器放置在跑道环的几何中心区域（两个直线段之间）。
    加热器通过多层 cross_section 拉伸实现，包含正负两层并做布尔差运算。
    通常由 RaceTrackS 在 HeaterConfig.TypeHeater="center" 时委托调用。

    参数:
        WidthRing: 跑道环波导宽度 (µm)。
        LengthRun: 跑道环直线段长度 (µm)。
        RadiusRing: 跑道环弯曲半径 (µm)。
        GapCouple: 环与耦合总线之间的间隙 (µm)。
        LengthCouple: 直线耦合段的长度 (µm)。
        IsAD: 是否包含 Add/Drop 端口（四端口器件）。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。
                      从配置中提取 WidthHeat, DeltaHeat, GapHeat, LayerHeat 等参数。

    返回:
        Component: 带中心加热的直线耦合跑道环谐振器。

    端口:
        Input: 输入端口。
        Through: 直通端口。
        Add: (IsAD=True 时) 增加端口。
        Drop: (IsAD=True 时) 下载端口。
        RingSmid1, RingSmid2: 环上方直线段中点参考端口。
        RingBmid1, RingBmid2: 环下方直线段中点参考端口。
        Rcen1, Rcen2: 弯曲中心参考端口。
        HeatIn, HeatOut: (HeaterConfig 不为 None 时) 加热器电学端口。
    """
    c = gf.Component()
    # h = gf.Component(Name + "heat")
    layer = oplayer
    secring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("o1", "o2"))
    secnring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("o1", "o2"))
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
    RP2.connect("o1", other=RP1.ports["o1"])
    RP3.connect("o2", other=RP2.ports["o2"])
    RP4.connect("o1", other=RP3.ports["o1"])
    CRaceTrack.add_port("RingSmid1", port=RP1.ports["o2"])
    CRaceTrack.add_port("RingSmid2", port=RP3.ports["o2"])
    CRaceTrack.add_port("RingBmid1", port=RP2.ports["o1"])
    CRaceTrack.add_port("RingBmid2", port=RP4.ports["o1"])
    c << CRaceTrack
    c.add_port("RingSmid1", port=CRaceTrack.ports["RingSmid1"])
    c.add_port("RingSmid2", port=CRaceTrack.ports["RingSmid2"])
    c.add_port("RingBmid1", port=CRaceTrack.ports["RingBmid1"])
    c.add_port("RingBmid2", port=CRaceTrack.ports["RingBmid2"])
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
    RC1.connect("o2", other=RP3.ports["o2"])
    RC1.movex(-GapCouple - WidthRing)
    RC2.connect("o1", other=RC1.ports["o2"])
    # ports:
    c.add_port(name="Input", port=RC1.ports["o1"])
    c.add_port(name="Through", port=RC2.ports["o2"])
    # add drop
    if IsAD:
        RC3 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
        RC4 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
        RC3.connect("o2", other=RP1.ports["o2"])
        RC3.movex(GapCouple + WidthRing)
        RC4.connect("o1", other=RC3.ports["o2"])
        c.add_port(name="Add", port=RC3.ports["o1"])
        c.add_port(name="Drop", port=RC4.ports["o2"])
    c.add_port(name="Rcen1", port=RP1.ports["o2"])
    c.add_port(name="Rcen2", port=RP3.ports["o2"])

    # heat part
    if HeaterConfig:
        # 从配置对象中提取参数
        TypeHeater = HeaterConfig.TypeHeater
        WidthHeat = HeaterConfig.WidthHeat
        WidthRoute = HeaterConfig.WidthRoute
        WidthVia = HeaterConfig.WidthVia
        Spacing = HeaterConfig.Spacing
        DeltaHeat = HeaterConfig.DeltaHeat
        GapRoute = HeaterConfig.GapHeat
        heatlayer = HeaterConfig.LayerHeat
        routelayer = HeaterConfig.LayerRoute
        vialayer = HeaterConfig.LayerVia
        h_plus = gf.Component()
        h_minus = gf.Component()
        secheat1 = gf.Section(width=WidthHeat, offset=-DeltaHeat, layer=heatlayer, port_names=("o1", "o2"))
        secheatout1 = gf.Section(width=RadiusRing, offset=-(DeltaHeat + WidthHeat / 2 + RadiusRing / 2), layer=heatlayer,
                                 port_names=("o1", "o2"))
        secheatpad1 = gf.Section(width=RadiusRing - (WidthHeat / 2 - DeltaHeat + GapRoute),
                                 offset=RadiusRing - (RadiusRing - WidthHeat / 2 + DeltaHeat - GapRoute) / 2,
                                 layer=heatlayer, port_names=("r_in", "r_out"))
        heatring1 = gf.CrossSection(sections=[secheat1, secheatpad1])
        heatout1 = gf.CrossSection(sections=[secheatout1])
        secheat2 = gf.Section(width=WidthHeat, offset=DeltaHeat, layer=heatlayer, port_names=("o1", "o2"))
        secheatout2 = gf.Section(width=RadiusRing, offset=(DeltaHeat + WidthHeat / 2 + RadiusRing / 2), layer=heatlayer,
                                 port_names=("o1", "o2"))
        secheatpad2 = gf.Section(width=RadiusRing - WidthHeat / 2 + DeltaHeat - GapRoute,
                                 offset=-RadiusRing + (RadiusRing - WidthHeat / 2 + DeltaHeat - GapRoute) / 2,
                                 layer=heatlayer, port_names=("r_in", "r_out"))
        heatring2 = gf.CrossSection(sections=[secheat2, secheatpad2])
        heatout2 = gf.CrossSection(sections=[secheatout2])
        S_mout1 = gf.Section(width = WidthHeat ,offset = -DeltaHeat-WidthHeat,layer=heatlayer, port_names=("o1", "o2"))
        heatmout1 = gf.CrossSection(sections=[S_mout1])
        S_mout2 = gf.Section(width = WidthHeat ,offset = DeltaHeat+WidthHeat,layer=heatlayer, port_names=("o1", "o2"))
        heatmout2 = gf.CrossSection(sections=[S_mout2])
        # Heat Path
        HP1 = h_plus << gf.path.extrude(RingPath1, cross_section=heatring2)
        HP2 = h_plus << gf.path.extrude(RingPath2, cross_section=heatring1)
        HP3 = h_plus << gf.path.extrude(RingPath1, cross_section=heatring2)
        HP4 = h_plus << gf.path.extrude(RingPath2, cross_section=heatring1)
        # HP1.connect("o1",other=RP1.ports["o1"]).mirror_y("o1")
        HP2.connect("o1", other=HP1.ports["o1"])
        HP3.connect("o2", other=HP2.ports["o2"])
        HP4.connect("o1", other=HP3.ports["o1"])
        # Heat
        HO1 = h_minus << gf.path.extrude(RingPath1, cross_section=heatout2)
        HO2 = h_minus << gf.path.extrude(RingPath2, cross_section=heatout1)
        HO3 = h_minus << gf.path.extrude(RingPath1, cross_section=heatout2)
        HO4 = h_minus << gf.path.extrude(RingPath2, cross_section=heatout1)
        HO2.connect("o1", other=HO1.ports["o1"])
        HO3.connect("o2", other=HO2.ports["o2"])
        HO4.connect("o1", other=HO3.ports["o1"])
        delta = RP3.ports["o1"].center[1] - RP1.ports["o1"].center[1]
        HR1 = h_plus << GfCStraight(width=WidthRoute * 2 + 2 * GapRoute,
                                    length=(RadiusRing - WidthRing / 2 - WidthHeat + DeltaHeat - GapRoute),
                                    layer=heatlayer)
        HR2 = h_minus << GfCStraight(width=2 * GapRoute, length=delta-GapRoute+WidthHeat,
                                     layer=heatlayer)
        # HR3 = h_minus << GfCStraight(width=2 * GapRoute,)
        HR1.connect("o1", other=HP1.ports["o1"],allow_width_mismatch=True,allow_layer_mismatch=True)
        HR1.rotate(-90, HR1.ports["o1"].center)
        HR2.connect("o1", other=HP1.ports["o1"],allow_width_mismatch=True,allow_layer_mismatch=True)
        HR2.rotate(-90, HR2.ports["o1"].center)
        HR2.movey( - WidthHeat/2 )

        Htotal = c << gf.boolean(A=h_plus, B=h_minus, operation="not", layer=heatlayer)
        c.add_port(name="HeatIn", port=HP1.ports["o1"], orientation=0)
        c.add_port(name="HeatOut", port=HP2.ports["o2"])
    # remove_layer(c,layer=(512,8))
    add_labels_to_ports(c)
    print("length="+str(RingPath1.length()*4))
    return c

# %% TaperRaceTrackPulley: 锥形波导滑轮耦合跑道环
@gf.cell
def TaperRaceTrackPulley(
        WidthRing: float = 4,
        WidthNear: float = 3,
        WidthRun: float = 8,
        LengthRun: float = 300,
        LengthTaper: float = 200,
        RadiusRing: float = 150,
        GapCouple: float = 1,
        AngleCouple: float = 20,
        IsAD: bool = True,
        DirectionHeater: str = "down",
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
) -> Component:
    """
    滑轮耦合跑道环谐振器，直线段采用锥形波导（taper）以增加局部波导宽度。
    环由圆弧段 + 欧拉弯曲 + 锥形波导直线段组成，耦合为滑轮型角度耦合。
    支持 Add/Drop 端口和可配置的加热器。

    参数:
        WidthRing: 跑道环圆弧段波导宽度 (µm)。
        WidthNear: 耦合总线波导的宽度 (µm)。
        WidthRun: 直线段展宽后波导的宽度 (µm)。
        LengthRun: 跑道环直线段总长度 (µm)。
        LengthTaper: 锥形过渡段长度 (µm)。
        RadiusRing: 跑道环弯曲半径 (µm)。
        GapCouple: 环与耦合总线之间的间隙 (µm)。
        AngleCouple: 滑轮耦合器的耦合角度 (度)。
        IsAD: 是否包含 Add/Drop 端口（四端口器件）。False 则为双端口（Input/Through）。
        DirectionHeater: 加热器相对于环的放置方向，"up" 或 "down"。
        oplayer: 光学波导层。
        HeaterConfig: 加热器配置对象，None 表示不添加加热器。
                      其 Coverage 字段控制加热器覆盖范围 ("half" 或 "full")。

    返回:
        Component: 锥形波导滑轮耦合跑道环谐振器。

    端口:
        Input: 输入端口。
        Through: 直通端口。
        Add: (IsAD=True 时) 增加端口。
        Drop: (IsAD=True 时) 下载端口。
        Rcen1, Rcen2: 弯曲中心参考端口。
        RingSmid1, RingSmid2: 环上方参考端口。
        RingBmid1, RingBmid2: 环下方参考端口。
        (HeaterConfig 不为 None 时) 相应的加热器电学端口。
    """
    c = gf.Component()
    layer = oplayer
    secring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("o1", "o2"))
    secnring = gf.Section(width=WidthNear, offset=0, layer=layer, port_names=("o1", "o2"))
    wgring = gf.CrossSection(sections=[secring])
    wgnear = gf.CrossSection(sections=[secnring])
    LengthRun = ((LengthRun - 2*LengthTaper) >= 0) * (LengthRun - LengthTaper) + 2*LengthTaper
    # run ring path
    rring1 = gf.path.arc(radius=RadiusRing, angle=70)
    rring2 = gf.path.arc(radius=RadiusRing, angle=-70)
    rb1 = euler_Bend_Half(radius=RadiusRing, angle=20, p=0.5)
    rb2 = euler_Bend_Half(radius=RadiusRing, angle=-20, p=0.5)
    RingPath = list(range(2))
    RingPath[0] = rring1 + rb1
    RingPath[1] = rring2 + rb2
    # print("length="+str(RingPath[0].length()*4))
    race = gf.Component()
    racetaper = race << gf.c.taper(width1=WidthRing, width2=WidthRun, length=LengthTaper)
    racestraight = race << GfCStraight(length=(LengthRun - 2*LengthTaper) / 2, width=WidthRun)
    racestraight.connect("o1", other=racetaper.ports["o2"])
    race.add_port("o2", port=racestraight.ports["o2"])
    race.add_port("o1", port=racetaper.ports["o1"])
    RP = list(range(4))
    RPr = list(range(4))
    RPc = list(range(4))
    for i in range(4):
        RP0 = gf.Component()
        RPr[i] = RP0 << gf.path.extrude(RingPath[i % 2], cross_section=wgring)
        RPc[i] = RP0 << race
        RPc[i].connect("o1", other=RPr[i].ports["o2"])
        RP0.add_port("o1", port=RPr[i].ports["o1"])
        RP0.add_port("o2", port=RPc[i].ports["o2"])
        RP[i] = c << RP0
    RP[0].connect("o2", other=RP[3].ports["o2"])
    RP[1].connect("o1", other=RP[0].ports["o1"])
    RP[2].connect("o2", other=RP[1].ports["o2"])
    RP[3].connect("o1", other=RP[2].ports["o1"])
    # out port
    r_delta = WidthRing / 2 + GapCouple + WidthNear / 2
    rcoup1 = gf.path.arc(radius=RadiusRing + r_delta, angle=-AngleCouple / 2)
    rcoup2 = gf.path.arc(radius=RadiusRing + r_delta, angle=AngleCouple / 2)
    rcb1 = euler_Bend_Half(radius=RadiusRing + r_delta, angle=-AngleCouple / 2, p=0.5)
    rcb2 = euler_Bend_Half(radius=RadiusRing + r_delta, angle=AngleCouple / 2, p=0.5)
    RingCoup1 = rcoup1 + rcb2
    RingCoup2 = rcoup2 + rcb1
    # input through
    RC1 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
    RC2 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
    RC1.connect("o1", other=RP[2].ports["o1"], allow_width_mismatch=True)
    RC1.movey(r_delta)
    RC2.connect("o1", other=RC1.ports["o1"])
    # ports:
    c.add_port(name="Input", port=RC1.ports["o2"], orientation=0)
    c.add_port(name="Through", port=RC2.ports["o2"])
    # add dropd
    if IsAD:
        RC3 = c << gf.path.extrude(RingCoup1, cross_section=wgnear)
        RC4 = c << gf.path.extrude(RingCoup2, cross_section=wgnear)
        RC3.connect("o1", other=RP[0].ports["o1"], allow_width_mismatch=True)
        RC3.movey(-r_delta)
        RC4.connect("o1", other=RC3.ports["o1"])
        c.add_port(name="Add", port=RC3.ports["o2"], orientation=180)
        c.add_port(name="Drop", port=RC4.ports["o2"])
    c.add_port(name="Rcen1", port=RP[0].ports["o2"])
    c.add_port(name="Rcen2", port=RP[2].ports["o2"])
    c.add_port("RingSmid2", port=RP[0].ports["o2"])
    c.add_port("RingBmid1", port=RP[0].ports["o1"])
    c.add_port("RingSmid1", port=RP[2].ports["o2"])
    c.add_port("RingBmid2", port=RP[2].ports["o1"])
    if HeaterConfig:
        localheater(c, WidthRing=WidthRing, LengthRun=LengthRun, RadiusRing=RadiusRing,
                    HeaterConfig=HeaterConfig, coverage=HeaterConfig.Coverage, DirectionHeater=DirectionHeater)
    add_labels_to_ports(c)
    return c


def localheater(
        c: Component,
        WidthRing: float,
        LengthRun: float,
        RadiusRing: float,
        HeaterConfig: HeaterConfigClass,
        coverage: str = "half",
        DirectionHeater: str = "up",
) -> None:
    """
    统一的跑道环加热器放置函数，将加热器直接添加到目标组件 c 上。
    支持半环覆盖（half）和全环覆盖（full）两种模式。

    参数:
        c: 待添加加热器的目标组件，需包含 RingBmid1 和 Rcen1 端口用于对齐。
        WidthRing: 跑道环波导宽度 (µm)。
        LengthRun: 跑道环直线段长度 (µm)。
        RadiusRing: 跑道环弯曲半径 (µm)。
        HeaterConfig: 加热器配置对象，控制加热器类型、尺寸、层等参数。
        coverage: 加热器覆盖范围。"half" 为半环覆盖，"full" 为全环覆盖。
        DirectionHeater: 仅 coverage="half" 时生效，加热器放置方向，"up" 或 "down"。

    coverage="half":
        加热器覆盖环的下半部分（约 180°），由 3 段路径拼接而成。
        通过 HeatBmid1 端口与目标组件 c 的 RingBmid1 端口对齐。

    coverage="full":
        加热器覆盖整个环（约 360°），由 5 段路径拼接而成。
        支持 HeaterConfig.TypeHeater="ELE" 时使用 GSG 电极替代普通加热器。
    """
    if coverage == "half":
        rrun1 = gf.path.straight(length=LengthRun / 2)
        rring1 = gf.path.arc(radius=RadiusRing, angle=45)
        rring2 = gf.path.arc(radius=RadiusRing, angle=70)
        rb1 = euler_Bend_Half(radius=RadiusRing / 2, angle=45, p=0.5, direction='Forward')
        rb2 = euler_Bend_Half(radius=RadiusRing, angle=20, p=0.5)
        HeatPath1 = rb1 + rring1
        HeatPath2 = rring2 + rb2 + rrun1
        HeatPath3 = rrun1
        HeatPathAll = HeatPath1 + HeatPath2 + HeatPath3
        heater = gf.Component()
        heater_assit = gf.Component()
        RHP1 = heater_assit << DifferentHeater(PathHeat=HeatPath1, WidthWG=WidthRing, HeaterConfig=HeaterConfig)
        RHP2 = heater_assit << DifferentHeater(PathHeat=HeatPath2, WidthWG=WidthRing, HeaterConfig=HeaterConfig)
        RHP3 = heater_assit << DifferentHeater(PathHeat=HeatPath3, WidthWG=WidthRing, HeaterConfig=HeaterConfig)
        RHP2.connect("HeatIn", other=RHP1.ports["HeatOut"])
        RHP3.connect("HeatIn", other=RHP2.ports["HeatOut"])
        RHPA = heater << DifferentHeater(PathHeat=HeatPathAll, WidthWG=WidthRing, HeaterConfig=HeaterConfig)
        for port in RHPA.ports:
            if "Heat" in port.name:
                heater.add_port(port.name, port=port)
        heater.add_port("HeatBmid1", port=RHP1.ports["HeatOut"])
        heater.add_port("HeatBmid2", port=RHP2.ports["HeatIn"])
        h = c << heater
        h.connect("HeatBmid1", c.ports["RingBmid1"], allow_width_mismatch=True, allow_layer_mismatch=True)
        if DirectionHeater == 'up':
            h.mirror_y(c.ports["Rcen1"].center[1])
        for port in h.ports:
            if port.name not in c.ports:
                c.add_port(port.name, port=port)
    elif coverage == "full":
        rrun1 = gf.path.straight(length=LengthRun / 2)
        rring1 = gf.path.arc(radius=RadiusRing, angle=70)
        rring2 = gf.path.arc(radius=RadiusRing, angle=-70)
        rb1 = euler_Bend_Half(radius=RadiusRing, angle=20, p=0.5)
        rb1_1 = euler_Bend_Half(radius=RadiusRing, angle=20, p=0.5, direction='Forward')
        rb2 = euler_Bend_Half(radius=RadiusRing / 2, angle=-20, p=0.5)
        rb2_1 = euler_Bend_Half(radius=RadiusRing / 2, angle=20, p=0.5, direction='Forward')
        rb2_2 = euler_Bend_Half(radius=RadiusRing / 2, angle=20, p=0.5)
        HeatPath1 = rring1 + rb1 + rrun1
        HeatPath2 = rring2 + rb2
        HeatPath3 = rrun1 + rb1_1 + rring1
        HeatPath4 = rb2_1 + rring1
        HeatPath5 = rring1 + rb2_2
        HeatPathAll = HeatPath4 + HeatPath1 + HeatPath3 + HeatPath5
        if HeaterConfig.TypeHeater == "ELE":
            ele = c << GSGELE(
                WidthS=20, WidthG=80, GapGS=5, LengthEle=LengthRun + 60, IsPad=True, LengthToPad=90,
                elelayer=HeaterConfig.LayerELE,
            )
            ele.connect("Oin1", other=c.ports["Rcen1"], allow_width_mismatch=True, allow_layer_mismatch=True)
            ele.movey(-LengthRun / 2)
        else:
            heater = gf.Component()
            heater_assit = gf.Component()
            RHP1 = heater_assit << DifferentHeater(PathHeat=HeatPath1, WidthWG=WidthRing, HeaterConfig=HeaterConfig)
            RHP2 = heater_assit << DifferentHeater(PathHeat=HeatPath1, WidthWG=WidthRing, HeaterConfig=HeaterConfig)
            RHP3 = heater_assit << DifferentHeater(PathHeat=HeatPath4, WidthWG=WidthRing, HeaterConfig=HeaterConfig)
            RHP4 = heater_assit << DifferentHeater(PathHeat=HeatPath2, WidthWG=WidthRing, HeaterConfig=HeaterConfig)
            RHPA = heater << DifferentHeater(PathHeat=HeatPathAll, WidthWG=WidthRing, HeaterConfig=HeaterConfig)
            RHP1.connect("HeatIn", other=RHP3.ports["HeatOut"])
            RHP2.connect("HeatOut", other=RHP1.ports["HeatOut"], mirror=True)
            RHP4.connect("HeatIn", other=RHP2.ports["HeatIn"], mirror=True)
            heater.add_port("HeatBmid1", port=RHP3.ports["HeatOut"])
            heater.add_port("HeatBmin2", port=RHP2.ports["HeatIn"])
            for port in RHPA.ports:
                if "Heat" in port.name:
                    heater.add_port(port.name, port=port)
            h = c << heater
            h.connect("HeatBmid1", c.ports["RingBmid1"], allow_width_mismatch=True, allow_layer_mismatch=True)
            # h.mirror_x(h.ports["HeatBmid1"].center[0])
            # if HeaterConfig.TypeHeater == "side":
                # h.movey(-HeaterConfig.DeltaHeat)


__all__ = ['RaceTrackS', 'RaceTrackP', 'RaceTrackStrHC', 'TaperRaceTrackPulley']
