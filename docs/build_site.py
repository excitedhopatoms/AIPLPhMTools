#!/usr/bin/env python
"""生成 AIPLPhMTools 静态手册站点。

用法（在包含 ``AIPLPhMTools`` 的工程根目录下）::

    python AIPLPhMTools/docs/build_site.py

产物在 ``AIPLPhMTools/docs/``：

* ``index.html`` / ``guide.html`` / ``modules.html`` / ``gdsmerge.html`` /
  ``platforms_soi.html``
* ``components/<器件>.html``
* ``categories/<分类>.html``
* ``assets/img/``          每个器件的默认参数版图 PNG
* ``assets/img/variants/`` 参数对比 PNG
* ``assets/gds/``          默认参数 GDS（gzip 压缩，可下载）
* ``assets/platforms_soi/``     Platforms/SOI 子库演示图

图像不是示意图：脚本会真正调用器件函数、写出 GDS、再用 KLayout 合并同层
多边形、Matplotlib 填充渲染。所有尺寸/端口数据也都来自实际构建结果。
"""
from __future__ import annotations

import enum
import gzip
import html
import inspect
import json
import math
import re
import shutil
import sys
import tempfile
import textwrap
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
import klayout.db as kdb  # noqa: E402
import gdsfactory as gf  # noqa: E402

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
sys.path.insert(0, str(PKG.parent))

import AIPLPhMTools as ap  # noqa: E402

IMG = HERE / "assets" / "img"
IMG_V = IMG / "variants"
GDS_DIR = HERE / "assets" / "gds"
PLATFORMS_SOI_IMG = HERE / "assets" / "platforms_soi"

for _d in (IMG, IMG_V, GDS_DIR, PLATFORMS_SOI_IMG, HERE / "components", HERE / "categories"):
    _d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 分类
# ---------------------------------------------------------------------------
CATEGORIES = [
    ("basic", "基础图元", "直/弯波导、锥形、斜端面、交叉与延迟线", "GfCStraight"),
    ("rings", "环形谐振器", "Pulley 环、单/双/三环与 finger 环", "RingPulleyT1"),
    ("racetrack", "跑道环", "跑道腔、双跑道腔与锥形耦合入口", "RaceTrackP"),
    ("couplers", "耦合器与 MZI", "Pulley 2×2、DMZI、PMZI 与 Sagnac 环", "DMZI"),
    ("coupled", "耦合腔", "二阶耦合环滤波器、CROW 与 SCISSOR", "CoupledRingFilter"),
    ("dbr", "DBR 与反射器", "常规 DBR、E-DBR 与反相 E-DBR", "DBR"),
    ("heaters", "加热器与电极", "不同加热器、过孔阵列、焊盘与 GSG", "GSGELE"),
    ("boomerang", "回旋镖腔", "Boomerang 单元及其单/双/三环耦合", "Boomerang"),
    ("extcav", "外腔与激光器", "外腔、Memyshev 与隔离器", "ExtCavDouRing"),
    ("microcavity", "微腔", "工字形与王字形闭合微腔", "GongCavity"),
    ("test", "TC 测试结构", "环形 / 跑道 / 耦合腔测试结构", "TCRing"),
    ("tools", "工具", "QR 码等版图工具", "TWQRcode"),
]
CAT_NAME = {c[0]: c[1] for c in CATEGORIES}
CAT_DESC = {c[0]: c[2] for c in CATEGORIES}
CAT_ORDER = {c[0]: i for i, c in enumerate(CATEGORIES)}

# 与 AIPLPhMTools 重组后的目录一一对应（2026-11-03）。
# 网页的“模块层级”页、目录树和器件页的“模块”徽标都从这里取。
MODULE_TREE = [
    ("Core", "与具体工艺、具体器件无关的底座", [
        ("Core/BasicDefine.py", "层号接口、截面、直/弯/锥、Euler 路径、route_off_grid"),
        ("Core/EulerConnection.py", "任意角度端口的 Euler 连线"),
        ("Core/SnapMerge.py", "顶点吸附 / 同层合并（DRC 预处理）"),
        ("Core/LayerStack.py", "LayerDef / LayerStack（设计手册与 3D 视图）"),
        ("Core/GdsMerge.py", "GDS 原位合并：同名 PDK cell 指纹比对 / 复用 / 冲突报告"),
    ]),
    ("Devices", "单器件：返回带端口的 Component", [
        ("Devices/Ring.py", "Pulley 环及 T1/T2/1DC 等变体"),
        ("Devices/RaceTrack.py", "跑道腔（弯段/直段耦合）"),
        ("Devices/CouplerMZI.py", "2×2 耦合器、DMZI、PMZI、Sagnac"),
        ("Devices/CoupledCavity.py", "二阶耦合环、CROW、SCISSOR"),
        ("Devices/FeedbackCavity.py", "Add-Drop 微腔、Sagnac 环镜、反馈环"),
        ("Devices/DBR.py", "常规 / 采样 / E-DBR"),
        ("Devices/DBR_inv.py", "反相 E-DBR"),
        ("Devices/Boomerang.py", "回旋镖单元及单/双/三环"),
        ("Devices/GongCavity.py", "工字形闭合微腔"),
        ("Devices/memyshev.py", "Memyshev 双环激光器"),
    ]),
    ("Assemblies", "多器件装配：仍返回一个 Component", [
        ("Assemblies/ExtCav.py", "外腔激光器、双环/跑道外腔"),
        ("Assemblies/MultiRing.py", "串联多环（Vernier）"),
        ("Assemblies/MultiRaceTrack.py", "串联多跑道腔"),
        ("Assemblies/Isolator.py", "单环 / 环+隔离器"),
        ("Assemblies/WangCavity.py", "王字形微腔"),
    ]),
    ("TestStructures", "测试与表征结构（TC*）", [
        ("TestStructures/TCRing.py", "环形谐振器测试结构"),
        ("TestStructures/TCRaceTrack.py", "跑道腔测试结构"),
        ("TestStructures/TCCoupledCavity.py", "耦合腔 / 回旋镖测试结构"),
        ("TestStructures/Coupon.py", "通用两端 coupon"),
        ("TestStructures/TestRow.py", "测试行 / 阵列"),
    ]),
    ("Electrical", "通用加热器与电极（与光子器件解耦）", [
        ("Electrical/Heater.py", "加热器配置、蛇形加热、过孔阵列"),
        ("Electrical/ELE.py", "焊盘、GSG 电极"),
    ]),
    ("Platforms/SOI", "SOI 12 英寸平台子库（独立层号 600/631/632/…）", [
        ("Platforms/SOI/FabBasic.py", "SOI 层号表 + 工艺常数"),
        ("Platforms/SOI/Geometry.py", "Route / taper / strip / add_annulus"),
        ("Platforms/SOI/Routing.py", "Si / SiN 走线 + 开窗 + SINOP"),
        ("Platforms/SOI/Electrical.py", "过孔 / 引线 / landing 焊盘"),
        ("Platforms/SOI/Ring.py", "RingPulley / RaceTrackPulley 宏封装"),
        ("Platforms/SOI/Spiral.py", "闭合双螺旋腔中心线"),
        ("Platforms/SOI/Facet.py", "12.9° 斜端面 + 反角弯"),
        ("Platforms/SOI/PDKPorts.py", "PDK 宏端口表"),
        ("Platforms/SOI/Assembly.py", "端口包装 / connect / PDK 宏加载"),
        ("Platforms/SOI/Audit.py", "GDS → shapely 审计"),
    ]),
]

MODULE_EXTRA_PAGE = {
    "Core/GdsMerge.py": "gdsmerge.html",
}


def module_anchor(path: str) -> str:
    return "module-" + re.sub(r"[^A-Za-z0-9]+", "-", path).strip("-")


def component_module_path(factory) -> str:
    """函数真实所在的新路径，例如 Devices/Ring.py。"""
    full = (getattr(factory, "__module__", "") or "").removeprefix("AIPLPhMTools.")
    return full.replace(".", "/") + ".py" if full else "AIPLPhMTools/__init__.py"

MODULE_CAT = {
    "BasicDefine": "basic",
    "Ring": "rings",
    "MultiRing": "rings",
    "RaceTrack": "racetrack",
    "MultiRaceTrack": "racetrack",
    "CouplerMZI": "couplers",
    "CoupledCavity": "coupled",
    "Coupon": "test",
    "DBR": "dbr",
    "DBR_inv": "dbr",
    "Heater": "heaters",
    "ELE": "heaters",
    "Boomerang": "boomerang",
    "ExtCav": "extcav",
    "FeedbackCavity": "extcav",
    "memyshev": "extcav",
    "Isolator": "extcav",
    "GongCavity": "microcavity",
    "WangCavity": "microcavity",
    "TCCoupledCavity": "test",
    "TCRing": "test",
    "TCRaceTrack": "test",
    "TestRow": "test",
}


# ---------------------------------------------------------------------------
# 图层配色
# ---------------------------------------------------------------------------
# (layer, datatype) -> (显示名, 颜色, 透明度)
MAIN_PALETTE = {
    (1, 0): ("WG", "#2563eb", 1.0),
    (10, 0): ("M1 / AA", "#f59e0b", 0.95),
    (4, 1): ("M2", "#dc2626", 0.95),
    (20, 0): ("OPEN", "#16a34a", 0.32),
    (130, 0): ("CPF / SiN", "#7c3aed", 0.95),
    (24, 0): ("TN", "#db2777", 0.9),
    (15, 0): ("TP", "#f97316", 0.9),
    (70, 0): ("VIA", "#111827", 1.0),
    (71, 0): ("V2", "#334155", 1.0),
    (219, 0): ("V0", "#475569", 1.0),
    (48, 0): ("SAB", "#94a3b8", 0.7),
    (48, 100): ("NONSAB", "#cbd5e1", 0.5),
    (51, 0): ("DT", "#0f766e", 0.9),
    (125, 0): ("LM1", "#b45309", 0.9),
    (216, 0): ("SR1", "#0891b2", 0.8),
    (217, 0): ("SR2", "#0e7490", 0.8),
    (58, 0): ("MIM", "#a16207", 0.9),
    (66, 0): ("M6", "#7f1d1d", 0.9),
    (512, 8): ("LABEL", "#94a3b8", 0.0),
}

SOI_PALETTE = {
    (600, 1): ("Si 芯", "#2563eb", 1.0),
    (600, 10): ("Si 开窗", "#93c5fd", 0.35),
    (631, 1): ("SiN", "#7c3aed", 1.0),
    (631, 10): ("SiN 开窗", "#c4b5fd", 0.30),
    (632, 10): ("SiN3 开窗", "#ddd6fe", 0.30),
    (639, 1): ("TiN", "#db2777", 0.95),
    (641, 1): ("M1", "#f59e0b", 0.95),
    (642, 1): ("M2", "#dc2626", 0.95),
    (643, 1): ("M3", "#0f766e", 0.95),
    (651, 1): ("V1", "#111827", 1.0),
    (652, 1): ("V2", "#334155", 1.0),
    (660, 1): ("RV", "#64748b", 0.9),
    (661, 1): ("ALPAD", "#eab308", 0.9),
    (662, 1): ("COVER", "#94a3b8", 0.35),
    (665, 1): ("SINOP", "#22c55e", 0.40),
}

_FALLBACK_COLORS = [
    "#0ea5e9", "#84cc16", "#e11d48", "#8b5cf6", "#14b8a6",
    "#f97316", "#6366f1", "#a855f7", "#06b6d4", "#eab308",
]


def layer_style(key, palette):
    if key in palette:
        return palette[key]
    idx = (key[0] * 7 + key[1] * 13) % len(_FALLBACK_COLORS)
    return (f"{key[0]}/{key[1]}", _FALLBACK_COLORS[idx], 0.85)


# 先画底层，再画金属/过孔
_LAYER_ORDER = {
    (600, 10): 1, (631, 10): 1, (632, 10): 1,
    (1, 0): 2, (600, 1): 2, (130, 0): 2, (631, 1): 2,
    (24, 0): 3, (15, 0): 3, (639, 1): 3, (48, 0): 4,
    (10, 0): 5, (641, 1): 5, (125, 0): 5, (58, 0): 5,
    (70, 0): 6, (651, 1): 6, (71, 0): 7, (652, 1): 7,
    (4, 1): 8, (642, 1): 8, (66, 0): 9, (643, 1): 9,
    (661, 1): 10, (660, 1): 10,
    # 开窗/覆盖层最后画，半透明叠在金属上，用来表示"这里被打开"
    (20, 0): 20, (662, 1): 21, (665, 1): 22,
}


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------
def _polygon_path(poly, dbu):
    hull = [(p.x * dbu, p.y * dbu) for p in poly.each_point_hull()]
    if len(hull) < 3:
        return None
    verts = hull + [hull[0]]
    codes = [MPath.MOVETO] + [MPath.LINETO] * (len(hull) - 1) + [MPath.CLOSEPOLY]
    for i in range(poly.holes()):
        hole = [(p.x * dbu, p.y * dbu) for p in poly.each_point_hole(i)]
        if len(hole) >= 3:
            verts += hole + [hole[0]]
            codes += [MPath.MOVETO] + [MPath.LINETO] * (len(hole) - 1) + [MPath.CLOSEPOLY]
    return MPath(verts, codes)


def _nice_length(target):
    if target <= 0:
        return 1.0
    exp = math.floor(math.log10(target))
    base = 10 ** exp
    return min((1, 2, 5, 10), key=lambda m: abs(m * base - target)) * base


