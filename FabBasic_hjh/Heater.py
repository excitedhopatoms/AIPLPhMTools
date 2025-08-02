from .BasicDefine import *
from .SnapMerge import *
from shapely.ops import unary_union
from shapely.affinity import translate
import numpy as np
from shapely.geometry import Polygon, MultiPoint, box
from joblib import Parallel, delayed,cpu_count
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
    # h = snap_all_polygons_iteratively(h)
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
    b_polys = B.get_polygons_points(by='tuple')
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

# 并行优化版本的ViaArray
@gf.cell
def ViaArrayParallel(
        CompEn: Component,
        WidthVia: float = 0.5,
        Spacing: float = 1.1,
        Enclosure: float = 2,
        arraylayer: LayerSpec = None,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    在给定组件 (`CompEn`) 的指定图层 (`arraylayer`) 形成的区域内，
    根据内缩值 (`Enclosure`)，高效地生成一个过孔阵列（并行优化版）。

    参数说明见原始文档。
    """

    via_array = gf.Component()
    B = gf.Component()
    Cw = gf.Section(width=WidthVia,layer=vialayer)
    Xw = gf.CrossSection(sections=(Cw,))
    via = gf.components.straight(length=WidthVia,cross_section=Xw)
    viabox = via.bbox()

    # ========== 关键优化1：预处理目标区域 ==========
    B0 = CompEn.copy()
    Br = B0.get_region(layer=arraylayer)
    Br.size(-Enclosure * 1000)
    B.add_polygon(Br, layer=arraylayer)
    b_polys = B.get_polygons_points(by='tuple')

    if arraylayer not in b_polys or not b_polys[arraylayer]:
        return via_array


    # 合并所有 polygon 为 shapely 区域
    b_shapely = unary_union([Polygon(poly) for poly in b_polys[arraylayer]])
    if b_shapely.is_empty:
        return via_array

    # 预生成单个 via 形状（基于 0 原点）
    via_shape = box(viabox.left, viabox.bottom, viabox.right, viabox.top)

    # 计算布孔区域边界 + 网格坐标
    min_x, min_y, max_x, max_y = b_shapely.bounds
    cols = int((max_x - min_x - WidthVia) // Spacing) + 5
    rows = int((max_y - min_y - WidthVia) // Spacing) + 5
    x_centers = min_x + WidthVia / 2 + Spacing * np.arange(cols)
    y_centers = min_y + WidthVia / 2 + Spacing * np.arange(rows)

    # 将 candidate 点转换为 numpy 坐标对
    candidates = np.array(np.meshgrid(x_centers, y_centers)).reshape(2, -1).T

    # 提取目标区域 bounding box，用于快速预筛
    bminx, bminy, bmaxx, bmaxy = b_shapely.bounds

    def is_inside_fast(x, y):
        # 粗筛：如果完全在 bounding box 外，则跳过
        if not (bminx <= x <= bmaxx and bminy <= y <= bmaxy):
            return None
        # 精筛：实际形状是否包含该 via
        via_moved = translate(via_shape, xoff=x, yoff=y)
        if b_shapely.contains(via_moved):
            return (x, y)
        return None

    # 并行判断 + 筛选合法位置
    # valid_coords = Parallel(n_jobs=-1, backend="threading")(
    #     delayed(is_inside_fast)(x, y) for x, y in candidates
    # )
    # valid_coords = [c for c in valid_coords if c is not None]
    # =================== 优化后的批处理并行计算 ===================

    # 1. 定义一个处理“一批”候选点的函数
    def process_batch(candidate_batch, b_shapely, via_shape):
        """
        处理一个批次的候选点，返回该批次中所有有效的坐标。
        这个函数将在并行进程中执行。
        """
        # 预提取目标区域的边界，避免在循环中重复调用
        bminx, bminy, bmaxx, bmaxy = b_shapely.bounds

        # 预提取 via 形状的相对边界
        via_b_left, via_b_bottom, via_b_right, via_b_top = via_shape.bounds

        valid_coords_in_batch = []
        for x, y in candidate_batch:
            # 2. 快速边界框预筛选 (Coarse Bounding Box Check)
            # 检查移动后的 via 的边界框是否完全在目标区域的边界框内部
            # 这比原来的点检查更精确，能过滤掉更多无效情况
            if not (
                    x + via_b_left >= bminx and
                    y + via_b_bottom >= bminy and
                    x + via_b_right <= bmaxx and
                    y + via_b_top <= bmaxy
            ):
                continue

            # 3. 精确几何包含检查 (Precise Containment Check)
            # 只有通过了快速筛选的点，才进行昂贵的几何操作
            via_moved = translate(via_shape, xoff=x, yoff=y)
            if b_shapely.contains(via_moved):
                valid_coords_in_batch.append((x, y))

        return valid_coords_in_batch

    # 4. 准备批处理任务
    # 动态计算一个合理的批大小。这个值可以根据机器性能和数据规模调整。
    # 一个经验法则是让每个核心至少能分到几个任务。
    num_cores = 6
    batch_size = max(1, len(candidates) // (num_cores * 4))

    # 将所有候选点分割成多个批次
    candidate_batches = [
        candidates[i:i + batch_size] for i in range(0, len(candidates), batch_size)
    ]

    # 5. 并行执行批处理任务
    # backend='loky' 或 'multiprocessing' 通常比 'threading' 更适合CPU密集型任务
    # 因为它可以绕开Python的全局解释器锁 (GIL)。
    results = Parallel(n_jobs=num_cores, backend="loky")(
        delayed(process_batch)(batch, b_shapely, via_shape) for batch in candidate_batches
    )

    # 6. 收集并合并所有结果
    # results 将是一个列表的列表，例如 [[(x1,y1)], [(x2,y2), (x3,y3)], ...]
    # 我们需要将其展平为一个单一的坐标列表
    valid_coords = [coord for batch_result in results for coord in batch_result]

    # =============================================================
    # 插入 via
    for x, y in valid_coords:
        via_ref = via_array << via
        via_ref.move((x, y))

    return via_array

@gf.cell
def ViaArray_optimized(
        CompEn: Component,
        WidthVia: float = 0.5,
        Spacing: float = 1.1,
        Enclosure: float = 2.0,
        arraylayer: LayerSpec = (1,0),
        vialayer: LayerSpec = (2,0),
) -> Component:
    """
    在给定组件 (`CompEn`) 的指定图层 (`arraylayer`) 形成的区域内，
    根据内缩值 (`Enclosure`)，高效地生成一个过孔阵列（并行优化版）。

    参数说明见原始文档。
    """

    via_array = gf.Component()
    B = gf.Component()
    Cw = gf.Section(width=WidthVia,layer=vialayer)
    Xw = gf.CrossSection(sections=(Cw,))
    via = gf.components.straight(length=WidthVia,cross_section=Xw)
    viabox = via.bbox()

    # ========== 关键优化1：预处理目标区域 ==========
    B0 = CompEn.copy()
    Br = B0.get_region(layer=arraylayer)
    Br.size(-Enclosure * 1000)
    B.add_polygon(Br, layer=arraylayer)
    b_polys = B.get_polygons_points(by='tuple')

    if arraylayer not in b_polys or not b_polys[arraylayer]:
        return via_array


    # 合并所有 polygon 为 shapely 区域
    b_shapely = unary_union([Polygon(poly) for poly in b_polys[arraylayer]])
    if b_shapely.is_empty:
        return via_array

    # 预生成单个 via 形状（基于 0 原点）
    via_shape = box(viabox.left, viabox.bottom, viabox.right, viabox.top)

    # 计算布孔区域边界 + 网格坐标
    min_x, min_y, max_x, max_y = b_shapely.bounds
    cols = int((max_x - min_x - WidthVia) // Spacing) + 5
    rows = int((max_y - min_y - WidthVia) // Spacing) + 5
    x_centers = min_x + WidthVia / 2 + Spacing * np.arange(cols)
    y_centers = min_y + WidthVia / 2 + Spacing * np.arange(rows)

    # 将 candidate 点转换为 numpy 坐标对
    candidates = np.array(np.meshgrid(x_centers, y_centers)).reshape(2, -1).T

    # 提取目标区域 bounding box，用于快速预筛
    bminx, bminy, bmaxx, bmaxy = b_shapely.bounds

    def is_inside_fast(x, y):
        # 粗筛：如果完全在 bounding box 外，则跳过
        if not (bminx <= x <= bmaxx and bminy <= y <= bmaxy):
            return None
        # 精筛：实际形状是否包含该 via
        via_moved = translate(via_shape, xoff=x, yoff=y)
        if b_shapely.contains(via_moved):
            return (x, y)
        return None

    # =================== 优化方案：并行批处理 + 内部矢量化 (混合方案) ===================
    # 确保你安装了最新版的 shapely: pip install shapely --upgrade

    def process_batch_vectorized(candidate_batch, b_shapely, via_half_width):
        """
        一个并行的工作函数，它使用矢量化操作处理一个批次的候选点。

        参数:
        - candidate_batch: 一个Numpy数组，形状为 (N, 2)，包含 [x, y] 坐标。
        - b_shapely: 目标区域的Shapely几何对象。
        - via_half_width: 过孔宽度的一半。
        """
        # 如果收到的批次是空的，直接返回
        if candidate_batch.shape[0] == 0:
            return []

        # 1. 矢量化创建几何对象 (仅针对当前批次)
        # 对批次内的所有坐标点，一次性创建出对应的过孔方块(box)的几何对象。
        # 这是内存开销最大的部分，但由于我们是按批处理，所以内存是可控的。
        via_boxes_in_batch = [
            box(x - via_half_width, y - via_half_width, x + via_half_width, y + via_half_width)
            for x, y in candidate_batch
        ]

        # 2. 关键的矢量化判断
        # 对当前批次的所有 via_boxes，进行一次性的、高效的“包含”判断。
        # b_shapely.contains() 会返回一个布尔值的列表或数组。
        contains_mask = b_shapely.contains(via_boxes_in_batch)

        # 3. 使用布尔掩码过滤
        # 从原始的坐标批次中，根据上面的判断结果，筛选出有效的坐标。
        valid_coords_in_batch = candidate_batch[contains_mask]

        # 以列表形式返回有效的坐标
        return valid_coords_in_batch.tolist()

    # -------------------- 在你的主函数中调用 --------------------

    # a. 预先计算过孔的半宽，避免在循环中重复计算
    via_half_width = WidthVia / 2.0

    # b. 设定批处理参数 (与之前相同)
    # 经验值：让每个核心至少能分到 8~16 个任务，以实现最佳负载均衡
    num_cores = 6
    batch_size = max(1, len(candidates) // (num_cores * 16))

    # 将所有候选点分割成多个批次
    # 确保 candidates 是一个 numpy array 以支持高级索引
    candidates = np.array(candidates)
    candidate_batches = [
        candidates[i:i + batch_size] for i in range(0, len(candidates), batch_size)
    ]

    # c. 并行执行新的、内部矢量化的批处理任务
    # backend='loky' 是最稳定和推荐的CPU密集型任务后端
    results = Parallel(n_jobs=num_cores, backend="loky")(
        delayed(process_batch_vectorized)(batch, b_shapely, via_half_width) for batch in candidate_batches
    )

    # d. 收集并合并所有结果
    valid_coords = [coord for sublist in results for coord in sublist]

    # =================================================================================

    # 插入 via
    for x, y in valid_coords:
        via_ref = via_array << via
        via_ref.move((x, y))

    return via_array


__all__ = ['SnakeHeater', 'ViaArray', 'DifferentHeater','ViaArrayParallel','ViaArray_optimized']
