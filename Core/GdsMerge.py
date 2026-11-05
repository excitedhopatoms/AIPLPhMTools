"""两个 GDS 的「原位」合并：同名的 PDK cell 复用而不是被改名。

为什么需要
----------
GDS 里 cell 只有**名字**没有 ID。把两颗 die 叠在同一坐标系里（原位合并）时，
两边都会带 ``GC_Focus_C`` / ``WG_TRACE_13`` 这类 PDK 宏；默认策略会把后读进来
的那个改名成 ``GC_Focus_C$1``（kfactory 里是 ``..._1``），层级一下就乱了。

本模块的做法：**先比对同名 cell 的内容，再决定合并策略**

* 内容一致（同一套 PDK 宏）→ ``SkipNewCell``：复用已有 cell，不产生 ``$1``；
* 内容不一致 → 默认抛错（否则会把两个不同器件悄悄并成一个），
  也可以 `on_conflict="rename"` 交给 KLayout 改名，或 `prefix="HJH_"` 给
  后一个文件的所有 cell 加前缀。

两种入口
--------
``merge_gds(A, B, out, ...)``
    纯 GDS → GDS。返回 :class:`MergeReport`（同名清单、cell 数、顶层、bbox）。
``merge_into_kcl(kcl, path, ...)``
    把外部 GDS 读进**已经存在的** kfactory ``KCLayout``（gdsfactory 组件构建
    流程里用），返回它的顶层 cell。注意不要用 ``gf.import_gds``：它先读进
    临时 kcl、再拷顶层 cell，拷贝那一步不受 ``skip_new_cells`` 控制。

注意
----
``SkipNewCell`` 是「盲跳」——不比对内容就会悄悄并错，所以本模块在复用前一定
先做 :func:`cell_signature` 比对（bbox + 每层(个数, 面积) + 实例变换）。
它只保证**版图内容**一致；如果两边用的是不同版本的同名 PDK 宏，请用 ``prefix``。
"""
from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import klayout.db as kdb

__all__ = [
    "MergeReport",
    "cell_signature",
    "merge_gds",
    "merge_into_kcl",
    "find_conflicts",
]


# --------------------------------------------------------------------------- #
# 报告
# --------------------------------------------------------------------------- #
@dataclass
class MergeReport:
    """一次合并的体检结果（也用于 dry-run）。"""

    a: str = ""
    b: str = ""
    shared: list[str] = field(default_factory=list)     # 同名且内容一致
    clashing: list[str] = field(default_factory=list)   # 同名但内容不同
    cells_before: int = 0
    cells_after: int = 0
    tops: list[str] = field(default_factory=list)
    bbox_um: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    renamed: list[str] = field(default_factory=list)    # 合并后带 $ 的名字

    @property
    def ok(self) -> bool:
        """没有内容冲突、也没有被改名的 cell 才算干净。"""
        return not self.clashing and not self.renamed

    def __str__(self) -> str:
        b = self.bbox_um
        return (f"A {self.a}: cells {self.cells_before}\n"
                f"B {self.b}\n"
                f"同名 {len(self.shared) + len(self.clashing)} 个："
                f"一致 {len(self.shared)}，不一致 {len(self.clashing)}\n"
                f"合并后 {self.cells_after} 个 cell，顶层 {self.tops}，"
                f"bbox ({b[0]:.3f},{b[1]:.3f};{b[2]:.3f},{b[3]:.3f})，"
                f"被改名 {self.renamed or '无'}")


# --------------------------------------------------------------------------- #
# 指纹 / 冲突
# --------------------------------------------------------------------------- #
def cell_signature(cell: kdb.Cell, layout: kdb.Layout) -> tuple:
    """cell 内容指纹：bbox + 每层 (合并后个数, 面积) + 实例 (名字, 位移, 角度)。

    只比较**内容**，不比较名字，用来判断两个同名 cell 能不能复用。
    """
    layers = []
    for li in layout.layer_indexes():
        sh = cell.shapes(li)
        if sh.size() == 0:
            continue
        reg = kdb.Region(sh).merged()
        info = layout.get_info(li)
        layers.append((info.layer, info.datatype,
                       len(reg), round(reg.area() / 1e6, 6)))
    insts = []
    for inst in cell.each_inst():
        t = inst.cplx_trans
        insts.append((inst.cell.name, t.disp.x, t.disp.y, int(t.angle) % 4))
    insts.sort()
    b = cell.dbbox()
    return (round(b.left, 4), round(b.bottom, 4), round(b.right, 4),
            round(b.top, 4), tuple(sorted(layers)), tuple(insts))


