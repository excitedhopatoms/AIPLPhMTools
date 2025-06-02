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
    该组件包含一个中心开放区域（通常用于暴露下层结构，如光栅耦合器或测试点）
    以及围绕该开放区域的金属电极层。

    参数:
        WidthOpen (float): 中心开放区域的宽度 (单位: um)。默认值为 90um。
        Enclosure (float): 金属电极层超出中心开放区域的包围宽度 (单位: um)。默认值为 10um。
        openlayer (LayerSpec): 定义中心开放区域的层。默认为 LAYER.OPEN。
        elelayer (LayerSpec): 定义金属电极层的层。默认为 LAYER.M1。

    返回:
        Component: 生成的开放焊盘组件。

    端口:
        "left": 组件左侧的金属电极端口。
        "right": 组件右侧的金属电极端口。
        "up": 组件上方的金属电极端口。
        "down": 组件下方的金属电极端口。
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

    参数:
        WidthG (float): G (Ground) 电极的宽度 (单位: um)。默认值为 80um。
        WidthS (float): S (Signal) 电极的宽度 (单位: um)。默认值为 25um。
        GapGS (float): G 电极与 S 电极之间的间隙宽度 (单位: um)。默认值为 6um。
        LengthEle (float): 电极的直线部分长度 (单位: um)。默认值为 10000um。
        LengthToPad (float): 电极连接到焊盘的过渡区域 (OffsetRamp) 的长度 (单位: um)。默认值为 300um。
        IsPad (bool): 是否在电极的右端添加 GSG 焊盘阵列。默认值为 False。
        Is2Pad (bool): 是否在电极的左端也添加 GSG 焊盘阵列。如果为 True，则 IsPad 也会被视为 True。默认值为 False。
        PitchPad (float): GSG 焊盘阵列中相邻焊盘的中心间距 (单位: um)。默认值为 150um。
        WidthOpen (float): 焊盘的开放区域宽度 (传递给 OpenPad 组件) (单位: um)。默认值为 45um。
        Enclosure (float): 焊盘的金属包围宽度 (传递给 OpenPad 组件) (单位: um)。默认值为 10um。
        openlayer (LayerSpec): 焊盘开放区域的层定义。默认为 LAYER.OPEN。
        elelayer (LayerSpec): 电极和焊盘金属层的定义。默认为 LAYER.M1。

    返回:
        Component: 生成的 GSG 电极组件。

    端口 (核心电极部分):
        "Gin1":  上方 G 电极的右侧端口。
        "Gout1": 上方 G 电极的左侧端口。
        "Sin":   中心 S 电极的右侧端口。
        "Sout":  中心 S 电极的左侧端口。
        "Gin2":  下方 G 电极的右侧端口。
        "Gout2": 下方 G 电极的左侧端口。
    端口 (辅助，可能用于连接或标记):
        "Oin1", "Oout1": 上方 G 和 S 电极间隙的左右端口。
        "Oin2", "Oout2": 下方 G 和 S 电极间隙的左右端口。
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


    # 创建 GSG 焊盘阵列单元 (包含三个 OpenPad)
    gsg_pad_array = gf.Component()
    pad1 = gsg_pad_array << OpenPad(
        WidthOpen=WidthOpen, Enclosure=Enclosure, elelayer=elelayer, openlayer=openlayer
    )
    pad2 = gsg_pad_array << OpenPad(
        WidthOpen=WidthOpen, Enclosure=Enclosure, elelayer=elelayer, openlayer=openlayer
    )
    pad3 = gsg_pad_array << OpenPad(
        WidthOpen=WidthOpen, Enclosure=Enclosure, elelayer=elelayer, openlayer=openlayer
    )

    # 排列三个焊盘，pad2 在中间，pad1 在下方，pad3 在上方 (按y轴排列)
    # 原代码 pad2.movey(PitchPad), pad3.movey(PitchPad*2) 暗示 pad1 在 y=0
    # 调整为中心对称或更明确的定位方式
    pad2.movey(0) # 中间焊盘
    pad1.movey(-PitchPad) # 下方焊盘
    pad3.movey(PitchPad)  # 上方焊盘

    # 为焊盘阵列添加端口，方便连接 (左右端口)
    # 假设 OpenPad 的左右端口名为 "left" 和 "right"
    gsg_pad_array.add_port("Pl1", port=pad1.ports["left"])   # 下方焊盘左端口
    gsg_pad_array.add_port("Pr1", port=pad1.ports["right"])  # 下方焊盘右端口
    gsg_pad_array.add_port("Pl2", port=pad2.ports["left"])   # 中心焊盘左端口
    gsg_pad_array.add_port("Pr2", port=pad2.ports["right"])  # 中心焊盘右端口
    gsg_pad_array.add_port("Pl3", port=pad3.ports["left"])   # 上方焊盘左端口
    gsg_pad_array.add_port("Pr3", port=pad3.ports["right"])  # 上方焊盘右端口

    # 如果 Is2Pad 为 True，则 IsPad 也应为 True
    if Is2Pad:
        IsPad = True # 确保 IsPad 也为 True，因为 Is2Pad 意味着两端都有焊盘

    # 在电极右端添加焊盘阵列
    if IsPad:
        pad_array_right = c << gsg_pad_array
        # 将焊盘阵列的中心焊盘 (Pr2) 连接到 S 电极的右端 (Sin)
        # 首先对齐 y 坐标
        pad_array_right.movey(c.ports["Sin"].center[1] - pad_array_right.ports["Pr2"].center[1])
        # 然后对齐 x 坐标，并留出 LengthToPad 的间距给 OffsetRamp
        pad_array_right.movex(c.ports["Sin"].center[0] + LengthToPad - pad_array_right.ports["Pr2"].center[0])


        # 使用 OffsetRamp 连接 G1, S, G2 电极到对应的焊盘
        # 连接上方 G 电极 (Gin1) 到上方焊盘 (Pr3)
        offset_g1 = pad_array_right.ports["Pr3"].center[1] - c.ports["Gin1"].center[1]
        ramp_g1_right = c << OffsetRamp(
            length=LengthToPad,
            width1=WidthG, # 电极宽度
            width2=pad_array_right.ports["Pr3"].width, # 焊盘端口宽度
            offset=offset_g1,
            layer=elelayer,
        )
        ramp_g1_right.connect("o1", other=c.ports["Gin1"]) # ramp的o1连接电极的Gin1
        # 手动连接 ramp 的 o2 到焊盘的 Pr3 (如果connect不支持，则需要手动放置)
        # GDSFactory 的 connect 通常处理对齐，但这里是 ramp 的输出连接到 pad_array 的输入
        # 这里假设 ramp_g1_right.ports["o2"] 应与 pad_array_right.ports["Pr3"] 对齐并连接
        # 如果 OffsetRamp 的 o2 在右边，焊盘的 Pr3 在左边，则需要旋转/镜像 OffsetRamp 或焊盘阵列
        # 根据原代码的 GPa.connect("Pr2", other=c.ports["Sin"])，Pr2是右端口，Sin是右端口
        # 这意味着焊盘阵列可能需要镜像，或者 OffsetRamp 的端口定义需要调整
        # 假设 OffsetRamp 的 o1 是左，o2 是右。焊盘的 Pl 是左，Pr 是右。
        # 连接电极右端 (Gin1, Sin, Gin2) 到 焊盘左端 (Pl3, Pl2, Pl1)
        # 因此，pad_array_right 应该使用 Pl1, Pl2, Pl3 端口

        # 重新审视连接逻辑：电极的右端口 (Gin1, Sin, Gin2) 连接到过渡ramp的左端口(o1)
        # ramp的右端口(o2) 连接到焊盘阵列的左端口 (Pl1, Pl2, Pl3)

        # 连接上方 G 电极 (Gin1) 到上方焊盘 (pad_array_right.ports["Pl3"])
        offset_g1_right = pad_array_right.ports["Pl3"].center[1] - c.ports["Gin1"].center[1]
        ramp_g1_right = c << OffsetRamp(length=LengthToPad, width1=WidthG, width2=pad_array_right.ports["Pl3"].width, offset=offset_g1_right, layer=elelayer)
        ramp_g1_right.connect("o1", c.ports["Gin1"])
        # 需要确保 ramp_g1_right.ports["o2"] 与 pad_array_right.ports["Pl3"] 正确连接
        # 这通常通过先放置 ramp，然后将 pad_array_right.ports["Pl3"] connect 到 ramp_g1_right.ports["o2"]
        # 或者，如果 connect 支持，直接 c.connect(ramp_g1_right.ports["o2"], pad_array_right.ports["Pl3"])

        # 连接中心 S 电极 (Sin) 到中心焊盘 (pad_array_right.ports["Pl2"])
        offset_s_right = pad_array_right.ports["Pl2"].center[1] - c.ports["Sin"].center[1]
        ramp_s_right = c << OffsetRamp(length=LengthToPad, width1=WidthS, width2=pad_array_right.ports["Pl2"].width, offset=offset_s_right, layer=elelayer)
        ramp_s_right.connect("o1", c.ports["Sin"])

        # 连接下方 G 电极 (Gin2) 到下方焊盘 (pad_array_right.ports["Pl1"])
        offset_g2_right = pad_array_right.ports["Pl1"].center[1] - c.ports["Gin2"].center[1]
        ramp_g2_right = c << OffsetRamp(length=LengthToPad, width1=WidthG, width2=pad_array_right.ports["Pl1"].width, offset=offset_g2_right, layer=elelayer)
        ramp_g2_right.connect("o1", c.ports["Gin2"])

        # 手动连接 Ramps 到 Pads (如果gdsfactory的connect不能直接跨层级或需要辅助)
        # 假设 pad_array_right 已经放置在 c.ports["Sin"].center[0] + LengthToPad 的x位置
        # 并且 y 已经对齐
        # GPa.connect("Pr2", other=c.ports["Sin"]... GPa.move([LengthToPad, 0])
        # 原代码的 GPa.move([LengthToPad,0]) 是相对于什么？
        # 假设 GPa (pad_array_right) 的 Pl2 端口的 x 坐标应该是 LengthEle + LengthToPad
        # 而 ramp 的 o2 端口的 x 坐标是 LengthEle + LengthToPad
        # 这样它们就可以连接了。

        # 修正连接：
        # 1. 放置电极
        # 2. 放置右侧焊盘阵列，使其 Pl2 的 x 坐标在 LengthEle + LengthToPad
        pad_array_right.movex(LengthEle + LengthToPad - pad_array_right.ports["Pl2"].x) # 确保x对齐
        # y 对齐 (以S电极为基准)
        pad_array_right.movey(c.ports["Sin"].y - pad_array_right.ports["Pl2"].y)


        # 重新创建 Ramps 并连接
        # G1 to Pad3 (upper)
        ramp_g1_r = c << OffsetRamp(length=LengthToPad, width1=WidthG, width2=pad_array_right.ports["Pl3"].width,
                                   offset=pad_array_right.ports["Pl3"].y - c.ports["Gin1"].y, layer=elelayer)
        ramp_g1_r.connect("o1", c.ports["Gin1"])
        # S to Pad2 (middle)
        ramp_s_r = c << OffsetRamp(length=LengthToPad, width1=WidthS, width2=pad_array_right.ports["Pl2"].width,
                                 offset=pad_array_right.ports["Pl2"].y - c.ports["Sin"].y, layer=elelayer)
        ramp_s_r.connect("o1", c.ports["Sin"])
        # G2 to Pad1 (lower)
        ramp_g2_r = c << OffsetRamp(length=LengthToPad, width1=WidthG, width2=pad_array_right.ports["Pl1"].width,
                                   offset=pad_array_right.ports["Pl1"].y - c.ports["Gin2"].y, layer=elelayer)
        ramp_g2_r.connect("o1", c.ports["Gin2"])


    # 在电极左端添加焊盘阵列
    if Is2Pad:
        pad_array_left = c << gsg_pad_array
        # 焊盘阵列需要水平翻转以使其右端口 (Pr1, Pr2, Pr3) 用于连接
        pad_array_left.mirror_x()

        # 放置左侧焊盘阵列，使其 Pr2 的 x 坐标在 -LengthToPad
        pad_array_left.movex(-LengthToPad - pad_array_left.ports["Pr2"].x)
        # y 对齐 (以S电极为基准)
        pad_array_left.movey(c.ports["Sout"].y - pad_array_left.ports["Pr2"].y)

        # 创建 Ramps 并连接 (电极左端口 Gout1, Sout, Gout2 连接到 ramp 的 o2, ramp 的 o1 连接到焊盘的 Pr)
        # G1 to Pad3 (upper)
        ramp_g1_l = c << OffsetRamp(length=LengthToPad, width1=pad_array_left.ports["Pr3"].width, width2=WidthG,
                                   offset=c.ports["Gout1"].y - pad_array_left.ports["Pr3"].y, layer=elelayer)
        ramp_g1_l.connect("o2", c.ports["Gout1"]) # ramp 的 o2 (右) 连接到电极的 Gout1 (左)
        # S to Pad2 (middle)
        ramp_s_l = c << OffsetRamp(length=LengthToPad, width1=pad_array_left.ports["Pr2"].width, width2=WidthS,
                                 offset=c.ports["Sout"].y - pad_array_left.ports["Pr2"].y, layer=elelayer)
        ramp_s_l.connect("o2", c.ports["Sout"])
        # G2 to Pad1 (lower)
        ramp_g2_l = c << OffsetRamp(length=LengthToPad, width1=pad_array_left.ports["Pr1"].width, width2=WidthG,
                                   offset=c.ports["Gout2"].y - pad_array_left.ports["Pr1"].y, layer=elelayer)
        ramp_g2_l.connect("o2", c.ports["Gout2"])

        # 手动连接 ramp 的 o1 到 pad_array_left 的对应 Pr 端口
        # (这一步通常在 gdsfactory 中通过先放置 ramp，然后 connect 焊盘端口到 ramp 端口来完成)
        # 例如: pad_array_left.ports["Pr3"].connect(ramp_g1_l.ports["o1"]) 但这会移动焊盘
        # 更好的做法是，ramp 的 connect 应该处理好其自身的位置


    # c.flatten() # 可选：将所有子组件的几何图形合并到当前组件，减少层级结构
    # 通常在最后导出GDS时执行flatten，或者在需要进行布尔运算等操作时
    return c


