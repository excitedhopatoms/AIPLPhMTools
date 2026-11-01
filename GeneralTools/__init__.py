"""GeneralTools —— 通用器件库（gdsfactory 版图组件）。

推荐直接从顶层导入，保持与旧写法一致::

    import AIPLPhMTools as ap
    c = ap.RingPulleyT1()

如果确实需要子包命名空间，``import AIPLPhMTools.GeneralTools as gt`` 也可以：
本文件通过 ``__getattr__`` 把顶层公共符号（``LAYER``、``RingPulleyT1`` 等）
转发过来，不重复实现、也不会在导入时创建几何。
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