def render_component(c, out_png: Path, gds_gz: Path | None = None,
                     palette=MAIN_PALETTE, show_ports: bool = True) -> dict | None:
    """把 Component 渲染成白底 PNG，并返回 bbox / 实际使用图层。"""
    tmp = Path(tempfile.mkdtemp()) / "render.gds"
    c.write_gds(str(tmp))
    if gds_gz is not None:
        gds_gz.parent.mkdir(parents=True, exist_ok=True)
        with open(tmp, "rb") as src, gzip.open(gds_gz, "wb", compresslevel=9) as dst:
            shutil.copyfileobj(src, dst)

    ly = kdb.Layout()
    ly.read(str(tmp))
    try:
        cell = ly.cell(c.name)
    except Exception:
        cell = ly.top_cell()

    draws = []
    used = {}
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        key = (info.layer, info.datatype)
        name, color, alpha = layer_style(key, palette)
        if alpha <= 0:
            continue
        region = kdb.Region(cell.begin_shapes_rec(li)).merged()
        if region.is_empty():
            continue
        used[key] = {"layer": key[0], "datatype": key[1], "name": name, "color": color}
        for poly in region.each():
            pa = _polygon_path(poly, ly.dbu)
            if pa is not None:
                draws.append((pa, color, alpha))

    if not draws:
        return None

    allpts = []
    for pa, _, _ in draws:
        allpts.append(np.asarray(pa.vertices, dtype=float))
    pts = np.concatenate(allpts, axis=0)
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    w, h = max(x1 - x0, 1e-6), max(y1 - y0, 1e-6)

    scale = min(8.6 / w, 5.6 / h)
    fw, fh = w * scale, h * scale
    fw = max(fw, 2.3)
    fh = fw * h / w
    if fh > 7.4:
        fh = 7.4
        fw = fh * w / h
    if fw < 2.3:
        fw = 2.3
        fh = fw * h / w

    fig, ax = plt.subplots(figsize=(fw, fh), dpi=110)
    fig.patch.set_facecolor("white")
    draws.sort(key=lambda d: _LAYER_ORDER.get(
        next((k for k, v in used.items() if v["color"] == d[1]), (0, 0)), 6))
    for pa, color, alpha in draws:
        ax.add_patch(PathPatch(pa, facecolor=color, edgecolor="none",
                               alpha=alpha, antialiased=True, linewidth=0))
    ax.set_xlim(x0 - w * 0.03, x1 + w * 0.03)
    ax.set_ylim(y0 - h * 0.07, y1 + h * 0.07)
    ax.set_aspect("equal")
    ax.axis("off")

    # 比例尺
    nice = _nice_length(max(w, h) / 5.0)
    xa = x0 + w * 0.03
    ya = y0 - h * 0.025
    ax.plot([xa, xa + nice], [ya, ya], color="#111827", lw=2.2, solid_capstyle="butt")
    ax.text(xa + nice / 2, ya + h * 0.012, f"{nice:g} µm", ha="center", va="bottom",
            fontsize=7, color="#111827")

    # 端口位置 + 方向：箭头从端口中心朝外，标签写“名字 角度”。
    # 这样在网页上能直接判断 IO 是否 0/90/180/270，而不用只查端口表。
    if show_ports:
        ports = list(c.ports)
        if ports:
            arrow_len = max(max(w, h) * 0.045, 2.0)
            seen = []
            for p in ports:
                try:
                    cx, cy = float(p.center[0]), float(p.center[1])
                    ori = float(p.orientation) % 360.0
                except Exception:
                    continue
                ang = np.radians(ori)
                ex, ey = np.cos(ang), np.sin(ang)
                ax.annotate(
                    "", xy=(cx + ex * arrow_len, cy + ey * arrow_len),
                    xytext=(cx, cy),
                    arrowprops=dict(arrowstyle="-|>", color="#d946ef",
                                    lw=1.15, shrinkA=0, shrinkB=0),
                    annotation_clip=False,
                )
                ax.plot([cx], [cy], marker="o", ms=2.4, color="#a21caf",
                        clip_on=False, zorder=20)
                # 同一位置的重复端口（例如参考端口）只标一次。
                if any(abs(cx - sx) < 0.01 and abs(cy - sy) < 0.01
                       for sx, sy in seen):
                    continue
                seen.append((cx, cy))
                ha = "left" if ex > 0.5 else ("right" if ex < -0.5 else "center")
                va = "bottom" if ey > 0.5 else ("top" if ey < -0.5 else "center")
                ax.text(cx + ex * arrow_len * 1.34,
                        cy + ey * arrow_len * 1.34,
                        f"{p.name} {ori:g}°", fontsize=5.4, color="#86198f",
                        ha=ha, va=va, clip_on=False, zorder=21)

    # 端口箭头/标签会伸出原 bbox，稍微放宽视野。
    if show_ports:
        pad_x, pad_y = w * 0.10, h * 0.13
        ax.set_xlim(x0 - pad_x, x1 + pad_x)
        ax.set_ylim(y0 - pad_y, y1 + pad_y)

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_png), bbox_inches="tight", pad_inches=0.05, facecolor="white")
    plt.close(fig)
    return {
        "bbox": [round(x0, 3), round(y0, 3), round(x1, 3), round(y1, 3)],
        "size": [round(x1 - x0, 3), round(y1 - y0, 3)],
        "layers": sorted(used.values(), key=lambda d: (_LAYER_ORDER.get((d["layer"], d["datatype"]), 6), d["layer"])),
    }


# ---------------------------------------------------------------------------
# 文档解析
# ---------------------------------------------------------------------------
_SECTION_END = re.compile(
    r"^\s*(返回|返回值|Returns|端口|Ports|异常|Raises|注意|Notes|信息|Info|示例|Examples)\s*[:：]?\s*$"
)
_PARAM_HEAD = re.compile(r"^\s*(参数|Parameters|Args)\s*[:：]?\s*$")
_PARAM_ENTRY = re.compile(
    r"^\s{2,}([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*(?:\(([^)]*)\))?\s*[:：]\s*(.*)$"
)


def clean_doc(doc: str | None) -> str:
    return textwrap.dedent(doc or "").strip()


def summary_of(doc: str | None, limit: int = 150) -> str:
    text = clean_doc(doc)
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith(("参数", "Args", "Parameters", "```")):
            s = re.sub(r"\s+", " ", line)
            return s if len(s) <= limit else s[: limit - 1] + "…"
    return ""


def parse_param_docs(doc: str | None) -> dict[str, str]:
    lines = clean_doc(doc).splitlines()
    start = None
    for i, line in enumerate(lines):
        if _PARAM_HEAD.match(line):
            start = i + 1
            break
    if start is None:
        # 没有"参数:"段时，退化为扫描所有 `name (type): ...` 行
        start, end = 0, len(lines)
    else:
        end = len(lines)
        for i in range(start, len(lines)):
            if _SECTION_END.match(lines[i]):
                end = i
                break

    out: dict[str, str] = {}
    current: list[str] = []
    for line in lines[start:end]:
        m = _PARAM_ENTRY.match(line)
        if m:
            names = [n.strip() for n in m.group(1).split(",") if n.strip()]
            body = m.group(3).strip()
            for n in names:
                out[n] = body
            current = names
        elif current and line.strip() and not line.strip().startswith(("（", "(")):
            for n in current:
                out[n] = (out.get(n, "") + " " + line.strip()).strip()
        else:
            current = []
    return out


PARAM_NOTES = {
    "HeaterConfig": "加热器配置对象。None 表示不加；可用 ap.heaterconfig0.with_changes(TypeHeater='side', WidthHeat=6) 生成。",
    "oplayer": "光学波导层，默认 LAYER.WG = (1, 0)。",
    "heatlayer": "加热器层，默认 LAYER.M1 = (10, 0)。",
    "routelayer": "加热器布线层，默认 LAYER.M2 = (4, 1)。",
    "vialayer": "过孔层，默认 LAYER.VIA = (70, 0)。",
    "IsAD": "True 为四端口 Add-Drop；False 只保留 Input / Through。",
    "IsPad": "True 时在对应端加 GSG 焊盘阵列。",
    "Is2Pad": "True 时两端都加焊盘阵列（同时隐含 IsPad=True）。",
    "IsHeat": "True 时叠加金属加热器；加热器只占金属层，不改变光路。",
    "IsSG": "True 时周期长度从 Length1/Length2 线性渐变到 Length1E/Length2E。",
    "IsTrench": "True 时在环外加深槽热隔离环。",
    "WidthRing": "环/腔波导宽度 (µm)。",
    "RadiusRing": "环半径 (µm)，从环心到波导中心线。",
    "GapRing": "环与耦合总线之间的间隙 (µm)。",
    "AngleCouple": "Pulley 耦合段的角度 (°)；角度越大，耦合区越长。",
    "WidthNear": "耦合总线波导宽度 (µm)。",
    "tin": "输入端组件。None 时使用默认 taper（TCRing/TCCoupled 系列）。",
    "tout": "输出端组件。None 时使用默认 taper。",
    "Name": "cell 名后缀；只影响 GDS 单元命名，不影响几何。",
    "Wcol": "CSV 中宽度列（1-based）。",
    "Lcol": "CSV 中长度列（1-based）。",
    "CSVName": "CSV 路径；None 时必须显式传入。相对路径先查 AIPL_DBR_CSV_DIR。",
    "WidthHeat": "加热条宽度 (µm)。",
    "WidthRoute": "加热器引出金属/布线宽度 (µm)。",
    "Offset": "周期中较宽波导段的宽度偏移 (µm)。",
    "PeriodSampled": "采样光栅的采样周期列表（µm）。",
    "NumSampled": "每个采样周期内的光栅周期数列表。",
}


def fmt_type(p: inspect.Parameter) -> str:
    if p.annotation is inspect.Parameter.empty:
        return "—"
    a = p.annotation
    if isinstance(a, str):
        return a
    name = getattr(a, "__name__", None)
    if name:
        return name
    return str(a).replace("typing.", "")


def fmt_default(value) -> str:
    if value is inspect.Parameter.empty:
        return "必填"
    if isinstance(value, ap.HeaterConfigClass):
        if value == ap.heaterconfig0:
            return "heaterconfig0"
        return f"HeaterConfigClass(TypeHeater={value.TypeHeater!r}, …)"
    if isinstance(value, enum.Enum):
        if hasattr(ap.LAYER, value.name):
            return f"LAYER.{value.name}"
        return value.name
    if callable(value) and not isinstance(value, type):
        n = getattr(value, "__name__", "")
        if n and n != "<lambda>":
            return n + "()"
        return "函数/组件"
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, (tuple, list)):
        return repr(value)
    if value is None:
        return "None"
    return str(value)


def fmt_code_value(value) -> str:
    if isinstance(value, enum.Enum):
        if hasattr(ap.LAYER, value.name):
            return f"ap.LAYER.{value.name}"
        return repr(value.value)
    if isinstance(value, ap.HeaterConfigClass):
        return (
            "ap.HeaterConfigClass("
            f"TypeHeater={value.TypeHeater!r}, WidthHeat={value.WidthHeat!r}"
            ")"
        )
    if isinstance(value, str):
        return repr(value)
    return repr(value)


def sanitize_filename(text: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_.-]+", "_", text)
    return s[:110].strip("_") or "image"


# ---------------------------------------------------------------------------
# 变体定义
# ---------------------------------------------------------------------------
def HC(**kw):
    return ap.HeaterConfigClass(**kw)


