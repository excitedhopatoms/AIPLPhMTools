import csv

from .BasicDefine import *
from .SnapMerge import *
import re
@gf.cell()
def EDBRStrRep(
        Structure: Component = None,
        WidthMidWG: float = 0.8,
        WidthSide: float = 0.2,
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
) -> Component:
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
                c.add_port('o1', port=structi.ports['o1'])
            if i == NumPeriod - 1:
                c.add_port('o2', port=structi.ports['o2'])
    else:
        Structure = gf.Component()
        Cmid = gf.Section(width=WidthMidWG, layer=oplayer, port_names=('o1', 'o2'))
        Cu = gf.Section(width=WidthSide + Offset, layer=oplayer, port_names=('o1u', 'o2u'), offset=GapMidSide)
        Cd = gf.Section(width=WidthSide + Offset, layer=oplayer, port_names=('o1d', 'o2d'), offset=-GapMidSide)
        X1 = gf.CrossSection(sections=(Cmid,))
        X2 = gf.CrossSection(sections=(Cmid, Cd, Cu))
        p1 = gf.path.straight(length=LengthPeriod * (1 - DutyCycle))
        p2 = gf.path.straight(length=LengthPeriod * DutyCycle)
        S1 = Structure << gf.path.extrude(p1, cross_section=X1)
        S2 = Structure << gf.path.extrude(p2, cross_section=X2)
        S2.connect('o1', S1.ports['o2'])
        Structure.add_port('o1', port=S1.ports['o1'])
        Structure.add_port('o2', port=S2.ports['o2'])
        for i in range(NumPeriod):
            structi = c << Structure
            structi.movex(LengthPeriod * i)
            if i == 0:
                c.add_port('o1', port=structi.ports['o1'])
            if i == NumPeriod - 1:
                c.add_port('o2', port=structi.ports['o2'])
    if IsHeat:
        # 添加主加热条
        total_length = NumPeriod * LengthPeriod
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
    # c.flatten()
    return c
