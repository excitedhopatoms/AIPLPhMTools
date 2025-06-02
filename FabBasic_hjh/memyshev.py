from .BasicDefine import *
from .CouplerMZI import *
from .Ring import *


# %% ExternalCavitySiN1:Proven design for SiN+Heater
def DoubleRingMemyshev(
        r_ring: float = 200,
        radius_delta: float = 4,
        width_ring: float = 1,
        width_single: float = 1,
        width_near: float = 0.91,
        width_heat: float = 5,
        delta_heat: float = 1,
        delta_ring: float = 20,
        angle_rc: float = 20,
        length_taper: float = 200,
        length_c2r: float = 230,
        length_ring2coup: float = -20,
        gap_rc: float = 0.3,

        gap_heat: float = 2,
        type_ringheater: str = "default",
        comp_coupler: Component = None,
        comp_reflecter: Component = None,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        trelayer: LayerSpec = LAYER.DT,
) -> Component:
    """
    创建一个双环 Memyshev 型谐振器结构。
    该结构通常由一个初始耦合器（默认为1x2 MMI）、两个带有独立环谐振器的臂、
    以及连接到每个环下载端口的反射器（默认为Sagnac环）组成。
    适用于需要复杂光谱滤波或特定色散特性的应用，如模式选择或脉冲整形。

    参数:
        r_ring (float): 环谐振器的基础半径 (µm)。
        radius_delta (float): 第二个环相对于第一个环的半径增加值 (µm)。用于失谐。
        width_ring (float): 环内波导的宽度 (µm)。
        width_single (float): 连接S弯和外部组件（耦合器、反射器）的单模波导宽度 (µm)。
        width_near (float): 环的耦合总线部分的波导宽度 (µm)。
        width_heat (float): 加热条的宽度 (µm)。
        delta_heat (float): 加热器的几何参数，传递给内部环加热器 (µm)。
        delta_ring (float): 两个环臂之间的垂直间隔，通过S弯实现 (µm)。
        angle_rc (float): 环耦合器（RingPulleyT1）的耦合角度 (度)。
        length_taper (float): 单模波导到耦合总线宽度的锥形渐变长度 (µm)。
        length_c2r (float): 从主耦合器输出到环谐振器输入耦合点之间的S弯的水平投影长度 (µm)。
        gap_rc (float): 环与总线之间的耦合间隙 (µm)。
        gap_heat (float): 波导与加热器之间的间隙 (µm)。
        type_ringheater (str): 环加热器的类型，传递给 `RingPulleyT1`。
        comp_coupler (ComponentSpec | None): 可选的自定义初始耦合器（如1x2分束器）。
                                           如果为 None，则使用默认的 `gf.c.mmi1x2_with_sbend`。
                                           应具有 "o1" (输入) 和 "o2", "o3" (两个输出) 端口。
        comp_reflecter (ComponentSpec | None): 可选的自定义反射器组件，连接到环的Drop端口。
                                             如果为 None，则使用默认的 `SagnacRing`。
                                             应具有 "o1" (输入) 和 "o2" (反射输出) 端口。
        oplayer (LayerSpec): 光学波导层。
        heatlayer (LayerSpec): 加热器层。
        trelayer (LayerSpec): 深槽刻蚀层 (此函数中未直接使用，但可能由子组件使用或为工艺兼容性保留)。

    返回:
        Component: 生成的双环Memyshev结构组件。

    端口:
        o1: 组件的总输入端口（来自初始耦合器的输入）。
        R1Through: 第一个环的直通端口。
        R2Through: 第二个环的直通端口。
        R1Add: 第一个环的增加端口。
        R2Add: 第二个环的增加端口。
        Reflect1Out: 第一个反射器的输出端口。
        Reflect2Out: 第二个反射器的输出端口。
        R1HeatIn, R1HeatOut: 第一个环加热器的电学端口 (如果RingPulleyT1生成它们)。
        R2HeatIn, R2HeatOut: 第二个环加热器的电学端口 (如果RingPulleyT1生成它们)。
    """
    c = gf.Component()
    # section and cross section
    S_near = gf.Section(width=width_near, offset=0, layer=oplayer, port_names=("o1", "o2"))
    S_single = gf.Section(width=width_single, offset=0, layer=oplayer, port_names=("o1", "o2"))
    X_near = gf.CrossSection(sections=[S_near])
    X_single = gf.CrossSection(sections=[S_single])
    if comp_coupler is None:
        coupler = c << gf.c.mmi1x2_with_sbend(cross_section=X_single, )
    else:
        coupler = c << comp_coupler
    if comp_reflecter is None:
        reflecter1 = c << SagnacRing(oplayer=oplayer, RadiusIn=r_ring, WidthIn=width_ring, WidthOut=width_near,
                                     GapCoup=gap_rc, AngleCouple=angle_rc, WidthSingle=width_single)
        reflecter2 = c << SagnacRing(oplayer=oplayer, RadiusIn=r_ring, WidthIn=width_ring, WidthOut=width_near,
                                     GapCoup=gap_rc, AngleCouple=angle_rc, WidthSingle=width_single)
    else:
        reflecter1 = c << comp_reflecter
        reflecter2 = c << comp_reflecter
    # ring ref1
    str1 = c << gf.c.bend_s(size=[length_c2r, delta_ring / 2], cross_section=X_single)
    taper1 = c << gf.c.taper(width1=width_single, width2=width_near, layer=oplayer, length=length_taper)
    taper1_2 = c << gf.c.taper(width2=width_single, width1=width_near, layer=oplayer, length=length_taper)
    ring1 = c << RingPulleyT1(
        WidthRing=width_ring, WidthNear=width_near, WidthHeat=width_heat,
        RadiusRing=r_ring, GapRing=gap_rc, GapHeat=gap_heat,
        AngleCouple=angle_rc, IsAD=True,
        oplayer=oplayer, heatlayer=heatlayer, IsHeat=True, TypeHeater=type_ringheater, DeltaHeat=delta_heat,
        DirectionHeater='down'
    )
    str1.connect('o1', coupler.ports["o2"])
    taper1.connect('o1', str1.ports["o2"])
    ring1.connect('Input', taper1.ports['o2'])
    taper1_2.connect('o1', ring1.ports['Drop'])
    reflecter1.connect('o1', taper1_2.ports['o2'], mirror=True)
    # ring ref1
    str2 = c << gf.c.bend_s(size=[length_c2r, -delta_ring / 2], cross_section=X_single)
    taper2 = c << gf.c.taper(width1=width_single, width2=width_near, layer=oplayer, length=length_taper)
    taper2_2 = c << gf.c.taper(width2=width_single, width1=width_near, layer=oplayer, length=length_taper)
    ring2 = c << RingPulleyT1(
        WidthRing=width_ring, WidthNear=width_near, WidthHeat=width_heat,
        RadiusRing=r_ring + radius_delta, GapRing=gap_rc, GapHeat=gap_heat,
        AngleCouple=angle_rc,
        oplayer=oplayer, heatlayer=heatlayer, IsHeat=True, TypeHeater=type_ringheater, DeltaHeat=delta_heat,
        DirectionHeater='down'
    )
    str2.connect('o1', coupler.ports["o3"])
    taper2.connect('o1', str2.ports["o2"])
    ring2.connect('Input', taper2.ports['o2'], mirror=True)
    taper2_2.connect('o1', ring2.ports['Drop'])
    reflecter2.connect('o1', taper2_2.ports['o2'])
    ## Add port
    c.add_port("o1", port=coupler.ports["o1"])
    c.add_port('R1Through', port=ring1.ports["Through"])
    c.add_port('R2Through', port=ring2.ports["Through"])
    c.add_port('R1Add', port=ring1.ports["Add"])
    c.add_port('R2Add', port=ring2.ports["Add"])
    c.add_port('Reflect1Out', port=reflecter1.ports["o2"])
    c.add_port('Reflect2Out', port=reflecter2.ports["o2"])
    for port in ring1.ports:
        if "Heat" in port:
            c.add_port("R1" + port, port=ring1.ports[port])
    for port in ring2.ports:
        if "Heat" in port:
            c.add_port("R2" + port, port=ring2.ports[port])
    add_labels_to_ports(c)
    return c


__all__ = ['DoubleRingMemyshev']
