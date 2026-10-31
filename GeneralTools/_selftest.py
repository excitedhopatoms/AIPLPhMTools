"""GeneralTools 全组件自检。

运行（在包含 AIPLPhMTools 的目录下）::

    python -m AIPLPhMTools.GeneralTools._selftest

检查内容
--------
1. 包入口：``list_components()`` / ``get_component()`` 可用，器件不重名；
2. 逐个用默认参数构建全部公共器件：返回 Component、bbox 有限、有端口；
3. 关键行为：加热器各类型、ViaArray、GSGELE 焊盘、CSV 缺失时报错清晰；
4. 几何抽查：DBR 周期长度、Crossing_taper 四端口朝向、TaperRsoa 端口。

不依赖任何 PDK 宏 GDS；CSV 驱动的 DBR 不在默认测试范围内。
"""
from __future__ import annotations

import math

import gdsfactory as gf

import AIPLPhMTools as ap


# 需要外部 CSV，默认不构建（否则在没有数据文件的机器上必失败）
_CSV_COMPONENTS = {
    "DBRFromCsv", "DBRFromCsvOffset", "SGDBRFromCsvOffset",
    "VSGDBRFromCsvOffset", "EstrDBRFromCsvOffset", "EDBRFromCsv",
}


def _check_component(name: str, factory) -> tuple[bool, str]:
    try:
        c = factory()
    except Exception as exc:  # noqa: BLE001 - 自检要把异常汇总成报告
        return False, f"{type(exc).__name__}: {exc}"

    if c is None:
        return False, "返回 None"
    if not hasattr(c, "bbox"):
        return False, f"返回类型 {type(c).__name__}，不是 Component"

    bb = c.bbox()
    if not all(math.isfinite(v) for v in (bb.left, bb.bottom, bb.right, bb.top)):
        return False, f"bbox 非有限: {bb}"
    if bb.right - bb.left <= 0 or bb.top - bb.bottom <= 0:
        return False, f"bbox 为空: {bb}"

    ports = list(c.ports)
    if not ports:
        return False, "没有端口"
    for p in ports:
        if p.width <= 0:
            return False, f"端口 {p.name} 宽度 <= 0"
        if not math.isfinite(p.orientation):
            return False, f"端口 {p.name} 方向非有限"

    if not c.layers:
        return False, "没有任何图层图形"
    return True, f"{len(ports)} ports, bbox=({bb.left:.1f},{bb.bottom:.1f},{bb.right:.1f},{bb.top:.1f})"


def main() -> int:
    ok = True

    def chk(name: str, cond: bool, detail: str = "") -> None:
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
        ok = ok and bool(cond)

    # 1. 包入口 ---------------------------------------------------------
    names = ap.list_components()
    chk("list_components() 非空", len(names) > 50, f"{len(names)} 个")
    chk("器件名唯一", len(names) == len(set(names)))
    for core in ("RingPulleyT1", "RaceTrackP", "DMZI", "DBR", "GSGELE",
                 "GfCStraight", "TCRing", "Boomerang"):
        chk(f"注册表包含 {core}", core in ap.COMPONENTS)
    try:
        ap.get_component("不存在的器件")
        chk("get_component 对未知名字报错", False)
    except KeyError:
        chk("get_component 对未知名字报错", True)

    # 2. 全量构建 -------------------------------------------------------
    failed = []
    for name in names:
        if name in _CSV_COMPONENTS:
            continue
        passed, detail = _check_component(name, ap.get_component(name))
        print(("PASS " if passed else "FAIL ") + f"build {name:30s}" + (f"  [{detail}]" if detail else ""))
        if not passed:
            failed.append((name, detail))
    chk("全部公共器件可构建", not failed, f"{len(failed)} 个失败")

    # 3. 关键行为 -------------------------------------------------------
    path = gf.path.straight(length=200)
    for heater_type in ("default", "side", "bothside", "multi", "spilt", "none"):
        try:
            cfg = ap.HeaterConfigClass(
                TypeHeater=heater_type,
                WidthHeat=(4, 4) if heater_type == "multi" else 4,
                DeltaHeat=(3, 3) if heater_type == "multi" else 10,
            )
            h = ap.DifferentHeater(PathHeat=path, HeaterConfig=cfg)
            chk(f"DifferentHeater[{heater_type}]", True, f"{len(h.ports)} ports")
        except Exception as exc:  # noqa: BLE001
            chk(f"DifferentHeater[{heater_type}]", False, f"{type(exc).__name__}: {exc}")

    try:
        src = gf.Component("via_src")
        src.add_ref(gf.c.rectangle(size=(100, 50), layer=ap.LAYER.M1, centered=True))
        via = ap.ViaArray(src, arraylayer=ap.LAYER.M1)
        chk("ViaArray 在 M1 区域内布孔", len(via.insts) > 100, f"{len(via.insts)} 孔")
    except Exception as exc:  # noqa: BLE001
        chk("ViaArray 在 M1 区域内布孔", False, f"{type(exc).__name__}: {exc}")

    try:
        gsg = ap.GSGELE(LengthEle=200, Is2Pad=True, LengthToPad=50, PitchPad=100)
        pad_names = {p.name for p in gsg.ports if p.name.startswith("Pad_")}
        chk("GSGELE 两端焊盘共 6 个对外端口", len(pad_names) == 6, ",".join(sorted(pad_names)))
        # 焊盘外侧 x 应分别落在 -115 与 +315（LengthEle=200, LengthToPad=50, pad=65）
        chk("GSGELE 焊盘位置正确",
            abs(gsg.ports["Pad_R_S"].center[0] - 315) < 1e-6
            and abs(gsg.ports["Pad_L_S"].center[0] + 115) < 1e-6)
    except Exception as exc:  # noqa: BLE001
        chk("GSGELE 两端焊盘", False, f"{type(exc).__name__}: {exc}")

    # CSV 缺失必须给可操作的报错，而不是崩在某个 D: 盘路径上
    try:
        ap.DBRFromCsvOffset()
        chk("DBR CSV 缺失时报错", False)
    except FileNotFoundError as exc:
        chk("DBR CSV 缺失时报错", "AIPL_DBR_CSV_DIR" in str(exc))

    # 4. 几何抽查 -------------------------------------------------------
    dbr = ap.DBR(Length1=0.4, Length2=0.5, Period=10)
    chk("DBR(Period=10) 长度 = 9 um", abs((dbr.bbox().right - dbr.bbox().left) - 9.0) < 1e-6,
        f"{dbr.bbox().right - dbr.bbox().left:.4f}")

    cross = ap.Crossing_taper()
    orientations = sorted(round(p.orientation) % 360 for p in cross.ports)
    chk("Crossing_taper 四臂朝外", orientations == [0, 90, 180, 270], str(orientations))

    rsoa = ap.TaperRsoa()
    chk("TaperRsoa 两个端口", len(rsoa.ports) == 2)
    chk("TaperRsoa o1 宽度 = WidthRsoa", abs(rsoa.ports["o1"].width - 8) < 1e-6)

    print("\nSELFTEST " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
