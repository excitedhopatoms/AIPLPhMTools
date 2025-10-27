from .BasicDefine import *
from .RaceTrack import *
from .Ring import *

# %% Double RaceTrack Cavity
@gf.cell
def DoubleRaceTrack(
        WidthRing: float = 8,
        WidthNear: float = 5,
        LengthCouple: float = 10,
        LengthRun: float = 200,
        LengthR2R: float = 300,
        RadiusR2R: float = None,
        RadiusRing: float = 100,
        GapCouple: float = 1,
        AngleCouple: float = 20,
        DeltaRoundTrip: float = 2,
        TypeCouple: str = "p",
        TypeR2R: str = "straight",
        DirectionsHeater: [str] = ["up", "up"],
        DirectionsRing: [str] = ["up", "up"],
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass=None,
) -> Component:
    """
    创建一个双跑道环谐振腔组件。
    该组件由两个可独立调谐（如果`IsHeat`为True）的跑道环谐振器串联而成。
    支持不同类型的环耦合方式和环间连接方式。

    参数:
        WidthRing (float): 跑道环中波导的宽度 (µm)。
        WidthNear (float): 当 `TypeCouple` 为 "p" (滑轮耦合) 时，耦合总线的宽度 (µm)。
        WidthHeat (float): 加热器的宽度 (µm)。
        LengthCouple (float): 当 `TypeCouple` 为 "s" (直线耦合) 时，直线耦合段的长度 (µm)。
        LengthRun (float): 第一个跑道环直线部分的长度 (µm)。
        LengthR2R (float): 两个环之间连接直波导的长度 (µm)，当 `TypeR2R` 为 "straight" 时使用。
        RadiusR2R (float | None): 两个环之间连接弯曲的半径 (µm)，当 `TypeR2R` 为 "bend" 时使用。
                                  如果为 None，则基于 `RadiusRing` 计算。
        RadiusRing (float): 跑道环的弯曲半径 (µm)。
        GapHeat (float): 波导与加热器之间的间隙 (µm)。
        GapCouple (float): 环与耦合总线之间的间隙 (µm)。
        AngleCouple (float): 当 `TypeCouple` 为 "p" 时，滑轮耦合器的耦合角度 (度)。
        DeltaHeat (float): 加热器的几何调整参数 (µm)，传递给内部环组件。
        DeltaRun (float): 第二个跑道环的直线段长度相对于第一个环的增量 (µm)。
                          L_run_ring2 = LengthRun + DeltaRun。
        IsHeat (bool): 是否为两个环都添加加热器。
        TypeCouple (str): 环的耦合类型。"p" 代表滑轮耦合 (依赖 `RaceTrackP`)，
                          "s" 代表直线耦合 (依赖 `RaceTrackS`)。
        TypeHeater (str): 加热器的类型，传递给内部的跑道环组件。
        TypeR2R (str): 两个环之间的连接方式。"straight" 使用直波导连接Drop端口，
                       "bend" 尝试使用弯曲波导连接（当前实现可能不完整或需要调整）。
        DirectionsHeater (list[str]): 长度为2的列表，分别指定第一个和第二个环加热器的方向/位置
                                     （例如 ["up", "down"]），具体行为取决于内部环组件的实现。
        DirectionsRing (list[str]): 长度为2的列表，分别指定第一个和第二个环的几何方向或镜像状态
                                   （例如 ["up", "down"]），用于调整环的开口或整体朝向。
        oplayer (LayerSpec): 光学波导层。
        heatlayer (LayerSpec): 加热器层。
        routelayer (LayerSpec): 加热器布线层。
        vialayer (LayerSpec): 过孔层。

    返回:
        Component: 生成的双跑道环谐振腔组件。

    端口:
        o1: 第一个环的输入端口 (Input)。
        o2: 第二个环的输入端口 (Input)。
        R2Ro1: 第一个环的下载端口 (Drop)，作为环间连接的起点。
        R1Add, R1Drop, R1Input, R1Through: 第一个环的四个标准端口。
        R2Add, R2Drop, R2Input, R2Through: 第二个环的四个标准端口。
        (如果 IsHeat=True，还会根据内部环组件的实现，继承并重命名加热器端口，
         例如 R1HeatIn, R1HeatOut, R2HeatIn, R2HeatOut)
    """
    c = gf.Component()
    if TypeCouple == "p" or TypeCouple == "P":
        ring1 = c << RaceTrackP(
            WidthRing=WidthRing, WidthNear=WidthNear, GapCouple=GapCouple,HeaterConfig=HeaterConfig,
            LengthRun=LengthRun, RadiusRing=RadiusRing, AngleCouple=AngleCouple, oplayer=oplayer,DirectionHeater=DirectionsHeater[0],
        )
        ring2 = c << RaceTrackP(
            WidthRing=WidthRing, WidthNear=WidthNear, GapCouple=GapCouple,HeaterConfig=HeaterConfig,
            LengthRun=LengthRun + DeltaRoundTrip/2, RadiusRing=RadiusRing, AngleCouple=AngleCouple, oplayer=oplayer,DirectionHeater=DirectionsHeater[1],
        )
    elif TypeCouple == "s" or TypeCouple == "S":
        ring1 = c << RaceTrackS(
            WidthRing=WidthRing,
            LengthRun=LengthRun,
            RadiusRing=RadiusRing,
            GapCouple=GapCouple,
            LengthCouple=LengthCouple,
            IsAD=True,
            oplayer=oplayer,
            HeaterConfig=HeaterConfig,
            DirectionHeater=DirectionsHeater[0],
        )
        ring2 = c << RaceTrackS(
            WidthRing=WidthRing,
            LengthRun=LengthRun+DeltaRoundTrip/2,
            RadiusRing=RadiusRing,
            GapCouple=GapCouple,
            LengthCouple=LengthCouple,
            IsAD=True,
            oplayer=oplayer,
            HeaterConfig=HeaterConfig,
            DirectionHeater=DirectionsHeater[1],
        )
        WidthNear=WidthRing
    if TypeR2R == "straight":
        str_R2R = c << GfCStraight(width=WidthNear, length=LengthR2R, layer=oplayer)
        ring1.connect("Drop", str_R2R.ports["o1"])
        ring2.connect("Drop", str_R2R.ports["o2"], allow_width_mismatch=True)
    elif TypeR2R == "bend":
        if RadiusR2R is None:
            RadiusR2R = RadiusRing - 10
        str_R2R = c << GfCStraight(width=WidthNear, length=LengthR2R, layer=oplayer)
        str_R2R.connect("o1", ring1.ports["Drop"])
        ring2.connect("Drop", str_R2R.ports["o2"], allow_width_mismatch=True)
        # Add circular bends for ring-to-ring connection
        bendl1 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=90, layer=oplayer)
        bendr1 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=90, layer=oplayer)
        bendl2 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=-90, layer=oplayer)
        bendr2 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=-90, layer=oplayer)
        bendl1.connect("o1", ring1.ports["Drop"])
        bendl2.connect("o1", bendl1.ports["o2"])
        bendr1.connect("o2", ring2.ports["Drop"])
        bendr2.connect("o2", bendr1.ports["o1"])
        route = gf.routing.route_single(c, bendl2.ports["o2"], bendr2.ports["o1"], route_width=WidthNear, layer=oplayer)
        # c.add(route.references)
        c.remove(str_R2R)

    if DirectionsRing[0] == "down":
        ring1.mirror_y(ring1.ports["Drop"].center[1])
    if DirectionsRing[1] == "up":
        ring2.mirror_y(ring2.ports["Drop"].center[1])
    c.add_port(name="o1", port=ring1.ports["Input"])
    c.add_port(name="o2", port=ring2.ports["Input"])
    c.add_port(name="R2Ro1", port=ring1.ports["Drop"])
    c.add_port(name="R1Add", port=ring1.ports["Add"])
    c.add_port(name="R1Drop", port=ring1.ports["Drop"])
    c.add_port(name="R1Input", port=ring1.ports["Input"])
    c.add_port(name="R1Through", port=ring1.ports["Through"])
    c.add_port(name="R2Add", port=ring2.ports["Add"])
    c.add_port(name="R2Drop", port=ring2.ports["Drop"])
    c.add_port(name="R2Input", port=ring2.ports["Input"])
    c.add_port(name="R2Through", port=ring2.ports["Through"])

    for port in ring1.ports:
        if "Heat" in port.name:
            c.add_port(name="R1" + port.name, port=ring1.ports[port.name])
    for port in ring2.ports:
        if "Heat" in port.name:
            c.add_port(name="R2" + port.name, port=ring2.ports[port.name])
    add_labels_to_ports(c, label_layer=(512, 8))
    return c
