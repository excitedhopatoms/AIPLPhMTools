"""兼容 shim：旧路径 AIPLPhMTools.SOITools.Assembly -> AIPLPhMTools.Platforms.SOI.Assembly。"""
from importlib import import_module as _import_module
_impl = _import_module("AIPLPhMTools.Platforms.SOI.Assembly")
for _k, _v in vars(_impl).items():
    if not _k.startswith("_"):
        globals()[_k] = _v
del _import_module, _impl
