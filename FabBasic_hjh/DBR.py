import csv

from .BasicDefine import *
from .SnapMerge import *

# %% DBR: 分布式布拉格反射器
@gf.cell
def DBR(
        Width1: float = 2,  # 第一部分波导宽度 (µm)
        Width2: float = 1,  # 第二部分波导宽度 (µm)
        WidthHeat: float = 4,  # 加热器宽度 (µm)
        WidthRoute: float = 10,  # 加热器路由宽度 (µm)
        Length1: float = 0.4,  # 第一部分波导长度 (µm)
        Length2: float = 0.5,  # 第二部分波导长度 (µm)
        Length1E: float = 0.6,  # 第一部分波导结束长度 (µm)
        Length2E: float = 0.7,  # 第二部分波导结束长度 (µm)
        Period: float = 100,  # 周期数
        IsSG: bool = False,  # 是否使用渐变长度
        IsHeat: bool = False,  # 是否包含加热器
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    创建一个分布式布拉格反射器（DBR）组件。
    DBR由两段不同宽度（从而具有不同有效折射率）的波导周期性排列而成。
    支持固定周期长度和渐变周期长度模式，并可选择添加直线型加热器。

    参数:
        Width1 (float): DBR中第一种类型（通常较宽，高有效折射率）波导段的宽度 (单位: µm)。
        Width2 (float): DBR中第二种类型（通常较窄，低有效折射率）波导段的宽度 (单位: µm)。
        WidthHeat (float): 如果添加加热器，加热条的宽度 (单位: µm)。
        WidthRoute (float): 如果添加加热器，加热器引出金属的宽度 (单位: µm)。
        Length1 (float): 第一种类型波导段的长度 (单位: µm)。在渐变模式下，这是起始长度。
        Length2 (float): 第二种类型波导段的长度 (单位: µm)。在渐变模式下，这是起始长度。
        Length1E (float): 在渐变长度模式 (IsSG=True) 下，第一种类型波导段在DBR末端的长度 (单位: µm)。
        Length2E (float): 在渐变长度模式 (IsSG=True) 下，第二种类型波导段在DBR末端的长度 (单位: µm)。
        Period (int): DBR的周期数。一个周期包含一个Length1段和一个Length2段。
        IsSG (bool): 是否启用渐变光栅 (Sampled Grating) 模式。
                     如果为 True，每个周期中 Length1 和 Length2 会从初始值线性渐变到 Length1E 和 Length2E。
                     如果为 False，所有周期的 Length1 和 Length2 都固定不变。
        IsHeat (bool): 是否在DBR上方添加一个简单的直线型加热器。
        oplayer (LayerSpec): 定义光学波导的GDS图层。
        heatlayer (LayerSpec): 定义加热器的GDS图层。
        routelayer (LayerSpec): (当前未直接使用) 定义加热器引出线的GDS图层。
        vialayer (LayerSpec): (当前未直接使用) 定义过孔的GDS图层。

    返回:
        Component: 生成的DBR组件。

    端口:
        o1: DBR的输入光学端口。
        o2: DBR的输出光学端口。
        h1: (如果 IsHeat=True) 加热器的第一个电学端口。
        h2: (如果 IsHeat=True) 加热器的第二个电学端口。
    """
    c = gf.Component()
    if IsSG:
        # 渐变长度模式
        deltap1 = (Length1E - Length1) / (Period - 1)  # 第一部分长度增量 (µm)
        deltap2 = (Length2E - Length2) / (Period - 1)  # 第二部分长度增量 (µm)
        XBegin = 0  # 起始位置 (µm)
        for i in range(Period):
            r1 = c << GfCStraight(length=Length1 + i * deltap1, width=Width1, layer=oplayer)
            r2 = c << GfCStraight(length=Length2 + i * deltap2, width=Width2, layer=oplayer)
            r1.movex(XBegin)
            r2.movex(XBegin + Length1 + i * deltap1)
            XBegin += Length1 + i * deltap1 + Length2 + i * deltap2
            if i == 0:  # 第一个周期
                c.add_port(name="o1", port=r1.ports["o1"], orientation=180)
            elif i == Period - 1:  # 最后一个周期
                c.add_port(name="o2", port=r2.ports["o2"], orientation=0)
    else:
        # 固定长度模式
        op = gf.Component()
        r1 = op << GfCStraight(length=Length1, width=Width1, layer=oplayer)
        r2 = op << GfCStraight(length=Length2, width=Width2, layer=oplayer)
        r2.connect(port="o1", other=r1.ports["o2"], allow_width_mismatch=True)
        op.add_port("o1", port=r1.ports["o1"])
        op.add_port("o2", port=r2.ports["o2"])
        c.add_array(op, columns=Period, rows=1, spacing=(Length2 + Length1, 100))
        c.add_port(name="o1", port=r1.ports["o1"])
        c.add_port(name="o2", port=r2.ports["o2"], center=[(Length1 + Length2) * Period, 0])

    if IsHeat:
        # 添加加热器
        length_dbr = c.ports["o2"].center - c.ports["o1"].center
        heater = c << GfCStraight(width=WidthHeat, length=length_dbr[0], layer=heatlayer)
        heater.connect("o1", c.ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True,
                       allow_type_mismatch=True)
        heater.rotate(180, heater.ports["o1"].center)
        heattaper1 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2,
                                     layer=heatlayer)
        heattaper2 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2,
                                     layer=heatlayer)
        heattaper1.connect("o1", other=heater.ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True,
                           allow_type_mismatch=True)
        heattaper2.connect("o1", other=heater.ports["o2"], allow_width_mismatch=True, allow_layer_mismatch=True,
                           allow_type_mismatch=True)
        c.add_port(name="h1", port=heattaper1.ports["o2"])
        c.add_port(name="h2", port=heattaper2.ports["o2"])
    return c


# %% DBRFromCsv: 从 CSV 文件创建 DBR
@gf.cell
def DBRFromCsv(
        CSVName: str = "D:/Mask Download/Temp202311_LN_ZJ/单_D01.5e-25_k0.5_1500-1600.csv",  # CSV 文件路径
        WidthHeat: float = 4,  # 加热器宽度 (µm)
        WidthRoute: float = 10,  # 加热器路由宽度 (µm)
        IsHeat: bool = False,  # 是否包含加热器
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
) -> Component:
    """
    从 CSV 文件创建分布式布拉格反射器（DBR）。
    CSV文件的每一行应包含一个DBR周期中两段波导的宽度和长度信息。
    格式预期为: width0, length0, width1, length1 (其中0代表第一段，1代表第二段)
    单位在CSV中可能是米(m)，代码中会转换为微米(µm)并进行圆整。

    参数:
        CSVName (str): CSV文件的完整路径。
        WidthHeat (float): 如果添加加热器，加热条的宽度 (单位: µm)。
        WidthRoute (float): 如果添加加热器，加热器引出金属的宽度 (单位: µm)。
        IsHeat (bool): 是否在DBR上方添加一个简单的直线型加热器。
        oplayer (LayerSpec): 定义光学波导的GDS图层。
        heatlayer (LayerSpec): 定义加热器的GDS图层。

    返回:
        Component: 生成的基于CSV数据的DBR组件。

    端口:
        o1: DBR的输入光学端口。
        o2: DBR的输出光学端口。
        h1: (如果 IsHeat=True) 加热器的第一个电学端口。
        h2: (如果 IsHeat=True) 加热器的第二个电学端口。

    注意:
        - CSV文件中的长度和宽度单位需要注意，代码中做了简单的单位转换和圆整处理。
        - `snap_all_polygons_iteratively` 函数用于后处理，对齐多边形顶点。
    """
    c = gf.Component()
    lengthrows = csv.reader(open(CSVName))
    Period = len(list(lengthrows))
    lengthrows = csv.reader(open(CSVName))
    width_min = 5
    r1 = []
    r2 = []

    for i, length in enumerate(lengthrows):
        length0 = float(length[1])  # 第一部分长度 (µm)
        width0 = float(length[0])
        length1 = float(length[3])  # 第二部分长度 (µm)
        width1 = float(length[2])  # 第二部分长度 (µm)
        if length0 < 1e-5:
            length0 = length0 * 1e6
        if length1 < 1e-5:
            length1 = length1 * 1e6
        if width0 < 1e-5:
            width0 = width0 * 1e6
        if width1 < 1e-5:
            width1 = width1 * 1e6
        width0 = round(width0*1000 / 2)/500  # 结果: 2.0
        width1 = round(width1*1000 / 2)/500  # 结果: 2.0
        r1.append(c << GfCStraight(length=length0, width=width0, layer=oplayer))
        r2.append(c << GfCStraight(length=length1, width=width1, layer=oplayer))
        if width0 < width_min:
            width_min = width0
        elif width1 < width_min:
            width_min = width1
        if i == 0:
            r2[0].connect(port="o1", other=r1[0].ports["o2"], allow_width_mismatch=True, allow_layer_mismatch=True,
                          allow_type_mismatch=True)
        else:
            r1[i].connect(port="o1", other=r2[i - 1].ports["o2"], allow_width_mismatch=True, allow_layer_mismatch=True,
                          allow_type_mismatch=True)
            r2[i].connect(port="o1", other=r1[i].ports["o2"], allow_width_mismatch=True, allow_layer_mismatch=True,
                          allow_type_mismatch=True)
    # c << GfCStraight(length=-r1[0].ports["o1"].center[0] + r2[-1].ports["o2"].center[0], width=width_min, layer=oplayer)
    c.add_port("o1", port=r1[0].ports["o1"])
    c.add_port("o2", port=r2[-1].ports["o2"])

    if IsHeat:
        # 添加加热器
        length_dbr = c.ports["o2"].center - c.ports["o1"].center
        heater = c << GfCStraight(width=WidthHeat, length=length_dbr[0], layer=heatlayer)
        heater.connect("o1", c.ports["o1"]).rotate(180, heater.ports["o1"].center)
        heattaper1 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2,
                                     layer=heatlayer)
        heattaper2 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2,
                                     layer=heatlayer)
        heattaper1.connect("o1", other=heater.ports["o1"])
        heattaper2.connect("o1", other=heater.ports["o2"])
        c.add_port(name="h1", port=heattaper1.ports["o2"])
        c.add_port(name="h2", port=heattaper2.ports["o2"])
    c = snap_all_polygons_iteratively(c)
    return c


# %% DBRFromCsv: 从 CSV 文件创建 DBR
@gf.cell
def DBRFromCsvOffset(
        CSVName: str = "D:/Mask Download/Temp202311_LN_ZJ/单_D01.5e-25_k0.5_1500-1600.csv",  # CSV 文件路径
        WidthHeat: float = 4,  # 加热器宽度 (µm)
        WidthRoute: float = 10,  # 加热器路由宽度 (µm)
        Offset: float = 0.5,
        IsHeat: bool = False,  # 是否包含加热器
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    从 CSV 文件创建分布式布拉格反射器（DBR），并对周期中较宽的波导段应用一个宽度偏移 (Offset)。
    CSV文件的格式和单位转换与 `DBRFromCsv` 函数中的预期相同。
    偏移量 `Offset` 会加到每周期两段波导中较宽的那一段上。

    参数:
        CSVName (str): CSV文件的完整路径。
        WidthHeat (float): 如果添加加热器，加热条的宽度 (单位: µm)。
        WidthRoute (float): 如果添加加热器，加热器引出金属的宽度 (单位: µm)。
        Offset (float): 应用于周期中较宽波导段的宽度增加值 (单位: µm)。默认为 0.5 µm。
        IsHeat (bool): 是否在DBR上方添加一个简单的直线型加热器。
        oplayer (LayerSpec): 定义光学波导的GDS图层。
        heatlayer (LayerSpec): 定义加热器的GDS图层。

    返回:
        Component: 生成的带宽度偏移的DBR组件。

    端口及注意同 `DBRFromCsv`。
    """
    c = gf.Component()
    lengthrows = csv.reader(open(CSVName))
    Period = len(list(lengthrows))
    lengthrows = csv.reader(open(CSVName))
    width_min = 5
    r1 = []
    r2 = []

    for i, length in enumerate(lengthrows):
        length0 = float(length[1])  # 第一部分长度 (µm)
        width0 = float(length[0])
        length1 = float(length[3])  # 第二部分长度 (µm)
        width1 = float(length[2])  # 第二部分长度 (µm)
        if length0 < 1e-5:
            length0 = length0 * 1e6
        if length1 < 1e-5:
            length1 = length1 * 1e6
        if width0 < 1e-5:
            width0 = width0 * 1e6
        if width1 < 1e-5:
            width1 = width1 * 1e6
        if width0 > width1:
            width0 = width0 + Offset
        else:
            width1 = width1 + Offset
        width0 = round(width0 * 1000 / 2) / 500  # 结果: 2.0
        width1 = round(width1 * 1000 / 2) / 500  # 结果: 2.0
        r1.append(c << GfCStraight(length=length0, width=width0, layer=oplayer))
        r2.append(c << GfCStraight(length=length1, width=width1, layer=oplayer))
        if width0 < width_min:
            width_min = width0
        elif width1 < width_min:
            width_min = width1
        if i == 0:
            r2[0].connect(port="o1", other=r1[0].ports["o2"],allow_width_mismatch=True)
        else:
            r1[i].connect(port="o1", other=r2[i - 1].ports["o2"],allow_width_mismatch=True)
            r2[i].connect(port="o1", other=r1[i].ports["o2"],allow_width_mismatch=True)
    # c << GfCStraight(length=-r1[0].ports["o1"].center[0] + r2[-1].ports["o2"].center[0], width=width_min, layer=oplayer)
    c.add_port("o1", port=r1[0].ports["o1"])
    c.add_port("o2", port=r2[-1].ports["o2"])

    if IsHeat:
        # 添加加热器
        length_dbr = c.ports["o2"].center - c.ports["o1"].center
        heater = c << GfCStraight(width=WidthHeat, length=length_dbr[0], layer=heatlayer)
        heater.connect("o1", c.ports["o1"]).rotate(180, heater.ports["o1"].center)
        heattaper1 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2,
                                     layer=heatlayer)
        heattaper2 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2,
                                     layer=heatlayer)
        heattaper1.connect("o1", other=heater.ports["o1"])
        heattaper2.connect("o1", other=heater.ports["o2"])
        c.add_port(name="h1", port=heattaper1.ports["o2"])
        c.add_port(name="h2", port=heattaper2.ports["o2"])
    c = snap_all_polygons_iteratively(c)
    return c
