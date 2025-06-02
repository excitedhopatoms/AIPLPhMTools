# PKU-AIPL 光子器件设计代码库

- *version:* **Gdsfactory-v9,Tools-v1o**

## 概述
本代码库包含了一系列用于光子器件设计的Python代码。这些代码利用了 `gdsfactory` 库，用于创建、操作和优化光子集成电路（PIC）中的各种组件。

## 文件结构与功能

### 1. `BasicDefine.py`
此文件包含了多个基础组件的定义和辅助函数，用于创建和操作光子器件。

#### 主要功能
- **基本组件创建**
    - `GfCStraight`：创建一个直线波导组件，可指定长度、宽度和层。
    - `GfCBendEuler`：创建一个欧拉弯曲波导组件，其弯曲半径可变。
    - `TaperRsoa`：创建一个用于RSOA（半导体光放大器）的锥形波导组件。
    - `Crossing_taper`：创建一个带有锥形过渡的交叉波导组件。
    - `OffsetRamp`：创建一个具有偏移的斜坡组件。
    - `TWQRcode`：创建一个包含二维码的组件，用于标记或识别。
    - `cir2end`：创建一个从圆形到端部的过渡组件，通常用于构建螺旋结构。

- **组件操作函数**
    - `remove_layer`：从组件中删除指定层的所有多边形。
    - `GetFromLayer`：从组件中提取指定层的多边形并创建一个新组件。
    - `shift_component`：将组件中的所有元素沿x和y方向移动指定的距离。

- **路径生成函数**
    - `euler_Bend_Half`：生成一个从弯曲到直线的绝热过渡欧拉弯曲路径。
    - `euler_Bend_Part`：生成一个曲率从 `radius1` 过渡到 `radius2` 的欧拉弯曲路径。

- **标签添加函数**
    - `add_labels_to_ports`：为组件的端口添加标签，方便识别和调试。

### 2. `CouplerMZI.py`
此文件主要用于创建和操作光子耦合器和马赫 - 曾德尔干涉仪（MZI）结构。

#### 主要功能
- **耦合器创建**
    - `PulleyCoupler2X2`：创建一个2x2的Pulley定向耦合器，可指定宽度、角度、半径和间隙等参数。

- **MZI结构创建**
    - `PMZI`：创建一个Pulley耦合的MZI结构，包含输入、输出端口和可选的加热器。
    - `DMZI`：创建一个基于直波导定向耦合器的MZI结构，可配置臂长、耦合长度及可选加热器。
    - `PMZIHSn`：`PMZI` 的一个变种，特指使用蛇形加热器（snake heater）。
    - `SagnacRing`：创建一个Sagnac环形干涉仪/反射镜结构，使用 `PulleyCoupler2X2` 作为核心耦合元件。

### 3. `Boomerang.py`
此文件用于创建基于“回旋镖”形状的复杂谐振器组件。

#### 主要功能
- **回旋镖组件创建**
    - `Boomerang`：定义核心的回旋镖单元，包含内外环臂、桥接波导和锥形过渡，支持内外臂独立加热。
- **环形回旋镖结构创建**
    - `RingBoomerang`：创建一个单回旋镖环形谐振器，具有输入、直通、添加和下降端口。
    - `RingDouBoomerang`：创建一个由两个回旋镖组件串联或并联构成的双环谐振器结构。
    - `RingTriBoomerang`：创建一个由三个回旋镖组件构成的环形三角回旋镖结构，并添加了相应的输入、直通、添加和下降端口。

### 4. `DBR.py`
此文件用于创建分布式布拉格反射器（DBR）结构，支持通过固定参数或从 CSV 文件读取参数来生成 DBR 组件，并且可以选择是否添加加热器。

#### 主要功能
- **分布式布拉格反射器创建**
    - `DBR`：根据给定的波导宽度、长度、周期数等参数创建一个分布式布拉格反射器，支持渐变长度模式和固定长度模式，可选择是否添加加热器。
    - `DBRFromCsv`：从 CSV 文件中读取波导的宽度和长度信息，创建分布式布拉格反射器，同样可选择是否添加加热器。
    - `DBRFromCsvOffset`：在从 CSV 文件读取参数的基础上，对波导宽度进行偏移处理，再创建分布式布拉格反射器，也可选择是否添加加热器。