def find_conflicts(path_a: str | Path, path_b: str | Path) -> MergeReport:
    """只体检、不合并：返回两个 GDS 里同名 cell 的一致/不一致清单。"""
    la = kdb.Layout()
    la.read(str(path_a))
    lb = kdb.Layout()
    lb.read(str(path_b))
    names_a = {c.name for c in la.each_cell()}
    names_b = {c.name for c in lb.each_cell()}
    shared, clash = [], []
    for nm in sorted(names_a & names_b):
        if cell_signature(la.cell(nm), la) == cell_signature(lb.cell(nm), lb):
            shared.append(nm)
        else:
            clash.append(nm)
    b = _layout_bbox(la)
    return MergeReport(
        a=Path(path_a).name, b=Path(path_b).name,
        shared=shared, clashing=clash,
        cells_before=len(names_a), cells_after=len(names_a),
        tops=[c.name for c in la.top_cells()],
        bbox_um=(b.left, b.bottom, b.right, b.top))


# --------------------------------------------------------------------------- #
# 文件 → 文件
# --------------------------------------------------------------------------- #
def _layout_bbox(layout: kdb.Layout) -> kdb.DBox:
    """所有顶层 cell 的并集 bbox（µm）。"""
    boxes = [c.dbbox() for c in layout.top_cells()]
    if not boxes:
        return kdb.DBox()
    return kdb.DBox(min(b.left for b in boxes), min(b.bottom for b in boxes),
                    max(b.right for b in boxes), max(b.top for b in boxes))


def _rename_all(layout: kdb.Layout, prefix: str) -> None:
    for c in list(layout.each_cell()):
        c.name = prefix + c.name


def merge_gds(path_a: str | Path, path_b: str | Path,
              out: str | Path | None = None, *,
              prefix: str | None = None,
              union_top: str | None = None,
              on_conflict: str = "error",
              dry_run: bool = False,
              return_layout: bool = False):
    """把 ``B`` 原位合并进 ``A``（坐标不动），同名 PDK cell 不重复。

    参数
    ----
    path_a, path_b : 两个 GDS；A 的 cell 名优先保留。
    out            : 输出 GDS。``dry_run=False`` 且没给 ``return_layout`` 时必填。
    prefix         : 给 B 的所有 cell 加前缀（内容不同又必须合时用）。
    union_top      : 新建一个顶层 cell（这个名字），把 A/B 的顶层都放在 (0,0)。
    on_conflict    : ``"error"``（默认，内容不同就抛错）/
                     ``"rename"``（交给 KLayout 改名 ``$1``）。
    dry_run        : 只体检，不写文件。
    return_layout  : 返回 ``(layout, report)``，方便调用方继续处理。

    返回
    ----
    :class:`MergeReport`，或 ``(kdb.Layout, MergeReport)``。
    """
    pa, pb = Path(path_a), Path(path_b)
    for p in (pa, pb):
        if not p.is_file():
            raise FileNotFoundError(p)
    if on_conflict not in ("error", "rename"):
        raise ValueError("on_conflict 只支持 'error' / 'rename'")

    la = kdb.Layout()
    la.read(str(pa))
    lb = kdb.Layout()
    lb.read(str(pb))
    tops_a = [c.name for c in la.top_cells()]
    tops_b = [c.name for c in lb.top_cells()]

    names_a = {c.name for c in la.each_cell()}
    names_b = {c.name for c in lb.each_cell()}
    shared, clash = [], []
    for nm in sorted(names_a & names_b):
        if cell_signature(la.cell(nm), la) == cell_signature(lb.cell(nm), lb):
            shared.append(nm)
        else:
            clash.append(nm)

    b = _layout_bbox(la)
    rep = MergeReport(a=pa.name, b=pb.name, shared=shared, clashing=clash,
                      cells_before=len(names_a), cells_after=len(names_a),
                      tops=tops_a,
                      bbox_um=(b.left, b.bottom, b.right, b.top))
    if dry_run:
        return rep
    if clash and on_conflict == "error" and not prefix:
        raise ValueError(
            f"{pb.name}: 这些 cell 与 {pa.name} 同名但内容不同，不能复用："
            f"{clash[:6]}。请确认 PDK 版本；或 prefix='XXX_'；"
            f"或 on_conflict='rename'。")

    # B 需要加前缀时先落成临时 GDS；否则直接读
    src_b = pb
    tmp = None
    if prefix:
        _rename_all(lb, prefix)
        tmp = Path(tempfile.mkdtemp()) / "b_prefixed.gds"
        lb.write(str(tmp))
        src_b = tmp

    opt = kdb.LoadLayoutOptions()
    opt.cell_conflict_resolution = (
        kdb.LoadLayoutOptions.CellConflictResolution.SkipNewCell
        if not clash else
        kdb.LoadLayoutOptions.CellConflictResolution.RenameCell)
    la.read(str(src_b), opt)
    if tmp is not None:
        tmp.unlink(missing_ok=True)

    if union_top:
        top = la.create_cell(union_top)
        for nm in tops_a + [prefix + t if prefix else t for t in tops_b]:
            c = la.cell(nm)
            if c is not None:
                top.insert(kdb.DCellInstArray(c.cell_index(), kdb.DTrans()))

    rep.cells_after = len(list(la.each_cell()))
    rep.tops = [c.name for c in la.top_cells()]
    rep.renamed = [c.name for c in la.each_cell() if "$" in c.name]
    b = _layout_bbox(la)
    rep.bbox_um = (b.left, b.bottom, b.right, b.top)

    if out is not None:
        la.write(str(out))
    elif not return_layout:
        raise ValueError("要么给 out=输出路径，要么 return_layout=True")
    return (la, rep) if return_layout else rep