# 按cell反转的EDBR
@gf.cell()
def EDBRStrRep_InvertTone(
        Structure: Component = None,
        WidthMidWG: float = 0.8,
        WidthSide: float = 0.2,
        GapMidSide: float = 0.2,
        DutyCycle: float = 0.35,  # 占空比
        NumPeriod: int = 100,
        LengthPeriod: float = 1.1,
        WidthHeat: float = 4,     # 加热器宽度 (µm)
        WidthRoute: float = 10,   # 加热器路由宽度 (µm)
        Offset: float = 0.5,
        IsHeat: bool = False,     # 是否包含加热器
        strlayer:LayerSpec = None,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        UseParallel: bool = True,
        TrenchWidth: float = 4.0  # 正胶版图单侧背景挖槽宽度 (µm，含半波导宽度)
) -> Component:
    """
    专门用于生成正胶 (反相) 布拉格反射器 (DBR) 结构的函数。
    通过在单周期层面进行布尔相减并阵列，极大优化了GDS文件大小和渲染速度。
    """
    c = gf.Component()
    if strlayer is None:
        strlayer = oplayer
    # ---------------------------------------------------------
    # 1. 生成或获取单周期基础结构 (正相)
    # ---------------------------------------------------------
    if Structure is not None:
        if 'o1' in Structure.ports and 'o2' in Structure.ports:
            LengthPeriod = abs(Structure.ports['o2'].center[0] - Structure.ports['o1'].center[0])
            xmin = Structure.ports['o1'].center[0]
        else:
            ybbox = Structure.bbox_np()
            xmin = ybbox[0][0]
            xmax = ybbox[1][0]
            LengthPeriod = xmax - xmin
    else:
        Structure = gf.Component()
        Cmid = gf.Section(width=WidthMidWG, layer=strlayer, port_names=('o1', 'o2'))
        Cu = gf.Section(width=WidthSide + Offset, layer=strlayer, port_names=('o1u', 'o2u'), offset=GapMidSide)
        Cd = gf.Section(width=WidthSide + Offset, layer=strlayer, port_names=('o1d', 'o2d'), offset=-GapMidSide)
        X1 = gf.CrossSection(sections=(Cmid,))
        X2 = gf.CrossSection(sections=(Cmid, Cd, Cu))
        
        p1 = gf.path.straight(length=LengthPeriod * (1 - DutyCycle))
        p2 = gf.path.straight(length=LengthPeriod * DutyCycle)
        
        S1 = Structure << gf.path.extrude(p1, cross_section=X1)
        S2 = Structure << gf.path.extrude(p2, cross_section=X2)
        S2.connect('o1', S1.ports['o2'])
        
        Structure.add_port('o1', port=S1.ports['o1'])
        Structure.add_port('o2', port=S2.ports['o2'])
        xmin = Structure.ports['o1'].center[0]
    print(LengthPeriod)
    # ---------------------------------------------------------
    # 2. 核心逻辑：执行单周期布尔相减 (Invert Tone)
    # ---------------------------------------------------------
    # 创建单周期大小的背景矩形
    S_trench = gf.Section(width=2*TrenchWidth,layer=oplayer,port_names=('o1', 'o2'))
    X_trench = gf.CrossSection(sections=(S_trench,))
    bg = gf.components.straight(length=LengthPeriod,cross_section=X_trench)
    temp_bg_comp = gf.Component()
    bg_ref = temp_bg_comp << bg
    # bg_ref.move((xmin, 0))
    print(xmin)
    # 将背景与原始单周期相减 (A - B)
    inverted_struct = gf.boolean(
        A=temp_bg_comp, 
        B=Structure, 
        operation='A-B',
        layer=oplayer,
        layer1=oplayer,
        layer2=strlayer,
    )
    
    # 恢复因布尔运算丢失的端口信息
    inverted_struct.add_port('o1', port=Structure.ports['o1'])
    inverted_struct.add_port('o2', port=Structure.ports['o2'])
    
    # 将需要阵列的结构替换为反相后的 Cell
    inverted_struct << Structure

    # ---------------------------------------------------------
    # 3. 阵列反相后的单周期 (保持 Cell 复用)
    # ---------------------------------------------------------
    for i in range(NumPeriod):
        structi = c << inverted_struct
        structi.movex(LengthPeriod * i)
        if i == 0:
            c.add_port('o1', port=structi.ports['o1'])
        if i == NumPeriod - 1:
            c.add_port('o2', port=structi.ports['o2'])
            
    # ---------------------------------------------------------
    # 4. 附加结构：加热器逻辑
    # ---------------------------------------------------------
    if IsHeat:
        total_length = NumPeriod * LengthPeriod
        y_heat_half = WidthHeat / 2
        
        # 主加热条
        c.add_polygon(
            [(0, -y_heat_half), (total_length, -y_heat_half), (total_length, y_heat_half), (0, y_heat_half)],
            layer=heatlayer,
        )

        # 加热器的Taper引出线
        taper_len = (WidthRoute - WidthHeat) / 2
        if taper_len > 1e-9:
            heater_port1 = gf.Port('h_p1', center=(0, 0), width=WidthHeat, orientation=180, layer=heatlayer)
            heater_port2 = gf.Port('h_p2', center=(total_length, 0), width=WidthHeat, orientation=0, layer=heatlayer)

            taper = gf.components.taper(width1=WidthHeat, width2=WidthRoute, length=taper_len, layer=heatlayer)
            ht1 = c << taper
            ht2 = c << taper

            ht1.connect("o1", heater_port1)
            ht2.connect("o1", heater_port2)
            
            c.add_port(name="h1", port=ht1.ports["o2"])
            c.add_port(name="h2", port=ht2.ports["o2"])
        else:
            c.add_port(name="h1", center=(0, 0), width=WidthHeat, orientation=180, layer=routelayer)
            c.add_port(name="h2", center=(total_length, 0), width=WidthHeat, orientation=0, layer=routelayer)
            
    return c