### 5. `ELE.py`
此文件用于创建多种电极相关的组件，包括开放焊盘、偏移斜坡和GSG电极，支持不同的参数配置以满足多样化的设计需求。

#### 主要功能
- **开放焊盘创建**
    - `OpenPad`：创建一个开放焊盘组件，包含一个中心焊盘和外围的电极层。可通过指定中心焊盘的宽度、电极层与中心焊盘的间距、中心焊盘和电极层的层定义来生成组件。组件具有四个端口，分别为左侧、右侧、上侧和下侧端口。

- **偏移斜坡创建**
    - `OffsetRamp`：创建一个偏移斜坡组件，用于连接不同宽度的波导。可设置斜坡的长度、起始端和终止端的宽度、输出端中心相对于输入端中心的偏移量以及斜坡的层定义。组件具有输入端和输出端两个端口。

- **GSG电极创建**
    - `GSGELE`：创建一个GSG电极组件，支持焊盘和双焊盘配置。可指定G电极和S电极的宽度、G电极与S电极之间的间距、电极的长度，还能选择是否添加焊盘或双焊盘，以及设置焊盘的相关参数（如间距、宽度、外围电极层间距等）和层定义。组件具有多个端口，包括输入输出端口和G、S电极的输入输出端口。

### 6. `ExtCav.py`
此文件用于创建不同类型的外部腔（External Cavity）结构，主要应用于光学器件设计，提供了多种经过验证的设计方案，可根据不同的需求和材料（如 SOI、SiN 等）进行选择，同时支持对结构的多个参数进行灵活配置。

#### 主要功能
- **外部腔结构创建**
    - `ExternalCavitySOI`：创建基于绝缘体上硅（SOI）材料的外部腔结构。可通过设置环半径、波导宽度、长度、间隙等参数来定制该结构，并且可以选择是否添加加热器。
    - `ExternalCavitySiN`：为氮化硅（SiN）材料并带有加热器的情况设计的外部腔结构。相较于 `ExternalCavitySOI`，增加了一些特定参数，如欧拉半径、MZI 环半径等，以适应 SiN 材料的特性，同样支持加热器的添加。
    - `ExternalCavitySiNH2`：另一种适用于 SiN 材料加加热器的外部腔结构设计。该结构在参数设置上与 `ExternalCavitySiN` 有部分差异，对环与耦合器之间的长度、总线加热器长度等进行了特殊设置。
    - `ExternalCavitySiNH2_1`：与 `ExternalCavitySiNH2` 类似，也是针对 SiN 材料加加热器的设计，但环与环之间采用弯曲连接方式，可根据实际需求调整相关参数。
    - `ExternalCavity2`：创建一个三环外部腔激光器（tri ring ecl）结构。该结构具有特定的角度和长度参数设置，可用于特定的光学应用场景。
    - `ExternalCavity3`：一种风险设计的外部腔结构，在参数设置上与其他结构有所不同，如路由层的选择等，可用于探索新的设计可能性。
    - `ExternalCavitryRaceTrack`：创建一个基于跑道型谐振器的外部腔结构，可配置多种参数，如环半径、MZI参数、耦合器类型等，并支持加热器集成。

### 7. `Heater.py`
该文件实现了不同类型的加热器组件，包括蛇形加热器、多种不同布局的加热器，以及通孔阵列的生成。

#### 主要功能
- **加热器创建**
    - `SnakeHeater`：创建蛇形加热器，可通过设置加热器宽度、波导宽度、间隙等参数进行定制。
    - `DifferentHeater`：根据不同的 `TypeHeater` 参数，创建不同类型的加热器，如默认加热器、蛇形加热器、侧边加热器、两侧边加热器和分割型加热器（spilt-type）等。
    - `ViaArray`：在给定组件内部高效生成通孔阵列，可设置通孔宽度、间距、包围距离等参数。

### 8. `Isolator.py`
此文件用于创建单环隔离器相关的组件，包含三种不同类型的单环隔离器和一个环与隔离器的组合结构。

#### 主要功能
- **单环隔离器创建**
    - `SingleRingIsolator0`：创建一个包含 ADD - DROP 环和监测器的单环隔离器，通过设置环的半径、宽度、耦合角度等参数来定制结构。
    - `SingleRingIsolator1`：在 `SingleRingIsolator0` 的基础上增加了监测功能，同样可以通过多个参数进行结构定制。
    - `RingAndIsolator0`：创建一个环与单环隔离器的组合结构，用于梳状滤波器和 ADD - DROP 环的组合，支持参数化定制。