VARIANTS: dict[str, list[dict]] = {
    "RingPulley": [
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 50}, "label": "RadiusRing = 50"},
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 200}, "label": "RadiusRing = 200"},
        {"param": "IsAD", "kwargs": {"IsAD": False}, "label": "IsAD = False（双端口）"},
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 10}, "label": "AngleCouple = 10°"},
        {"param": "HeaterConfig", "kwargs": {"HeaterConfig": HC(TypeHeater="default", WidthHeat=6)},
         "label": "加环形加热器", "code": "ap.RingPulley(HeaterConfig=ap.HeaterConfigClass(TypeHeater='default', WidthHeat=6))"},
    ],
    "RingPulleyT1": [
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 50}, "label": "RadiusRing = 50"},
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 200}, "label": "RadiusRing = 200"},
        {"param": "WidthRing", "kwargs": {"WidthRing": 1.5}, "label": "WidthRing = 1.5"},
        {"param": "GapRing", "kwargs": {"GapRing": 0.5}, "label": "GapRing = 0.5"},
        {"param": "IsAD", "kwargs": {"IsAD": False}, "label": "IsAD = False"},
        {"param": "HeaterConfig", "kwargs": {"HeaterConfig": HC(TypeHeater="default", WidthHeat=6)},
         "label": "加环形加热器", "code": "ap.RingPulleyT1(HeaterConfig=ap.HeaterConfigClass(TypeHeater='default', WidthHeat=6))"},
    ],
    "RingPulley1HS": [
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 200}, "label": "RadiusRing = 200"},
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 500}, "label": "RadiusRing = 500"},
        {"param": "GapRing", "kwargs": {"GapRing": 0.5}, "label": "GapRing = 0.5"},
    ],
    "RingPulley1HSn": [
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 200}, "label": "RadiusRing = 200"},
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 500}, "label": "RadiusRing = 500"},
    ],
    "RingPulley2": [
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 60}, "label": "RadiusRing = 60"},
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 10}, "label": "AngleCouple = 10°"},
        {"param": "GapRing", "kwargs": {"GapRing": 2}, "label": "GapRing = 2"},
    ],
    "RingPulley2ES": [
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 60}, "label": "RadiusRing = 60"},
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 10}, "label": "AngleCouple = 10°"},
    ],
    "RingPulley3": [
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 60}, "label": "RadiusRing = 60"},
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 10}, "label": "AngleCouple = 10°"},
    ],
    "RingPulley4": [
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 60}, "label": "RadiusRing = 60"},
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 20}, "label": "AngleCouple = 20°"},
    ],
    "RingPulleyT2": [
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 60}, "label": "RadiusRing = 60"},
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 10}, "label": "AngleCouple = 10°"},
    ],
    "RaceTrackP": [
        {"param": "LengthRun", "kwargs": {"LengthRun": 100}, "label": "LengthRun = 100"},
        {"param": "LengthRun", "kwargs": {"LengthRun": 400}, "label": "LengthRun = 400"},
        {"param": "RadiusRing", "kwargs": {"RadiusRing": 50}, "label": "RadiusRing = 50"},
        {"param": "IsAD", "kwargs": {"IsAD": False}, "label": "IsAD = False"},
        {"param": "HeaterConfig", "kwargs": {"HeaterConfig": HC(TypeHeater="default", WidthHeat=4, Coverage="half")},
         "label": "加半环加热器"},
    ],
    "RaceTrackS": [
        {"param": "LengthCouple", "kwargs": {"LengthCouple": 100}, "label": "LengthCouple = 100"},
        {"param": "LengthCouple", "kwargs": {"LengthCouple": 400}, "label": "LengthCouple = 400"},
        {"param": "GapCouple", "kwargs": {"GapCouple": 0.5}, "label": "GapCouple = 0.5"},
        {"param": "IsAD", "kwargs": {"IsAD": False}, "label": "IsAD = False"},
    ],
    "DoubleRaceTrack": [
        {"param": "LengthRun", "kwargs": {"LengthRun": 100}, "label": "LengthRun = 100"},
        {"param": "LengthRun", "kwargs": {"LengthRun": 400}, "label": "LengthRun = 400"},
        {"param": "DeltaRoundTrip", "kwargs": {"DeltaRoundTrip": 5}, "label": "Δ 周长 = 5"},
        {"param": "TypeCouple", "kwargs": {"TypeCouple": "s"}, "label": "TypeCouple = 's'（直耦合）"},
    ],
    "DoubleRingPulley": [
        {"param": "DeltaRadius", "kwargs": {"DeltaRadius": 1}, "label": "DeltaRadius = 1"},
        {"param": "DeltaRadius", "kwargs": {"DeltaRadius": 10}, "label": "DeltaRadius = 10"},
        {"param": "TypeR2R", "kwargs": {"TypeR2R": "bend"}, "label": "TypeR2R = 'bend'"},
        {"param": "DirectionsHeater", "kwargs": {"DirectionsHeater": ("up", "down")},
         "label": "加热器方向 (up, down)"},
    ],
    "DoubleRingPulley2HSn": [
        {"param": "DeltaRadius", "kwargs": {"DeltaRadius": 10}, "label": "DeltaRadius = 10"},
    ],
    "DoubleRingPulley2_1HSn": [
        {"param": "DeltaRadius", "kwargs": {"DeltaRadius": 10}, "label": "DeltaRadius = 10"},
    ],
    "TriRingPulley": [
        {"param": "DeltaRadius", "kwargs": {"DeltaRadius": 10}, "label": "DeltaRadius = 10"},
    ],
    "DMZI": [
        {"param": "LengthBridge", "kwargs": {"LengthBridge": 100}, "label": "LengthBridge = 100"},
        {"param": "LengthBridge", "kwargs": {"LengthBridge": 600}, "label": "LengthBridge = 600"},
        {"param": "Radius", "kwargs": {"Radius": 100}, "label": "Radius = 100"},
        {"param": "GapCoup", "kwargs": {"GapCoup": 0.5}, "label": "GapCoup = 0.5"},
        {"param": "HeaterConfig", "kwargs": {"HeaterConfig": HC(TypeHeater="default", WidthHeat=8)},
         "label": "双臂加加热器"},
    ],
    "PMZI": [
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 10}, "label": "AngleCouple = 10°"},
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 30}, "label": "AngleCouple = 30°"},
        {"param": "LengthBend", "kwargs": {"LengthBend": 100}, "label": "LengthBend = 100"},
        {"param": "HeaterConfig", "kwargs": {"HeaterConfig": HC(TypeHeater="default", WidthHeat=8)},
         "label": "双臂加加热器"},
    ],
    "PMZIHSn": [
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 10}, "label": "AngleCouple = 10°"},
        {"param": "LengthBend", "kwargs": {"LengthBend": 100}, "label": "LengthBend = 100"},
    ],
    "PulleyCoupler2X2": [
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 5}, "label": "AngleCouple = 5°"},
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 20}, "label": "AngleCouple = 20°"},
        {"param": "GapCoup", "kwargs": {"GapCoup": 0.2}, "label": "GapCoup = 0.2"},
        {"param": "IsParallel", "kwargs": {"IsParallel": True}, "label": "IsParallel = True"},
    ],
    "SagnacRing": [
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 5}, "label": "AngleCouple = 5°"},
        {"param": "RadiusBend", "kwargs": {"RadiusBend": 50}, "label": "RadiusBend = 50"},
        {"param": "GapCoup", "kwargs": {"GapCoup": 0.2}, "label": "GapCoup = 0.2"},
    ],
    "DBR": [
        {"param": "Period", "kwargs": {"Period": 20}, "label": "Period = 20"},
        {"param": "Period", "kwargs": {"Period": 50}, "label": "Period = 50"},
        {"param": "IsSG", "kwargs": {"IsSG": True, "Length1E": 0.7, "Length2E": 0.8},
         "label": "IsSG = True（渐变周期）"},
        {"param": "IsHeat", "kwargs": {"IsHeat": True}, "label": "IsHeat = True"},
        {"param": "Width1", "kwargs": {"Width1": 3}, "label": "Width1 = 3（强光栅）"},
    ],
    "EDBRStrRep": [
        {"param": "NumPeriod", "kwargs": {"NumPeriod": 50}, "label": "NumPeriod = 50"},
        {"param": "NumPeriod", "kwargs": {"NumPeriod": 200}, "label": "NumPeriod = 200"},
        {"param": "DutyCycle", "kwargs": {"DutyCycle": 0.2}, "label": "DutyCycle = 0.2"},
        {"param": "IsHeat", "kwargs": {"IsHeat": True}, "label": "IsHeat = True"},
    ],
    "CoupledRingFilter": [
        {"param": "Radius1", "kwargs": {"Radius1": 60}, "label": "Radius1 = 60"},
        {"param": "Radius1", "kwargs": {"Radius1": 150}, "label": "Radius1 = 150"},
        {"param": "Radius2", "kwargs": {"Radius2": 110}, "label": "Radius2 = 110（Vernier 失谐）"},
        {"param": "GapRing", "kwargs": {"GapRing": 0.1}, "label": "GapRing = 0.1（强耦合）"},
        {"param": "GapRing", "kwargs": {"GapRing": 0.5}, "label": "GapRing = 0.5（弱耦合）"},
        {"param": "GapBus", "kwargs": {"GapBus": 0.6}, "label": "GapBus = 0.6"},
        {"param": "IsAddDrop", "kwargs": {"IsAddDrop": False}, "label": "IsAddDrop = False（双端口）"},
    ],
    "CROW": [
        {"param": "NumRings", "kwargs": {"NumRings": 2}, "label": "NumRings = 2（光分子）"},
        {"param": "NumRings", "kwargs": {"NumRings": 6}, "label": "NumRings = 6"},
        {"param": "Radius", "kwargs": {"Radius": 30}, "label": "Radius = 30"},
        {"param": "Radius", "kwargs": {"Radius": 60}, "label": "Radius = 60"},
        {"param": "GapRing", "kwargs": {"GapRing": 0.5}, "label": "GapRing = 0.5（弱耦合）"},
    ],
    "SCISSOR": [
        {"param": "NumRings", "kwargs": {"NumRings": 2}, "label": "NumRings = 2"},
        {"param": "NumRings", "kwargs": {"NumRings": 6}, "label": "NumRings = 6"},
        {"param": "Radius", "kwargs": {"Radius": 30}, "label": "Radius = 30"},
        {"param": "GapBus", "kwargs": {"GapBus": 0.6}, "label": "GapBus = 0.6"},
        {"param": "RingGap", "kwargs": {"RingGap": 5}, "label": "RingGap = 5（更独立）"},
    ],
    "TCRingCoupon": [
        {"param": "r_ring", "kwargs": {"r_ring": 80}, "label": "r_ring = 80"},
        {"param": "r_ring", "kwargs": {"r_ring": 200}, "label": "r_ring = 200"},
        {"param": "gap_rc", "kwargs": {"gap_rc": 0.5}, "label": "gap_rc = 0.5"},
        {"param": "position_taper_in", "kwargs": {"position_taper_in": "no_bend"}, "label": "输入 no_bend"},
        {"param": "is_ad", "kwargs": {"is_ad": False}, "label": "is_ad = False"},
    ],
    "GSGELE": [
        {"param": "IsPad", "kwargs": {"IsPad": True, "LengthEle": 300}, "label": "IsPad = True"},
        {"param": "Is2Pad", "kwargs": {"Is2Pad": True, "LengthEle": 300},
         "label": "Is2Pad = True（两端焊盘）"},
        {"param": "PitchPad", "kwargs": {"Is2Pad": True, "LengthEle": 300, "PitchPad": 150},
         "label": "PitchPad = 150"},
        {"param": "WidthOpen", "kwargs": {"WidthOpen": 30, "Enclosure": 5}, "label": "小焊盘 30 / 5"},
    ],
    "OpenPad": [
        {"param": "WidthOpen", "kwargs": {"WidthOpen": 50}, "label": "WidthOpen = 50"},
        {"param": "WidthOpen", "kwargs": {"WidthOpen": 120}, "label": "WidthOpen = 120"},
        {"param": "Enclosure", "kwargs": {"Enclosure": 20}, "label": "Enclosure = 20"},
    ],
    "OffsetRamp": [
        {"param": "offset", "kwargs": {"offset": 10, "length": 40}, "label": "offset = +10"},
        {"param": "offset", "kwargs": {"offset": -10, "length": 40}, "label": "offset = -10"},
        {"param": "width2", "kwargs": {"width2": 1, "length": 40}, "label": "width2 = 1"},
    ],
    "Crossing_taper": [
        {"param": "LengthTaper", "kwargs": {"LengthTaper": 50}, "label": "LengthTaper = 50"},
        {"param": "LengthTaper", "kwargs": {"LengthTaper": 200}, "label": "LengthTaper = 200"},
        {"param": "WidthCross", "kwargs": {"WidthCross": 2}, "label": "WidthCross = 2"},
    ],
    "TaperRsoa": [
        {"param": "AngleRsoa", "kwargs": {"AngleRsoa": 30}, "label": "AngleRsoa = 30°"},
        {"param": "AngleRsoa", "kwargs": {"AngleRsoa": 5}, "label": "AngleRsoa = 5°"},
        {"param": "WidthRsoa", "kwargs": {"WidthRsoa": 20}, "label": "WidthRsoa = 20"},
        {"param": "LengthRsoa", "kwargs": {"LengthRsoa": 100}, "label": "LengthRsoa = 100"},
    ],
    "cir2end": [
        {"param": "Period", "kwargs": {"Period": 2}, "label": "Period = 2"},
        {"param": "Period", "kwargs": {"Period": 8}, "label": "Period = 8"},
        {"param": "Pitch", "kwargs": {"Pitch": 15}, "label": "Pitch = 15"},
    ],
    "GfCStraight": [
        {"param": "width", "kwargs": {"width": 0.5, "length": 100}, "label": "width = 0.5"},
        {"param": "width", "kwargs": {"width": 5, "length": 100}, "label": "width = 5"},
        {"param": "length", "kwargs": {"length": 100}, "label": "length = 100"},
    ],
    "GfCBendEuler": [
        {"param": "radius", "kwargs": {"radius": 20}, "label": "radius = 20"},
        {"param": "radius", "kwargs": {"radius": 100}, "label": "radius = 100"},
        {"param": "angle", "kwargs": {"angle": 45, "radius": 50}, "label": "angle = 45°"},
    ],
    "Boomerang": [
        {"param": "WidthRingIn", "kwargs": {"WidthRingIn": 1}, "label": "WidthRingIn = 1"},
        {"param": "WidthRingIn", "kwargs": {"WidthRingIn": 3}, "label": "WidthRingIn = 3"},
        {"param": "GapRR", "kwargs": {"GapRR": 0.6}, "label": "GapRR = 0.6"},
        {"param": "HeaterConfig+IsHeatIn", "kwargs": {"HeaterConfig": HC(TypeHeater="default", WidthHeat=6), "IsHeatIn": True, "IsHeatOut": True},
         "label": "内外环都加热", "code": "ap.Boomerang(IsHeatIn=True, IsHeatOut=True, HeaterConfig=ap.HeaterConfigClass(TypeHeater='default', WidthHeat=6))"},
    ],
    "RingBoomerang": [
        {"param": "GapRB", "kwargs": {"GapRB": 0.2}, "label": "GapRB = 0.2"},
        {"param": "GapRB", "kwargs": {"GapRB": 1.0}, "label": "GapRB = 1.0"},
    ],
    "RingDouBoomerang": [
        {"param": "DeltaLB2", "kwargs": {"DeltaLB2": 10}, "label": "DeltaLB2 = 10"},
    ],
    "RingTriBoomerang": [
        {"param": "DeltaLB2", "kwargs": {"DeltaLB2": 10}, "label": "DeltaLB2 = 10"},
    ],
    "FeedbackRing": [
        {"param": "AngleFeedback", "kwargs": {"AngleFeedback": 30}, "label": "AngleFeedback = 30°"},
        {"param": "AngleFeedback", "kwargs": {"AngleFeedback": 45}, "label": "AngleFeedback = 45°"},
        {"param": "AngleFeedback", "kwargs": {"AngleFeedback": 90}, "label": "AngleFeedback = 90°"},
        {"param": "AngleFeedback", "kwargs": {"AngleFeedback": 135}, "label": "AngleFeedback = 135°"},
        {"param": "MirrorType", "kwargs": {"MirrorType": "pdc"}, "label": "pulley DC mirror"},
    ],
    "OptFeedbackRing": [
        {"param": "AngleFeedback", "kwargs": {"AngleFeedback": 45}, "label": "Opt · AngleFeedback = 45°"},
        {"param": "AngleFeedback", "kwargs": {"AngleFeedback": 90}, "label": "Opt · AngleFeedback = 90°"},
        {"param": "AngleFeedback", "kwargs": {"AngleFeedback": 135}, "label": "Opt · AngleFeedback = 135°"},
        {"param": "MirrorType", "kwargs": {"MirrorType": "pdc"}, "label": "Opt · pulley DC mirror"},
    ],
    "OptMMISagnacLoop": [
        {"param": "Radius", "kwargs": {"Radius": 52}, "label": "Radius = 52 um"},
        {"param": "Radius", "kwargs": {"Radius": 80}, "label": "Radius = 80 um"},
        {"param": "RadiusMin",
         "kwargs": {"RadiusMin": 11},
         "label": "RadiusMin = 11 um (Si)"},
        {"param": "LoopShape",
         "kwargs": {"LoopShape": "euler"},
         "label": "LoopShape = euler (larger)"},
    ],
    "OptPDCSagnacLoop": [
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 11}, "label": "AngleCouple = 11°"},
        {"param": "AngleCouple", "kwargs": {"AngleCouple": 20}, "label": "AngleCouple = 20°"},
        {"param": "Radius", "kwargs": {"Radius": 60}, "label": "Radius = 60 um"},
        {"param": "RadiusMin",
         "kwargs": {"RadiusMin": 30},
         "label": "RadiusMin = 30 um (Si)"},
        {"param": "LoopShape",
         "kwargs": {"LoopShape": "euler"},
         "label": "LoopShape = euler (larger)"},
        {"param": "WidthLoop",
         "kwargs": {"Width": 1.55, "WidthLoop": 2.0, "AngleCouple": 11, "RadiusIn": 200},
         "label": "Width 1.55 -> loop 2.0"},
    ],
    "ExtCavDouRing": [
        {"param": "r_ring", "kwargs": {"r_ring": 100}, "label": "r_ring = 100"},
        {"param": "r_ring", "kwargs": {"r_ring": 300}, "label": "r_ring = 300"},
        {"param": "gap_rc", "kwargs": {"gap_rc": 0.2}, "label": "gap_rc = 0.2"},
        {"param": "gap_rc", "kwargs": {"gap_rc": 0.6}, "label": "gap_rc = 0.6"},
    ],
    "ExtCavTriRing": [
        {"param": "r_ring", "kwargs": {"r_ring": 100}, "label": "r_ring = 100"},
        {"param": "gap_rc", "kwargs": {"gap_rc": 0.6}, "label": "gap_rc = 0.6"},
    ],
    "ExtCavDouRaceTrack": [
        {"param": "r_ring", "kwargs": {"r_ring": 100}, "label": "r_ring = 100"},
        {"param": "gap_rc", "kwargs": {"gap_rc": 0.6}, "label": "gap_rc = 0.6"},
    ],
    "DoubleRingMemyshev": [
        {"param": "r_ring", "kwargs": {"r_ring": 100}, "label": "r_ring = 100"},
        {"param": "r_ring", "kwargs": {"r_ring": 300}, "label": "r_ring = 300"},
        {"param": "gap_rc", "kwargs": {"gap_rc": 0.6}, "label": "gap_rc = 0.6"},
    ],
    "SingleRingIsolator0": [
        {"param": "gap_rc1", "kwargs": {"gap_rc1": 0.5}, "label": "gap_rc1 = 0.5"},
        {"param": "gap_rc2", "kwargs": {"gap_rc2": 6}, "label": "gap_rc2 = 6"},
        {"param": "r_ring", "kwargs": {"r_ring": 80}, "label": "r_ring = 80"},
    ],
    "GongCavity": [
        {"param": "LengthHoriz", "kwargs": {"LengthHoriz": 150}, "label": "LengthHoriz = 150"},
        {"param": "LengthHoriz", "kwargs": {"LengthHoriz": 500}, "label": "LengthHoriz = 500"},
        {"param": "GapRing", "kwargs": {"GapRing": 0.5}, "label": "GapRing = 0.5"},
    ],
    "WangCavity": [
        {"param": "LengthHoriz", "kwargs": {"LengthHoriz": 150}, "label": "LengthHoriz = 150"},
        {"param": "LengthVert", "kwargs": {"LengthVert": 600}, "label": "LengthVert = 600"},
        {"param": "GapRing", "kwargs": {"GapRing": 0.5}, "label": "GapRing = 0.5"},
    ],
    "TCRing": [
        {"param": "r_ring", "kwargs": {"r_ring": 80}, "label": "r_ring = 80"},
        {"param": "gap_rc", "kwargs": {"gap_rc": 0.5}, "label": "gap_rc = 0.5"},
        {"param": "is_ad", "kwargs": {"is_ad": True, "length_total": 3000}, "label": "is_ad = True"},
    ],
    "TCRing1AD": [
        {"param": "r_ring", "kwargs": {"r_ring": 80, "length_total": 1500}, "label": "r_ring = 80"},
        {"param": "gap_rc", "kwargs": {"gap_rc": 0.5, "length_total": 1500}, "label": "gap_rc = 0.5"},
    ],
    "TCRing2": [
        {"param": "r_ring", "kwargs": {"r_ring": 80}, "label": "r_ring = 80"},
    ],
    "TCRingBoomerangT1": [
        {"param": "r_ring", "kwargs": {"r_ring": 80, "length_total": 3000}, "label": "r_ring = 80"},
        {"param": "gap_rr", "kwargs": {"gap_rr": 0.5, "length_total": 3000}, "label": "gap_rr = 0.5"},
    ],
    "TCCoupleDouRingT1": [
        {"param": "r_ring1", "kwargs": {"r_ring1": 80, "length_total": 3000}, "label": "r_ring1 = 80"},
        {"param": "gap_rr", "kwargs": {"gap_rr": 0.5, "length_total": 3000}, "label": "gap_rr = 0.5"},
    ],
    "TCRaceTrackP": [
        {"param": "r_ring", "kwargs": {"r_ring": 1000, "length_total": 6000}, "label": "r_ring = 1000"},
        {"param": "length_run", "kwargs": {"length_run": 300, "length_total": 6000}, "label": "length_run = 300"},
        {"param": "gap_rc", "kwargs": {"gap_rc": 0.5, "length_total": 6000}, "label": "gap_rc = 0.5"},
    ],
    "TCRaceTrackS": [
        {"param": "length_run", "kwargs": {"length_run": 300}, "label": "length_run = 300"},
        {"param": "gap_rc", "kwargs": {"gap_rc": 0.5}, "label": "gap_rc = 0.5"},
    ],
}


