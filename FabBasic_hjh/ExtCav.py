import gdsfactory as gf
import numpy as np
import csv
from gdsfactory.typings import Layer
from gdsfactory.component import Component
from gdsfactory.path import Path, _fresnel, _rotate_points
from gdsfactory.typings import LayerSpec
from gdsfactory.cross_section import cross_section
from gdsfactory.generic_tech import get_generic_pdk
from gdsfactory.pdk import get_active_pdk
from gdsfactory.typings import Layer, LayerSpec, LayerSpecs ,Optional, Callable
from .BasicDefine import *
from .Heater import *
from .Ring import *
from .RaceTrack import *
from .CouplerMZI import *
from .MultiRing import *
# %% ExternalCavity:Proven design
@gf.cell
def ExternalCavitySOI(
        r_ring: float = 200,
        radius_delta: float = 4,
        width_ring: float = 1,
        width_single:float= 1,
        width_single2:float = 1,
        width_near: float = 0.91,
        width_heat:float =5,
        width_route:float =20,
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
        slablayer: LayerSpec = (1,0),
        swglayer: LayerSpec = LAYER.WG,
) -> Component:
    ec_ref = gf.Component("ec_ref")
    offsetVC = ViaArray(Spacing=0.7,WidthVia=0.3,Row=15,Col=8,IsEn=True,Enclosure=0.5,ViaLayer=(0,1),ViaEnLayers=[heatlayer,swglayer])
    deltaVCY = offsetVC.ports["up"].center[1]-offsetVC.ports["down"].center[1]
    deltaVCX = -offsetVC.ports["left"].center[0] + offsetVC.ports["right"].center[0]
    # section and cross section
    S_near = gf.Section(width=width_near, offset=0, layer=oplayer, port_names=("o1", "o2"))
    S_heater1 = gf.Section(width=width_heat, offset=gap_heat+width_heat/2+width_near/2, layer=heatlayer)
    S_heater2 = gf.Section(width=width_heat, offset=-(gap_heat + width_heat / 2 + width_near/2), layer=heatlayer)
    S_swg = gf.Section(width = 2*width_heat+2*gap_heat+width_near,offset=0, layer=swglayer,port_names=("o1","o2"))
    S_Rup = gf.Section(width=width_route, offset=2*deltaVCY+gap_heat+width_near/2-width_route/2,layer=routelayer)
    S_Rdown = gf.Section(width=width_route, offset=-(2 * deltaVCY + gap_heat + width_near / 2 - width_route / 2),layer=routelayer)
    BusHeatRouteComp = gf.Component("BHRC")
    BHRC0 = BusHeatRouteComp << gf.c.straight(width=deltaVCX, length=deltaVCY * 3 + width_near + 2 * gap_heat,layer=routelayer)
    BHRC0.rotate(-90)
    CAP_viaup = gf.cross_section.ComponentAlongPath(component=offsetVC,spacing=50,offset = gap_heat+width_near/2+deltaVCY,padding = 0)
    CAP_viadown = gf.cross_section.ComponentAlongPath(component=offsetVC, spacing=50,offset=-gap_heat-width_near / 2)
    CAP_Routeup = gf.cross_section.ComponentAlongPath(component=BusHeatRouteComp,spacing=100,offset=-width_near/2-gap_heat-deltaVCY)
    CAP_Routedown = gf.cross_section.ComponentAlongPath(component=BusHeatRouteComp,spacing=100,padding = 50,offset=width_near/2+gap_heat-(deltaVCY * 2 + width_near + 2 * gap_heat))
    CS_near = gf.CrossSection(sections=[S_near])
    CS_heat = gf.CrossSection(sections=[S_heater1,S_heater2,S_swg],components_along_path=[CAP_viaup,CAP_viadown])
    CS_Route = gf.CrossSection(sections=[S_Rup,S_Rdown],components_along_path=[CAP_Routeup,CAP_Routedown])
    # taper near to single
    tsn = gf.Component()
    tsn = gf.c.taper(width1=width_near, width2=width_single, length=length_t_s2n, layer=oplayer)
    # ring ref
    coupler_ref = DMZI(LengthCoup=length_dc, GapCoup=gap_dc, layer=oplayer, WidthSingle=width_single,LengthBridge=length_bridge)
    coupler2x2 = ec_ref << coupler_ref
    tapercoupler1 = ec_ref << gf.c.taper(width1=width_single, width2=width_near, length=length_t_s2n + 40,layer=oplayer)
    tapercoupler2 = ec_ref << gf.c.taper(width1=width_single, width2=width_near, length=length_t_s2n, layer=oplayer)
    tapercoupler1.connect("o1", destination=coupler2x2.ports["Output1"])
    tapercoupler2.connect("o1", destination=coupler2x2.ports["Output2"])
    bend_c2r = ec_ref << gf.c.bend_euler(width=width_near, angle=180, layer=oplayer, radius=r_euler_false*1.7,with_arc_floorplan=False,p=0.5)
    bend_c2r.connect("o1", tapercoupler2.ports["o2"]).mirror_y("o1")
    # str_c2r = ec_ref << gf.c.straight(width = width_near, layer = oplayer)
    # bend_c2r2 =
    ring_ref = DoubleRingPulley(
        WidthRing=width_ring, WidthNear=width_near, WidthEnd=0.2,
        LengthTaper=150, LengthR2R=length_r2r, DeltaRadius=radius_delta,
        RadiusRing=r_ring, RadiusBend0=40, GapRing=gap_rc,
        AngleCouple=angle_rc,
        oplayer=oplayer, heatlayer=heatlayer,
        Pitch=5,EndPort=[]
    )
    doublering = ec_ref << ring_ref[0]
    doublering.connect("o1", bend_c2r.ports["o2"])
    doublering.movex(-length_r2r+r_ring*3)#.movey(-r_ring)
    c2rRoute1 = gf.routing.get_route_sbend(
        tapercoupler1.ports["o2"], doublering.ports["o2"], cross_section=CS_near
    )
    ec_ref.add(c2rRoute1.references)
    c2rRoute2 = gf.routing.get_route(bend_c2r.ports["o2"],doublering.ports["o1"],cross_section=CS_near)
    ec_ref.add(c2rRoute2.references)
    # ring to out
    bend_ringout = ec_ref << gf.c.bend_euler(width=width_near, angle=180, layer=oplayer, radius=r_euler_false,with_arc_floorplan=False)
    bend_ringout.connect("o1",doublering.ports["RingPort0"])
    bend_ringout1 = ec_ref << gf.c.bend_euler(width=width_near, angle=180, layer=oplayer, radius=r_euler_false*3.5,
                                             with_arc_floorplan=False)
    bend_ringout1.connect("o1", doublering.ports["RingPort1"])
    taper_r2o_0 = ec_ref << gf.c.taper(width1 = width_near,width2 = width_single2,layer = oplayer,length = length_taper)
    taper_r2o_0.connect("o1",bend_ringout.ports["o2"])
    taper_r2o_2 = ec_ref << gf.c.taper(width1 = width_near,width2 = width_single2,layer = oplayer,length = length_taper)
    taper_r2o_2.connect("o1",doublering.ports["RingPort2"])

    taper_r2o_1 = ec_ref << gf.c.taper(width1 = width_near,width2 = width_single2,layer = oplayer,length = length_taper)
    taper_r2o_1.connect("o1",bend_ringout1.ports["o2"])
    taper_r2o_3 = ec_ref << gf.c.taper(width1 = width_near,width2 = width_single2,layer = oplayer,length = length_taper)
    taper_r2o_3.connect("o1",doublering.ports["RingPort3"])
    ec_ref.add_port("Rout2", port=taper_r2o_2.ports["o2"],orientation=180)
    ec_ref.add_port("Rout0", port=taper_r2o_0.ports["o2"],orientation=180)
    ec_ref.add_port("Rout1", port=taper_r2o_1.ports["o2"],orientation=180)
    ec_ref.add_port("Rout3", port=taper_r2o_3.ports["o2"],orientation=180)
    ## input
    str_input = list(range(30))
    bend_input = list(range(30))
    bend_input[0] = ec_ref << gf.c.bend_euler(width=width_single, angle=-225, layer=oplayer, radius=r_euler_false,with_arc_floorplan=False)
    bend_input[0].connect("o2", coupler2x2.ports["Input2"])
    bend_input[1] = ec_ref << gf.c.bend_euler(width=width_single, angle=45, layer=oplayer, radius=r_euler_false,with_arc_floorplan=False)
    bend_input[1].connect("o2", bend_input[0].ports["o1"])
    str_input[0] = ec_ref<<gf.c.straight(width = width_single,length=length_bridge*3-100+length_taper,layer=oplayer)
    str_input[0].connect("o2", bend_input[1].ports["o1"])
    bend_input[2] = ec_ref << gf.c.bend_euler(width=width_single, angle=180, layer=oplayer, radius=r_euler_false,with_arc_floorplan=False)
    bend_input[2].connect("o2",str_input[0].ports["o1"])
    str_input[1] = ec_ref<<gf.c.straight(width = width_single,length=length_input-100+length_taper+length_bridge*2,layer=oplayer)
    str_input[1].connect("o2", bend_input[2].ports["o1"])
    ec_ref.add_port("input", port=str_input[1].ports["o1"])
    ## output
    str_output = list(range(30))
    bend_output = list(range(30))
    bend_output[0] = ec_ref << gf.c.bend_euler(width=width_single, angle=200, layer=oplayer, radius=r_euler_false,with_arc_floorplan=False)
    bend_output[0].connect("o2", coupler2x2.ports["Input1"])
    bend_output[1] = ec_ref << gf.c.bend_euler(width=width_single, angle=-20, layer=oplayer, radius=r_euler_false,with_arc_floorplan=False)
    bend_output[1].connect("o2", bend_output[0].ports["o1"])
    delta = tapercoupler1.ports["o2"].center-bend_output[1].ports["o1"].center
    str_output[0] = ec_ref<<gf.c.taper(width1 = width_single,width2 = width_single2,length=length_taper,layer=oplayer)
    str_output[0].connect("o2", bend_output[1].ports["o1"])
    ec_ref.add_port("output", port=str_output[0].ports["o1"], orientation=180)
    # heater
    # Ring Heater

    # bus heater
    BusHeater = gf.Component(name="BusHeater")
    BusHeater_path = gf.path.straight(length=length_r2r-300)
    BusHeater_wg = BusHeater <<  gf.path.extrude(BusHeater_path,cross_section=CS_heat)
    BusHeater_route = BusHeater << gf.path.extrude(BusHeater_path,cross_section=CS_Route)
    BusHeater.add_port("o1",port=BusHeater_wg.ports["o1"])
    heat_cld0 = gf.geometry.offset(BusHeater_wg, distance=width_cld+0.8)
    heat_cld1 = gf.geometry.offset(heat_cld0, distance=-0.8, layer=slablayer)
    BusHeater.add_ref(heat_cld1)
    BusHeater_ref = ec_ref << BusHeater
    BusHeater_ref.connect("o1",destination=doublering.ports["r2ro1"]).movex(150)
    BusHeater_ref.mirror_x(port_name="o1")
    # mzi heater component
    MZIHeater = gf.Component(name="MZIHeater")
    MZI_path = gf.path.straight(length=length_bridge-100)
    MZIHeater_wg = MZIHeater << gf.path.extrude(MZI_path, cross_section=CS_heat)
    MZIHeater_route = MZIHeater << gf.path.extrude(MZI_path, cross_section=CS_Route)
    MZIHeater_cld0 = gf.geometry.offset(MZIHeater_wg, distance=width_cld + 0.8)
    MZIHeater_cld1 = gf.geometry.offset(MZIHeater_cld0, distance=-0.8, layer=slablayer)
    MZIHeater.add_ref(MZIHeater_cld1)
    MZIHeater.add_port("o1",port=MZIHeater_wg.ports["o1"],orientation=0)
    ## MZIheatup and down
    MZIHeaterup = ec_ref << MZIHeater
    MZIHeaterup.connect("o1",destination=coupler2x2.ports["Bridge1"])
    MZIHeaterup.movex(-100)
    MZIHeaterdown = ec_ref << MZIHeater
    MZIHeaterdown.connect("o1",destination=coupler2x2.ports["Bridge2"])
    MZIHeaterdown.movex(100)
    return ec_ref

