"""AIPLPhMTools —— 基于 gdsfactory 的光子版图器件库。

目录结构（2026-11-03 重组）：

* ``Core``         层号/截面/直弯锥/路由/几何工具（``BasicDefine``、``EulerConnection``、
                   ``SnapMerge``、``LayerStack``、``GdsMerge``）
* ``Devices``      单器件：Ring / RaceTrack / CouplerMZI / DBR / FeedbackCavity ...
* ``Assemblies``   多器件装配：MultiRing / MultiRaceTrack / ExtCav / Isolator ...
* ``TestStructures`` 测试/表征结构：TCRing* / TCRaceTrack* / TCCoupledCavity* / Coupon ...
* ``Electrical``   加热器与焊盘/过孔
* ``Platforms.SOI`` SOI 12 英寸平台子库（原 ``SOITools``）

兼容性：旧路径 ``AIPLPhMTools.GeneralTools.<module>`` 与
``AIPLPhMTools.SOITools`` 保留为 thin shim，至少保留一个版本周期。
新代码请使用新子包路径；顶层 ``import AIPLPhMTools as ap`` 用法不变。

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
    "Core.BasicDefine",
    "Core.EulerConnection",
    "Core.SnapMerge",
    "Core.LayerStack",
    "Core.GdsMerge",
    "Electrical.Heater",
    "Electrical.ELE",
    "Devices.CouplerMZI",
    "Devices.Ring",
    "Devices.RaceTrack",
    "Devices.CoupledCavity",
    "Devices.Boomerang",
    "Devices.GongCavity",
    "Devices.memyshev",
    "Devices.DBR_inv",
    "Devices.DBR",
    "Devices.FeedbackCavity",
    "Assemblies.MultiRing",
    "Assemblies.MultiRaceTrack",
    "Assemblies.Isolator",
    "Assemblies.WangCavity",
    "Assemblies.ExtCav",
    "TestStructures.Coupon",
    "TestStructures.TCCoupledCavity",
    "TestStructures.TCRaceTrack",
    "TestStructures.TCRing",
    "TestStructures.TestRow",
)

_loaded: dict[str, Any] = {}
for _mod_name in _MODULES:
    _loaded[_mod_name] = importlib.import_module(f".{_mod_name}", __name__)

# 兼容历史写法：`from AIPLPhMTools import RingPulley` / `import AIPLPhMTools as ap`
from .Core.BasicDefine import *  # noqa: F401,F403
from .Core.LayerStack import LayerDef, LayerStack  # noqa: F401
from .Core.EulerConnection import connect_ports_euler  # noqa: F401
for _mod in _loaded.values():
    for _name in getattr(_mod, "__all__", ()):
        globals()[_name] = getattr(_mod, _name)

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
    # 配置对象 / 通用框架，不是默认参数可构建的器件
    "RingCouponSpec",
    "Coupon",
    "LayerDef",
    "LayerStack",
    # GDS 合并工具：是函数/报告类，不是"返回 Component 的构造函数"
    "MergeReport",
    "cell_signature",
    "merge_gds",
    "merge_into_kcl",
    "find_conflicts",
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
    _obj = getattr(_loaded["Core.BasicDefine"], _name, None)
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
    "LayerDef",
    "LayerMapUserDef",
    "LayerStack",
    "get_component",
    "list_components",
    "MergeReport",
    "cell_signature",
    "merge_gds",
    "merge_into_kcl",
    "find_conflicts",
    *sorted(COMPONENTS),
]
