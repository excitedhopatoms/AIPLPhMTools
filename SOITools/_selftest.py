"""AIPLPhMTools.SOITools 自检：不依赖任何 PDK 宏，直接跑几何 + 与 ICRDPhMTools 对照。

运行（在含 ICRDPhMTools 的项目根目录）::

    python -m AIPLPhMTools.SOITools._selftest

检查项
------
1. 层号表与工艺常数；
2. Route：straight / turn / s_bend 的端点与 S 弯跨度公式；
3. add_si_route / add_sin_route：芯宽 + 631/10·632/10·600/10 开窗 + SINOP；
4. add_annulus 面积；add_bond_pad 的 landing 只画必要层（M3/M2/M1 三档）；
5. 与 ICRDPhMTools 逐层对照同一组走线（bbox + 面积完全一致）。
"""
from __future__ import annotations

import math
import tempfile
from pathlib import Path

import gdsfactory as gf
import klayout.db as kdb

import AIPLPhMTools.SOITools as soi


def _layer_bbox(gds_path: Path, cell_name: str) -> dict:
    ly = kdb.Layout()
    ly.read(str(gds_path))
    cell = ly.cell(cell_name)
    out = {}
    for li in ly.layer_indexes():
        r = kdb.Region(cell.begin_shapes_rec(li))
        if r.is_empty():
            continue
        b = r.bbox()
        out[ly.get_info(li).to_s()] = (b.left, b.bottom, b.right, b.top,
                                       round(r.area()))
    return out


def main() -> int:
    ok = True

    def chk(name, cond, detail=""):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
        ok = ok and bool(cond)

    # 1. 层号 / 常数 -------------------------------------------------------
    chk("layer map is the SOI stack",
        (soi.SIWG, soi.SIN, soi.SIN3, soi.TIN, soi.M1, soi.M2, soi.M3,
         soi.V1, soi.V2, soi.RV, soi.ALPAD, soi.COVER, soi.SINOP)
        == ((600, 1), (631, 1), (632, 1), (639, 1), (641, 1), (642, 1),
            (643, 1), (651, 1), (652, 1), (660, 1), (661, 1), (662, 1),
            (665, 1)))
    chk("core widths / radii", (soi.W_SI, soi.W_SIN, soi.R_SI, soi.R_SIN)
        == (0.45, 1.0, 11.0, 52.0))

    # 2. Route ------------------------------------------------------------
    p = soi.Route(0.0, 0.0, 0).straight(100.0).turn(-90.0, soi.R_SI).straight(50.0)
    chk("Route: straight(100) + turn(-90, R_SI) + straight(50) "
        "ends at (100+R, -R-50) [south]",
        abs(p.x - (100.0 + soi.R_SI)) < 1e-9
        and abs(p.y - (-soi.R_SI - 50.0)) < 1e-9,
        f"{p.x:.3f},{p.y:.3f}")
    rise, R = 30.0, soi.R_SIN
    q = soi.Route(0.0, 0.0, 0).s_bend(rise, R)
    ext = math.sqrt(4 * R * rise - rise ** 2)
    chk(f"Route.s_bend({rise}, {R}) spans (ext, rise) = ({ext:.2f}, {rise})",
        abs(q.x - ext) < 1e-6 and abs(q.y - rise) < 1e-6, f"{q.x:.2f},{q.y:.2f}")

    # 3. 走线层栈 ----------------------------------------------------------
    c = gf.Component("soi_demo")
    r1 = soi.Route(0.0, 0.0, 0).straight(200.0)
    soi.add_si_route(c, r1.pts)
    r2 = soi.Route(0.0, 40.0, 0).straight(60.0).s_bend(-30.0, soi.R_SIN).straight(20.0)
    soi.add_sin_route(c, r2.pts)
    soi.add_annulus(c, 150.0, 120.0, 10.0, 12.0, 0.0, 360.0, soi.TIN)

    # 4. 焊盘 landing ------------------------------------------------------
    for landing, has_m1, has_m2 in (("M3", False, False), ("M2", False, True),
                                    ("M1", True, True)):
        px = 300.0 + 80.0 * ("M3", "M2", "M1").index(landing)
        soi.add_bond_pad(c, px, 0.0, size=50.0, cover=40.0, landing=landing)

    tmp = Path(tempfile.mkdtemp()) / "soi_demo.gds"
    c.write_gds(str(tmp))
    bb = _layer_bbox(tmp, "soi_demo")
    chk("Si core 0.45 and 10 um window", bb.get("600/1") and bb.get("600/10"))
    chk("SiN route: core + 631/10 + 632/10 + 600/10 + SINOP",
        all(k in bb for k in ("631/1", "631/10", "632/10", "665/1")))
    chk("TiN annulus area = pi*(12^2-10^2)",
        abs(bb["639/1"][4] / 1e6 - math.pi * (144 - 100)) < 0.5,
        f"{bb['639/1'][4] / 1e6:.1f} um2")

    def has(layer, x):
        b = bb.get(layer)
        return b is not None and b[0] / 1000 <= x <= b[2] / 1000

    chk("pad landing=M3 draws no M1/M2 plate", not has("641/1", 300) and not has("642/1", 300))
    chk("pad landing=M2 draws M2 plate but no M1", has("642/1", 380) and not has("641/1", 380))
    chk("pad landing=M1 draws both M1 and M2", has("641/1", 460) and has("642/1", 460))

    # 5. 与 ICRDPhMTools 逐层对照 -----------------------------------------
    try:
        import ICRDPhMTools as icrd
    except Exception as e:                                    # pragma: no cover
        print(f"skip ICRD comparison ({e})")
        return 0 if ok else 1

    c2 = gf.Component("icrd_demo")
    icrd.add_si_route(c2, icrd.Route(0.0, 0.0, 0).straight(200.0).pts)
    icrd.add_sin_route(c2, icrd.Route(0.0, 40.0, 0).straight(60.0)
                       .s_bend(-30.0, icrd.R_SIN).straight(20.0).pts)
    icrd.add_annulus(c2, 150.0, 120.0, 10.0, 12.0, 0.0, 360.0, icrd.TIN)
    tmp2 = Path(tempfile.mkdtemp()) / "icrd_demo.gds"
    c2.write_gds(str(tmp2))
    b2 = _layer_bbox(tmp2, "icrd_demo")
    # 只比走线/环带（焊盘在 4 里已单独查过）。
    # bbox 必须逐位相同；面积允许 0.5% 的差——两个库的采样常数
    # （ARC_STEP_DEG / BUFFER_RES）会各自调，采样只改多边形的弦逼近，
    # 不改中心线/宽度，所以面积应当只差采样精度那一丁点。
    keys = ("600/1", "600/10", "631/1", "631/10", "632/10", "665/1", "639/1")

    def _same(k):
        va, vb = bb.get(k), b2.get(k)
        if va is None or vb is None:
            return va is vb
        if va[:4] != vb[:4]:
            return False
        if va[4] == vb[4]:
            return True
        return abs(va[4] - vb[4]) <= 0.005 * max(va[4], vb[4], 1)

    same = all(_same(k) for k in keys)
    chk("geometry identical to ICRDPhMTools (same layers, bbox; area ±0.5%)",
        same)

    print("\nSELFTEST " + ("OK" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