# ---------------------------------------------------------------------------
# 手工登记的"需要额外输入"的绘制函数
# ---------------------------------------------------------------------------
def _build_different_heater(**kw):
    return ap.DifferentHeater(PathHeat=gf.path.straight(length=220), **kw)


def _build_snake_heater(**kw):
    return ap.SnakeHeater(PathHeat=gf.path.straight(length=300), **kw)


def _build_via_array(**kw):
    src = gf.Component()
    src.add_ref(gf.c.rectangle(size=(110, 60), layer=ap.LAYER.M1, centered=True))
    vias = ap.ViaArray(src, arraylayer=ap.LAYER.M1, **kw)
    out = gf.Component()
    out << src
    out << vias
    return out


def _build_coupon_demo():
    core = ap.GfCStraight(length=200, width=2)
    return ap.Coupon(
        core=core, core_input="o1", core_output="o2",
        io_width=1.0, width_in=2.0, width_out=2.0,
        taper_length=100, length_total=1000,
            center_ports=None, forward_ports=("o1", "o2"), port_prefix="Core",
    )


MANUAL = {
    "Coupon": {
        "module": "Coupon", "module_path": "TestStructures/Coupon.py", "category": "test",
        "factory": _build_coupon_demo, "sig": ap.Coupon,
        "note": "通用两端 coupon：中间 core 只要有左右端口即可。这里用 200 µm 直波导作 core 演示。",
        "code": "core = ap.GfCStraight(length=200, width=2)\ncoupon = ap.Coupon(core=core, core_input='o1', core_output='o2', io_width=1.0, length_total=1000)",
    },
    "DifferentHeater": {
        "module": "Heater", "module_path": "Electrical/Heater.py", "category": "heaters",
        "factory": _build_different_heater, "sig": ap.DifferentHeater,
        "note": "PathHeat 必须由调用者给出；这里统一用 220 µm 直波导演示。TypeHeater 决定加热条是单条、侧边、双侧、多条还是蛇形切割。",
        "code": "import gdsfactory as gf\n\nc = ap.DifferentHeater(PathHeat=gf.path.straight(length=220))",
        "variants": [
            {"param": "TypeHeater", "kwargs": {"HeaterConfig": HC(TypeHeater="side", WidthHeat=6, DeltaHeat=10)},
             "label": "TypeHeater = 'side'", "code": "ap.DifferentHeater(PathHeat=gf.path.straight(220), HeaterConfig=ap.HeaterConfigClass(TypeHeater='side', WidthHeat=6, DeltaHeat=10))"},
            {"param": "TypeHeater", "kwargs": {"HeaterConfig": HC(TypeHeater="bothside", WidthHeat=4, DeltaHeat=8)},
             "label": "TypeHeater = 'bothside'", "code": "ap.DifferentHeater(PathHeat=gf.path.straight(220), HeaterConfig=ap.HeaterConfigClass(TypeHeater='bothside', WidthHeat=4, DeltaHeat=8))"},
            {"param": "TypeHeater", "kwargs": {"HeaterConfig": HC(TypeHeater="multi", WidthHeat=(4, 4), DeltaHeat=(-8, 8))},
             "label": "TypeHeater = 'multi'", "code": "ap.DifferentHeater(PathHeat=gf.path.straight(220), HeaterConfig=ap.HeaterConfigClass(TypeHeater='multi', WidthHeat=(4,4), DeltaHeat=(-8,8)))"},
            {"param": "TypeHeater", "kwargs": {"HeaterConfig": HC(TypeHeater="spilt", WidthHeat=6, WidthRoute=10, DeltaHeat=20, GapHeat=3)},
             "label": "TypeHeater = 'spilt'", "code": "ap.DifferentHeater(PathHeat=gf.path.straight(220), HeaterConfig=ap.HeaterConfigClass(TypeHeater='spilt', WidthHeat=6, DeltaHeat=20, GapHeat=3))"},
        ],
    },
    "SnakeHeater": {
        "module": "Heater", "module_path": "Electrical/Heater.py", "category": "heaters",
        "factory": _build_snake_heater, "sig": ap.SnakeHeater,
        "note": "蛇形加热器沿 PathHeat 周期性切除上下两条槽；WidthHeat 越大、槽越深，等效电阻越高。",
        "code": "import gdsfactory as gf\n\nc = ap.SnakeHeater(PathHeat=gf.path.straight(length=300))",
        "variants": [
            {"param": "WidthHeat", "kwargs": {"WidthHeat": 4}, "label": "WidthHeat = 4"},
            {"param": "WidthHeat", "kwargs": {"WidthHeat": 12}, "label": "WidthHeat = 12"},
            {"param": "GapHeat", "kwargs": {"GapHeat": 2}, "label": "GapHeat = 2"},
        ],
    },
    "ViaArray": {
        "module": "Heater", "module_path": "Electrical/Heater.py", "category": "heaters",
        "factory": _build_via_array, "sig": ap.ViaArray,
        "note": "在给定组件某个图层（这里是 110×60 µm 的 M1 矩形）内部按 Enclosure 内缩后布孔；演示图同时显示源区域与过孔。",
        "allow_no_ports": True,
        "code": "import gdsfactory as gf\n\nsrc = gf.Component(\"src\")\nsrc.add_ref(gf.c.rectangle(size=(110, 60), layer=ap.LAYER.M1, centered=True))\nc = ap.ViaArray(src, arraylayer=ap.LAYER.M1)",
        "variants": [
            {"param": "Spacing", "kwargs": {"Spacing": 0.8}, "label": "Spacing = 0.8"},
            {"param": "Spacing", "kwargs": {"Spacing": 1.6}, "label": "Spacing = 1.6"},
            {"param": "WidthVia", "kwargs": {"WidthVia": 1.0}, "label": "WidthVia = 1.0"},
            {"param": "Enclosure", "kwargs": {"Enclosure": 6}, "label": "Enclosure = 6"},
        ],
    },
    "TWQRcode": {
        "module": "BasicDefine", "module_path": "Core/BasicDefine.py", "category": "tools",
        "factory": ap.TWQRcode, "sig": ap.TWQRcode,
        "note": "把团队网址打成 QR 码放在版图上；没有光学/电学端口。Size 是单个码点尺寸 (µm)。",
        "code": "c = ap.TWQRcode(Size=10)",
        "allow_no_ports": True,
        "variants": [
            {"param": "Size", "kwargs": {"Size": 6}, "label": "Size = 6"},
            {"param": "Size", "kwargs": {"Size": 14}, "label": "Size = 14"},
        ],
    },
}


# ---------------------------------------------------------------------------
# CSV 演示数据（CSV 驱动的 DBR 没有默认数据，这里生成一份可复现的小样本）
# ---------------------------------------------------------------------------
CSV_DIR = HERE / "assets" / "csv"
CSV_DIR.mkdir(parents=True, exist_ok=True)
DBR_CSV = CSV_DIR / "dbr_demo.csv"
EDBR_CSV = CSV_DIR / "edbr_demo.csv"


def ensure_demo_csv():
    rows = []
    for i in range(24):
        w0 = 0.80 + 0.05 * math.sin(i / 3.0)
        rows.append(f"{w0:.4f},0.4000,0.5000,0.6000")
    DBR_CSV.write_text("\n".join(rows) + "\n", encoding="utf-8")

    lines = [
        "% center_waveguide_width_um=0.8",
        "% side_block_width_um=0.3",
        "% center_to_block_center_distance_um=0.8",
        "% total_length_um=20",
        "start,end",
    ]
    for i in range(12):
        x = i * 1.6
        lines.append(f"{x:.3f},{x + 0.8:.3f}")
    EDBR_CSV.write_text("\n".join(lines) + "\n", encoding="utf-8")


CSV_BUILDERS = {
    "DBRFromCsv": lambda: ap.DBRFromCsv(CSVName=str(DBR_CSV)),
    "DBRFromCsvOffset": lambda: ap.DBRFromCsvOffset(CSVName=str(DBR_CSV)),
    "SGDBRFromCsvOffset": lambda: ap.SGDBRFromCsvOffset(CSVName=str(DBR_CSV)),
    "VSGDBRFromCsvOffset": lambda: ap.VSGDBRFromCsvOffset(
        CSVName=str(DBR_CSV), PeriodSampled=[4, 4], NumSampled=[4, 2]),
    "EstrDBRFromCsvOffset": lambda: ap.EstrDBRFromCsvOffset(CSVName=str(DBR_CSV)),
    "EDBRFromCsv": lambda: ap.EDBRFromCsv(csv_path=str(EDBR_CSV)),
}
CSV_NOTE = ("CSV 驱动器件：手册用仓库内示例数据 assets/csv/ 渲染；"
            "实际使用时传入自己的 CSVName，或设置 AIPL_DBR_CSV_DIR。"
            "示例几何只用于展示参数与结构关系，不代表你的设计值。")

CSV_CODES = {
    "DBRFromCsv": 'c = ap.DBRFromCsv(CSVName="dbr_demo.csv")',
    "DBRFromCsvOffset": 'c = ap.DBRFromCsvOffset(CSVName="dbr_demo.csv")',
    "SGDBRFromCsvOffset": 'c = ap.SGDBRFromCsvOffset(CSVName="dbr_demo.csv")',
    "VSGDBRFromCsvOffset": 'c = ap.VSGDBRFromCsvOffset(CSVName="dbr_demo.csv", PeriodSampled=[4, 4], NumSampled=[4, 2])',
    "EstrDBRFromCsvOffset": 'c = ap.EstrDBRFromCsvOffset(CSVName="dbr_demo.csv")',
    "EDBRFromCsv": 'c = ap.EDBRFromCsv(csv_path="edbr_demo.csv")',
}

COMPONENT_NOTES = {
    "GSGELE": "默认 LengthEle=10000 µm（10 mm），整图是一条很长的线；焊盘与 GSG 形状见下方 IsPad / Is2Pad 对比。",
    "TCRing": "默认 length_total=10000 µm，整图很扁；对比图里缩小 length_total，以便看清环和引出臂。",
    "TCRing1AD": "默认 length_total=2000 µm；对比图进一步缩小，便于观察 Add/Drop 端口。",
    "TCRing2": "默认 length_total=10000 µm；对比图缩小了环半径，便于观察结构。",
    "TCRing3": "默认 length_total=10000 µm；整图很扁，属于测试结构。",
    "TCRing4": "默认 length_total=10000 µm；整图很扁，属于测试结构。",
    "TCRingBoomerangT1": "默认 length_total=10000 µm；对比图缩小到 3000 µm，便于观察 Boomerang 核心。",
    "TCRingDouBoomerangT1": "默认 length_total=10000 µm；整图很扁，属于测试结构。",
    "TCRingTriBoomerangT1": "默认 length_total=4000 µm；Boomerang 核心在左侧，右侧是引出臂。",
    "TCCoupleDouRingT1": "默认 length_total=10000 µm；对比图缩小到 3000 µm，便于观察双环核心。",
    "TCCoupleDouRaceTrackT1": "默认 length_total=10000 µm；属于长测试结构，整图很扁。",
    "TCCoupleDouRaceTrackT2": "默认 width_total=5000 µm；属于长测试结构，整图很扁。",
    "TCRaceTrackP": "默认 length_total=10000 µm / r_ring=2000 µm；对比图缩小了总长与半径。",
    "TCRaceTrackS": "默认 length_total=10000 µm；属于长测试结构，整图很扁。",
    "RingPulley1HS": "默认 RadiusRing=1000 µm，带侧边加热器，整图较大；对比图用更小半径。",
    "RingPulley1HSn": "默认 RadiusRing=1000 µm，带蛇形加热器，整图较大；对比图用更小半径。",
}


# ---------------------------------------------------------------------------
# 加热器 3D 层叠图
# ---------------------------------------------------------------------------
# 3D 只做“层序示意”，z 间距被夸张；不是真实膜厚。
_STACK_ORDER = {
    (51, 0): -1,
    (1, 0): 0,
    (130, 0): 1,
    (24, 0): 2,
    (15, 0): 2,
    (10, 0): 4,
    (70, 0): 5,
    (4, 1): 6,
    (20, 0): 7,
    (71, 0): 8,
}

_STACK3D = {
    (1, 0): (0.0, 3.0),
    (130, 0): (0.0, 3.0),
    (10, 0): (9.0, 4.0),
    (70, 0): (13.0, 2.0),
    (4, 1): (17.0, 4.0),
    (20, 0): (24.0, 1.5),
    (71, 0): (21.0, 2.0),
}

HEATER_3D_LINK = {
    "DifferentHeater": "dh-default",
    "SnakeHeater": "snake",
    "RingPulley1HS": "ring-side",
    "RingPulley1HSn": "ring-snake",
}

