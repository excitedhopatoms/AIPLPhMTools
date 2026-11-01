"""基于端口连通性的 LVS（Layout vs Schematic）检查。

核心思想
--------
把版图按层合并成若干**连通多边形**，再把“原理图”给出的端子放到版图上：

* 同一个 net 的所有端子必须落在**同一个**连通多边形里（否则报 open）；
* 不同 net 的端子不能落在同一个连通多边形里（否则报 short）；
* 每个端子必须落在它声明的图层上（否则报 missing / wrong layer）。

不关心器件内部有多少个环、多少段波导；这些属于版图内容，不参与 netlist 比较。
可选的 ``required_cells`` 检查 GDS 里是否存在指定 cell 名，用于确认器件确实被例化。

两种用法
--------
1. **直接检查 Python 器件**（端子坐标自动从 Component.ports 读取）::

       python -m AIPLPhMTools.lvs --component CoupledRingFilter \\
           --spec AIPLPhMTools/examples/lvs_coupled_filter.yaml

2. **检查已有 GDS**（端子在 spec 的 ``ports`` 里给出坐标）::

       python -m AIPLPhMTools.lvs --gds chip.gds --spec chip_lvs.yaml

spec 格式（YAML / JSON）
------------------------
::

    # 可选：图层名 -> (layer, datatype)
    layers:
      WG: [1, 0]
      M1: [10, 0]

    # 仅 --gds 模式需要：端子名 -> 坐标 / 图层
    ports:
      Input:   {layer: WG, xy: [-130, 0]}
      Through: {layer: WG, xy: [130, 0]}
      Add:     {layer: WG, xy: [-130, 403.7]}
      Drop:    {layer: WG, xy: [130, 403.7]}

    # 期望的 net：同一 net 的端子必须连通
    nets:
      bottom_bus:
        layer: WG
        ports: [Input, Through]
      top_bus:
        layer: WG
        ports: [Add, Drop]

    # 可选
    min_width: 0.4                 # 每个端子处的线宽下限
    required_cells: [CoupledRingFilter]  # GDS 里必须存在的 cell 名（子串匹配）
    allow_extra_nets: true         # 允许未声明 net 的连通块（器件内部图形）

退出码
------
0 = 全部通过；1 = 有 FAIL。

注意
----
这是**连通性 LVS**，不是针对有源/无源器件参数的完整 LVS；它验证的是
“端子有没有接对、有没有开路/短路、有没有画错层”，不验证器件模型参数。
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import klayout.db as kdb
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import AIPLPhMTools as ap


# ---------------------------------------------------------------------------
# 数据结构
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Terminal:
    name: str
    layer: tuple[int, int]
    xy: tuple[float, float]


# ---------------------------------------------------------------------------
# spec 读取
# ---------------------------------------------------------------------------
def _parse_layer(value: Any, layer_map: dict[str, tuple[int, int]]) -> tuple[int, int]:
    """把 ``"WG"`` / ``"1/0"`` / ``[1, 0]`` / ``1`` 解析成 (layer, datatype)。"""
    if isinstance(value, (tuple, list)):
        if len(value) != 2:
            raise ValueError(f"图层必须是 (layer, datatype)，收到 {value!r}")
        return int(value[0]), int(value[1])
    if isinstance(value, int):
        return value, 0
    if isinstance(value, str):
        s = value.strip()
        if s in layer_map:
            return layer_map[s]
        if "/" in s:
            a, b = s.split("/", 1)
            return int(a), int(b)
        # 名称回退：AIPLPhMTools.LAYER（GeneralTools 的层表）
        if hasattr(ap.LAYER, s):
            layer = getattr(ap.LAYER, s)
            return int(getattr(layer, "layer", layer)), int(getattr(layer, "datatype", 0))
    raise ValueError(f"无法解析图层 {value!r}")


def load_spec(path: str | Path) -> dict:
    """读取 YAML 或 JSON spec。"""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        return json.loads(text)
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("读取 YAML 需要 PyYAML；或改用 .json spec") from exc
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("spec 顶层必须是 mapping")
    return data


def _terminal_from_port_dict(name: str, value: Any,
                             layer_map: dict[str, tuple[int, int]]) -> Terminal:
    if not isinstance(value, dict):
        raise ValueError(f"端口 {name} 必须是 {{layer, xy}}，收到 {value!r}")
    layer = _parse_layer(value.get("layer", "WG"), layer_map)
    xy = value.get("xy", value.get("center"))
    if not xy or len(xy) != 2:
        raise ValueError(f"端口 {name} 缺少 xy 坐标")
    return Terminal(name, layer, (float(xy[0]), float(xy[1])))


def _spec_nets(spec: dict, layer_map: dict[str, tuple[int, int]]) -> list[tuple[str, tuple[str, ...], tuple[int, int] | None]]:
    raw = spec.get("nets")
    if not raw:
        raise ValueError("spec 缺少 nets")
    out = []
    for name, value in raw.items():
        if isinstance(value, (list, tuple)):
            ports = tuple(str(p) for p in value)
            layer = None
        elif isinstance(value, dict):
            ports = tuple(str(p) for p in value.get("ports", ()))
            layer = value.get("layer")
        else:
            raise ValueError(f"net {name} 的格式不对：{value!r}")
        if not ports:
            raise ValueError(f"net {name} 没有端口")
        out.append((str(name), ports, layer))
    # 图层未知时由端子推断；这里先用占位 (0,0)，随后修正
    result = []
    for name, ports, layer in out:
        result.append((name, ports, _parse_layer(layer, layer_map) if layer is not None else None))
    return result


# ---------------------------------------------------------------------------
# 版图几何
# ---------------------------------------------------------------------------
def polygon_of(poly) -> Polygon:
    """KLayout 多边形 -> shapely Polygon（µm），保留孔洞。"""
    hull = [(p.x / 1000.0, p.y / 1000.0) for p in poly.each_point_hull()]
    holes = [[(p.x / 1000.0, p.y / 1000.0) for p in poly.each_point_hole(i)]
             for i in range(poly.holes())]
    return Polygon(hull, holes)


def split_nets(geom) -> list[Polygon]:
    """MultiPolygon / GeometryCollection -> 互相独立的 Polygon 列表。"""
    if geom.is_empty:
        return []
    if geom.geom_type == "Polygon":
        return [geom]
    return [g for g in getattr(geom, "geoms", []) if g.geom_type == "Polygon"]


def read_geometry(gds_path: str) -> tuple[dict[tuple[int, int], list[Polygon]], dict[str, Any]]:
    """读 GDS，返回每层的连通块和统计量。"""
    ly = kdb.Layout()
    ly.read(gds_path)
    cell = ly.top_cell()
    if cell is None:
        raise ValueError(f"GDS 没有 top cell: {gds_path}")

    layers: dict[tuple[int, int], list[Polygon]] = {}
    stats: dict[str, Any] = {}
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        key = (info.layer, info.datatype)
        region = kdb.Region(cell.begin_shapes_rec(li)).merged()
        if region.is_empty():
            continue
        polys = [polygon_of(p) for p in region.each()]
        if not polys:
            continue
        merged = unary_union(polys)
        nets = split_nets(merged)
        layers[key] = nets
        b = merged.bounds
        stats[f"{key[0]}/{key[1]}"] = {
            "polygons": len(polys),
            "nets": len(nets),
            "area": round(float(merged.area), 6),
            "bbox": [round(float(v), 6) for v in b],
        }
    cell_names = [c.name for c in ly.each_cell()]
    stats["_cells"] = cell_names
    return layers, stats


def net_index(nets: list[Polygon], xy: tuple[float, float]) -> int | None:
    """返回包含该点的连通块下标；点在边界上也算。"""
    p = Point(xy)
    for i, g in enumerate(nets):
        if g.covers(p) or g.distance(p) < 1e-3:
            return i
    return None


def _width_at(nets: list[Polygon], xy: tuple[float, float], half: float) -> float:
    """在端子附近取水平/竖直截线的较小非零宽度。

    对沿 x 或 y 的波导端口，一个截线沿传播方向、一个截线横跨波导；
    取较小值才近似真实线宽（取 max 会把端口外的长度也算进去）。
    """
    from shapely.geometry import LineString
    x, y = xy
    widths = []
    for line in (
        LineString([(x - half, y), (x + half, y)]),
        LineString([(x, y - half), (x, y + half)]),
    ):
        w = 0.0
        for g in nets:
            inter = g.intersection(line)
            if inter.is_empty:
                continue
            for part in getattr(inter, "geoms", [inter]):
                w = max(w, float(getattr(part, "length", 0)))
        if w > 1e-9:
            widths.append(w)
    return min(widths) if widths else 0.0


# ---------------------------------------------------------------------------
# 检查
# ---------------------------------------------------------------------------
def run_lvs(
        gds: str,
        spec: dict,
        terminals: dict[str, Terminal],
        *,
        reference: str | None = None,
        reference_tol: float = 1e-3,
) -> dict:
    layer_map = {str(k): _parse_layer(v, {}) for k, v in (spec.get("layers") or {}).items()}
    nets_raw = _spec_nets(spec, layer_map)
    allow_extra = bool(spec.get("allow_extra_nets", True))
    min_width = spec.get("min_width")

    geometry, layer_stats = read_geometry(gds)
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})
        print(("  PASS  " if ok else "  FAIL  ") + name + (f"  [{detail}]" if detail else ""))

    # 1) 只检查 netlist 真正引用的端子；器件上的 RingC 等参考端口不参与 LVS
    used_terminals = {p for _, ports, _ in nets_raw for p in ports}
    port_net: dict[str, int] = {}
    port_layer: dict[str, tuple[int, int]] = {}
    for name, term in terminals.items():
        if name not in used_terminals:
            continue
        layers = geometry.get(term.layer)
        if not layers:
            add(f"terminal {name} on layer {term.layer}", False, "该层没有多边形")
            continue
        idx = net_index(layers, term.xy)
        if idx is None:
            add(f"terminal {name} on layer {term.layer}", False,
                f"坐标 {term.xy} 不在任何多边形上")
            continue
        add(f"terminal {name} on layer {term.layer}", True, f"net #{idx}")
        port_net[name] = idx
        port_layer[name] = term.layer

    # 2) 每个 net 的所有端子在同一个连通块
    resolved_nets: list[tuple[str, tuple[int, int], int]] = []
    for name, ports, layer_hint in nets_raw:
        missing = [p for p in ports if p not in terminals]
        if missing:
            add(f"net {name}", False, f"缺少端子: {', '.join(missing)}")
            continue
        net_layers = {port_layer[p] for p in ports if p in port_layer}
        if len(net_layers) != 1:
            add(f"net {name}", False, f"端子跨层: {sorted(net_layers)}")
            continue
        layer = next(iter(net_layers))
        if layer_hint is not None and layer_hint != layer:
            add(f"net {name}", False, f"spec 声明层 {layer_hint} 与端子层 {layer} 不一致")
            continue
        indices = {port_net[p] for p in ports if p in port_net}
        if len(indices) != 1:
            add(f"net {name}", False,
                f"开路：端子位于不同连通块 {sorted(indices)}")
            continue
        idx = next(iter(indices))
        add(f"net {name}", True, f"{len(ports)} 个端子 / net #{idx} / layer {layer}")
        resolved_nets.append((name, layer, idx))

    # 3) 不同 net 不能落在同一连通块（短路）
    seen: dict[tuple[tuple[int, int], int], str] = {}
    for name, layer, idx in resolved_nets:
        key = (layer, idx)
        if key in seen and seen[key] != name:
            add(f"isolation {seen[key]} / {name}", False, f"同一连通块 {key}")
        else:
            add(f"isolation {name}", True, f"layer {layer} / net #{idx}")
            seen[key] = name

    # 4) 端子处线宽
    if min_width:
        for name, term in terminals.items():
            if name not in port_net:
                continue
            w = _width_at(geometry[term.layer], term.xy, max(1.0, float(min_width) * 3))
            add(f"width {name}", w >= float(min_width) - 1e-3,
                f"{w:.3f} µm >= {float(min_width):g}")

    # 5) required cells
    for req in spec.get("required_cells") or ():
        found = any(str(req) in name for name in layer_stats.get("_cells", []))
        add(f"cell {req}", found,
            "找到" if found else "GDS 中没有匹配的 cell 名")

    # 6) 未声明的连通块
    assigned = {(layer, idx) for _, layer, idx in resolved_nets}
    extras = []
    for layer, nets in geometry.items():
        for i, g in enumerate(nets):
            if g.area > 1e-9 and (layer, i) not in assigned:
                extras.append((layer, i, round(float(g.area), 3)))
    if extras:
        add("extra nets", allow_extra, f"{len(extras)} 个未声明连通块（允许={allow_extra}）")
    else:
        add("extra nets", True, "0")

    # 7) 可选：与参考 GDS 的层统计对比
    if reference:
        ref_layers, ref_stats = read_geometry(reference)
        keys = (set(layer_stats) | set(ref_stats)) - {"_cells"}
        for key in sorted(keys):
            a = layer_stats.get(key, {})
            b = ref_stats.get(key, {})
            if set(a) != set(b) or "area" not in a or "area" not in b:
                add(f"reference layer {key}", False, "只在一侧存在")
                continue
            da = abs(a["area"] - b["area"]) / max(abs(b["area"]), 1e-9)
            db = max(abs(x - y) for x, y in zip(a["bbox"], b["bbox"]))
            ok = da <= reference_tol and db <= reference_tol and a["nets"] == b["nets"]
            add(f"reference layer {key}", ok,
                f"area Δ={da:.2e}, bbox Δ={db:.2e}, nets {a['nets']}→{b['nets']}")

    ok = all(c["ok"] for c in checks)
    print("\n== LVS " + ("PASS" if ok else "FAIL") + " ==")
    if not ok:
        for c in checks:
            if not c["ok"]:
                print("  -", c["name"], c["detail"])
    return {
        "ok": ok,
        "gds": str(gds),
        "reference": str(reference) if reference else None,
        "nets": [{"name": n, "layer": list(l), "net": i} for n, l, i in resolved_nets],
        "terminals": {n: {"layer": list(t.layer), "xy": list(t.xy)}
                      for n, t in terminals.items()},
        "layers": layer_stats,
        "checks": checks,
    }


# ---------------------------------------------------------------------------
# 端子来源
# ---------------------------------------------------------------------------
def _layer_tuple(layer) -> tuple[int, int]:
    if isinstance(layer, (tuple, list)) and len(layer) == 2:
        return int(layer[0]), int(layer[1])
    # 端口 layer 可能是 LayerMap 的整数枚举值（如 47），不是 GDS 的 (10,0)；
    # 必须让 active PDK 解析成真实 (layer, datatype)。
    try:
        import gdsfactory as gf
        return tuple(int(v) for v in gf.get_layer_tuple(layer))
    except Exception:
        pass
    if hasattr(layer, "layer") and hasattr(layer, "datatype"):
        return int(layer.layer), int(layer.datatype)
    return 0, 0


def terminals_from_component(c) -> dict[str, Terminal]:
    out = {}
    for p in c.ports:
        out[p.name] = Terminal(p.name, _layer_tuple(p.layer),
                               (round(float(p.center[0]), 6),
                                round(float(p.center[1]), 6)))
    return out


def build_component(name: str, kwargs: dict) -> Any:
    factory = ap.get_component(name)
    return factory(**kwargs)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="AIPLPhMTools 连通性 LVS：netlist 端子 vs 版图连通块")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--gds", help="待检查 GDS")
    src.add_argument("--component", help="直接构建的器件名（ap.list_components()）")
    parser.add_argument("--kwargs", default="{}", help="--component 的构造参数 JSON")
    parser.add_argument("--spec", required=True, help="LVS spec（YAML/JSON）")
    parser.add_argument("--json", dest="json_out", help="报告输出 JSON 路径")
    parser.add_argument("--write-gds", help="--component 模式下把版图另存到该路径")
    parser.add_argument("--reference", help="可选：参考 GDS，做层面积/bbox/net 数回归")
    parser.add_argument("--reference-tol", type=float, default=1e-3,
                        help="参考对比的相对容差（默认 1e-3）")
    args = parser.parse_args(argv)

    spec = load_spec(args.spec)
    layer_map = {str(k): _parse_layer(v, {}) for k, v in (spec.get("layers") or {}).items()}

    tmp_path = None
    try:
        if args.component:
            kwargs = json.loads(args.kwargs or "{}")
            c = build_component(args.component, kwargs)
            terminals = terminals_from_component(c)
            if args.write_gds:
                gds = args.write_gds
                c.write_gds(gds)
            else:
                tmp = tempfile.NamedTemporaryFile(suffix=".gds", delete=False)
                tmp.close()
                gds = tmp.name
                tmp_path = gds
                c.write_gds(gds)
        else:
            gds = args.gds
            raw_ports = spec.get("ports")
            if not raw_ports:
                parser.error("--gds 模式需要在 spec 里提供 ports（端子坐标 + 图层）")
            terminals = {str(n): _terminal_from_port_dict(str(n), v, layer_map)
                         for n, v in raw_ports.items()}

        report = run_lvs(gds, spec, terminals, reference=args.reference,
                         reference_tol=args.reference_tol)
        if args.json_out:
            Path(args.json_out).write_text(
                json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0 if report["ok"] else 1
    finally:
        if tmp_path:
            try:
                Path(tmp_path).unlink()
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
