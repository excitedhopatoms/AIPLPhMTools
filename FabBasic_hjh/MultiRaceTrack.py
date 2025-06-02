from .BasicDefine import *
from .RaceTrack import *
from .Ring import *

# %% Double RaceTrack Cavity
@gf.cell
def DoubleRaceTrack(
        WidthRing: float = 8,
        WidthNear: float = 5,
        WidthHeat: float = 2,
        LengthCouple: float = 10,
        LengthRun: float = 200,
        LengthR2R: float = 300,
        RadiusR2R: float = None,
        RadiusRing: float = 100,
        GapHeat: float = 10,
        GapCouple: float = 1,
        AngleCouple: float = 20,
        DeltaHeat: float = 0,
        DeltaRun: float = 2,
        IsHeat: bool = False,
        TypeCouple: str = "p",
        TypeHeater: str = "default",
        TypeR2R: str = "straight",
        DirectionsHeater: [str] = ["up", "up"],
        DirectionsRing: [str] = ["up", "up"],
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个双环形跑道形谐振器组件，支持加热电极和环形波导的连接。
    双环形谐振器由两个环形波导组成，可以通过参数调整环的尺寸、间距和加热电极的配置。

    参数：
        WidthRing: 环形波导的宽度（单位：um）。
        WidthNear: 靠近环形波导的波导宽度（单位：um）。
        WidthHeat: 加热电极的宽度（单位：um）。
        WidthEnd: 末端波导的宽度（单位：um）。
        Pitch: 结构的间距（单位：um）。
        Period: 结构的周期（单位：um）。
        LengthTaper: 锥形波导的长度（单位：um）。
        LengthR2R: 环形波导之间的连接长度（单位：um）。
        RadiusRing: 环形波导的半径（单位：um）。
        RadiusBend0: 弯曲波导的半径（单位：um）。
        DeltaRadius: 两个环形波导的半径差（单位：um）。
        GapCouple: 环形波导之间的间隙（单位：um）。
        EndPort: 需要连接的端口列表。
        AngleCouple: 耦合角度（单位：度）。
        IsHeat: 是否包含加热电极。
        Name: 组件名称。
        oplayer: 光学波导层的定义。
        heatlayer: 加热层的定义。

    返回：
        Component: 包含双环形谐振器的组件。

    端口：
        o1: 第一个环形波导的输入端口。
        o2: 第二个环形波导的输入端口。
        r2ro1: 环形波导之间的连接端口。
        r1A: 第一个环形波导的 Add 端口。
        r1D: 第一个环形波导的 Drop 端口。
        r1I: 第一个环形波导的 Input 端口。
        r1T: 第一个环形波导的 Through 端口。
        r2A: 第二个环形波导的 Add 端口。
        r2D: 第二个环形波导的 Drop 端口。
        r2I: 第二个环形波导的 Input 端口。
        r2T: 第二个环形波导的 Through 端口。
        R1HeatIn: 第一个环形波导的加热输入端口（如果包含加热电极）。
        R1HeatOut: 第一个环形波导的加热输出端口（如果包含加热电极）。
        R2HeatIn: 第二个环形波导的加热输入端口（如果包含加热电极）。
        R2HeatOut: 第二个环形波导的加热输出端口（如果包含加热电极）。
    """
    c = gf.Component()
    if TypeCouple == "p" or TypeCouple == "P":
        ring1 = c << RaceTrackP(
            WidthRing=WidthRing, WidthNear=WidthNear, GapCouple=GapCouple,IsHeat=IsHeat,
            LengthRun=LengthRun, RadiusRing=RadiusRing, AngleCouple=AngleCouple, oplayer=oplayer
        )
        ring2 = c << RaceTrackP(
            WidthRing=WidthRing, WidthNear=WidthNear, GapCouple=GapCouple,IsHeat=IsHeat,
            LengthRun=LengthRun + DeltaRun, RadiusRing=RadiusRing, AngleCouple=AngleCouple, oplayer=oplayer
        )
    elif TypeCouple == "s" or TypeCouple == "S":
        ring1 = c << RaceTrackS(
            WidthRing=WidthRing,
            WidthHeat=WidthHeat,
            LengthRun=LengthRun,
            RadiusRing=RadiusRing,
            GapCouple=GapCouple,
            GapHeat=GapHeat,
            DeltaHeat=DeltaHeat,
            LengthCouple=LengthCouple,
            IsAD=True,
            IsHeat=IsHeat,
            oplayer=oplayer,
            heatlayer=heatlayer,
            vialayer=vialayer,
            routelayer=routelayer,
        )
        ring2 = c << RaceTrackS(
            WidthRing=WidthRing,
            WidthHeat=WidthHeat,
            LengthRun=LengthRun,
            RadiusRing=RadiusRing,
            GapCouple=GapCouple,
            GapHeat=GapHeat,
            DeltaHeat=DeltaHeat,
            LengthCouple=LengthCouple,
            IsAD=True,
            IsHeat=IsHeat,
            oplayer=oplayer,
            heatlayer=heatlayer,
            vialayer=vialayer,
            routelayer=routelayer,
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

    if IsHeat:
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
        WidthHeat: float = 10,
        WidthRoute: float = 20,
        WidthNear: float = 1,
        LengthRun: float = 200,
        RadiusRing: float = 100,
        GapCoupleOut: float = 1,
        GapCoupleIn: float = 1,
        LengthCoupleOut: float = 200,
        LengthCoupleIn: float = 100,
        AngleCouple:float = 10,
        GapHeat: float = 10,
        DeltaHeat: float = 0,
        DeltaRun: float = 20,
        IsHeat: bool = True,
        TypeHeater: str = "default",
        DirectionsHeater: str = ['down', 'down'],
        TypeCouple: str = "S",
        oplayer: LayerSpec = LAYER.WG,
        elelayer: LayerSpec = LAYER.M2,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
)->Component:
    c = gf.Component()
    if TypeCouple == "s" or TypeCouple == "S":
        racetrack1 = c << RaceTrackS(
            WidthRing= WidthRing,WidthHeat= WidthHeat,WidthRoute= WidthRoute,
            LengthRun= LengthRun,
            RadiusRing= RadiusRing,GapCouple= GapCoupleOut,LengthCouple= LengthCoupleOut,
            GapHeat= GapHeat,DeltaHeat= DeltaHeat,IsHeat= IsHeat,elelayer= elelayer,heatlayer= heatlayer,TypeHeater= TypeHeater,
            IsAD= False,
            oplayer= oplayer,routelayer= routelayer,vialayer= vialayer)
        racetrack2 = c << RaceTrackS(
            WidthRing= WidthRing,WidthHeat= WidthHeat,WidthRoute= WidthRoute,
            LengthRun= LengthRun+DeltaRun,
            RadiusRing= RadiusRing,GapCouple= GapCoupleOut,LengthCouple= LengthCoupleOut,
            GapHeat= GapHeat,DeltaHeat= DeltaHeat,IsHeat= IsHeat,elelayer= elelayer,heatlayer= heatlayer,TypeHeater= TypeHeater,
            IsAD= False,
            oplayer= oplayer,routelayer= routelayer,vialayer= vialayer)
    elif TypeCouple == "p" or TypeCouple == "P":
        racetrack1 = c << RaceTrackP(
            WidthRing=WidthRing, WidthNear=WidthNear, GapCouple=GapCoupleOut,IsHeat=IsHeat,
            LengthRun=LengthRun, RadiusRing=RadiusRing, AngleCouple=AngleCouple, oplayer=oplayer
        )
        racetrack2 = c << RaceTrackP(
            WidthRing=WidthRing, WidthNear=WidthNear, GapCouple=GapCoupleOut,IsHeat=IsHeat,
            LengthRun=LengthRun + DeltaRun, RadiusRing=RadiusRing, AngleCouple=AngleCouple, oplayer=oplayer
        )
    racetrack1.connect("RingSmid1",other=racetrack2.ports["RingSmid1"])
    racetrack1.movex(+WidthRing+GapCoupleIn)
    racetrack1.movey(DeltaRun/2-LengthCoupleIn+LengthRun)
    c.add_port("R1Input",port=racetrack1.ports["Input"])
    c.add_port("R1Through", port=racetrack1.ports["Through"])
    c.add_port("R2Input", port=racetrack2.ports["Input"])
    c.add_port("R2Through", port=racetrack2.ports["Through"])
    return c