### 9. `memyshev.py`
此文件实现了一种特定的反射器结构，即双环 Memyshev 反射器。

#### 主要功能
- **双环 Memyshev 反射器创建**
    - `DoubleRingMemyshev`：创建一个双环 Memyshev 反射器，通常用于构建 Memyshev 激光器腔。该结构包含两个环形谐振器（基于`RingPulleyT1`）和两个Sagnac环反射镜（基于`SagnacRing`），通过一个1x2 MMI或自定义耦合器连接。可通过设置环的半径、宽度、耦合角度、加热器参数等，实现结构的定制。

### 10. `MultiRing.py`
此文件用于创建多种复杂的多环形谐振器结构，支持加热电极、不同连接方式及耦合配置，适用于光子集成电路中的滤波、传感等应用。

#### 主要功能
##### 10.1. **双环形谐振器结构**
- **`DoubleRingPulley`** 创建双环形谐振器组件，由两个 `RingPulleyT1` 构成，支持直连或弯曲连接方式 (`TypeR2R`)，可选多种加热器类型及配置 (`TypeHeater`, `DirectionsHeater`)。
  **关键参数**：
  - `WidthRing`: 环形波导宽度（μm）
  - `LengthR2R`: 环间连接长度（μm）
  - `DeltaRadius`: 两个环的半径差（μm）
  - `TypeHeater`: 加热器类型（`"default"`, `"snake"`, `"side"`, `"bothside"`）
  - `IsHeat`: 是否包含加热电极
  **端口**：`o1`（输入）, `o2`（第二环输入）, `R1Add`（Add端口）, `R1HeatIn`（加热输入）等。

- **`DoubleRingPulley2HSn`** 带蛇形加热器的双环形谐振器，是 `DoubleRingPulley` 的一个特例，固定 `TypeHeater="snake"`。

- **`DoubleRingPulley2_1HSn`** 环形间采用圆形弯曲连接（`TypeR2R="bend"`）的双环形结构，集成蛇形加热器 (`TypeHeater="snake"`)。

##### 10.2. **三环形谐振器与交叉波导**
- **`ADRAPRADR`** 创建包含三个环形谐振器（两个 `RingPulley` 带Add-Drop，一个 `RingPulley2` 全通）和可选交叉波导的复杂结构。
  **关键参数**：
  - `RadiusCrossBend`: 交叉波导弯曲半径（μm）
  - `IsSquare`: 是否使用方形布局（当提供`CrossComp`时）
  **端口**：`r1Th`（Through端口）, `co2`（交叉输出, if `IsSquare` and `CrossComp`）等。

##### 10.3. **耦合腔结构**
- **`CoupleRingDRT1`** 支持不同尺寸和参数的两个 `RingPulleyT1` 进行特定方式耦合（第二个环的波导部分由基本ring创建，加热器部分从`RingPulleyT1`提取并放置）。适用于高精度传感。
  **关键参数**：
  - `GapRR`: 环间垂直间隙（μm）
  - `AngleR12`: 第二个环相对于第一个环的旋转角度
  - `TypeHeaterR1/R2`: 各环加热器类型

### 11. `RaceTrack.py`
此文件用于创建跑道形谐振器及其变体，支持锥形耦合、加热电极集成及热隔离刻蚀层。

#### 主要功能
##### 11.1. **基础跑道形谐振器**
- **`RaceTrackP`** (`RaceTrackPulley` in README)
  标准跑道形谐振器，采用Pulley型耦合器，支持输入/输出端口和Add-Drop端口。
  **关键参数**：
  - `LengthRun`: 直线部分长度（μm）
  - `AngleCouple`: 耦合角度（°）

- **`RaceTrackS`** (`RaceTrackPulley2HS` in README potentially refers to this with heater)
  跑道形谐振器，采用直线型耦合段，支持Add-Drop端口及多种加热器类型（包括通过`GSGELE`实现的电极）。
  **关键参数**：
  - `LengthRun`: 直线部分长度（μm）
  - `LengthCouple`: 耦合部分长度（μm）
  - `TypeHeater`: 加热器类型 (`"default"`, `"snake"`, `"side"`, `"bothside"`, `"center"`, `"ELE"`)

