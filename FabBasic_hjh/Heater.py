import gdsfactory as gf
import numpy as np
import csv
from gdsfactory.typings import Layer
from gdsfactory.component import Component
from gdsfactory.path import Path, _fresnel, _rotate_points
from gdsfactory.typings import LayerSpec
from gdsfactory.typings import Layer, LayerSpec, LayerSpecs ,Optional, Callable
from shapely.geometry import Polygon, box
from shapely.prepared import prep
from shapely.ops import unary_union
from .BasicDefine import add_labels_to_ports,add_labels_decorator,Crossing_taper,TaperRsoa,cir2end,euler_Bend_Half,TWQRcode,LAYER,r_euler_true,r_euler_false


def SnakeHeater(
        WidthHeat:float = 8,
        WidthWG: float = 2,
        GapHeat:float = 1,
        PathHeat:Path = None,
        PortName:list[str] = ["o1","o2"],
        heatlayer:LayerSpec = LAYER.M1,
)->Component:
    h = gf.Component()
    # section and crosssection
    S_heat = gf.Section(width=WidthHeat, offset=0, layer=heatlayer, port_names=(PortName[0], PortName[1]))
    CAP_Rin_comp = gf.Component()
    CAP_R0 = CAP_Rin_comp << gf.c.straight(width=GapHeat, length=WidthHeat - WidthWG, layer=(1, 10))
    CAP_R0.rotate(90).movey(WidthWG / 2)
    CAP_Rout_comp = gf.Component()
    CAP_R1 = CAP_Rout_comp << gf.c.straight(width=GapHeat, length=WidthHeat - WidthWG, layer=(1, 10))
    CAP_R1.rotate(90).movey(-(WidthHeat - WidthWG) - WidthWG / 2)
    CAP_Rin = gf.cross_section.ComponentAlongPath(component=CAP_Rout_comp, spacing=WidthHeat + GapHeat,
                                                  padding=WidthHeat + GapHeat / 2)
    CAP_Rout = gf.cross_section.ComponentAlongPath(component=CAP_Rin_comp, spacing=WidthHeat + GapHeat,
                                                   padding=WidthHeat / 2)
    # Cross-Section
    CS_RnoH = gf.CrossSection(components_along_path=[CAP_Rin, CAP_Rout])
    CS_Heat = gf.CrossSection(sections=[S_heat])
    #heat component
    Hp = gf.Component("HL" )
    Hm = gf.Component("HL2")
    HSn = gf.Component("HPart")
    Hp1 = Hp << gf.path.extrude(PathHeat, cross_section=CS_Heat)
    Hm1 = Hm << gf.path.extrude(PathHeat, cross_section=CS_RnoH)
    HSn = h << gf.geometry.boolean(A=Hp, B=Hm, operation="not", layer=heatlayer)
    h.add_port(PortName[0], port=Hp1.ports[PortName[0]])
    h.add_port(PortName[1], port=Hp1.ports[PortName[1]])
    return h