# %% ExternalCavitySiN1:Proven design for SiN+Heater
def ExternalCavitySiN(
        r_ring: float = 200,
        r_euler_false :float = 100,
        r_mzi: float = 100,
        r_r2r: float = None,
        radius_delta: float = 4,
        width_ring: float = 1,
        width_ring_mzi: float = None,
        width_single:float= 1,
        width_near: float = 0.91,
        width_near_mzi: float = 1.2,
        width_heat:float =5,
        delta_heat:float = 1,
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
        length_c1r1:float = 100,
        gap_rc: float = 0.3,
        gap_mzi: float = 0.5,
        gap_heat: float = 2,
        gap_heat2: float = 75,
        type_ringheater: str = "default",
        type_mziheater: str = "default",
        type_busheater: str = "default",
        type_r2r: str = "straight",
        direction_io: str = "LR",
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        trelayer: LayerSpec = LAYER.DT,
) -> Component:
    '''
    diffenernt:
        width_ring_PMZI
        width_near_PMZI
        width_ring
        width_near

    '''
    ec_ref = gf.Component("ec_ref")
    heat_ref = gf.Component("heat_ref")
    if width_ring_mzi is None:
        width_ring_mzi = width_near
    # section and cross section
    S_near = gf.Section(width=width_near, offset=0, layer=oplayer, port_names=("o1", "o2"))
    CS_near = gf.CrossSection(sections=[S_near])
    # ring ref
    coupler_ref = PMZI(WidthNear=width_near_mzi,WidthRing=width_ring_mzi,Radius=r_mzi,
                        AngleCouple=angle_pmzi, LengthTaper=length_taper,LengthBend=length_bend,LengthBridge=length_bridge,
                       GapCoup=gap_mzi,IsHeat=True,
                       oplayer=oplayer,heatlayer=heatlayer,
                       WidthHeat=width_heat,GapHeat=gap_heat2,TypeHeater=type_mziheater,DeltaHeat=delta_heat
                       )
    coupler2x2 = ec_ref << coupler_ref
    coupler2x2.mirror_y()
    bend_c1r1 = ec_ref << gf.c.bend_euler(radius=r_euler_false, angle = -angle_m2r,width = width_near_mzi,layer = oplayer)
    bend_c1r2 = ec_ref << gf.c.bend_euler(radius=r_euler_false, angle=angle_m2r, width=width_near, layer=oplayer)
    str_c1r1 = ec_ref << gf.c.straight(width=width_near_mzi,length = length_c1r1,layer=oplayer)
    str_c1r1.connect("o1", destination=coupler2x2.ports["Output1"])
    bend_c1r1.connect("o1",destination=str_c1r1.ports["o2"])
    tapercoupler1 = ec_ref << gf.c.taper(width1=width_near_mzi, width2=width_near, length=min(length_t_s2n,300*abs(width_near_mzi-width_near)+1),layer=oplayer)
    tapercoupler1.connect("o1", destination=bend_c1r1.ports["o2"])
    tapercoupler2 = ec_ref << gf.c.taper(width1=width_ring_mzi, width2=width_near, length=min(length_t_s2n,300*abs(width_ring_mzi-width_near)+1),layer=oplayer)
    bend_c2r_path = euler_Bend_Half(angle = -90,radius=r_mzi)
    bend_c2r = ec_ref << gf.path.extrude(bend_c2r_path,width=width_ring_mzi, layer=oplayer)
    bend_c2r.connect("o1", coupler2x2.ports["Output2"])
    tapercoupler2.connect("o1",bend_c2r.ports["o2"])
    ring_ref = DoubleRingPulley(
        WidthRing=width_ring, WidthNear=width_near,WidthHeat=width_heat,
        LengthR2R=length_r2r, DeltaRadius=-radius_delta,
        RadiusRing=r_ring+radius_delta, GapRing=gap_rc,GapHeat=gap_heat,RadiusR2R=r_r2r,
        AngleCouple=angle_rc,
        oplayer=oplayer, heatlayer=heatlayer,IsHeat=True,TypeHeater=type_ringheater,DeltaHeat=delta_heat,TypeR2R=type_r2r,
    )
    doublering = ec_ref << ring_ref
    doublering.connect("o1", bend_c2r.ports["o2"])
    doublering.movex(length_ring2coup)
    delta1 = bend_c1r1.ports["o1"].center-bend_c1r1.ports["o2"].center
    delta2 = tapercoupler1.ports["o2"].center-doublering.ports["o2"].center
    addlength = abs(delta1[1]-delta2[1])/np.sin(angle_m2r*np.pi/180)
    str_tapercoupler = ec_ref << gf.c.straight(width = width_near,length = addlength,layer= oplayer)
    str_tapercoupler.connect("o1",destination=tapercoupler1.ports["o2"])
    bend_c1r2.connect("o1",destination=str_tapercoupler.ports["o2"])
    c2rRoute1 = gf.routing.get_route(bend_c1r2.ports["o2"],doublering.ports["o2"],cross_section=CS_near)
    ec_ref.add(c2rRoute1.references)
    c2rRoute2 = gf.routing.get_route(tapercoupler2.ports["o2"],doublering.ports["o1"],cross_section=CS_near)
    ec_ref.add(c2rRoute2.references)
    ## left
    str_input = list(range(30))
    bend_input = list(range(30))
    str_input[0] = ec_ref<<gf.c.taper(width1 = width_near_mzi,width2=width_single,length=length_taper,layer=oplayer)
    str_input[0].connect("o1", coupler2x2.ports["Input2"])
    ## right
    str_output = list(range(30))
    bend_output = list(range(30))
    path_bend_output = euler_Bend_Half(angle = -90,radius=r_mzi)
    bend_output[0] = ec_ref << gf.path.extrude(path_bend_output,layer=oplayer,width=width_near)
    bend_output[0].connect("o1",coupler2x2.ports["Input1"])
    str_output[0] = ec_ref<<gf.c.taper(width1 = width_near,width2 = width_single,length=length_taper,layer=oplayer)
    str_output[0].connect("o1", bend_output[0].ports["o2"])
    # input heater
    str_input[1] = ec_ref << gf.c.straight(width=width_single, length=length_input, layer=oplayer)
    path_input = gf.path.straight(length=length_input)
    inputh = ec_ref << DifferentHeater(PathHeat=path_input,WidthHeat=width_heat,WidthWG=width_single,DeltaHeat=delta_heat,GapHeat=gap_heat2*length_input/length_bridge,WidthRoute=20,
                                       heatlayer=heatlayer,TypeHeater=type_busheater)
    if direction_io == "LR":
        str_input[1].connect("o2", str_input[0].ports["o1"])
        ec_ref.add_port("o1", port=str_input[1].ports["o2"])
        ec_ref.add_port("o2", port=str_output[0].ports["o2"])
    elif direction_io == "RL":
        str_input[1].connect("o1", str_output[0].ports["o2"])
        ec_ref.add_port("o1", port=str_input[0].ports["o2"])
        ec_ref.add_port("o2", port=str_input[1].ports["o2"])
    inputh.connect("HeatIn",str_input[1].ports["o2"],allow_width_mismatch=True,allow_layer_mismatch=True,allow_type_mismatch=True).mirror_x("HeatIn")
    # add drop
    ## optics


    ec_ref.add_port("Ro1",port=doublering.ports["R1Through"])
    ec_ref.add_port("Ro2", port=doublering.ports["R1Add"])
    ec_ref.add_port("Ro3", port=doublering.ports["R2Through"])
    ec_ref.add_port("Ro4", port=doublering.ports["R2Add"])
    ## heat and optics
    for port in doublering.ports:
        if "Heat" in port:
            ec_ref.add_port("Ring"+port, port=doublering.ports[port])
    for port in coupler2x2.ports:
        if "Heat" in port:
            ec_ref.add_port("PMZI" + port, port=coupler2x2.ports[port])
    for port in inputh.ports:
        if "Heat" in port:
            ec_ref.add_port("Bus" + port, port=inputh.ports[port])
    # print(heat_ref.ports)
    ## heat
    # test2 = gf.Component()
    # test2 << ec_ref
    # test2 << heat_ref
    # test2.show()
    add_labels_to_ports(ec_ref,label_layer=(512,8))
    return ec_ref
