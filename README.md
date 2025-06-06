
# PKU-AIPL 光子器件设计代码库  
version: Gdsfactory-v9, Tools-v1o  


## 概述  
本代码库是基于 gdsfactory 的光子集成电路（PIC）组件PDK（Process Design Kit）。

它包含了一系列用于光子器件设计、仿真和版图生成的Python脚本。主要是AIPL实验室自用。


## 文件结构与功能  
本代码库按功能分为几个层次：基础定义、核心PDK单元、高级集成组件和顶层测试组件。这种分层结构有助于代码的维护和扩展。  


### 第一部分：基础与工具模块  
这些模块提供了整个库所需的基础定义和通用辅助功能，是构建所有更高级组件的基石。  

#### 1. BasicDefine.py  
定义了整个PDK的基础，包含自定义的GDS图层映射、预设的波导截面（CrossSection），以及一系列用于创建和操作几何图形的基础函数。  
- **图层定义**：通过 `LayerMapUserDef` 类定义工艺层，如 `LAYER.WG`（波导）、`LAYER.M1`（金属1）、`LAYER.HEATER`（加热器）等，实现设计与工艺层号解耦。  
- **基础组件创建**：  
  - `GfCStraight`：标准直波导。  
  - `GfCBendEuler`：标准欧拉弯曲波导，降低弯曲损耗。  
  - `OffsetRamp`：连接不同宽度或垂直偏移波导的锥形渐变。  
  - `Crossing_taper`：带锥形过渡的波导交叉，降低串扰。  
  - `TaperRsoa`：优化光斑尺寸的RSOA特殊锥形波导。  
  - `cir2end`、`euler_Bend_Half`、`euler_Bend_Part`：生成特殊曲线路径的底层函数。  
- **通用辅助函数**：  
  - `remove_layer`、`GetFromLayer`：组件图层操作。  
  - `add_labels_to_ports`：自动为端口添加文本标签。  
  - `shift_component`：平移组件。  
  - `TWQRcode`：生成二维码标记芯片信息。  

#### 2. Heater.py  
实现热光调谐所需的加热器组件和底层结构。  
- **加热器类型**：  
  - `DifferentHeater`：通用加热器工厂函数，支持类型：  
    - `"default"`：直线/弧形加热条，用于相位调制。  
    - `"side"`/`"bothside"`：波导单侧/双侧加热条，优化热场分布。  
    - `"snake"`：蛇形加热器，增加电阻和加热效率。  
    - `"spilt"`：分裂型加热器，支持复杂电学连接。  
- **底层工具**：  
  - `SnakeHeater`：蛇形加热器核心实现。  
  - `ViaArray`：生成过孔阵列，实现金属层电学连接。  

#### 3. ELE.py  
定义射频（RF）/直流（DC）测试的电极结构。  
- `OpenPad`：开放金属焊盘，中心无顶层金属，用于探针接触或暴露光学结构。  
- `GSGELE`：标准GSG（Ground-Signal-Ground）电极结构，支持高频信号测试，自动生成焊盘阵列。  

#### 4. SnapMerge.py  
提供GDS几何图形的DRC预处理和优化函数。  
- `snap_all_polygons_iteratively`：通过“膨胀-合并-腐蚀”修复间隙/重叠，对齐制造网格。  
- `merge_polygons_in_each_layer`：合并同层相交多边形，简化GDS文件大小，提升制造性能。  


### 第二部分：核心PDK单元  
定义构成复杂结构的基础光子学组件。  

#### 5. Ring.py  
提供多种环形谐振器设计，用于滤波器、开关等。  
- **核心单元**：  
  - `RingPulleyT1`：基础环形谐振器，支持对称/非对称端口、多种加热器。  
  - `RingPulleyT2`：弯曲Pulley耦合器，IO端口90度引出。  
- **封装与变体**：`RingPulley`、`RingPulley1DC`等，快速创建特定配置环。  
- **特殊结构**：`RingPulley3`、`RingFinger`等，用于特殊路由或色散特性。  

#### 6. RaceTrack.py  
定义跑道型谐振器，延长耦合长度以精确控制耦合比。  
- **核心单元**：  
  - `RaceTrackP`：Pulley耦合跑道环。  
  - `RaceTrackS`：直线耦合跑道环，支持GSG电极。  
- **高级变体**：`TaperRaceTrackPulley`（锥形直线段）、`RaceTrackStrHC`（中心对称加热器）。  

