from .BasicDefine import *
from .Heater import *
from .Ring import *
from .RaceTrack import *
from .CouplerMZI import *
from .MultiRing import *
# %% ExternalCavitySiN1:Proven design for SiN+Heater
def DoubleRingMemyshev(
        r_ring: float = 200,
        radius_delta: float = 4,
        width_ring: float = 1,
        width_single:float= 1,
        width_near: float = 0.91,
        width_heat:float =5,
        delta_heat:float = 1,
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
    '''
    diffenernt:
        width_ring_PMZI
        width_near_PMZI
        width_ring
        width_near

    '''
    c = gf.Component()
    # section and cross section
    S_near = gf.Section(width=width_near, offset=0, layer=oplayer, port_names=("o1", "o2"))
    S_single = gf.Section(width=width_single, offset=0, layer=oplayer, port_names=("o1", "o2"))
    X_near = gf.CrossSection(sections=[S_near])
    X_single = gf.CrossSection(sections=[S_single])
    if comp_coupler is None:
        coupler = c << gf.c.mmi1x2_with_sbend(cross_section=X_single,)
    else:
        coupler = c << comp_coupler
    if comp_reflecter is None:
        reflecter1 = c << SagnacRing(oplayer=oplayer,RadiusIn=r_ring,WidthIn=width_ring,WidthOut=width_near,GapCoup=gap_rc,AngleCouple=angle_rc,WidthSingle=width_single)
        reflecter2 = c << SagnacRing(oplayer=oplayer,RadiusIn=r_ring,WidthIn=width_ring,WidthOut=width_near,GapCoup=gap_rc,AngleCouple=angle_rc,WidthSingle=width_single)
    else:
        reflecter1 = c << comp_reflecter
        reflecter2 = c << comp_reflecter
    # ring ref1
    str1 = c << gf.c.bend_s(size=[length_c2r,delta_ring/2],cross_section=X_single)
    taper1 = c << gf.c.taper(width1 = width_single,width2 = width_near,layer= oplayer,length=length_taper)
    taper1_2 = c << gf.c.taper(width2 = width_single,width1 = width_near,layer= oplayer,length=length_taper)
    ring1 = c << RingPulleyT1(
        WidthRing=width_ring, WidthNear=width_near,WidthHeat=width_heat,
        RadiusRing=r_ring, GapRing=gap_rc,GapHeat=gap_heat,
        AngleCouple=angle_rc,IsAD=True,
        oplayer=oplayer, heatlayer=heatlayer,IsHeat=True,TypeHeater=type_ringheater,DeltaHeat=delta_heat,DirectionHeater='down'
    )
    str1.connect('o1',coupler.ports["o2"])
    taper1.connect('o1',str1.ports["o2"])
    ring1.connect('Input',taper1.ports['o2'])
    taper1_2.connect('o1',ring1.ports['Drop'])
    reflecter1.connect('o1',taper1_2.ports['o2'],mirror=True)
    # ring ref1
    str2 = c << gf.c.bend_s(size=[length_c2r,-delta_ring/2],cross_section=X_single)
    taper2 = c << gf.c.taper(width1 = width_single,width2 = width_near,layer= oplayer,length=length_taper)
    taper2_2 = c << gf.c.taper(width2=width_single, width1=width_near, layer=oplayer, length=length_taper)
    ring2 = c << RingPulleyT1(
        WidthRing=width_ring, WidthNear=width_near,WidthHeat=width_heat,
        RadiusRing=r_ring+radius_delta, GapRing=gap_rc,GapHeat=gap_heat,
        AngleCouple=angle_rc,
        oplayer=oplayer, heatlayer=heatlayer,IsHeat=True,TypeHeater=type_ringheater,DeltaHeat=delta_heat,DirectionHeater='down'
    )
    str2.connect('o1',coupler.ports["o3"])
    taper2.connect('o1',str2.ports["o2"])
    ring2.connect('Input',taper2.ports['o2'],mirror=True)
    taper2_2.connect('o1', ring2.ports['Drop'])
    reflecter2.connect('o1', taper2_2.ports['o2'])
    ## Add port
    c.add_port("o1",port=coupler.ports["o1"])
    c.add_port('R1Through',port=ring1.ports["Through"])
    c.add_port('R2Through', port=ring2.ports["Through"])
    c.add_port('R1Add',port=ring1.ports["Add"])
    c.add_port('R2Add', port=ring2.ports["Add"])
    c.add_port('Reflect1Out',port=reflecter1.ports["o2"])
    c.add_port('Reflect2Out',port=reflecter2.ports["o2"])
    for port in ring1.ports:
        if "Heat" in port:
            c.add_port("R1"+port,port=ring1.ports[port])
    for port in ring2.ports:
        if "Heat" in port:
            c.add_port("R2"+port,port=ring2.ports[port])
    add_labels_to_ports(c)
    return c
__all__=['DoubleRingMemyshev']