from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from .BasicDefine import *
from .SnapMerge import *

def SnakeHeater(
        WidthHeat: float = 8,
        WidthWG: float = 2,
        GapHeat: float = 1,
        PathHeat: Path = None,
        PortName: list[str] = ["o1", "o2"],
        heatlayer: LayerSpec = LAYER.M1,
) -> Component:
    """
    创建一个蛇形（或梳状）加热器。
    该加热器通过在一个较宽的加热条上周期性地移除材料条（“切割”）来形成蛇形路径，
    从而增加电流路径长度，提高加热效率。

    参数:
        WidthHeat (float): 主加热条的宽度 (单位: µm)。
        WidthWG (float): 被加热波导的宽度 (单位: µm)。此参数与 `GapHeat` 一起用于定义
                         蛇形结构中周期性移除部分的几何形状。移除部分的长度通常为
                         `(WidthHeat - WidthWG) / 2` （每一边）。
        GapHeat (float): 蛇形结构中“切割”部分的宽度，即周期性移除的材料条的宽度 (单位: µm)。
        PathHeat (Path | None): 定义加热器中心线走向的 gdsfactory.path.Path 对象。
                                如果为None，则需要在使用此函数前提供一个有效的Path对象。
        PortName (list[str]): 包含两个字符串的列表，用于定义加热器输出端口的名称。
                              默认为 ["o1", "o2"]。
        heatlayer (LayerSpec): 加热器所在的GDS图层。

    返回:
        Component: 生成的蛇形加热器组件。

    端口:
        根据 `PortName` 定义的两个端口，通常是加热器的电极连接点。
    """
    h = gf.Component()
    # section and crosssection
    S_heat = gf.Section(width=WidthHeat, offset=0, layer=heatlayer, port_names=(PortName[0], PortName[1]))
    S_test = gf.Section(width=1, offset=0, layer=(1, 100), port_names=(PortName[0], PortName[1]))
    CAP_Rin_comp = gf.Component()
    CAP_R0 = CAP_Rin_comp << GfCStraight(width=GapHeat, length=WidthHeat - WidthWG, layer=(1, 10))
    CAP_R0.rotate(90).movey(WidthWG / 2)
    CAP_Rout_comp = gf.Component()
    CAP_R1 = CAP_Rout_comp << GfCStraight(width=GapHeat, length=WidthHeat - WidthWG, layer=(1, 10))
    CAP_R1.rotate(90).movey(-(WidthHeat - WidthWG) - WidthWG / 2)
    via = gf.cross_section.ComponentAlongPath(
        component=gf.c.rectangle(size=(1, 1), centered=True), spacing=5, padding=2
    )
    CAP_Rin = gf.cross_section.ComponentAlongPath(component=CAP_Rout_comp, spacing=WidthHeat + GapHeat,
                                                  padding=WidthHeat + GapHeat / 2)
    CAP_Rout = gf.cross_section.ComponentAlongPath(component=CAP_Rin_comp, spacing=WidthHeat + GapHeat,
                                                   padding=WidthHeat / 2)
    # Cross-Section
    CS_RnoH = gf.CrossSection(components_along_path=(CAP_Rin, CAP_Rout), sections=(S_test,))
    CS_Heat = gf.CrossSection(sections=(S_heat,))
    # heat component
    Hp = gf.Component()
    Hm = gf.Component()
    HSn = gf.Component()
    Hp1 = Hp << gf.path.extrude(PathHeat, cross_section=CS_Heat)
    Hm1 = Hm << gf.path.extrude(PathHeat, cross_section=CS_RnoH)
    HSn = h << gf.boolean(A=Hp, B=Hm, operation="not", layer1=heatlayer, layer2=(1, 10), layer=heatlayer)
    h.add_port(PortName[0], port=Hp1.ports[PortName[0]])
    h.add_port(PortName[1], port=Hp1.ports[PortName[1]])
    return h


