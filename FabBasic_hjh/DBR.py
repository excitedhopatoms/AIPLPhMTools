import gdsfactory as gf
import csv
from gdsfactory.typings import LayerSpec, Component
from .BasicDefine import *
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
        Name: str = "DBR"  # 组件名称
) -> Component:
    """
    创建一个分布式布拉格反射器（DBR）。

    Args:
        Width1: 第一部分波导宽度 (µm)
        Width2: 第二部分波导宽度 (µm)
        WidthHeat: 加热器宽度 (µm)
        WidthRoute: 加热器路由宽度 (µm)
        Length1: 第一部分波导长度 (µm)
        Length2: 第二部分波导长度 (µm)
        Length1E: 第一部分波导结束长度 (µm)
        Length2E: 第二部分波导结束长度 (µm)
        Period: 周期数
        IsSG: 是否使用渐变长度
        IsHeat: 是否包含加热器
        heatlayer: 加热层
        layer: 光学层
        layers: 多层光学层
        Name: 组件名称

    Returns:
        包含 o1, o2 端口的 Component，如果包含加热器则还有 h1, h2 端口
    """
    c = gf.Component(Name)
    if IsSG:
        # 渐变长度模式
        deltap1 = (Length1E - Length1) / (Period - 1)  # 第一部分长度增量 (µm)
        deltap2 = (Length2E - Length2) / (Period - 1)  # 第二部分长度增量 (µm)
        XBegin = 0  # 起始位置 (µm)
        for i in range(Period):
            r1 = c << gf.c.straight(length=Length1 + i * deltap1, width=Width1, layer=oplayer)
            r2 = c << gf.c.straight(length=Length2 + i * deltap2, width=Width2, layer=oplayer)
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
        r1 = op << gf.c.straight(length=Length1, width=Width1, layer=oplayer)
        r2 = op << gf.c.straight(length=Length2, width=Width2, layer=oplayer)
        r2.connect(port="o1", destination=r1.ports["o2"], allow_width_mismatch=True)
        op.add_port("o1", port=r1.ports["o1"])
        op.add_port("o2", port=r2.ports["o2"])
        c.add_array(op, columns=Period, rows=1, spacing=(Length2 + Length1, 100))
        c.add_port(name="o1", port=r1.ports["o1"])
        c.add_port(name="o2", port=r2.ports["o2"], center=[(Length1 + Length2) * Period, 0])

    if IsHeat:
        # 添加加热器
        length_dbr = c.ports["o2"].center - c.ports["o1"].center
        heater = c << gf.c.straight(width=WidthHeat, length=length_dbr[0], layer=heatlayer)
        heater.connect("o1", c.ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True, allow_type_mismatch=True).rotate(180, "o1")
        heattaper1 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2, layer=heatlayer)
        heattaper2 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2, layer=heatlayer)
        heattaper1.connect("o1", destination=heater.ports["o1"], allow_width_mismatch=True, allow_layer_mismatch=True, allow_type_mismatch=True)
        heattaper2.connect("o1", destination=heater.ports["o2"], allow_width_mismatch=True, allow_layer_mismatch=True, allow_type_mismatch=True)
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
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        Name: str = "DBR"  # 组件名称
) -> Component:
    """
    从 CSV 文件创建分布式布拉格反射器（DBR）。

    Args:
        Width1: 第一部分波导宽度 (µm)
        Width2: 第二部分波导宽度 (µm)
        WidthHeat: 加热器宽度 (µm)
        WidthRoute: 加热器路由宽度 (µm)
        CSVName: CSV 文件路径
        IsHeat: 是否包含加热器
        heatlayer: 加热层
        oplayer: 光学层
        Name: 组件名称

    Returns:
        包含 o1, o2 端口的 Component，如果包含加热器则还有 h1, h2 端口
    """
    c = gf.Component(Name)
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
            length0 = length0*1e6
        if length1 < 1e-5:
            length1 = length1*1e6
        if width0 < 1e-5:
            width0 = width0*1e6
        if width1 < 1e-5:
            width1 = width1 * 1e6
        r1.append(c << gf.c.straight(length=length0, width=width0, layer=oplayer))
        r2.append(c << gf.c.straight(length=length1, width=width1, layer=oplayer))
        if width0<width_min:
            width_min=width0
        elif width1<width_min:
            width_min=width1
        if i == 0:
            r2[0].connect(port="o1", destination=r1[0].ports["o2"])
        else:
            r1[i].connect(port="o1", destination=r2[i - 1].ports["o2"])
            r2[i].connect(port="o1", destination=r1[i].ports["o2"])
    c << gf.c.straight(length=-r1[0].ports["o1"].center[0]+r2[-1].ports["o2"].center[0], width=width_min, layer=oplayer)
    c.add_port("o1", port=r1[0].ports["o1"])
    c.add_port("o2", port=r2[-1].ports["o2"])

    if IsHeat:
        # 添加加热器
        length_dbr = c.ports["o2"].center - c.ports["o1"].center
        heater = c << gf.c.straight(width=WidthHeat, length=length_dbr[0], layer=heatlayer)
        heater.connect("o1", c.ports["o1"]).rotate(180, "o1")
        heattaper1 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2, layer=heatlayer)
        heattaper2 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2, layer=heatlayer)
        heattaper1.connect("o1", destination=heater.ports["o1"])
        heattaper2.connect("o1", destination=heater.ports["o2"])
        c.add_port(name="h1", port=heattaper1.ports["o2"])
        c.add_port(name="h2", port=heattaper2.ports["o2"])

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
        Name: str = "DBR"  # 组件名称
) -> Component:
    """
    从 CSV 文件创建分布式布拉格反射器（DBR）。

    Args:
        Width1: 第一部分波导宽度 (µm)
        Width2: 第二部分波导宽度 (µm)
        WidthHeat: 加热器宽度 (µm)
        WidthRoute: 加热器路由宽度 (µm)
        CSVName: CSV 文件路径
        IsHeat: 是否包含加热器
        heatlayer: 加热层
        oplayer: 光学层
        Name: 组件名称

    Returns:
        包含 o1, o2 端口的 Component，如果包含加热器则还有 h1, h2 端口
    """
    c = gf.Component(Name)
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
            length0 = length0*1e6
        if length1 < 1e-5:
            length1 = length1*1e6
        if width0 < 1e-5:
            width0 = width0*1e6
        if width1 < 1e-5:
            width1 = width1 * 1e6
        if width0 > width1:
            width0 = width0+Offset
        else:
            width1 = width1+Offset
        r1.append(c << gf.c.straight(length=length0, width=width0, layer=oplayer))
        r2.append(c << gf.c.straight(length=length1, width=width1, layer=oplayer))
        if width0<width_min:
            width_min=width0
        elif width1<width_min:
            width_min=width1
        if i == 0:
            r2[0].connect(port="o1", destination=r1[0].ports["o2"])
        else:
            r1[i].connect(port="o1", destination=r2[i - 1].ports["o2"])
            r2[i].connect(port="o1", destination=r1[i].ports["o2"])
    c << gf.c.straight(length=-r1[0].ports["o1"].center[0]+r2[-1].ports["o2"].center[0], width=width_min, layer=oplayer)
    c.add_port("o1", port=r1[0].ports["o1"])
    c.add_port("o2", port=r2[-1].ports["o2"])

    if IsHeat:
        # 添加加热器
        length_dbr = c.ports["o2"].center - c.ports["o1"].center
        heater = c << gf.c.straight(width=WidthHeat, length=length_dbr[0], layer=heatlayer)
        heater.connect("o1", c.ports["o1"]).rotate(180, "o1")
        heattaper1 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2, layer=heatlayer)
        heattaper2 = c << gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=WidthRoute / 2 - WidthHeat / 2, layer=heatlayer)
        heattaper1.connect("o1", destination=heater.ports["o1"])
        heattaper2.connect("o1", destination=heater.ports["o2"])
        c.add_port(name="h1", port=heattaper1.ports["o2"])
        c.add_port(name="h2", port=heattaper2.ports["o2"])

    return c

# %% 导出所有函数
__all__ = ['DBR', 'DBRFromCsv','DBRFromCsvOffset']