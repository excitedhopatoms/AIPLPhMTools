"""TC 测试结构同层波导重叠审计。

用法（在包含 AIPLPhMTools 的工程根目录）::

    python AIPLPhMTools/examples/tc_overlap_audit.py
    python AIPLPhMTools/examples/tc_overlap_audit.py --layer 1 0 --tol 0.01

判定方法
--------
对每个 cell 的直接子 instance 计算同层 WG Region，并两两求交：

* butt joint 只共享一条边，交叠面积为 0；
* 面积 > ``--tol``（默认 0.01 µm²）视为需要人工确认的重叠；
* 同时支持普通 Component 和 ComponentAllAngle（vinsts）。

说明：Boomerang 系列在共享端口处存在大块同层交叠，可能是“共用一段
波导”的设计意图；脚本只报告几何事实，不判断拓扑是否允许。
"""
from __future__ import annotations

import argparse

import AIPLPhMTools as ap
from kfactory import kdb
from gdsfactory.component import ComponentAllAngle


def _audit_normal(component, layer, tol):
    layer_index = component.kcl.layer(*layer)
    dbu = component.kcl.dbu
    seen = set()
    findings = []

    def walk(cell):
        cell_index = cell.kdb_cell.cell_index()
        if cell_index in seen:
            return
        seen.add(cell_index)
        insts = list(cell.insts)
        regions = []
        for inst in insts:
            trans = kdb.ICplxTrans.from_dtrans(inst.dcplx_trans, dbu)
            regions.append(
                kdb.Region(inst.cell.kdb_cell.begin_shapes_rec(layer_index)).transformed(trans)
            )
        for i in range(len(insts)):
            for j in range(i + 1, len(insts)):
                inter = regions[i] & regions[j]
                area = inter.area() * dbu ** 2
                if area > tol:
                    bb = inter.bbox()
                    findings.append({
                        "cell": cell.name,
                        "a": insts[i].cell.name,
                        "b": insts[j].cell.name,
                        "area": area,
                        "bbox": (bb.left * dbu, bb.bottom * dbu,
                                 bb.right * dbu, bb.top * dbu),
                    })
        for inst in insts:
            walk(inst.cell)

    walk(component)
    return findings


def _audit_all_angle(component, layer, tol):
    layer_index = component.kcl.layer(*layer)
    dbu = component.kcl.dbu
    vinsts = list(component.vinsts)
    regions = [
        kdb.Region(v.cell.kdb_cell.begin_shapes_rec(layer_index)).transformed(
            kdb.ICplxTrans.from_dtrans(v.dcplx_trans, dbu)
        )
        for v in vinsts
    ]
    findings = []
    for i in range(len(regions)):
        for j in range(i + 1, len(regions)):
            inter = regions[i] & regions[j]
            area = inter.area() * dbu ** 2
            if area > tol:
                bb = inter.bbox()
                findings.append({
                    "cell": component.name,
                    "a": vinsts[i].cell.name,
                    "b": vinsts[j].cell.name,
                    "area": area,
                    "bbox": (bb.left * dbu, bb.bottom * dbu,
                             bb.right * dbu, bb.top * dbu),
                })
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer", nargs=2, type=int, default=(1, 0))
    parser.add_argument("--tol", type=float, default=0.01,
                        help="面积阈值，单位 um^2，默认 0.01")
    args = parser.parse_args(argv)
    layer = tuple(args.layer)

    total = 0
    for name in [n for n in ap.list_components() if n.startswith("TC")]:
        component = ap.get_component(name)()
        if isinstance(component, ComponentAllAngle):
            findings = _audit_all_angle(component, layer, args.tol)
        else:
            findings = _audit_normal(component, layer, args.tol)
        total += len(findings)
        if findings:
            print(f"{name}: {len(findings)} 处")
            for item in findings:
                print(
                    f"   area={item['area']:.3f} um^2  "
                    f"{item['a']}  <->  {item['b']}  "
                    f"bbox={tuple(round(v, 3) for v in item['bbox'])}"
                )
    print(f"\n总计: {total} 处（阈值 {args.tol} um^2）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
