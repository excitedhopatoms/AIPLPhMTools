from .BasicDefine import *
import gdsfactory as gf
import numpy as np
from gdsfactory.typings import  ComponentSpec, LayerSpecs
from shapely.ops import unary_union
from shapely.geometry import Polygon, box
def snap_polygon_vertices(polygon_points: np.ndarray, grid_size: float):
    """
    Snaps the vertices of a single polygon to the specified grid.

    Args:
        polygon_points: Numpy array of polygon vertices (Nx2).
        grid_size: The grid size to snap to.

    Returns:
        Numpy array of snapped polygon vertices.
    """
    if not isinstance(polygon_points, np.ndarray):
        polygon_points = np.array(polygon_points)
    a = np.round(polygon_points / grid_size) * grid_size
    return np.round(polygon_points / grid_size) * grid_size


def snap_all_polygons_iteratively(
        component_in: ComponentSpec,
        grid_size: float = 0.001,
) -> Component:
    """
    Snaps all polygons in a component to the grid by iterating through
    each polygon on each layer. Ports and labels are also transferred and
    their positions snapped. The component is flattened first to ensure
    all geometry is processed.

    Args:
        component_in: The input gdsfactory Component or ComponentSpec.
        grid_size: The grid size (in um) to snap vertices to.
                   Defaults to 0.001 (1 nm).

    Returns:
        A new gdsfactory Component with all polygons, port positions,
        and label positions snapped to the grid. Returns an empty component
        with a modified name if flattening fails.
    """
    # 获取 Component 对象
    c_in_orig = gf.get_component(component_in)

    if c_in_orig is None:
        print(f"错误: 输入 '{component_in}' 无法解析为有效组件。将返回一个空组件。")
        # 尝试生成一个基于输入（如果它是字符串）的名称，否则使用默认名称
        base_name = str(component_in) if isinstance(component_in, str) else "invalid_input"
        safe_base_name = "".join(
            char if char.isalnum() or char in ['_', '-'] else '_' for char in base_name
        )
        return gf.Component(name=f"{safe_base_name}_snap_failed_no_input_component")

    # 1. 扁平化组件以访问顶层所有多边形
    # flatten() 返回一个新的扁平化组件，原始组件不受影响
    c_in_orig.flatten()
    c_flat = c_in_orig
    # 检查 flatten() 是否返回了 None
    if c_flat is None:
        print(f"错误: 组件 '{c_in_orig.name}' 的 flatten() 操作返回了 None。将返回一个空组件。")
        # 为输出组件创建一个描述性的名称，即使 c_flat 为 None
        safe_original_name_fallback = "".join(
            char if char.isalnum() or char in ['_', '-'] else '_' for char in c_in_orig.name
        )
        return gf.Component(name=f"{safe_original_name_fallback}_iter_snapped_flatten_returned_none")

    # 为输出组件创建一个描述性的名称
    # 此时 c_flat 不应该是 None，所以 c_flat.name 应该是可访问的
    safe_original_name = "".join(
        char if char.isalnum() or char in ['_', '-'] else '_' for char in c_flat.name
    )
    component_out = gf.Component(name=f"{safe_original_name}_iter_snapped")

    # 2. 获取扁平化组件中的所有图层
    active_layers: LayerSpecs = c_flat.layers

    if not active_layers:
        # gf.logger.warning(f"组件 '{c_flat.name}' 中没有带多边形的图层可处理。")
        print(f"警告: 组件 '{c_flat.name}' 中没有带多边形的图层可处理。")
        # 即使没有多边形，仍然处理端口和标签
    c_sized = gf.Component(name=f"{safe_original_name}_iter_snapped_sized")
    c_sized2 = gf.Component(name=f"{safe_original_name}_iter_snapped_sized2")
    # 3. 遍历每一个图层,对所有图层都扩大一点点，然后进行合并
    for layer_spec in active_layers:
        c_in_sized_from_layer = c_in_orig.get_region(layer_spec)
        c_in_sized_from_layer = c_in_sized_from_layer.size(-20)
        c_sized.add_polygon(c_in_sized_from_layer,layer=layer_spec)
    c_sized = merge_polygons_in_each_layer(c_sized)
    c_sized.flatten()
    for layer_spec in active_layers:
        c_in_sized_from_layer = c_sized.get_region(layer_spec)
        c_in_sized_from_layer = c_in_sized_from_layer.size(20)
        # c_in_sized_from_layer = c_in_sized_from_layer.size(0)
        c_sized2.add_polygon(c_in_sized_from_layer,layer=layer_spec)
    c_sized2 = merge_polygons_in_each_layer(c_sized2)
    # 4. 遍历每一个图层,对所有图层都snap到格点上
    for layer_spec in active_layers:
        # 获取当前图层上的所有多边形
        polygons_on_layer = c_sized2.get_polygons_points(merge=True,by="tuple",layers=[layer_spec])

        if polygons_on_layer:
            # 遍历该图层上的每一个多边形
            for single_polygon_points in polygons_on_layer[layer_spec]:
                snapped_polygon_points = snap_polygon_vertices(
                    single_polygon_points, grid_size
                )
                component_out.add_polygon(snapped_polygon_points, layer=layer_spec)

    # 处理端口：复制、对齐位置，并添加到新组件
    for port in c_flat.ports:
        new_port = port
        snapped_center = snap_polygon_vertices(
            np.array(new_port.center), grid_size
        )
        new_port.center = snapped_center
        if abs(np.round(new_port.orientation/90)-new_port.orientation/90)<0.001:
            new_port.orientation = np.round(new_port.orientation/90)*90
        component_out.add_port(name=new_port.name, port=new_port)

    # # 处理标签：复制、对齐位置，并添加到新组件
    # for label_obj in c_flat.labels:
    #     snapped_position = snap_polygon_vertices(
    #         np.array(label_obj.origin), grid_size
    #     ).tolist()
    #     component_out.add_label(
    #         text=label_obj.text,
    #         position=snapped_position,
    #         layer=label_obj.layer,
    #         magnification=label_obj.magnification,
    #         rotation=label_obj.rotation,
    #         anchor=label_obj.anchor
    #     )

    # component_out.info.update(c_flat.info)

    return component_out


