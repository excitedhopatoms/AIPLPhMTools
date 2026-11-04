"""GeneralTools —— 旧路径兼容命名空间（thin shim）。

2026-11-03 起，实际实现已按职责移动到 ``Core`` / ``Devices`` / ``Assemblies`` /
``TestStructures`` / ``Electrical`` / ``Platforms.SOI``。本包只保留一个版本的
兼容入口，避免旧脚本的 ``AIPLPhMTools.GeneralTools.X`` 立即失效。

新代码请使用新路径，例如::

    from AIPLPhMTools.Devices.Ring import RingPulleyT1
    from AIPLPhMTools.Core.BasicDefine import LAYER

顶层 ``import AIPLPhMTools as ap`` 的用法不变。
"""
from __future__ import annotations

import importlib


def __getattr__(name: str):
    """延迟转发到 AIPLPhMTools 顶层，避免子包与包入口循环导入。"""
    # 先尝试同名子模块（如 gt.BasicDefine），再尝试顶层公共符号
    try:
        return importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError:
        pass
    import AIPLPhMTools as ap
    try:
        return getattr(ap, name)
    except AttributeError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


def __dir__():
    import AIPLPhMTools as ap
    return sorted(set(globals()) | set(dir(ap)))