def _parse_edbr_csv(csv_path: str) -> dict:
    """
    解析 E-DBR 版图 CSV, 自动识别 PP(2列) 或 LPD(4列) 格式。

    返回:
        dict: {
            'params': {...},
            'format': 'PP' | 'LPD',
            'upper_blocks': ndarray (N,2),
            'lower_blocks': ndarray (N,2),
        }
    """
    params = {}
    rows = []
    fmt = None

    with open(csv_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith('%'):
                m = re.match(r'%\s*(\S+)\s*=\s*(.+)', line)
                if m:
                    key = m.group(1).strip()
                    val_str = m.group(2).strip()
                    try:
                        params[key] = float(val_str) if '.' in val_str else int(val_str)
                    except ValueError:
                        params[key] = val_str
                continue

            if 'start' in line.lower():
                ncols = len(line.split(','))
                fmt = 'LPD' if ncols >= 4 else 'PP'
                continue

            parts = line.split(',')
            nums = []
            for p in parts:
                p = p.strip()
                try:
                    nums.append(float(p)) if p else nums.append(np.nan)
                except ValueError:
                    nums.append(np.nan)
            if nums:
                rows.append(nums)

    if fmt is None and rows:
        fmt = 'LPD' if len(rows[0]) >= 4 else 'PP'
    if fmt is None:
        fmt = 'LPD' if 'LPD' in str(params.get('apodization_method', '')).upper() else 'PP'

    if fmt == 'LPD':
        upper_blocks, lower_blocks = [], []
        for row in rows:
            if len(row) >= 4:
                if not np.isnan(row[0]) and not np.isnan(row[1]):
                    upper_blocks.append([row[0], row[1]])
                if not np.isnan(row[2]) and not np.isnan(row[3]):
                    lower_blocks.append([row[2], row[3]])
            elif len(row) >= 2 and not np.isnan(row[0]):
                upper_blocks.append([row[0], row[1]])
        upper_blocks = np.array(upper_blocks) if upper_blocks else np.empty((0, 2))
        lower_blocks = np.array(lower_blocks) if lower_blocks else np.empty((0, 2))
    else:
        blocks = []
        for row in rows:
            if len(row) >= 2 and not np.isnan(row[0]) and not np.isnan(row[1]):
                blocks.append([row[0], row[1]])
        blocks = np.array(blocks) if blocks else np.empty((0, 2))
        upper_blocks = blocks
        lower_blocks = blocks.copy()

    return {
        'params': params,
        'format': fmt,
        'upper_blocks': upper_blocks,
        'lower_blocks': lower_blocks,
    }

def _merge_blocks(blocks: np.ndarray, tol: float) -> np.ndarray:
    if len(blocks) <= 1 or tol <= 0:
        return blocks
    merged = [blocks[0].copy()]
    for i in range(1, len(blocks)):
        if blocks[i, 0] - merged[-1][1] <= tol:
            merged[-1][1] = blocks[i, 1]
        else:
            merged.append(blocks[i].copy())
    return np.array(merged)
@gf.cell()
def EDBRStrRep_InvertTone_Full(
        WidthMidWG: float = 0.8,
        WidthSide: float = 0.2,
        GapMidSide: float = 0.2,
        DutyCycle: float = 0.35,
        NumPeriod: int = 100,
        LengthPeriod: float = 1.1,
        IsHeat: bool = False,
        WidthHeat: float = 4,
        WidthRoute: float = 10,
        tin: Component | None = None,
        tout: Component | None = None,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
        TrenchWidth: float = 4.0,
) -> Component:
    """
    DBR + 端面耦合器 + 整体取反（正胶版图）。

    与 EDBRStrRep_InvertTone 的核心区别：
    本函数先将 DBR 与两端 taper 组装为完整正相结构，
    再整体做一次布尔相减（A-B），从而彻底避免分块取反时
    各块背景矩形在拼接处互相重叠、覆盖 DBR 空白区域的问题。

    Args:
        WidthMidWG: DBR 中心波导宽度 (um)
        WidthSide: DBR 侧边齿宽度 (um)
        GapMidSide: 中心波导与侧边齿间隙 (um)
        DutyCycle: 占空比
        NumPeriod: DBR 周期数
        LengthPeriod: 单周期长度 (um)
        IsHeat: 是否包含加热器
        WidthHeat: 加热器宽度 (um)
        WidthRoute: 加热器引出金属宽度 (um)
        tin: 输入端 taper 组件 (o1=外侧, o2=DBR侧)，None 则自动生成
        tout: 输出端 taper 组件 (o1=DBR侧, o2=外侧)，None 则自动生成
        oplayer: 光波导图层
        heatlayer: 加热器图层
        routelayer: 加热器引出金属图层
        vialayer: 通孔图层
        TrenchWidth: 正胶版图外扩的背景挖槽宽度 (um)

    Returns:
        Component: 整体取反后的 DBR + 端面耦合器组件
    """
    if tin is None:
        tin = gf.components.taper(
            width1=0.15, width2=WidthMidWG,
            length=200.0, layer=oplayer
        )
    if tout is None:
        tout = gf.components.taper(
            width1=WidthMidWG, width2=0.15,
            length=200.0, layer=oplayer
        )

    dbr = EDBRStrRep(
        WidthMidWG=WidthMidWG,
        WidthSide=WidthSide,
        GapMidSide=GapMidSide,
        DutyCycle=DutyCycle,
        NumPeriod=NumPeriod,
        LengthPeriod=LengthPeriod,
        IsHeat=False,
        oplayer=oplayer,
    )

    full = gf.Component()

    tin_ref = full << tin
    dbr_ref = full << dbr
    dbr_ref.connect('o1', tin_ref.ports['o2'])

    tout_ref = full << tout
    tout_ref.connect('o1', dbr_ref.ports['o2'])

    full.add_port('o1', port=tin_ref.ports['o1'])
    full.add_port('o2', port=tout_ref.ports['o2'])

    bbox = full.bbox_np()
    xmin, ymin = bbox[0][0], bbox[0][1]
    xmax, ymax = bbox[1][0], bbox[1][1]

    bg_width = xmax - xmin
    bg_height = ymax - ymin + 2 * TrenchWidth

    bg = gf.components.rectangle(size=(bg_width, bg_height), layer=oplayer)
    temp_bg = gf.Component()
    bg_ref = temp_bg << bg
    bg_ref.move((xmin, ymin - TrenchWidth))

    inverted = gf.boolean(A=temp_bg, B=full, operation='A-B', layer=oplayer)

    for port in full.ports:
        inverted.add_port(port.name, port=port)

    if IsHeat:
        total_length = NumPeriod * LengthPeriod
        tin_bbox = tin.bbox_np()
        dbr_start_x = tin_bbox[1][0] - tin_bbox[0][0]

        y_heat_half = WidthHeat / 2
        inverted.add_polygon(
            [(dbr_start_x, -y_heat_half),
             (dbr_start_x + total_length, -y_heat_half),
             (dbr_start_x + total_length, y_heat_half),
             (dbr_start_x, y_heat_half)],
            layer=heatlayer,
        )

        taper_len = (WidthRoute - WidthHeat) / 2
        if taper_len > 1e-9:
            heater_port1 = gf.Port('h_p1', center=(dbr_start_x, 0), width=WidthHeat, orientation=180, layer=heatlayer)
            heater_port2 = gf.Port('h_p2', center=(dbr_start_x + total_length, 0), width=WidthHeat, orientation=0, layer=heatlayer)

            taper = gf.components.taper(width1=WidthHeat, width2=WidthRoute, length=taper_len, layer=heatlayer)
            ht1 = inverted << taper
            ht2 = inverted << taper

            ht1.connect("o1", heater_port1)
            ht2.connect("o1", heater_port2)

            inverted.add_port(name="h1", port=ht1.ports["o2"])
            inverted.add_port(name="h2", port=ht2.ports["o2"])
        else:
            inverted.add_port(name="h1", center=(dbr_start_x, 0), width=WidthHeat, orientation=180, layer=routelayer)
            inverted.add_port(name="h2", center=(dbr_start_x + total_length, 0), width=WidthHeat, orientation=0, layer=routelayer)

    return inverted


def make_flush_inverted_cell(
        comp: Component,
        trench_width: float = 4.0,
        layer: LayerSpec = LAYER.WG
) -> Component:
    """
    通用反相转换器：将任意双端口正向组件转换为"首尾平齐"的反相(正胶)组件。

    核心思路：背景矩形在端口处一刀切平，只在上下两侧扩宽，
    不在端口沿传播方向伸长。这样多个反相组件拼接时，
    背景能无缝融合，内部光路不会被堵死。

    Args:
        comp: 原始正向组件（需有 o1, o2 端口）
        trench_width: 上下两侧外扩宽度 (um)
        layer: 目标图层

    Returns:
        首尾平齐的反相组件
    """
    p1 = comp.ports['o1'] if 'o1' in comp.ports else None
    p2 = comp.ports['o2'] if 'o2' in comp.ports else None

    if p1 and p2:
        x_min = min(p1.center[0], p2.center[0])
        x_max = max(p1.center[0], p2.center[0])
    else:
        bbox = comp.bbox_np()
        x_min = bbox[0][0]
        x_max = bbox[1][0]

    length = x_max - x_min

    bg = gf.components.rectangle(size=(length, trench_width), layer=layer)
    temp_bg = gf.Component()
    bg_ref = temp_bg << bg
    bg_ref.move((x_min, -trench_width / 2))

    inverted_comp = gf.boolean(
        A=temp_bg,
        B=comp,
        operation='A-B',
        layer=layer
    )

    for port in comp.ports:
        inverted_comp.add_port(port.name, port=port)

    return inverted_comp


@gf.cell()
def Complete_Inverted_Device(
        NumPeriod: int = 100,
        LengthPeriod: float = 1.1,
        WidthMidWG: float = 0.8,
        WidthSide: float = 0.2,
        GapMidSide: float = 0.2,
        DutyCycle: float = 0.35,
        TrenchWidth: float = 4.0,
        IsHeat: bool = False,
        WidthHeat: float = 4,
        WidthRoute: float = 10,
        tin: Component | None = None,
        tout: Component | None = None,
        oplayer: LayerSpec = LAYER.WG,
        heatlayer: LayerSpec = LAYER.M1,
        routelayer: LayerSpec = LAYER.M2,
        vialayer: LayerSpec = LAYER.VIA,
) -> Component:
    """
    完整反相器件：输入 taper + DBR + 输出 taper，全部平齐拼接。

    采用"平齐拼图"策略：每个子结构独立反相，但背景矩形在端口处
    一刀切平，拼接时背景无缝融合，光路畅通。

    Args:
        NumPeriod: DBR 周期数
        LengthPeriod: DBR 单周期长度 (um)
        WidthMidWG: DBR 中心波导宽度 (um)
        WidthSide: DBR 侧边齿宽度 (um)
        GapMidSide: 中心波导与侧边齿间隙 (um)
        DutyCycle: DBR 占空比
        TrenchWidth: 全局挖槽宽度 (um)
        IsHeat: 是否包含加热器
        WidthHeat: 加热器宽度 (um)
        WidthRoute: 加热器引出金属宽度 (um)
        tin: 输入端 taper 组件 (o1=外侧, o2=DBR侧)，None 则自动生成
        tout: 输出端 taper 组件 (o1=DBR侧, o2=外侧)，None 则自动生成
        oplayer: 光波导图层
        heatlayer: 加热器图层
        routelayer: 加热器引出金属图层
        vialayer: 通孔图层

    Returns:
        完整拼接的反相器件
    """
    if tin is None:
        tin = gf.components.taper(
            width1=0.15, width2=WidthMidWG,
            length=200.0, layer=oplayer
        )
    if tout is None:
        tout = gf.components.taper(
            width1=WidthMidWG, width2=0.15,
            length=200.0, layer=oplayer
        )

    c = gf.Component()

    dbr_inv = EDBRStrRep_InvertTone(
        WidthMidWG=WidthMidWG,
        WidthSide=WidthSide,
        GapMidSide=GapMidSide,
        DutyCycle=DutyCycle,
        NumPeriod=NumPeriod,
        LengthPeriod=LengthPeriod,
        IsHeat=IsHeat,
        WidthHeat=WidthHeat,
        WidthRoute=WidthRoute,
        oplayer=oplayer,
        heatlayer=heatlayer,
        routelayer=routelayer,
        vialayer=vialayer,
        TrenchWidth=TrenchWidth,
    )

    tin_inv = make_flush_inverted_cell(tin, trench_width=TrenchWidth, layer=oplayer)
    tout_inv = make_flush_inverted_cell(tout, trench_width=TrenchWidth, layer=oplayer)

    ref_dbr = c << dbr_inv

    ref_tin = c << tin_inv
    ref_tin.connect('o2', ref_dbr.ports['o1'])

    ref_tout = c << tout_inv
    ref_tout.connect('o1', ref_dbr.ports['o2'])

    c.add_port('o1', port=ref_tin.ports['o1'])
    c.add_port('o2', port=ref_tout.ports['o2'])

    if IsHeat:
        for pname in ['h1', 'h2']:
            if pname in dbr_inv.ports:
                c.add_port(pname, port=dbr_inv.ports[pname])

    return c


# %% 导出所有函数
__all__ = ['EDBRStrRep_InvertTone', 'EDBRStrRep_InvertTone_Full', 'make_flush_inverted_cell', 'Complete_Inverted_Device']
