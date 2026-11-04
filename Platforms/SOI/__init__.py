"""AIPLPhMTools.SOITools —— SOI 硅光（12 英寸、三层金属）版图子库。

从 ICRD 项目（``202610_SOI_icrd``）的 ``ICRDPhMTools`` 提炼出的**可复用**部分，
层号表与工艺常数与那套流片文件一致（SOI 220 nm Si + 双层 SiN + TiN 加热 +
M1/M2/M3 + ALPAD/COVER，层号 600/631/632/639/641..643/651..652/660..662/665）。

为什么单独一个子包
------------------
AIPLPhMTools 主库用的是另一套层号（WG 1/0、M1 10/0、M2 4/1、SiN 130/0 ...）。
把 SOI 的 ``M1=(641,1)`` 混进主库命名空间会互相覆盖，所以这里做**显式命名空间**：

    import AIPLPhMTools.SOITools as soi          # 推荐
    from AIPLPhMTools.SOITools import Route, add_si_route, add_bond_pad

**不要**在 ``AIPLPhMTools/__init__.py`` 里 star-import 本子库。

模块
----
===============  ==========================================================
``FabBasic``       SOI 层号表（SIWG/SIN/SIN3/TIN/M1..M3/V1/V2/RV/ALPAD/
                   COVER/SINOP/PB/TEXT）、工艺常数（W_SI/W_SIN/…/R_SI/R_SIN）、
                   最小绘图函数 ``box/add_poly/cosd/sind``
``Geometry``       切线连续 ``Route``（straight/turn/s_bend）、等宽/闭合/
                   变宽条带、圆弧环带 ``add_annulus``、pulley 弧
``Routing``        Si / SiN 走线：核心 + 631/10·632/10·600/10 开窗 + SINOP；
                   锥形入口 ``add_sin_route_taper``、宏间链路 ``add_si_link``
``Electrical``     过孔阵列、金属引线、``add_bond_pad(landing=...)``、
                   TiN 落点 ``add_heat_landing``
``Ring``           ``RingPulley`` 单侧 pulley 耦合环 / ``RaceTrackPulley``
                   跑道腔（弯段 pulley 耦合），都带端口
``Spiral``         闭合双螺旋腔中心线（SOI SiN 长延迟线）
``Facet``          12.9° 斜端面 + 反角弯（RSOA / 光纤端面耦合）
``Audit``          GDS -> shapely：并集、连通网、线宽、断言（``GdsAudit``）
``Assembly``       带端口的组件包装 + ``reference.connect`` 组装 + PDK 宏加载

PDK 宏目录
----------
本子库不带 PDK 宏 GDS。需要 ``pdk()`` / RingPulley 的宏时，先指定目录::

    import AIPLPhMTools.SOITools as soi
    soi.set_pdk_dir("S:/path/to/gdsPDK")     # 或设环境变量 SOI_PDK_DIR

快速开始
--------
::

    import gdsfactory as gf
    import AIPLPhMTools.SOITools as soi

    c = gf.Component("demo")
    p = soi.Route(0, 0, 0).straight(100).turn(-90, soi.R_SI).straight(50)
    soi.add_si_route(c, p.pts)                       # 600/1 + 600/10
    soi.add_bond_pad(c, 40, -40, size=60, cover=40,
                     landing="M2")                   # M2 → V2 → M3/ALPAD
"""

from __future__ import annotations

from pathlib import Path

from .FabBasic import *
from .Geometry import *
from .Electrical import *
from .Routing import *
from .Audit import *
from .Assembly import *
from .Ring import RaceTrackPulley, RingPulley
from . import Spiral
from . import FabBasic


def set_pdk_dir(path) -> Path:
    """设置 PDK 宏 GDS 目录（``pdk()`` / ``RingPulley`` 等宏加载用）。

    子库本身不绑定项目路径：默认读环境变量 ``SOI_PDK_DIR``，或者调用本函数。
    返回设置后的 ``Path``；目录不存在时抛 ``FileNotFoundError``。
    """
    p = Path(path)
    if not p.is_dir():
        raise FileNotFoundError(f"SOI PDK dir not found: {p}")
    FabBasic.PDK_DIR = p
    globals()["PDK_DIR"] = p
    return p


PDK_DIR = FabBasic.PDK_DIR