# %% ExternalCavity1SiNH:Proven design for SiN+Heater
def ExternalCavitySiNH2(
        r_ring: float = 200,
        r_euler_false :float = 100,
        r_mzi: float = 100,
        radius_delta: float = 4,
        width_ring: float = 1,
        width_single:float= 1,
        width_near: float = 0.91,
        width_near_mzi: float = 1.2,
        width_heat:float =5,
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
        length_busheater:float = 300,
        gap_rc: float = 0.3,
        gap_mzi: float = 0.5,
        gap_heat: float = 2,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        trelayer: LayerSpec = LAYER.DT,
) -> [Component]:
    '''
    width_ring_PMZI = width_near_Ring
    width_near_PMZI  = couple width_ring_PMZI
    width_ring_Ring
    width_ring_Ring > width_near_Ring = width_ring_PMZI = width_near_PMZI
    '''
    ec_ref = gf.Component("ec_ref")
    heat_ref = gf.Component("heat_ref")
    # section and cross section
    S_near = gf.Section(width=width_near, offset=0, layer=oplayer, port_names=("o1", "o2"))
    CS_near = gf.CrossSection(sections=[S_near])
    # ring ref
    coupler_ref = PMZIHSn(WidthNear=width_near_mzi,WidthRing=width_near,Radius=r_mzi,
                        AngleCouple=angle_pmzi, LengthTaper=length_taper,LengthBend=400,LengthBridge=length_bridge,
                       GapCoup=gap_mzi, oplayer=oplayer,
                          heatlayer=heatlayer,WidthHeat=width_heat,GapHeat=gap_heat
                       )
    coupler2x2 = ec_ref << coupler_ref[0]
    coupler2x2.mirror_y()
    bend_c1r1 = ec_ref << gf.c.bend_euler(radius=r_euler_false, angle = -angle_m2r,width = width_near_mzi,layer = oplayer,with_arc_floorplan=False)
    bend_c1r2 = ec_ref << gf.c.bend_euler(radius=r_euler_false, angle=angle_m2r, width=width_near, layer=oplayer,with_arc_floorplan=False)
    bend_c1r1.connect("o1", destination=coupler2x2.ports["Output1"])
    tapercoupler1 = ec_ref << gf.c.taper(width1=width_near_mzi, width2=width_near, length=length_t_s2n,layer=oplayer)
    tapercoupler1.connect("o1", destination=bend_c1r1.ports["o2"])
    bend_c2r_path = euler_Bend_Half(angle = -90,radius=r_mzi)
    bend_c2r = ec_ref << gf.path.extrude(bend_c2r_path,width=width_near, layer=oplayer)
    bend_c2r.connect("o1", coupler2x2.ports["Output2"])
    ring_ref = DoubleRingPulley2HSn(
        WidthRing=width_ring, WidthNear=width_near,WidthHeat=width_heat,
        LengthR2R=length_r2r, DeltaRadius=-radius_delta,
        RadiusRing=r_ring+radius_delta, GapRing=gap_rc,GapHeat=gap_heat,
        AngleCouple=angle_rc,
        oplayer=oplayer, heatlayer=heatlayer,IsHeat=True,
    )
    doublering = ec_ref << ring_ref[0]
    doublering.connect("o1", bend_c2r.ports["o2"])
    doublering.movex(length_ring2coup)
    delta1 = bend_c1r1.ports["o1"].center-bend_c1r1.ports["o2"].center
    delta2 = tapercoupler1.ports["o2"].center-doublering.ports["o2"].center
    addlength = abs(delta1[1]-delta2[1])/np.sin(angle_m2r*np.pi/180)
    str_tapercoupler = ec_ref << gf.c.straight(width = width_near,length = addlength,layer= oplayer)
    str_tapercoupler.connect("o1",destination=tapercoupler1.ports["o2"])
    bend_c1r2.connect("o1",destination=str_tapercoupler.ports["o2"])
    c2rRoute1 = gf.routing.get_route(bend_c1r2.ports["o2"],doublering.ports["o2"],cross_section=CS_near)
    ec_ref.add(c2rRoute1.references)
    c2rRoute2 = gf.routing.get_route(bend_c2r.ports["o2"],doublering.ports["o1"],cross_section=CS_near)
    ec_ref.add(c2rRoute2.references)
    ## input
    str_input = list(range(30))
    bend_input = list(range(30))
    str_input[0] = ec_ref << gf.c.taper(width1 = width_single,width2 = width_near_mzi ,length = length_taper,layer = oplayer)
    str_input[0].connect("o2", coupler2x2.ports["Input2"])
    path_input = gf.path.straight(length=length_busheater)
    str_input[1] = ec_ref << gf.path.extrude(path_input,width = width_single,layer=oplayer)
    str_input[2] = ec_ref << gf.c.straight(width=width_single, length=length_input, layer=oplayer)
    str_input[1].connect("o2", str_input[0].ports["o1"])
    str_input[2].connect("o2", str_input[1].ports["o1"])
    ## output
    str_output = list(range(30))
    bend_output = list(range(30))
    path_bend_output = euler_Bend_Half(angle = 90,radius=r_mzi)
    bend_output[0] = ec_ref << gf.path.extrude(path_bend_output,layer=oplayer,width=width_near)
    bend_output[0].connect("o1", coupler2x2.ports["Input1"]).mirror_x("o1")
    str_output[0] = ec_ref<<gf.c.taper(width1 = width_near,width2 = width_single,length=length_taper,layer=oplayer)
    str_output[0].connect("o1", bend_output[0].ports["o2"])

    # heater
    Hring = heat_ref << ring_ref[1]
    Hring.connect("1HeatIn",destination=doublering.ports["1HeatIn"]).rotate(180,center="1HeatIn")
    pmzih = heat_ref << coupler_ref[1]
    pmzih.mirror_y().connect("HeatLout",destination=coupler2x2.ports["HeatLout"],
                             allow_width_mismatch=True,allow_layer_mismatch=True,allow_type_mismatch=True)
    inputh = heat_ref << SnakeHeater(
        heatlayer=heatlayer,WidthHeat=width_heat,WidthWG=width_near_mzi,GapHeat=gap_heat,PathHeat=path_input)
    inputh.connect("o2",str_input[0].ports["o1"],allow_width_mismatch=True,allow_layer_mismatch=True,allow_type_mismatch=True)
    # add drop
    ## optics
    ec_ref.add_port("Input", port=str_input[2].ports["o1"])
    ec_ref.add_port("Output", port=str_output[0].ports["o2"])
    ec_ref.add_port("Ro1",port=doublering.ports["R1T"])
    ec_ref.add_port("Ro2", port=doublering.ports["R1A"])
    ec_ref.add_port("Ro3", port=doublering.ports["R2I"])
    ec_ref.add_port("Ro4", port=doublering.ports["R2D"])
    ## heat and optics
    ec_ref.add_port("Ring1HeatIn",port=doublering.ports["1HeatIn"])
    ec_ref.add_port("PMZIHeatLout",port=coupler2x2.ports["HeatLout"])
    # print(pmzih.ports)
    for port in pmzih.ports:
        heat_ref.add_port("PMZI"+port, port=pmzih.ports[port])
    for port in Hring.ports:
        heat_ref.add_port("Ring"+port,port = Hring.ports[port])
    for port in inputh.ports:
        heat_ref.add_port("Input"+port,port=inputh.ports[port])
    # print(heat_ref.ports)
    ## heat
    # test2 = gf.Component()
    # test2 << ec_ref
    # test2 << heat_ref
    # test2.show()
    return [ec_ref,heat_ref]