def merge_polygons_in_each_layer(
        component_in: ComponentSpec,
        precision: float = 1e-4,
) -> Component:
    """
    对输入组件的每一个图层上的所有多边形执行合并 (布尔 OR) 操作。
    此函数会处理组件层级结构，有效地在每个图层上扁平化并合并形状。

    Args:
        component_in: 输入的 gdsfactory 组件或组件引用。
        precision: 布尔运算的精度。

    Returns:
        一个新的 gdsfactory 组件，其中每个图层上的多边形都已合并。
    """
    c_in = gf.get_component(component_in)

    if c_in is None:
        print(f"错误: 输入 '{component_in}' 无法解析为有效组件。将返回一个空组件。")
        base_name = str(component_in) if isinstance(component_in, str) else "invalid_input"
        safe_base_name = "".join(
            char if char.isalnum() or char in ['_', '-'] else '_' for char in base_name
        )
        return gf.Component(name=f"{safe_base_name}_merge_failed_no_input_component")

    safe_original_name = "".join(
        char if char.isalnum() or char in ['_', '-'] else '_' for char in c_in.name
    )
    component_out = gf.Component(name=f"{safe_original_name}_layers_merged")

    active_layers: LayerSpecs = c_in.layers

    if not active_layers:
        print(f"警告: 组件 '{c_in.name}' 中没有图层可供处理。")
        return component_out
    # c_in.flatten()
    for layer_spec in active_layers:
        try:
            layer_merged_component = gf.boolean(
                c_in,c_in, operation="or", layer=layer_spec
            )
        except Exception as e:
            print(f"警告: 无法在图层 {layer_spec} 上为组件 '{c_in.name}' 执行布尔操作: {e}")
            continue

        if layer_merged_component:
            component_out << layer_merged_component

    return component_out


if __name__ == "__main__":
    # --- 创建一个示例组件用于测试 ---
    original_comp = gf.Component("my_complex_device_for_iter_snap")
    layer_wg = (1, 0)
    layer_heater = (2, 0)
