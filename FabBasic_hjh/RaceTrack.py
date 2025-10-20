from .BasicDefine import *
from .ELE import *
from .Heater import DifferentHeater
from .SnapMerge import *
# %% RaceTrackPulley
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
        HeaterConfig:HeaterConfigClass = None,
) -> Component:
    """
    创建一个基于滑轮型（角度）耦合的跑道环谐振器 (RaceTrack Pulley Coupler)。
    该组件包含一个跑道形环和通过弯曲耦合段耦合到该环的输入/输出总线。
    可以选择添加Add/Drop端口和加热器。

    参数:
        WidthRing (float): 跑道环波导的宽度 (µm)。
        WidthNear (float): 耦合总线波导的宽度 (µm)。
        WidthHeat (float): 加热器的宽度 (µm)。
        DeltaHeat (float): 加热器的几何调整参数 (例如，偏移量) (µm)。
        GapHeat (float): 波导与加热器之间的间隙 (µm)。
        WidthRoute (float): 加热器引出线的宽度 (µm)。
        LengthRun (float): 跑道环直线部分的长度 (µm)。
        RadiusRing (float): 跑道环弯曲部分的半径 (µm)。
        GapCouple (float): 环与耦合总线之间的最小间隙 (µm)。
        AngleCouple (float): 定义滑轮耦合器弯曲耦合段的角度 (度)。
        IsAD (bool): 如果为True，则添加Add和Drop端口；否则为双端口直通器件。
        IsHeat (bool): 如果为True，则为跑道环添加加热器。
        TypeHeater (str): 加热器的类型 (例如 "default", "snake", "side")。
        DirectionHeater (str): 加热器的位置/方向，相对于环。
        oplayer (LayerSpec): 光学波导层。
        heatlayer (LayerSpec): 加热器层。
        routelayer (LayerSpec): 加热器布线层 (主要用于某些复杂加热器类型)。
        vialayer (LayerSpec): 过孔层 (主要用于某些复杂加热器类型)。

    返回:
        Component: 生成的滑轮耦合跑道环谐振器组件。

    端口:
        Input: 输入端口。
        Through: 直通端口。
        Add: (如果 IsAD=True) 增加端口。
        Drop: (如果 IsAD=True) 下载端口。
        RingSmid1, RingSmid2: 跑道环直线段中点上方的参考端口。
        RingBmid1, RingBmid2: 跑道环直线段中点下方的参考端口。
        Rcen1, Rcen2: 跑道环两个弯曲部分的中心点参考端口。
        (如果 IsHeat=True，还会根据 TypeHeater 和 DirectionHeater 生成相应的加热器电学端口)
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
    c.add_port("RingSmid1", port=RP1.ports["o2"])
    c.add_port("RingSmid2", port=RP3.ports["o2"])
    c.add_port("RingBmid1", port=RP2.ports["o1"])
    c.add_port("RingBmid2", port=RP4.ports["o1"])
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
    print("length="+str(RingPath1.length()*4))
    if HeaterConfig:
        rrun1 = gf.path.straight(length=LengthRun / 2)
        rring1 = gf.path.arc(radius=RadiusRing, angle=45)
        rring2 = gf.path.arc(radius=RadiusRing, angle=-70)
        rb1 = euler_Bend_Half(radius=RadiusRing/2, angle=45, p=0.5)
        rb2 = euler_Bend_Half(radius=RadiusRing, angle=-20, p=0.5)
        HeatPath1 = rring1 + rb1
        HeatPath2 = rring2 + rb2+ rrun1
        HeatPath3 = rrun1
        heater = gf.Component()
        RHP1 = heater << DifferentHeater(PathHeat=HeatPath1,WidthWG=WidthRing,HeaterConfig=HeaterConfig)
        RHP2 = heater << DifferentHeater(PathHeat=HeatPath2,WidthWG=WidthRing,HeaterConfig=HeaterConfig)
        RHP3 = heater << DifferentHeater(PathHeat=HeatPath3,WidthWG=WidthRing,HeaterConfig=HeaterConfig)
        RHP2.connect("HeatIn", other=RHP1.ports["HeatIn"])
        RHP3.connect("HeatOut", other=RHP2.ports["HeatOut"])
        heater.add_port("HeatBmid1", port=RHP1.ports["HeatIn"])
        heater.add_port("HeatBmid2", port=RHP2.ports["HeatIn"])
        heater.add_port("HeatIn", port=RHP3.ports["HeatIn"])
        heater.add_port("HeatOut",port=RHP1.ports["HeatOut"])
        if HeaterConfig.TypeHeater == 'spilt':
            heater.add_port("HeatLIn", port=RHP3.ports["HeatLIn"])
            heater.add_port("HeatRIn", port=RHP3.ports["HeatRIn"])
            heater.add_port("HeatLOut", port=RHP1.ports["HeatLOut"])
            heater.add_port("HeatROut", port=RHP1.ports["HeatROut"])
        heater = snap_all_polygons_iteratively(heater)
        h = c << heater
        h.connect("HeatBmid1",c.ports["RingBmid1"],allow_width_mismatch=True,allow_layer_mismatch=True)
        if DirectionHeater == 'down':
            h.mirror_x(RP1.ports["o1"].center[0])
        # h.mirror_x(h.ports["HeatBmid1"].center[0])
        if HeaterConfig.TypeHeater == "side":
            heater.add_port("HeatSIn", port=RHP3.ports["HeatSIn"])
            heater.add_port("HeatSOut", port=RHP1.ports["HeatSOut"])
        for port in h.ports:
            c.add_port(port.name, port=port)
    return c


# %% RaceTrackPulley2
@gf.cell
def RaceTrackS(
        WidthRing: float = 8,
        WidthHeat: float = 10,
        WidthRoute: float = 20,
        LengthRun: float = 200,
        RadiusRing: float = 100,
        GapCouple: float = 1,
        LengthCouple: float = 200,
        GapHeat: float = 10,
        DeltaHeat: float = 20,
        IsAD: bool = True,
        IsHeat: bool = True,
        TypeHeater: str = "center",
        oplayer: LayerSpec = LAYER.WG,
        elelayer: LayerSpec = LAYER.M2,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        Name: str = "RaceTrack_Pulley",
        HeaterConfig: HeaterConfigClass = heaterconfig0,
) -> Component:
    """
    创建一个基于直线耦合的跑道环谐振器。
    耦合通过环的直线段与平行总线波导之间的近场相互作用实现。
    支持Add/Drop端口和不同类型的加热器（包括中心加热、侧边加热或GSG电极）。

    参数:
        WidthRing (float): 跑道环波导宽度 (µm)。
        WidthHeat (float): （如果IsHeat）加热条宽度 (µm)。
        WidthRoute (float): （如果IsHeat）加热器引出线宽度 (µm)。
        LengthRun (float): 跑道环直线段长度 (µm)。
        RadiusRing (float): 跑道环弯曲半径 (µm)。
        GapCouple (float): 环的直线段与耦合总线之间的间隙 (µm)。
        LengthCouple (float): 直线耦合段的长度 (µm)。
        GapHeat (float): 波导与加热器（或GSG的G电极）的间隙 (µm)。
        DeltaHeat (float): 加热器/GSG电极的几何偏移参数 (µm)。
                           - TypeHeater="center": 中心加热条的y偏移。
                           - TypeHeater="side": 侧边加热条的y偏移。
        IsAD (bool): 是否包含Add/Drop端口。
        IsHeat (bool): 是否添加加热器/电极。
        TypeHeater (str): 加热器/电极类型:
                          - "center": 在环的直线段中心下方/上方放置加热条。
                          - "side": 在环的直线段一侧放置加热条。
                          - "ele": 在环的一侧放置GSG（Ground-Signal-Ground）电极。
                          - "default", "snake": (如果DifferentHeater支持)
        DirectionHeater (str): 当TypeHeater="side"时，指定加热器在"up"或"down"。
        oplayer (LayerSpec): 光学波导层。
        elelayer (LayerSpec): GSG电极层。
        heatlayer (LayerSpec): 普通加热器层。
        routelayer, vialayer: 用于加热器或GSG的布线和过孔层。
        Name (str): 组件名称。

    返回:
        Component: 生成的直线耦合跑道环谐振器组件。

    端口: (与RaceTrackP类似，但耦合机制不同)
        Input, Through, Add, Drop.
        RingSmid1, RingSmid2, RingBmid1, RingBmid2: 环上参考点。
        Rcen1, Rcen2: 弯曲中心参考点。
        (以及可能的加热器/电极端口)
    """
    if HeaterConfig.TypeHeater == "center":
        return RaceTrackStrHC(
            WidthRing=WidthRing,
            LengthRun=LengthRun,
            RadiusRing=RadiusRing,
            GapCouple=GapCouple,
            LengthCouple=LengthCouple,
            IsAD=IsAD,
            IsHeat=IsHeat,
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
    rring1 = gf.path.arc(radius=RadiusRing, angle=60)
    rring2 = gf.path.arc(radius=RadiusRing, angle=-60)
    rring3 = gf.path.arc(radius=RadiusRing, angle=-30)
    rb1 = euler_Bend_Half(radius=RadiusRing, angle=30, p=0.5)
    rb2 = euler_Bend_Half(radius=RadiusRing, angle=-30, p=0.5)
    rbh1 = euler_Bend_Half(radius=RadiusRing-4*WidthRoute, angle=-60, p=0.5)
    RingPath1 = rring1 + rb1 + rrun1
    RingPath2 = rring2 + rb2 + rrun1
    HeatPath1 = rring1 + rb1 + rrun1
    HeatPath2 = rring3 + rbh1
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
    c.add_port("RingBmid1", port=RP2.ports["o1"])
    c.add_port("RingBmid2", port=RP4.ports["o1"])
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
    if HeaterConfig.TypeHeater == "ELE" or TypeHeater == "ele":
        ele = c << GSGELE(
            WidthS=20,WidthG=80,GapGS=5,LengthEle=LengthRun+60,IsPad=True,LengthToPad=90,
            elelayer=elelayer,
        )
        ele.connect("Oin1", other=RP1.ports["o2"],allow_width_mismatch=True,allow_layer_mismatch=True)
        ele.movey(-LengthRun/2)
    else:
        heater = gf.Component()
        RHP1 = heater << DifferentHeater(PathHeat=HeatPath1,WidthWG=WidthRing,HeaterConfig=HeaterConfig)
        RHP2 = heater << DifferentHeater(PathHeat=HeatPath1,WidthWG=WidthRing,HeaterConfig=HeaterConfig)
        RHP3 = heater << DifferentHeater(PathHeat=HeatPath2,WidthWG=WidthRing,HeaterConfig=HeaterConfig)
        RHP4 = heater << DifferentHeater(PathHeat=HeatPath2,WidthWG=WidthRing,HeaterConfig=HeaterConfig)
        RHP2.connect("HeatOut", other=RHP1.ports["HeatOut"],mirror=True)
        RHP3.connect("HeatIn", other=RHP1.ports["HeatIn"])
        RHP4.connect("HeatIn", other=RHP2.ports["HeatIn"],mirror=True)
        heater.add_port("HeatBmid1", port=RHP1.ports["HeatIn"])
        heater.add_port("HeatBmin2", port=RHP2.ports["HeatIn"])
        heater.add_port("HeatIn", port=RHP3.ports["HeatOut"])
        heater.add_port("HeatOut",port=RHP4.ports["HeatOut"])
        h = c << heater
        h.connect("HeatBmid1",c.ports["RingBmid1"],allow_width_mismatch=True,allow_layer_mismatch=True)
        h.mirror_x(h.ports["HeatBmid1"].center[0])
        if TypeHeater == "side":
            h.movey(-DeltaHeat)
        heater = snap_all_polygons_iteratively(heater)
    print("length="+str(RingPath1.length()*4))
    # if IsLabels:
    add_labels_to_ports(c)
    return c

# %% RaceTrackStrH2
def RaceTrackStrHC(
        WidthRing: float = 8,
        WidthHeat: float = 8,
        WidthRoute: float = 50,
        LengthRun: float = 200,
        RadiusRing: float = 500,
        GapCouple: float = 1,
        LengthCouple: float = 200,
        IsAD: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        HeaterConfig: HeaterConfigClass = None
) -> Component:
    """
     创建一个带有加热电极的环形跑道波导组件，支持输入、输出、添加和丢弃端口。
     加热电极置于中间

     参数：
         WidthRing: 环形波导的宽度（单位：um）。
         WidthHeat: 加热电极的宽度（单位：um）。
         WidthRoute: 加热电极路径的宽度（单位：um）。
         DeltaHeat: 加热电极中心距离波导中心的偏移量（单位：um）。
         GapRoute: 加热电极之间的间距（单位：um）。
         LengthRun: 直线部分的长度（单位：um）。
         RadiusRing: 环形波导的半径（单位：um）。
         GapCouple: 环形波导与耦合波导之间的间距（单位：um）。
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
    # add_labels_to_ports(c)
    print("length="+str(RingPath1.length()*4))
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
        GapCouple: float = 1,
        AngleCouple: float = 20,
        IsAD: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass=None,
) -> Component:
    """
     创建一个带有中心放置加热电极的直线耦合跑道环谐振器。
     加热电极位于跑道环的几何中心区域（通常在两个直线段之间），并通过特定结构引出。

     参数:
         WidthRing (float): 跑道环波导宽度 (µm)。
         WidthHeat (float): 中心加热条的宽度 (µm)。
         WidthRoute (float): 加热器引出金属线的宽度 (µm)。
         DeltaHeat (float): 加热条中心相对于环几何中心线的垂直偏移量 (µm)。
                            负值表示向下偏移。
         GapRoute (float): 加热器引出结构（例如两个引出臂之间）的间隙或相关尺寸 (µm)。
         LengthRun (float): 跑道环直线段长度 (µm)。
         RadiusRing (float): 跑道环弯曲半径 (µm)。
         GapCouple (float): 环与耦合总线的间隙 (µm)。
         LengthCouple (float): 直线耦合段的长度 (µm)。
         IsAD (bool): 是否包含Add/Drop端口。
         IsHeat (bool): 是否添加加热器（在此函数中通常为True）。
         oplayer (LayerSpec): 光学波导层。
         heatlayer (LayerSpec): 加热器主条层。
         routelayer (LayerSpec): 加热器引出线层。
         vialayer (LayerSpec): 过孔层（如果引出结构需要）。
         Name (str): 组件名称。

     返回:
         Component: 生成的带中心加热的跑道环组件。

     端口: (与RaceTrackS类似，但加热器端口不同)
         Input, Through, Add, Drop.
         HeatIn, HeatOut: 中心加热器的电学端口。
     """
    c = gf.Component()
    layer = oplayer
    secring = gf.Section(width=WidthRing, offset=0, layer=layer, port_names=("o1", "o2"))
    secnring = gf.Section(width=WidthNear, offset=0, layer=layer, port_names=("o1", "o2"))
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
    return c

__all__ = ['RaceTrackS', 'RaceTrackP', 'RaceTrackStrHC', 'TaperRaceTrackPulley']