# __all__ 定义了当使用 from <module> import * 时，哪些名称会被导入
# 保持原样，或者根据实际需要调整
__all__ = ['OffsetRamp', 'OpenPad', 'GSGELE']

if __name__ == '__main__':
    # 创建并显示组件的示例代码
    # 需要一个有效的 LAYER 定义，例如：
    class LAYER_CLASS: # 临时的 LAYER 定义，实际项目中应从 BasicDefine 导入
        WG = (1, 0)
        M1 = (10, 0)
        OPEN = (11,0)
    LAYER = LAYER_CLASS()

    # 测试 OpenPad
    # open_pad_comp = OpenPad()
    # open_pad_comp.show() # gdsfactory 的显示方法

    # 测试 OffsetRamp
    # offset_ramp_comp = OffsetRamp(width1=2, width2=1, offset=5, length=20)
    # offset_ramp_comp.show()

    # 测试 GSGELE
    gsg_ele_comp_no_pad = GSGELE(LengthEle=200)
    # gsg_ele_comp_no_pad.show()
    # print(gsg_ele_comp_no_pad.ports)

    gsg_ele_comp_one_pad = GSGELE(LengthEle=200, IsPad=True, LengthToPad=50, PitchPad=100)
    # gsg_ele_comp_one_pad.show()
    # print(gsg_ele_comp_one_pad.ports)

    gsg_ele_comp_two_pads = GSGELE(LengthEle=200, Is2Pad=True, LengthToPad=50, PitchPad=100)
    gsg_ele_comp_two_pads.show()
    # print(gsg_ele_comp_two_pads.ports)
