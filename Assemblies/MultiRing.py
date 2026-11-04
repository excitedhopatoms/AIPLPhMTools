"""双/三环 Pulley 谐振腔与耦合环结构。
"""
from ..Core.BasicDefine import *
from ..Devices.RaceTrack import *
from ..Devices.Ring import *


# %% DoubleRingPulley
@gf.cell
def DoubleRingPulley(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        LengthR2R: float = 150,
        RadiusRing: float = 100,
        RadiusR2R: float = None,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        AngleCouple: float = 20,
        HeaterConfig: HeaterConfigClass = None,
        TypeR2R: str = "straight",
        DirectionsHeater: Sequence[str] = ("up", "up"),
        DirectionsRing: Sequence[str] = ("up", "up"),
        oplayer: LayerSpec = LAYER.WG,
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
        WidthRing=WidthRing, WidthNear=WidthNear,
        RadiusRing=RadiusRing, GapRing=GapRing,
        AngleCouple=AngleCouple,
        oplayer=oplayer, HeaterConfig=HeaterConfig,  DirectionHeater=DirectionsHeater[0]
    )
    ring2 = c << RingPulleyT1(
        WidthRing = WidthRing, WidthNear = WidthNear,
        RadiusRing = RadiusRing+DeltaRadius, GapRing = GapRing,
        AngleCouple = AngleCouple,
        oplayer = oplayer, HeaterConfig = HeaterConfig, DirectionHeater = DirectionsHeater[1]
    )
    if TypeR2R == "straight":
        str_R2R = c << GfCStraight(width=WidthNear, length=LengthR2R, layer=oplayer)
        str_R2R.connect("o1", ring1.ports["Drop"])
        ring2.connect("Drop", str_R2R.ports["o2"], allow_width_mismatch=True)
    elif TypeR2R == "bend":
        if RadiusR2R is None:
            RadiusR2R = RadiusRing - 10
        # str_R2R = c << GfCStraight(width=WidthNear, length=LengthR2R, layer=oplayer)
        # str_R2R.connect("o1", ring1.ports["Drop"])
        ring2.connect("Drop", ring1.ports["Drop"], allow_width_mismatch=True)
        ring2.movex(LengthR2R)
        # Add circular bends for ring-to-ring connection
        bendl1 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=90, layer=oplayer)
        bendr1 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=90, layer=oplayer)
        bendl2 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=-90, layer=oplayer)
        bendr2 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=-90, layer=oplayer)
        bendl1.connect("o1", ring1.ports["Drop"])
        bendl2.connect("o1", bendl1.ports["o2"])
        bendr1.connect("o2", ring2.ports["Drop"])
        bendr2.connect("o2", bendr1.ports["o1"])
        route = gf.routing.route_single(c, bendl2.ports["o2"], bendr2.ports["o1"], cross_section=make_cs(WidthNear, oplayer), radius=RadiusR2R)
        # c.add(route.references)
        # c.remove(str_R2R)

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


# %% DoubleRingPulley2：Snake Heater
@gf.cell
def DoubleRingPulley2HSn(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        LengthR2R: float = 150,
        RadiusRing: float = 100,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        AngleCouple: float = 20,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
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
        LengthR2R=LengthR2R,
        RadiusRing=RadiusRing,
        DeltaRadius=DeltaRadius,
        GapRing=GapRing,
        AngleCouple=AngleCouple,
        oplayer=oplayer,
        HeaterConfig=HeaterConfig,
    )
    # add_labels_to_ports(c)
    return c


# %% DoubleRingPulley2：Snake Heater & ring to ring round
@gf.cell
def DoubleRingPulley2_1HSn(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        LengthR2R: float = 700,
        RadiusRing: float = 100,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        AngleCouple: float = 20,
        oplayer: LayerSpec = LAYER.WG,
        HeaterConfig: HeaterConfigClass = None,
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
        LengthR2R=LengthR2R,
        RadiusRing=RadiusRing,
        DeltaRadius=DeltaRadius,
        GapRing=GapRing,
        AngleCouple=AngleCouple,
        oplayer=oplayer,
        TypeR2R="bend",
        HeaterConfig=HeaterConfig,
    )
    return c


