from .BasicDefine import *
from .Heater import *
from .Boomerang import *
from .MultiRing import *
# %% defult in out taper
@gf.cell
def create_taper(width1, width2, lengthleft=20,lengthtaper=200,lengthright=20, layer:LayerSpec=LAYER.WG):
    taper = gf.Component("taper")
    taper_te = taper << gf.c.taper(width1=width1, width2=width2, length=lengthtaper, layer=layer)
    taper_straight1 = taper << GfCStraight(width=width1, length=lengthleft, layer=layer)
    taper_straight2 = taper << GfCStraight(width=width2, length=lengthright, layer=layer)
    taper_te.connect("o1", other=taper_straight1.ports["o2"])
    taper_straight2.connect("o1", taper_te.ports["o2"])
    taper.add_port(name="o1", port=taper_straight1.ports["o1"])
    taper.add_port(name="o2", port=taper_straight2.ports["o2"])
    return taper

taper_in = create_taper("taper_in", width1=0.3, width2=1,  layer=LAYER.WG)
taper_out = create_taper("taper_out", width1=1, width2=0.2, layer=LAYER.WG)
# TCRingBoomerangT1: Total singleBoomerang Ring
@gf.cell
def TCRingBoomerangT1(
        r_ring: float = 120,
        r_euler_min: float = 100,
        r_euler_boom: float= 100,
        width_ringin: float = 1,
        width_ringout: float = 2,
        width_straight:float = 3,
        width_heat: float = 5,
        width_route: float = 20,
        width_single: float = 1,
        width_via:float = 0.5,
        length_bridge1:float = 100,
        length_bridge2:float = 100,
        length_couple:float = 100,
        length_taper: float = 150,
        length_total: float = 10000,
        length_th_horizontal: float = 10,
        length_th_vertical: float = 10,
        pos_ring: float = 700,
        gap_rr: float = 1,
        gap_rb: float = 2,
        gap_heat: float = 1,
        delta_heat: float = 20,
        spacing:float =1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        is_heat: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        type_heater: str = "default",  # 控制加热器类型
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个环形波导组件，支持通过 position_taper 参数控制锥形波导的位置，并通过 type_heater 参数控制加热器类型。
    使用 RingPulleyT1 型的微环结构。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_euler_min: 欧拉弯曲的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        length_th_horizontal: 水平直波导的长度（单位：um）。
        length_th_vertical: 垂直直波导的长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        gap_heat: 加热器与波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        is_heat: 是否添加加热器。
        is_ad: 是否添加 Add/Drop 端口。
        oplayer: 光学层定义。
        heatlayer: 加热层定义。
        position_taper: 锥形波导的位置，支持 "before_bend"（默认）、"after_bend"、"between_bend"、"no_bend"。
        type_heater: 加热器类型，支持 "default"（默认）、"side"（侧边加热）、"bothside"（两侧加热）。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
        RingInput: 环形波导的输入端口。
        RingL: 环形波导的左侧端口。
        RingR: 环形波导的右侧端口。
    """
    sr = gf.Component()
    ring = gf.Component("Ring")
    ring0 = ring << RingBoomerang(
        WidthRingIn=width_ringin, WidthRingOut=width_ringout, WidthHeat=width_heat,WidthStraight=width_straight,WidthRoute=width_route,WidthVia=width_via,
        LengthTaper=length_taper,LengthBridge2=length_bridge2,LengthBridge1=length_bridge1,LengthCouple=length_couple,
        GapRR=gap_rr,GapRB=gap_rb,GapHeat=gap_heat,DeltaHeat=delta_heat,Spacing=spacing,
        RadiusRing=r_ring,RadiusEuler=r_euler_boom,IsHeatIn=is_heat,IsHeatOut=is_heat,
        oplayer=oplayer, heatlayer=heatlayer, TypeHeater=type_heater
    )
    # input through
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring0.ports["Input"])
    taper_s2n2 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_thr1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer,angle=-90,with_arc_floorplan=False)
    bend_thr2 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer,angle=90,with_arc_floorplan=False)
    str_th_horizontal = ring << GfCStraight(width=width_straight,length=length_th_horizontal,layer=oplayer)
    str_th_vertical = ring << GfCStraight(width=width_single, length=length_th_vertical, layer=oplayer)
    str_th_horizontal.connect("o1", ring0.ports["Through"])
    bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
    taper_s2n2.connect("o1", other=bend_thr1.ports["o2"])
    str_th_vertical.connect("o1",other=taper_s2n2.ports["o2"])
    bend_thr2.connect("o1",other=str_th_vertical.ports["o2"])
    ring.add_port("o1", port=taper_s2n1.ports["o1"])
    ring.add_port("o2", port=bend_thr2.ports["o2"])
    # add drop
    taper_s2n3 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    taper_s2n3.connect("o2", ring0.ports["Add"])
    taper_s2n4 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_dp1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer,angle=90,with_arc_floorplan=False)
    bend_dp1.connect('o1',ring0.ports["Drop"])
    taper_s2n4.connect('o1',bend_dp1.ports['o2'])
    ring.add_port('o3',port=taper_s2n3.ports['o1'])
    ring.add_port('o4',port=taper_s2n4.ports['o2'])
    # add port
    ring.add_port("RingInput", port=ring0.ports["Input"])
    for port in ring0.ports:
        if "Heat" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Add" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Drop" in port:
            ring.add_port(port, port=ring0.ports[port])
    comp_Ring = sr << ring

    # input
    tinring = sr << tin
    comp_Ring.connect("o1", other=tinring.ports["o2"], allow_width_mismatch=True,mirror=True)
    comp_Ring.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])

    # add
    tadring = sr << tin
    tadring.movey(tinring.ports['o1'].center[1]-tadring.ports['o1'].center[1]+30)
    tadring.movex( - tadring.ports['o1'].center[0])
    # drop
    tdpring = sr << tout
    tdpring.movey(comp_Ring.ports['o4'].center[1]-tdpring.ports['o1'].center[1])
    tdpring.movex(length_total-tdpring.ports['o2'].center[0])
    # through
    toutring = sr << tout
    delta = toutring.ports["o2"].center - toutring.ports["o1"].center
    toutring.connect("o1",other=comp_Ring.ports["o2"])
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("through", port=toutring.ports["o2"])
    # route
    str_tout2r = gf.routing.get_bundle([toutring.ports["o1"],comp_Ring.ports["o1"],tdpring.ports['o1']],
                                       [comp_Ring.ports["o2"],tinring.ports["o2"],comp_Ring.ports['o4']],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    str_tout2r = gf.routing.get_bundle([comp_Ring.ports["o3"]], [tadring.ports["o2"]],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    # add port

    for port in comp_Ring.ports:
        if "Heat" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Add" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Drop" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
    add_labels_to_ports(sr)
    return sr
# TCRingDouBoomerangT1: Total singleBoomerang Ring
@gf.cell
def TCRingDouBoomerangT1(
        r_ring: float = 120,
        r_euler_min: float = 100,
        r_euler_boom: float= 100,
        width_ringin: float = 1,
        width_ringout: float = 2,
        width_straight:float = 3,
        width_heat: float = 5,
        width_route: float = 20,
        width_single: float = 1,
        width_via:float = 0.5,
        length_bridge1:float = 100,
        length_bridge2:float = 100,
        length_couple:float = 10,
        length_taper: float = 150,
        length_total: float = 10000,
        length_th_horizontal: float = 10,
        length_th_vertical: float = 780,
        pos_ring: float = 700,
        gap_rr: float = 1,
        gap_rb: float = 2,
        gap_heat: float = 1,
        delta_heat: float = 20,
        delta_lb2: float = 20,
        spacing:float =1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        is_heat: bool = True,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        type_heater: str = "default",  # 控制加热器类型
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    Total Component
    创建一个环形波导组件，支持通过 position_taper 参数控制锥形波导的位置，并通过 type_heater 参数控制加热器类型。
    使用 RingPulleyT1 型的微环结构。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_euler_min: 欧拉弯曲的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        length_th_horizontal: 水平直波导的长度（单位：um）。
        length_th_vertical: 垂直直波导的长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        gap_heat: 加热器与波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        is_heat: 是否添加加热器。
        is_ad: 是否添加 Add/Drop 端口。
        oplayer: 光学层定义。
        heatlayer: 加热层定义。
        position_taper: 锥形波导的位置，支持 "before_bend"（默认）、"after_bend"、"between_bend"、"no_bend"。
        type_heater: 加热器类型，支持 "default"（默认）、"side"（侧边加热）、"bothside"（两侧加热）。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
        RingInput: 环形波导的输入端口。
        RingL: 环形波导的左侧端口。
        RingR: 环形波导的右侧端口。
    """
    sr = gf.Component()
    ring = gf.Component("Ring")
    ring0 = ring << RingDouBoomerang(
        WidthRingIn=width_ringin, WidthRingOut=width_ringout, WidthHeat=width_heat,WidthStraight=width_straight,WidthRoute=width_route,WidthVia=width_via,
        LengthTaper=length_taper,LengthBridge2=length_bridge2,LengthBridge1=length_bridge1,LengthCouple=length_couple,
        GapRR=gap_rr,GapRB=gap_rb,GapHeat=gap_heat,DeltaHeat=delta_heat,Spacing=spacing,
        RadiusRing=r_ring,RadiusEuler=r_euler_boom,DeltaLB2=delta_lb2,
        oplayer=oplayer, heatlayer=heatlayer, TypeHeater=type_heater
    )
    # input
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring0.ports["Input"])
    # through
    taper_s2n2 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_thr1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer,angle=90,with_arc_floorplan=False)
    str_th_horizontal = ring << GfCStraight(width=width_straight,length=length_th_horizontal+r_euler_boom*2+length_bridge2,layer=oplayer)
    str_th_horizontal.connect("o1", ring0.ports["Through"])
    bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
    taper_s2n2.connect("o1", other=bend_thr1.ports["o2"])
    ring.add_port("o1", port=taper_s2n1.ports["o1"])
    ring.add_port("o2", port=taper_s2n2.ports["o2"])
    # add drop
    str_ad = ring << GfCStraight(width = width_straight,length=length_bridge2,layer =oplayer)
    bend_ad = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer,angle=-90,with_arc_floorplan=False)
    taper_s2n3 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    str_ad.connect('o2',ring0.ports["Add"])
    bend_ad.connect('o2',str_ad.ports["o1"])
    taper_s2n3.connect("o2", bend_ad.ports['o1'])
    taper_s2n4 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_dp1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer,angle=-90,with_arc_floorplan=False)
    bend_dp1.connect('o1',ring0.ports["Drop"])
    taper_s2n4.connect('o1',bend_dp1.ports['o2'])
    ring.add_port('o3',port=taper_s2n3.ports['o1'])
    ring.add_port('o4',port=taper_s2n4.ports['o2'])
    # add port
    ring.add_port("RingInput", port=ring0.ports["Input"])
    for port in ring0.ports:
        if "Heat" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Add" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Drop" in port:
            ring.add_port(port, port=ring0.ports[port])
    comp_Ring = sr << ring

    # input
    tinring = sr << tin
    comp_Ring.connect("o1", other=tinring.ports["o2"], allow_width_mismatch=True,mirror=True)
    comp_Ring.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])

    # add
    tadring = sr << tin
    tadring.movey(tinring.ports['o1'].center[1]-tadring.ports['o1'].center[1]-30)
    tadring.movex( - tadring.ports['o1'].center[0])
    sr.add_port("add",port=tadring.ports['o1'])
    # drop
    tdpring = sr << tout
    tdpring.movey(comp_Ring.ports['o4'].center[1]-tdpring.ports['o1'].center[1])
    tdpring.movex(length_total-tdpring.ports['o2'].center[0])
    sr.add_port("drop", port=tdpring.ports['o2'])
    # through
    toutring = sr << tout
    toutring.movey(tdpring.ports['o1'].center[1]-toutring.ports['o1'].center[1]+30)
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("through", port=toutring.ports["o2"])
    # route
    str_tout2r = gf.routing.get_bundle([comp_Ring.ports["o1"],tdpring.ports['o1']],
                                       [tinring.ports["o2"],comp_Ring.ports['o4']],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    str_tout2r = gf.routing.get_bundle([toutring.ports["o1"]],[comp_Ring.ports["o2"]],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    str_tout2r = gf.routing.get_bundle([tadring.ports["o2"]],[comp_Ring.ports["o3"]],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    # add port

    for port in comp_Ring.ports:
        if "Heat" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Add" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Drop" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
    add_labels_to_ports(sr)
    sr.info['R1length'] = ring0.info['R1length']
    sr.info['R2length'] = ring0.info['R2length']
    return sr
# TCRingTriBoomerangT1: Total singleBoomerang Ring
@gf.cell
def TCRingTriBoomerangT1(
        r_ring: float = 120,
        r_euler_min: float = 100,
        r_euler_boom: float= 100,
        width_ringin: float = 1,
        width_ringout: float = 2,
        width_straight:float = 3,
        width_heat: float = 5,
        width_route: float = 20,
        width_single: float = 1,
        width_via:float = 0.5,
        length_bridge1:float = 100,
        length_bridge2:float = 100,
        length_couple:float = 10,
        length_taper: float = 200,
        length_total: float = 4000,
        length_th_horizontal: float = 10,
        length_th_vertical: float = 780,
        pos_ring: float = 1100,
        gap_rr: float = 1,
        gap_rb: float = 2,
        gap_heat: float = 1,
        delta_heat: float = 20,
        delta_lb2: float = 20,
        spacing:float =1,
        tin: Component = taper_in,
        tout: Component = taper_out,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        type_heater: str = "default",  # 控制加热器类型
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    Total Component
    创建一个环形波导组件，支持通过 position_taper 参数控制锥形波导的位置，并通过 type_heater 参数控制加热器类型。
    使用 RingPulleyT1 型的微环结构。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_euler_min: 欧拉弯曲的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        length_th_horizontal: 水平直波导的长度（单位：um）。
        length_th_vertical: 垂直直波导的长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        gap_heat: 加热器与波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        is_heat: 是否添加加热器。
        is_ad: 是否添加 Add/Drop 端口。
        oplayer: 光学层定义。
        heatlayer: 加热层定义。
        position_taper: 锥形波导的位置，支持 "before_bend"（默认）、"after_bend"、"between_bend"、"no_bend"。
        type_heater: 加热器类型，支持 "default"（默认）、"side"（侧边加热）、"bothside"（两侧加热）。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
        RingInput: 环形波导的输入端口。
        RingL: 环形波导的左侧端口。
        RingR: 环形波导的右侧端口。
    """
    sr = gf.Component()
    ring = gf.Component("Ring")
    ring0 = ring << RingTriBoomerang(
        WidthRingIn=width_ringin, WidthRingOut=width_ringout, WidthHeat=width_heat,WidthStraight=width_straight,WidthRoute=width_route,WidthVia=width_via,
        LengthTaper=length_taper,LengthBridge2=length_bridge2,LengthBridge1=length_bridge1,LengthCouple=length_couple,
        GapRR=gap_rr,GapRB=gap_rb,GapHeat=gap_heat,DeltaHeat=delta_heat,Spacing=spacing,
        RadiusRing=r_ring,RadiusEuler=r_euler_boom,DeltaLB2=delta_lb2,
        oplayer=oplayer, heatlayer=heatlayer, TypeHeater=type_heater
    )
    # input
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring0.ports["Input"])
    # through
    taper_s2n2 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_thr1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer,angle=-90,with_arc_floorplan=False)
    str_th_horizontal = ring << GfCStraight(width=width_straight,length=length_th_horizontal+r_euler_boom*2+length_bridge2,layer=oplayer)
    str_th_vertical = ring << GfCStraight(width=width_single, length=length_th_vertical, layer=oplayer)
    str_th_horizontal.connect("o1", ring0.ports["Through"])
    bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
    taper_s2n2.connect("o1", other=bend_thr1.ports["o2"])
    str_th_vertical.connect("o1",other=taper_s2n2.ports["o2"])
    ring.add_port("o1", port=taper_s2n1.ports["o1"])
    ring.add_port("o2", port=str_th_vertical.ports["o2"])
    # add
    taper_s2n3 = ring << gf.c.taper(width1=width_single, width2=width_straight, length=length_taper, layer=oplayer)
    taper_s2n3.connect("o2", ring0.ports["Add"])
    bend_ad = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer,angle=90,with_arc_floorplan=False)
    bend_ad.connect('o2',taper_s2n3.ports["o1"])
    ring.add_port('o3',port=bend_ad.ports['o1'])
    # drop
    str_dr = ring << GfCStraight(width=width_straight, length=length_bridge2 + 2 * r_euler_boom, layer=oplayer)
    taper_s2n4 = ring << gf.c.taper(width1=width_straight, width2=width_single, length=length_taper, layer=oplayer)
    bend_dp1 = ring << gf.c.bend_euler(width=width_straight, radius=r_euler_min, layer=oplayer,angle=90,with_arc_floorplan=False)
    str_dr.connect('o1',ring0.ports["Drop"])
    bend_dp1.connect('o1',str_dr.ports['o2'])
    taper_s2n4.connect('o1',bend_dp1.ports['o2'])
    ring.add_port('o4',port=taper_s2n4.ports['o2'])
    # add port
    ring.add_port("RingInput", port=ring0.ports["Input"])
    for port in ring0.ports:
        if "Heat" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Add" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Drop" in port:
            ring.add_port(port, port=ring0.ports[port])
    comp_Ring = sr << ring

    # port edge io
    ## input
    tinring = sr << tin
    comp_Ring.connect("o3", other=tinring.ports["o2"], allow_width_mismatch=True,mirror=True)
    comp_Ring.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])

    ## add
    tadring = sr << tin
    tadring.movey(tinring.ports['o1'].center[1]-tadring.ports['o1'].center[1]-30)
    tadring.movex( - tadring.ports['o1'].center[0])
    sr.add_port("add",port=tadring.ports['o1'])
    ## drop
    tdpring = sr << tout
    tdpring.movey(comp_Ring.ports['o2'].center[1]-tdpring.ports['o1'].center[1])
    tdpring.movex(length_total-tdpring.ports['o2'].center[0])
    sr.add_port("drop", port=tdpring.ports['o2'])
    ## through
    toutring = sr << tout
    toutring.movey(tdpring.ports['o1'].center[1]-toutring.ports['o1'].center[1]+30)
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("through", port=toutring.ports["o2"])
    # # route
    str_tout2r = gf.routing.get_bundle([toutring.ports["o1"],comp_Ring.ports["o3"],tdpring.ports['o1']],
                                       [comp_Ring.ports["o4"],tinring.ports["o2"],comp_Ring.ports['o2']],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    str_tout2r = gf.routing.get_bundle([tadring.ports["o2"]],[comp_Ring.ports["o1"]],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    # add port
    for port in comp_Ring.ports:
        if "Heat" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Add" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
        if "Drop" in port:
            sr.add_port(port, port=comp_Ring.ports[port])
    add_labels_to_ports(sr)
    sr.info['R1length'] = ring0.info['R1length']
    sr.info['R2length'] = ring0.info['R2length']
    sr.info['R3length'] = ring0.info['R3length']
    return sr
# TCRingT1: TCRing use RingPulleyT1
@gf.cell
def TCCoupleRingDRT1(
        r_ring1: float = 120,
        width_ring1: float = 1,
        width_near1: float = 2,
        width_heat1: float = 5,
        gap_rc1: float = 1,
        angle_rc1: float = 20,
        type_heater1: str = "default",  # 控制加热器类型
        gap_heat1: float = 1,
        delta_heat1: float = 1,
        r_ring2: float = None,
        width_ring2: float = None,
        width_near2: float = None,
        width_heat2: float = None,
        length_near2: float = 130,
        gap_rc2: float = 1,
        type_heater2: str = "default",  # 控制加热器类型
        gap_heat2: float = 0,
        delta_heat2: float = 0,
        gap_rr:float= 1,
        angle_rr:float = 30,
        width_single: float = 1,
        r_euler_min: float = 100,
        length_taper: float = 150,
        length_total: float = 10000,
        length_th_horizontal: float = 10,
        length_th_vertical: float = 10,
        length_ad_horizontal: float = 10,
        length_ad_vertical:float = 10,
        pos_ring: float = 500,
        tin: Component = taper_in,
        tout: Component = taper_out,
        is_heat: bool = True,
        is_ad: bool = False,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        position_taper: str = "before_bend",  # 控制锥形波导的位置

) -> Component:
    """
    创建一个环形波导组件，支持通过 position_taper 参数控制锥形波导的位置，并通过 type_heater 参数控制加热器类型。
    使用 RingPulleyT1 型的微环结构。

    参数：
        r_ring: 环形波导的半径（单位：um）。
        r_euler_min: 欧拉弯曲的半径（单位：um）。
        width_ring: 环形波导的宽度（单位：um）。
        width_near: 耦合波导的宽度（单位：um）。
        width_heat: 加热器的宽度（单位：um）。
        width_single: 输入输出波导的宽度（单位：um）。
        angle_rc: 耦合角度（单位：度）。
        length_taper: 锥形波导的长度（单位：um）。
        length_total: 总长度（单位：um）。
        length_th_horizontal: 水平直波导的长度（单位：um）。
        length_th_vertical: 垂直直波导的长度（单位：um）。
        pos_ring: 环形波导的位置（单位：um）。
        gap_rc: 耦合波导与环形波导的间距（单位：um）。
        gap_heat: 加热器与波导的间距（单位：um）。
        tin: 输入锥形波导组件。
        tout: 输出锥形波导组件。
        is_heat: 是否添加加热器。
        is_ad: 是否添加 Add/Drop 端口。
        oplayer: 光学层定义。
        heatlayer: 加热层定义。
        position_taper: 锥形波导的位置，支持 "before_bend"（默认）、"after_bend"、"between_bend"、"no_bend"。
        type_heater: 加热器类型，支持 "default"（默认）、"side"（侧边加热）、"bothside"（两侧加热）。

    返回：
        Component: 生成的环形波导组件。

    端口：
        input: 输入端口。
        output: 输出端口。
        RingC: 环形波导的中心端口。
        RingInput: 环形波导的输入端口。
        RingL: 环形波导的左侧端口。
        RingR: 环形波导的右侧端口。
    """
    sr = gf.Component()
    ring = gf.Component("Ring")
    if width_ring2 is None:
        width_ring2=width_ring1
    if width_heat2 is None:
        width_heat2=width_heat1
    if r_ring2 is None:
        r_ring2 = r_ring1
    if width_near2 is None:
        width_near2= width_near1
    S_single = gf.Section(width=width_single,layer = oplayer,port_names=['o1','o2'])
    X_single = gf.CrossSection(sections = [S_single])
    ring0 = ring << CoupleRingDRT1(
        RadiusRing1=r_ring1,WidthRing1=width_ring1, WidthNear1=width_near1, WidthHeat1=width_heat1,GapRB1=gap_rc1,DeltaHeat1=delta_heat1,
        AngleCouple1=angle_rc1,
        RadiusRing2=r_ring2, WidthRing2=width_ring2, WidthNear2=width_near2, WidthHeat2=width_heat2, GapRB2=gap_rc2,DeltaHeat2=delta_heat2,LengthNear2=length_near2,
        GapRR=gap_rr,AngleR12=angle_rr,
        TypeHeaterR1=type_heater1,TypeHeaterR2=type_heater2,GapHeat1=gap_heat1,
        IsHeat=is_heat,oplayer=oplayer, heatlayer=heatlayer,DirectionsHeater=['down','down']
    )
    # input through
    taper_s2n1 = ring << gf.c.taper(width1=width_single, width2=width_near1, length=length_taper, layer=oplayer)
    taper_s2n1.connect("o2", ring0.ports["Input"])
    taper_s2n2 = ring << gf.c.taper(width1=width_near1, width2=width_single, length=length_taper, layer=oplayer)
    ## 根据 position_taper 参数调整锥形波导的位置（input through）
    if position_taper == "before_bend":
        bend_thr1 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer,angle=90,with_arc_floorplan=False)
        bend_thr2 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer,angle=-90,with_arc_floorplan=False)
        str_th_horizontal = ring << GfCStraight(width=width_single,length=length_th_horizontal,layer=oplayer)
        str_th_vertical = ring << GfCStraight(width=width_single, length=length_th_vertical, layer=oplayer)
        taper_s2n2.connect("o1", ring0.ports["Through"])
        str_th_horizontal.connect("o1",other=taper_s2n2.ports["o2"])
        bend_thr1.connect("o1",other=str_th_horizontal.ports["o2"])
        str_th_vertical.connect("o1",other=bend_thr1.ports["o2"])
        bend_thr2.connect("o1",other=str_th_vertical.ports["o2"])
        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=bend_thr2.ports["o2"])
    elif position_taper == "after_bend":
        bend_thr1 = ring << gf.c.bend_euler(width=width_near1, radius=r_euler_min, layer=oplayer,angle=90,with_arc_floorplan=False)
        bend_thr2 = ring << gf.c.bend_euler(width=width_near1, radius=r_euler_min, layer=oplayer,angle=-90,with_arc_floorplan=False)
        str_th_horizontal = ring << GfCStraight(width=width_near1, length=length_th_horizontal, layer=oplayer)
        str_th_vertical = ring << GfCStraight(width=width_near1, length=length_th_vertical, layer=oplayer)

        str_th_horizontal.connect("o1", ring0.ports["Through"])
        bend_thr1.connect("o1",other=str_th_horizontal.ports["o2"])
        str_th_vertical.connect("o1",other=bend_thr1.ports["o2"])
        bend_thr2.connect("o1",other=str_th_vertical.ports["o2"])
        taper_s2n2.connect("o1",other=bend_thr2.ports["o2"])

        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=taper_s2n2.ports["o2"])
    elif position_taper == "between_bend":
        bend_thr1 = ring << gf.c.bend_euler(width=width_near1, radius=r_euler_min, layer=oplayer,angle=90,with_arc_floorplan=False)
        bend_thr2 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer,angle=-90,with_arc_floorplan=False)
        str_th_horizontal = ring << GfCStraight(width=width_near1,length=length_th_horizontal,layer=oplayer)
        str_th_vertical = ring << GfCStraight(width=width_single, length=length_th_vertical, layer=oplayer)
        str_th_horizontal.connect("o1", ring0.ports["Through"])
        bend_thr1.connect("o1", other=str_th_horizontal.ports["o2"])
        taper_s2n2.connect("o1", other=bend_thr1.ports["o2"])
        str_th_vertical.connect("o1",other=taper_s2n2.ports["o2"])
        bend_thr2.connect("o1",other=str_th_vertical.ports["o2"])
        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=bend_thr2.ports["o2"])
    elif position_taper == "no_bend":
        taper_s2n2.connect("o1",other=ring0.ports["Through"])
        ring.add_port("o1", port=taper_s2n1.ports["o1"])
        ring.add_port("o2", port=taper_s2n2.ports["o2"])
    else:
        raise ValueError("position_taper 必须是 'before_bend' 或 'after_bend' 或 'between_bend' 或 'no_bend'")
    # add drop
    taper_s2n3 = ring << gf.c.taper(width1=width_single, width2=width_near2, length=length_taper, layer=oplayer)
    taper_s2n4 = ring << gf.c.taper(width1=width_near2, width2=width_single, length=length_taper, layer=oplayer)
    taper_s2n4.connect("o1",ring0.ports["Add"])
    ## add drop bend out
    bend_ad1 = ring << gf.c.bend_euler(width=width_near2, radius=r_euler_min, layer=oplayer, angle=-90,
                                        with_arc_floorplan=False)
    bend_ad2 = ring << gf.c.bend_euler(width=width_single, radius=r_euler_min, layer=oplayer, angle=90,
                                        with_arc_floorplan=False)
    str_ad = ring << GfCStraight(width=width_single,length=length_ad_vertical,layer=oplayer)
    str_ad0 = ring << GfCStraight(width=width_near2,length=length_ad_horizontal,layer=oplayer)
    str_ad0.connect("o2", other=ring0.ports["Drop"])
    bend_ad1.connect("o2", other=str_ad0.ports["o1"])
    taper_s2n3.connect("o2", other=bend_ad1.ports["o1"])
    str_ad.connect("o2", other=taper_s2n3.ports["o1"])
    bend_ad2.connect("o2", other=str_ad.ports["o1"])
    ring.add_port("o3", port=taper_s2n4.ports["o2"])
    ring.add_port("o4", port=bend_ad2.ports["o1"])
    ring.add_port("RingInput", port=ring0.ports["Input"])
    ring.add_port("Ring1C", port=ring0.ports["Ring1C"])
    ring.add_port("Ring2C", port=ring0.ports["Ring2C"])
    for port in ring0.ports:
        if "Heat" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Add" in port:
            ring.add_port(port, port=ring0.ports[port])
        if "Drop" in port:
            ring.add_port(port, port=ring0.ports[port])
    # add_labels_to_ports(ring,(412,8))
    CCRing = sr << ring

    ## input
    tinring = sr << tin
    CCRing.connect("o1", other=tinring.ports["o2"], allow_width_mismatch=True,mirror=True)
    CCRing.movex(pos_ring)
    sr.add_port("input", port=tinring.ports["o1"])
    ## add
    tadring = sr << tin
    tadring.connect('o2',CCRing.ports['o4'])
    tadring.movex(tinring.ports['o1'].center[0]-tadring.ports['o1'].center[0])
    sr.add_port("add", port=tadring.ports["o1"])
    ## output
    toutring = sr << tout
    toutring.connect("o1",other=CCRing.ports["o2"])
    toutring.movex(length_total - toutring.ports["o2"].center[0])
    sr.add_port("output", port=toutring.ports["o2"])
    ## drop
    tdpring = sr << tout
    tdpring.movey(-tdpring.ports['o1'].center[1]+CCRing.ports["o3"].center[1])
    tdpring.movex(length_total - tdpring.ports["o2"].center[0])
    bend_s_dp = sr << gf.c.bend_s(cross_section=X_single,size = [10,0])
    bend_s_dp.connect("o1",other=CCRing.ports["o3"])
    sr.add_port("drop", port=tdpring.ports["o2"])
    ## route
    str_tout2r = gf.routing.get_bundle([toutring.ports["o1"],CCRing.ports["o1"],tdpring.ports['o1'],CCRing.ports["o4"]],
                                       [CCRing.ports["o2"],tinring.ports["o2"],bend_s_dp.ports["o2"],tadring.ports['o2']],
                                       layer=oplayer, width=width_single, radius=r_euler_min)
    for route in str_tout2r:
        sr.add(route.references)
    sr.add_port("Ring1C", port=CCRing.ports["Ring1C"])
    sr.add_port("Ring2C", port=CCRing.ports["Ring2C"])

    for port in CCRing.ports:
        if "Heat" in port:
            sr.add_port(port, port=CCRing.ports[port])
        if "Add" in port:
            sr.add_port(port, port=CCRing.ports[port])
        if "Drop" in port:
            sr.add_port(port, port=CCRing.ports[port])
    # add_labels_to_ports(ring, (612, 8))
    return sr
__all__=['TCRingBoomerangT1','TCRingDouBoomerangT1','TCRingTriBoomerangT1','TCCoupleRingDRT1']