import csv

from PIL.ImageChops import offset

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
        NumPeriod: float = 100,  # 周期数
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
        deltap1 = (Length1E - Length1) / (NumPeriod - 1)  # 第一部分长度增量 (µm)
        deltap2 = (Length2E - Length2) / (NumPeriod - 1)  # 第二部分长度增量 (µm)
        XBegin = 0  # 起始位置 (µm)
        for i in range(NumPeriod):
            r1 = c << GfCStraight(length=Length1 + i * deltap1, width=Width1, layer=oplayer)
            r2 = c << GfCStraight(length=Length2 + i * deltap2, width=Width2, layer=oplayer)
            r1.movex(XBegin)
            r2.movex(XBegin + Length1 + i * deltap1)
            XBegin += Length1 + i * deltap1 + Length2 + i * deltap2
            if i == 0:  # 第一个周期
                c.add_port(name="o1", port=r1.ports["o1"], orientation=180)
            elif i == NumPeriod - 1:  # 最后一个周期
                c.add_port(name="o2", port=r2.ports["o2"], orientation=0)
    else:
        # 固定长度模式
        op = gf.Component()
        r1 = op << GfCStraight(length=Length1, width=Width1, layer=oplayer)
        r2 = op << GfCStraight(length=Length2, width=Width2, layer=oplayer)
        r2.connect(port="o1", other=r1.ports["o2"], allow_width_mismatch=True)
        op.add_port("o1", port=r1.ports["o1"])
        op.add_port("o2", port=r2.ports["o2"])
        c.add_array(op, columns=NumPeriod, rows=1, spacing=(Length2 + Length1, 100))
        c.add_port(name="o1", port=r1.ports["o1"])
        c.add_port(name="o2", port=r2.ports["o2"], center=[(Length1 + Length2) * NumPeriod, 0])

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
        Wcol = [1,3],
        Lcol = [2,4],
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
    return DBRFromCsvOffset(
        CSVName,
        WidthHeat,
        WidthRoute,
        0,
        IsHeat,
        Wcol,
        Lcol,
        oplayer,
        heatlayer,
)