# %% ADRAPRADR: ADRing + APRing + ADRing (with crossing ?)
@gf.cell(check_instances=False)
def ADRAPRADR(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
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
        IsSquare: bool = True,
        Name: str = "ADRAPRADR",
        oplayer: LayerSpec = LAYER.WG,
        CrossComp: Component = None,
        HeaterConfig: HeaterConfigClass = None,
) -> Component:
    """
    创建一个由三个环组成的谐振结构：两个 Add-Drop 环（ADR1/ADR2）和一个
    位于它们下方的全通环（APR, ring3）。

    新版布局（避免旧版环互相压住）：
    - ADR1/ADR2 横向排布，ADR2 用 Drop 对齐后向上镜像；
    - APR 放在两个 Drop 下方，用两条 45° Euler S 弯分别接 ADR1.Drop
      和 ADR2.Drop；
    - 两个 ADR 的 Input 之间放 CrossComp，左右各接一段，剩余两个端口
      作为 co2/co3。

    参数:
        WidthRing, WidthNear: 环/总线宽度 (µm)。
        WidthSingle: 保留参数；当前布局的 CrossComp 直接使用 WidthNear。
        LengthR2R: 两个 AD 环 Drop 间距的**最小值**；实际间距还会根据
            ring3 宽度自动放大，保证 S 弯能放下。
        LengthR2C, RadiusCrossBend: 保留参数（旧版方形布局使用），当前
            交叉波导居中放置，不再用它们生成穿过环的长直波导。
        RadiusRing: ADR1 半径；ADR2 = RadiusRing + DeltaRadius；
            ring3 = RadiusRing + DeltaRadius/2。
        AngleCouple, AngleCouple3: ADR / APR 的耦合角 (度)。
        IsSquare: True 时用 CrossComp 连接两个 ADR 的 Input；False 时
            直接暴露两个 Input 为 co2/co3。
        CrossComp: 2x2 交叉波导；端口宽度必须等于 WidthNear。

    返回:
        Component: 生成的 ADR-AP-ADR 结构组件。

    端口:
        co2, co3: 交叉波导的另外两个端口；没有 CrossComp 时为两个
            ADR 的 Input。
        r1Th, r1Ad: 第一个 AD 环的 Through/Add。
        r2Th, r2Ad: 第二个 AD 环的 Through/Add。
        r1L, r1R, r2L, r2R, r3L, r3R: 三个环的加热器端口。
    """
    TriRing = gf.Component()
    Ring3Radius = RadiusRing + DeltaRadius / 2
    route_radius = 50.0

    # 1) 两个 AD 环横向排布；ring2 用 Drop 对齐后向上镜像，和 TriRingPulley
    #    的干净排法一致。两个 Drop 之间的距离必须足够放中间的全通环及两条
    #    对角 S 弯，否则会像旧版一样把环压在别的环上。
    ring1 = TriRing << RingPulley(
        IsAD=True, WidthRing=WidthRing, RadiusRing=RadiusRing, oplayer=oplayer, GapRing=GapRing,
        WidthNear=WidthNear, AngleCouple=AngleCouple, HeaterConfig=HeaterConfig
    )
    spacing = max(float(LengthR2R), 2.0 * Ring3Radius + 300.0)
    place_r2 = TriRing << GfCStraight(width=WidthNear, length=spacing, layer=oplayer)
    place_r2.connect("o1", ring1.ports["Drop"])
    ring2 = TriRing << RingPulley(
        IsAD=True, WidthRing=WidthRing, RadiusRing=RadiusRing + DeltaRadius, oplayer=oplayer, GapRing=GapRing,
        WidthNear=WidthNear, AngleCouple=AngleCouple, HeaterConfig=HeaterConfig
    )
    ring2.connect("Drop", place_r2.ports["o2"], allow_width_mismatch=True)
    ring2.mirror_y(ring2.ports["Drop"].center[1])
    place_r2.delete()

    # 2) 全通环放在两个 Drop 下方。RingPulley(IsAD=False) 的 Input/Through
    #    是 0°/180°，可以直接用两条对角 Euler S 弯接回两个 Drop；旧版用
    #    RingPulley2 的 45° 端口硬接，导致环互相压住。
    ring3 = TriRing << RingPulley(
        IsAD=False, WidthRing=WidthRing, RadiusRing=Ring3Radius,
        oplayer=oplayer, GapRing=GapRing, WidthNear=WidthNear,
        AngleCouple=AngleCouple3, HeaterConfig=HeaterConfig,
    )
    ring1_bb, ring2_bb = ring1.dbbox(), ring2.dbbox()
    ring3_bb = ring3.dbbox()
    center_x = (ring1.ports["Drop"].center[0] + ring2.ports["Drop"].center[0]) / 2.0
    top_y = min(ring1_bb.bottom, ring2_bb.bottom) - 50.0
    ring3.move((center_x - (ring3_bb.left + ring3_bb.right) / 2.0, top_y - ring3_bb.top))

    def _check_route(route, p0, p1):
        for route_port, target in (("o1", p0), ("o2", p1)):
            rp = route.ports[route_port]
            if not np.allclose(rp.center, target.center, atol=1e-6):
                raise ValueError(
                    f"ADRAPRADR 路由端点不重合：{route_port} @ {rp.center} "
                    f"vs {target.name} @ {target.center}"
                )
            expected = (float(target.orientation) + 180.0) % 360.0
            if abs((float(rp.orientation) - expected + 180.0) % 360.0 - 180.0) > 1e-6:
                raise ValueError(
                    f"ADRAPRADR 路由端点朝向错误：{route_port}={rp.orientation}°，"
                    f"应为 {expected}°（与 {target.name} 相反）"
                )

    def _horizontal_s_route(p0, p1):
        """两条水平端口的 Euler S 弯；用 45° 斜段跨越 y 差。"""
        start = np.array(p0.center, dtype=float)
        end = np.array(p1.center, dtype=float)
        sign = 1.0 if abs((float(p0.orientation) % 360.0) - 0.0) < 1e-6 else -1.0
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        if sign * dx <= 0:
            raise ValueError(
                "ADRAPRADR: 环间端口方向与相对位置不一致，"
                f"p0={p0.name}@{p0.center} {p0.orientation}°, p1={p1.name}@{p1.center}"
            )
        lead = (abs(dx) - abs(dy)) / 2.0
        if lead < 0.65 * route_radius:
            raise ValueError(
                "ADRAPRADR: 两个 AD 环间距不足，无法放置中间全通环和 Euler S 弯；"
                f"lead={lead:.3f} um，至少需要 {0.65 * route_radius:.3f} um。"
            )
        pts = np.array([
            start,
            [start[0] + sign * lead, start[1]],
            [end[0] - sign * lead, end[1]],
            end,
        ])
        path = gf.path.smooth(pts, radius=route_radius, bend=gf.path.euler)
        route = gf.path.extrude(path, width=WidthNear, layer=oplayer)
        _check_route(route, p0, p1)
        return route

    TriRing << _horizontal_s_route(ring1.ports["Drop"], ring3.ports["Through"])
    TriRing << _horizontal_s_route(ring2.ports["Drop"], ring3.ports["Input"])

    # 3) 交叉波导放在两个 AD 环 Input 之间，左右各接一段，剩下两个端口
    #    作为外腔的 co2/co3。这里不再使用 route_single 在同一点重复布线。
    if IsSquare and CrossComp:
        crossing = TriRing << CrossComp
        cross_width = float(crossing.ports["o3"].width)
        if abs(cross_width - WidthNear) > 1e-9:
            raise ValueError(
                "ADRAPRADR: CrossComp 的端口宽度必须等于 WidthNear，"
                f"当前 {cross_width} vs {WidthNear} um；请先加 taper 或修改 CrossComp。"
            )
        left_len = (ring2.ports["Input"].center[0] - ring1.ports["Input"].center[0]) / 2.0
        # o3 在 crossing 中心的左侧，直波导长度要把这段偏置加回来，
        # 保证 crossing 中心落在两个 Input 的中点。
        left_len += crossing.ports["o3"].center[0] - crossing.center[0]
        left = TriRing << GfCStraight(width=WidthNear, length=left_len, layer=oplayer)
        left.connect("o1", ring1.ports["Input"])
        crossing.connect("o3", left.ports["o2"])

        start = np.array(crossing.ports["o1"].center, dtype=float)
        end = np.array(ring2.ports["Input"].center, dtype=float)
        lead = 50.0
        pts = np.array([
            start,
            [start[0] + lead, start[1]],
            [end[0] - lead, end[1]],
            end,
        ])
        path = gf.path.smooth(pts, radius=route_radius, bend=gf.path.euler)
        right_route = gf.path.extrude(path, width=WidthNear, layer=oplayer)
        _check_route(right_route, crossing.ports["o1"], ring2.ports["Input"])
        TriRing << right_route
        TriRing.add_port(name="co2", port=crossing.ports["o2"])
        TriRing.add_port(name="co3", port=crossing.ports["o4"])
    else:
        # 没有交叉波导时，至少把两个 AD 环 Input 暴露出来，避免端口悬空。
        TriRing.add_port(name="co2", port=ring1.ports["Input"])
        TriRing.add_port(name="co3", port=ring2.ports["Input"])

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