# %% different heater
@gf.cell
def DifferentHeater(
        PathHeat:Path = None,
        WidthHeat:float = 4,
        WidthWG: float = 1,
        WidthRoute: float = 10,
        WidthVia: float = 0.5,
        Spacing: float = 1.1,
        DeltaHeat: float = 2,
        GapHeat: float = 3,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        TypeHeater: str = "default",
        **kwargs
)->Component:
    h = gf.Component("Heater")
    if TypeHeater == "default":
        # 默认加热电极
        heatL_comp1 = h << gf.path.extrude(PathHeat, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        h.add_port(name="HeatIn", port=heatL_comp1.ports["o1"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=heatL_comp1.ports["o2"])  # 添加加热输出端口
    elif TypeHeater == "snake":
        # 蛇形加热电极
        HPart = h << SnakeHeater(WidthHeat, WidthWG, GapHeat, PathHeat, ["o1", "o2"],heatlayer)
        h.add_port(name="HeatIn", port=HPart.ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=HPart.ports["o2"])  # 添加加热输出端口
    elif TypeHeater == "side":
        # 侧边加热电极
        section1 = h << gf.Section(width=WidthHeat, offset=DeltaHeat, layer=heatlayer, port_names=("Uo1", "Uo2"))
        section2 = h << gf.Section(width=WidthHeat, offset=-DeltaHeat, layer=heatlayer, port_names=("Do1", "Do2"))
        CrossSection = gf.CrossSection(sections = [section1])
        HPart = h << gf.path.extrude(PathHeat,cross_section=CrossSection)  # 创建左侧加热电极
        h.add_port(name="HeatIn", port=HPart.ports["Uo1"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=HPart.ports["Uo2"])  # 添加加热输出端口
    elif TypeHeater == "bothside":
        GapHeat = abs(GapHeat)
        # 两侧边加热电极
        section1 = h << gf.Section(width=WidthHeat, offset=DeltaHeat, layer=heatlayer, port_names=("Uo1", "Uo2"))
        section2 = h << gf.Section(width=WidthHeat, offset=-DeltaHeat, layer=heatlayer, port_names=("Do1", "Do2"))
        CrossSection = gf.CrossSection(sections = [section1, section2])
        HPart = h << gf.path.extrude(PathHeat,cross_section=CrossSection)  # 创建左侧加热电极
        h.add_port(name="HeatLIn", port=HPart.ports["Uo1"])  # 添加加热输入端口
        h.add_port(name="HeatLOut", port=HPart.ports["Uo2"])  # 添加加热输出端口
        h.add_port(name="HeatRIn", port=HPart.ports["Do1"])  # 添加加热输入端口
        h.add_port(name="HeatROut", port=HPart.ports["Do2"])  # 添加加热输出端口
        h.add_port(name="HeatIn", port=HPart.ports["o1"],center=h.ports["HeatLIn"].center/2+h.ports["HeatRIn"].center/2)  # 添加加热输入端口
        h.add_port(name="HeatOut", port=HPart.ports["o2"],center=h.ports["HeatLOut"].center/2+h.ports["HeatROut"].center/2)  # 添加加热输出端口
    elif TypeHeater == "spilt":
        # section and crosssection
        n_pieces = np.floor((PathHeat.length())/(WidthRoute+GapHeat))
        GapHeat = (PathHeat.length()-WidthRoute*(n_pieces+1))/n_pieces-0.5
        S_heat = gf.Section(width=WidthHeat, offset=0, layer=heatlayer, port_names=("o1", "o2"))
        S_route1 = gf.Section(width=WidthRoute, offset=DeltaHeat, layer=routelayer, port_names=("r1o1", "r1o2"))
        S_route2 = gf.Section(width=WidthRoute, offset=-(DeltaHeat), layer=routelayer, port_names=("r2o1", "r2o2"))
        CAP_Rin_comp = gf.Component()
        CAP_H0 = CAP_Rin_comp << gf.c.straight(width=WidthRoute, length=DeltaHeat, layer=heatlayer)
        CAP_R0 = CAP_Rin_comp << gf.c.straight(width=WidthRoute, length=DeltaHeat, layer=routelayer)
        CAP_H0.rotate(90).movey(-WidthHeat / 2+0.3)
        CAP_R0.rotate(90).movey(-WidthHeat / 2+0.3)
        CAP_Rout_comp = gf.Component()
        CAP_H1 = CAP_Rout_comp << gf.c.straight(width=WidthRoute, length=DeltaHeat, layer=heatlayer)
        CAP_R1 = CAP_Rout_comp << gf.c.straight(width=WidthRoute, length=DeltaHeat, layer=routelayer)
        CAP_R1.rotate(-90).movey(WidthHeat / 2-0.3)
        CAP_H1.rotate(-90).movey(WidthHeat / 2-0.3)
        CAP_Rin = gf.cross_section.ComponentAlongPath(component=CAP_Rout_comp, spacing=2*(WidthRoute + GapHeat),padding=0)
        CAP_Rout = gf.cross_section.ComponentAlongPath(component=CAP_Rin_comp, spacing=2*(WidthRoute + GapHeat),padding=WidthRoute+GapHeat)
        ## Cross-Section
        X_RnoH = gf.CrossSection(components_along_path=[CAP_Rin,CAP_Rout])
        X_Heat = gf.CrossSection(sections=[S_heat,S_route1,S_route2])
        # heat component
        Hp1 = h << gf.path.extrude(PathHeat, cross_section=X_Heat)
        Hhvr = gf.Component("Heat hvr")
        Hc1 =  gf.path.extrude(PathHeat, cross_section=X_RnoH)
        Hvia = h << ViaArray(Hc1,WidthVia=WidthVia,Spacing=Spacing,vialayer=vialayer)
        h << Hc1
        h.add_port(name="HeatLIn", port=Hp1.ports["r1o1"])  # 添加加热输入端口
        h.add_port(name="HeatLOut", port=Hp1.ports["r1o2"])  # 添加加热输出端口
        h.add_port(name="HeatRIn", port=Hp1.ports["r2o1"])  # 添加加热输入端口
        h.add_port(name="HeatROut", port=Hp1.ports["r2o2"])  # 添加加热输出端口
        h.add_port(name="HeatIn", port=Hp1.ports["o1"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=Hp1.ports["o2"])  # 添加加热输出端口
    else:
        raise ValueError(
            "no Heater Type"
        )
    return h


# %% ViaArray (Optimized)
@gf.cell
def ViaArray(
        CompEn: Component,
        WidthVia: float = 0.5,
        Spacing: float = 1.1,
        Enclosure: float = 0.8,
        vialayer: gf.typings.LayerSpec = LAYER.VIA,
) -> Component:
    '''
    高效实现CompEn内部覆盖通孔阵列
    '''
    via_array = gf.Component("ViaArray")
    via = gf.c.straight(width=WidthVia, length=WidthVia, layer=vialayer)
    # ========== 关键优化1：预处理目标区域 ==========
    # 获取内缩后的几何区域
    B = gf.geometry.offset(CompEn, distance=-Enclosure)
    b_polys = B.get_polygons()
    for poly in b_polys:
        b_shapely = unary_union([Polygon(poly)])
        # ========== 关键优化2：动态计算网格范围 ==========
        # 获取B的有效区域边界
        min_x, min_y, max_x, max_y = b_shapely.bounds
        via_size = WidthVia
        # 计算实际需要的行列数（替代固定Num参数）
        cols = int((max_x - min_x - via_size) // Spacing) + 5
        rows = int((max_y - min_y - via_size) // Spacing) + 5
        # 生成所有候选中心坐标
        x_centers = min_x + via_size / 2 + Spacing * np.arange(cols)
        y_centers = min_y + via_size / 2 + Spacing * np.arange(rows)
        # 生成通孔阵列
        for x in x_centers:
            for y in y_centers:
                via_ref = via_array << via
                via_ref.movex(x)
                via_ref.movey(y)
                a_polys = via_ref.get_polygons()
                a_shapely = unary_union([Polygon(p) for p in a_polys])
                # 检查是否完全在B内部
                if not b_shapely.contains(a_shapely):
                    via_array.remove(via_ref)  # 删除不满足条件的实例
    return via_array

__all__=['SnakeHeater','ViaArray','DifferentHeater']