HEATER_3D_ITEMS = {
    "dh-default": {
        "title": "DifferentHeater · default",
        "note": "沿 PathHeat 拉伸的单条 M1 加热条。",
        "factory": lambda: ap.DifferentHeater(PathHeat=gf.path.straight(length=220)),
        "code": "ap.DifferentHeater(PathHeat=gf.path.straight(length=220))",
    },
    "dh-side": {
        "title": "DifferentHeater · side",
        "note": "单侧加热：加热条相对波导中心偏移 DeltaHeat，另一侧不铺金属。",
        "factory": lambda: ap.DifferentHeater(
            PathHeat=gf.path.straight(length=220),
            HeaterConfig=ap.HeaterConfigClass(TypeHeater="side", WidthHeat=6, DeltaHeat=10),
        ),
        "code": "ap.DifferentHeater(PathHeat=gf.path.straight(220), HeaterConfig=ap.HeaterConfigClass(TypeHeater='side', WidthHeat=6, DeltaHeat=10))",
    },
    "dh-bothside": {
        "title": "DifferentHeater · bothside",
        "note": "双侧对称加热：波导两侧各一条 M1，对应两路独立电流。",
        "factory": lambda: ap.DifferentHeater(
            PathHeat=gf.path.straight(length=220),
            HeaterConfig=ap.HeaterConfigClass(TypeHeater="bothside", WidthHeat=4, DeltaHeat=8),
        ),
        "code": "ap.DifferentHeater(PathHeat=gf.path.straight(220), HeaterConfig=ap.HeaterConfigClass(TypeHeater='bothside', WidthHeat=4, DeltaHeat=8))",
    },
    "dh-multi": {
        "title": "DifferentHeater · multi",
        "note": "多条加热条：WidthHeat / DeltaHeat 用元组给出每一对（宽度，偏移）。",
        "factory": lambda: ap.DifferentHeater(
            PathHeat=gf.path.straight(length=220),
            HeaterConfig=ap.HeaterConfigClass(TypeHeater="multi", WidthHeat=(4, 4), DeltaHeat=(-8, 8)),
        ),
        "code": "ap.DifferentHeater(PathHeat=gf.path.straight(220), HeaterConfig=ap.HeaterConfigClass(TypeHeater='multi', WidthHeat=(4,4), DeltaHeat=(-8,8)))",
    },
    "dh-spilt": {
        "title": "DifferentHeater · spilt",
        "note": "主加热条 M1 + 两侧 M2 布线臂；层间过孔阵列太密，3D 中省略 VIA 层。",
        "factory": lambda: ap.DifferentHeater(
            PathHeat=gf.path.straight(length=220),
            HeaterConfig=ap.HeaterConfigClass(TypeHeater="spilt", WidthHeat=6, WidthRoute=10, DeltaHeat=20, GapHeat=3),
        ),
        "code": "ap.DifferentHeater(PathHeat=gf.path.straight(220), HeaterConfig=ap.HeaterConfigClass(TypeHeater='spilt', WidthHeat=6, WidthRoute=10, DeltaHeat=20, GapHeat=3))",
    },
    "snake": {
        "title": "SnakeHeater",
        "note": "蛇形切割加热器：沿路径周期性切掉上下两条槽，增加等效电阻。",
        "factory": lambda: ap.SnakeHeater(PathHeat=gf.path.straight(length=300), WidthHeat=8, GapHeat=1),
        "code": "ap.SnakeHeater(PathHeat=gf.path.straight(length=300), WidthHeat=8, GapHeat=1)",
    },
    "ring-side": {
        "title": "RingPulley1HS · 侧加热环",
        "note": "WG 环 + M1 侧边加热条；3D 中可看到金属层悬在波导层上方。",
        "factory": lambda: ap.RingPulley1HS(RadiusRing=100),
        "code": "ap.RingPulley1HS(RadiusRing=100)",
    },
    "ring-snake": {
        "title": "RingPulley1HSn · 蛇形加热环",
        "note": "WG 环 + M1 蛇形加热器；环周被周期性切割。",
        "factory": lambda: ap.RingPulley1HSn(RadiusRing=100),
        "code": "ap.RingPulley1HSn(RadiusRing=100)",
    },
}


