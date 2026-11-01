"""层叠对象：把设计手册里的“名称 -> (layer, datatype)”读成统一的 LayerStack。

设计手册可以是一份 Markdown 表格，也可以是一段 YAML/JSON::

    | 名称 | layer/datatype | 角色 | 显示厚度 |
    |------|----------------|------|----------|
    | WG   | 1/0            | 波导 | 1.0      |
    | M1   | 10/0           | 加热 | 1.0      |

::

    layers:
      WG:  {layer: 1,  datatype: 0, role: optical, display_thickness: 1.0}
      M1:  {layer: 10, datatype: 0, role: heater,  display_thickness: 1.0}

``LayerStack`` 只是**层号/角色/显示厚度**的统一容器；它不绑定任何具体工艺，
厚度只用于 3D/文档显示。器件函数可以逐步改为接收 ``stack``，而不是分别传
``oplayer`` / ``heatlayer`` / ``elelayer``。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .BasicDefine import LAYER


@dataclass(frozen=True)
class LayerDef:
    """单层定义。``name`` 是设计手册中的名字，``key`` 是 GDS 的 (layer, datatype)。"""

    name: str
    layer: int
    datatype: int = 0
    role: str = ""
    display_thickness: float = 1.0

    @property
    def key(self) -> tuple[int, int]:
        return self.layer, self.datatype

    def __iter__(self):
        """兼容 ``for layer, datatype in layer_def``。"""
        yield self.layer
        yield self.datatype


@dataclass(frozen=True)
class LayerStack:
    """一组层定义；可通过 ``stack.WG`` 或 ``stack.get("WG")`` 访问。"""

    layers: tuple[LayerDef, ...]

    def __post_init__(self):
        names = [l.name for l in self.layers]
        if len(names) != len(set(names)):
            raise ValueError(f"LayerStack 名称重复: {names}")

    @property
    def by_name(self) -> dict[str, LayerDef]:
        return {l.name: l for l in self.layers}

    def __getattr__(self, name: str) -> LayerDef:
        # dataclass 内部属性不要拦截
        if name.startswith("__"):
            raise AttributeError(name)
        try:
            return self.by_name[name]
        except KeyError:
            raise AttributeError(f"LayerStack 没有层 {name!r}") from None

    def __iter__(self):
        return iter(self.layers)

    def get(self, name_or_key: str | tuple[int, int]) -> LayerDef:
        if isinstance(name_or_key, tuple):
            for l in self.layers:
                if l.key == name_or_key:
                    return l
            raise KeyError(f"LayerStack 没有 key {name_or_key!r}")
        return self.by_name[name_or_key]

    def names(self) -> list[str]:
        return [l.name for l in self.layers]

    def keys(self) -> list[tuple[int, int]]:
        return [l.key for l in self.layers]

    def to_dict(self) -> dict[str, dict[str, Any]]:
        return {
            l.name: {
                "layer": l.layer,
                "datatype": l.datatype,
                "role": l.role,
                "display_thickness": l.display_thickness,
            }
            for l in self.layers
        }

    # ------------------------------------------------------------------
    # 构造
    # ------------------------------------------------------------------
    @classmethod
    def from_mapping(cls, mapping: dict[str, Any]) -> "LayerStack":
        """从 ``{name: (layer, datatype)}`` 或 ``{name: {...}}`` 构造。"""
        out = []
        for name, value in mapping.items():
            if isinstance(value, dict):
                out.append(LayerDef(
                    name=str(name),
                    layer=int(value.get("layer", value.get("layer_num", 0))),
                    datatype=int(value.get("datatype", 0)),
                    role=str(value.get("role", "")),
                    display_thickness=float(value.get("display_thickness", 1.0)),
                ))
            else:
                layer, datatype = _parse_layer_value(value)
                out.append(LayerDef(str(name), layer, datatype))
        return cls(tuple(out))

    @classmethod
    def from_design_manual(cls, path: str | Path, section: str | None = None) -> "LayerStack":
        """从设计手册读取 LayerStack。

        支持:

        * Markdown 表格：``| 名称 | 1/0 | ... |`` 或 ``| 名称 | (1, 0) | ... |``；
        * YAML / JSON：顶层 ``layers: {WG: {layer: 1, datatype: 0}}``。

        参数:
            path: 设计手册路径。
            section: 可选，只扫描该 section 标题（例如 ``"层号"``）之后的表格。
        """
        p = Path(path)
        text = p.read_text(encoding="utf-8")
        suffix = p.suffix.lower()
        if suffix in (".yaml", ".yml", ".json"):
            if suffix == ".json":
                data = json.loads(text)
            else:
                try:
                    import yaml
                except ImportError as exc:  # pragma: no cover
                    raise RuntimeError("读取 YAML 需要 PyYAML") from exc
                data = yaml.safe_load(text)
            if isinstance(data, dict) and "layers" in data:
                data = data["layers"]
            if not isinstance(data, dict):
                raise ValueError("YAML/JSON 里需要 layers: {name: {layer, datatype}}")
            return cls.from_mapping(data)

        if section:
            idx = text.find(section)
            if idx == -1:
                raise ValueError(f"设计手册中没有 section {section!r}")
            text = text[idx:]

        rows = _parse_markdown_tables(text)
        if not rows:
            raise ValueError(
                f"{p} 中没有找到可识别的层表；需要形如 "
                "'| 名称 | 1/0 | 角色 | 显示厚度 |' 的行"
            )
        return cls(tuple(rows))

    @classmethod
    def default(cls) -> "LayerStack":
        """按 BasicDefine.LAYER 的常用层生成默认对象（不写工艺厚度）。"""
        names_roles = (
            ("WG", "optical"),
            ("CPF", "sin"),
            ("TN", "doping_n"),
            ("TP", "doping_p"),
            ("M1", "metal"),
            ("VIA", "via"),
            ("M2", "metal2"),
            ("V2", "via2"),
            ("OPEN", "open"),
            ("DT", "trench"),
        )
        layers = []
        for name, role in names_roles:
            if not hasattr(LAYER, name):
                continue
            value = getattr(LAYER, name)
            try:
                import gdsfactory as gf
                layer, datatype = gf.get_layer_tuple(value)
            except Exception:
                layer, datatype = int(getattr(value, "value", value)), 0
            layers.append(LayerDef(name, int(layer), int(datatype), role))
        return cls(tuple(layers))


def _parse_layer_value(value: Any) -> tuple[int, int]:
    if isinstance(value, (tuple, list)) and len(value) == 2:
        return int(value[0]), int(value[1])
    if isinstance(value, str):
        m = re.search(r"(\d+)\s*/\s*(\d+)", value)
        if m:
            return int(m.group(1)), int(m.group(2))
        m = re.search(r"(\d+)\s*,\s*(\d+)", value)
        if m:
            return int(m.group(1)), int(m.group(2))
    if isinstance(value, int):
        return value, 0
    raise ValueError(f"无法解析层号: {value!r}")


def _parse_markdown_tables(text: str) -> list[LayerDef]:
    """扫描 Markdown 表格，取“名称 + layer/datatype”行。"""
    out: list[LayerDef] = []
    seen = set()
    for line in text.splitlines():
        if "|" not in line:
            continue
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        name = cells[0].strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            continue
        key = None
        role = ""
        thickness = 1.0
        for cell in cells[1:]:
            if key is None:
                try:
                    key = _parse_layer_value(cell)
                    continue
                except ValueError:
                    pass
            # 可选：role / display thickness
            if re.fullmatch(r"\d+(\.\d+)?", cell):
                thickness = float(cell)
            elif cell and not role and not re.fullmatch(r"[-\s]+", cell):
                role = cell
        if key is None or name in seen:
            continue
        seen.add(name)
        out.append(LayerDef(name, key[0], key[1], role, thickness))
    return out


__all__ = ["LayerDef", "LayerStack"]