@gf.cell
def TriRingPulley(
        WidthRing: float = 1,
        WidthNear: float = 0.9,
        LengthR2R: float = 300,
        RadiusRing: float = 100,
        RadiusR2R: float = None,
        DeltaRadius: float = 1,
        GapRing: float = 1,
        AngleCouple: float = 20,
        TypeR2R: str = "straight",
        DirectionsHeater: Sequence[str] = ("up", "up"),
        DirectionsRing: Sequence[str] = ("up", "up"),
        oplayer: LayerSpec = LAYER.WG,
        RadiusRing3:float=100,
        GapRing3:float=1,
        WidthNear3:float=1 ,
        WidthRing3:float=1,
        AngleCouple3:float=15,
        HeaterConfig:HeaterConfigClass=None,
) -> Component:
    """
    2025/07/23
    创建一个三环滑轮型（Pulley）谐振器组件。
    该组件由两个 `RingPulleyT1` 单元串联而成，第二个环的半径可以与第一个不同。
    第三个环耦合在两个环之间，是all-pass类型
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
        WidthRing=WidthRing, WidthNear=WidthNear,
        RadiusRing=RadiusRing, GapRing=GapRing,
        AngleCouple=AngleCouple,
        oplayer=oplayer,HeaterConfig=HeaterConfig, DirectionHeater=DirectionsHeater[0]
    )
    ring2 = c << RingPulleyT1(
        WidthRing=WidthRing, WidthNear=WidthNear,
        RadiusRing=RadiusRing + DeltaRadius, GapRing=GapRing,HeaterConfig=HeaterConfig,
        AngleCouple=AngleCouple,
        oplayer=oplayer, DirectionHeater=DirectionsHeater[1]
    )
    if TypeR2R == "straight":
        str_R2R = c << GfCStraight(width=WidthNear, length=LengthR2R, layer=oplayer)
        str_R2R.connect("o1", ring1.ports["Drop"])
        ring2.connect("Drop", str_R2R.ports["o2"], allow_width_mismatch=True)
    elif TypeR2R == "bend":
        if RadiusR2R is None:
            RadiusR2R = RadiusRing - 10
        # str_R2R = c << GfCStraight(width=WidthNear, length=LengthR2R, layer=oplayer)
        # str_R2R.connect("o1", ring1.ports["Drop"])
        ring2.connect("Drop", ring1.ports["Drop"], allow_width_mismatch=True)
        ring2.movex(LengthR2R)
        # Add circular bends for ring-to-ring connection
        bendl1 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=90, layer=oplayer)
        bendr1 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=90, layer=oplayer)
        bendl2 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=-90, layer=oplayer)
        bendr2 = c << gf.c.bend_euler(width=WidthNear, radius=RadiusR2R, angle=-90, layer=oplayer)
        bendl1.connect("o1", ring1.ports["Drop"])
        bendl2.connect("o1", bendl1.ports["o2"])
        bendr1.connect("o2", ring2.ports["Drop"])
        bendr2.connect("o2", bendr1.ports["o1"])

        ring3= c << RingPulleyT1(IsAD=False,RadiusRing=RadiusRing3,WidthRing=WidthRing3,WidthNear=WidthNear3,DirectionHeater="down",AngleCouple=AngleCouple3,GapRing=GapRing3)
        #ring3.mirror_y(ring3.center[1])
        ring3.connect("Through",bendl2.ports["o2"],allow_width_mismatch=True)

        delta=bendr2.ports["o1"].center[0]-ring3.ports["Input"].center[0]
        con= c << GfCStraight(width=WidthNear,length=max(delta,0))
        con.connect("o1", ring3["Input"], allow_width_mismatch=True)

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

# %% CoupleCavity
@gf.cell(check_instances=False)
def CoupleRingDRT1(
        WidthRing1: float = 1,
        WidthNear1: float = 0.9,
        RadiusRing1: float = 100,
        GapRB1: float = 2,
        AngleCouple1: float = 20,
        WidthRing2: float = None,
        WidthNear2: float = None,
        LengthNear2: float = 110,
        RadiusRing2: float = None,
        GapRB2: float = 3,
        AngleR12: float = 30,
        GapRR: float = 1,
        TypeR2R: str = "strsight",
        DirectionsHeater: Sequence[str] = ("up", "down"),
        HeaterConfigRing1: HeaterConfigClass = None,
        HeaterConfigRing2: HeaterConfigClass = None,
        IsAD: bool = False,
        oplayer: LayerSpec = LAYER.WG,
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
    if RadiusRing2 is None:
        RadiusRing2 = RadiusRing1
    if WidthNear2 is None:
        WidthNear2 = WidthNear1
    c = gf.Component()
    ring1 = c << RingPulleyT1(
        WidthRing=WidthRing1, WidthNear=WidthNear1,
        RadiusRing=RadiusRing1, GapRing=GapRB1,
        AngleCouple=AngleCouple1, IsAD=False,
        oplayer=oplayer,HeaterConfig=HeaterConfigRing1,
        DirectionHeater=DirectionsHeater[0]
    )
    ring2_c = gf.Component()
    ring2_c << gf.c.ring(width=WidthRing2, radius=RadiusRing2, layer=oplayer)
    ring2_c.add_port("RingC", center=[0, 0], layer=oplayer, width=1)
    ring2 = c << ring2_c
    ring2.move(ring1.ports['RingC'].center)
    ring2.move((0, -(RadiusRing1 + RadiusRing2 + WidthRing1 / 2 + WidthRing2 / 2 + GapRR)))
    ring2.rotate(AngleR12, ring1.ports['RingC'].center)
    if IsAD:
        str_ring2_1 = c << GfCStraight(width=WidthNear2, length=LengthNear2 / 2, layer=oplayer)
        str_ring2_1.move(ring2.ports["RingC"].center)
        str_ring2_1.move((0, -WidthRing2 / 2 - WidthNear2 / 2 - RadiusRing2 - GapRB2))
        str_ring2_2 = c << GfCStraight(width=WidthNear2, length=LengthNear2 / 2, layer=oplayer)
        str_ring2_2.connect('o2', str_ring2_1.ports['o1'])
        c.add_port(name="Add", port=str_ring2_2.ports["o1"])
        c.add_port(name="Drop", port=str_ring2_1.ports["o2"])
    ring2_hc = RingPulleyT1(
        WidthRing=WidthRing2, WidthNear=WidthNear2,
        RadiusRing=RadiusRing2, GapRing=GapRB2,
        AngleCouple=AngleCouple1, IsAD=False,
        oplayer=oplayer, HeaterConfig=HeaterConfigRing2,
        DirectionHeater=DirectionsHeater[1]
    )

    if HeaterConfigRing2 is not None:
        ring2h = c << GetFromLayer(ring2_hc, OLayer=HeaterConfigRing2.LayerHeat)
        ring2h.move(np.array(ring2.ports["RingC"].center) - np.array(ring2h.ports["RingC"].center))

    # c.add_port(name="R1Add", port=ring1.ports["Add"])
    # c.add_port(name="R1Drop", port=ring1.ports["Drop"])
    c.add_port(name="Input", port=ring1.ports["Input"])
    c.add_port(name="Through", port=ring1.ports["Through"])
    c.add_port(name="Ring1C", port=ring1.ports["RingC"])
    c.add_port(name="Ring2C", port=ring2.ports["RingC"])
    # c.add_port(name="R2Input", port=ring2.ports["Input"])
    # c.add_port(name="R2Through", port=ring2.ports["Through"])

    for port in ring1.ports:
        if "Heat" in port.name:
            c.add_port(name="Ring1" + port.name, port=port)
            c.add_port(name="R1" + port.name, port=port)
    if HeaterConfigRing2 is not None:
        for port in ring2h.ports:
            if "Heat" in port.name:
                c.add_port(name="Ring2" + port.name, port=port)
                c.add_port(name="R2" + port.name, port=port)
    # add_labels_to_ports(c,label_layer=(412,8))
    return c


__all__ = ['DoubleRingPulley', 'DoubleRingPulley2HSn', 'ADRAPRADR', 'DoubleRingPulley2_1HSn',
           'CoupleRingDRT1','TriRingPulley']
