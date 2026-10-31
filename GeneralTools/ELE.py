"""电学图元：开放焊盘（OpenPad）与 GSG 探针电极（GSGELE）。
"""
# 导入自定义的基础定义模块，其中可能包含常量、枚举、自定义组件等
from .BasicDefine import *
import gdsfactory as gf # 假设使用的是gdsfactory库，根据实际情况修改
from gdsfactory.component import Component # 明确导入Component类
from gdsfactory.typings import LayerSpec # 明确导入LayerSpec类型

# %% OpenPad: 定义一个开放焊盘组件
@gf.cell
def OpenPad(
    WidthOpen: float = 90,  # 中心开放区域的宽度，单位：um
    Enclosure: float = 10,  # 金属电极层超出开放区域的包围宽度，单位：um
    openlayer: LayerSpec = LAYER.OPEN,  # 开放区域的层定义
    elelayer: LayerSpec = LAYER.M1,  # 金属电极层的层定义
) -> Component:
    """
    创建一个开放焊盘组件 (Open Pad Component)。
    该组件通常用于测试点或需要暴露下层结构（如光栅耦合器）的场合。
    它包含一个中心开放区域（通常为正方形）和围绕该区域的金属电极层。

    参数:
        WidthOpen (float): 中心开放区域的宽度或边长 (单位: um)。默认值为 90.0 um。
        Enclosure (float): 金属电极层超出中心开放区域的单边包围宽度 (单位: um)。
                           例如，如果开放区域宽度为W, 则金属宽度为 W + 2*Enclosure。
                           默认值为 10.0 um。
        openlayer (LayerSpec): 定义中心开放区域的GDS图层。默认为 `LAYER.OPEN`。
        elelayer (LayerSpec): 定义金属电极层的GDS图层。默认为 `LAYER.M1`。

    返回:
        Component: 生成的开放焊盘组件。

    端口:
        "left": 组件左侧边缘中点的金属电极端口。
        "right": 组件右侧边缘中点的金属电极端口。
        "up": 组件上侧边缘中点的金属电极端口。
        "down": 组件下侧边缘中点的金属电极端口。
        (所有端口的宽度等于金属焊盘的边长)
    """
    c = gf.Component()  # 创建一个新的组件实例，并指定一个描述性的名称

    # 创建中心开放区域 (通常是一个正方形)
    # GfCStraight 可能是自定义的直线波导组件，这里用作矩形
    pad_open_area = c << gf.components.rectangle(
        size=(WidthOpen, WidthOpen), layer=openlayer
    )
    pad_open_area.move(
        (-WidthOpen / 2, -WidthOpen / 2)
    )  # 将其中心移动到原点，方便后续操作

    # 创建外围的金属电极层 (也是一个正方形)
    width_metal_pad = WidthOpen + 2 * Enclosure
    metal_electrode = c << gf.components.rectangle(
        size=(width_metal_pad, width_metal_pad), layer=elelayer
    )
    metal_electrode.move(
        (-width_metal_pad / 2, -width_metal_pad / 2)
    )  # 将其中心移动到原点

    # 添加端口
    # 端口通常定义在组件的边缘，用于连接其他组件
    # 端口的宽度是金属电极层的宽度，方向指向外部
    c.add_port(
        name="left",
        center=(-width_metal_pad / 2, 0),
        width=width_metal_pad,
        orientation=180, # 指向左侧
        layer=elelayer,
    )
    c.add_port(
        name="right",
        center=(width_metal_pad / 2, 0),
        width=width_metal_pad,
        orientation=0, # 指向右侧
        layer=elelayer,
    )
    c.add_port(
        name="up",
        center=(0, width_metal_pad / 2),
        width=width_metal_pad,
        orientation=90, # 指向上方
        layer=elelayer,
    )
    c.add_port(
        name="down",
        center=(0, -width_metal_pad / 2),
        width=width_metal_pad,
        orientation=270, # 指向下方 (或 -90)
        layer=elelayer,
    )

    # 如果 BasicDefine 中定义了 add_labels_to_ports 函数，则调用它
    if "add_labels_to_ports" in globals():
        add_labels_to_ports(c)

    return c