#### 7. CouplerMZI.py  
定义耦合器和马赫-曾德尔干涉仪（MZI）。  
- **耦合器**：`PulleyCoupler2X2`（2x2滑轮型定向耦合器）。  
- **MZI结构**：`DMZI`（直波导耦合）、`PMZI`（滑轮耦合，布局紧凑）、`PMZIHSn`（蛇形加热器版本）。  
- **其他**：`SagnacRing`（宽带反射镜，用于激光器腔）。  

#### 8. DBR.py  
实现分布式布拉格反射器（DBR）。  
- `DBR`：参数化创建周期性光栅，支持渐变周期（Chirped DBR）。  
- `DBRFromCsv`/`DBRFromCsvOffset`：从CSV导入外部优化的光栅参数。  
- `SGDBRFromCsvOffset`：从CSV导入外部优化的光栅参数，同时引入周期采样，从而实现类似微环的效果。  

#### 9. Boomerang.py  
定义“回旋镖”形状谐振器，用于大FSR或色散工程。  
- `Boomerang`：核心回旋镖单元，含内外臂和桥接结构。  
- `RingBoomerang`系列：集成回旋镖单元的环形谐振器。  

#### 10. MultiRing.py & MultiRaceTrack.py  
定义多环/多跑道环耦合结构，实现高级滤波功能。  
- `DoubleRingPulley`：串联两环，利用Vernier效应扩大FSR。  
- `CoupleRingDRT1`等：侧边耦合多谐振器，形成CROW单元。  

#### 11. Isolator.py  
基于环形谐振器的隔离器原型。  
- `SingleRingIsolator0`/`SingleRingIsolator1`：单环实现波长选择性“伪隔离”。  
- `RingAndIsolator0`：集成梳状环和隔离器环的复合结构。  

#### 12. memyshev.py  
实现Memyshev激光器的双环反射器结构。  
- `DoubleRingMemyshev`：含1x2分束器、双环谐振器和反射器，提供精确光谱滤波。  


### 第三部分：顶层集成组件模块  
调用核心单元，添加标准IO接口和端口路由，形成可直接例化的“总组件”（TC）。  

#### 13. ExtCav.py  
构建外腔激光器核心光学回路，集成增益芯片接口、耦合器和调谐元件。  
- `ExternalCavitySOI`/`ExternalCavitySiN`：SOI/SiN平台外腔结构，集成MZI和多环。  
- `ExternalCavityRaceTrack`：基于跑道环的外腔设计。  

#### 14. TCRaceTrack.py  
提供跑道型谐振器完整测试结构，添加引出臂和IO组件。  
- `TCRaceTrackP`/`TCRaceTrackS`系列：不同耦合方式和IO路由的跑道环测试结构。  
- `TCTaperRaceTrackP`/`TCTaperRaceTrackS`：基于锥形跑道环的测试结构。  

#### 15. TCCoupledCavity.py  
提供复杂耦合腔测试结构，面向多谐振器器件。  
- `TCRingBoomerangT1`系列：封装回旋镖谐振器，提供四端口引出。  
- `TCCoupleDouRingT1`系列：侧向耦合多谐振器系统，设计端口路由。  

#### 16. TCRing.py  
提供通用环形谐振腔组件库，封装基础环为可测试器件。  
- **核心函数**：  
  - `TCRingT1`/`TCRingT2`：基于不同耦合方式的环，支持灵活IO路由。  
  - `TCRing1AD`/`TCRing1DC`：四端口Add-Drop滤波器，支持非对称耦合。  
- **特殊结构**：`TCFingerRing1`（山形环）、`TCRingDCouple`（自耦合环，产生Fano谐振）。  


## 使用示例  
### 创建直线波导  
```python  
import gdsfactory as gf  
from .BasicDefine import GfCStraight, LAYER  

# 创建长度20um、宽度1um的直线波导  
straight_waveguide = GfCStraight(length=20, width=1, layer=LAYER.WG)  
straight_waveguide.show()  # 在gdsfactory KLayout中显示  
```  

### 创建带IO的环形谐振器  
```python  
import gdsfactory as gf  
from .TCRing import TCRing  

# 创建默认参数的环形谐振器测试结构（含IO锥形波导和加热器）  
tc_ring_component = TCRing(r_ring=50, width_ring=0.8, is_ad=False)  
tc_ring_component.show()  # 显示组件  
```