# %% COupled Double Racetrack Cavity
def CoupleDouRaceTrack(
        WidthRing: float = 8,
        WidthNear: float = 1,
        LengthRun: float = 200,
        RadiusRing: float = 100,
        GapCoupleOut: float = 1,
        GapCoupleIn: float = 1,
        LengthCoupleOut: float = 200,
        LengthCoupleIn: float = 100,
        AngleCouple:float = 10,
        DeltaRun: float = 20,
        HeaterConfig:HeaterConfigClass=None,
        DirectionsHeater = ['down', 'down'],
        TypeCouple: str = "S",
        oplayer: LayerSpec = LAYER.WG,
        elelayer: LayerSpec = LAYER.M2,
)->Component:
    """
    创建一个耦合的双跑道环谐振腔组件。
    与 `DoubleRaceTrack` 不同，此组件中的两个跑道环是通过它们的一个侧面（例如，直线段）
    直接耦合（通过 `GapCoupleIn`），而不是通过它们的Add/Drop端口串联。
    每个环仍然有其自己的外部总线耦合（通过 `GapCoupleOut`）。

    参数:
        (许多参数与 DoubleRaceTrack 中的类似，用于定义单个跑道环的几何和加热)
        WidthNear (float): 当 `TypeCouple`='p'时，外部耦合总线的宽度 (µm)。
        GapCoupleOut (float): 跑道环与外部总线（输入/直通）之间的耦合间隙 (µm)。
        GapCoupleIn (float): 两个跑道环之间的内部耦合间隙 (µm)。
        LengthCoupleOut (float): 当 `TypeCouple`='s'时，跑道环与外部总线的直线耦合长度 (µm)。
        LengthCoupleIn (float): 用于定位两个环的相对位置的参数，可能与内部耦合长度有关 (µm)。
        AngleCouple (float): 当 `TypeCouple`='p'时，滑轮耦合的角度 (度)。
        DeltaRun (float): 第二个跑道环直线段长度与第一个的差值 (µm)。
        DirectionsHeater (list[str]): 两个环加热器的方向/位置。
        TypeCouple (str): 环与外部总线的耦合类型 ('s'或'p')。环间耦合是侧面耦合。

    返回:
        Component: 生成的耦合双跑道环谐振腔组件。

    端口:
        R1Input, R1Through: 第一个环的外部输入和直通端口。
        R2Input, R2Through: 第二个环的外部输入和直通端口。
        (如果 IsHeat=True，还会继承并重命名两个环的加热器端口，如 R1HeatIn, R2HeatOut 等)
    """
    c = gf.Component()
    if TypeCouple == "s" or TypeCouple == "S":
        racetrack1 = c << RaceTrackS(
            WidthRing= WidthRing,
            LengthRun= LengthRun,
            RadiusRing= RadiusRing,GapCouple= GapCoupleOut,LengthCouple= LengthCoupleOut,
            HeaterConfig=HeaterConfig,DirectionsHeater=DirectionsHeater[0],
            IsAD= False,
            oplayer= oplayer)
        racetrack2 = c << RaceTrackS(
            WidthRing= WidthRing,
            LengthRun= LengthRun+DeltaRun,
            RadiusRing= RadiusRing,GapCouple= GapCoupleOut,LengthCouple= LengthCoupleOut,
            HeaterConfig=HeaterConfig, DirectionsHeater=DirectionsHeater[1],
            IsAD= False,
            oplayer= oplayer)
        racetrack1.connect("RingSmid1", other=racetrack2.ports["RingSmid1"])
        racetrack1.movex(+WidthRing + GapCoupleIn)
        racetrack1.movey(-DeltaRun / 2 + LengthCoupleIn - LengthRun)
    elif TypeCouple == "p" or TypeCouple == "P":
        racetrack1 = c << RaceTrackP(
            WidthRing=WidthRing, WidthNear=WidthNear, GapCouple=GapCoupleOut,
            LengthRun=LengthRun, RadiusRing=RadiusRing, AngleCouple=AngleCouple, oplayer=oplayer,IsAD=False,
            HeaterConfig=HeaterConfig, DirectionsHeater=DirectionsHeater[0],
        )
        racetrack2 = c << RaceTrackP(
            WidthRing=WidthRing, WidthNear=WidthNear, GapCouple=GapCoupleOut,
            LengthRun=LengthRun + DeltaRun, RadiusRing=RadiusRing, AngleCouple=AngleCouple, oplayer=oplayer,IsAD=False,
            HeaterConfig=HeaterConfig, DirectionsHeater=DirectionsHeater[1],
        )
        racetrack1.connect("RingSmid1", other=racetrack2.ports["RingSmid1"])
        racetrack1.movex(+WidthRing + GapCoupleIn)
        racetrack1.movey(-DeltaRun / 2 + LengthCoupleIn - LengthRun)
        racetrack2.mirror_y(racetrack2.ports["Input"].center[1])
        racetrack1.mirror_y(racetrack2.ports["Input"].center[1])

    for port in racetrack1.ports:
        if "Heat" in port.name:
            c.add_port(name="R1" + port.name, port=port)
    for port in racetrack2.ports:
        if "Heat" in port.name:
            c.add_port(name="R2" + port.name, port=port)
    c.add_port("R1Input",port=racetrack1.ports["Input"])
    c.add_port("R1Through", port=racetrack1.ports["Through"])
    c.add_port("R2Input", port=racetrack2.ports["Input"])
    c.add_port("R2Through", port=racetrack2.ports["Through"])
    return c