# %% ExternalCavity1SiNH:Proven design for SiN+Heater
#Ring to ring is bend
def ExternalCavitySiNH2_1(
        r_ring: float = 200,
        r_euler_false :float = 100,
        r_mzi: float = 100,
        radius_delta: float = 4,
        width_ring: float = 1,
        width_single:float= 1,
        width_near: float = 0.91,
        width_near_mzi: float = 1.2,
        width_heat:float =5,
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
        length_busheater:float = 300,
        gap_rc: float = 0.3,
        gap_mzi: float = 0.5,
        gap_heat: float = 2,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
) -> [Component]:
    '''
    width_ring_PMZI = width_near_Ring
    width_near_PMZI  = couple width_ring_PMZI
    width_ring_Ring
    width_ring_Ring > width_near_Ring = width_ring_PMZI = width_near_PMZI
    '''
    ec_ref = gf.Component("ec_ref")
    heat_ref = gf.Component("heat_ref")
    # section and cross section
    S_near = gf.Section(width=width_near, offset=0, layer=oplayer, port_names=("o1", "o2"))
    CS_near = gf.CrossSection(sections=[S_near])
    # ring ref
    coupler_ref = PMZIHSn(WidthNear=width_near_mzi,WidthRing=width_near,Radius=r_mzi,
                        AngleCouple=angle_pmzi, LengthTaper=length_taper,LengthBend=400,LengthBridge=length_bridge,
                       GapCoup=gap_mzi, oplayer=oplayer,
                          heatlayer=heatlayer,WidthHeat=width_heat,GapHeat=gap_heat
                       )
    coupler2x2 = ec_ref << coupler_ref[0]
    coupler2x2.mirror_y()
    bend_c1r1 = ec_ref << gf.c.bend_euler(radius=r_euler_false, angle = -angle_m2r,width = width_near_mzi,layer = oplayer,with_arc_floorplan=False)
    bend_c1r2 = ec_ref << gf.c.bend_euler(radius=r_euler_false, angle=angle_m2r, width=width_near, layer=oplayer,with_arc_floorplan=False)
    bend_c1r1.connect("o1", destination=coupler2x2.ports["Output1"])
    tapercoupler1 = ec_ref << gf.c.taper(width1=width_near_mzi, width2=width_near, length=length_t_s2n,layer=oplayer)
    tapercoupler1.connect("o1", destination=bend_c1r1.ports["o2"])
    bend_c2r_path = euler_Bend_Half(angle = -90,radius=r_mzi)
    bend_c2r = ec_ref << gf.path.extrude(bend_c2r_path,width=width_near, layer=oplayer)
    bend_c2r.connect("o1", coupler2x2.ports["Output2"])
    ring_ref = DoubleRingPulley2_1HSn(
        WidthRing=width_ring, WidthNear=width_near,WidthHeat=width_heat,
        LengthR2R=length_r2r, DeltaRadius=-radius_delta,
        RadiusRing=r_ring+radius_delta, GapRing=gap_rc,GapHeat=gap_heat,
        AngleCouple=angle_rc,
        oplayer=oplayer, heatlayer=heatlayer,IsHeat=True,
    )
    doublering = ec_ref << ring_ref[0]
    doublering.connect("o1", bend_c2r.ports["o2"])
    doublering.movex(length_ring2coup)
    delta1 = bend_c1r1.ports["o1"].center-bend_c1r1.ports["o2"].center
    delta2 = tapercoupler1.ports["o2"].center-doublering.ports["o2"].center
    addlength = abs(delta1[1]-delta2[1])/np.sin(angle_m2r*np.pi/180)
    str_tapercoupler = ec_ref << gf.c.straight(width = width_near,length = addlength,layer= oplayer)
    str_tapercoupler.connect("o1",destination=tapercoupler1.ports["o2"])
    bend_c1r2.connect("o1",destination=str_tapercoupler.ports["o2"])
    c2rRoute1 = gf.routing.get_route(bend_c1r2.ports["o2"],doublering.ports["o2"],cross_section=CS_near)
    ec_ref.add(c2rRoute1.references)
    c2rRoute2 = gf.routing.get_route(bend_c2r.ports["o2"],doublering.ports["o1"],cross_section=CS_near)
    ec_ref.add(c2rRoute2.references)
    ## input
    str_input = list(range(30))
    bend_input = list(range(30))
    str_input[0] = ec_ref << gf.c.taper(width1 = width_single,width2 = width_near_mzi ,length = length_taper,layer = oplayer)
    str_input[0].connect("o2", coupler2x2.ports["Input2"])
    path_input = gf.path.straight(length=length_busheater)
    str_input[1] = ec_ref << gf.path.extrude(path_input,width = width_single,layer=oplayer)
    str_input[2] = ec_ref << gf.c.straight(width=width_single, length=length_input, layer=oplayer)
    str_input[1].connect("o2", str_input[0].ports["o1"])
    str_input[2].connect("o2", str_input[1].ports["o1"])
    ## output
    str_output = list(range(30))
    bend_output = list(range(30))
    path_bend_output = euler_Bend_Half(angle = 90,radius=r_mzi)
    bend_output[0] = ec_ref << gf.path.extrude(path_bend_output,layer=oplayer,width=width_near)
    bend_output[0].connect("o1", coupler2x2.ports["Input1"]).mirror_x("o1")
    str_output[0] = ec_ref<<gf.c.taper(width1 = width_near,width2 = width_single,length=length_taper,layer=oplayer)
    str_output[0].connect("o1", bend_output[0].ports["o2"])

    # heater
    Hring = heat_ref << ring_ref[1]
    Hring.connect("1HeatIn",destination=doublering.ports["1HeatIn"]).rotate(180,center="1HeatIn")
    pmzih = heat_ref << coupler_ref[1]
    pmzih.mirror_y().connect("HeatLout",destination=coupler2x2.ports["HeatLout"],
                             allow_width_mismatch=True,allow_layer_mismatch=True,allow_type_mismatch=True)
    inputh = heat_ref << SnakeHeater(
        heatlayer=heatlayer,WidthHeat=width_heat,WidthWG=width_near_mzi,GapHeat=gap_heat,PathHeat=path_input)
    inputh.connect("o2",str_input[0].ports["o1"],allow_width_mismatch=True,allow_layer_mismatch=True,allow_type_mismatch=True)
    # add drop
    ## optics
    ec_ref.add_port("Input", port=str_input[1].ports["o1"])
    ec_ref.add_port("Output", port=str_output[0].ports["o2"])
    ec_ref.add_port("Ro1",port=doublering.ports["R1Through"])
    ec_ref.add_port("Ro2", port=doublering.ports["R1Add"])
    ec_ref.add_port("Ro3", port=doublering.ports["R2Input"])
    ec_ref.add_port("Ro4", port=doublering.ports["R2Drop"])
    ## heat and optics
    ec_ref.add_port("Ring1HeatIn",port=doublering.ports["1HeatIn"])
    ec_ref.add_port("PMZIHeatLout",port=coupler2x2.ports["HeatLout"])
    # print(pmzih.ports)
    for port in pmzih.ports:
        heat_ref.add_port("PMZI"+port, port=pmzih.ports[port])
    for port in Hring.ports:
        heat_ref.add_port("Ring"+port,port = Hring.ports[port])
    for port in inputh.ports:
        heat_ref.add_port("Input"+port,port=inputh.ports[port])
    # print(heat_ref.ports)
    ## heat
    # test2 = gf.Component()
    # test2 << ec_ref
    # test2 << heat_ref
    # test2.show()
    return [ec_ref,heat_ref]