# %% different heater
@gf.cell
def DifferentHeater(
        PathHeat: Path = None,
        WidthHeat: float = 4,
        WidthWG: float = 1,
        WidthRoute: float = 10,
        WidthVia: float = 0.26,
        Spacing: float = 1.1,
        DeltaHeat: float = 2,
        GapHeat: float = 3,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        TypeHeater: str = "default",
        **kwargs
) -> Component:
    """
    根据指定的类型和其他参数，生成不同类型的加热器组件。

    参数:
        PathHeat (Path | None): 定义加热器中心线的 gdsfactory.path.Path 对象。
        WidthHeat (float): 主加热条的宽度 (单位: µm)。
        WidthWG (float): （仅用于'snake'类型）波导宽度，用于计算蛇形切割的几何形状 (单位: µm)。
        WidthRoute (float): （仅用于'spilt'类型）金属布线臂的宽度 (单位: µm)。
        WidthVia (float): （仅用于'spilt'类型）过孔的边长 (假设为正方形过孔) (单位: µm)。
        Spacing (float): （仅用于'spilt'类型）过孔阵列中过孔的中心间距 (单位: µm)。
        DeltaHeat (float): 几何偏移或长度参数 (单位: µm)。
                           对于 "side"/"bothside": 加热条中心相对于PathHeat的横向偏移。
                           对于 "spilt": 连接主加热条和布线臂的短臂长度。
        GapHeat (float): 几何间隙参数 (单位: µm)。
                         对于 "snake": 蛇形切割部分的宽度。
                         对于 "spilt": 沿路径的布线段之间的间隙，或用于ViaArray的Enclosure。
        heatlayer (LayerSpec): 定义加热器主要部分所在的GDS图层。
        routelayer (LayerSpec): （仅用于'spilt'类型）定义金属布线臂所在的GDS图层。
        vialayer (LayerSpec): （仅用于'spilt'类型）定义过孔所在的GDS图层。
        TypeHeater (str): 指定加热器的类型。可选值包括:
            - "default": 沿PathHeat拉伸的简单直线型加热器。
            - "snake": 蛇形加热器 (调用 SnakeHeater 组件)。
            - "side": 单侧加热器，加热条位于PathHeat的一侧。
            - "bothside": 双侧对称加热器，加热条位于PathHeat的两侧。
            - "spilt": 分裂型加热器，包含主加热区和通过过孔连接的独立布线臂。
            - "None" 或 "none": 不生成加热器，返回空组件。
        **kwargs: 传递给底层 gdsfactory 组件或函数的额外参数。

    返回:
        gf.Component: 生成的加热器组件。

    异常:
        ValueError: 如果提供了无效的 TypeHeater 类型或 PathHeat 为 None。

    端口 (不同类型加热器的主要端口):
        - "default", "snake", "side":
            - "HeatIn": 加热器电学输入端。
            - "HeatOut": 加热器电学输出端。
        - "bothside":
            - "HeatLIn", "HeatLOut": 左侧加热条的电学输入/输出。
            - "HeatRIn", "HeatROut": 右侧加热条的电学输入/输出。
            - "HeatIn", "HeatOut": (复合端口) 代表整体的输入/输出。
        - "spilt":
            - "HeatLIn", "HeatLOut": 左侧布线臂的电学输入/输出。
            - "HeatRIn", "HeatROut": 右侧布线臂的电学输入/输出。
            - "HeatIn", "HeatOut": 主加热区域（中心条）的（概念性）输入/输出。
    """
    h = gf.Component()
    if TypeHeater == "default":
        # 默认加热电极
        heatL_comp1 = h << gf.path.extrude(PathHeat, width=WidthHeat, layer=heatlayer)  # 创建左侧加热电极
        h.add_port(name="HeatIn", port=heatL_comp1.ports["o1"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=heatL_comp1.ports["o2"])  # 添加加热输出端口
    elif TypeHeater == "snake":
        # 蛇形加热电极
        HPart = h << SnakeHeater(WidthHeat, WidthWG, GapHeat, PathHeat, ["o1", "o2"], heatlayer)
        h.add_port(name="HeatIn", port=HPart.ports["o2"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=HPart.ports["o2"])  # 添加加热输出端口
    elif TypeHeater == "side":
        # 侧边加热电极
        section1 = gf.Section(width=WidthHeat, offset=DeltaHeat, layer=heatlayer, port_names=("Uo1", "Uo2"))
        section2 = gf.Section(width=WidthHeat, offset=-DeltaHeat, layer=heatlayer, port_names=("Do1", "Do2"))
        CrossSection = gf.CrossSection(sections=[section1])
        HPart = h << gf.path.extrude(PathHeat, cross_section=CrossSection)  # 创建左侧加热电极
        h.add_port(name="HeatIn", port=HPart.ports["Uo1"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=HPart.ports["Uo2"])  # 添加加热输出端口
    elif TypeHeater == "bothside":
        DeltaHeat = abs(DeltaHeat)
        # 两侧边加热电极
        section1 = gf.Section(width=WidthHeat, offset=DeltaHeat, layer=heatlayer, port_names=("Uo1", "Uo2"))
        section2 = gf.Section(width=WidthHeat, offset=-DeltaHeat, layer=heatlayer, port_names=("Do1", "Do2"))
        CrossSection = gf.CrossSection(sections=[section1, section2])
        HPart = h << gf.path.extrude(PathHeat, cross_section=CrossSection)  # 创建左侧加热电极
        h.add_port(name="HeatLIn", port=HPart.ports["Uo1"])  # 添加加热输入端口
        h.add_port(name="HeatLOut", port=HPart.ports["Uo2"])  # 添加加热输出端口
        h.add_port(name="HeatRIn", port=HPart.ports["Do1"])  # 添加加热输入端口
        h.add_port(name="HeatROut", port=HPart.ports["Do2"])  # 添加加热输出端口
        h.add_port(name="HeatIn", port=HPart.ports["o1"],
                   center=np.array(h.ports["HeatLIn"].center) / 2 + np.array(h.ports["HeatRIn"].center / 2))  # 添加加热输入端口
        h.add_port(name="HeatOut", port=HPart.ports["o2"],
                   center=np.array(h.ports["HeatLOut"].center) / 2 + np.array(h.ports["HeatROut"].center / 2))  # 添加加热输出端口
    elif TypeHeater == "spilt":
        # section and crosssection
        n_pieces = np.floor((PathHeat.length()) / (WidthRoute + GapHeat))
        GapHeat = (PathHeat.length() - WidthRoute * (n_pieces + 1)) / n_pieces - 0.5
        S_heat = gf.Section(width=WidthHeat, offset=0, layer=heatlayer, port_names=("o1", "o2"))
        S_route1 = gf.Section(width=WidthRoute, offset=DeltaHeat, layer=routelayer, port_names=("r1o1", "r1o2"))
        S_route2 = gf.Section(width=WidthRoute, offset=-(DeltaHeat), layer=routelayer, port_names=("r2o1", "r2o2"))
        S_hmid = gf.Section(width=0, layer=(512, 8))
        CAP_Rin_comp = gf.Component()
        CAP_H0 = CAP_Rin_comp << GfCStraight(width=WidthRoute, length=DeltaHeat, layer=heatlayer)
        CAP_R0 = CAP_Rin_comp << GfCStraight(width=WidthRoute, length=DeltaHeat, layer=routelayer)
        CAP_H0.rotate(90, CAP_H0.ports["o1"].center)
        CAP_R0.rotate(90, CAP_R0.ports["o1"].center)
        CAP_Rout = gf.cross_section.ComponentAlongPath(component=CAP_Rin_comp, spacing=2 * (WidthRoute + GapHeat),
                                                       padding=WidthRoute + GapHeat,
                                                       offset=(- 0.3))
        CAP_Rout_comp = gf.Component()
        CAP_H1 = CAP_Rout_comp << GfCStraight(width=WidthRoute, length=DeltaHeat, layer=heatlayer)
        CAP_R1 = CAP_Rout_comp << GfCStraight(width=WidthRoute, length=DeltaHeat, layer=routelayer)
        CAP_R1.rotate(-90, CAP_R1.ports["o1"].center)
        CAP_H1.rotate(-90, CAP_H1.ports["o1"].center)
        CAP_Rin = gf.cross_section.ComponentAlongPath(component=CAP_Rout_comp, spacing=2 * (WidthRoute + GapHeat),
                                                      padding=0, offset=(+ 0.3))

        ## Cross-Section
        X_RnoH = gf.CrossSection(components_along_path=[CAP_Rout, CAP_Rin], sections=(S_hmid,))
        X_Heat = gf.CrossSection(sections=[S_heat, S_route1, S_route2])
        # heat component
        Hp1 = h << gf.path.extrude(PathHeat, cross_section=X_Heat)
        Hc1 = gf.path.extrude(PathHeat, cross_section=X_RnoH)
        Hvia = h << ViaArray(Hc1, WidthVia=WidthVia, Spacing=Spacing, vialayer=vialayer, arraylayer=heatlayer)
        h << Hc1
        h.add_port(name="HeatLIn", port=Hp1.ports["r1o1"])  # 添加加热输入端口
        h.add_port(name="HeatLOut", port=Hp1.ports["r1o2"])  # 添加加热输出端口
        h.add_port(name="HeatRIn", port=Hp1.ports["r2o1"])  # 添加加热输入端口
        h.add_port(name="HeatROut", port=Hp1.ports["r2o2"])  # 添加加热输出端口
        h.add_port(name="HeatIn", port=Hp1.ports["o1"])  # 添加加热输入端口
        h.add_port(name="HeatOut", port=Hp1.ports["o2"])  # 添加加热输出端口
    elif TypeHeater == "None" or TypeHeater == "none":
        return h
    else:
        raise ValueError(
            "no Heater Type"
        )
    h.add_port(name="o1", port=h.ports["HeatIn"])  # 添加加热输入端口
    h.add_port(name="o2", port=h.ports["HeatOut"])  # 添加加热输入端口
    h = snap_all_polygons_iteratively(h,grid_size=0.001)
    return h


# %% ViaArray (Optimized)
@gf.cell
def ViaArray(
        CompEn: Component,
        WidthVia: float = 0.5,
        Spacing: float = 1.1,
        Enclosure: float = 2,
        arraylayer: LayerSpec = None,
        vialayer: gf.typings.LayerSpec = LAYER.VIA,
) -> Component:
    """
    在给定组件 (`CompEn`) 的指定图层 (`arraylayer`) 形成的区域内，
    根据内缩值 (`Enclosure`)，高效地生成一个过孔阵列。
    过孔将填充处理后的区域。

    参数:
        CompEn (Component): 源组件，其在 `arraylayer` 上的几何形状定义了过孔阵列的外部边界。
        WidthVia (float): 单个过孔的边长（假设为正方形过孔）(单位: µm)。
        Spacing (float): 过孔之间的中心到中心间距 (单位: µm)。
        Enclosure (float): 从 `CompEn` 在 `arraylayer` 上的几何边界向内缩进的距离 (单位: µm)。
                           过孔将被放置在这个缩进后的区域内。
        arraylayer (LayerSpec | None): `CompEn` 组件中用于定义边界的图层。
                                     如果为 None，则函数会尝试使用 `CompEn` 的整体轮廓或其包含的第一个图层。
                                     推荐明确指定此图层。
        vialayer (LayerSpec): 生成的过孔所在的GDS图层。默认为 `LAYER.VIA`。

    返回:
        Component: 包含生成的过孔阵列的新组件。

    注意:
        - 此函数使用 `shapely` 库进行几何运算。
        - "关键优化" 注释表明此实现旨在提高效率。
        - 如果 `arraylayer` 未指定或 `CompEn` 在该层上没有几何图形，可能不会生成过孔。
    """
    via_array = gf.Component()
    B = gf.Component()
    via = GfCStraight(width=WidthVia, length=WidthVia, layer=vialayer)
    viabox = via.bbox()
    # ========== 关键优化1：预处理目标区域 ==========
    # 获取内缩后的几何区域
    B0 = CompEn.copy()
    Br = B0.get_region(layer=arraylayer)
    Br.size(-Enclosure * 1000)
    B.add_polygon(Br, layer=arraylayer)
    # B.show()
    # B.offset(layer=arraylayer,distance=-Enclosure)
    b_polys = B.get_polygons_points(merge=True)
    for poly in b_polys[arraylayer]:
        # shape=Polygon(poly)
        # b_shapely = poly
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
                # via_ref = via_array << via
                # via_ref.movex(x)
                # via_ref.movey(y)
                # bbox = via_ref.bbox()
                a_shapely = box(viabox.left + x, viabox.bottom + y, viabox.right + x, viabox.top + y)
                # 检查是否完全在B内部
                if b_shapely.contains(a_shapely):
                    via_ref = via_array << via
                    via_ref.movex(x)
                    via_ref.movey(y)
    return via_array


__all__ = ['SnakeHeater', 'ViaArray', 'DifferentHeater']
