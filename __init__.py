"""AIPLPhMTools —— 基于 gdsfactory 的光子版图器件库。

本包提供两类内容：

1. ``GeneralTools``：主器件库（层号表 ``LAYER``、截面、直/弯波导、环/跑道环、
   耦合器、MZI、DBR、加热器、电极、外腔以及测试结构）。
   所有"画版图"的函数都返回 ``gdsfactory.Component``，并尽量使用 ``@gf.cell``
   缓存；导入本包**不会**产生任何几何副作用。
2. ``SOITools``：另一套 SOI 工艺（12 英寸、三层金属）的独立命名空间子库，
   必须用 ``import AIPLPhMTools.SOITools as soi`` 访问，不能在主命名空间 star-import。

约定
----
* 参数单位统一为 µm；端口名区分大小写，构造后可用 ``c.ports`` 查看。
* 组合器件优先用 ``connect`` 对齐，不在下游手写绝对坐标。
* ``list_components()`` 返回本包全部公共器件构造函数名；
  ``get_component(name)`` 按名字取回构造函数。
"""

from __future__ import annotations

import importlib
from typing import Any, Callable

# ---------------------------------------------------------------------------
# 模块导入顺序有讲究：
#   * DBR_inv 的 __all__ 不含重名的 EDBRStrRep，因此必须在 DBR 之前导入，
#     让 DBR.EDBRStrRep 成为包级公开符号；
#   * BasicDefine 必须最先导入（其余模块都依赖 LAYER / 基础函数）。
# ---------------------------------------------------------------------------
_MODULES: tuple[str, ...] = (
    "BasicDefine",
    "EulerConnection",
    "Heater",
    "SnapMerge",
    "ELE",
    "Boomerang",
    "CouplerMZI",
    "DBR_inv",
    "DBR",
    "GongCavity",
    "Isolator",
    "MultiRaceTrack",
    "MultiRing",
    "RaceTrack",
    "Ring",
    "TCCoupledCavity",
    "TCRaceTrack",
    "TCRing",
    "WangCavity",
    "ExtCav",
    "memyshev",
)

_loaded: dict[str, Any] = {}
for _mod_name in _MODULES:
    _loaded[_mod_name] = importlib.import_module(f".GeneralTools.{_mod_name}", __name__)

# 兼容历史写法：`from AIPLPhMTools import RingPulley` / `import AIPLPhMTools as ap`
from .GeneralTools.BasicDefine import *  # noqa: F401,F403
from .GeneralTools.EulerConnection import connect_ports_euler  # noqa: F401
from .GeneralTools.Heater import *  # noqa: F401,F403
from .GeneralTools.ELE import *  # noqa: F401,F403
from .GeneralTools.Boomerang import *  # noqa: F401,F403
from .GeneralTools.CouplerMZI import *  # noqa: F401,F403
from .GeneralTools.DBR_inv import *  # noqa: F401,F403
from .GeneralTools.DBR import *  # noqa: F401,F403
from .GeneralTools.GongCavity import *  # noqa: F401,F403
from .GeneralTools.Isolator import *  # noqa: F401,F403
from .GeneralTools.MultiRaceTrack import *  # noqa: F401,F403
from .GeneralTools.MultiRing import *  # noqa: F401,F403
from .GeneralTools.RaceTrack import *  # noqa: F401,F403
from .GeneralTools.Ring import *  # noqa: F401,F403
from .GeneralTools.TCCoupledCavity import *  # noqa: F401,F403
from .GeneralTools.TCRaceTrack import *  # noqa: F401,F403
from .GeneralTools.TCRing import *  # noqa: F401,F403
from .GeneralTools.WangCavity import *  # noqa: F401,F403
from .GeneralTools.ExtCav import *  # noqa: F401,F403
from .GeneralTools.memyshev import *  # noqa: F401,F403

# 非器件函数：出现在模块 __all__ 里但不是"返回 Component 的构造函数"
_NON_COMPONENTS = {
    "boomerang_heater",
    "connect_ports_euler",
    "snap_polygon_vertices",
    "snap_all_polygons_iteratively",
    "merge_polygons_in_each_layer",
    "merge_polygons_in_layer",
    "create_taper",
    "localheater",
    "DifferentHeater",
    "SnakeHeater",
    # 需要调用者提供源组件，不属于"默认参数即可构建"的器件
    "ViaArray",
    "ViaArray_optimized",
    "ViaArrayParallel",
    "make_flush_inverted_cell",
}

# BasicDefine 没有定义 __all__（其它模块靠 star-import 取它的内部符号），
# 这里显式登记其中的公共器件构造函数。
_BASIC_COMPONENTS = (
    "GfCStraight",
    "GfCBendEuler",
    "Crossing_taper",
    "TaperRsoa",
    "OffsetRamp",
    "cir2end",
)

# 公共器件注册表：只收模块 __all__ 里声明的、可调用的名字。
COMPONENTS: dict[str, Callable[..., Any]] = {}
for _mod_name in _MODULES:
    _mod = _loaded[_mod_name]
    for _name in getattr(_mod, "__all__", ()):
        if _name in _NON_COMPONENTS:
            continue
        _obj = getattr(_mod, _name, None)
        if callable(_obj):
            COMPONENTS.setdefault(_name, _obj)

for _name in _BASIC_COMPONENTS:
    _obj = getattr(_loaded["BasicDefine"], _name, None)
    if callable(_obj):
        COMPONENTS.setdefault(_name, _obj)


def list_components() -> list[str]:
    """返回本包全部公共器件构造函数名（按字母排序）。"""
    return sorted(COMPONENTS)


def get_component(name: str) -> Callable[..., Any]:
    """按名字取回器件构造函数；不存在时抛 ``KeyError`` 并提示可用名字。"""
    try:
        return COMPONENTS[name]
    except KeyError:
        available = ", ".join(list_components())
        raise KeyError(f"未知器件 {name!r}。可用器件：{available}") from None


__version__ = "0.2.0"

__all__ = [
    "COMPONENTS",
    "HeaterConfigClass",
    "LAYER",
    "LayerMapUserDef",
    "get_component",
    "list_components",
    *sorted(COMPONENTS),
]
