"""兼容 shim：旧路径 AIPLPhMTools.SOITools.Electrical -> AIPLPhMTools.Platforms.SOI.Electrical。"""
from importlib import import_module as _import_module
_impl = _import_module("AIPLPhMTools.Platforms.SOI.Electrical")
for _k, _v in vars(_impl).items():
    if not _k.startswith("_"):
        globals()[_k] = _v
del _import_module, _impl
