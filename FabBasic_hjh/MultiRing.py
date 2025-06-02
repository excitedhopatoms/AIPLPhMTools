from .BasicDefine import *
from .RaceTrack import *
from .Ring import *


# %% DoubleRingPulley
@gf.cell
def DoubleRingPulley(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        LengthR2R: float = 150,
        RadiusRing: float = 100,
        RadiusR2R: float = None,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        GapHeat: float = 10,
        DeltaHeat: float = 0,
        AngleCouple: float = 20,
        IsHeat: bool = False,
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
    创建一个双环滑轮型（Pulley）谐振器组件。
    该组件由两个 `RingPulleyT1` 单元串联而成，第二个环的半径可以与第一个不同。
    支持为每个环独立配置加热器方向和环的几何朝向。

    参数:
        WidthRing (float): 环的波导宽度 (µm)。
        WidthNear (float): 耦合到环的总线波导宽度 (µm)。
        WidthHeat (float): 加热器的宽度 (µm)。
        LengthR2R (float): 当 `TypeR2R`="straight"时，连接两个环的直波导长度 (µm)。
        RadiusRing (float): 第一个环的弯曲半径 (µm)。
        RadiusR2R (float | None): 当 `TypeR2R`="bend"时，连接两个环的弯曲半径 (µm)。
                                  若为None，则设为 `RadiusRing - 10`。
        DeltaRadius (float): 第二个环的半径相对于第一个环的半径增量 (µm)。
                             `RadiusRing2 = RadiusRing + DeltaRadius`。
        GapRing (float): 环与其耦合总线之间的间隙 (µm)。
        GapHeat (float): 波导与加热器之间的间隙 (µm)。
        DeltaHeat (float): 传递给 `RingPulleyT1` 的加热器几何参数 (µm)。
        AngleCouple (float): `RingPulleyT1` 组件的耦合角度 (度)。
        IsHeat (bool): 是否为两个环都启用加热器。
        TypeHeater (str): 加热器的类型，传递给 `RingPulleyT1`。
        TypeR2R (str): 两个环之间的连接方式。"straight" 或 "bend"。
        DirectionsHeater (list[str]): 长度为2的列表，分别指定第一个和第二个环加热器的方向。
        DirectionsRing (list[str]): 长度为2的列表，分别指定第一个和第二个环的几何朝向或镜像状态。
        oplayer (LayerSpec): 光学波导层。
        heatlayer (LayerSpec): 加热器层。
        routelayer (LayerSpec): (当前函数未直接使用) 加热器布线层。
        vialayer (LayerSpec): (当前函数未直接使用) 过孔层。

    返回:
        Component: 生成的双环滑轮型谐振器组件。

    端口:
        o1: 第一个环的 "Input" 端口。
        o2: 第二个环的 "Input" 端口。 (注意：如果环是串联的，此端口可能不是外部输入)
        R2Ro1: 第一个环的 "Drop" 端口，用作环间连接的起点。
        R1Add, R1Drop, R1Input, R1Through: 第一个环的四个标准端口。
        R2Add, R2Drop, R2Input, R2Through: 第二个环的四个标准端口。
        (如果 IsHeat=True，还会添加如 R1HeatIn, R2HeatOut 等加热器端口)
    """
    c = gf.Component()
    ring1 = c << RingPulleyT1(
        WidthRing=WidthRing, WidthNear=WidthNear, WidthHeat=WidthHeat,
        RadiusRing=RadiusRing, GapRing=GapRing, GapHeat=GapHeat, DeltaHeat=DeltaHeat,
        AngleCouple=AngleCouple,
        oplayer=oplayer, heatlayer=heatlayer, TypeHeater=TypeHeater, IsHeat=IsHeat, DirectionHeater=DirectionsHeater[0]
    )
    ring2 = c << RingPulleyT1(
        WidthRing=WidthRing, WidthNear=WidthNear, WidthHeat=WidthHeat,
        RadiusRing=RadiusRing + DeltaRadius, GapRing=GapRing, GapHeat=GapHeat, DeltaHeat=DeltaHeat,
        AngleCouple=AngleCouple,
        oplayer=oplayer, heatlayer=heatlayer, TypeHeater=TypeHeater, IsHeat=IsHeat, DirectionHeater=DirectionsHeater[1]
    )
    if TypeR2R == "straight":
        str_R2R = c << GfCStraight(width=WidthNear, length=LengthR2R, layer=oplayer)
        str_R2R.connect("o1", ring1.ports["Drop"])
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


# %% DoubleRingPulley2：Snake Heater
@gf.cell
def DoubleRingPulley2HSn(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        LengthR2R: float = 150,
        RadiusRing: float = 100,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        GapHeat: float = 1,
        AngleCouple: float = 20,
        IsHeat: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个双环滑轮型谐振器组件，固定使用蛇形加热器 (`TypeHeater="snake"`)。
    这是 `DoubleRingPulley` 的一个特定配置版本。

    参数:
        (与 `DoubleRingPulley` 的参数类似，但 `TypeHeater` 被固定)
        GapHeat (float): 传递给内部蛇形加热器的间隙参数 (µm)。
        IsHeat (bool): 是否启用加热器。虽然类型固定为蛇形，但仍可通过此参数关闭加热。

    返回:
        Component: 生成的带蛇形加热器的双环滑轮谐振器。
    """
    c = DoubleRingPulley(
        WidthRing=WidthRing,
        WidthNear=WidthNear,
        WidthHeat=WidthHeat,
        LengthR2R=LengthR2R,
        RadiusRing=RadiusRing,
        DeltaRadius=DeltaRadius,
        GapRing=GapRing,
        GapHeat=GapHeat,
        AngleCouple=AngleCouple,
        IsHeat=IsHeat,
        oplayer=oplayer,
        heatlayer=heatlayer,
        TypeHeater="snake",
    )
    # add_labels_to_ports(c)
    return c


# %% DoubleRingPulley2：Snake Heater & ring to ring round
@gf.cell
def DoubleRingPulley2_1HSn(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        LengthR2R: float = 700,
        RadiusRing: float = 100,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        GapHeat: float = 1,
        AngleCouple: float = 20,
        Name: str = "Ring_Pulley_Snake_Heater_Round",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建双环滑轮型谐振器，固定使用蛇形加热器 (`TypeHeater="snake"`)
    并且两个环之间采用弯曲波导连接 (`TypeR2R="bend"`)。
    这是 `DoubleRingPulley` 的一个特定配置版本。

    参数:
        (与 `DoubleRingPulley` 的参数类似，但 `TypeHeater` 和 `TypeR2R` 被固定)
        LengthR2R (float): 影响环间弯曲连接布局的特征长度 (µm)。
        Name (str): 组件的名称。

    返回:
        Component: 生成的特定配置的双环组件。
    """
    c = DoubleRingPulley(
        WidthRing=WidthRing,
        WidthNear=WidthNear,
        WidthHeat=WidthHeat,
        LengthR2R=LengthR2R,
        RadiusRing=RadiusRing,
        DeltaRadius=DeltaRadius,
        GapRing=GapRing,
        GapHeat=GapHeat,
        AngleCouple=AngleCouple,
        IsHeat=True,
        Name=Name,
        oplayer=oplayer,
        heatlayer=heatlayer,
        TypeHeater="snake",
        TypeR2R="bend",
    )
    return c


# %% ADRAPRADR: ADRing + APRing + ADRing (with crossing ?)
@gf.cell
def ADRAPRADR(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        WidthHeat: float = 2,
        WidthSingle: float = 0.45,
        LengthTaper: float = 100,
        LengthR2R: float = 50,
        LengthR2C: float = 2,
        RadiusRing: float = 100,
        RadiusCrossBend: float = 100,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        AngleCouple: float = 20,
        AngleCouple3: float = 40,
        IsHeat: bool = False,
        IsSquare: bool = True,
        Name: str = "ADRAPRADR",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        CrossComp: Component = None,
) -> Component:
    """
    创建一个由三个环组成的谐振结构：两个Add-Drop环（ADR1, ADR2）夹着一个全通环（APR, ring3）。
    ADR1的Drop连接到APR的Input，APR的Through连接到ADR2的Drop。
    可以选择是否通过一个交叉波导组件连接ADR1的Input和ADR2的Input。

    参数:
        (大部分参数用于定义内部的 `RingPulley` 和 `RingPulley2` 组件)
        WidthSingle (float): 当 `IsSquare`=True时，连接到交叉波导的波导宽度 (µm)。
        LengthR2R (float): ADR1到APR，以及APR到ADR2的连接直波导长度 (µm)。
        LengthR2C (float): 当 `IsSquare`=True时，从外部到交叉波导的连接直波导长度 (µm)。
        RadiusCrossBend (float): 当 `IsSquare`=True时，连接到交叉波导的弯曲半径 (µm)。
        DeltaRadius (float): 中间环 (ring3) 相对于两侧AD环的半径差异 (µm)。
        AngleCouple3 (float): 中间环 (ring3, 使用RingPulley2) 的耦合角度 (度)。
        IsSquare (bool): 如果为True，则尝试以方形布局连接ADR1和ADR2的Input端口到提供的`CrossComp`。
        CrossComp (ComponentSpec | None): 可选的外部交叉波导组件。如果`IsSquare`为True且提供了此组件，
                                        则会尝试使用它。

    返回:
        Component: 生成的 ADR-AP-ADR 结构组件。

    端口:
        (如果IsSquare=False，则没有co2, co3端口，ADR1和ADR2的Input端口直接暴露)
        co2, co3: (仅当IsSquare=True且CrossComp提供时) 交叉波导的另外两个端口。
        r1Th, r1Ad: 第一个AD环的Through和Add端口。
        r2Th, r2Ad: 第二个AD环的Through和Add端口。
        r1L, r1R, r2L, r2R, r3L, r3R: 三个环的加热器端口（如果IsHeat=True且内部环组件生成这些端口）。
    """
    TriRing = gf.Component()
    ring1 = TriRing << RingPulley(
        IsAD=True, WidthRing=WidthRing, RadiusRing=RadiusRing, oplayer=oplayer, GapRing=GapRing,
        WidthNear=WidthNear, AngleCouple=AngleCouple, IsHeat=IsHeat, heatlayer=heatlayer, WidthHeat=WidthHeat
    )
    ring2 = TriRing << RingPulley(
        IsAD=True, WidthRing=WidthRing, RadiusRing=RadiusRing + DeltaRadius, oplayer=oplayer, GapRing=GapRing,
        WidthNear=WidthNear, AngleCouple=AngleCouple, IsHeat=IsHeat, heatlayer=heatlayer, WidthHeat=WidthHeat
    )
    ring3 = TriRing << RingPulley2(
        WidthRing=WidthRing, RadiusRing=RadiusRing + DeltaRadius / 2, oplayer=oplayer, GapRing=GapRing,
        WidthNear=WidthNear, AngleCouple=AngleCouple3, IsHeat=IsHeat, heatlayer=heatlayer, WidthHeat=WidthHeat
    )
    str_r1r3 = TriRing << GfCStraight(length=LengthR2R, width=WidthNear, layer=oplayer)
    str_r2r3 = TriRing << GfCStraight(length=LengthR2R, width=WidthNear, layer=oplayer)
    str_r1r3.connect("o1", ring1.ports["Drop"])
    ring3.connect("Input", str_r1r3.ports["o2"], mirror=True)
    str_r2r3.connect("o1", ring3.ports["Through"])
    ring2.connect("Drop", str_r2r3.ports["o2"])

    if IsSquare and CrossComp:
        crossing = TriRing << CrossComp
        str_r12c = TriRing << GfCStraight(length=LengthR2C, width=WidthNear, layer=oplayer)
        str_r22c = TriRing << GfCStraight(length=LengthR2C, width=WidthNear, layer=oplayer)
        str_r12c.connect("o2", ring1.ports["Input"])
        str_r22c.connect("o1", ring2.ports["Input"])
        bend_r12c = TriRing << gf.c.bend_euler(width=WidthNear, radius=RadiusCrossBend, angle=-90, layer=oplayer)
        bend_r22c = TriRing << gf.c.bend_euler(width=WidthNear, radius=RadiusCrossBend, angle=-90, layer=oplayer)
        bend_r12c.connect("o2", str_r12c.ports["o1"])
        bend_r22c.connect("o1", str_r22c.ports["o2"])
        crossing.connect("o1", bend_r12c.ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True)
        crossing.movey(bend_r22c.ports["o2"].center[1] - crossing.ports["o4"].center[1])
        route_cr1 = gf.routing.get_route(crossing.ports["o1"], bend_r12c.ports["o1"], width=WidthNear, layer=oplayer)
        route_cr2 = gf.routing.get_route(crossing.ports["o4"], bend_r22c.ports["o2"], width=WidthNear, layer=oplayer)
        TriRing.add(route_cr1.references)
        TriRing.add(route_cr2.references)
        TriRing.add_port(name="co2", port=crossing.ports["o2"])
        TriRing.add_port(name="co3", port=crossing.ports["o3"])

    TriRing.add_port("r1Th", port=ring1.ports["Through"])
    TriRing.add_port("r1Ad", port=ring1.ports["Add"])
    TriRing.add_port("r2Th", port=ring2.ports["Through"])
    TriRing.add_port("r2Ad", port=ring2.ports["Add"])
    TriRing.add_port("r1L", port=ring1.ports["RingL"])
    TriRing.add_port("r1R", port=ring1.ports["RingR"])
    TriRing.add_port("r2L", port=ring2.ports["RingL"])
    TriRing.add_port("r2R", port=ring2.ports["RingR"])
    TriRing.add_port("r3L", port=ring3.ports["RingL"])
    TriRing.add_port("r3R", port=ring3.ports["RingR"])
    add_labels_to_ports(TriRing)
    return TriRing

# %% CoupleCavity
@gf.cell
def CoupleRingDRT1(
        WidthRing1: float = 1,
        WidthNear1: float = 0.9,
        WidthHeat1: float = 2,
        RadiusRing1: float = 100,
        GapRB1: float = 2,
        GapHeat1: float = 1,
        DeltaHeat1: float = 0,
        AngleCouple1: float = 20,
        WidthRing2: float = None,
        WidthNear2: float = None,
        WidthHeat2: float = None,
        LengthNear2: float = 110,
        RadiusRing2: float = None,
        GapRB2: float = 3,
        GapHeat2: float = None,
        DeltaHeat2: float = 0,
        AngleR12: float = 30,
        GapRR: float = 1,
        GapHeat: float = 10,
        IsHeat: bool = True,
        TypeHeaterR1: str = "default",
        TypeHeaterR2: str = "default",
        TypeR2R: str = "strsight",
        DirectionsHeater: [str] = ["up", "down"],
        Name: str = "Ring_Pulley",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个由两个可配置参数的 `RingPulleyT1` 单元组成的耦合环结构。
    第二个环 (`ring2_c` - 仅光学部分) 相对于第一个环 (`ring1`) 进行旋转和平移定位，
    并通过两条直波导 (`str_ring2_1`, `str_ring2_2`) 连接到其概念上的耦合总线。
    加热器部分 (`ring2h`) 是独立获取并对齐的。

    这种结构设计比较特殊，环2的光学部分和加热部分是分开处理和对齐的。

    参数:
        (参数分为两组，分别对应ring1和ring2的 RingPulleyT1 配置)
        WidthRing1, WidthNear1, ..., AngleCouple1: 第一个环的参数。
        WidthRing2, WidthNear2, ..., RadiusRing2, GapRB2: 第二个环的参数。
            如果为None，则通常继承自第一个环的对应参数。
        LengthNear2 (float): 第二个环耦合总线的长度 (µm)。
        DeltaHeat2 (float | None): 第二个环加热器的DeltaHeat参数。
        AngleR12 (float): 第二个环相对于第一个环的旋转角度 (度)，旋转中心是第一个环的中心。
        GapRR (float): 两个环之间的（期望）间隙 (µm)，用于定位第二个环。
        IsHeat (bool): 是否为两个环都启用加热器。
        TypeHeaterR1, TypeHeaterR2: 两个环各自的加热器类型。
        DirectionsHeater (list[str]): 两个环加热器的方向。
        Name (str): 组件名称。
        oplayer, heatlayer: GDS图层。

    返回:
        Component: 生成的耦合双环组件。

    端口:
        Input, Through: 第一个环的外部输入/直通端口。
        Add, Drop: 连接到第二个环耦合总线的外部端口。
        Ring1C, Ring2C: 两个环的中心参考端口。
        (以及可能的加热器端口 R1Heat..., R2Heat...)
    """
    if WidthRing2 is None:
        WidthRing2 = WidthRing1
    if WidthHeat2 is None:
        WidthHeat2 = WidthHeat1
    if RadiusRing2 is None:
        RadiusRing2 = RadiusRing1
    if WidthNear2 is None:
        WidthNear2 = WidthNear1
    if GapHeat2 is None:
        GapHeat2 = GapHeat1
    if DeltaHeat2 is None:
        DeltaHeat2 = DeltaHeat1
    c = gf.Component()
    ring1 = c << RingPulleyT1(
        WidthRing=WidthRing1, WidthNear=WidthNear1, WidthHeat=WidthHeat1,
        RadiusRing=RadiusRing1, GapRing=GapRB1, GapHeat=GapHeat1, DeltaHeat=DeltaHeat1,
        AngleCouple=AngleCouple1, IsAD=False,
        oplayer=oplayer, heatlayer=heatlayer, TypeHeater=TypeHeaterR1, IsHeat=IsHeat,
        DirectionHeater=DirectionsHeater[0]
    )
    ring2_c = gf.Component('ring2_c')
    ring2_c << gf.c.ring(width=WidthRing2, radius=RadiusRing2, layer=oplayer)
    ring2_c.add_port("RingC", center=[0, 0], layer=oplayer, width=1)
    ring2 = c << ring2_c
    ring2.move(
        ring1.ports['RingC'].center + [0, -(RadiusRing1 + RadiusRing2 + WidthRing1 / 2 + WidthRing2 / 2 + GapRR)])
    ring2.rotate(AngleR12, ring1.ports['RingC'].center)
    str_ring2_1 = c << GfCStraight(width=WidthNear2, length=LengthNear2 / 2, layer=oplayer)
    str_ring2_1.move(ring2.ports["RingC"].center + [0, -WidthRing2 / 2 - WidthNear2 / 2 - RadiusRing2 - GapRB2])
    str_ring2_2 = c << GfCStraight(width=WidthNear2, length=LengthNear2 / 2, layer=oplayer)
    str_ring2_2.connect('o2', str_ring2_1.ports['o1'])
    ring2_hc = RingPulleyT1(
        WidthRing=WidthRing2, WidthNear=WidthNear2, WidthHeat=WidthHeat2,
        RadiusRing=RadiusRing2, GapRing=GapRB2, GapHeat=GapHeat2, DeltaHeat=DeltaHeat2,
        AngleCouple=AngleCouple1, IsAD=False,
        oplayer=oplayer, heatlayer=heatlayer, TypeHeater=TypeHeaterR2, IsHeat=IsHeat,
        DirectionHeater=DirectionsHeater[1]
    )
    ring2h = c << GetFromLayer(ring2_hc, OLayer=heatlayer)
    ring2h.move(ring2.ports["RingC"].center - ring2h.ports["RingC"].center)

    # c.add_port(name="R1Add", port=ring1.ports["Add"])
    # c.add_port(name="R1Drop", port=ring1.ports["Drop"])
    c.add_port(name="Input", port=ring1.ports["Input"])
    c.add_port(name="Through", port=ring1.ports["Through"])
    c.add_port(name="Add", port=str_ring2_2.ports["o1"])
    c.add_port(name="Drop", port=str_ring2_1.ports["o2"])
    c.add_port(name="Ring1C", port=ring1.ports["RingC"])
    c.add_port(name="Ring2C", port=ring2.ports["RingC"])
    # c.add_port(name="R2Input", port=ring2.ports["Input"])
    # c.add_port(name="R2Through", port=ring2.ports["Through"])

    if IsHeat:
        for port in ring1.ports:
            if "Heat" in port:
                c.add_port(name="R1" + port, port=ring1.ports[port])
        for port in ring2h.ports:
            if "Heat" in port:
                c.add_port(name="R2" + port, port=ring2h.ports[port])
    # add_labels_to_ports(c,label_layer=(412,8))
    return c


__all__ = ['DoubleRingPulley', 'DoubleRingPulley2HSn', 'ADRAPRADR', 'DoubleRingPulley2_1HSn',
           'CoupleRingDRT1']