# --------------------------------------------------------------------------- #
# 读进已有 kcl（gdsfactory / kfactory 流程）
# --------------------------------------------------------------------------- #
def merge_into_kcl(kcl: Any, path: str | Path, *,
                   on_conflict: str = "error",
                   prefix: str | None = None):
    """把外部 GDS 读进**已有** kcl，同名 cell 复用（不产生 ``$1``）。

    ``kcl`` 可以是 kfactory 的 ``KCLayout``（``component.kcl``），也可以是
    ``klayout.db.Layout``。返回读入文件的顶层 cell（KCLayout 时是 KCell，
    可以直接 ``total << it``）。

    与 ``gf.import_gds`` 的区别：后者先读进临时 kcl、再把顶层 cell 拷进来，
    拷贝那一步不受 ``skip_new_cells`` 控制，同名 PDK 宏照样被改名。
    """
    if on_conflict not in ("error", "rename"):
        raise ValueError("on_conflict 只支持 'error' / 'rename'")
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(p)

    ly = getattr(kcl, "layout", kcl)          # KCLayout -> 底层 kdb.Layout
    if not isinstance(ly, kdb.Layout):
        raise TypeError(f"kcl 需要 KCLayout 或 kdb.Layout，实际 {type(kcl)}")

    src = kdb.Layout()
    src.read(str(p))
    tops = [c.name for c in src.top_cells()]
    if len(tops) != 1:
        raise ValueError(f"{p.name}: 需要单顶层，实际 {tops}")
    top_name = tops[0]

    if prefix:
        _rename_all(src, prefix)
        top_name = prefix + top_name

    have = {c.name for c in ly.each_cell()}
    clash = []
    for c in src.each_cell():
        if c.name in have and \
                cell_signature(c, src) != cell_signature(ly.cell(c.name), ly):
            clash.append(c.name)
    if clash and on_conflict == "error":
        raise ValueError(
            f"{p.name}: 这些 cell 与已有版图同名但内容不同，不能复用："
            f"{clash[:6]}；请对齐 PDK 版本，或改用 merge_gds(prefix=...).")

    opt = kdb.LoadLayoutOptions()
    opt.cell_conflict_resolution = (
        kdb.LoadLayoutOptions.CellConflictResolution.SkipNewCell
        if not clash else
        kdb.LoadLayoutOptions.CellConflictResolution.RenameCell)

    src_path = p
    tmp = None
    if prefix:
        tmp = Path(tempfile.mkdtemp()) / "prefixed.gds"
        src.write(str(tmp))
        src_path = tmp
    try:
        kcl.read(str(src_path), options=opt) if hasattr(kcl, "read") \
            else ly.read(str(src_path), opt)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return kcl[top_name] if hasattr(kcl, "__getitem__") else ly.cell(top_name)
