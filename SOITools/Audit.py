"""兼容 shim：旧路径 AIPLPhMTools.SOITools.Audit -> AIPLPhMTools.Platforms.SOI.Audit。"""
from importlib import import_module as _import_module
_impl = _import_module("AIPLPhMTools.Platforms.SOI.Audit")
for _k, _v in vars(_impl).items():
    if not _k.startswith("_"):
        globals()[_k] = _v
del _import_module, _impl