# %% DBRFromCsv: 从 CSV 文件创建 DBR
@gf.cell
def DBRFromCsvOffset(
        CSVName: str = "D:/Mask Download/Temp202311_LN_ZJ/单_D01.5e-25_k0.5_1500-1600.csv",  # CSV 文件路径
        WidthHeat: float = 4,  # 加热器宽度 (µm)
        WidthRoute: float = 10,  # 加热器路由宽度 (µm)
        Offset: float = 0.5,
        IsHeat: bool = False,  # 是否包含加热器
        Wcol=[1, 3],
        Lcol=[2, 4],
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    (优化版) 从 CSV 文件创建分布式布拉格反射器（DBR），并对周期中较宽的波导段应用一个宽度偏移。

    此版本使用 NumPy 预先计算所有几何坐标，然后通过 `add_polygon` 批量添加几何形状，
    避免了创建和连接大量独立组件所带来的缓慢迭代过程。
    函数的参数、功能和最终生成的几何图形与原始版本完全相同。
    """
    # --- 1. 数据加载与准备 ---
    try:
        # 一次性将CSV加载到NumPy数组中，以便进行高效的矢量化计算
        data = np.loadtxt(CSVName, delimiter=',')
    except Exception as e:
        raise IOError(f"无法读取或解析CSV文件，路径: {CSVName}。错误: {e}")

    # 将指定列的数据提取到命名清晰的数组中
    lengths0 = data[:, Lcol[0] - 1]
    lengths1 = data[:, Lcol[1] - 1]
    widths0 = data[:, Wcol[0] - 1]
    widths1 = data[:, Wcol[1] - 1]
    num_periods = len(data)

    # --- 2. 矢量化逻辑应用 ---

    # A. 单位转换：如果数值很小（比如单位是米），则将其转换为微米
    lengths0[lengths0 < 1e-5] *= 1e6
    lengths1[lengths1 < 1e-5] *= 1e6
    widths0[widths0 < 1e-5] *= 1e6
    widths1[widths1 < 1e-5] *= 1e6

    # B. 条件偏移：为每个周期中较宽的部分增加偏移量
    # 使用 np.where 实现矢量化的 if/else 语句，效率极高。
    is_w0_wider = widths0 > widths1
    w0_after_offset = np.where(is_w0_wider, widths0 + Offset, widths0)
    w1_after_offset = np.where(~is_w0_wider, widths1 + Offset, widths1)

    # C. 网格捕捉/取整：将宽度取整到最接近的2nm (0.002µm)
    # round(val * 500) / 500 的效果等同于取整到最接近的 1/500。
    final_widths0 = np.round(w0_after_offset * 500) / 500
    final_widths1 = np.round(w1_after_offset * 500) / 500

    # --- 3. 几何生成 ---
    c = gf.Component()

    # 将所有波导段的长度和宽度交错排列到一个数组中，以便统一处理
    all_lengths = np.empty(num_periods * 2)
    all_lengths[0::2] = lengths0
    all_lengths[1::2] = lengths1

    all_widths = np.empty(num_periods * 2)
    all_widths[0::2] = final_widths0
    all_widths[1::2] = final_widths1

    # 用一条命令计算出所有连接点的x坐标
    junction_x = np.cumsum(all_lengths)
    # 计算所有波导段的起始x坐标
    start_x = np.insert(junction_x[:-1], 0, 0)

    # 将所有波导段直接添加为多边形
    for i in range(len(start_x)):
        x0, x1 = start_x[i], junction_x[i]
        w_half = all_widths[i] / 2
        if w_half > 0: # 避免添加零宽度多边形
            c.add_polygon([(x0, -w_half), (x1, -w_half), (x1, w_half), (x0, w_half)], layer=oplayer)

    # --- 4. 添加端口和加热器 ---
    total_length = junction_x[-1]

    # 添加光学端口
    c.add_port("o1", center=(0, 0), width=final_widths0[0], orientation=180, layer=oplayer)
    c.add_port("o2", center=(total_length, 0), width=final_widths1[-1], orientation=0, layer=oplayer)

    # 添加可选的加热器
    if IsHeat:
        c.add_polygon(
            [(0, -WidthHeat/2), (total_length, -WidthHeat/2), (total_length, WidthHeat/2), (0, WidthHeat/2)],
            layer=heatlayer
        )
        taper_len = (WidthRoute - WidthHeat) / 2
        # 仅在需要时才添加Taper（即引出线比加热条宽）
        if taper_len > 1e-9:
            heater_port1 = gf.Port('h_p1', center=(0, 0), width=WidthHeat, orientation=180, layer=heatlayer)
            heater_port2 = gf.Port('h_p2', center=(total_length, 0), width=WidthHeat, orientation=0, layer=heatlayer)

            taper = gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=taper_len, layer=heatlayer)
            ht1 = c << taper
            ht2 = c << taper

            ht1.connect("o1", heater_port1)
            ht2.connect("o1", heater_port2)
            c.add_port(name="h1", port=ht1.ports["o2"])
            c.add_port(name="h2", port=ht2.ports["o2"])
        else:
            c.add_port(name="h1", center=(0, 0), width=WidthHeat, orientation=180, layer=routelayer)
            c.add_port(name="h2", center=(total_length, 0), width=WidthHeat, orientation=0, layer=routelayer)

    # --- 5. 完成 ---
    # 如果定义了自定义的捕捉函数，则应用它
    c = snap_all_polygons_iteratively(c, Flag=True)
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
        Wcol=[1, 3],
        Lcol=[2, 4],
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
        (优化版) 使用矢量化计算从CSV文件创建采样DBR。

        本函数使用NumPy高效地实现了单位转换、条件偏移和周期采样等复杂逻辑，
        并随后直接生成多边形，以达到最优性能。

        参数:
            CSVName (str): CSV文件的完整路径。
            Offset (float): 应用于每周期中较宽部分的宽度偏移量。
            PeirdSampled (int): 一个采样超周期（super-period）内的总周期数。
            NumSampled (int): 在一个超周期末尾，宽度需要被修改的周期数。
            IsHeat (bool): 如果为True，则在DBR上方添加一个加热器。
            WidthHeat (float): 加热条的宽度。
            WidthRoute (float): 加热器引出金属的宽度。
            Wcol (list): CSV文件中宽度所在列的索引（1-based）。
            Lcol (list): CSV文件中长度所在列的索引（1-based）。
            oplayer (LayerSpec): 光学波导的GDS图层。
            heatlayer (LayerSpec): 加热器的GDS图层。
            routelayer (LayerSpec): 加热器引出金属的GDS图层。

        返回:
            Component: 生成的采样DBR的gdsfactory组件。
        """
    # --- 1. 数据加载与准备 ---
    try:
        data = np.loadtxt(CSVName, delimiter=',')
    except Exception as e:
        raise IOError(f"无法读取或解析CSV文件，路径: {CSVName}。错误: {e}")

    num_periods = len(data)
    indices = np.arange(num_periods)

    # 将指定列的数据提取到命名清晰的数组中
    lengths0 = data[:, Lcol[0] - 1]
    lengths1 = data[:, Lcol[1] - 1]
    widths0 = data[:, Wcol[0] - 1]
    widths1 = data[:, Wcol[1] - 1]

    # --- 2. 矢量化逻辑应用 ---

    # A. 单位转换：如果数值很小（比如单位是米），则将其转换为微米
    # lengths0[lengths0 < 1e-5] *= 1e6
    # lengths1[lengths1 < 1e-5] *= 1e6
    # widths0[widths0 < 1e-5] *= 1e6
    # widths1[widths1 < 1e-5] *= 1e6

    # B. 条件偏移：为每个周期中较宽的部分增加偏移量
    # 使用 np.where 实现矢量化的 if/else 语句，效率极高。
    is_w0_wider = widths0 > widths1
    w0_after_offset = np.where(is_w0_wider, widths0 + Offset, widths0)
    w1_after_offset = np.where(~is_w0_wider, widths1 + Offset, widths1)

    # C. 周期采样：对指定的周期，将 width0 设置为与 width1 相等
    # 为需要被采样的周期创建一个布尔掩码（boolean mask）。
    sampling_mask = (indices % PeirdSampled) > (PeirdSampled - NumSampled - 1)  # 为适应0-based索引进行调整
    w0_after_sampling = np.where(sampling_mask, w1_after_offset, w0_after_offset)

    # D. 网格捕捉/取整：将宽度取整到最接近的2nm (0.002µm)
    # round(val * 500) / 500 的效果等同于取整到最接近的 1/500。
    final_widths0 = np.round(w0_after_sampling * 500) / 500
    final_widths1 = np.round(w1_after_offset * 500) / 500

    # --- 3. 几何生成 ---
    c = gf.Component()

    # 将所有波导段的长度和宽度交错排列到一个数组中
    all_lengths = np.empty(num_periods * 2)
    all_lengths[0::2] = lengths0
    all_lengths[1::2] = lengths1

    all_widths = np.empty(num_periods * 2)
    all_widths[0::2] = final_widths0
    all_widths[1::2] = final_widths1

    # 用一条命令计算出所有连接点的x坐标
    junction_x = np.cumsum(all_lengths)
    # 计算所有波导段的起始x坐标
    start_x = np.insert(junction_x[:-1], 0, 0)

    # 将所有波导段直接添加为多边形
    for i in range(len(start_x)):
        x0, x1 = start_x[i], junction_x[i]
        w_half = all_widths[i] / 2
        c.add_polygon([(x0, -w_half), (x1, -w_half), (x1, w_half), (x0, w_half)], layer=oplayer)

    # --- 4. 添加端口和加热器 ---
    total_length = junction_x[-1]

    # 添加光学端口
    c.add_port("o1", center=(0, 0), width=final_widths0[0], orientation=180, layer=oplayer)
    c.add_port("o2", center=(total_length, 0), width=final_widths1[-1], orientation=0, layer=oplayer)

    # 添加可选的加热器
    if IsHeat:
        c.add_polygon(
            [(0, -WidthHeat / 2), (total_length, -WidthHeat / 2), (total_length, WidthHeat / 2), (0, WidthHeat / 2)],
            layer=heatlayer
        )
        taper_len = (WidthRoute - WidthHeat) / 2
        # 仅在需要时才添加Taper（即引出线比加热条宽）
        if taper_len > 1e-9:
            heater_port1 = gf.Port('h_p1', center=(0, 0), width=WidthHeat, orientation=180, layer=heatlayer)
            heater_port2 = gf.Port('h_p2', center=(total_length, 0), width=WidthHeat, orientation=0, layer=heatlayer)

            taper = gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=taper_len, layer=heatlayer)
            ht1 = c << taper
            ht2 = c << taper

            ht1.connect("o1", heater_port1)
            ht2.connect("o1", heater_port2)
            c.add_port(name="h1", port=ht1.ports["o2"])
            c.add_port(name="h2", port=ht2.ports["o2"])
        else:
            c.add_port(name="h1", center=(0, 0), width=WidthHeat, orientation=180, layer=routelayer)
            c.add_port(name="h2", center=(total_length, 0), width=WidthHeat, orientation=0, layer=routelayer)

    # --- 5. 完成 ---
    # 如果定义了自定义的捕捉函数，则应用它
    c.flatten()
    c = snap_all_polygons_iteratively(c, Flag=True)
    return c