# %% DBRFromCsv: 从 CSV 文件创建 DBR
@gf.cell
def SGDBRFromCsvOffset(
        CSVName: str = "D:/Mask Download/Temp202311_LN_ZJ/单_D01.5e-25_k0.5_1500-1600.csv",  # CSV 文件路径
        WidthHeat: float = 4,  # 加热器宽度 (µm)
        WidthRoute: float = 10,  # 加热器路由宽度 (µm)
        PeirdSampled: float = 40,
        NumSampled:float = 4,
        Offset: float = 0.5,
        IsHeat: bool = False,  # 是否包含加热器
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    从 CSV 文件创建分布式布拉格反射器（DBR），并对周期中较宽的波导段应用一个宽度偏移 (Offset)。
    CSV文件的格式和单位转换与 `DBRFromCsv` 函数中的预期相同。
    偏移量 `Offset` 会加到每周期两段波导中较宽的那一段上。

    参数:
        CSVName (str): CSV文件的完整路径。
        WidthHeat (float): 如果添加加热器，加热条的宽度 (单位: µm)。
        WidthRoute (float): 如果添加加热器，加热器引出金属的宽度 (单位: µm)。
        Offset (float): 应用于周期中较宽波导段的宽度增加值 (单位: µm)。默认为 0.5 µm。
        IsHeat (bool): 是否在DBR上方添加一个简单的直线型加热器。
        oplayer (LayerSpec): 定义光学波导的GDS图层。
        heatlayer (LayerSpec): 定义加热器的GDS图层。

    返回:
        Component: 生成的带宽度偏移的DBR组件。

    端口及注意同 `DBRFromCsv`。
    """
    c = gf.Component()
    lengthrows = csv.reader(open(CSVName))
    Period = len(list(lengthrows))
    lengthrows = csv.reader(open(CSVName))
    width_min = 5
    r1 = []
    r2 = []

    for i, length in enumerate(lengthrows):
        length0 = float(length[1])  # 第一部分长度 (µm)
        width0 = float(length[0])
        length1 = float(length[3])  # 第二部分长度 (µm)
        width1 = float(length[2])  # 第二部分长度 (µm)
        if length0 < 1e-5:
            length0 = length0 * 1e6
        if length1 < 1e-5:
            length1 = length1 * 1e6
        if width0 < 1e-5:
            width0 = width0 * 1e6
        if width1 < 1e-5:
            width1 = width1 * 1e6
        if width0 > width1:
            width0 = width0 + Offset
        else:
            width1 = width1 + Offset
        if i%PeirdSampled > PeirdSampled-NumSampled:
            width0 = width1
        width0 = round(width0 * 1000 / 2) / 500  # 结果: 2.0
        width1 = round(width1 * 1000 / 2) / 500  # 结果: 2.0
        r1.append(c << GfCStraight(length=length0, width=width0, layer=oplayer))
        r2.append(c << GfCStraight(length=length1, width=width1, layer=oplayer))
        if i == 0:
            r2[0].connect(port="o1", other=r1[0].ports["o2"],allow_width_mismatch=True)
        else:
            r1[i].connect(port="o1", other=r2[i - 1].ports["o2"],allow_width_mismatch=True)
            r2[i].connect(port="o1", other=r1[i].ports["o2"],allow_width_mismatch=True)
    # c << GfCStraight(length=-r1[0].ports["o1"].center[0] + r2[-1].ports["o2"].center[0], width=width_min, layer=oplayer)
    c.add_port("o1", port=r1[0].ports["o1"])
    c.add_port("o2", port=r2[-1].ports["o2"])

    if IsHeat:
        # 添加加热器
        length_dbr = c.ports["o2"].center - c.ports["o1"].center
        heater = c << GfCStraight(width=WidthHeat, length=length_dbr[0], layer=heatlayer)
        heater.connect("o1", c.ports["o1"]).rotate(180, heater.ports["o1"].center)
        heattaper1 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2,
                                     layer=heatlayer)
        heattaper2 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2,
                                     layer=heatlayer)
        heattaper1.connect("o1", other=heater.ports["o1"])
        heattaper2.connect("o1", other=heater.ports["o2"])
        c.add_port(name="h1", port=heattaper1.ports["o2"])
        c.add_port(name="h2", port=heattaper2.ports["o2"])
    c = snap_all_polygons_iteratively(c)
    return c

# %% 导出所有函数
__all__ = ['DBR', 'DBRFromCsv', 'DBRFromCsvOffset','SGDBRFromCsvOffset']