# %% ExternalCavity2: tri ring ecl
@gf.cell
def ExternalCavity2(
        r_ring: float = 200,
        radius_delta: float = 4,
        width_single:float = 1,
        width_ring: float = 1,
        width_near: float = 0.91,
        width_heat: float = 5,
        width_route: float = 20,
        width_cld: float = 3,
        angle_rc: float = 20,
        angle_rc3:float = 40,
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
    ec2_ref = gf.Component(Name)
    if Crossing == None:
        crossing0 = Crossing_taper(WidthCross=0.8,WidthWg=width_single,LengthTaper=5,oplayer = oplayer)
    else:
        crossing0 = Crossing
    TriRing = ec2_ref << ADRAPRADR(WidthRing=width_ring,WidthNear=width_near,WidthSingle=width_single,
                                     RadiusRing=r_ring,DeltaRadius=radius_delta,LengthTaper=length_taper,LengthR2R=length_r2r,
                                     AngleCouple=angle_rc,AngleCouple3=angle_rc3,GapRing=gap_rc,CrossComp=crossing0,LengthR2C=500
    )
    # ring port taper & bend
    taperbend = gf.Component("taperbend")
    taper_n2s = taperbend << gf.c.taper(width1 = width_near,width2=width_single,layer=oplayer,length = length_taper/2)
    bend_n2s = taperbend << gf.c.bend_euler(width = width_single,layer = oplayer,radius=120,angle = 45)
    bend_n2s.connect("o1",taper_n2s.ports["o2"])
    taperbend.add_port("o1",port=taper_n2s.ports["o1"])
    taperbend.add_port("o2", port=bend_n2s.ports["o2"])
    taper_n2s_1 = ec2_ref << taperbend
    taper_n2s_1.connect("o1",TriRing.ports["r1Th"]).mirror_y("o1")
    taper_n2s_2 = ec2_ref << taperbend
    taper_n2s_2.connect("o1",TriRing.ports["r1Ad"]).mirror_y("o1")
    taper_n2s_3 = ec2_ref << taperbend
    taper_n2s_3.connect("o1",TriRing.ports["r2Th"])
    taper_n2s_4 = ec2_ref << taperbend
    taper_n2s_4.connect("o1",TriRing.ports["r2Ad"])
    # crossing bend
    bend45 = gf.c.bend_euler(width = width_single,radius=120,angle=45,layer=oplayer)
    bend45_o2 = ec2_ref << bend45
    bend45_o2.connect("o1",TriRing.ports["co2"])
    bend45_o3 = ec2_ref << bend45
    bend45_o3.connect("o1",TriRing.ports["co3"]).mirror_y("o1")
    ec2_ref.add_port("input",port=bend45_o2.ports["o2"])
    ec2_ref.add_port("output", port=bend45_o3.ports["o2"])
    # Heater
    offsetVC = ViaArray(Spacing=0.7, WidthVia=0.3, Row=15, Col=8, IsEn=True, Enclosure=0.5, ViaLayer=LAYER.CT,
                           ViaEnLayers=[LAYER.CTE, heatlayer, swglayer])
    deltaVCY = offsetVC.ports["up"].center[1] - offsetVC.ports["down"].center[1]
    deltaVCX = -offsetVC.ports["left"].center[0] + offsetVC.ports["right"].center[0]
    ec2_ref.add_port("to1",port=TriRing.ports["to1"])
    ec2_ref.add_port("to2", port=TriRing.ports["to2"])
    ec2_ref.add_port("r1Th",port=taper_n2s_1.ports["o2"])
    ec2_ref.add_port("r1Ad", port=taper_n2s_2.ports["o2"])
    ec2_ref.add_port("r2Th", port=taper_n2s_3.ports["o2"])
    ec2_ref.add_port("r2Ad", port=taper_n2s_4.ports["o2"])
    ec2_ref.add_port("r1L",port = TriRing.ports["r1L"])
    ec2_ref.add_port("r1R", port=TriRing.ports["r1R"])
    ec2_ref.add_port("r2L", port=TriRing.ports["r2L"])
    ec2_ref.add_port("r2R", port=TriRing.ports["r2R"])
    ec2_ref.add_port("r3L", port=TriRing.ports["r3L"])
    ec2_ref.add_port("r3R", port=TriRing.ports["r3R"])
    ec2_ref.add_port("co2", port=TriRing.ports["co2"])
    ec2_ref.add_port("co3", port=TriRing.ports["co3"])
    add_labels_to_ports(ec2_ref)
    return ec2_ref
# %% ExternalCavity3: risky design2
@gf.cell
def ExternalCavity3(
        r_ring: float = 200,
        radius_delta: float = 4,
        width_single:float = 1,
        width_ring: float = 1,
        width_near: float = 0.91,
        width_heat: float = 5,
        width_route: float = 20,
        width_cld: float = 3,
        angle_rc: float = 20,
        angle_rc3:float = 40,
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
    ec3_ref = gf.Component(Name)
    if Crossing == None:
        crossing0 = Crossing_taper(WidthCross=2,WidthWg=width_near,LengthTaper=10,oplayer = oplayer)
    else:
        crossing0 = Crossing
    TriRing = ec3_ref << ADRAPRADR(WidthRing=width_ring,WidthNear=width_near,WidthSingle=width_single,IsSquare=True,IsHeat=True,
                                     RadiusRing=r_ring,RadiusCrossBend=80,DeltaRadius=radius_delta,
                                   LengthTaper=length_taper,LengthR2R=length_r2r,LengthR2C=length_r2c,
                                    AngleCouple=angle_rc,AngleCouple3=angle_rc3,GapRing=gap_rc,CrossComp=crossing0,
                                   oplayer=oplayer,heatlayer=heatlayer,WidthHeat=width_heat
    )
    # ring port taper & bend
    taperbend = gf.Component("taperbend")
    taper_n2s = taperbend << gf.c.taper(width1 = width_near,width2=width_single,layer=oplayer,length = length_taper/2)
    bend_n2s = taperbend << gf.c.bend_euler(width = width_single,layer = oplayer,radius=120,angle = 45)
    bend_n2s.connect("o1",taper_n2s.ports["o2"])
    taperbend.add_port("o1",port=taper_n2s.ports["o1"])
    taperbend.add_port("o2", port=bend_n2s.ports["o2"])
    # taper_n2s_1 = ec3_ref << taperbend
    # taper_n2s_1.connect("o1",TriRing.ports["r1Th"],allow_layer_mismatch=True).mirror_y("o1")
    # taper_n2s_2 = ec3_ref << taperbend
    # taper_n2s_2.connect("o1",TriRing.ports["r1Ad"],allow_layer_mismatch=True).mirror_y("o1")
    # taper_n2s_3 = ec3_ref << taperbend
    # taper_n2s_3.connect("o1",TriRing.ports["r2Th"],allow_layer_mismatch=True)
    # taper_n2s_4 = ec3_ref << taperbend
    # taper_n2s_4.connect("o1",TriRing.ports["r2Ad"],allow_layer_mismatch=True)
    # crossing taper
    taper_cross = gf.c.taper(width1=width_near,width2=width_single,length=length_taper,layer=oplayer)
    taper_cross_1 = ec3_ref << taper_cross
    taper_cross_2 = ec3_ref << taper_cross
    taper_cross_1.connect("o1",destination=TriRing.ports["co2"])
    taper_cross_2.connect("o1", destination=TriRing.ports["co3"])
    # Heater
    # ec3_ref.add_port("to1",port=TriRing.ports["to1"])
    # ec3_ref.add_port("to2", port=TriRing.ports["to2"])
    # ec3_ref.add_port("r1Th",port=taper_n2s_1.ports["o2"])
    # ec3_ref.add_port("r1Ad", port=taper_n2s_2.ports["o2"])
    # ec3_ref.add_port("r2Th", port=taper_n2s_3.ports["o2"])
    # ec3_ref.add_port("r2Ad", port=taper_n2s_4.ports["o2"])
    ec3_ref.add_port("r1L",port = TriRing.ports["r1L"])
    ec3_ref.add_port("r1R", port=TriRing.ports["r1R"])
    ec3_ref.add_port("r2L", port=TriRing.ports["r2L"])
    ec3_ref.add_port("r2R", port=TriRing.ports["r2R"])
    ec3_ref.add_port("r3L", port=TriRing.ports["r3L"])
    ec3_ref.add_port("r3R", port=TriRing.ports["r3R"])
    ec3_ref.add_port("co2", port=taper_cross_1.ports["o2"])
    ec3_ref.add_port("co3", port=taper_cross_2.ports["o2"])
    add_labels_to_ports(ec3_ref)
    return ec3_ref

#%% function export
__all__ = ['ExternalCavity2','ExternalCavitySOI','ExternalCavity3','ExternalCavitySiNH2','ExternalCavitySiNH2_1','ExternalCavitySiN']