# %% DBRFromCsv: 从 CSV 文件创建 DBR
@gf.cell
def EstrDBRFromCsvOffset(
        CSVName: str = "D:/Mask Download/Temp202311_LN_ZJ/单_D01.5e-25_k0.5_1500-1600.csv",  # CSV 文件路径
        WidthMidWG: float = 0.8,
        GapMidSide: float = 0.2,
        WidthHeat: float = 4,  # 加热器宽度 (µm)
        WidthRoute: float = 10,  # 加热器路由宽度 (µm)
        Offset: float = 0.5,
        IsHeat: bool = False,  # 是否包含加热器
        Wcol=[1, 3],
        Lcol=[2, 4],
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        UseParallel: bool = True
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
    """
        (优化版) 从 CSV 文件创建 DBR，使用矢量化计算以实现高性能。

        此版本使用 NumPy 预先计算所有几何坐标，然后通过 `add_polygon` 批量添加几何形状，
        避免了创建和连接大量独立组件所带来的缓慢迭代过程。
        函数的参数、功能和最终生成的几何图形与原始版本完全相同。
        """
    # --- 1. 数据加载与准备 ---
    # 一次性将 CSV 加载到 NumPy 数组中，以进行高效的矢量化计算
    try:
        data = np.loadtxt(CSVName, delimiter=',')
    except FileNotFoundError:
        raise FileNotFoundError(f"错误：找不到CSV文件，路径: {CSVName}")
    except Exception as e:
        raise ValueError(f"无法读取CSV文件。请确保文件格式有效。 错误: {e}")

    # 将指定列的数据提取到命名清晰的数组中
    # 参数中的列是1-based索引, Numpy是0-based, 因此减1
    widths0 = data[:, Wcol[0] - 1]
    lengths0 = data[:, Lcol[0] - 1]
    widths1 = data[:, Wcol[1] - 1]
    lengths1 = data[:, Lcol[1] - 1]
    num_periods = len(data)

    # --- 2. 几何坐标的矢量化计算 ---
    c = gf.Component()

    # A. 计算侧边“牙齿”的宽度
    # 根据原始逻辑，牙齿宽度由每个周期中较宽的波导决定，并加上偏移量
    side_widths = np.maximum(widths0, widths1) + Offset

    # B. 批量计算所有X坐标
    # 每个周期的总长度
    period_lengths = lengths0 + lengths1
    # DBR结构的总长度
    total_length = np.sum(period_lengths)

    # 计算每个周期内“牙齿”的起始和结束X坐标，这一步替代了迭代`connect`
    period_start_x = np.insert(np.cumsum(period_lengths[:-1]), 0, 0)
    teeth_start_x = period_start_x + lengths0
    teeth_end_x = teeth_start_x + lengths1

    # --- 3. 将几何图形添加为多边形 ---

    # A. 将中心连续波导添加为一整个长方形
    y_mid_half = WidthMidWG / 2
    c.add_polygon(
        [(0, -y_mid_half), (total_length, -y_mid_half), (total_length, y_mid_half), (0, y_mid_half)],
        layer=oplayer,
    )

    # B. 批量添加侧边的“牙齿”
    # 这里的循环速度很快，因为内部只涉及从数组中取值和简单的加法
    for i in range(num_periods):
        x_start, x_end = teeth_start_x[i], teeth_end_x[i]
        w_side = side_widths[i]

        # 上方的牙齿
        y_top_bottom = GapMidSide - w_side/2
        y_top_top = GapMidSide + w_side/2
        c.add_polygon(
            [(x_start, y_top_bottom), (x_end, y_top_bottom), (x_end, y_top_top), (x_start, y_top_top)],
            layer=oplayer,
        )

        # 下方的牙齿
        y_bot_top = -GapMidSide + w_side/2
        y_bot_bottom = -GapMidSide - w_side/2
        c.add_polygon(
            [(x_start, y_bot_top), (x_end, y_bot_top), (x_end, y_bot_bottom), (x_start, y_bot_bottom)],
            layer=oplayer,
        )

    # --- 4. 添加端口和可选的加热器 ---
    c.add_port("o1", center=(0, 0), width=WidthMidWG, orientation=180, layer=oplayer)
    c.add_port("o2", center=(total_length, 0), width=WidthMidWG, orientation=0, layer=oplayer)

    if IsHeat:
        # 添加主加热条
        y_heat_half = WidthHeat / 2
        c.add_polygon(
            [(0, -y_heat_half), (total_length, -y_heat_half), (total_length, y_heat_half), (0, y_heat_half)],
            layer=heatlayer,
        )

        # 添加加热器的Taper引出线
        taper_len = (WidthRoute - WidthHeat) / 2
        if taper_len > 1e-9:  # 仅在需要taper时添加
            heater_port1 = gf.Port('h_p1', center=(0, 0), width=WidthHeat, orientation=180, layer=heatlayer)
            heater_port2 = gf.Port('h_p2', center=(total_length, 0), width=WidthHeat, orientation=0, layer=heatlayer)

            taper = gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=taper_len, layer=heatlayer)
            ht1 = c << taper
            ht2 = c << taper

            ht1.connect("o1", heater_port1)
            ht2.connect("o1", heater_port2)
            c.add_port(name="h1", port=ht1.ports["o2"])
            c.add_port(name="h2", port=ht2.ports["o2"])
        else:  # 如果宽度相同或更小，则直接添加端口
            c.add_port(name="h1", center=(0, 0), width=WidthHeat, orientation=180, layer=routelayer)
            c.add_port(name="h2", center=(total_length, 0), width=WidthHeat, orientation=0, layer=routelayer)

    # --- 5. 完成 ---
    c.flatten()
    return c
