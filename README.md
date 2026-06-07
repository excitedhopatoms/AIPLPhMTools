# AIPLPhMTools

**PKU-AIPL 光子集成电路（PIC）组件 PDK**

基于 [gdsfactory v9](https://github.com/gdsfactory/gdsfactory) 的光子器件设计、仿真和版图生成工具包。

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![gdsfactory](https://img.shields.io/badge/gdsfactory-9.14%2B-orange)](https://gdsfactory.github.io/gdsfactory/)

---

## 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [包结构](#包结构)
- [API 参考](#api-参考)
  - [工具函数](#工具函数)
  - [基础定义 (BasicDefine)](#基础定义-basicdefine)
  - [环形谐振器 (Ring)](#环形谐振器-ring)
  - [跑道型谐振器 (RaceTrack)](#跑道型谐振器-racetrack)
  - [耦合器与 MZI (CouplerMZI)](#耦合器与-mzi-couplermzi)
  - [DBR 反射器 (DBR)](#dbr-反射器-dbr)
  - [加热器 (Heater)](#加热器-heater)
  - [电极 (ELE)](#电极-ele)
  - [回旋镖谐振器 (Boomerang)](#回旋镖谐振器-boomerang)
  - [多环结构 (MultiRing / MultiRaceTrack)](#多环结构-multiring--multitrack)
  - [隔离器 (Isolator)](#隔离器-isolator)
  - [Memyshev 激光器 (memyshev)](#memyshev-激光器-memyshev)
  - [外腔激光器 (ExtCav)](#外腔激光器-extcav)
  - [王字形微腔 (WangCavity)](#王字形微腔-wangcavity)
  - [测试结构 (TC 系列)](#测试结构-tc-系列)
  - [DRC 预处理 (SnapMerge)](#drc-预处理-snapmerge)
  - [通用版图绘制引擎 (layout_engine)](#通用版图绘制引擎-layout_engine)
- [批量生成 GDS](#批量生成-gds)
- [注意事项](#注意事项)

---

## 安装

### 环境要求

- Python >= 3.10
- gdsfactory >= 9.14.0
- numpy >= 1.24
- kfactory >= 1.13

### 从源码安装

```bash
git clone <repository-url>
cd AIPLPhMTools
pip install -e .
```

### 开发模式安装

```bash
pip install -e ".[dev]"
```

---

## 快速开始

```python
import AIPLPhMTools as ap

# 查看所有可用组件
print(ap.list_components())

# 创建直波导
wg = ap.GfCStraight(length=20, width=1)
wg.show()                    # 在 KLayout 中交互查看
wg.write_gds("wg.gds")       # 导出 GDS 文件

# 创建环形谐振器
ring = ap.RingPulley(r_ring=50, width_ring=0.8)
ring.show()

# 创建跑道型谐振器
rt = ap.RaceTrackP(r_ring=50, length=20, width_ring=0.8)
rt.write_gds("racetrack.gds")

# 创建 MZI
mzi = ap.DMZI(delta_length=100)
mzi.show()

# 创建 DBR
dbr = ap.DBR(length=200, period=0.3, width=0.5)
dbr.write_gds("dbr.gds")

# 使用工艺预设配置
config = ap.get_preset_config("700nmSiN")
print(config.waveguide.width_ring)  # 1.0
```

---

## 包结构

```
AIPLPhMTools/
├── __init__.py              # 包入口，延迟导入 + 显式导出
├── FabBasic_hjh/            # 器件库（核心版图组件）
│   ├── BasicDefine.py       # 基础定义（图层、截面、直波导、弯曲等）
│   ├── Ring.py              # 环形谐振器（Pulley耦合、山形环、回旋镖环等）
│   ├── RaceTrack.py         # 跑道型谐振器（Pulley/直线耦合）
│   ├── CouplerMZI.py        # 耦合器与MZI（定向耦合器、Sagnac环等）
│   ├── DBR.py               # 分布式布拉格反射器
│   ├── Heater.py            # 加热器（蛇形加热器、过孔阵列等）
│   ├── ELE.py               # 电极（GSG高频电极、焊盘等）
│   ├── Boomerang.py         # 回旋镖谐振器
│   ├── MultiRing.py         # 多环串联结构
│   ├── MultiRaceTrack.py    # 多跑道环结构
│   ├── Isolator.py          # 隔离器
│   ├── memyshev.py          # Memyshev激光器
│   ├── ExtCav.py            # 外腔激光器
│   ├── WangCavity.py        # 王字形微腔（原始版）
│   ├── WangCavity_v2.py     # 王字形微腔（layout_engine重构版）
│   ├── TCRing.py            # 环形谐振器测试结构
│   ├── TCRaceTrack.py       # 跑道环测试结构
│   ├── TCCoupledCavity.py   # 耦合腔测试结构
│   └── SnapMerge.py         # DRC预处理（多边形合并/对齐）
└── layout_engine/           # 通用版图绘制引擎
    ├── errors.py            # 异常体系
    ├── coordinate.py        # 坐标计算引擎
    ├── layer_manager.py     # 图层管理器
    ├── path_utils.py        # 路径构建工具
    ├── port_utils.py        # 端口管理工具
    ├── interface.py         # 标准化绘制流程接口
    ├── validation.py        # 验证框架
    ├── renderer.py          # 渲染管线
    ├── config/              # 配置化参数管理
    │   └── config_manager.py
    └── elements/            # 可复用版图元素库
        ├── waveguides.py    # 波导元素
        ├── couplers.py      # 耦合器元素
        └── heaters.py       # 加热器集成元素
```

---

## API 参考

### 工具函数

包级别提供的工具函数，无需导入子模块即可使用。

#### `ap.list_components()`

列出所有可用的版图组件函数名。

```python
import AIPLPhMTools as ap
components = ap.list_components()
print(len(components))  # 135+
print(components[:5])   # ['Boomerang', 'CoupleDouRaceTrack', ...]
```

**返回值**: `list[str]` — 按字母排序的组件函数名列表。

---

#### `ap.import_module(name)`

显式导入并缓存一个子模块。适用于需要直接访问模块内部函数（而非通过包级别导出）的场景。

```python
import AIPLPhMTools as ap

ring_mod = ap.import_module('Ring')
c = ring_mod.RingPulley(r_ring=50)

le = ap.import_module('layout_engine')
print(le.list_presets())
```

**参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 模块名，如 `'Ring'`、`'RaceTrack'`、`'BasicDefine'`、`'layout_engine'` 等 |

**返回值**: 导入的模块对象。

---

#### `ap.generate_all_gds(output_dir, with_plot)`

批量生成所有版图组件的 GDS 文件和预览图。

```python
import AIPLPhMTools as ap

summary = ap.generate_all_gds(
    output_dir="./my_gds_output",
    with_plot=True,
)
print(f"成功: {summary['success']}, 跳过: {summary['skipped']}, 错误: {summary['error']}")
```

**参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output_dir` | `str` | `"./gds_output"` | GDS 文件和预览图的输出目录 |
| `with_plot` | `bool` | `True` | 是否同时生成预览图（PNG） |

**返回值**: `dict` — 包含 `total`、`success`、`skipped`、`error`、`elapsed_seconds` 等统计信息。

> **注意**: 此操作会导入所有模块，首次运行可能需要约 20 分钟。

---

### 基础定义 (BasicDefine)

定义在 `BasicDefine` 模块中，提供最基础的波导结构、图层定义和截面定义。该模块在首次导入时自动初始化 PDK。

#### 图层定义

| 名称 | 说明 |
|------|------|
| `LAYER` | 图层映射类，定义所有工艺层（WG、M1、HEATER、VIA 等） |
| `LayerMapUserDef` | 用户自定义图层映射 |

```python
from AIPLPhMTools import LAYER

wg_layer = LAYER.WG       # 波导层
m1_layer = LAYER.M1       # 金属1层
heater_layer = LAYER.HEATER  # 加热器层
via_layer = LAYER.VIA     # 过孔层
```

#### 截面定义

| 名称 | 说明 |
|------|------|
| `S_in_te0` | 输入截面 (width=0.5, layer=WG) |
| `S_in_te1` | 输入截面 TE1 |
| `S_out_te0` | 输出截面 (width=1.0, layer=WG) |
| `S_out_te1` | 输出截面 TE1 |
| `X_in0` | 输入 CrossSection |
| `X_in1` | 输入 CrossSection TE1 |
| `X_out0` | 输出 CrossSection |
| `X_out1` | 输出 CrossSection TE1 |

#### 基础波导组件

##### `GfCStraight(length, width, layer)`

创建直波导。

```python
wg = ap.GfCStraight(length=100, width=1.0, layer=(1, 0))
wg.show()
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `length` | `float` | — | 波导长度 (um) |
| `width` | `float` | — | 波导宽度 (um) |
| `layer` | `LayerSpec` | — | 图层 |

**端口**: `o1`（输入）、`o2`（输出）

---

##### `GfCBendEuler(radius, angle, width, p)`

创建欧拉弯曲波导。

```python
bend = ap.GfCBendEuler(radius=50, angle=90, width=1.0, p=0.5)
bend.show()
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `radius` | `float` | — | 弯曲半径 (um) |
| `angle` | `float` | `90` | 弯曲角度 (度) |
| `width` | `float` | — | 波导宽度 (um) |
| `p` | `float` | `0.5` | 欧拉曲线比例 (0~1) |

**端口**: `o1`（输入）、`o2`（输出）

---

##### `OffsetRamp(length, width1, width2, layer)`

锥形渐变波导，用于连接不同宽度的波导。

```python
taper = ap.OffsetRamp(length=50, width1=0.5, width2=1.0, layer=(1, 0))
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `length` | `float` | 锥形段长度 (um) |
| `width1` | `float` | 起始宽度 (um) |
| `width2` | `float` | 终止宽度 (um) |
| `layer` | `LayerSpec` | 图层 |

---

##### `Crossing_taper(width, crossing_width, layer)`

带锥形过渡的波导交叉结构。

```python
cross = ap.Crossing_taper(width=0.8, crossing_width=1.2, layer=(1, 0))
```

---

##### `TaperRsoa(width1, width2, length, layer)`

RSOA 特殊锥形波导。

---

##### `cir2end(W1, W0p5, L100, P1)`

特殊曲线路径生成函数。

---

##### `euler_Bend_Half(radius, angle, p)`

创建欧拉半弯曲路径（Path 对象，非 Component）。

---

##### `euler_Bend_Part(radius, angle, p)`

创建欧拉部分弯曲路径。

---

##### `remove_layer(component, layer)`

从组件中移除指定图层的所有几何图形。

---

##### `GetFromLayer(component, layer)`

从组件中提取指定图层的几何图形。

---

##### `add_labels_to_ports(component, layer)`

为组件的所有端口添加标签。

---

##### `shift_component(component, dx, dy)`

平移组件。

---

##### `TWQRcode(text, size, layer)`

生成二维码标记。

```python
qr = ap.TWQRcode(text="AIPL-001", size=100, layer=(10, 0))
```

---

##### `make_cs(width, layer)`

快速创建 CrossSection 的便捷函数。

---

##### `route_off_grid(component, port1, port2, cross_section)`

离网格布线函数。

---

##### `route_bundle_off_grid(component, ports1, ports2, cross_section)`

离网格批量布线函数。

---

### 环形谐振器 (Ring)

定义在 `Ring` 模块中。所有环形谐振器均使用 Pulley 耦合结构。

#### `RingPulley(r_ring, width_ring, gap, width_near, oplayer, heater_config)`

基础环形谐振器（Pulley 耦合，Add-Drop 结构）。

```python
ring = ap.RingPulley(r_ring=50, width_ring=0.8, gap=0.2)
ring.show()
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `r_ring` | `float` | — | 环半径 (um) |
| `width_ring` | `float` | — | 环波导宽度 (um) |
| `gap` | `float` | — | 耦合间隙 (um) |
| `width_near` | `float` | — | 总线波导宽度 (um) |
| `oplayer` | `LayerSpec` | `(1, 0)` | 光学层 |
| `heater_config` | — | `None` | 加热器配置 |

**端口**: `Input`、`Through`、`Add`、`Drop`（如有加热器则额外包含 `HeatIn`、`HeatOut`）

---

#### `RingPulleyT1(r_ring, width_ring, gap, is_ad, oplayer, heater_config)`

环形谐振器变体 1，支持对称/非对称端口配置。

```python
ring = ap.RingPulleyT1(r_ring=50, width_ring=0.8, is_ad=True)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `is_ad` | `bool` | 是否启用 Add-Drop 端口 |

---

#### `RingPulleyT2(r_ring, width_ring, gap, oplayer, heater_config)`

环形谐振器变体 2，90 度 IO 引出。

---

#### `RingPulley1DC(r_ring, width_ring, gap, oplayer, heater_config)`

单侧耦合环形谐振器（仅 Input/Through，无 Add/Drop）。

---

#### `RingPulley2(r_ring, width_ring, gap, oplayer, heater_config)`

双 Pulley 耦合环。

---

#### `RingPulley2ES(r_ring, width_ring, gap, oplayer, heater_config)`

双 Pulley 耦合环（增强版）。

---

#### `RingPulley3(r_ring, width_ring, gap, oplayer, heater_config)`

三 Pulley 耦合环。

---

#### `RingPulley4(r_ring, width_ring, gap, oplayer, heater_config)`

四 Pulley 耦合环。

---

#### `RingFinger(r_ring, width_ring, gap, oplayer, heater_config)`

山形环（特殊色散特性），环路径呈指形起伏。

---

#### `RingBoomerang(r_ring, width_ring, gap, oplayer, heater_config)`

集成回旋镖单元的环形谐振器。

---

#### `RingDouBoomerang(r_ring, width_ring, gap, oplayer, heater_config)`

双回旋镖环形谐振器。

---

#### `RingTriBoomerang(r_ring, width_ring, gap, oplayer, heater_config)`

三回旋镖环形谐振器。

---

### 跑道型谐振器 (RaceTrack)

定义在 `RaceTrack` 模块中。跑道型谐振器在环的两侧有平行直线段，支持 Pulley 耦合和直线耦合两种方式。

#### `RaceTrackP(r_ring, length, width_ring, gap, width_near, oplayer, heater_config)`

Pulley 耦合跑道环。

```python
rt = ap.RaceTrackP(r_ring=50, length=30, width_ring=0.8, gap=0.2)
rt.write_gds("racetrack.gds")
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `r_ring` | `float` | 弯曲半径 (um) |
| `length` | `float` | 直线段长度 (um) |
| `width_ring` | `float` | 环波导宽度 (um) |
| `gap` | `float` | 耦合间隙 (um) |
| `width_near` | `float` | 总线波导宽度 (um) |

**端口**: `Input`、`Through`、`Add`、`Drop`

---

#### `RaceTrackS(r_ring, length, width_ring, gap, width_near, oplayer, heater_config)`

直线耦合跑道环（支持 GSG 电极）。

```python
rt = ap.RaceTrackS(r_ring=50, length=30, width_ring=0.8, gap=0.2)
```

与 `RaceTrackP` 的区别在于耦合区域使用平行直波导而非 Pulley 弯曲耦合。

---

#### `TaperRaceTrackPulley(r_ring, length, width_ring, gap, oplayer, heater_config)`

锥形直线段跑道环，直线段宽度渐变。

---

#### `RaceTrackStrHC(r_ring, length, width_ring, gap, oplayer, heater_config)`

中心对称加热器跑道环。

---

### 耦合器与 MZI (CouplerMZI)

定义在 `CouplerMZI` 模块中。

#### `PulleyCoupler2X2(gap, length, radius, width, oplayer)`

2x2 Pulley 型定向耦合器。

```python
coupler = ap.PulleyCoupler2X2(gap=0.2, length=50, radius=30, width=0.8)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `gap` | `float` | 耦合间隙 (um) |
| `length` | `float` | 耦合段长度 (um) |
| `radius` | `float` | 弯曲半径 (um) |
| `width` | `float` | 波导宽度 (um) |

**端口**: `o1`、`o2`、`o3`、`o4`

---

#### `DMZI(delta_length, width, oplayer)`

直波导耦合 MZI（Mach-Zehnder 干涉仪）。

```python
mzi = ap.DMZI(delta_length=100, width=0.8)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `delta_length` | `float` | 两臂长度差 (um) |
| `width` | `float` | 波导宽度 (um) |

**端口**: `o1`（输入）、`o2`（输出）

---

#### `PMZI(delta_length, width, oplayer)`

Pulley 耦合 MZI（紧凑布局）。

```python
mzi = ap.PMZI(delta_length=200, width=0.8)
```

---

#### `PMZIHSn(delta_length, width, oplayer)`

蛇形加热器 MZI，在 MZI 一臂上集成蛇形加热器用于相位调谐。

---

#### `SagnacRing(r_ring, width, oplayer)`

Sagnac 环（宽带反射镜）。

```python
sagnac = ap.SagnacRing(r_ring=50, width=0.8)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `r_ring` | `float` | 环半径 (um) |
| `width` | `float` | 波导宽度 (um) |

---

### DBR 反射器 (DBR)

定义在 `DBR` 模块中。分布式布拉格反射器，用于波长选择和反馈。

#### `DBR(length, period, width, duty_cycle, layer)`

参数化分布式布拉格反射器。

```python
dbr = ap.DBR(length=300, period=0.32, width=0.5, duty_cycle=0.5)
dbr.show()
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `length` | `float` | — | DBR 总长度 (um) |
| `period` | `float` | — | 光栅周期 (um) |
| `width` | `float` | — | 波导宽度 (um) |
| `duty_cycle` | `float` | `0.5` | 占空比 (0~1) |
| `layer` | `LayerSpec` | `(1, 0)` | 图层 |

**端口**: `o1`（输入）、`o2`（输出/透射）

---

#### `DBRFromCsv(csv_path, layer)`

从 CSV 文件导入光栅参数生成 DBR。CSV 文件应包含光栅齿的位置和宽度信息。

---

#### `DBRFromCsvOffset(csv_path, layer)`

从 CSV 导入（带偏移），支持非对称光栅结构。

---

#### `SGDBRFromCsvOffset(csv_path, layer)`

采样光栅 DBR（Sampled Grating DBR），从 CSV 导入，用于宽调谐范围激光器。

---

#### `EDBRStrRep()`

DBR 字符串表示（用于调试和日志）。

---

#### `EDBRFromCsv(csv_path, layer)`

从 CSV 导入 DBR（扩展版），支持更多光栅参数。

---

### 加热器 (Heater)

定义在 `Heater` 模块中。提供热光相位调谐所需的加热器结构。

#### `DifferentHeater(PathHeat, WidthWG, HeaterConfig)`

通用加热器工厂函数，根据配置生成不同类型的加热器。

```python
from AIPLPhMTools import DifferentHeater, heaterconfig0

heater = DifferentHeater(
    PathHeat=my_ring_path,
    WidthWG=0.8,
    HeaterConfig=heaterconfig0,
)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `PathHeat` | `gf.Path` | 加热器跟随的波导路径 |
| `WidthWG` | `float` | 波导宽度 (um) |
| `HeaterConfig` | `HeaterConfigClass` | 加热器配置对象 |

**端口**: `HeatIn`、`HeatOut`

---

#### `SnakeHeater(width, length, turns, layer)`

蛇形加热器，用于长距离相位调谐。

```python
heater = ap.SnakeHeater(width=2, length=200, turns=5, layer=(10, 0))
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `width` | `float` | 加热条宽度 (um) |
| `length` | `float` | 加热器总长度 (um) |
| `turns` | `int` | 蛇形折返次数 |
| `layer` | `LayerSpec` | 加热器图层 |

---

#### `ViaArray(rows, cols, spacing, layer)`

过孔阵列。

```python
vias = ap.ViaArray(rows=3, cols=5, spacing=2, layer=(70, 0))
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `rows` | `int` | 行数 |
| `cols` | `int` | 列数 |
| `spacing` | `float` | 过孔间距 (um) |
| `layer` | `LayerSpec` | 过孔图层 |

---

#### `ViaArrayParallel(rows, cols, spacing, layer)`

并行过孔阵列（两组对称排列）。

---

### 电极 (ELE)

定义在 `ELE` 模块中。提供高频电极和焊盘结构。

#### `OpenPad(width, length, layer)`

开放金属焊盘。

```python
pad = ap.OpenPad(width=70, length=70, layer=(10, 0))
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `width` | `float` | 焊盘宽度 (um) |
| `length` | `float` | 焊盘长度 (um) |
| `layer` | `LayerSpec` | 金属图层 |

---

#### `GSGELE(pitch, width, length, layer)`

GSG（Ground-Signal-Ground）高频电极结构。

```python
ele = ap.GSGELE(pitch=150, width=60, length=80, layer=(10, 0))
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `pitch` | `float` | G-S-G 间距 (um) |
| `width` | `float` | 电极宽度 (um) |
| `length` | `float` | 电极长度 (um) |
| `layer` | `LayerSpec` | 金属图层 |

**端口**: `S`（信号）、`G1`（地1）、`G2`（地2）

---

### 回旋镖谐振器 (Boomerang)

定义在 `Boomerang` 模块中。

#### `Boomerang(r_ring, width_ring, gap, oplayer, heater_config)`

回旋镖形谐振器，在环形路径中嵌入回旋镖状结构以增强光-物质相互作用。

```python
b = ap.Boomerang(r_ring=50, width_ring=0.8, gap=0.2)
```

---

### 多环结构 (MultiRing / MultiRaceTrack)

定义在 `MultiRing` 和 `MultiRaceTrack` 模块中。多环串联结构利用 Vernier 效应扩展自由光谱范围（FSR）。

#### `DoubleRingPulley(r_ring, width_ring, gap, oplayer, heater_config)`

双环串联（Vernier 效应）。

```python
dr = ap.DoubleRingPulley(r_ring=50, width_ring=0.8, gap=0.2)
```

**端口**: `Input`、`Through`、`Add`、`Drop`

---

#### `DoubleRingPulley2HSn(r_ring, width_ring, gap, oplayer, heater_config)`

双环串联 + 双蛇形加热器（每个环独立调谐）。

---

#### `DoubleRingPulley2_1HSn(r_ring, width_ring, gap, oplayer, heater_config)`

双环串联 + 单蛇形加热器。

---

#### `CoupleRingDRT1(r_ring, width_ring, gap, oplayer, heater_config)`

侧边耦合多谐振器（CROW 单元），环与环之间通过侧边耦合连接。

---

#### `CoupleDouRaceTrack(r_ring, length, width_ring, gap, oplayer, heater_config)`

双跑道环耦合结构。

---

#### `DoubleRaceTrack(r_ring, length, width_ring, gap, oplayer, heater_config)`

双跑道环结构。

---

### 隔离器 (Isolator)

定义在 `Isolator` 模块中。

#### `SingleRingIsolator0(r_ring, width_ring, gap, oplayer)`

单环隔离器变体 0。

---

#### `SingleRingIsolator1(r_ring, width_ring, gap, oplayer)`

单环隔离器变体 1。

---

#### `RingAndIsolator0(r_ring, width_ring, gap, oplayer)`

环与隔离器集成结构。

---

### Memyshev 激光器 (memyshev)

定义在 `memyshev` 模块中。

#### `DoubleRingMemyshev(r_ring, width_ring, gap, oplayer, heater_config)`

双环 Memyshev 激光器结构，利用双环 Vernier 效应实现单模激射。

---

### 外腔激光器 (ExtCav)

定义在 `ExtCav` 模块中。外腔激光器将增益芯片与外部谐振腔（环/跑道环）结合。

#### `ExternalCavitySOI(r_ring, width_ring, gap, oplayer, heater_config)`

SOI 平台外腔结构。

```python
ec = ap.ExternalCavitySOI(r_ring=50, width_ring=0.8, gap=0.2)
```

---

#### `ExternalCavitySiN(r_ring, width_ring, gap, oplayer, heater_config)`

SiN 平台外腔结构。

---

#### `ExternalCavityRaceTrack(r_ring, length, width_ring, gap, oplayer, heater_config)`

基于跑道环的外腔。

---

#### `ExtCavDouRing(r_ring, width_ring, gap, oplayer, heater_config)`

双环外腔。

---

#### `ExtCavDouRing2(r_ring, width_ring, gap, oplayer, heater_config)`

双环外腔变体 2。

---

#### `ExtCavTriRing(r_ring, width_ring, gap, oplayer, heater_config)`

三环外腔。

---

#### `ExtCavTriRing2(r_ring, width_ring, gap, oplayer, heater_config)`

三环外腔变体 2。

---

#### `ExtCavTriRing2_2(r_ring, width_ring, gap, oplayer, heater_config)`

三环外腔变体 2_2。

---

#### `ExtCavDouRaceTrack(r_ring, length, width_ring, gap, oplayer, heater_config)`

双跑道环外腔。

---

### 王字形微腔 (WangCavity)

定义在 `WangCavity` 和 `WangCavity_v2` 模块中。王字形微腔是一种类似汉字"王"的闭合曲线谐振腔，由一条连续波导沿"王"字外轮廓走线构成。

#### `WangCavity(width_ring, width_near, radius_bend, length_horiz, length_vert, gap_ring, oplayer, heater_config)`

原始版王字形微腔。

```python
wang = ap.WangCavity(
    width_ring=1.0,
    width_near=0.9,
    radius_bend=30.0,
    length_horiz=300.0,
    length_vert=350.0,
    gap_ring=0.2,
)
wang.show()
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `width_ring` | `float` | `1.0` | 主体波导宽度 (um) |
| `width_near` | `float` | `0.9` | 外部耦合总线波导宽度 (um) |
| `radius_bend` | `float` | `30.0` | 拐角弯曲半径 (um) |
| `length_horiz` | `float` | `300.0` | 水平总宽度 (um) |
| `length_vert` | `float` | `350.0` | 垂直总高度 (um) |
| `gap_ring` | `float` | `0.2` | 环与外部耦合总线之间的间隙 (um) |
| `oplayer` | `LayerSpec` | `(1, 0)` | 光学波导层 |
| `heater_config` | — | `None` | 加热器配置 |

**端口**: `Input`、`Through`、`Add`、`Drop`、`TopCenter`、`BottomCenter`（如有加热器则额外包含 `HeatIn`、`HeatOut`）

**结构示意**:
```
    Input ──────── Through     ← 上侧水平耦合总线
    ┌──────────────────────┐   ← 上横
    │   ┌──────────────┐   │   ← 中横
    │   │   ┌──────┐   │   │   ← 下横
    │   │   └──────┘   │   │
    │   └──────────────┘   │
    └──────────────────────┘
    Add ────────── Drop         ← 下侧水平耦合总线
```

---

#### `WangCavityV2(width_ring, width_near, radius_bend, length_horiz, length_vert, gap_ring, oplayer, heater_config)`

使用 `layout_engine` 重构的王字形微腔。参数和端口与 `WangCavity` 完全一致，但内部实现使用了通用版图绘制引擎的标准组件：

- 使用 `WaveguideTemplate` 消除 Section/CrossSection 样板代码
- 使用 `ComponentBuilder` 实现流式组件构建
- 使用 `check_positive` 进行参数验证
- 使用 `compute_coupling_offset` 自动计算耦合偏移
- 使用 `straight_coupling_path` 生成耦合总线路径
- 使用 `validate_component` 进行构建后验证

```python
from AIPLPhMTools.FabBasic_hjh.WangCavity_v2 import WangCavityV2

wang = WangCavityV2(length_horiz=300, length_vert=350)
wang.show()
```

---

### 测试结构 (TC 系列)

测试结构（Test Cell）是完整的测试单元，包含 IO 引出和端口路由，可直接用于流片。

#### TCRing 模块

环形谐振器测试结构。

| 函数 | 说明 |
|------|------|
| `TCRing` | 通用环形谐振器测试结构 |
| `TCRingT1` | 不同耦合方式的环测试结构 |
| `TCRingT2` | 90 度 IO 引出环测试结构 |
| `TCRing1AD` | Add-Drop 滤波器测试结构 |
| `TCRing1DC` | 单侧耦合环测试结构 |
| `TCRing1_3` | 环测试结构变体 1_3 |
| `TCRing2` | 双环测试结构 |
| `TCRing2_2` | 双环测试结构变体 2_2 |
| `TCRing2_3` | 双环测试结构变体 2_3 |
| `TCRing3` | 三环测试结构 |
| `TCRing4` | 四环测试结构 |
| `TCFingerRing1` | 山形环测试结构 |
| `TCRingDCouple` | 自耦合环（Fano 谐振）测试结构 |
| `TCRingBoomerangT1` | 回旋镖环测试结构 |

```python
tc = ap.TCRing1AD(r_ring=50, width_ring=0.8)
tc.show()
```

---

#### TCRaceTrack 模块

跑道环测试结构。

| 函数 | 说明 |
|------|------|
| `TCRaceTrackP` | Pulley 耦合跑道环测试结构 |
| `TCRaceTrackS` | 直线耦合跑道环测试结构 |
| `TCRaceTrackS2` | 直线耦合跑道环变体 2 |
| `TCRaceTrackS3` | 直线耦合跑道环变体 3 |
| `TCRaceTrackS3h` | 直线耦合跑道环变体 3（带加热器） |
| `TCTaperRaceTrackP` | 锥形 Pulley 耦合跑道环测试结构 |
| `TCTaperRaceTrackS` | 锥形直线耦合跑道环测试结构 |

---

#### TCCoupledCavity 模块

耦合腔测试结构。

| 函数 | 说明 |
|------|------|
| `TCRingBoomerangT1` | 回旋镖谐振器测试结构 |
| `TCRingDouBoomerangT1` | 双回旋镖谐振器测试结构 |
| `TCRingTriBoomerangT1` | 三回旋镖谐振器测试结构 |
| `TCCoupleDouRingT1` | 双环耦合测试结构 |
| `TCCoupleDouRaceTrackT1` | 双跑道环耦合测试结构 |
| `TCCoupleDouRaceTrackT2` | 双跑道环耦合测试结构变体 2 |

---

### DRC 预处理 (SnapMerge)

定义在 `SnapMerge` 模块中。提供 GDS 导出前的 DRC 预处理功能。

#### `snap_all_polygons_iteratively(component, grid_size)`

迭代式多边形网格对齐。将所有多边形的顶点对齐到指定网格，消除亚网格精度导致的 DRC 违例。

```python
from AIPLPhMTools import snap_all_polygons_iteratively

snap_all_polygons_iteratively(my_component, grid_size=0.001)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `component` | `Component` | 待处理的组件 |
| `grid_size` | `float` | 网格大小 (um) |

---

#### `merge_polygons_in_each_layer(component)`

逐层合并重叠/相邻多边形。

---

#### `merge_polygons_in_layer(component, layer)`

合并指定图层的多边形。

---

### 通用版图绘制引擎 (layout_engine)

`layout_engine` 是本工具包的核心基础设施，提供版图绘制中通用的坐标计算、图层管理、路径构建、端口管理、配置化参数、可复用元素库、标准化接口和验证框架。

所有 `layout_engine` 的组件均可通过 `ap.xxx` 直接访问，也可通过 `ap.layout_engine.xxx` 访问。

---

#### 异常体系 (errors)

提供版图绘制过程中可能出现的各类异常，支持精确的错误定位和上下文信息。

##### 异常类

| 异常类 | 父类 | 说明 |
|--------|------|------|
| `LayoutEngineError` | `Exception` | 版图引擎基础异常 |
| `GeometryError` | `LayoutEngineError` | 几何约束违反（路径段长度不足、半径过大等） |
| `PortError` | `LayoutEngineError` | 端口操作异常（端口不存在、类型不匹配等） |
| `LayerError` | `LayoutEngineError` | 图层操作异常（图层未注册、冲突等） |
| `ConfigurationError` | `LayoutEngineError` | 配置异常（配置文件缺失、参数无效等） |
| `ConnectivityError` | `LayoutEngineError` | 连通性异常（波导连接存在间隙或错位） |

##### 检查函数

###### `check_positive(value, name, component)`

检查参数是否为正数。

```python
from AIPLPhMTools import check_positive

check_positive(radius, "radius")  # radius <= 0 时抛出 GeometryError
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `value` | `float` | 待检查的值 |
| `name` | `str` | 参数名称（用于错误消息） |
| `component` | `str` | 组件名称（可选，用于错误上下文） |

---

###### `check_geometry_constraint(available, required, name, component)`

检查几何约束：可用空间是否满足最小需求。

```python
from AIPLPhMTools import check_geometry_constraint

check_geometry_constraint(straight_len, 0, "bar_straight")
```

---

###### `check_port_exists(component, port_name)`

检查端口是否存在。

```python
from AIPLPhMTools import check_port_exists

check_port_exists(my_component, "o1")
```

---

#### 坐标计算引擎 (coordinate)

提供版图绘制中通用的坐标计算、网格布局、对齐和间距管理功能。

##### 枚举类型

###### `Alignment`

对齐方式枚举。

| 值 | 说明 |
|----|------|
| `Alignment.MIN` | 左对齐/下对齐 |
| `Alignment.CENTER` | 居中对齐 |
| `Alignment.MAX` | 右对齐/上对齐 |

###### `Direction`

布局方向枚举。

| 值 | 说明 |
|----|------|
| `Direction.HORIZONTAL` | 水平排列 |
| `Direction.VERTICAL` | 垂直排列 |

---

##### `Spacing(x, y)`

间距定义数据类。

```python
from AIPLPhMTools import Spacing

s = Spacing(x=100, y=200)
s_uniform = Spacing.uniform(150)  # x=y=150
```

| 属性/方法 | 类型 | 说明 |
|-----------|------|------|
| `x` | `float` | 水平间距 (um)，默认 100 |
| `y` | `float` | 垂直间距 (um)，默认 200 |
| `uniform(value)` | `classmethod` | 创建均匀间距 |

---

##### `GridLayout(spacing, direction, columns, alignment)`

网格布局计算器。根据组件尺寸列表自动计算每个组件的放置位置。

```python
from AIPLPhMTools import GridLayout, Spacing, Direction, Alignment

grid = GridLayout(
    spacing=Spacing(100, 200),
    direction=Direction.HORIZONTAL,
    columns=3,
    alignment=Alignment.CENTER,
)

sizes = [(300, 200), (250, 180), (350, 220), (280, 190)]
positions = grid.compute_positions(sizes)
# [(0, 0), (450, 0), (900, 0), (0, 420)]

total_w, total_h = grid.total_size(sizes)
```

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `spacing` | `Spacing` | `Spacing()` | 组件间距 |
| `direction` | `Direction` | `HORIZONTAL` | 排列方向 |
| `columns` | `int` | `0` | 列数（0 表示自动） |
| `alignment` | `Alignment` | `CENTER` | 行内对齐方式 |

| 方法 | 说明 |
|------|------|
| `compute_positions(sizes)` | 计算每个组件的位置，返回 `[(x, y), ...]` |
| `total_size(sizes)` | 计算网格总尺寸，返回 `(width, height)` |

---

##### 坐标计算函数

###### `compute_coupling_offset(width_ring, width_bus, gap)`

计算耦合总线相对于环中心线的偏移量。

```python
from AIPLPhMTools import compute_coupling_offset

offset = compute_coupling_offset(
    width_ring=1.0,   # 环波导宽度
    width_bus=0.9,    # 总线波导宽度
    gap=0.2,          # 耦合间隙
)
# offset = 1.0/2 + 0.2 + 0.9/2 = 1.15
```

---

###### `compute_straight_length_for_connection(port_a_center, port_b_center, axis)`

计算连接两个端口所需的直波导长度。

```python
from AIPLPhMTools import compute_straight_length_for_connection

length = compute_straight_length_for_connection(
    (0, 0), (100, 0), axis="x"
)
# length = 100
```

---

###### `compute_taper_length(width1, width2, min_length, slope)`

根据宽度差自动计算锥形波导的合理长度。

```python
from AIPLPhMTools import compute_taper_length

length = compute_taper_length(0.5, 1.0, min_length=1.0, slope=500)
# length = max(1.0, 500 * 0.5) = 250
```

---

###### `align_components_vertical(refs, alignment)`

垂直对齐一组组件引用。

```python
from AIPLPhMTools import align_components_vertical, Alignment

align_components_vertical([ref1, ref2, ref3], Alignment.CENTER)
```

---

###### `align_components_horizontal(refs, alignment)`

水平对齐一组组件引用。

---

#### 图层管理器 (layer_manager)

集中管理所有图层的 CrossSection 定义，提供工厂方法快速创建常用的波导截面。

##### `LayerManager()`

图层管理器类。

```python
from AIPLPhMTools import LayerManager

lm = LayerManager()

# 注册 CrossSection
lm.register("wg_1um", width=1.0, layer=(1, 0))
lm.register("wg_0p5", width=0.5, layer=(1, 0), radius=50)

# 注册多 Section CrossSection
lm.register_multi("wg_rib", sections=[
    {"width": 0.5, "layer": (1, 0)},
    {"width": 2.0, "layer": (2, 0), "offset": 0},
])

# 获取 CrossSection
cs = lm.get("wg_1um")

# 获取或自动创建
cs = lm.get_or_create("wg_temp", width=0.8, layer=(1, 0))

# 使用 CrossSection 创建波导
straight = lm.make_straight("wg_1um", length=100)
bend = lm.make_bend_euler("wg_1um", radius=50, angle=90)

# 列出所有已注册的 CrossSection
print(lm.list_registered())
```

| 方法 | 说明 |
|------|------|
| `register(name, width, layer, ...)` | 注册一个 CrossSection |
| `register_multi(name, sections, ...)` | 注册多 Section CrossSection |
| `get(name)` | 获取已注册的 CrossSection |
| `get_or_create(name, width, layer, ...)` | 获取或自动创建 |
| `make_straight(cs_name, length)` | 使用已注册 CrossSection 创建直波导 |
| `make_bend_euler(cs_name, radius, angle, p)` | 使用已注册 CrossSection 创建欧拉弯曲 |
| `list_registered()` | 列出所有已注册名称 |
| `clear()` | 清除所有注册 |

---

##### `quick_cs(width, layer, port_names, radius)`

快速创建单 Section CrossSection 的便捷函数。

```python
from AIPLPhMTools import quick_cs

cs = quick_cs(width=0.8, layer=(1, 0))
```

---

##### `quick_cs_multi(specs, radius)`

快速创建多 Section CrossSection。

```python
from AIPLPhMTools import quick_cs_multi

cs = quick_cs_multi([
    (0.5, (1, 0)),
    (2.0, (2, 0)),
])
```

---

#### 路径构建工具 (path_utils)

封装 gdsfactory Path 的复杂组合逻辑，提供常用的路径构建模式。

##### `euler_half_bend(radius, angle, p)`

创建欧拉半弯曲路径。欧拉半弯用于平滑过渡直线段和圆弧段，保证曲率连续。

```python
from AIPLPhMTools import euler_half_bend

path = euler_half_bend(radius=50, angle=30, p=0.5)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `radius` | `float` | — | 弯曲半径 (um) |
| `angle` | `float` | — | 弯曲角度 (度)，正值为逆时针 |
| `p` | `float` | `0.5` | 欧拉曲线比例 (0~1) |

---

##### `arc_path(radius, angle)`

创建圆弧路径。

```python
from AIPLPhMTools import arc_path

path = arc_path(radius=100, angle=90)
```

---

##### `straight_path(length)`

创建直线路径。

```python
from AIPLPhMTools import straight_path

path = straight_path(length=200)
```

---

##### `pulley_coupling_path(radius, angle, p)`

创建 Pulley 耦合路径。由一段圆弧 + 一段欧拉半弯组成，用于环形谐振器的弯曲耦合区域。

```python
from AIPLPhMTools import pulley_coupling_path

path = pulley_coupling_path(radius=100, angle=20, p=0.5)
```

路径结构: `arc(angle/2) + euler_half(-angle/2)`

---

##### `straight_coupling_path(length_couple, radius_bend, bend_angle, p)`

创建直线耦合路径。由一段直波导 + 两段欧拉半弯组成，用于跑道型谐振器的平行耦合区域。

```python
from AIPLPhMTools import straight_coupling_path

path = straight_coupling_path(
    length_couple=200,
    radius_bend=100,
    bend_angle=15,
    p=0.5,
)
```

路径结构: `euler_half(bend_angle) + straight(length_couple/2) + euler_half(-bend_angle)`

---

##### `racetrack_half_path(length_run, radius_ring, arc_angle, euler_angle, p)`

创建跑道环的半边路径。

```python
from AIPLPhMTools import racetrack_half_path

half = racetrack_half_path(
    length_run=100,
    radius_ring=50,
    arc_angle=60,
    euler_angle=30,
    p=0.5,
)
```

路径结构: `arc(arc_angle) + euler_half(euler_angle) + straight(length_run/2)`

---

##### `mirror_path(path, axis)`

创建路径的镜像副本。

```python
from AIPLPhMTools import mirror_path

mirrored = mirror_path(original_path, axis="y")
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `Path` | 源路径 |
| `axis` | `str` | 镜像轴 (`'x'` 或 `'y'`) |

---

##### `build_closed_ring_path(radius, width)`

构建简单闭合圆环路径。

```python
from AIPLPhMTools import build_closed_ring_path

ring_path = build_closed_ring_path(radius=100)
```

---

##### `build_racetrack_closed_path(length_run, radius_ring, arc_angle, euler_angle, p)`

构建闭合跑道环路径。由两个半跑道路径首尾相连组成。

```python
from AIPLPhMTools import build_racetrack_closed_path

rt_path = build_racetrack_closed_path(
    length_run=100, radius_ring=50,
)
```

---

##### `extrude_path(path, cross_section, component)`

将路径挤出为波导组件引用。

```python
from AIPLPhMTools import extrude_path, quick_cs

cs = quick_cs(0.8, (1, 0))
ref = extrude_path(my_path, cs, parent_component)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `path` | `Path` | 路径对象 |
| `cross_section` | `CrossSection` | CrossSection 定义 |
| `component` | `Component` | 目标组件（可选，用于 add_ref） |

---

#### 端口管理工具 (port_utils)

提供端口创建、命名、转发和验证的通用工具。

##### `add_optical_port(component, name, center, orientation, width, layer, port_type)`

向组件添加光学端口。

```python
from AIPLPhMTools import add_optical_port

add_optical_port(
    my_component, "o1",
    center=(0, 0),
    orientation=0,
    width=0.8,
    layer=(1, 0),
)
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `component` | `Component` | 目标组件 |
| `name` | `str` | 端口名称 |
| `center` | `(float, float)` | 端口中心坐标 |
| `orientation` | `float` | 端口方向 (度) |
| `width` | `float` | 端口宽度 (um) |
| `layer` | `LayerSpec` | 图层 |
| `port_type` | `str` | 端口类型 (`'optical'` 或 `'electrical'`) |

---

##### `add_electrical_port(component, name, center, width, layer)`

向组件添加电学端口。

---

##### `forward_ports(source_component, target_component, port_filter, prefix, suffix)`

将源组件的端口转发到目标组件。

```python
from AIPLPhMTools import forward_ports

forward_ports(heater, my_component, port_filter="Heat", prefix="ring1_")
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `source_component` | `Component` | 源组件 |
| `target_component` | `Component` | 目标组件 |
| `port_filter` | `str` | 端口名称过滤字符串 |
| `prefix` | `str` | 端口名称前缀 |
| `suffix` | `str` | 端口名称后缀 |

---

##### `forward_heater_ports(heater_component, target_component, prefix)`

转发加热器组件的所有 Heat 端口。

---

##### `get_port_center(component, port_name)`

获取端口中心坐标。

```python
from AIPLPhMTools import get_port_center

x, y = get_port_center(my_component, "o1")
```

---

##### `get_port_orientation(component, port_name)`

获取端口方向（度）。

---

##### `midpoint_port(component, port_a, port_b, name, width, layer, orientation)`

在两个端口的中点创建新端口。

```python
from AIPLPhMTools import midpoint_port

midpoint_port(my_component, "o1", "o2", "center_port")
```

---

##### `connect_with_straight(parent, port_a, port_b, cross_section, allow_width_mismatch)`

使用直波导连接两个端口，自动计算所需长度并放置。

```python
from AIPLPhMTools import connect_with_straight

ref = connect_with_straight(
    parent_component,
    port_a=comp1.ports["o2"],
    port_b=comp2.ports["o1"],
    cross_section=my_cs,
)
```

---

##### `validate_port_orientation(component, port_name, expected_orientation, tolerance)`

验证端口方向是否符合预期。

```python
from AIPLPhMTools import validate_port_orientation

validate_port_orientation(my_component, "o1", 0, tolerance=1.0)
```

---

#### 配置化参数管理 (config)

支持多工艺配置切换、参数验证和预设管理。

##### 配置数据类

###### `ProcessConfig`

工艺配置。

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `name` | `str` | `"default"` | 工艺名称 |
| `die_width` | `float` | `21000` | Die 宽度 (um) |
| `die_height` | `float` | `21000` | Die 高度 (um) |
| `mask_version` | `str` | `"v1"` | 掩模版本号 |
| `default_layer` | `tuple` | `(1, 0)` | 默认波导图层 |

###### `WaveguideConfig`

波导参数配置。

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `width_single` | `float` | `0.8` | 单模波导宽度 (um) |
| `width_ring` | `float` | `1.0` | 环波导宽度 (um) |
| `width_near` | `float` | `0.9` | 近耦合波导宽度 (um) |
| `width_edge` | `float` | `1.5` | 边缘耦合器宽度 (um) |
| `radius_min` | `float` | `300` | 最小弯曲半径 (um) |

###### `CouplingConfig`

耦合参数配置。

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `gap_rc` | `float` | `1.0` | 环-总线耦合间隙 (um) |
| `angle_couple` | `float` | `20` | 耦合角度 (度) |
| `r_euler_false` | `float` | `500` | 伪欧拉半径 (um) |
| `r_delta` | `float` | `2.0` | 半径微调量 (um) |

###### `HeaterConfigData`

加热器参数配置。

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `width_heat` | `float` | `2.0` | 加热条宽度 (um) |
| `width_route` | `float` | `20` | 布线宽度 (um) |
| `width_pad` | `float` | `70` | Pad 宽度 (um) |
| `delta_heat` | `float` | `5.0` | 加热器偏移 (um) |
| `gap_heat` | `float` | `3.1` | 加热器-波导间隙 (um) |
| `type_heater` | `str` | `"default"` | 加热器类型 |

###### `LayoutConfig`

版图总配置，聚合所有子配置。

```python
from AIPLPhMTools import LayoutConfig

config = LayoutConfig()
config.waveguide.width_ring = 1.2
config.coupling.gap_rc = 0.8

# 从字典创建
config = LayoutConfig.from_dict({
    "waveguide": {"width_ring": 1.0},
    "coupling": {"gap_rc": 0.5},
})

# 从 JSON 文件加载
config = LayoutConfig.from_json("./my_config.json")

# 保存到 JSON
config.to_json("./output_config.json")

# 深拷贝
config2 = config.copy()
```

---

##### 预设配置

工具包内置三套工艺预设：

| 预设名称       | 平台          | 典型波导宽度      | 最小弯曲半径 |
| ---------- | ----------- | ----------- | ------ |
| `700nmSiN` | 700nm 氮化硅   | 0.8~1.0 um  | 300 um |
| `SOI`      | 220nm 绝缘体上硅 | 0.45~0.5 um | 5 um   |
| `InP`      | 磷化铟         | 2.0 um      | 100 um |

```python
from AIPLPhMTools import get_preset_config, list_presets, PRESET_CONFIGS

# 列出所有预设
print(list_presets())  # ['700nmSiN', 'SOI', 'InP']

# 获取预设配置
config = get_preset_config("SOI")
print(config.waveguide.width_ring)  # 0.5
print(config.coupling.gap_rc)       # 0.2

# 直接访问预设字典
print(PRESET_CONFIGS["700nmSiN"]["waveguide"]["width_ring"])  # 1.0
```

---

##### `validate_config(config)`

验证配置的有效性，返回警告信息列表。

```python
from AIPLPhMTools import validate_config, get_preset_config

config = get_preset_config("700nmSiN")
warnings = validate_config(config)
if warnings:
    for w in warnings:
        print(f"Warning: {w}")
```

---

#### 可复用版图元素库 (elements)

提供预定义的版图元素模板，每个元素都是独立的、可组合的构建块。

##### 波导元素 (elements.waveguides)

###### `WaveguideTemplate(width, layer, radius, radius_min)`

通用波导模板，封装了 Section/CrossSection 创建和常用波导操作。

```python
from AIPLPhMTools import WaveguideTemplate

tmpl = WaveguideTemplate(width=1.0, layer=(1, 0), radius=50)

# 创建 CrossSection
cs = tmpl.make_cross_section()

# 创建直波导
wg = tmpl.make_straight(length=100)

# 创建欧拉弯曲
bend = tmpl.make_bend_euler(angle=90)

# 路径挤出
component = tmpl.extrude_path(my_path)
```

| 方法 | 说明 |
|------|------|
| `make_section(port_names)` | 创建 Section |
| `make_cross_section()` | 创建 CrossSection |
| `make_straight(length)` | 创建直波导 Component |
| `make_bend_euler(angle, p, radius)` | 创建欧拉弯曲 Component |
| `extrude_path(path)` | 路径挤出为 Component |

---

###### `TaperedWaveguide(width_start, width_end, length_taper, length_start, length_end, layer)`

锥形波导元素，由 直波导(start) → 锥形 → 直波导(end) 三段组成。

```python
from AIPLPhMTools import TaperedWaveguide

taper = TaperedWaveguide(
    width_start=0.35,
    width_end=0.8,
    length_taper=250,
    length_start=50,
    length_end=10,
)
component = taper.build()
```

---

###### `EdgeCouplerElement(width_start, width_end, length_taper, length_straight_start, length_straight_end, layer, reverse_ports)`

边缘耦合器元素，用于芯片边缘的光纤耦合。

```python
from AIPLPhMTools import EdgeCouplerElement

ec = EdgeCouplerElement(
    width_start=0.25,
    width_end=0.8,
    length_taper=200,
)
component = ec.build()
```

---

###### `DirectionalCouplerElement(width_wg, gap, length_couple, length_straight, layer)`

定向耦合器元素，由两段平行直波导组成。

```python
from AIPLPhMTools import DirectionalCouplerElement

dc = DirectionalCouplerElement(
    width_wg=0.8,
    gap=0.2,
    length_couple=100,
)
component = dc.build()
```

**端口**: `o1`、`o2`、`o3`、`o4`

---

###### `create_taper_component(width1, width2, length_left, length_taper, length_right, layer, name)`

创建带直波导段的锥形波导组件的便捷函数。

```python
from AIPLPhMTools import create_taper_component

c = create_taper_component(
    width1=0.5, width2=1.0,
    length_left=100, length_right=100,
)
```

---

###### `create_edge_coupler(width_start, width_end, length_taper, length_straight_start, length_straight_end, layer, reverse_ports)`

创建边缘耦合器的便捷函数。

---

##### 耦合器元素 (elements.couplers)

###### `PulleyCoupler(width_ring, width_bus, radius_ring, gap, angle_couple, p, layer)`

Pulley 型耦合器元素，用于环形谐振器的弯曲耦合区域。

```python
from AIPLPhMTools import PulleyCoupler

coupler = PulleyCoupler(
    width_ring=1.0,
    width_bus=0.9,
    radius_ring=100,
    gap=0.2,
    angle_couple=20,
)

# 在父组件中构建
result = coupler.build(parent_component, add_drop=True)
# result["ring_ref"], result["bus_ref"], result["ring_ref2"], result["bus_ref2"]
```

| 属性/方法 | 说明 |
|-----------|------|
| `bus_radius` | 总线路径的半径（自动计算） |
| `build_ring_path()` | 构建环侧的耦合路径 |
| `build_bus_path()` | 构建总线侧的耦合路径 |
| `build(parent, add_drop)` | 在父组件中构建完整耦合结构 |

---

###### `StraightCoupler(width_ring, width_bus, radius_bend, gap, length_couple, bend_angle, p, layer)`

直线型耦合器元素，用于跑道型谐振器的平行耦合区域。

```python
from AIPLPhMTools import StraightCoupler

coupler = StraightCoupler(
    width_ring=1.0,
    width_bus=0.9,
    radius_bend=100,
    gap=0.2,
    length_couple=200,
)

result = coupler.build(parent_component, add_drop=True)
```

---

###### `create_pulley_coupler(width_ring, width_bus, radius_ring, gap, angle_couple, p, layer)`

创建 Pulley 耦合器的便捷函数。

---

###### `create_straight_coupler(width_ring, width_bus, radius_bend, gap, length_couple, bend_angle, p, layer)`

创建直线耦合器的便捷函数。

---

##### 加热器集成元素 (elements.heaters)

###### `HeaterIntegration(width_heat, width_route, width_via, gap_heat, delta_heat, spacing, type_heater, layer_heat, layer_route, layer_via)`

加热器集成元素，将加热器与波导路径集成。

```python
from AIPLPhMTools import HeaterIntegration

hi = HeaterIntegration(
    width_heat=4.0,
    gap_heat=3.0,
    delta_heat=2.0,
)

# 转换为 HeaterConfigClass 兼容的字典
config_dict = hi.to_heater_config()
```

---

###### `HeaterPadGroup(pad_component, width_heat, width_route, width_pad, layer_heat)`

加热器 Pad 组元素，为一组加热器端口自动创建 taper 和 Pad 连接。

---

###### `integrate_heater_to_ring(parent, ring_ref, heater_config, path_heat, width_wg, direction, mirror_center)`

将加热器集成到环形谐振器的通用函数。

```python
from AIPLPhMTools import integrate_heater_to_ring

h_ref = integrate_heater_to_ring(
    parent=my_component,
    ring_ref=ring_ref,
    heater_config=heater_config,
    path_heat=ring_path,
    width_wg=0.8,
    direction="down",
)
```

---

###### `create_heater_pad_group(parent, pad_component, heat_ports, width_heat, width_route, width_pad, layer_heat, cross_section_route)`

创建加热器 Pad 组的便捷函数。

---

#### 标准化绘制流程接口 (interface)

提供版图组件的标准化基类、构建器模式和绘制流程规范。

##### `LayoutComponent`

版图组件标准化抽象基类。所有版图组件应继承此类，实现标准的构建流程。

```python
from AIPLPhMTools import LayoutComponent
from AIPLPhMTools import check_positive, add_optical_port
import gdsfactory as gf

class MyComponent(LayoutComponent):
    name = "MyComponent"
    width: float = 1.0
    length: float = 100.0

    def _validate_params(self):
        check_positive(self.width, "width")
        check_positive(self.length, "length")

    def _build_impl(self):
        self._component = gf.Component(self.name)
        self._wg = self._component << gf.c.straight(
            length=self.length,
            cross_section=gf.cross_section.strip(width=self.width),
        )

    def _define_ports(self):
        add_optical_port(self._component, "o1", (0, 0), 0, self.width, (1, 0))
        add_optical_port(self._component, "o2", (self.length, 0), 0, self.width, (1, 0))

comp = MyComponent(width=0.8, length=200)
c = comp.build()
c.show()
```

| 方法 | 说明 |
|------|------|
| `_validate_params()` | 参数验证（子类可重写） |
| `_build_impl()` | 核心构建逻辑（子类必须实现） |
| `_define_ports()` | 端口定义逻辑（子类必须实现） |
| `build()` | 标准构建流程（1.验证 → 2.构建 → 3.端口 → 4.后处理） |
| `_post_process()` | 构建后处理（子类可重写） |
| `write_gds(path)` | 导出 GDS 文件 |
| `plot()` | 绘制版图预览 |
| `show()` | 交互式显示版图 |

---

##### `ComponentBuilder(name, layer_manager)`

版图组件构建器，提供流式 API 用于逐步构建复杂版图组件。封装了 Section/CrossSection 创建、路径挤出、端口管理等样板代码。

```python
from AIPLPhMTools import ComponentBuilder

builder = ComponentBuilder("my_component")
builder.add_cross_section("wg", width=1.0, layer=(1, 0))
builder.add_path_extrusion("wg", my_path)
builder.add_port("o1", center=(0, 0), orientation=0, width=1.0)
component = builder.build()
component.write_gds("output.gds")
```

| 方法 | 说明 |
|------|------|
| `add_cross_section(name, width, layer)` | 注册一个 CrossSection |
| `get_cross_section(name)` | 获取已注册的 CrossSection |
| `add_straight(cs_name, length)` | 添加直波导 |
| `add_bend_euler(cs_name, radius, angle, p)` | 添加欧拉弯曲 |
| `add_path_extrusion(cs_name, path)` | 添加路径挤出 |
| `add_ref(component)` | 添加组件引用 |
| `add_port(name, center, orientation, width, layer, port_type)` | 添加端口定义（延迟应用） |
| `add_port_from_ref(name, ref, port_name)` | 从组件引用转发端口 |
| `build()` | 完成构建并返回 Component |
| `write_gds(path)` | 构建并导出 GDS |

**属性**: `component` — 直接访问内部的 gf.Component 对象。

---

##### `draw_component(func)`

装饰器：将普通函数包装为标准化绘制流程。自动添加参数验证、错误处理和日志记录。

```python
from AIPLPhMTools import draw_component

@draw_component
def my_ring(width: float = 1.0, radius: float = 100.0) -> Component:
    ...
```

---

#### 验证框架 (validation)

提供版图组件的系统性验证，包括端口连通性检查、图层完整性验证、几何边界检查和 DRC 预处理。

##### 枚举类型

###### `ValidationLevel`

验证级别枚举。

| 值 | 说明 |
|----|------|
| `ValidationLevel.INFO` | 信息级别 |
| `ValidationLevel.WARNING` | 警告级别 |
| `ValidationLevel.ERROR` | 错误级别 |
| `ValidationLevel.CRITICAL` | 严重错误级别 |

---

##### `ValidationResult`

验证结果汇总数据类。

```python
from AIPLPhMTools import validate_component

result = validate_component(my_component)
print(result.passed)        # True/False
print(result.error_count)   # 错误数量
print(result.warning_count) # 警告数量
print(result.summary())     # 完整摘要
```

| 属性 | 类型 | 说明 |
|------|------|------|
| `component_name` | `str` | 组件名称 |
| `issues` | `list[ValidationIssue]` | 问题列表 |
| `passed` | `bool` | 是否通过验证 |
| `error_count` | `int` | 错误数量 |
| `warning_count` | `int` | 警告数量 |

| 方法 | 说明 |
|------|------|
| `add_issue(level, message, category, **details)` | 添加验证问题 |
| `summary()` | 返回验证摘要字符串 |

---

##### `validate_component(component, check_ports, check_layers, check_bounds, check_connectivity)`

对组件执行全面验证。

```python
from AIPLPhMTools import validate_component

result = validate_component(
    my_component,
    check_ports=True,
    check_layers=True,
    check_bounds=True,
    check_connectivity=True,
)

if not result.passed:
    print(f"Validation failed: {result.summary()}")
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `component` | `Component` | — | 待验证的组件 |
| `check_ports` | `bool` | `True` | 是否检查端口 |
| `check_layers` | `bool` | `True` | 是否检查图层 |
| `check_bounds` | `bool` | `True` | 是否检查几何边界 |
| `check_connectivity` | `bool` | `True` | 是否检查连通性 |

**返回值**: `ValidationResult`

---

##### `check_port_connectivity(component, port_a, port_b, max_gap)`

检查两个端口是否连通（位置匹配）。

```python
from AIPLPhMTools import check_port_connectivity

check_port_connectivity(my_component, "o1", "o2", max_gap=0.01)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `component` | `Component` | — | 组件 |
| `port_a` | `str` | — | 端口 A 名称 |
| `port_b` | `str` | — | 端口 B 名称 |
| `max_gap` | `float` | `0.01` | 最大允许间隙 (um) |

**返回值**: `bool` — True 如果端口位置匹配。

---

##### `check_layer_integrity(component, expected_layers)`

检查组件是否包含所有预期的图层。

```python
from AIPLPhMTools import check_layer_integrity

check_layer_integrity(my_component, [(1, 0), (10, 0)])
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `component` | `Component` | 组件 |
| `expected_layers` | `list` | 预期图层列表 |

**返回值**: `bool` — True 如果所有预期图层都存在。

---

##### `check_geometry_bounds(component, max_width, max_height, min_width, min_height)`

检查组件几何尺寸是否在允许范围内。

```python
from AIPLPhMTools import check_geometry_bounds

check_geometry_bounds(
    my_component,
    max_width=21000,   # Die 宽度限制
    max_height=21000,  # Die 高度限制
    min_width=10,
    min_height=10,
)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `component` | `Component` | — | 组件 |
| `max_width` | `float` | `None` | 最大允许宽度 (um) |
| `max_height` | `float` | `None` | 最大允许高度 (um) |
| `min_width` | `float` | `0.0` | 最小允许宽度 (um) |
| `min_height` | `float` | `0.0` | 最小允许高度 (um) |

**返回值**: `bool` — True 如果尺寸在允许范围内。

---

#### 渲染管线 (renderer)

提供版图组件的批量渲染、GDS 导出和性能优化功能。

##### `LayoutRenderer(output_dir, add_labels, label_layer, validate_before_export, auto_create_dir)`

版图渲染器，提供统一的 GDS 导出接口。

```python
from AIPLPhMTools import LayoutRenderer

renderer = LayoutRenderer(
    output_dir="./gds_output",
    add_labels=True,
    validate_before_export=True,
)

filepath = renderer.render(ring_component, "ring.gds")
print(f"Exported to: {filepath}")

# 批量渲染
components = {
    "ring_r100.gds": ring_r100,
    "ring_r200.gds": ring_r200,
}
stats = renderer.render_all(components, prefix="batch_")
print(f"Success: {stats.success_count}, Failed: {stats.failure_count}")
```

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output_dir` | `str` | `"./gds_output"` | 输出目录 |
| `add_labels` | `bool` | `True` | 是否添加端口标签 |
| `label_layer` | `tuple` | `(512, 8)` | 标签图层 |
| `validate_before_export` | `bool` | `True` | 导出前是否验证 |
| `auto_create_dir` | `bool` | `True` | 是否自动创建输出目录 |

| 方法 | 说明 |
|------|------|
| `render(component, filename, **kwargs)` | 渲染单个组件并导出 GDS |
| `render_all(components, prefix)` | 批量渲染多个组件 |

---

##### `BatchRenderer(output_dir, jobs, renderer, validate)`

批量渲染器，支持从工厂函数批量生成和导出组件。

```python
from AIPLPhMTools import BatchRenderer

renderer = BatchRenderer(output_dir="./batch_output")
renderer.add_job("ring_r100", lambda: RingPulley(RadiusRing=100))
renderer.add_job("ring_r200", lambda: RingPulley(RadiusRing=200))

# 批量添加
renderer.add_jobs_from_dict({
    "ring_r300": lambda: RingPulley(RadiusRing=300),
    "ring_r400": lambda: RingPulley(RadiusRing=400),
})

stats = renderer.run()
print(f"Success: {stats.success_count}, Failed: {stats.failure_count}")
```

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `output_dir` | `str` | `"./batch_output"` | 输出目录 |
| `jobs` | `dict` | `{}` | 渲染任务字典 |
| `renderer` | `LayoutRenderer` | `None` | 底层渲染器 |
| `validate` | `bool` | `True` | 是否验证 |

| 方法 | 说明 |
|------|------|
| `add_job(name, factory)` | 添加渲染任务 |
| `add_jobs_from_dict(jobs)` | 批量添加渲染任务 |
| `run(parallel)` | 执行所有渲染任务 |

---

##### `render_to_gds(component, filepath, validate, add_labels)`

便捷函数：将组件渲染为 GDS 文件。

```python
from AIPLPhMTools import render_to_gds

render_to_gds(
    my_component,
    "./output/my_component.gds",
    validate=True,
    add_labels=True,
)
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `component` | `Component` | — | 组件 |
| `filepath` | `str` | — | 输出路径 |
| `validate` | `bool` | `True` | 是否验证 |
| `add_labels` | `bool` | `True` | 是否添加端口标签 |

**返回值**: `str` — 输出文件路径。

---

## 批量生成 GDS

### 使用 `generate_all_gds` 批量生成

```python
import AIPLPhMTools as ap

summary = ap.generate_all_gds(
    output_dir="./my_gds_output",
    with_plot=True,
)
print(f"成功: {summary['success']}, 跳过: {summary['skipped']}, 错误: {summary['error']}")
```

> **注意**: 此操作会导入所有模块，首次运行可能需要约 20 分钟。

### 使用 `BatchRenderer` 自定义批量生成

```python
from AIPLPhMTools import BatchRenderer, RingPulley, RaceTrackP

renderer = BatchRenderer(output_dir="./custom_batch")

# 参数扫描
for r in [50, 100, 150, 200]:
    renderer.add_job(f"ring_r{r}", lambda r=r: RingPulley(RadiusRing=r))

for length in [50, 100, 200]:
    renderer.add_job(f"rt_l{length}", lambda l=length: RaceTrackP(LengthRun=l))

stats = renderer.run()
print(f"Generated {stats.success_count} GDS files in {stats.total_time:.1f}s")
```

### 使用 `LayoutRenderer` 渲染已有组件

```python
from AIPLPhMTools import LayoutRenderer

renderer = LayoutRenderer(output_dir="./output", validate_before_export=True)

# 逐个渲染
renderer.render(ring1, "ring1.gds")
renderer.render(ring2, "ring2.gds")

# 批量渲染
components = {f"ring_{i}.gds": ring for i, ring in enumerate(rings)}
stats = renderer.render_all(components)
```

---

## 注意事项

### 首次导入时间

首次导入 `AIPLPhMTools` 时，`BasicDefine` 模块需要约 **20 分钟** 初始化（PDK 激活和测试组件创建）。后续导入会使用缓存，速度很快。

### 参数命名约定

不同模块中的参数命名风格可能略有差异：
- **新风格**（推荐）: `width_ring`, `radius_ring`, `gap_ring`（小写 + 下划线）
- **旧风格**: `WidthRing`, `RadiusRing`, `GapRing`（驼峰命名）

两种风格均可正常使用，新风格更符合 Python PEP 8 规范。

### 图层定义

所有图层通过 `LAYER` 对象访问：

```python
from AIPLPhMTools import LAYER

LAYER.WG    # (1, 0)   — 波导层
LAYER.M1    # (10, 0)  — 金属1层
LAYER.M2    # (4, 1)   — 金属2层（高频电极）
LAYER.VIA   # (70, 0)  — 过孔层
LAYER.OPEN  # (20, 0)  — 开窗层
```

### 端口命名约定

| 端口类型 | 命名 | 说明 |
|----------|------|------|
| 光学输入 | `Input`, `o1`, `in1` | 光信号输入 |
| 光学输出 | `Through`, `o2`, `out1` | 光信号输出 |
| Add-Drop | `Add`, `Drop` | 四端口器件的附加端口 |
| 加热器 | `HeatIn`, `HeatOut` | 加热器电学端口 |
| 参考端口 | `RingC`, `TopCenter`, `BottomCenter` | 辅助定位端口 |

### 坐标系约定

- 原点 `(0, 0)` 通常位于组件的左下角或中心
- X 轴正方向向右，Y 轴正方向向上
- 端口方向：0° = 向右，90° = 向上，180° = 向左，270° = 向下

### 工艺预设

工具包内置三套工艺预设，可通过 `get_preset_config` 获取：

| 预设 | 平台 | 波导宽度 | 最小弯曲半径 | 耦合间隙 |
|------|------|----------|-------------|----------|
| `700nmSiN` | 700nm SiN | 0.8~1.0 um | 300 um | 1.0 um |
| `SOI` | 220nm SOI | 0.45~0.5 um | 5 um | 0.2 um |
| `InP` | InP | 2.0 um | 100 um | 0.5 um |

### 常见问题

**Q: 导入时报错 `ModuleNotFoundError: No module named 'gdsfactory'`？**

A: 请确保已安装 gdsfactory >= 9.14.0：
```bash
pip install gdsfactory>=9.14.0
```

**Q: 首次导入为什么这么慢？**

A: `BasicDefine` 模块在初始化时会激活 PDK 并创建测试组件，这是 gdsfactory 的正常行为。后续导入会使用缓存。

**Q: 如何只导入需要的模块？**

A: 使用 `import_module` 按需导入：
```python
from AIPLPhMTools import import_module
Ring = import_module("Ring")
ring = Ring.RingPulley(r_ring=50)
```

**Q: 生成的 GDS 文件在 KLayout 中打开看不到标签？**

A: 标签默认在图层 `(512, 8)`，请在 KLayout 中确保该图层可见。

---

## 许可证

内部使用 — PKU-AIPL 实验室。

---

## 引用

如果在工作中使用了本工具包，请引用：

```
AIPLPhMTools v1.0.0 — PKU-AIPL PIC Component PDK
Based on gdsfactory v9 (https://github.com/gdsfactory/gdsfactory)
```