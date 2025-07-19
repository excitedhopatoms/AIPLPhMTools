from .BasicDefine import *
from .CouplerMZI import *
from .Heater import *
from .MultiRing import *
from .MultiRaceTrack import *

# %% ExternalCavity:Proven design
@gf.cell
def ExternalCavitySOI(
        r_ring: float = 200,
        radius_delta: float = 4,
        width_ring: float = 1,
        width_single: float = 1,
        width_single2: float = 1,
        width_near: float = 0.91,
        width_heat: float = 5,
        width_route: float = 20,
        width_cld: float = 3,
        angle_rc: float = 20,
        length_dc: float = 7,
        length_t_s2n: float = 200,
        length_taper: float = 200,
        length_r2r: float = 1000,
        length_bridge: float = 300,
        length_input: float = 330,
        gap_rc: float = 0.3,
        gap_dc: float = 0.5,
        gap_heat: float = 2,
        oplayer: LayerSpec = LAYER.WG,
        routelayer: LayerSpec = LAYER.M1,
        openlayer: LayerSpec = open,
        heatlayer: LayerSpec = LAYER.M1,
        slablayer: LayerSpec = (1, 0),
        swglayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    创建一个SOI（Silicon-On-Insulator）平台的外腔激光器（External Cavity Laser）核心光学组件。
    该设计包含一个DMZI（马赫-曾德干涉仪）作为模式选择单元，以及一个双环滑轮型谐振器（DoubleRingPulley）
    作为精细调谐和窄线宽单元。组件还集成了加热器用于调谐。

    参数:
        r_ring (float): 环谐振器的基础半径 (µm)。
        radius_delta (float): 双环之间的小半径差，用于失谐 (µm)。
        width_ring (float): 环谐振器波导宽度 (µm)。
        width_single (float): 输入/输出及MZI内部的单模波导宽度 (µm)。
        width_single2 (float): 从环输出到外部的单模波导宽度 (µm)。
        width_near (float): 环与总线耦合区域的总线波导宽度 (µm)。
        width_heat (float): 加热条宽度 (µm)。
        width_route (float): 加热器引出金属线的宽度 (µm)。
        width_cld (float): 波导到slab区域边缘的包层宽度，用于定义slab区域 (µm)。
        angle_rc (float): 环形耦合器的耦合角度 (度)。
        length_dc (float): DMZI中定向耦合器的耦合长度 (µm)。
        length_t_s2n (float): 从单模波导到环耦合总线波导的锥形过渡长度 (µm)。
        length_taper (float): 通用锥形波导长度 (µm)。
        length_r2r (float): 双环谐振器中两个环之间的连接长度 (µm)。
        length_bridge (float): DMZI臂的桥接（平行臂）长度 (µm)。
        length_input (float): 输入端口波导的额外延伸长度 (µm)。
        gap_rc (float): 环与总线之间的耦合间隙 (µm)。
        gap_dc (float): DMZI中定向耦合器的平行波导间隙 (µm)。
        gap_heat (float): 光波导与加热器之间的间隙 (µm)。
        oplayer (LayerSpec): 光学波导层。
        routelayer (LayerSpec): 加热器布线层。
        openlayer (LayerSpec): 焊盘开口层。
        heatlayer (LayerSpec): 加热器金属层。
        slablayer (LayerSpec): Slab层（例如浅刻蚀层）。
        swglayer (LayerSpec): 用于加热器下方的亚波长光栅或其他辅助结构层。

    返回:
        Component: 生成的外腔激光器核心组件。

    端口:
        input: 组件的光学输入端口。
        output: 组件的光学输出端口。
        Rout0, Rout1, Rout2, Rout3: 从双环谐振器引出的额外端口（可能用于监控或特定配置）。
        (以及多个加热器相关的电学端口，未在文档中一一列出，但会根据加热器设计自动生成)
    """
    ec_ref = gf.Component()
    offsetVC = ViaArray(Spacing=0.7, WidthVia=0.3, Row=15, Col=8, IsEn=True, Enclosure=0.5, ViaLayer=(0, 1),
                        ViaEnLayers=[heatlayer, swglayer])
    deltaVCY = offsetVC.ports["up"].center[1] - offsetVC.ports["down"].center[1]
    deltaVCX = -offsetVC.ports["left"].center[0] + offsetVC.ports["right"].center[0]
    # section and cross section
    S_near = gf.Section(width=width_near, offset=0, layer=oplayer, port_names=("o1", "o2"))
    S_heater1 = gf.Section(width=width_heat, offset=gap_heat + width_heat / 2 + width_near / 2, layer=heatlayer)
    S_heater2 = gf.Section(width=width_heat, offset=-(gap_heat + width_heat / 2 + width_near / 2), layer=heatlayer)
    S_swg = gf.Section(width=2 * width_heat + 2 * gap_heat + width_near, offset=0, layer=swglayer,
                       port_names=("o1", "o2"))
    S_Rup = gf.Section(width=width_route, offset=2 * deltaVCY + gap_heat + width_near / 2 - width_route / 2,
                       layer=routelayer)
    S_Rdown = gf.Section(width=width_route, offset=-(2 * deltaVCY + gap_heat + width_near / 2 - width_route / 2),
                         layer=routelayer)
    BusHeatRouteComp = gf.Component("BHRC")
    BHRC0 = BusHeatRouteComp << GfCStraight(width=deltaVCX, length=deltaVCY * 3 + width_near + 2 * gap_heat,
                                            layer=routelayer)
    BHRC0.rotate(-90)
    CAP_viaup = gf.cross_section.ComponentAlongPath(component=offsetVC, spacing=50,
                                                    offset=gap_heat + width_near / 2 + deltaVCY, padding=0)
    CAP_viadown = gf.cross_section.ComponentAlongPath(component=offsetVC, spacing=50, offset=-gap_heat - width_near / 2)
    CAP_Routeup = gf.cross_section.ComponentAlongPath(component=BusHeatRouteComp, spacing=100,
                                                      offset=-width_near / 2 - gap_heat - deltaVCY)
    CAP_Routedown = gf.cross_section.ComponentAlongPath(component=BusHeatRouteComp, spacing=100, padding=50,
                                                        offset=width_near / 2 + gap_heat - (
                                                                    deltaVCY * 2 + width_near + 2 * gap_heat))
    CS_near = gf.CrossSection(sections=[S_near])
    CS_heat = gf.CrossSection(sections=[S_heater1, S_heater2, S_swg], components_along_path=[CAP_viaup, CAP_viadown])
    CS_Route = gf.CrossSection(sections=[S_Rup, S_Rdown], components_along_path=[CAP_Routeup, CAP_Routedown])
    # taper near to single
    tsn = gf.Component()
    tsn = gf.c.taper(width1=width_near, width2=width_single, length=length_t_s2n, layer=oplayer)
    # ring ref
    coupler_ref = DMZI(LengthCoup=length_dc, GapCoup=gap_dc, layer=oplayer, WidthSingle=width_single,
                       LengthBridge=length_bridge)
    coupler2x2 = ec_ref << coupler_ref
    tapercoupler1 = ec_ref << gf.c.taper(width1=width_single, width2=width_near, length=length_t_s2n + 40,
                                         layer=oplayer)
    tapercoupler2 = ec_ref << gf.c.taper(width1=width_single, width2=width_near, length=length_t_s2n, layer=oplayer)
    tapercoupler1.connect("o1", other=coupler2x2.ports["Output1"])
    tapercoupler2.connect("o1", other=coupler2x2.ports["Output2"])
    bend_c2r = ec_ref << GfCBendEuler(width=width_near, angle=180, layer=oplayer, radius=r_euler_false * 1.7,
                                      with_arc_floorplan=False, p=0.5)
    bend_c2r.connect("o1", tapercoupler2.ports["o2"], mirror=True)
    # str_c2r = ec_ref << GfCStraight(width = width_near, layer = oplayer)
    # bend_c2r2 =
    ring_ref = DoubleRingPulley(
        WidthRing=width_ring, WidthNear=width_near, WidthEnd=0.2,
        LengthTaper=150, LengthR2R=length_r2r, DeltaRadius=radius_delta,
        RadiusRing=r_ring, RadiusBend0=40, GapRing=gap_rc,
        AngleCouple=angle_rc,
        oplayer=oplayer, heatlayer=heatlayer,
        Pitch=5, EndPort=[]
    )
    doublering = ec_ref << ring_ref[0]
    doublering.connect("o1", bend_c2r.ports["o2"])
    doublering.movex(-length_r2r + r_ring * 3)  # .movey(-r_ring)
    c2rRoute1 = gf.routing.route_single_sbend(ec_ref,
                                              tapercoupler1.ports["o2"], doublering.ports["o2"], cross_section=CS_near)
    # ec_ref.add(c2rRoute1.references)
    c2rRoute2 = gf.routing.route_single(ec_ref,
                                        bend_c2r.ports["o2"], doublering.ports["o1"], cross_section=CS_near)
    # ec_ref.add(c2rRoute2.references)
    # ring to out
    bend_ringout = ec_ref << GfCBendEuler(width=width_near, angle=180, layer=oplayer, radius=r_euler_false,
                                          with_arc_floorplan=False)
    bend_ringout.connect("o1", doublering.ports["RingPort0"])
    bend_ringout1 = ec_ref << GfCBendEuler(width=width_near, angle=180, layer=oplayer, radius=r_euler_false * 3.5,
                                           with_arc_floorplan=False)
    bend_ringout1.connect("o1", doublering.ports["RingPort1"])
    taper_r2o_0 = ec_ref << gf.c.taper(width1=width_near, width2=width_single2, layer=oplayer, length=length_taper)
    taper_r2o_0.connect("o1", bend_ringout.ports["o2"])
    taper_r2o_2 = ec_ref << gf.c.taper(width1=width_near, width2=width_single2, layer=oplayer, length=length_taper)
    taper_r2o_2.connect("o1", doublering.ports["RingPort2"])

    taper_r2o_1 = ec_ref << gf.c.taper(width1=width_near, width2=width_single2, layer=oplayer, length=length_taper)
    taper_r2o_1.connect("o1", bend_ringout1.ports["o2"])
    taper_r2o_3 = ec_ref << gf.c.taper(width1=width_near, width2=width_single2, layer=oplayer, length=length_taper)
    taper_r2o_3.connect("o1", doublering.ports["RingPort3"])
    ec_ref.add_port("Rout2", port=taper_r2o_2.ports["o2"], orientation=180)
    ec_ref.add_port("Rout0", port=taper_r2o_0.ports["o2"], orientation=180)
    ec_ref.add_port("Rout1", port=taper_r2o_1.ports["o2"], orientation=180)
    ec_ref.add_port("Rout3", port=taper_r2o_3.ports["o2"], orientation=180)
    ## input
    str_input = list(range(30))
    bend_input = list(range(30))
    bend_input[0] = ec_ref << GfCBendEuler(width=width_single, angle=-225, layer=oplayer, radius=r_euler_false,
                                           with_arc_floorplan=False)
    bend_input[0].connect("o2", coupler2x2.ports["Input2"])
    bend_input[1] = ec_ref << GfCBendEuler(width=width_single, angle=45, layer=oplayer, radius=r_euler_false,
                                           with_arc_floorplan=False)
    bend_input[1].connect("o2", bend_input[0].ports["o1"])
    str_input[0] = ec_ref << GfCStraight(width=width_single, length=length_bridge * 3 - 100 + length_taper,
                                         layer=oplayer)
    str_input[0].connect("o2", bend_input[1].ports["o1"])
    bend_input[2] = ec_ref << GfCBendEuler(width=width_single, angle=180, layer=oplayer, radius=r_euler_false,
                                           with_arc_floorplan=False)
    bend_input[2].connect("o2", str_input[0].ports["o1"])
    str_input[1] = ec_ref << GfCStraight(width=width_single,
                                         length=length_input - 100 + length_taper + length_bridge * 2, layer=oplayer)
    str_input[1].connect("o2", bend_input[2].ports["o1"])
    ec_ref.add_port("input", port=str_input[1].ports["o1"])
    ## output
    str_output = list(range(30))
    bend_output = list(range(30))
    bend_output[0] = ec_ref << GfCBendEuler(width=width_single, angle=200, layer=oplayer, radius=r_euler_false,
                                            with_arc_floorplan=False)
    bend_output[0].connect("o2", coupler2x2.ports["Input1"])
    bend_output[1] = ec_ref << GfCBendEuler(width=width_single, angle=-20, layer=oplayer, radius=r_euler_false,
                                            with_arc_floorplan=False)
    bend_output[1].connect("o2", bend_output[0].ports["o1"])
    delta = tapercoupler1.ports["o2"].center - bend_output[1].ports["o1"].center
    str_output[0] = ec_ref << gf.c.taper(width1=width_single, width2=width_single2, length=length_taper, layer=oplayer)
    str_output[0].connect("o2", bend_output[1].ports["o1"])
    ec_ref.add_port("output", port=str_output[0].ports["o1"], orientation=180)
    # heater
    # Ring Heater

    # bus heater
    BusHeater = gf.Component(name="BusHeater")
    BusHeater_path = gf.path.straight(length=length_r2r - 300)
    BusHeater_wg = BusHeater << gf.path.extrude(BusHeater_path, cross_section=CS_heat)
    BusHeater_route = BusHeater << gf.path.extrude(BusHeater_path, cross_section=CS_Route)
    BusHeater.add_port("o1", port=BusHeater_wg.ports["o1"])
    heat_cld0 = gf.geometry.offset(BusHeater_wg, distance=width_cld + 0.8)
    heat_cld1 = gf.geometry.offset(heat_cld0, distance=-0.8, layer=slablayer)
    BusHeater.add_ref(heat_cld1)
    BusHeater_ref = ec_ref << BusHeater
    BusHeater_ref.connect("o1", other=doublering.ports["r2ro1"]).movex(150)
    BusHeater_ref.mirror_x(BusHeater_ref.ports["o1"].center[0])
    # mzi heater component
    MZIHeater = gf.Component(name="MZIHeater")
    MZI_path = gf.path.straight(length=length_bridge - 100)
    MZIHeater_wg = MZIHeater << gf.path.extrude(MZI_path, cross_section=CS_heat)
    MZIHeater_route = MZIHeater << gf.path.extrude(MZI_path, cross_section=CS_Route)
    MZIHeater_cld0 = gf.geometry.offset(MZIHeater_wg, distance=width_cld + 0.8)
    MZIHeater_cld1 = gf.geometry.offset(MZIHeater_cld0, distance=-0.8, layer=slablayer)
    MZIHeater.add_ref(MZIHeater_cld1)
    MZIHeater.add_port("o1", port=MZIHeater_wg.ports["o1"], orientation=0)
    ## MZIheatup and down
    MZIHeaterup = ec_ref << MZIHeater
    MZIHeaterup.connect("o1", other=coupler2x2.ports["Bridge1"])
    MZIHeaterup.movex(-100)
    MZIHeaterdown = ec_ref << MZIHeater
    MZIHeaterdown.connect("o1", other=coupler2x2.ports["Bridge2"])
    MZIHeaterdown.movex(100)
    return ec_ref


# %% ExternalCavitySiN1:Proven design for SiN+Heater
def ExternalCavitySiN(
        r_ring: float = 200,
        r_euler_false: float = 100,
        r_mzi: float = 100,
        r_r2r: float = None,
        radius_delta: float = 4,
        width_ring: float = 1,
        width_mzi_ring: float = 2,
        width_single: float = 1,
        width_near: float = 0.91,
        width_mzi_near: float = 1.2,
        width_heat: float = 5,
        delta_heat: float = 1,
        angle_rc: float = 20,
        angle_pmzi: float = 20,
        angle_m2r: float = 45,
        length_bend: float = 50,
        length_t_s2n: float = 200,
        length_taper: float = 200,
        length_r2r: float = 550,
        length_bridge: float = 300,
        length_input: float = 230,
        length_cr2: float = 20,
        length_cr1: float = 1,
        gap_rc: float = 0.3,
        gap_mzi: float = 0.5,
        gap_heat: float = 2,
        gap_heat2: float = 75,
        type_ringheater: str = "default",
        type_mziheater: str = "default",
        type_busheater: str = "default",
        type_r2r: str = "straight",
        direction_io: str = "LR",
        direction_rh: str = "down",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
) -> Component:
    """
    为氮化硅（SiN）平台设计的外腔激光器核心组件。
    此设计集成了一个PMZI（基于Pulley耦合器的MZI）和带有加热器的双环谐振器。
    组件参数允许对各个部分进行详细配置。

    参数:
        (各项参数含义请参考上面各子组件或类似组件的文档)
        r_ring, r_euler_false, r_mzi, r_r2r, radius_delta: 半径相关参数 (µm)。
        width_ring, width_mzi_ring, width_single, width_near, width_mzi_near, width_heat: 宽度相关参数 (µm)。
        delta_heat: 加热器几何参数 (µm)。
        angle_rc, angle_pmzi, angle_m2r: 角度相关参数 (度)。
        length_bend, length_t_s2n, length_taper, length_r2r, length_bridge, length_input, length_cr2, length_cr1: 长度相关参数 (µm)。
        gap_rc, gap_mzi, gap_heat, gap_heat2: 间隙相关参数 (µm)。
        type_ringheater, type_mziheater, type_busheater: 不同部分加热器的类型。
        type_r2r: 双环连接方式。
        direction_io: 组件整体输入输出方向。
        direction_rh: 环加热器的相对位置。
        oplayer, heatlayer, trelayer: GDS图层定义。

    返回:
        Component: 生成的SiN外腔激光器核心组件。

    端口:
        o1, o2: 组件的主光学输入和输出端口。
        Ro1, Ro2, Ro3, Ro4: 从双环引出的附加光学端口。
        Ring1HeatIn, Ring1HeatOut, Ring2HeatIn, Ring2HeatOut: 双环加热器的电学端口。
        PMZIHeatLIn, PMZIHeatLOut, PMZIHeatRIn, PMZIHeatROut: PMZI加热器的电学端口。
        BusHeatLIn, BusHeatLOut, BusHeatRIn, BusHeatROut: 输入总线加热器的电学端口。
        (实际端口名称可能因内部加热器组件的具体实现而略有不同)
    """
    ec_ref = gf.Component()
    # section and cross section
    S_near = gf.Section(width=width_near, offset=0, layer=oplayer, port_names=("o1", "o2"))
    CS_near = gf.CrossSection(sections=(S_near,))
    S_NM = gf.Section(width=width_mzi_near, layer=oplayer, port_names=("o1", "o2"))
    S_N = gf.Section(width=width_near, layer=oplayer, port_names=("o1", "o2"))
    X_NM = gf.CrossSection(sections=(S_NM,))
    X_N = gf.CrossSection(sections=(S_N,))
    # ring ref
    coupler2x2 = ec_ref << PMZI(WidthNear=width_mzi_near, WidthRing=width_mzi_ring, Radius=r_mzi,
                                AngleCouple=angle_pmzi, LengthTaper=length_taper, LengthBend=length_bend,
                                LengthBridge=length_bridge,
                                GapCoup=gap_mzi, IsHeat=True,
                                oplayer=oplayer, heatlayer=heatlayer,
                                WidthHeat=width_heat, GapHeat=gap_heat2, TypeHeater=type_mziheater, DeltaHeat=delta_heat
                                )
    # coupler2x2.mirror_y()
    bend_cr1_1 = ec_ref << GfCBendEuler(radius=r_euler_false, angle=-angle_m2r, cross_section=X_NM)
    bend_cr1_2 = ec_ref << GfCBendEuler(radius=r_euler_false, angle=angle_m2r, cross_section=X_N)
    str_cr1_1 = ec_ref << GfCStraight(width=width_mzi_near, length=length_cr1, layer=oplayer)
    str_cr1_1.connect("o1", other=coupler2x2.ports["Output1"])
    bend_cr1_1.connect("o1", other=str_cr1_1.ports["o2"])
    tapercoupler1 = ec_ref << gf.c.taper(width1=width_mzi_near, width2=width_near,
                                         length=min(length_t_s2n, 500 * abs(width_mzi_near - width_near) + 1),
                                         layer=oplayer)
    tapercoupler1.connect("o1", other=bend_cr1_1.ports["o2"])
    tapercoupler2 = ec_ref << gf.c.taper(width1=width_mzi_ring, width2=width_near,
                                         length=min(length_t_s2n, 500 * abs(width_mzi_ring - width_near) + 1),
                                         layer=oplayer)
    bend_c2r_path = euler_Bend_Half(angle=-90, radius=r_mzi)
    bend_c2r = ec_ref << gf.path.extrude(bend_c2r_path, width=width_mzi_ring, layer=oplayer)
    bend_c2r.connect("o1", coupler2x2.ports["Output2"])
    tapercoupler2.connect("o1", bend_c2r.ports["o2"])
    ring_ref = DoubleRingPulley(
        WidthRing=width_ring, WidthNear=width_near, WidthHeat=width_heat,
        LengthR2R=length_r2r, DeltaRadius=-radius_delta,
        RadiusRing=r_ring + radius_delta, GapRing=gap_rc, GapHeat=gap_heat, RadiusR2R=r_r2r,
        AngleCouple=angle_rc,
        oplayer=oplayer, heatlayer=heatlayer, IsHeat=True, TypeHeater=type_ringheater, DeltaHeat=delta_heat,
        TypeR2R=type_r2r,DirectionsHeater=[direction_rh,direction_rh]
    )
    doublering = ec_ref << ring_ref
    doublering.connect("o1", tapercoupler2.ports["o2"])
    doublering.movex(length_cr2)
    str_cr2_1 = ec_ref << GfCStraight(width=width_near, length=length_cr2, layer=oplayer)
    str_cr2_1.connect("o1", tapercoupler2.ports["o2"])
    delta1 = np.array(bend_cr1_1.ports["o1"].center) - np.array(bend_cr1_1.ports["o2"].center)
    delta2 = np.array(tapercoupler1.ports["o2"].center) - np.array(doublering.ports["o2"].center)
    addlength = abs(delta1[1] - delta2[1]) / np.sin(angle_m2r * np.pi / 180)
    str_tapercoupler = ec_ref << GfCStraight(width=width_near, length=addlength, layer=oplayer)
    str_tapercoupler.connect("o1", other=tapercoupler1.ports["o2"])
    bend_cr1_2.connect("o1", other=str_tapercoupler.ports["o2"])
    str_cr1_2 = ec_ref << GfCStraight(width=width_near, layer=oplayer,
                                      length=-doublering.ports["o2"].center[0] + bend_cr1_2.ports["o2"].center[0])
    str_cr1_2.connect("o1", bend_cr1_2.ports["o2"])
    ## left
    str_input = list(range(30))
    bend_input = list(range(30))
    str_input[0] = ec_ref << gf.c.taper(width1=width_mzi_near, width2=width_single, length=min(length_taper,abs(width_near-width_single)*500,50), layer=oplayer)
    str_input[0].connect("o1", coupler2x2.ports["Input2"], mirror=True)
    ## right
    str_output = list(range(30))
    bend_output = list(range(30))
    path_bend_output = euler_Bend_Half(angle=-90, radius=r_mzi)
    bend_output[0] = ec_ref << gf.path.extrude(path_bend_output, layer=oplayer, width=width_mzi_ring)
    bend_output[0].connect("o1", coupler2x2.ports["Input1"])
    str_output[0] = ec_ref << gf.c.taper(width1=width_mzi_ring, width2=width_single, length=min(length_taper,abs(width_near-width_single)*500,50), layer=oplayer)
    str_output[0].connect("o1", bend_output[0].ports["o2"])
    # input heater
    str_input[1] = ec_ref << GfCStraight(width=width_single, length=length_input, layer=oplayer)
    path_input = gf.path.straight(length=length_input)
    inputh = ec_ref << DifferentHeater(PathHeat=path_input, WidthHeat=width_heat, WidthWG=width_single,
                                       DeltaHeat=delta_heat, GapHeat=gap_heat2 * length_input / length_bridge,
                                       WidthRoute=20,
                                       heatlayer=heatlayer, TypeHeater=type_busheater)
    if direction_io == "LR":
        str_input[1].connect("o1", str_input[0].ports["o2"])
        ec_ref.add_port("o1", port=str_input[1].ports["o2"])
        ec_ref.add_port("o2", port=str_output[0].ports["o2"])
    elif direction_io == "RL":
        str_input[1].connect("o1", str_output[0].ports["o2"])
        ec_ref.add_port("o1", port=str_input[0].ports["o2"])
        ec_ref.add_port("o2", port=str_input[1].ports["o2"])
    if (type_busheater != "None") and (type_busheater != "none"):
        inputh.connect("HeatIn", ec_ref.ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True,
                       allow_type_mismatch=True)
        inputh.mirror_x(inputh.ports["HeatIn"].center[0])
    # add drop
    ## optics

    ec_ref.add_port("Ro1", port=doublering.ports["R1Through"])
    ec_ref.add_port("Ro2", port=doublering.ports["R1Add"])
    ec_ref.add_port("Ro3", port=doublering.ports["R2Through"])
    ec_ref.add_port("Ro4", port=doublering.ports["R2Add"])
    ## heat and optics
    for port in doublering.ports:
        if "Heat" in port.name:
            ec_ref.add_port("Ring" + port.name, port=doublering.ports[port.name])
    for port in coupler2x2.ports:
        if "Heat" in port.name:
            ec_ref.add_port("PMZI" + port.name, port=coupler2x2.ports[port.name])
    for port in inputh.ports:
        if "Heat" in port.name:
            ec_ref.add_port("Bus" + port.name, port=inputh.ports[port.name])
    # print(ec_ref.ports)
    ## heat
    # test2 = gf.Component()
    # test2 << ec_ref
    # test2 << ec_ref
    # test2.show()
    ec_ref = remove_layer(ec_ref, layer=(512, 8))
    add_labels_to_ports(ec_ref)
    return ec_ref


# %% ExternalCavity1SiNH:Proven design for SiN+Heater
def ExternalCavitySiNH2(
        r_ring: float = 200,
        r_euler_false: float = 100,
        r_mzi: float = 100,
        radius_delta: float = 4,
        width_ring: float = 1,
        width_single: float = 1,
        width_near: float = 0.91,
        width_mzi_near: float = 1.2,
        width_heat: float = 5,
        angle_rc: float = 20,
        angle_pmzi: float = 20,
        angle_m2r: float = 45,
        length_bend: float = 50,
        length_t_s2n: float = 200,
        length_taper: float = 200,
        length_r2r: float = 1550,
        length_bridge: float = 300,
        length_input: float = 230,
        length_rc1: float = 20,
        length_rc2: float = 20,
        length_busheater: float = 300,
        gap_rc: float = 0.3,
        gap_mzi: float = 0.5,
        gap_heat: float = 2,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        trelayer: LayerSpec = LAYER.DT,
) -> Component:
    """
    `ExternalCavitySiN` 的一个特定配置版本。
    主要区别在于 `width_mzi_ring` 被设置为等于 `width_near` (环耦合总线宽度)，
    以及 `length_input` 参数被用于 `ExternalCavitySiN` 内部的 `length_busheater`。

    参数:
        (大部分参数与 ExternalCavitySiN 相同)
        length_r2r (float): 双环间连接长度，默认为 1550.0 µm。
        length_busheater (float): 明确的总线加热器段长度，默认为 300.0 µm。
                                (原 `length_input` 的角色由此参数替代)。
        length_rc1, length_rc2: 连接MZI和环的短直波导长度。

    返回:
        Component: 生成的特定配置的外腔激光器核心组件。
    """
    return ExternalCavitySiN(
        r_ring=r_ring,
        r_euler_false=r_euler_false,
        r_mzi=r_mzi,
        radius_delta=radius_delta,
        width_ring=width_ring,
        width_single=width_single,
        width_near=width_near,
        width_mzi_ring=width_near,
        width_mzi_near=width_mzi_near,
        width_heat=width_heat,
        angle_rc=angle_rc,
        angle_pmzi=angle_pmzi,
        angle_m2r=angle_m2r,
        length_bend=length_bend,
        length_t_s2n=length_t_s2n,
        length_taper=length_taper,
        length_r2r=length_r2r,
        length_bridge=length_bridge,
        length_input=length_busheater,
        length_cr1=length_rc1,
        length_cr2=length_rc2,
        gap_mzi=gap_mzi,
        gap_heat=gap_heat,
        gap_rc=gap_rc,
        oplayer=oplayer,
        heatlayer=heatlayer,
        trelayer=trelayer,
    )


# %% ExternalCavity1SiNH:Proven design for SiN+Heater
# Ring to ring is bend
def ExternalCavitySiNH2_1(
        r_ring: float = 200,
        r_euler_false: float = 100,
        r_mzi: float = 100,
        radius_delta: float = 4,
        width_ring: float = 1,
        width_single: float = 1,
        width_near: float = 0.91,
        width_mzi_near: float = 1.2,
        width_heat: float = 5,
        angle_rc: float = 20,
        angle_pmzi: float = 20,
        angle_m2r: float = 45,
        length_bend: float = 50,
        length_t_s2n: float = 200,
        length_taper: float = 200,
        length_r2r: float = 550,
        length_bridge: float = 300,
        length_input: float = 230,
        length_ring2coup: float = -20,
        length_busheater: float = 300,
        gap_rc: float = 0.3,
        gap_mzi: float = 0.5,
        gap_heat: float = 2,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
) -> Component:
    """
    `ExternalCavitySiN` 的又一个特定配置版本，此版本在其原始代码中
    明确调用了 `PMZIHSn` (带蛇形加热器的PMZI) 和 `DoubleRingPulley2_1HSn` (可能是特定版本的双环)。
    这里的实现将基于这些假设，并尽量保持与 `ExternalCavitySiN` 结构的一致性，
    同时反映这些特定组件的调用。

    参数:
        (大部分参数与 ExternalCavitySiN/SiNH2 相同)
        length_ring2coup (float): 双环单元相对于其输入连接点的额外X轴偏移，默认为 -20.0 µm。
        length_busheater (float): 总线加热器段长度，默认为 300.0 µm。
        (其他参数如 delta_heat, gap_heat2, type_ringheater, direction_rh 用于配置内部的加热组件)

    返回:
        Component: 生成的特定配置的外腔激光器核心组件。

    注意:
        此函数依赖于 `PMZIHSn` 和 `DoubleRingPulley2_1HSn` 组件的可用性。
        如果这些组件未定义或行为不同，此处的实现可能需要调整。
    """
    ec_ref = gf.Component("ec_ref")
    ec_ref = gf.Component()
    # section and cross section
    S_near = gf.Section(width=width_near, offset=0, layer=oplayer, port_names=("o1", "o2"))
    CS_near = gf.CrossSection(sections=[S_near])
    # ring ref
    coupler_ref = PMZIHSn(WidthNear=width_mzi_near, WidthRing=width_near, Radius=r_mzi,
                          AngleCouple=angle_pmzi, LengthTaper=length_taper, LengthBend=400, LengthBridge=length_bridge,
                          GapCoup=gap_mzi, oplayer=oplayer,
                          heatlayer=heatlayer, WidthHeat=width_heat, GapHeat=gap_heat
                          )
    coupler2x2 = ec_ref << coupler_ref[0]
    coupler2x2.mirror_y()
    bend_cr1_1 = ec_ref << GfCBendEuler(radius=r_euler_false, angle=-angle_m2r, width=width_mzi_near, layer=oplayer,
                                        with_arc_floorplan=False)
    bend_cr1_2 = ec_ref << GfCBendEuler(radius=r_euler_false, angle=angle_m2r, width=width_near, layer=oplayer,
                                        with_arc_floorplan=False)
    bend_cr1_1.connect("o1", other=coupler2x2.ports["Output1"])
    tapercoupler1 = ec_ref << gf.c.taper(width1=width_mzi_near, width2=width_near, length=length_t_s2n, layer=oplayer)
    tapercoupler1.connect("o1", other=bend_cr1_1.ports["o2"])
    bend_c2r_path = euler_Bend_Half(angle=-90, radius=r_mzi)
    bend_c2r = ec_ref << gf.path.extrude(bend_c2r_path, width=width_near, layer=oplayer)
    bend_c2r.connect("o1", coupler2x2.ports["Output2"])
    ring_ref = DoubleRingPulley2_1HSn(
        WidthRing=width_ring, WidthNear=width_near, WidthHeat=width_heat,
        LengthR2R=length_r2r, DeltaRadius=-radius_delta,
        RadiusRing=r_ring + radius_delta, GapRing=gap_rc, GapHeat=gap_heat,
        AngleCouple=angle_rc,
        oplayer=oplayer, heatlayer=heatlayer, IsHeat=True,
    )
    doublering = ec_ref << ring_ref[0]
    doublering.connect("o1", bend_c2r.ports["o2"])
    doublering.movex(length_ring2coup)
    delta1 = np.array(bend_cr1_1.ports["o1"].center) - np.array(bend_cr1_1.ports["o2"].center)
    delta2 = np.array(tapercoupler1.ports["o2"].center) - np.array(doublering.ports["o2"].center)
    addlength = abs(delta1[1] - delta2[1]) / np.sin(angle_m2r * np.pi / 180)
    str_tapercoupler = ec_ref << GfCStraight(width=width_near, length=addlength, layer=oplayer)
    str_tapercoupler.connect("o1", other=tapercoupler1.ports["o2"])
    bend_cr1_2.connect("o1", other=str_tapercoupler.ports["o2"])
    c2rRoute1 = gf.routing.route_single(ec_ref, bend_cr1_2.ports["o2"], doublering.ports["o2"], cross_section=CS_near)
    # ec_ref.add(c2rRoute1.references)
    c2rRoute2 = gf.routing.route_single(ec_ref, bend_c2r.ports["o2"], doublering.ports["o1"], cross_section=CS_near)
    # ec_ref.add(c2rRoute2.references)
    ## input
    str_input = list(range(30))
    bend_input = list(range(30))
    str_input[0] = ec_ref << gf.c.taper(width1=width_single, width2=width_mzi_near, length=length_taper, layer=oplayer)
    str_input[0].connect("o2", coupler2x2.ports["Input2"])
    path_input = gf.path.straight(length=length_busheater)
    str_input[1] = ec_ref << gf.path.extrude(path_input, width=width_single, layer=oplayer)
    str_input[2] = ec_ref << GfCStraight(width=width_single, length=length_input, layer=oplayer)
    str_input[1].connect("o2", str_input[0].ports["o1"])
    str_input[2].connect("o2", str_input[1].ports["o1"])
    ## output
    str_output = list(range(30))
    bend_output = list(range(30))
    path_bend_output = euler_Bend_Half(angle=90, radius=r_mzi)
    bend_output[0] = ec_ref << gf.path.extrude(path_bend_output, layer=oplayer, width=width_near)
    bend_output[0].connect("o1", coupler2x2.ports["Input1"], mirror=True)
    str_output[0] = ec_ref << gf.c.taper(width1=width_near, width2=width_single, length=length_taper, layer=oplayer)
    str_output[0].connect("o1", bend_output[0].ports["o2"])

    # heater
    Hring = ec_ref << ring_ref[1]
    Hring.connect("1HeatIn", other=doublering.ports["1HeatIn"])
    Hring.rotate(180, center=Hring.ports["1HeatIn"].center)
    pmzih = ec_ref << coupler_ref[1]
    pmzih.mirror_y().connect("HeatLout", other=coupler2x2.ports["HeatLout"],
                             allow_width_mismatch=True, allow_layer_mismatch=True, allow_type_mismatch=True)
    inputh = ec_ref << SnakeHeater(
        heatlayer=heatlayer, WidthHeat=width_heat, WidthWG=width_mzi_near, GapHeat=gap_heat, PathHeat=path_input)
    inputh.connect("o2", str_input[0].ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True,
                   allow_type_mismatch=True)
    # add drop
    ## optics
    ec_ref.add_port("Input", port=str_input[1].ports["o1"])
    ec_ref.add_port("Output", port=str_output[0].ports["o2"])
    ec_ref.add_port("Ro1", port=doublering.ports["R1Through"])
    ec_ref.add_port("Ro2", port=doublering.ports["R1Add"])
    ec_ref.add_port("Ro3", port=doublering.ports["R2Input"])
    ec_ref.add_port("Ro4", port=doublering.ports["R2Drop"])
    ## heat and optics
    ec_ref.add_port("Ring1HeatIn", port=doublering.ports["1HeatIn"])
    ec_ref.add_port("PMZIHeatLout", port=coupler2x2.ports["HeatLout"])
    # print(pmzih.ports)
    for port in pmzih.ports:
        ec_ref.add_port("PMZI" + port.name, port=pmzih.ports[port.name])
    for port in Hring.ports:
        ec_ref.add_port("Ring" + port.name, port=Hring.ports[port.name])
    for port in inputh.ports:
        ec_ref.add_port("Input" + port.name, port=inputh.ports[port.name])
    # print(ec_ref.ports)
    ## heat
    # test2 = gf.Component()
    # test2 << ec_ref
    # test2 << ec_ref
    # test2.show()
    return ec_ref


# %% ExternalCavity2: tri ring ecl
@gf.cell
def ExternalCavity2(
        r_ring: float = 200,
        radius_delta: float = 4,
        width_single: float = 1,
        width_ring: float = 1,
        width_near: float = 0.91,
        width_heat: float = 5,
        width_route: float = 20,
        width_cld: float = 3,
        angle_rc: float = 20,
        angle_rc3: float = 40,
        length_taper: float = 200,
        length_r2r: float = 50,
        gap_rc: float = 0.3,
        gap_dc: float = 0.5,
        gap_heat: float = 2,
        oplayer: LayerSpec = LAYER.WG,
        routelayer: LayerSpec = LAYER.M1,
        heatlayer: LayerSpec = LAYER.M1,
        swglayer: LayerSpec = LAYER.WG,
        Crossing: Component = None,
        Name="ec2_ref"
) -> Component:
    """
    创建一种外腔激光器设计，其核心是一个三环谐振结构（通过ADRAPRADR组件实现），
    并通过交叉波导进行输入和输出。

    参数:
        r_ring (float): 三环结构中环的基础半径 (µm)。
        radius_delta (float): 三环结构中环之间的半径差 (µm)。
        width_single (float): 输入/输出波导以及连接交叉波导的波导宽度 (µm)。
        width_ring (float): 三环结构中各个环的波导宽度 (µm)。
        width_near (float): 三环结构中用于耦合的总线波导宽度 (µm)。
        angle_rc (float): 三环结构中主环的耦合角度 (度)。
        angle_rc3 (float): 三环结构中特定耦合部分的角度 (度)。
        length_taper (float): 锥形波导的长度 (µm)。
        length_r2r (float): ADRAPRADR组件内部环间连接的长度 (µm)。
        gap_rc (float): ADRAPRADR组件内部环耦合的间隙 (µm)。
        oplayer (LayerSpec): 光学波导层。
        Crossing (ComponentSpec | None): 用户提供的交叉波导组件。如果为None，则使用默认的Crossing_taper。
        Name (str): 生成组件的名称。

    返回:
        Component: 生成的基于三环和交叉的外腔组件。

    端口:
        input: 组件的光学输入端口。
        output: 组件的光学输出端口。
        to1, to2: 从三环结构引出的端口。
        r1Th, r1Ad, r2Th, r2Ad: 从三环结构的特定环引出的Through和Add端口（经过taper和bend）。
        r1L, r1R, r2L, r2R, r3L, r3R: 三环结构内部加热器（如果存在于ADRAPRADR中）的端口。
        co2, co3: 三环结构连接到交叉波导之前的端口。
    """
    ec2_ref = gf.Component(Name)
    if Crossing == None:
        crossing0 = Crossing_taper(WidthCross=0.8, WidthWg=width_single, LengthTaper=5, oplayer=oplayer)
    else:
        crossing0 = Crossing
    TriRing = ec2_ref << ADRAPRADR(WidthRing=width_ring, WidthNear=width_near, WidthSingle=width_single,
                                   RadiusRing=r_ring, DeltaRadius=radius_delta, LengthTaper=length_taper,
                                   LengthR2R=length_r2r,
                                   AngleCouple=angle_rc, AngleCouple3=angle_rc3, GapRing=gap_rc, CrossComp=crossing0,
                                   LengthR2C=500
                                   )
    # ring port taper & bend
    taperbend = gf.Component("taperbend")
    taper_n2s = taperbend << gf.c.taper(width1=width_near, width2=width_single, layer=oplayer, length=length_taper / 2)
    bend_n2s = taperbend << GfCBendEuler(width=width_single, layer=oplayer, radius=120, angle=45)
    bend_n2s.connect("o1", taper_n2s.ports["o2"])
    taperbend.add_port("o1", port=taper_n2s.ports["o1"])
    taperbend.add_port("o2", port=bend_n2s.ports["o2"])
    taper_n2s_1 = ec2_ref << taperbend
    taper_n2s_1.connect("o1", TriRing.ports["r1Th"]).mirror_y(taper_n2s_1.ports["o1"].center[1])
    taper_n2s_2 = ec2_ref << taperbend
    taper_n2s_2.connect("o1", TriRing.ports["r1Ad"]).mirror_y(taper_n2s_2.ports["o1"].center[1])
    taper_n2s_3 = ec2_ref << taperbend
    taper_n2s_3.connect("o1", TriRing.ports["r2Th"])
    taper_n2s_4 = ec2_ref << taperbend
    taper_n2s_4.connect("o1", TriRing.ports["r2Ad"])
    # crossing bend
    bend45 = GfCBendEuler(width=width_single, radius=120, angle=45, layer=oplayer)
    bend45_o2 = ec2_ref << bend45
    bend45_o2.connect("o1", TriRing.ports["co2"])
    bend45_o3 = ec2_ref << bend45
    bend45_o3.connect("o1", TriRing.ports["co3"], mirror=True)
    ec2_ref.add_port("input", port=bend45_o2.ports["o2"])
    ec2_ref.add_port("output", port=bend45_o3.ports["o2"])
    # Heater
    offsetVC = ViaArray(Spacing=0.7, WidthVia=0.3, Row=15, Col=8, IsEn=True, Enclosure=0.5, ViaLayer=LAYER.CT,
                        ViaEnLayers=[LAYER.CTE, heatlayer, swglayer])
    deltaVCY = offsetVC.ports["up"].center[1] - offsetVC.ports["down"].center[1]
    deltaVCX = -offsetVC.ports["left"].center[0] + offsetVC.ports["right"].center[0]
    ec2_ref.add_port("to1", port=TriRing.ports["to1"])
    ec2_ref.add_port("to2", port=TriRing.ports["to2"])
    ec2_ref.add_port("r1Th", port=taper_n2s_1.ports["o2"])
    ec2_ref.add_port("r1Ad", port=taper_n2s_2.ports["o2"])
    ec2_ref.add_port("r2Th", port=taper_n2s_3.ports["o2"])
    ec2_ref.add_port("r2Ad", port=taper_n2s_4.ports["o2"])
    ec2_ref.add_port("r1L", port=TriRing.ports["r1L"])
    ec2_ref.add_port("r1R", port=TriRing.ports["r1R"])
    ec2_ref.add_port("r2L", port=TriRing.ports["r2L"])
    ec2_ref.add_port("r2R", port=TriRing.ports["r2R"])
    ec2_ref.add_port("r3L", port=TriRing.ports["r3L"])
    ec2_ref.add_port("r3R", port=TriRing.ports["r3R"])
    ec2_ref.add_port("co2", port=TriRing.ports["co2"])
    ec2_ref.add_port("co3", port=TriRing.ports["co3"])
    ec2_ref = remove_layer(ec2_ref, layer=(512, 8))
    add_labels_to_ports(ec2_ref)
    return ec2_ref


# %% ExternalCavity3: risky design2
@gf.cell
def ExternalCavity3(
        r_ring: float = 200,
        radius_delta: float = 4,
        width_single: float = 1,
        width_ring: float = 1,
        width_near: float = 0.91,
        width_heat: float = 5,
        width_route: float = 20,
        width_cld: float = 3,
        angle_rc: float = 20,
        angle_rc3: float = 40,
        length_taper: float = 200,
        length_r2r: float = 300,
        length_r2c: float = 1,
        gap_rc: float = 0.3,
        gap_heat: float = 2,
        oplayer: LayerSpec = LAYER.WG,
        routelayer: LayerSpec = LAYER.M2,
        heatlayer: LayerSpec = LAYER.M1,
        Crossing: Component = None,
        Name="ec2_ref"
) -> Component:
    """
    创建另一种基于三环谐振结构（ADRAPRADR）和交叉波导的外腔激光器设计。
    与 ExternalCavity2 的主要区别可能在于 ADRAPRADR 的参数配置 (如 IsSquare=True)
    以及输出端口的处理方式 (直接从交叉引出并taper)。

    参数:
        (大部分参数与 ExternalCavity2 类似)
        width_near (float): 同时用作三环耦合总线宽度和提供给默认Crossing_taper的臂宽。
        length_r2c (float): ADRAPRADR内部环到交叉的连接长度，默认为1.0 µm。
        Crossing (ComponentSpec | None): 自定义交叉波导。如果None，默认Crossing_taper的臂宽为width_near。

    返回:
        Component: 生成的特定配置的外腔组件。

    端口:
        co2, co3: 从交叉波导引出的光学端口 (经过taper)。
        r1L, r1R, r2L, r2R, r3L, r3R: ADRAPRADR内部加热器（如果存在）的端口。
    """
    ec3_ref = gf.Component(Name)
    if Crossing == None:
        crossing0 = Crossing_taper(WidthCross=2, WidthWg=width_near, LengthTaper=10, oplayer=oplayer)
    else:
        crossing0 = Crossing
    TriRing = ec3_ref << ADRAPRADR(WidthRing=width_ring, WidthNear=width_near, WidthSingle=width_single, IsSquare=True,
                                   IsHeat=True,
                                   RadiusRing=r_ring, RadiusCrossBend=80, DeltaRadius=radius_delta,
                                   LengthTaper=length_taper, LengthR2R=length_r2r, LengthR2C=length_r2c,
                                   AngleCouple=angle_rc, AngleCouple3=angle_rc3, GapRing=gap_rc, CrossComp=crossing0,
                                   oplayer=oplayer, heatlayer=heatlayer, WidthHeat=width_heat
                                   )
    # ring port taper & bend
    taperbend = gf.Component("taperbend")
    taper_n2s = taperbend << gf.c.taper(width1=width_near, width2=width_single, layer=oplayer, length=length_taper / 2)
    bend_n2s = taperbend << GfCBendEuler(width=width_single, layer=oplayer, radius=120, angle=45)
    bend_n2s.connect("o1", taper_n2s.ports["o2"])
    taperbend.add_port("o1", port=taper_n2s.ports["o1"])
    taperbend.add_port("o2", port=bend_n2s.ports["o2"])
    # crossing taper
    taper_cross = gf.c.taper(width1=width_near, width2=width_single, length=length_taper, layer=oplayer)
    taper_cross_1 = ec3_ref << taper_cross
    taper_cross_2 = ec3_ref << taper_cross
    taper_cross_1.connect("o1", other=TriRing.ports["co2"])
    taper_cross_2.connect("o1", other=TriRing.ports["co3"])
    # Heater
    # ec3_ref.add_port("to1",port=TriRing.ports["to1"])
    # ec3_ref.add_port("to2", port=TriRing.ports["to2"])
    # ec3_ref.add_port("r1Th",port=taper_n2s_1.ports["o2"])
    # ec3_ref.add_port("r1Ad", port=taper_n2s_2.ports["o2"])
    # ec3_ref.add_port("r2Th", port=taper_n2s_3.ports["o2"])
    # ec3_ref.add_port("r2Ad", port=taper_n2s_4.ports["o2"])
    ec3_ref.add_port("r1L", port=TriRing.ports["r1L"])
    ec3_ref.add_port("r1R", port=TriRing.ports["r1R"])
    ec3_ref.add_port("r2L", port=TriRing.ports["r2L"])
    ec3_ref.add_port("r2R", port=TriRing.ports["r2R"])
    ec3_ref.add_port("r3L", port=TriRing.ports["r3L"])
    ec3_ref.add_port("r3R", port=TriRing.ports["r3R"])
    ec3_ref.add_port("co2", port=taper_cross_1.ports["o2"])
    ec3_ref.add_port("co3", port=taper_cross_2.ports["o2"])
    ec3_ref = remove_layer(ec3_ref,layer=(512, 8))
    add_labels_to_ports(ec3_ref)
    return ec3_ref

def ExternalCavityRaceTrack(
        r_ring: float = 200,
        r_euler_false: float = 100,
        r_mzi: float = 100,
        r_r2r: float = None,
        width_ring: float = 1,
        width_mzi_ring: float = 2,
        width_single: float = 1,
        width_near: float = 0.91,
        width_mzi_near: float = 1.2,
        width_mzi: float = 1,
        width_heat: float = 5,
        delta_heat: float = 1,
        angle_rc: float = 20,
        angle_pmzi: float = 20,
        angle_m2r: float = 90,
        length_bend: float = 50,
        length_racetrack: float = 100,
        lengthrs_delta:float = 20,
        length_t_s2n: float = 200,
        length_taper: float = 200,
        length_r2r: float = 550,
        length_bridge: float = 300,
        length_input: float = 230,
        length_cr2: float = 20,
        length_cr1: float = 1,
        length_cmzi: float = 10,
        length_cring:float = 10,
        gap_rc: float = 0.3,
        gap_mzi: float = 0.5,
        gap_heat: float = 2,
        gap_heat2: float = 75,
        type_ringheater: str = "default",
        type_mziheater: str = "default",
        type_busheater: str = "default",
        type_rscoupler: str = "s",
        type_r2r: str = "straight",
        type_mzi: str = "DMZI",
        direction_io: str = "LR",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        trelayer: LayerSpec = LAYER.DT,
) -> Component:
    """
    创建一个基于跑道形（RaceTrack）谐振器的外腔激光器核心组件。
    该设计集成了可选类型的MZI（DMZI或PMZI）和双跑道环谐振器，并支持各部分加热调谐。

    参数:
        (各项参数含义复杂，具体参考内部子组件和设计意图)
        r_ring: 跑道环的弯曲半径 (µm)。
        width_ring, width_near, ... : 各种波导宽度 (µm)。
        length_racetrack, length_bridge, ... : 各种直线段长度 (µm)。
        angle_rc, angle_pmzi, ... : 角度参数 (度)。
        gap_rc, gap_mzi, ... : 间隙参数 (µm)。
        type_...heater: 各部分加热器类型。
        type_rscoupler: 跑道环的耦合方式 ('s'代表直线耦合, 'p'代表滑轮式/角度耦合)。
        type_r2r: 双跑道环的连接方式。
        type_mzi: MZI的类型。
        direction_io: 组件整体输入输出方向。
        oplayer, heatlayer, trelayer: GDS图层。

    返回:
        Component: 生成的基于跑道环的外腔激光器组件。

    端口:
        o1, o2: 主光学输入/输出。
        Ro1, Ro2, Ro3, Ro4: 从双跑道环引出的附加端口。
        (以及各加热器对应的电学端口)
    """
    ec_ref = gf.Component()
    if type_rscoupler =="s" or type_rscoupler == "S":
        width_near=width_ring
        bendout = 90
        if type_mzi == "DMZI":
            width_mzi_ring = width_mzi
            width_mzi_near = width_mzi
            bendout = 180
    elif type_rscoupler =="p" or type_rscoupler == "P":
        bendout = 0
        if type_mzi == "DMZI":
            width_mzi_ring = width_mzi
            width_mzi_near = width_mzi
            bendout = 90
    # section and cross section
    S_near = gf.Section(width=width_near, offset=0, layer=oplayer, port_names=("o1", "o2"))
    CS_near = gf.CrossSection(sections=(S_near,))
    S_NM = gf.Section(width=width_mzi_near, layer=oplayer, port_names=("o1", "o2"))
    S_N = gf.Section(width=width_near, layer=oplayer, port_names=("o1", "o2"))
    X_NM = gf.CrossSection(sections=(S_NM,))
    X_N = gf.CrossSection(sections=(S_N,))
    # ring ref
    if type_mzi == "DMZI":
        coupler2x2 = ec_ref << DMZI(WidthWG=width_mzi_ring, Radius=r_mzi,
                                    LengthCoup=length_cmzi, LengthBend=length_bend,
                                    LengthBridge=length_bridge,
                                    GapCoup=gap_mzi, IsHeat=True,
                                    oplayer=oplayer, heatlayer=heatlayer,
                                    WidthHeat=width_heat, GapHeat=gap_heat2, TypeHeater=type_mziheater, DeltaHeat=delta_heat
                                    )
        bend_c2r_path = gf.path.euler(angle=-bendout, radius=r_mzi)
    else:
        coupler2x2 = ec_ref << PMZI(WidthNear=width_mzi_near, WidthRing=width_mzi_ring, Radius=r_mzi,
                                    AngleCouple=angle_pmzi, LengthTaper=length_taper, LengthBend=length_bend,
                                    LengthBridge=length_bridge,
                                    GapCoup=gap_mzi, IsHeat=True,
                                    oplayer=oplayer, heatlayer=heatlayer,
                                    WidthHeat=width_heat, GapHeat=gap_heat2, TypeHeater=type_mziheater,
                                    DeltaHeat=delta_heat
                                    )
        bend_c2r_path = euler_Bend_Half(angle=-bendout, radius=r_mzi)
    coupler2x2.mirror_y()

    str_cr1_1 = ec_ref << GfCStraight(width=width_mzi_near, length=length_cr1, layer=oplayer)
    str_cr1_1.connect("o1", other=coupler2x2.ports["Output1"])
    tapercoupler1 = ec_ref << gf.c.taper(width1=width_mzi_near, width2=width_near,
                                         length=min(length_t_s2n, 300 * abs(width_mzi_near - width_near) + 1),
                                         layer=oplayer)
    tapercoupler2 = ec_ref << gf.c.taper(width1=width_mzi_ring, width2=width_near,
                                         length=min(length_t_s2n, 300 * abs(width_mzi_ring - width_near) + 1),
                                         layer=oplayer)
    bend_c2r = ec_ref << gf.path.extrude(bend_c2r_path, width=width_mzi_ring, layer=oplayer)
    bend_c2r.connect("o1", coupler2x2.ports["Output2"])
    tapercoupler2.connect("o1", bend_c2r.ports["o2"])
    ring_ref = DoubleRaceTrack(
        WidthRing=width_ring, WidthNear=width_near, WidthHeat=width_heat,
        LengthR2R=length_r2r, DeltaLengthRS=-lengthrs_delta,LengthRun = length_racetrack,
        RadiusRing=r_ring, GapCouple=gap_rc, GapHeat=gap_heat, RadiusR2R=r_r2r,
        AngleCouple=angle_rc,LengthCouple = length_cring,
        oplayer=oplayer, heatlayer=heatlayer, IsHeat=True, TypeHeater=type_ringheater, DeltaHeat=delta_heat,
        TypeR2R=type_r2r,TypeCouple=type_rscoupler
    )
    doublering = ec_ref << ring_ref
    if type_rscoupler=="s" or type_rscoupler=="S":
        doublering.connect("o1", tapercoupler2.ports["o2"], allow_width_mismatch=True,mirror=True)
    else:
        doublering.connect("o1", tapercoupler2.ports["o2"],allow_width_mismatch=True)
    if tapercoupler2.ports["o2"].orientation == 180:
        doublering.movex(-length_cr2)
    else:
        doublering.movey(-length_cr2)
    str_cr2_1 = ec_ref << GfCStraight(width=width_near, length=length_cr2, layer=oplayer)
    str_cr2_1.connect("o1", tapercoupler2.ports["o2"])
    if type_rscoupler == 's' or type_rscoupler == 'S':
        bend_cr1_1 = ec_ref << GfCBendEuler(radius=r_euler_false, angle=-angle_m2r, cross_section=X_NM)
        bend_cr1_1.connect("o1", other=str_cr1_1.ports["o2"])
        tapercoupler1.connect("o1", other=bend_cr1_1.ports["o2"])
        bend_cr1_2 = ec_ref << GfCBendEuler(radius=r_euler_false, angle=angle_m2r, cross_section=X_N)
        delta1 = np.array(bend_cr1_1.ports["o1"].center) - np.array(bend_cr1_1.ports["o2"].center)
        delta2 = np.array(tapercoupler1.ports["o2"].center) - np.array(doublering.ports["o2"].center)
        addlength = abs(delta1[1] - delta2[1]) / np.sin(angle_m2r * np.pi / 180)
        str_tapercoupler = ec_ref << GfCStraight(width=width_near, length=addlength, layer=oplayer)
        str_tapercoupler.connect("o1", other=tapercoupler1.ports["o2"])
        bend_cr1_2.connect("o1", other=str_tapercoupler.ports["o2"])
        str_cr1_2 = ec_ref << GfCStraight(width=width_near, layer=oplayer,
                                          length=abs(-doublering.ports["o2"].center[0] + bend_cr1_2.ports["o2"].center[0]))
        str_cr1_2.connect("o1", bend_cr1_2.ports["o2"])
    else:
        bend_cr1_1 = ec_ref << GfCBendEuler(radius=r_euler_false, angle=-angle_m2r, cross_section=X_NM)
        bend_cr1_1.connect("o1", other=str_cr1_1.ports["o2"],mirror=True)
        tapercoupler1.connect("o1", other=bend_cr1_1.ports["o2"])
        size = np.array(doublering.ports["o2"].center)-np.array(tapercoupler1.ports["o2"].center)
        bend_cr1_2 = ec_ref << gf.c.bend_s(size=(-size[1],size[0]), cross_section=X_N)
        bend_cr1_2.connect("o1", other=tapercoupler1.ports["o2"])
    ## left
    str_input = list(range(30))
    bend_input = list(range(30))
    str_input[0] = ec_ref << gf.c.taper(width1=width_mzi_near, width2=width_single, length=length_taper, layer=oplayer)
    str_input[0].connect("o1", coupler2x2.ports["Input1"], mirror=True)
    ## right
    str_output = list(range(30))
    bend_output = list(range(30))
    path_bend_output = euler_Bend_Half(angle=90, radius=r_mzi)
    bend_output[0] = ec_ref << gf.path.extrude(path_bend_output, layer=oplayer, width=width_mzi_ring)
    bend_output[0].connect("o1", coupler2x2.ports["Input2"])
    str_output[0] = ec_ref << gf.c.taper(width1=width_mzi_ring, width2=width_single, length=length_taper, layer=oplayer)
    str_output[0].connect("o1", bend_output[0].ports["o2"])
    # input heater
    str_input[1] = ec_ref << GfCStraight(width=width_single, length=length_input, layer=oplayer)
    path_input = gf.path.straight(length=length_input)
    inputh = ec_ref << DifferentHeater(PathHeat=path_input, WidthHeat=width_heat, WidthWG=width_single,
                                       DeltaHeat=delta_heat, GapHeat=gap_heat2 * length_input / length_bridge,
                                       WidthRoute=20,
                                       heatlayer=heatlayer, TypeHeater=type_busheater)
    if direction_io == "LR":
        str_input[1].connect("o2", str_input[0].ports["o2"])
        ec_ref.add_port("o1", port=str_input[1].ports["o1"])
        ec_ref.add_port("o2", port=str_output[0].ports["o2"])
    elif direction_io == "RL":
        str_input[1].connect("o1", str_output[0].ports["o2"])
        ec_ref.add_port("o1", port=str_input[0].ports["o2"])
        ec_ref.add_port("o2", port=str_input[1].ports["o2"])
    if (type_busheater != "None") and (type_busheater != "none"):
        inputh.connect("HeatIn", ec_ref.ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True,
                       allow_type_mismatch=True)
        inputh.mirror_x(inputh.ports["HeatIn"].center[0])
    # add drop
    ## optics

    ec_ref.add_port("Ro1", port=doublering.ports["R1Through"])
    ec_ref.add_port("Ro2", port=doublering.ports["R1Add"])
    ec_ref.add_port("Ro3", port=doublering.ports["R2Through"])
    ec_ref.add_port("Ro4", port=doublering.ports["R2Add"])
    ## heat and optics
    for port in doublering.ports:
        if "Heat" in port.name:
            ec_ref.add_port("Ring" + port.name, port=doublering.ports[port.name])
    for port in coupler2x2.ports:
        if "Heat" in port.name:
            ec_ref.add_port("PMZI" + port.name, port=coupler2x2.ports[port.name])
    for port in inputh.ports:
        if "Heat" in port.name:
            ec_ref.add_port("Bus" + port.name, port=inputh.ports[port.name])
    # print(ec_ref.ports)
    ## heat
    # test2 = gf.Component()
    # test2 << ec_ref
    # test2 << ec_ref
    # test2.show()
    ec_ref = remove_layer(ec_ref, layer=(512, 8))
    add_labels_to_ports(ec_ref)
    return ec_ref



__all__ = [
    'ExternalCavitySOI',
    'ExternalCavitySiN',
    'ExternalCavitySiNH2',
    'ExternalCavitySiNH2_1',
    'ExternalCavity2',
    'ExternalCavity3',
    'ExternalCavityRaceTrack'
]