# %% GSGELE: 定义一个GSG (Ground-Signal-Ground) 电极组件
@gf.cell
def GSGELE(
    WidthG: float = 80,  # G (Ground) 电极的宽度，单位：um
    WidthS: float = 25,  # S (Signal) 电极的宽度，单位：um
    GapGS: float = 6,  # G 电极与 S 电极之间的间隙宽度，单位：um
    LengthEle: float = 10000,  # 电极的长度，单位：um
    LengthToPad: float = 300, # 电极连接到焊盘的过渡区域长度，单位：um
    IsPad: bool = False,  # 是否在电极的一端添加 GSG 焊盘阵列
    Is2Pad: bool = False,  # 是否在电极的两端都添加 GSG 焊盘阵列 (如果为True，则IsPad也应为True)
    PitchPad: float = 150,  # GSG 焊盘阵列中相邻焊盘的中心间距，单位：um
    WidthOpen: float = 45,  # 焊盘的开放区域宽度 (用于 OpenPad 组件)，单位：um
    Enclosure: float = 10,  # 焊盘的金属包围宽度 (用于 OpenPad 组件)，单位：um
    openlayer: LayerSpec = LAYER.OPEN,  # 焊盘开放区域的层定义
    elelayer: LayerSpec = LAYER.M1,  # 电极和焊盘金属层的定义
) -> Component:
    """
    创建一个 GSG (Ground-Signal-Ground) 电极组件。
    该组件包含一个中心信号电极 (S) 和两侧的接地电极 (G)。
    可以选择在电极的一端或两端添加 GSG 焊盘阵列，用于外部探针测试或连接。
    焊盘通过 `OffsetRamp` 组件与GSG电极的直线部分平滑连接。

    参数:
        WidthG (float): G (Ground) 电极的宽度 (单位: um)。
        WidthS (float): S (Signal) 电极的宽度 (单位: um)。
        GapGS (float): G 电极与 S 电极之间的间隙宽度 (单位: um)。
        LengthEle (float): GSG 电极直线部分的长度 (单位: um)。
        LengthToPad (float): 从GSG电极连接到焊盘的过渡 `OffsetRamp` 的长度 (单位: um)。
        IsPad (bool): 是否在GSG电极的右端添加焊盘阵列。
        Is2Pad (bool): 是否在GSG电极的左端也添加焊盘阵列。如果为 True，则 IsPad 也被视为 True。
        PitchPad (float): GSG 焊盘阵列中，中心到中心（垂直方向）的间距 (单位: um)。
        WidthOpen (float): 传递给 `OpenPad` 组件的开放区域宽度 (单位: um)。
        Enclosure (float): 传递给 `OpenPad` 组件的金属包围宽度 (单位: um)。
        openlayer (LayerSpec): 焊盘开放区域的GDS图层。
        elelayer (LayerSpec): 电极和焊盘金属的GDS图层。

    返回:
        Component: 生成的 GSG 电极组件。

    端口 (核心电极部分，位于 LengthEle 的两端):
        "Gout1_ele": 上方 G 电极的左端端口。
        "Gin1_ele":  上方 G 电极的右端端口。
        "Sout_ele":  中心 S 电极的左端端口。
        "Sin_ele":   中心 S 电极的右端端口。
        "Gout2_ele": 下方 G 电极的左端端口。
        "Gin2_ele":  下方 G 电极的右端端口。
    端口 (如果添加了焊盘，则会有焊盘的外部端口，例如):
        "Pad_R_G1", "Pad_R_S", "Pad_R_G2": 右侧焊盘阵列的G, S, G端口 (通常是最外侧)。
        "Pad_L_G1", "Pad_L_S", "Pad_L_G2": 左侧焊盘阵列的G, S, G端口。
    (原代码中的 Oin1, Oout1 等辅助端口已移除，因为它们通常不用于外部连接)
    """
    c = gf.Component()  # 创建一个新的组件实例

    # 计算 G 电极中心相对于 S 电极中心的垂直偏移量
    # delta_gs_center = S 电极半宽 + 间隙 + G 电极半宽
    delta_gs_center = WidthS / 2 + GapGS + WidthG / 2

    # 创建直线电极单元 (G 和 S)
    # GfCStraight 可能是自定义的直线组件，这里用 gf.components.straight 替代
    g_electrode_ref = GfCStraight(width=WidthG, length=LengthEle, layer=elelayer)
    s_electrode_ref = GfCStraight(width=WidthS, length=LengthEle, layer=elelayer)

    # 实例化电极并放置
    s1_electrode = c << s_electrode_ref  # 中心 S 电极，默认放置在 y=0
    g1_electrode = c << g_electrode_ref  # 上方 G 电极
    g2_electrode = c << g_electrode_ref  # 下方 G 电极

    g1_electrode.movey(delta_gs_center)  # 将上方 G 电极向上移动
    g2_electrode.movey(-delta_gs_center) # 将下方 G 电极向下移动

    # 添加核心电极端口 (左侧为 "o1", 右侧为 "o2" 在 straight 组件中)
    # 注意：原代码端口命名 Gout1/Gin1 指向左/右，这里调整为更直观的 left/right 后再映射
    # 或者直接使用原始端口，但确保其含义清晰
    c.add_port(name="Gout1", port=g1_electrode.ports["o1"]) # 上方 G 电极左端
    c.add_port(name="Gin1", port=g1_electrode.ports["o2"])   # 上方 G 电极右端
    c.add_port(name="Sout", port=s1_electrode.ports["o1"])   # 中心 S 电极左端
    c.add_port(name="Sin", port=s1_electrode.ports["o2"])    # 中心 S 电极右端
    c.add_port(name="Gout2", port=g2_electrode.ports["o1"]) # 下方 G 电极左端
    c.add_port(name="Gin2", port=g2_electrode.ports["o2"])   # 下方 G 电极右端

    # 添加辅助端口 (可能用于标记间隙或特殊连接点)
    # 这些端口位于 G 和 S 电极之间的间隙中心
    gap_center_y_upper = WidthS / 2 + GapGS / 2
    gap_center_y_lower = -WidthS / 2 - GapGS / 2
    c.add_port(name="Oin1", center=(0, gap_center_y_upper), width=GapGS, orientation=180, layer=elelayer)
    c.add_port(name="Oout1", center=(LengthEle, gap_center_y_upper), width=GapGS, orientation=0, layer=elelayer)
    c.add_port(name="Oin2", center=(0, gap_center_y_lower), width=GapGS, orientation=180, layer=elelayer)
    c.add_port(name="Oout2", center=(LengthEle, gap_center_y_lower), width=GapGS, orientation=0, layer=elelayer)


    # ---- GSG 焊盘阵列：三个 OpenPad 竖直排列，中间为 S，上下为 G ----
    gsg_pad_array = gf.Component()
    pad_list = []
    for _ in range(3):
        pad_list.append(gsg_pad_array << OpenPad(
            WidthOpen=WidthOpen, Enclosure=Enclosure,
            elelayer=elelayer, openlayer=openlayer,
        ))
    pad_list[0].movey(-PitchPad)   # 下方 G
    pad_list[1].movey(0)           # 中间 S
    pad_list[2].movey(PitchPad)    # 上方 G
    for idx, pad in enumerate(pad_list, start=1):
        gsg_pad_array.add_port(f"Pl{idx}", port=pad.ports["left"])
        gsg_pad_array.add_port(f"Pr{idx}", port=pad.ports["right"])

    def _connect_ramp(elec_port_name, pad_port, width_elec, from_left):
        """把电极端口与焊盘端口用 OffsetRamp 连起来（含宽度渐变）。"""
        if from_left:
            # 左侧焊盘：焊盘在左，电极在右 -> ramp 的 o2 接电极
            offset = c.ports[elec_port_name].y - pad_port.y
            ramp = c << OffsetRamp(
                length=LengthToPad, width1=pad_port.width, width2=width_elec,
                offset=offset, layer=elelayer,
            )
            ramp.connect("o2", c.ports[elec_port_name])
        else:
            # 右侧焊盘：电极在左，焊盘在右 -> ramp 的 o1 接电极
            offset = pad_port.y - c.ports[elec_port_name].y
            ramp = c << OffsetRamp(
                length=LengthToPad, width1=width_elec, width2=pad_port.width,
                offset=offset, layer=elelayer,
            )
            ramp.connect("o1", c.ports[elec_port_name])
        return ramp

    # 如果 Is2Pad 为 True，则两端都要焊盘
    if Is2Pad:
        IsPad = True

    # ---------- 右端焊盘 ----------
    if IsPad:
        pad_array_right = c << gsg_pad_array
        # 焊盘左沿放在电极右端 + LengthToPad 处，S 焊盘与 S 电极同高
        pad_array_right.movex(LengthEle + LengthToPad - pad_array_right.ports["Pl2"].x)
        pad_array_right.movey(c.ports["Sin"].y - pad_array_right.ports["Pl2"].y)

        for elec, pad_name, width_elec, tag in (
            ("Gin1", "Pl3", WidthG, "G1"),
            ("Sin", "Pl2", WidthS, "S"),
            ("Gin2", "Pl1", WidthG, "G2"),
        ):
            _connect_ramp(elec, pad_array_right.ports[pad_name], width_elec, from_left=False)
            # 对外端口取焊盘外侧（右）端口
            c.add_port(f"Pad_R_{tag}", port=pad_array_right.ports["Pr" + pad_name[-1]])

    # ---------- 左端焊盘 ----------
    if Is2Pad:
        pad_array_left = c << gsg_pad_array
        pad_array_left.mirror_x()
        # 镜像后：Pl* 朝向电极（右侧），Pr* 在左侧作为对外探测面
        pad_array_left.movex(-LengthToPad - pad_array_left.ports["Pl2"].x)
        pad_array_left.movey(c.ports["Sout"].y - pad_array_left.ports["Pl2"].y)

        for elec, pad_name, width_elec, tag in (
            ("Gout1", "Pl3", WidthG, "G1"),
            ("Sout", "Pl2", WidthS, "S"),
            ("Gout2", "Pl1", WidthG, "G2"),
        ):
            _connect_ramp(elec, pad_array_left.ports[pad_name], width_elec, from_left=True)
            c.add_port(f"Pad_L_{tag}", port=pad_array_left.ports["Pr" + pad_name[-1]])

    # c.flatten() # 可选：将所有子组件的几何图形合并到当前组件，减少层级结构
    # 通常在最后导出GDS时执行flatten，或者在需要进行布尔运算等操作时
    return c


# __all__ 定义了当使用 from <module> import * 时，哪些名称会被导入
# 保持原样，或者根据实际需要调整
__all__ = ['OffsetRamp', 'OpenPad', 'GSGELE']