# %% EDBR structure Repeat
@gf.cell()
def EDBRStrRep(
        Structure:Component = None,
        WidthMidWG: float = 0.8,
        WidthSide:float = 0.2,
        GapMidSide: float = 0.2,
        DutyCycle: float = 0.35,  # 占空比
        NumPeriod: int = 100,
        LengthPeriod: float = 1.1,
        WidthHeat: float = 4,  # 加热器宽度 (µm)
        WidthRoute: float = 10,  # 加热器路由宽度 (µm)
        Offset: float = 0.5,
        IsHeat: bool = False,  # 是否包含加热器
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        UseParallel: bool = True
)->Component:
    c = gf.Component()
    if Structure is not None:
        ybbox = Structure.bbox_np()
        xmin = ybbox[0][0]
        xmax = ybbox[1][0]
        LengthPeriod = xmax - xmin
        for i in range(NumPeriod):
            structi = c << Structure
            structi.movex(LengthPeriod * i)
            if i == 0:
                c.add_port('o1',port=structi.ports['o1'])
            if i == NumPeriod-1:
                c.add_port('o2', port=structi.ports['o2'])
    else:
        Structure = gf.Component()
        Cmid = gf.Section(width=WidthMidWG,layer=oplayer,port_names=('o1','o2'))
        Cu = gf.Section(width=WidthSide+Offset,layer=oplayer,port_names=('o1u','o2u'),offset=GapMidSide)
        Cd = gf.Section(width=WidthSide+Offset,layer=oplayer,port_names=('o1d','o2d'),offset=-GapMidSide)
        X1 = gf.CrossSection(sections=(Cmid,))
        X2 = gf.CrossSection(sections=(Cmid,Cd,Cu))
        p1 = gf.path.straight(length=LengthPeriod*(1-DutyCycle))
        p2 = gf.path.straight(length=LengthPeriod*DutyCycle)
        S1 = Structure << gf.path.extrude(p1,cross_section=X1)
        S2 = Structure << gf.path.extrude(p2,cross_section=X2)
        S2.connect('o1',S1.ports['o2'])
        Structure.add_port('o1',port=S1.ports['o1'])
        Structure.add_port('o2',port=S2.ports['o2'])
        for i in range(NumPeriod):
            structi = c << Structure
            structi.movex(LengthPeriod *i)
            if i == 0:
                c.add_port('o1',port=structi.ports['o1'])
            if i == NumPeriod-1:
                c.add_port('o2', port=structi.ports['o2'])
    if IsHeat:
        # 添加主加热条
        total_length = NumPeriod*LengthPeriod
        y_heat_half = WidthHeat / 2
        c.add_polygon(
            [(0, -y_heat_half), (total_length, -y_heat_half), (total_length, y_heat_half), (0, y_heat_half)],
            layer=heatlayer,
        )

        # 添加加热器的Taper引出线
        taper_len = (WidthRoute - WidthHeat) / 2
        if taper_len > 1e-9:  # 仅在需要taper时添加
            heater_port1 = gf.Port('h_p1', center=(0, 0), width=WidthHeat, orientation=180, layer=heatlayer)
            heater_port2 = gf.Port('h_p2', center=(total_length, 0), width=WidthHeat, orientation=0, layer=heatlayer)

            taper = gf.c.taper(width1=WidthHeat, width2=WidthRoute, length=taper_len, layer=heatlayer)
            ht1 = c << taper
            ht2 = c << taper

            ht1.connect("o1", heater_port1)
            ht2.connect("o1", heater_port2)
            c.add_port(name="h1", port=ht1.ports["o2"])
            c.add_port(name="h2", port=ht2.ports["o2"])
        else:  # 如果宽度相同或更小，则直接添加端口
            c.add_port(name="h1", center=(0, 0), width=WidthHeat, orientation=180, layer=routelayer)
            c.add_port(name="h2", center=(total_length, 0), width=WidthHeat, orientation=0, layer=routelayer)
    return c
# %% 导出所有函数
__all__ = ['DBR', 'DBRFromCsv', 'DBRFromCsvOffset','SGDBRFromCsvOffset','EstrDBRFromCsvOffset','EDBRStrRep']
