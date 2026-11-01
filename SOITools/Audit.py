"""GDS 版图审计：把版图转成 shapely 几何，并提供通用量测与断言。

设计验证脚本（连接关系、层叠、线宽、间隙）都建立在同一套基础操作上：

* ``GdsAudit`` —— 读入 GDS、展平、按层取多边形；
* ``polygon_of`` —— gdsfactory 的 KLayout 多边形 -> shapely Polygon（um）；
* ``union_layer`` —— 同层合并；
* ``nets`` —— 把多部件几何拆成独立多边形（即彼此断开的网络）；
* ``width_v`` / ``width_h`` —— 在一点附近测竖直 / 水平截线宽度；
* ``net_at`` / ``on`` —— 按坐标查找网络 / 判断点是否落在网络上；
* ``check`` —— 打印 PASS/FAIL 并累计失败项。

所有坐标单位为 um。
"""

from __future__ import annotations

from collections.abc import Iterable

import gdsfactory as gf
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union


def polygon_of(p) -> Polygon:
    """gdsfactory / KLayout 多边形 -> shapely Polygon（nm -> um）。"""
    hull = [(pt.x / 1000.0, pt.y / 1000.0) for pt in p.each_point_hull()]
    holes = [[(pt.x / 1000.0, pt.y / 1000.0) for pt in p.each_point_hole(i)]
             for i in range(p.holes())]
    return Polygon(hull, holes)


def load_polygons(gds_path: str) -> dict:
    """读入 GDS 并返回 {layer tuple: [KLayout polygon, ...]}。"""
    c = gf.import_gds(gds_path)
    c.flatten()
    return c.get_polygons(by="tuple")


def union_layer(polys: dict, layer) -> Polygon:
    """合并一层的所有多边形；空层返回空 Polygon。"""
    gs = [polygon_of(p) for p in polys.get(layer, [])]
    return unary_union(gs) if gs else Polygon()


def nets(geom):
    """把 MultiPolygon / GeometryCollection 拆成独立 Polygon 列表。"""
    if geom.is_empty:
        return []
    if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
        return [g for g in geom.geoms if g.geom_type == "Polygon"]
    return [geom]


def width_v(g, x: float, y: float, half: float = 2.5) -> float:
    """竖直线段 (x, y-half)..(x, y+half) 与几何相交的最长长度。"""
    inter = g.intersection(LineString([(x, y - half), (x, y + half)]))
    return max((q.length for q in getattr(inter, "geoms", [inter])),
               default=0.0)


def width_h(g, x: float, y: float, half: float = 2.5) -> float:
    """水平线段 (x-half, y)..(x+half, y) 与几何相交的最长长度。"""
    inter = g.intersection(LineString([(x - half, y), (x + half, y)]))
    return max((q.length for q in getattr(inter, "geoms", [inter])),
               default=0.0)


def net_at(components: Iterable[Polygon], x: float, y: float,
           tol: float = 0.02):
    """返回包含 / 最靠近 (x, y) 的网络，找不到返回 None。"""
    p = Point(x, y)
    for g in components:
        if g.buffer(0.001).contains(p) or g.distance(p) < tol:
            return g
    return None


def on(g, x: float, y: float) -> bool:
    """点 (x, y) 是否落在网络 ``g`` 上（1 nm 容差）。"""
    return g is not None and (g.buffer(0.001).contains(Point(x, y))
                              or g.distance(Point(x, y)) < 1e-3)


def check(name: str, ok: bool, detail: str = "") -> bool:
    """打印一条断言结果并返回 ``ok``（供模块级脚本累计失败项）。"""
    print(("  PASS  " if ok else "  FAIL  ") + name
          + (f"  [{detail}]" if detail else ""))
    return ok


class GdsAudit:
    """一次读入 GDS，缓存多边形并提供便捷方法。

    ``check`` 会把失败项累计到 ``self.fails``；``report`` 打印汇总并
    返回进程退出码。
    """

    def __init__(self, gds_path: str):
        self.path = gds_path
        self.c = gf.import_gds(gds_path)
        self.c.flatten()
        self.polys = self.c.get_polygons(by="tuple")
        self.fails: list[str] = []

    def U(self, layer) -> Polygon:
        """合并一层的多边形。"""
        return union_layer(self.polys, layer)

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        """打印 PASS/FAIL 并累计失败项。"""
        check(name, ok, detail)
        if not ok:
            self.fails.append(name)

    def report(self, passed_msg: str) -> int:
        """打印汇总；全部通过返回 0，否则返回 1。"""
        print("\n== summary ==")
        if self.fails:
            print(f"FAILED: {len(self.fails)} check(s)")
            for f in self.fails:
                print("  -", f)
            return 1
        print(passed_msg)
        return 0