def _simplify_contour(points, max_points=600):
    """3D 预览用的顶点抽稀；只影响显示，不影响器件本身。"""
    if len(points) <= max_points:
        return points
    step = max(1, len(points) // max_points)
    out = points[::step]
    return out if len(out) >= 3 else points


def extract_3d(c) -> dict | None:
    """从一个 Component 提取 3D 层叠数据（外轮廓 + 孔洞 + 层序）。"""
    tmp = Path(tempfile.mkdtemp()) / "3d.gds"
    c.write_gds(str(tmp))
    ly = kdb.Layout()
    ly.read(str(tmp))
    try:
        cell = ly.cell(c.name)
    except Exception:
        cell = ly.top_cell()

    layers = []
    allpts = []
    for li in ly.layer_indexes():
        info = ly.get_info(li)
        key = (info.layer, info.datatype)
        name, color, alpha = layer_style(key, MAIN_PALETTE)
        if alpha <= 0:
            continue
        region = kdb.Region(cell.begin_shapes_rec(li)).merged()
        if region.is_empty():
            continue
        z, thick = _STACK3D.get(key, (9.0, 3.0))
        order = _STACK_ORDER.get(key, 9)
        # 过密的小图形（例如过孔阵列）抽样显示，保留层叠关系但控制数据量
        polys_all = list(region.each())
        limit = 200 if key == (70, 0) else 800
        if len(polys_all) > limit:
            step = max(1, len(polys_all) // limit)
            polys_all = polys_all[::step]
        polys = []
        for poly in polys_all:
            outer = _simplify_contour([(p.x * ly.dbu, p.y * ly.dbu) for p in poly.each_point_hull()])
            if len(outer) < 3:
                continue
            holes = []
            for h in range(poly.holes()):
                hole = _simplify_contour([(p.x * ly.dbu, p.y * ly.dbu) for p in poly.each_point_hole(h)])
                if len(hole) >= 3:
                    holes.append([[round(x, 3), round(y, 3)] for x, y in hole])
            outer = [[round(x, 3), round(y, 3)] for x, y in outer]
            polys.append({"outer": outer, "holes": holes})
            allpts.extend(outer)
        if polys:
            layers.append({
                "key": f"{key[0]}/{key[1]}", "name": name, "color": color,
                "alpha": alpha, "z": z, "order": order,
                "thickness": thick, "display": 1.0, "polygons": polys,
            })

    if not layers:
        return None
    layers.sort(key=lambda d: (d["order"], d["z"]))
    pts = np.asarray(allpts)
    x0, y0 = pts.min(axis=0)
    x1, y1 = pts.max(axis=0)
    return {
        "layers": layers,
        "bbox": [round(float(x0), 3), round(float(y0), 3),
                 round(float(x1), 3), round(float(y1), 3)],
        "size": [round(float(x1 - x0), 3), round(float(y1 - y0), 3)],
    }


def build_heater_3d() -> dict:
    data = {}
    for key, spec in HEATER_3D_ITEMS.items():
        try:
            c = spec["factory"]()
            info = extract_3d(c)
            if info is None:
                print(f"  !! 3D empty: {key}")
                continue
            data[key] = {
                "title": spec["title"], "note": spec["note"], "code": spec["code"],
                "layers": info["layers"], "bbox": info["bbox"], "size": info["size"],
            }
            print(f"  3D {key:14s} layers={[l['name'] for l in info['layers']]}")
        except Exception as exc:  # noqa: BLE001
            print(f"  !! 3D {key}: {type(exc).__name__}: {exc}")
    js = "window.HEATER_3D = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    (HERE / "assets" / "heaters3d-data.js").write_text(js, encoding="utf-8")
    return data


# ---------------------------------------------------------------------------
# 构建数据
# ---------------------------------------------------------------------------
def component_module(factory) -> str:
    mod = getattr(factory, "__module__", "") or ""
    return mod.rsplit(".", 1)[-1] if mod else "AIPLPhMTools"


def category_of(name, factory, module, override=None):
    if override:
        return override
    return MODULE_CAT.get(module, "basic")


def build_component(name, factory, sig_source, module, category, note="",
                    code_override=None, allow_no_ports=False, module_path=None) -> dict:
    doc = clean_doc(inspect.getdoc(sig_source))
    docs = parse_param_docs(doc)
    sig = inspect.signature(sig_source)
    params = []
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        pdoc = docs.get(p.name) or PARAM_NOTES.get(p.name, "")
        params.append({
            "name": p.name,
            "type": fmt_type(p),
            "default": fmt_default(p.default),
            "required": p.default is inspect.Parameter.empty,
            "doc": re.sub(r"\s+", " ", pdoc).strip(),
        })

    default_code = (f"import AIPLPhMTools as ap\n\nc = ap.{name}()\n"
                    f"c.write_gds(\"{name}.gds\")")
    if code_override:
        code = code_override if "import AIPLPhMTools" in code_override else (
            "import AIPLPhMTools as ap\n\n" + code_override)
    else:
        code = default_code
    info = {"name": name, "module": module, "module_path": module_path or f"{module}.py",
            "category": category,
            "summary": summary_of(doc), "doc": doc, "params": params,
            "ports": [], "layers": [], "bbox": None, "size": None,
            "image": None, "gds": None, "variants": [], "note": note,
            "error": None, "code": code}

    try:
        c = factory()
    except Exception as exc:  # noqa: BLE001
        info["error"] = f"{type(exc).__name__}: {exc}"
        print(f"  !! {name}: default build failed: {info['error']}")
        return info

    info["ports"] = [
        {"name": p.name, "width": round(float(p.width), 4),
         "orientation": round(float(p.orientation), 3),
         "center": [round(float(p.center[0]), 3), round(float(p.center[1]), 3)],
         "layer": str(p.layer)}
        for p in c.ports
    ]

    png = IMG / f"{name}.png"
    gz = GDS_DIR / f"{name}.gds.gz"
    r = render_component(c, png, gz)
    if r is None:
        info["error"] = "该函数没有产生任何多边形（空版图）"
        print(f"  !! {name}: empty layout")
    else:
        info["image"] = f"assets/img/{name}.png"
        info["gds"] = f"assets/gds/{name}.gds.gz"
        info["layers"] = r["layers"]
        info["bbox"] = r["bbox"]
        info["size"] = r["size"]
        print(f"  ok {name:28s} ports={len(info['ports']):2d} layers={len(r['layers'])}")
        try:
            v3 = extract_3d(c)
            if v3:
                vdir = HERE / "assets" / "view3d"
                vdir.mkdir(parents=True, exist_ok=True)
                payload = {
                    "title": name, "note": info["summary"], "code": info["code"],
                    "layers": v3["layers"], "bbox": v3["bbox"], "size": v3["size"],
                }
                (vdir / f"{name}.js").write_text(
                    "window.VIEW3D = " + json.dumps(payload, ensure_ascii=False,
                                                   separators=(",", ":")) + ";\n",
                    encoding="utf-8",
                )
                info["view3d"] = f"assets/view3d/{name}.js"
        except Exception as exc:  # noqa: BLE001
            print(f"  !! 3D {name}: {type(exc).__name__}: {exc}")

    if not allow_no_ports and not info["ports"]:
        info["error"] = info["error"] or "没有端口（通用图元/工具，正常）"
    return info


def build_variants(comp: dict, factory, entries) -> None:
    if not entries:
        return
    out = []
    for e in entries:
        try:
            c = factory(**e["kwargs"])
            slug = sanitize_filename(comp["name"] + "__" + e.get("label", e["param"]))
            png = IMG_V / f"{slug}.png"
            r = render_component(c, png)
            if r is None:
                print(f"     variant empty: {comp['name']} {e['label']}")
                continue
            code = e.get("code") or (
                f"ap.{comp['name']}(" +
                ", ".join(f"{k}={fmt_code_value(v)}" for k, v in e["kwargs"].items()) + ")"
            )
            out.append({"param": e["param"], "label": e["label"],
                        "image": f"assets/img/variants/{slug}.png",
                        "code": code, "bbox": r["bbox"], "size": r["size"]})
            print(f"     variant {comp['name']:22s} {e['label']}")
        except Exception as exc:  # noqa: BLE001
            print(f"     variant FAIL {comp['name']} {e.get('label')}: {type(exc).__name__}: {exc}")
    comp["variants"] = out


def build_all() -> list[dict]:
    ensure_demo_csv()
    comps = []
    for name in ap.list_components():
        default_factory = ap.get_component(name)
        factory = CSV_BUILDERS.get(name, default_factory)
        module = component_module(default_factory)
        cat = category_of(name, default_factory, module)
        note = CSV_NOTE if name in CSV_BUILDERS else COMPONENT_NOTES.get(name, "")
        comp = build_component(name, factory, default_factory, module, cat,
                               note=note, code_override=CSV_CODES.get(name),
                               module_path=component_module_path(default_factory))
        build_variants(comp, factory, VARIANTS.get(name))
        comps.append(comp)

    for name, spec in MANUAL.items():
        comp = build_component(
            name, spec["factory"], spec["sig"], spec["module"], spec["category"],
            note=spec.get("note", ""), code_override=spec.get("code"),
            allow_no_ports=spec.get("allow_no_ports", False),
            module_path=spec.get("module_path"),
        )
        build_variants(comp, spec["factory"], spec.get("variants"))
        comps.append(comp)

    comps.sort(key=lambda c: (CAT_ORDER.get(c["category"], 99), c["name"].lower()))
    return comps


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------
def esc(s) -> str:
    return html.escape(str(s), quote=True)


def fmt_bbox(comp) -> str:
    if not comp["bbox"]:
        return "—"
    x0, y0, x1, y1 = comp["bbox"]
    return f"({x0:g}, {y0:g}) → ({x1:g}, {y1:g}) µm"


def fmt_size(comp) -> str:
    if not comp["size"]:
        return "—"
    return f"{comp['size'][0]:g} × {comp['size'][1]:g} µm"


def sidebar_html(rel, active_name=None, active_cat=None, comps=None) -> str:
    groups = []
    for cid, cname, _, _ in CATEGORIES:
        items = [c for c in comps if c["category"] == cid]
        links = []
        for c in items:
            kw = " ".join(p["name"] for p in c["params"]) + " " + c["summary"]
            links.append(
                f'<a class="nav-link{" active" if c["name"] == active_name else ""}" '
                f'href="{rel}components/{c["name"]}.html" data-name="{esc(c["name"])}" '
                f'data-keywords="{esc(kw)}">{esc(c["name"])}</a>'
            )
        open_attr = " open" if cid == active_cat or active_name in [c["name"] for c in items] else ""
        groups.append(
            f'<details class="nav-group"{open_attr}><summary>{esc(cname)}'
            f'<span class="count">{len(items)}</span></summary>'
            f'<div class="nav-links">{"".join(links)}</div></details>'
        )
    return f"""
<aside class="sidebar">
  <a class="brand" href="{rel}index.html">
    <span class="brand-mark">AP</span>
    <span><strong>AIPLPhMTools</strong><span>PDK 手册</span></span>
  </a>
  <div class="nav-search-wrap">
    <input id="nav-search" type="search" placeholder="搜索器件 / 参数…  ( / )" autocomplete="off">
  </div>
  <nav>
    <a class="nav-top" href="{rel}index.html">概览</a>
    <a class="nav-top" href="{rel}guide.html">快速开始与约定</a>
    <a class="nav-top" href="{rel}modules.html">模块层级</a>
    <a class="nav-top" href="{rel}gdsmerge.html">GDS 合并</a>
    <a class="nav-top" href="{rel}platforms_soi.html">SOI 平台子库</a>
    <a class="nav-top" href="{rel}heaters3d.html">加热器 3D</a>
    {''.join(groups)}
    <div class="nav-empty">没有匹配的器件。试试参数名，如 <code>RadiusRing</code>。</div>
  </nav>
</aside>
<button class="menu-btn" aria-label="菜单">≡</button>
<div class="lightbox-overlay"><button class="lightbox-close" aria-label="关闭">×</button><img alt=""></div>
"""


def layout(title, body, rel="", active_name=None, active_cat=None, desc="", comps=None) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · AIPLPhMTools</title>
<meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="{rel}assets/site.css">
<script defer src="{rel}assets/site.js"></script>
</head>
<body>
{sidebar_html(rel, active_name, active_cat, comps)}
<div class="main"><div class="main-inner">
{body}
<div class="footer">
  AIPLPhMTools {esc(ap.__version__)} · 版图图像由 gdsfactory + KLayout + Matplotlib 从真实 GDS 渲染 ·
  生成脚本 <code>docs/build_site.py</code>
</div>
</div></div>
</body>
</html>"""


def breadcrumb(rel, comp=None, cat=None) -> str:
    parts = [f'<a href="{rel}index.html">概览</a>']
    if cat:
        parts.append(f'<span>/</span><a href="{rel}categories/{cat}.html">{esc(CAT_NAME[cat])}</a>')
    if comp:
        parts.append(f'<span>/</span><span>{esc(comp)}</span>')
    return '<div class="breadcrumb">' + "".join(parts) + "</div>"


def param_table(comp) -> str:
    var_params = {v["param"].split("+")[0] for v in comp["variants"]}
    rows = []
    for p in comp["params"]:
        tag = ""
        if p["required"]:
            tag = '<span class="tag req">必填</span>'
        elif p["name"] in var_params:
            tag = '<span class="tag">有对比</span>'
        doc = p["doc"] or "—"
        rows.append(
            f'<tr id="param-{esc(p["name"])}"><td><span class="param-name">{esc(p["name"])}</span>{tag}</td>'
            f'<td><span class="type">{esc(p["type"])}</span></td>'
            f'<td class="num">{esc(p["default"])}</td>'
            f'<td>{esc(doc)}</td></tr>'
        )
    return f"""<div class="table-wrap"><table>
<thead><tr><th>参数</th><th>类型</th><th>默认值</th><th>含义 / 对版图的影响</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""


def ports_table(comp) -> str:
    if not comp["ports"]:
        return '<div class="note warn">该函数没有对外端口（工具/图元，或端口由调用者自行组织）。</div>'
    rows = []
    for p in comp["ports"]:
        rows.append(
            f'<tr><td><code>{esc(p["name"])}</code></td>'
            f'<td class="num">{p["width"]:g}</td>'
            f'<td class="num">{p["orientation"]:g}°</td>'
            f'<td class="num">({p["center"][0]:g}, {p["center"][1]:g})</td>'
            f'<td class="num">{esc(p["layer"])}</td></tr>'
        )
    return f"""<div class="table-wrap"><table>
<thead><tr><th>端口</th><th>宽度 (µm)</th><th>方向</th><th>中心 (µm)</th><th>层</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>"""


def layer_chips(comp) -> str:
    if not comp["layers"]:
        return '<p class="lead">未检测到多边形图层。</p>'
    chips = []
    for l in comp["layers"]:
        chips.append(
            f'<span class="layer-chip"><i style="background:{l["color"]}"></i>'
            f'{esc(l["name"])} {l["layer"]}/{l["datatype"]}</span>'
        )
    return '<div class="layer-list">' + "".join(chips) + "</div>"


def variant_grid(comp, rel) -> str:
    if not comp["variants"]:
        return ""
    cards = []
    if comp["image"]:
        default_code = next((line.strip() for line in comp["code"].splitlines()
                             if line.strip().startswith("c = ")), f"ap.{comp['name']}()")
        cards.append(f"""<figure class="variant">
  <a class="lightbox v-img" href="{rel}{comp['image']}"><img loading="lazy" src="{rel}{comp['image']}" alt="{esc(comp['name'])} 默认参数"></a>
  <figcaption><strong>默认参数</strong><code>{esc(default_code)}</code></figcaption>
</figure>""")
    for v in comp["variants"]:
        cards.append(f"""<figure class="variant">
  <a class="lightbox v-img" href="{rel}{v['image']}"><img loading="lazy" src="{rel}{v['image']}" alt="{esc(comp['name'])} {esc(v['label'])}"></a>
  <figcaption><strong>{esc(v['label'])}</strong><code>{esc(v['code'])}</code></figcaption>
</figure>""")
    return '<div class="variant-grid">' + "".join(cards) + "</div>"


def component_page(comp, comps) -> str:
    rel = "../"
    body = [f'<div class="topline">{breadcrumb(rel, comp["name"], comp["category"])}'
            '<div class="gh"><a href="../index.html">◀ 返回概览</a></div></div>']
    body.append(f"<h1>{esc(comp['name'])}</h1>")
    body.append(f'<p class="lead">{esc(comp["summary"] or "该器件没有 docstring。")}</p>')
    body.append('<div class="meta-row">')
    body.append(f'<span class="badge blue">{esc(CAT_NAME[comp["category"]])}</span>')
    mp = comp.get("module_path") or comp["module"]
    body.append(f'<span class="badge">模块 '
                f'<a href="../modules.html#{module_anchor(mp)}">{esc(mp)}</a></span>')
    body.append(f'<span class="badge">{len(comp["ports"])} 个端口</span>')
    body.append(f'<span class="badge">尺寸 {esc(fmt_size(comp))}</span>')
    if comp["variants"]:
        body.append(f'<span class="badge green">{len(comp["variants"])} 组参数对比</span>')
    body.append("</div>")

    if comp["note"]:
        body.append(f'<div class="note">{esc(comp["note"])}</div>')
    if comp["error"] and not comp["image"]:
        body.append(f'<div class="note warn">默认参数无法渲染：{esc(comp["error"])}</div>')
    if comp["image"]:
        body.append(f"""<figure class="figure">
  <a class="lightbox" href="{rel}{comp['image']}"><img src="{rel}{comp['image']}" alt="{esc(comp['name'])} 默认版图"></a>
  <figcaption><span>默认参数版图</span><span>bbox {esc(fmt_bbox(comp))}</span><span>{len(comp['ports'])} ports</span></figcaption>
</figure>""")

    body.append('<div class="actions">')
    if comp["gds"]:
        body.append(f'<a class="btn primary" href="{rel}{comp["gds"]}" download>下载 GDS</a>')
    body.append(f'<button class="btn copy-btn" data-code="{esc(comp["code"])}">复制构造代码</button>')
    body.append("</div>")
    body.append(f"<pre><code>{esc(comp['code'])}</code></pre>")

    if comp["name"] in HEATER_3D_LINK:
        hid = HEATER_3D_LINK[comp["name"]]
        body.append(
            '<div class="note green">加热器是叠在波导上的金属层：'
            '<a href="../heaters3d.html?item=' + hid + '">打开交互式 3D 层叠图</a>'
            '（左键旋转、右键/Shift 拖动平移、滚轮缩放，可看层间距）。</div>'
        )

    if comp.get("view3d"):
        body.append('<div class="section-head"><h2>3D 层叠视图</h2></div>')
        body.append('<p class="lead">左键旋转、右键/Shift 拖动平移、滚轮缩放；每一层按实体块显示'
                    '（顶面 + 侧壁，不绘制底面），厚度可以逐层单独调整。'
                    '厚度只用于显示，层叠顺序按图层类型自动排列，不绑定任何具体工艺。</p>')
        body.append('<div class="c3d">'
                    '<div class="c3d-stage"><canvas class="c3d-canvas"></canvas>'
                    '<div class="c3d-hint">左键旋转 · 右键/Shift 拖动平移 · 滚轮缩放 · 双击复位</div></div>'
                    '<aside class="c3d-side">'
                    '<div class="c3d-actions"><label class="h3d-check">'
                    '<input type="checkbox" class="c3d-auto"> 自动旋转</label>'
                    '<button class="btn c3d-reset">重置</button></div>'
                    '<div class="c3d-layers"></div><div class="c3d-meta"></div>'
                    '</aside></div>')
        body.append(f'<script src="{rel}{comp["view3d"]}"></script>')
        body.append(f'<script src="{rel}assets/component3d.js"></script>')

    body.append('<div class="section-head"><h2>参数与可选项</h2></div>')
    body.append('<p class="lead">默认值来自函数签名；说明优先取 docstring，缺失时用通用提示补齐。'
                '带 <span class="tag">有对比</span> 的参数在下方有预渲染的版图对比。</p>')
    body.append(param_table(comp))

    if comp["variants"]:
        body.append('<div class="section-head"><h2>版图对比</h2></div>')
        body.append('<p class="lead">以下图像全部由实际调用该器件、写出 GDS 后渲染；'
                    '同一组参数只改标签所示的选项，其余保持默认。</p>')
        body.append(variant_grid(comp, rel))

    body.append('<div class="section-head"><h2>端口</h2></div>')
    body.append(ports_table(comp))

    body.append('<div class="section-head"><h2>使用图层</h2></div>')
    body.append(layer_chips(comp))

    if comp["doc"]:
        body.append('<details><summary>展开完整 docstring</summary>'
                    f'<pre class="doc">{esc(comp["doc"])}</pre></details>')

    related = [c for c in comps if c["category"] == comp["category"] and c["name"] != comp["name"]][:8]
    if related:
        body.append('<div class="section-head"><h2>同类器件</h2></div><div class="grid auto">')
        for c in related:
            body.append(comp_card(c, rel))
        body.append("</div>")

    return layout(comp["name"], "\n".join(body), rel, active_name=comp["name"],
                  active_cat=comp["category"], desc=comp["summary"], comps=comps)


def comp_card(c, rel) -> str:
    thumb = (f'<img loading="lazy" src="{rel}{c["image"]}" alt="{esc(c["name"])}">'
             if c["image"] else '<span class="type">无渲染</span>')
    meta = f'{len(c["ports"])} ports'
    if c["size"]:
        meta += f' · {c["size"][0]:.1f}×{c["size"][1]:.1f} µm'
    return f"""<a class="comp-card" href="{rel}components/{c["name"]}.html">
  <div class="thumb">{thumb}</div>
  <strong>{esc(c["name"])}</strong>
  <p>{esc(c["summary"] or "—")}</p>
  <div class="card-meta"><span>{esc(meta)}</span></div>
</a>"""


def category_page(cid, comps) -> str:
    rel = "../"
    items = [c for c in comps if c["category"] == cid]
    body = [f'<div class="topline">{breadcrumb(rel, cat=cid)}</div>']
    body.append(f"<h1>{esc(CAT_NAME[cid])}</h1>")
    mods = sorted({(c.get("module_path") or c["module"]).split("/")[0] for c in items})
    body.append(f'<p class="lead">{esc(CAT_DESC[cid])}。共 {len(items)} 个器件，'
                f'涉及模块：{esc(" / ".join(mods))}。</p>')
    body.append('<div class="grid auto">')
    body.append("".join(comp_card(c, rel) for c in items))
    body.append("</div>")
    return layout(CAT_NAME[cid], "\n".join(body), rel, active_cat=cid,
                  desc=CAT_DESC[cid], comps=comps)


def overview_page(comps) -> str:
    rel = ""
    total_params = sum(len(c["params"]) for c in comps)
    total_variants = sum(len(c["variants"]) for c in comps)
    body = [f"""<section class="hero">
  <div class="meta-row"><span class="badge blue">gdsfactory v9</span><span class="badge">Core · Devices · Assemblies · TestStructures · Electrical</span><span class="badge purple">Platforms/SOI 子库</span></div>
  <h1>AIPLPhMTools 版图手册</h1>
  <p class="lead">每一个构造函数的真实版图、端口、参数含义，以及关键可选项的版图对比。
  图像来自实际构建的 GDS，不是示意图。</p>
  <div class="stats">
    <div class="stat"><b>{len(comps)}</b><span>可绘制器件</span></div>
    <div class="stat"><b>{len(MODULE_TREE)}</b><span>顶层模块</span></div>
    <div class="stat"><b>{len(CATEGORIES)}</b><span>功能分类</span></div>
    <div class="stat"><b>{total_params}</b><span>参数条目</span></div>
    <div class="stat"><b>{total_variants}</b><span>参数对比图</span></div>
  </div>
</section>"""]

    body.append('<div class="section-head"><h2>快速开始</h2><a href="guide.html">安装与约定 →</a></div>')
    body.append("""<pre><code>import AIPLPhMTools as ap

# 1) 查看全部可绘制器件
print(ap.list_components())

# 2) 构建一个 Pulley 环（默认参数）
c = ap.RingPulleyT1(RadiusRing=100)
c.write_gds("ring.gds")

# 3) 改一个参数，版图立即变化
c2 = ap.RingPulleyT1(RadiusRing=200, IsAD=False)
c2.write_gds("ring_2port.gds")</code></pre>""")

    body.append('<div class="note"><strong>交互式 3D：</strong>'
                '加热器的波导 / M1 / M2 / 开窗层叠关系可以拖动旋转查看：'
                '<a href="heaters3d.html">打开加热器 3D 层叠图</a>。</div>')
    body.append('<div class="note"><strong>GDS 原位合并：</strong>'
                '两颗 die 叠在同一坐标系时复用同名 PDK cell、避免 <code>$1</code> 副本：'
                '<a href="gdsmerge.html">merge_gds / merge_into_kcl 用法 →</a></div>')
    body.append('<div class="note green"><strong>怎么用这本手册：</strong>'
                '左侧「模块层级」按代码目录（Core / Devices / Assemblies / TestStructures / '
                'Electrical / Platforms/SOI）浏览，下面的分类按功能浏览；器件页先看默认版图，'
                '再看参数表，标有「有对比」的参数展开后有不同取值的版图。所有尺寸单位都是 µm。</div>')

    body.append('<div class="section-head"><h2>按分类浏览</h2></div><div class="grid auto">')
    for cid, cname, cdesc, thumb_name in CATEGORIES:
        items = [c for c in comps if c["category"] == cid]
        thumb = next((c for c in items if c["name"] == thumb_name and c["image"]), None)
        thumb = thumb or next((c for c in items if c["image"]), None)
        img = (f'<img loading="lazy" src="{thumb["image"]}" alt="{esc(cname)}">'
               if thumb else '<span class="type">暂无图像</span>')
        body.append(f"""<a class="comp-card" href="categories/{cid}.html">
  <div class="thumb">{img}</div>
  <strong>{esc(cname)}</strong>
  <p>{esc(cdesc)}</p>
  <div class="card-meta"><span>{len(items)} 个器件</span><span>查看全部 →</span></div>
</a>""")
    body.append("</div>")

    by_path: dict[str, list] = {}
    for c in comps:
        by_path.setdefault(c.get("module_path") or c["module"], []).append(c)
    body.append('<div class="section-head"><h2>按模块浏览</h2>'
                '<a href="modules.html">完整目录与层级 →</a></div><div class="grid auto">')
    for group, gdesc, files in MODULE_TREE:
        n = sum(len(by_path.get(path, [])) for path, _ in files)
        unit = f"{len(files)} 个文件 · {n} 个器件" if n else f"{len(files)} 个文件 · 平台层"
        body.append(f"""<a class="comp-card" href="modules.html#module-{module_anchor(group)[7:]}">
  <div class="thumb"><span class="type">{unit}</span></div>
  <strong>{esc(group)}/</strong>
  <p>{esc(gdesc)}</p>
  <div class="card-meta"><span>{len(files)} 个模块文件</span><span>查看 →</span></div>
</a>""")
    body.append("</div>")

    popular = ["RingPulleyT1", "RaceTrackP", "DMZI", "PMZI", "DBR", "GSGELE",
               "Boomerang", "ExtCavDouRing", "GongCavity", "TCRing", "DifferentHeater", "ViaArray"]
    by_name = {c["name"]: c for c in comps}
    body.append('<div class="section-head"><h2>常用器件</h2><a href="index.html#all">全部器件 →</a></div><div class="grid auto">')
    for n in popular:
        if n in by_name:
            body.append(comp_card(by_name[n], rel))
    body.append("</div>")

    body.append('<div class="section-head" id="all"><h2>全部器件</h2></div><div class="grid auto">')
    for c in comps:
        body.append(comp_card(c, rel))
    body.append("</div>")
    return layout("AIPLPhMTools 版图手册", "\n".join(body), rel, comps=comps,
                  desc="AIPLPhMTools 器件版图、端口与参数对照手册")


def modules_page(comps) -> str:
    rel = ""
    by_path: dict[str, list] = {}
    for c in comps:
        by_path.setdefault(c.get("module_path") or c["module"], []).append(c)

    total_files = sum(len(files) for _, _, files in MODULE_TREE)
    body = [f'<div class="topline">{breadcrumb(rel)}</div>']
    body.append("<h1>模块层级</h1>")
    body.append('<p class="lead">按 <code>AIPLPhMTools</code> 重组后的真实目录组织：'
                '左栏的分类是“按功能浏览”，本页是“按代码模块浏览”。'
                f'共 {len(MODULE_TREE)} 个顶层模块、{total_files} 个模块文件、'
                f'{len(comps)} 个可绘制器件。</p>')
    body.append('<div class="note">旧路径 <code>AIPLPhMTools.GeneralTools.*</code> 与 '
                '<code>AIPLPhMTools.SOITools.*</code> 仍可用，但只是<b>一个版本的兼容 shim</b>；'
                '新代码请使用下表的新路径。SOI 平台的文件不返回 Component，'
                '用法见 <a href="platforms_soi.html">Platforms/SOI 子库</a>。</div>')

    # 目录树
    lines = ["AIPLPhMTools/"]
    for gi, (group, _, files) in enumerate(MODULE_TREE):
        g_last = gi == len(MODULE_TREE) - 1
        n = sum(len(by_path.get(path, [])) for path, _ in files)
        tail = f"{n} 个器件" if n else ("子库，见专页" if group == "Platforms/SOI" else "无独立器件")
        lines.append(f"{'└──' if g_last else '├──'} {group + '/':<30}{tail}")
        for fi, (path, _) in enumerate(files):
            f_last = fi == len(files) - 1
            prefix = "    " if g_last else "│   "
            name = path[len(group) + 1:]
            m = len(by_path.get(path, []))
            tail_file = (f"{m} 个器件" if m
                         else ("见专页" if group == "Platforms/SOI" or path in MODULE_EXTRA_PAGE
                               else "—"))
            lines.append(f"{prefix}{'└──' if f_last else '├──'} {name:<26}{tail_file}")
    body.append(f'<pre><code>{esc(chr(10).join(lines))}</code></pre>')

    for group, desc, files in MODULE_TREE:
        n = sum(len(by_path.get(path, [])) for path, _ in files)
        body.append(f'<div class="section-head" id="module-{module_anchor(group)[7:]}">'
                    f'<h2>{esc(group)}/</h2><span class="type">{n} 个器件</span></div>')
        body.append(f'<p class="lead">{esc(desc)}。</p>')
        rows = []
        for path, fdesc in files:
            items = by_path.get(path, [])
            if items:
                refs = "、".join(
                    f'<a href="components/{esc(c["name"])}.html"><code>{esc(c["name"])}</code></a>'
                    for c in sorted(items, key=lambda x: x["name"].lower()))
            elif group == "Platforms/SOI":
                refs = f'<a href="platforms_soi.html">用法与图层 →</a>'
            elif path in MODULE_EXTRA_PAGE:
                refs = f'<a href="{MODULE_EXTRA_PAGE[path]}">用法 →</a>'
            else:
                refs = '<span class="type">—</span>'
            rows.append(
                f'<tr id="{module_anchor(path)}"><td><code>{esc(path)}</code></td>'
                f'<td>{esc(fdesc)}</td><td>{refs}</td></tr>')
        body.append('<div class="table-wrap"><table><thead><tr>'
                    '<th>文件</th><th>职责</th><th>本页器件</th></tr></thead>'
                    f'<tbody>{"".join(rows)}</tbody></table></div>')

    body.append('<div class="note green">器件页顶部的「模块」徽标会链回本页对应文件；'
                '包入口仍可用 <code>import AIPLPhMTools as ap; ap.list_components()</code> '
                '查看全部器件。</div>')
    return layout("模块层级", "\n".join(body), rel, comps=comps,
                  desc="AIPLPhMTools 重组后的模块目录与器件分布")


def guide_page(comps) -> str:
    rel = ""
    layer_rows = [
        ("WG", "1 / 0", "光学波导（Si / SiN 通用）"),
        ("CPF", "130 / 0", "氮化硅波导层"),
        ("M1", "10 / 0", "金属 1（加热条 / 电极）"),
        ("M2", "4 / 1", "金属 2（高频电极 / 布线）"),
        ("OPEN", "20 / 0", "开窗层（焊盘开口）"),
        ("DT", "51 / 0", "深槽 / 隔离槽"),
        ("TN", "24 / 0", "N 型掺杂"),
        ("TP", "15 / 0", "P 型掺杂"),
        ("VIA", "70 / 0", "M1–M2 过孔"),
        ("V2", "71 / 0", "M2–M3 过孔"),
    ]
    rows = "".join(f"<tr><td><code>{a}</code></td><td class=\"num\">{b}</td><td>{c}</td></tr>"
                   for a, b, c in layer_rows)
    body = [f'<div class="topline">{breadcrumb(rel)}<div class="gh"><a href="index.html">◀ 返回概览</a></div></div>']
    body.append("<h1>快速开始与约定</h1>")
    body.append('<p class="lead">这一页说明安装、目录结构、参数阅读方式和几个容易踩的约定；'
                '器件自身的参数见各器件页。</p>')

    body.append("<h2>安装</h2>")
    body.append("""<pre><code>git clone &lt;repository-url&gt;
cd AIPLPhMTools
pip install -e .

# 依赖：python &gt;= 3.10, gdsfactory &gt;= 9.14, numpy, kfactory, shapely, matplotlib</code></pre>""")
    body.append('<div class="note">本手册的版图图像由 <code>docs/build_site.py</code> 生成；'
                '重新生成只需在包含 <code>AIPLPhMTools</code> 的目录运行 '
                '<code>python AIPLPhMTools/docs/build_site.py</code>。</div>')

    body.append("<h2>目录结构</h2>")
    body.append("""<pre><code>AIPLPhMTools/
├── Core/                # 与工艺无关的底座
│   ├── BasicDefine.py   # 层号接口、截面、直/弯/锥、斜端面、Euler 路径、route_off_grid
│   ├── EulerConnection.py  # 任意角度端口的 Euler 连线
│   ├── SnapMerge.py     # 顶点吸附 / 同层合并（DRC 预处理）
│   ├── LayerStack.py    # LayerDef / LayerStack（手册与 3D 视图）
│   └── GdsMerge.py      # GDS 原位合并：同名 PDK cell 指纹比对 / 复用
├── Devices/             # 单器件：返回带端口的 Component
│   ├── Ring.py / RaceTrack.py
│   ├── CouplerMZI.py / CoupledCavity.py / FeedbackCavity.py
│   ├── DBR.py / DBR_inv.py
│   └── Boomerang.py / GongCavity.py / memyshev.py
├── Assemblies/          # 多器件装配：仍返回 Component
│   ├── ExtCav.py / Isolator.py / WangCavity.py
│   └── MultiRing.py / MultiRaceTrack.py
├── TestStructures/      # 测试/表征结构（TC*）
│   ├── TCRing.py / TCRaceTrack.py / TCCoupledCavity.py
│   └── Coupon.py / TestRow.py
├── Electrical/          # 通用加热器与电极
│   └── Heater.py / ELE.py
├── Platforms/SOI/       # SOI（12 英寸、三层金属）平台子库
│   ├── FabBasic.py / Geometry.py / Routing.py / Electrical.py
│   ├── Ring.py / Spiral.py / Facet.py
│   └── PDKPorts.py / Assembly.py / Audit.py
├── GeneralTools/        # 旧路径兼容 shim（一个版本周期）
├── SOITools/            # 旧路径兼容 shim（一个版本周期）
├── selftest/            # 自检（导入主包时不自动运行）
│   ├── general_tools.py # 通用器件构建/端口/几何检查
│   ├── soitools.py      # SOI 平台几何与层号检查
│   └── run_all.py       # 依次运行两组自检
└── docs/                # 本手册（由 build_site.py 生成）</code></pre>""")
    body.append('<div class="note">网页左侧的 <a href="modules.html"><b>模块层级</b></a> '
                '按这份目录逐文件列出器件；器件页顶部的「模块」徽标也会链回对应文件。'
                '整颗 die 的 GDS 原位合并（复用同名 PDK cell）见 '
                '<a href="gdsmerge.html">GDS 合并</a>。</div>')

    body.append("<h2>参数阅读方式</h2>")
    body.append('<div class="grid two">'
                '<div class="card"><h3>单位</h3><p>所有长度/宽度/间隙/半径均为 µm；角度为度 (°)。端口方向 0° 朝 +x，逆时针为正。</p></div>'
                '<div class="card"><h3>LayerSpec</h3><p>图层既可写 <code>(layer, datatype)</code>，也可用预设 <code>ap.LAYER.WG</code>。每个器件的图层使用情况在器件页底部列出。</p></div>'
                '<div class="card"><h3>HeaterConfig</h3><p>加热器不是单个数字，而是一组配置。用 <code>ap.HeaterConfigClass(TypeHeater="side", WidthHeat=6)</code>，或在默认配置上派生：<code>ap.heaterconfig0.with_changes(TypeHeater="snake")</code>。</p></div>'
                '<div class="card"><h3>None 的含义</h3><p>多数 <code>HeaterConfig=None</code> 表示不画加热器；<code>tin/tout=None</code> 表示使用库内默认 taper。参数表里的默认值以签名原样展示。</p></div>'
                '</div>')
    body.append("""<pre><code>import AIPLPhMTools as ap

# 在默认配置上只改一个字段（不会修改原对象）
cfg = ap.heaterconfig0.with_changes(TypeHeater="side", WidthHeat=6, DeltaHeat=8)
c = ap.RingPulleyT1(HeaterConfig=cfg)

# 显式图层
c = ap.RingPulleyT1(oplayer=ap.LAYER.CPF)   # 画到氮化硅层</code></pre>""")

    body.append("<h2>常用图层</h2>")
    body.append(f'<div class="table-wrap"><table><thead><tr><th>名称</th><th>layer / datatype</th><th>用途</th></tr></thead><tbody>{rows}</tbody></table></div>')
    body.append('<p class="lead">完整层表见 <code>Core/BasicDefine.py</code> 的 <code>LayerMapUserDef</code>。'
                'SOI 平台子库使用另一套层号（600/631/632/…），见 '
                '<a href="platforms_soi.html">Platforms/SOI 子库</a>。</p>')
    body.append("<h2>LayerStack：从设计手册生成</h2>")
    body.append("""<pre><code>stack = ap.LayerStack.from_design_manual(
    "AIPLPhMTools/examples/layer_stack_manual.md",
    section="层号表",
)
print(stack.WG.key, stack.M1.role)</code></pre>""")
    body.append('<div class="note">手册表格只需写“名称 + layer/datatype + 角色 + 显示厚度”；'
                '显示厚度仅用于 3D，不绑定具体工艺。</div>')

    body.append("<h2>自检</h2>")
    body.append("""<pre><code># 依次运行通用器件 + SOI 平台子库
python -m AIPLPhMTools.selftest.run_all

# 或单独运行
python -m AIPLPhMTools.selftest.general_tools
python -m AIPLPhMTools.selftest.soitools</code></pre>""")
    body.append('<div class="note">自检代码位于 <code>AIPLPhMTools/selftest/</code>，'
                '不会在导入主包时自动执行。</div>')

    body.append("<h2>CSV 驱动的 DBR</h2>")
    body.append('<div class="note warn"><strong>CSV 驱动的 DBR：</strong>'
                '<code>DBRFromCsv*</code> 不再内置作者机器路径。请传入 <code>CSVName=...</code>，'
                '或设置环境变量 <code>AIPL_DBR_CSV_DIR</code> 指向 CSV 目录。缺少文件时会给出明确报错。</div>')

    body.append("<h2>函数调用约定</h2>")
    body.append('<ul>'
                '<li>所有公共器件构造函数都返回 <code>gdsfactory.Component</code>；导入包不会创建几何。</li>'
                '<li>组合器件用 <code>connect()</code> 对齐，不在下游手写绝对坐标。</li>'
                '<li>需要 <code>PathHeat</code>、<code>CompEn</code> 的辅助绘制函数在参数表里标为「必填」，'
                '手册用演示输入生成图像。</li>'
                '<li>同一进程内可安全地用不同参数反复构建；cell 缓存按参数自动区分。</li>'
                '</ul>')
    return layout("快速开始与约定", "\n".join(body), rel, comps=comps)


def gdsmerge_page(comps) -> str:
    """GDS 原位合并工具页（Core/GdsMerge.py）。"""
    rel = ""
    from AIPLPhMTools.Core import GdsMerge as gm

    api = [
        (gm.merge_gds, "纯 GDS → GDS：把 B 原位合并进 A，返回 MergeReport。"),
        (gm.merge_into_kcl, "把外部 GDS 读进已有 KCLayout / kdb.Layout，返回顶层 cell。"),
        (gm.find_conflicts, "只体检不合并：列出同名 cell 中内容一致 / 不一致的清单。"),
        (gm.cell_signature, "计算单个 cell 的内容指纹（bbox + 各层图形 + 实例变换）。"),
    ]
    rows, sig_lines = [], []
    for fn, desc in api:
        try:
            sig = str(inspect.signature(fn)).replace("'", "")
        except (TypeError, ValueError):
            sig = "(...)"
        sig_lines.append(textwrap.fill(f"{fn.__name__}{sig}", width=100,
                                       subsequent_indent="    ",
                                       break_long_words=False,
                                       break_on_hyphens=False))
        rows.append(f"<tr><td><code>{esc(fn.__name__)}</code></td>"
                    f"<td>{esc(desc)}</td></tr>")

    body = [f'<div class="topline">{breadcrumb(rel)}'
            '<div class="gh"><a href="index.html">◀ 返回概览</a></div></div>']
    body.append("<h1>GDS 原位合并</h1>")
    body.append('<p class="lead">把两颗 die 叠在同一坐标系里时，复用同名 PDK cell，'
                '而不是产生 <code>$1</code> / <code>_1</code> 副本。'
                '源码在 <code>AIPLPhMTools/Core/GdsMerge.py</code>，'
                '顶层可直接 <code>from AIPLPhMTools import merge_gds</code>。'
                '模块归属见 <a href="modules.html#module-Core-GdsMerge-py">模块层级 → Core/GdsMerge.py</a>。</p>')

    body.append('<div class="note"><strong>为什么需要：</strong>GDS 里的 cell 只有名字没有 ID。'
                '两颗 die 都带 <code>GC_Focus_C</code> / <code>WG_TRACE_13</code> 这类 PDK 宏时，'
                '默认读入策略会把后读的改名成 <code>GC_Focus_C$1</code>，层级和后续 LVS/DRC 都会变乱。'
                '本模块先比对同名 cell 的内容，再决定复用、报错还是改名。</div>')

    body.append("<h2>两种入口</h2>")
    body.append('<div class="table-wrap"><table><thead><tr><th>入口</th><th>适用场景</th>'
                '<th>返回</th></tr></thead><tbody>'
                '<tr><td><code>merge_gds(A, B, out, ...)</code></td>'
                '<td>两个 GDS 文件直接合并；可 <code>dry_run</code> 只体检</td>'
                '<td><code>MergeReport</code>（或 <code>(layout, report)</code>）</td></tr>'
                '<tr><td><code>merge_into_kcl(kcl, path, ...)</code></td>'
                '<td>在 gdsfactory / kfactory 构建流程里读外部宏</td>'
                '<td>读入文件的顶层 cell</td></tr>'
                '</tbody></table></div>')

    body.append("<h2>先体检，再合并</h2>")
    body.append("""<pre><code>from AIPLPhMTools import find_conflicts, merge_gds

rep = find_conflicts("left.gds", "right.gds")
print(rep.shared, rep.clashing)      # 同名且一致 / 同名但内容不同

if not rep.clashing:
    rep = merge_gds("left.gds", "right.gds", "merged.gds",
                    union_top="TOP")     # 新建顶层，把两边顶层放在 (0,0)
    print(rep)                       # cell 数、顶层、bbox、被改名的 cell</code></pre>""")

    body.append("<h2>在 gdsfactory 里读 PDK 宏</h2>")
    body.append("""<pre><code>import gdsfactory as gf
from AIPLPhMTools import merge_into_kcl

c = gf.Component("merged")
top = merge_into_kcl(c.kcl, "pdk_macro.gds")
c &lt;&lt; top                         # 直接引用；同名 PDK cell 不会被改名
c.write_gds("merged.gds")</code></pre>""")
    body.append('<div class="note warn"><strong>不要用 <code>gf.import_gds</code> 做这件事：</strong>'
                '它会先读进临时 kcl，再把顶层 cell 拷进目标 kcl；拷贝那一步不受 '
                '<code>skip_new_cells</code> 控制，同名 PDK 宏照样会被改名。</div>')

    body.append("<h2>冲突策略</h2>")
    body.append('<div class="table-wrap"><table><thead><tr><th>情况</th><th>默认行为</th>'
                '<th>可选处理</th></tr></thead><tbody>'
                '<tr><td>同名且内容一致</td><td><code>SkipNewCell</code>：复用已有 cell，不产生 <code>$1</code></td>'
                '<td>—</td></tr>'
                '<tr><td>同名但内容不同</td><td><code>on_conflict="error"</code>：直接抛错</td>'
                '<td><code>on_conflict="rename"</code> 交给 KLayout 改名；<br>'
                '<code>prefix="HJH_"</code> 给 B 的所有 cell 加前缀</td></tr>'
                '<tr><td>需要一个新的总顶层</td><td>不创建</td>'
                '<td><code>union_top="TOP"</code>：把 A/B 顶层都放在 (0,0)</td></tr>'
                '</tbody></table></div>')

    body.append("<h2>内容指纹</h2>")
    body.append('<p class="lead">复用前会比较 <code>cell_signature</code>：bbox + 每层 '
                '（合并后图形个数、面积）+ 实例（cell 名、位移、角度）。'
                '只比较<b>版图内容</b>，不比较 PDK 版本；如果两边是不同版本的同名宏，'
                '请用 <code>prefix</code> 明确隔离。</p>')

    body.append("<h2>API</h2>")
    body.append(f'<pre><code>{esc(chr(10).join(sig_lines))}</code></pre>')
    body.append(f'<div class="table-wrap"><table><thead><tr><th>函数</th><th>作用</th>'
                f'</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    body.append('<div class="note green"><code>MergeReport</code> 的 <code>ok</code> 属性'
                '只有在“没有内容冲突、也没有 cell 被改名”时才为 <code>True</code>；'
                '适合在构建脚本里做交付前门禁。</div>')

    return layout("GDS 原位合并", "\n".join(body), rel, comps=comps,
                  desc="AIPLPhMTools GDS 原位合并：PDK cell 指纹比对、复用与冲突报告")


def platforms_soi_page(comps) -> str:
    rel = ""
    from AIPLPhMTools.Platforms import SOI as soi

    funcs = [
        ("Platforms/SOI/Geometry.py", "Route", "切线连续的走线构造器：straight / turn / s_bend"),
        ("Platforms/SOI/Routing.py", "add_si_route", "Si 走线：芯层 600/1 + 10 µm 开窗 600/10"),
        ("Platforms/SOI/Routing.py", "add_sin_route",
         "SiN 走线：芯 + 631/10、632/10、600/10 开窗 + SINOP"),
        ("Platforms/SOI/Routing.py", "add_sin_route_taper",
         "SiN 宽度过渡（环总线 / spiral 总线 → 单模）"),
        ("Platforms/SOI/Routing.py", "add_si_link",
         "两个 Si 端口之间自动选直线 / S 弯 / 掉头 C 形"),
        ("Platforms/SOI/Geometry.py", "add_annulus", "圆弧环带（TiN 环形加热器、金属环）"),
        ("Platforms/SOI/Electrical.py", "via_array", "过孔阵列"),
        ("Platforms/SOI/Electrical.py", "add_bond_pad",
         "探针焊盘；landing='M1'/'M2'/'M3' 只画本端需要的落点"),
        ("Platforms/SOI/Electrical.py", "add_heat_landing", "TiN 加热器落点"),
        ("Platforms/SOI/Ring.py", "RingPulley", "单侧 pulley 耦合环（需要 PDK 宏目录）"),
        ("Platforms/SOI/Ring.py", "RaceTrackPulley",
         "跑道腔，弯段 pulley 耦合（需要 PDK 宏目录）"),
        ("Platforms/SOI/Spiral.py", "centerline", "Spiral：闭合双螺旋腔中心线"),
        ("Platforms/SOI/Audit.py", "GdsAudit", "GDS → shapely：并集、连通网、线宽与断言"),
    ]
    rows = []
    for module, name, fallback in funcs:
        obj = getattr(soi, name, None)
        doc = clean_doc(inspect.getdoc(obj)) if obj else ""
        desc = summary_of(doc, 160) or fallback
        rows.append(f"<tr><td><code>{esc(module)}</code></td>"
                    f"<td><code>{esc(name)}</code></td><td>{esc(desc)}</td></tr>")

    layer_rows = []
    for n in ("SIWG", "SIN", "SIN3", "TIN", "M1", "M2", "M3", "V1", "V2", "RV", "ALPAD", "COVER", "SINOP"):
        v = getattr(soi, n, None)
        if v:
            layer_rows.append(f"<tr><td><code>{n}</code></td><td class=\"num\">{v[0]} / {v[1]}</td></tr>")

    body = [f'<div class="topline">{breadcrumb(rel)}<div class="gh"><a href="index.html">◀ 返回概览</a></div></div>']
    body.append("<h1>Platforms / SOI 子库</h1>")
    body.append('<p class="lead">SOI 12 英寸平台（220 nm Si + 双层 SiN + TiN + M1/M2/M3）'
                '的独立命名空间子库，源码位于 <code>AIPLPhMTools/Platforms/SOI/</code>。'
                '层号与主库不同，必须显式导入：'
                '<code>import AIPLPhMTools.Platforms.SOI as soi</code>。'
                '层级关系见 <a href="modules.html#module-Platforms-SOI">模块层级 → Platforms/SOI</a>。</p>')
    body.append('<div class="note">这是平台层（FabBasic / Routing / Geometry / Electrical / Ring / '
                'Spiral / Facet / PDKPorts / Assembly / Audit），与 <code>Devices/</code> 的通用器件分开。'
                '绘图函数大多<b>不返回</b> Component，而是把几何画进你传入的 <code>c</code> 里；'
                '这与主库“函数返回器件”的约定不同。下面演示图由 '
                '<code>add_si_route / add_sin_route / add_annulus / add_bond_pad</code> 组合而成。</div>')

    body.append('<div class="grid two">')
    for fname, cap in (("soi_routes.png", "Si 与 SiN 走线（含开窗与 SINOP）"),
                       ("soi_pad.png", "TiN 环形加热器 + M2 landing 焊盘")):
        if (PLATFORMS_SOI_IMG / fname).exists():
            body.append(f"""<figure class="figure"><a class="lightbox" href="assets/platforms_soi/{fname}">
<img src="assets/platforms_soi/{fname}" alt="{esc(cap)}"></a><figcaption>{esc(cap)}</figcaption></figure>""")
    body.append("</div>")

    body.append("<h2>绘图函数</h2>")
    body.append(f'<div class="table-wrap"><table><thead><tr><th>模块</th><th>函数</th><th>作用</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    body.append("<h2>SOI 图层</h2>")
    body.append(f'<div class="table-wrap"><table><thead><tr><th>名称</th><th>layer / datatype</th></tr></thead><tbody>{"".join(layer_rows)}</tbody></table></div>')
    body.append("""<h2>最小示例</h2>
<pre><code>import gdsfactory as gf
import AIPLPhMTools.Platforms.SOI as soi

c = gf.Component("demo")
p = soi.Route(0, 0, 0).straight(100).turn(-90, soi.R_SI).straight(80)
soi.add_si_route(c, p.pts)

q = soi.Route(0, 60, 0).straight(60).s_bend(-30, soi.R_SIN).straight(40)
soi.add_sin_route(c, q.pts)

soi.add_bond_pad(c, 60, -60, size=60, cover=40, landing="M2")
c.write_gds("soi_demo.gds")</code></pre>""")
    body.append('<div class="note warn">用到 <code>soi.pdk()</code> / <code>RingPulley</code> 的 PDK 宏前，'
                '先 <code>soi.set_pdk_dir(".../gdsPDK")</code> 或设置环境变量 '
                '<code>SOI_PDK_DIR</code>。</div>')
    return layout("Platforms / SOI 子库", "\n".join(body), rel, comps=comps)


# ---------------------------------------------------------------------------
# SOI 演示图
# ---------------------------------------------------------------------------
def build_platforms_soi_images():
    from AIPLPhMTools.Platforms import SOI as soi

    # 1) Si + SiN 走线
    c = gf.Component("soi_routes_demo")
    p = soi.Route(0, 0, 0).straight(160).turn(-90, soi.R_SI).straight(80)
    soi.add_si_route(c, p.pts)
    q = soi.Route(0, 130, 0).straight(80).s_bend(-40, soi.R_SIN).straight(60)
    soi.add_sin_route(c, q.pts)
    r = render_component(c, PLATFORMS_SOI_IMG / "soi_routes.png", palette=SOI_PALETTE)
    print("  soi routes", "ok" if r else "empty")

    # 2) TiN 环 + 焊盘
    c2 = gf.Component("soi_pad_demo")
    soi.add_annulus(c2, 320, 60, 90, 92, 0, 360, soi.TIN)
    soi.add_bond_pad(c2, 540, 60, size=60, cover=40, landing="M2")
    r2 = render_component(c2, PLATFORMS_SOI_IMG / "soi_pad.png", palette=SOI_PALETTE)
    print("  soi pad", "ok" if r2 else "empty")


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def heaters3d_page(data, comps) -> str:
    rel = ""
    body = [f'<div class="topline">{breadcrumb(rel)}<div class="gh"><a href="heaters3d.html">◀ 加热器 3D</a></div></div>']
    body.append("<h1>加热器 3D 层叠图</h1>")
    body.append('<p class="lead">拖动旋转、滚轮缩放、双击复位；每一层显示顶面与侧壁'
                '（不绘制底面，避免反射造成重复层错觉）。层与层之间的 z 间距被夸张显示，'
                '用来观察“波导 / M1 / M2 / 开窗”的上下关系；厚度只是显示参数。</p>')
    body.append('<div class="note">3D 数据由真实 GDS 多边形生成：环/加热条保留孔洞，'
                'VIA 阵列过密时在 3D 中省略。下面的器件选择来自 DifferentHeater 与环形加热器。</div>')

    body.append('<div class="h3d-layout">')
    body.append('<div class="h3d-list">')
    for key, item in data.items():
        first = item["layers"][0] if item["layers"] else {"color": "#64748b"}
        names = " · ".join(l["name"] for l in item["layers"])
        body.append(
            f'<button class="h3d-item" data-id="{key}">'
            f'<span class="h3d-dot" style="background:{first["color"]}"></span>'
            f'<span><strong>{esc(item["title"])}</strong><small>{esc(names)}</small></span>'
            f'</button>'
        )
    body.append("</div>")

    body.append('<div class="h3d-main">')
    body.append('<div class="h3d-stage"><canvas id="h3d-canvas"></canvas>'
                '<div class="h3d-hint">拖动旋转 · 滚轮缩放 · 双击复位</div></div>')
    body.append('<div class="h3d-controls">'
                '<label class="h3d-check"><input type="checkbox" id="h3d-auto"> 自动旋转</label>'
                '<label class="h3d-range">层间距 <input type="range" id="h3d-explode" '
                'min="0.5" max="2.5" step="0.1" value="1.0"></label>'
                '<button class="btn" id="h3d-reset">重置视角</button>'
                '<span class="h3d-zoom">滚轮缩放</span></div>')
    body.append('<div class="h3d-info" id="h3d-info"></div>')
    body.append('<div class="h3d-legend" id="h3d-legend"></div>')
    body.append("</div></div>")
    body.append('<script src="assets/heaters3d-data.js"></script>')
    body.append('<script src="assets/heaters3d.js"></script>')
    return layout("加热器 3D 层叠图", "\n".join(body), rel, comps=comps,
                  desc="AIPLPhMTools 加热器层叠结构的交互式 3D 预览")


def main() -> int:
    print("Building AIPLPhMTools handbook ...")
    comps = build_all()
    heater3d = build_heater_3d()
    print(f"components: {len(comps)}, 3D heaters: {len(heater3d)}")

    (HERE / "index.html").write_text(overview_page(comps), encoding="utf-8")
    (HERE / "guide.html").write_text(guide_page(comps), encoding="utf-8")
    (HERE / "modules.html").write_text(modules_page(comps), encoding="utf-8")
    (HERE / "gdsmerge.html").write_text(gdsmerge_page(comps), encoding="utf-8")
    (HERE / "heaters3d.html").write_text(heaters3d_page(heater3d, comps), encoding="utf-8")
    (HERE / ".nojekyll").write_text("", encoding="utf-8")

    for comp in comps:
        (HERE / "components" / f"{comp['name']}.html").write_text(
            component_page(comp, comps), encoding="utf-8")
    for cid, _, _, _ in CATEGORIES:
        (HERE / "categories" / f"{cid}.html").write_text(
            category_page(cid, comps), encoding="utf-8")

    build_platforms_soi_images()
    (HERE / "platforms_soi.html").write_text(platforms_soi_page(comps), encoding="utf-8")
    (HERE / "soitools.html").write_text(
        """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>已迁移到 Platforms / SOI</title>
<meta http-equiv="refresh" content="0; url=platforms_soi.html">
<link rel="canonical" href="platforms_soi.html"></head><body>
<p>本页已迁移到 <a href="platforms_soi.html">Platforms / SOI 子库</a>。</p>
</body></html>""", encoding="utf-8")

    print(f"written: {len(comps)} component pages, {len(CATEGORIES)} category pages, "
          f"modules + gdsmerge + platforms_soi")
    print("open: AIPLPhMTools/docs/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