##### 11.2. **高级跑道形结构**
- **`TaperRaceTrackPulley`**
  带锥形耦合的跑道形谐振器，跑道本身的直线段也是锥形的，优化模式匹配，减少插入损耗。
  **关键参数**：
  - `LengthTaper`: 跑道直段的锥形部分长度（μm）
  - `WidthRun`: 跑道直段较宽处的宽度（μm）

- **`RaceTrackStrHC`**
  一个内部辅助函数，被 `RaceTrackS` 调用，用于创建中心对称的复杂加热器结构，通过布尔运算实现。

### 12. `Ring.py`
此文件提供多种环形谐振器设计，涵盖不同耦合类型、加热配置及电子线路集成。

#### 主要功能
##### 12.1. **核心环形谐振器单元**
- **`RingPulleyT1`** 通用的环形谐振器单元，采用直Pulley型耦合器。支持Add-Drop端口，可配置不同类型加热器 (`TypeHeater`)，并能独立设置主耦合区和Add/Drop区的耦合参数。
  **关键参数**：
  - `TypeHeater`: 加热器类型（`"default"`, `"snake"`, `"side"`, `"bothside"`, `"spilt"`）
  - `GapHeat`: 加热电极间隙（μm）
  - `WidthNear2`, `GapRing2`, `AngleCouple2`: 用于Add/Drop侧的不同耦合参数。
  - `IsTrench`: 是否添加热隔离沟槽。

- **`RingPulleyT2`**
  通用的环形谐振器单元，采用弯曲Pulley型耦合器，导致端口呈90度出射。支持加热器配置。

##### 12.2. **基于核心单元的封装函数**
- **`RingPulley`**: `RingPulleyT1` 的简化封装，默认加热类型。
- **`RingPulley1DC`**: `RingPulleyT1` 的封装，专用于上下耦合器参数独立配置。
- **`RingPulley1HS`**: `RingPulleyT1` 的封装，专用于侧边加热器 (`TypeHeater="side"`)。
- **`RingPulley1HSn`**: `RingPulleyT1` 的封装，专用于蛇形加热器 (`TypeHeater="snake"`)。
- **`RingPulley2`**: `RingPulleyT2` 的简化封装。
- **`RingPulley2ES`**: `RingPulleyT2` 的封装，专用于双侧电极/加热器 (`TypeHeater="bothside"`)。

##### 12.3. **特殊耦合与形状结构**
- **`RingPulley3`**, **`RingPulley4`**: 具有大角度耦合器的环形谐振器，用于特定路由或高密度集成需求。
- **`RingFinger`**: 山形或指状的环形谐振器，具有非传统的环路形状。

##### 12.4. **加热器模块 (内部辅助)**
- **`DifferentHeater_local`** 一个内部辅助函数，用于在`RingPulleyT1`和`RingPulleyT2`等组件内部创建和放置各种类型的加热器。

### 13. `SnapMerge.py`
此文件提供了对 `gdsfactory` 组件进行几何体优化和修正的关键工具函数，主要用于确保设计符合制造要求（DRC clean）和提高GDS文件的健壮性。

#### 主要功能
- **顶点对齐 (Snapping)**
    - `snap_polygon_vertices`: 将单个多边形的顶点精确对齐到预设的制造网格上。
    - `snap_all_polygons_iteratively`: 核心处理函数。首先扁平化输入组件以访问所有几何图形，然后对每个图层上的多边形执行“膨胀-合并-腐蚀”操作（通过先放大微小量，合并重叠区域，再缩小相同量）以修复微小的间隙或重叠，并简化复杂的图形。最后，将所有处理过的多边形顶点以及组件的端口（ports）和标签（labels）位置对齐到指定的制造网格。

- **多边形合并 (Merging)**
    - `merge_polygons_in_each_layer`: 在组件的每一个图层上，将所有相交或接触的多边形合并成尽可能少的、更大的多边形。这通过对同一图层上的所有形状执行布尔“OR”运算来实现，有助于简化GDSII文件并可能改善某些制造过程的性能。

### 14. `TCCoupledCavity.py`
此文件用于创建完整的、通常带有输入输出结构的耦合环形谐振腔组件，支持多种环形拓扑（如基于Boomerang的单环、双环、三环谐振器）和加热器配置，提供灵活的几何参数控制。这些组件通常代表了一个完整功能模块。

#### 主要功能
- **完整多环耦合腔体结构**
  - `TCRingBoomerangT1`：基于 `RingBoomerang` 创建单环形谐振腔，集成输入/输出锥形波导、加热器及多端口配置，可控制耦合间距和加热器类型。
  - `TCRingDouBoomerangT1`：基于 `RingDouBoomerang` 创建双环形耦合谐振腔，支持更复杂的耦合路径和垂直/水平布局参数调整。
  - `TCRingTriBoomerangT1`：基于 `RingTriBoomerang` 创建三环形级联谐振腔，支持多段耦合桥和分层加热器设计。
  - `TCCoupleDouRingT1`：基于 `CoupleRingDRT1` 创建双环直接耦合结构，支持独立控制两个环的半径、宽度和加热器参数，并进行整体路由。
  - `TCCoupleDouRaceTrackT1`：旨在为耦合双跑道谐振器提供完整布线（注意：其内部实现可能需要核对是否正确调用了跑道谐振器而非环形谐振器）。

### 15. `TCRaceTrack.py`
此文件用于设计完整的、带有标准输入输出结构的跑道型（RaceTrack）谐振腔及其变体，支持直线耦合段、加热器集成和多种输入/输出路径配置。

#### 主要功能
- **完整跑道型谐振腔**
  - `TCRaceTrackP`：基于 `RaceTrackP` (Pulley耦合跑道谐振器) 创建完整组件，集成输入/输出光栅或锥形波导，并完成端口路由。
  - `TCRaceTrackS`, `TCRaceTrackS2`, `TCRaceTrackS3`：基于 `RaceTrackS` (直线耦合跑道谐振器) 创建完整组件，提供不同耦合方向和布局的变体，并完成端口路由。
  - `TCRaceTrackS3h`：`TCRaceTrackS3` 的带加热器版本，并暴露加热器端口。
  - `TCTaperRaceTrackP`：基于 `TaperRaceTrackPulley` (直段锥形、Pulley耦合跑道谐振器) 创建完整组件。
  - `TCTaperRaceTrackS`：基于锥形耦合段的跑道型结构，但采用直线耦合，并完成端口路由。

### 16. `TCRing.py`
此文件提供通用的、完整的环形谐振腔组件库，涵盖多种耦合方式（角度/长度/方向）、加热器类型和端口配置，并包含标准化的输入输出结构。

#### 主要功能
- **基础完整环形谐振腔**
  - `TCRingT1`：基于 `RingPulleyT1` 的核心函数，提供灵活的输入/输出路由选项，包括锥形波导在Through路径上的不同放置策略 (`position_taper`)。
  - `TCRingT2`：基于 `RingPulleyT2` 的核心函数，同样提供灵活的路由选项。
  - `TCRing`：`TCRingT1` 的简化封装。
  - `TCRing1AD`：基于 `RingPulley` 创建带Add/Drop端口的完整环形滤波器结构。
  - `TCRing1_3`：`TCRingT1` 的简化版本，无加热器和特定输出路由 (不推荐使用)。
  - `TCRing1DC`：基于 `RingPulley1DC` (不同耦合参数的环) 创建完整组件。
  - `TCRing2`: `TCRingT2` 的简化封装，无加热器 (不推荐使用)。
  - `TCRing2ES`: 基于 `RingPulley2ES` (带双侧电极) 创建完整光电组件，分别导出光学部和电学部。
  - `TCRing2_2`, `TCRing2_3`: `TCRingT2` 的封装，具有特定的 `position_taper` 配置。

- **特殊拓扑结构的完整组件**
  - `TCRing3`, `TCRing4`：基于 `RingPulley3` 和 `RingPulley4` (大角度耦合器环) 创建完整组件。
  - `TCFingerRing1`：基于 `RingFinger` (山形环) 创建完整组件。
  - `TCRingDCouple`：创建一个特殊的双耦合环结构，其中一个标准Add/Drop环的输入和Drop端口通过一个带加热器的波导段相连接，形成一个复合谐振结构。

---
## 使用示例

### 创建直线波导
```python
import gdsfactory as gf
# 假设 FabBasic_hjh 是代码库的顶层包名
from FabBasic_hjh.BasicDefine import GfCStraight

# 创建一个长度为20um，宽度为1um的直线波导
straight_waveguide = GfCStraight(length=20, width=1)
straight_waveguide.show()  # 显示波导