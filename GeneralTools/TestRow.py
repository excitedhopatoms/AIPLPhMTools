"""测试结构“排一行”的统一框架。

背景
----
``TCRingT1`` 负责画**单个** ring coupon（环 + 输入/输出 taper + 绕线 + 可选加热器）。
很多项目脚本（例如 202609_SiN730_WYL 的 dispersion ring 阵列）都在重复做同一件事：

1. 按列表生成一系列 ``TCRingT1``，每个 ring 的 gap / heater / taper 位置略有不同；
2. 把它们按固定 pitch 排成一行/一列；
3. 在环心加文字标签，并把每颗 ring 的端口汇总到父组件。

本模块把这套“排一行”的逻辑收成三层：

* :class:`RingCouponSpec` —— 一颗 ring coupon 的不可变参数；
* :func:`ring_coupon` —— 构建单个 coupon（内部调用 TCRingT1）；
* :func:`RingCouponRow` —— 把一组 coupon 按 x/y 偏移排好，统一加标签/端口；
* :func:`DispersionRingRow` —— 202609 色散环阵列的库内封装。

现有 ``TCRing*`` 函数保留为单颗 coupon 的兼容入口；新代码优先用本模块的
spec + row 组合，不再在项目脚本里手写 ``for i in range(...)`` 的排布逻辑。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import gdsfactory as gf

from .BasicDefine import (
    LAYER,
    Component,
    HeaterConfigClass,
    LayerSpec,
)
from .TCRing import TCRingT1


@dataclass(frozen=True)
class RingCouponSpec:
    """单颗 ring coupon 的完整参数（frozen，可直接作为 @gf.cell 的缓存键）。

    只放几何/加热器参数；``tin`` / ``tout`` 由行构建函数统一传入。
    """

    radius_ring: float = 120.0
    width_ring: float = 1.0
    width_near: float = 2.0
    width_single: float = 1.0
    gap_rc: float = 1.0
    angle_rc: float = 20.0
    r_euler_min: float = 200.0
    length_taper: float = 150.0
    length_total: float = 10000.0
    pos_ring: float = 500.0
    length_th_horizontal: float = 10.0
    length_th_vertical: float = 10.0
    length_busheater: float = 1.0
    is_ad: bool = False
    position_taper: str = "before_bend"
    direction_heater: str = "up"
    heater_config_ring: HeaterConfigClass | None = None
    heater_config_bus: HeaterConfigClass | None = None
    label: str = ""

    def auto_label(self) -> str:
        """给色散/测试阵列生成默认标签（不写工艺数值）。"""
        if self.label:
            return self.label
        hc = self.heater_config_ring
        partial = getattr(hc, "Partial", "-") if hc else "-"
        delta = getattr(hc, "DeltaHeat", "-") if hc else "-"
        return (f"R {self.radius_ring:g}\n"
                f"W {self.width_ring:g}  G {self.gap_rc:g}\n"
                f"P {partial}  D {delta}")


@gf.cell
def ring_coupon(
        spec: RingCouponSpec = RingCouponSpec(),
        tin: Any = None,
        tout: Any = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """构建一颗 ring coupon；参数全部来自 :class:`RingCouponSpec`。"""
    if tin is None:
        tin = gf.c.taper(width1=0.3, width2=spec.width_single,
                          length=spec.length_taper, layer=oplayer)
    if tout is None:
        tout = gf.c.taper(width1=spec.width_single, width2=0.2,
                           length=spec.length_taper, layer=oplayer)
    return TCRingT1(
        r_ring=spec.radius_ring,
        r_euler_min=spec.r_euler_min,
        width_ring=spec.width_ring,
        width_near=spec.width_near,
        width_single=spec.width_single,
        angle_rc=spec.angle_rc,
        length_taper=spec.length_taper,
        length_total=spec.length_total,
        pos_ring=spec.pos_ring,
        length_th_horizontal=spec.length_th_horizontal,
        length_th_vertical=spec.length_th_vertical,
        length_busheater=spec.length_busheater,
        gap_rc=spec.gap_rc,
        tin=tin,
        tout=tout,
        is_ad=spec.is_ad,
        oplayer=oplayer,
        direction_heater=spec.direction_heater,
        position_taper=spec.position_taper,
        heater_config_ring=spec.heater_config_ring,
        heater_config_bus=spec.heater_config_bus,
    )


def _as_specs(specs: Sequence[RingCouponSpec]) -> tuple[RingCouponSpec, ...]:
    out = tuple(specs)
    for s in out:
        if not isinstance(s, RingCouponSpec):
            raise TypeError(f"specs 里的元素必须是 RingCouponSpec，收到 {type(s).__name__}")
    return out


@gf.cell
def _RingCouponRow(
        specs: tuple[RingCouponSpec, ...],
        x: float = 0.0,
        y0: float = 0.0,
        dy: float = 0.0,
        dx: float = 0.0,
        label: bool = False,
        label_layer: LayerSpec = LAYER.M2,
        label_size: float = 20.0,
        tin: Any = None,
        tout: Any = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """内部缓存版本：specs 必须是 tuple；对外用 :func:`RingCouponRow`。"""
    c = gf.Component()
    for i, spec in enumerate(specs):
        ring = c << ring_coupon(spec, tin=tin, tout=tout, oplayer=oplayer)
        ring.movex(x + i * dx).movey(y0 + i * dy)
        # 每颗 ring 的端口统一加 R{i}_ 前缀，方便整行连接/审计
        for p in ring.ports:
            c.add_port(name=f"R{i}_{p.name}", port=p)
        if label:
            c << gf.c.text(
                spec.auto_label(),
                size=label_size,
                position=ring.ports["RingC"].center,
                justify="center",
                layer=label_layer,
            )
    return c


def RingCouponRow(
        specs: Sequence[RingCouponSpec] = (RingCouponSpec(),),
        x: float = 0.0,
        y0: float = 0.0,
        dy: float = 0.0,
        dx: float = 0.0,
        label: bool = False,
        label_layer: LayerSpec = LAYER.M2,
        label_size: float = 20.0,
        tin: Any = None,
        tout: Any = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """把一组 ring coupon 按 (x + i*dx, y0 + i*dy) 排好。

    参数:
        specs: RingCouponSpec 序列（允许 list，内部转 tuple）。
        x, y0: 第一颗 coupon 的偏移。
        dx, dy: 相邻 coupon 的 x/y 间距。
        label: 是否在环心加文字。
        label_layer: 文字层。
        label_size: 文字尺寸。
        tin, tout: 统一 IO 组件；None 时使用 TCRingT1 的默认 taper。
        oplayer: 光学层。

    返回:
        Component，端口名为 ``R{i}_<原端口名>``。
    """
    return _RingCouponRow(_as_specs(specs), x=x, y0=y0, dy=dy, dx=dx,
                          label=label, label_layer=label_layer,
                          label_size=label_size, tin=tin, tout=tout,
                          oplayer=oplayer)


@gf.cell
def _DispersionRingRow(
        specs: tuple[RingCouponSpec, ...],
        x: float = -50.0,
        y0: float = 0.0,
        dy: float = 20.0,
        label: bool = True,
        label_layer: LayerSpec = LAYER.M2,
        label_size: float = 20.0,
        tin: Any = None,
        tout: Any = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    return _RingCouponRow(specs, x=x, y0=y0, dy=dy, dx=0.0, label=label,
                          label_layer=label_layer, label_size=label_size,
                          tin=tin, tout=tout, oplayer=oplayer)


def DispersionRingRow(
        gaps: Sequence[float] = (0.7, 0.8),
        heater_configs: Sequence[HeaterConfigClass | None] | None = None,
        width_ring: float = 1.5,
        width_near: float = 1.27,
        width_single: float = 1.0,
        radius_ring: float = 217.0,
        angle_rc: float = 10.0,
        r_euler_min: float = 129.0,
        r_euler_min_last: float = 170.0,
        length_taper: float = 150.0,
        length_total: float = 4600.0,
        length_th_horizontal: float = 1.0,
        length_th_horizontal_last: float = 10.0,
        length_th_vertical: float = 70.0,
        length_th_vertical_last: float = 30.0,
        length_busheater: float = 100.0,
        pitch: float = 500.0,
        y0: float = 0.0,
        y_offset: float = -250.0,
        dy: float = 20.0,
        x: float = -50.0,
        label: bool = True,
        label_layer: LayerSpec = LAYER.M2,
        tin: Any = None,
        tout: Any = None,
        oplayer: LayerSpec = LAYER.WG,
        heater_config_bus: HeaterConfigClass | None = None,
        direction_heater: str = "up",
        position_taper_mid: str = "after_bend",
        position_taper_last: str = "no_bend",
        is_ad_mid: bool = True,
        is_ad_last: bool = False,
        last_no_bend: bool = True,
        ring_specs: Sequence[RingCouponSpec] | None = None,
) -> Component:
    """色散测试环阵列：每颗 ring 用不同 gap/heater，最后一颗可切到 no_bend。

    这是 202609_SiN730_WYL 的 ``add_dispersion_rings`` 的库内封装：

    * 第 i 颗 ring 的 ``pos_ring = 100 + pitch*i``；
    * 前 N-1 颗使用 ``position_taper='after_bend'``、``r_euler_min=129``；
    * 最后一颗（``last_no_bend=True``）使用 ``position_taper='no_bend'``、
      ``is_ad=False``、``r_euler_min=170``；
    * 每颗 ring 在 y 方向错开 ``dy``，整行横向偏移 ``x``；
    * 默认在环心加 ``R/W/G/P/D`` 标签。

    参数:
        gaps: 每颗 ring 的耦合间隙（边到边，Gap 约定），长度决定 ring 数量。
        heater_configs: 每颗 ring 的加热器配置；None 表示等长全 None。
        width_ring: 环波导宽度。
        width_near: 耦合总线（near）波导宽度。
        width_single: 行两端 IO / 单模波导宽度。
        radius_ring: 环半径。
        angle_rc: 环-总线耦合角。
        r_euler_min: 前 N-1 颗 ring 的最小 Euler 半径。
        r_euler_min_last: 最后一颗 ring 的最小 Euler 半径。
        length_total: coupon 总长度。
        y0, y_offset, dy, x: 行/环的绝对与相对排布偏移。
        last_no_bend: 最后一颗是否切到 no_bend（202609 的做法）。
        ring_specs: 逐环完整 ``RingCouponSpec``；给出时覆盖上面的批量参数。
        label, label_layer: 环心标签。
        tin, tout, oplayer: IO 和光学层。

    返回:
        Component；端口名 ``R{i}_...``。
    """
    if ring_specs is not None:
        specs = _as_specs(ring_specs)
    else:
        gaps = tuple(float(g) for g in gaps)
        if heater_configs is None:
            hcs = (None,) * len(gaps)
        else:
            hcs = tuple(heater_configs)
            if len(hcs) != len(gaps):
                raise ValueError(f"gaps ({len(gaps)}) 与 heater_configs ({len(hcs)}) 长度不一致")

        specs_list = []
        n = len(gaps)
        for i, (gap, hc) in enumerate(zip(gaps, hcs)):
            last = i == n - 1
            use_no_bend = bool(last and last_no_bend)
            specs_list.append(RingCouponSpec(
                radius_ring=radius_ring,
                width_ring=width_ring,
                width_near=width_near,
                width_single=width_single,
                gap_rc=gap,
                angle_rc=angle_rc,
                r_euler_min=(r_euler_min_last if use_no_bend else r_euler_min),
                length_taper=length_taper,
                length_total=length_total,
                pos_ring=100.0 + pitch * i,
                length_th_horizontal=(length_th_horizontal_last if use_no_bend
                                      else length_th_horizontal),
                length_th_vertical=(length_th_vertical_last if use_no_bend
                                    else length_th_vertical),
                length_busheater=length_busheater,
                is_ad=(is_ad_last if use_no_bend else is_ad_mid),
                position_taper=(position_taper_last if use_no_bend
                                else position_taper_mid),
                heater_config_ring=hc,
                heater_config_bus=heater_config_bus,
                direction_heater=direction_heater,
                label="",
            ))
        specs = tuple(specs_list)
    if tin is None:
        tin = gf.c.taper(width1=0.3, width2=specs[0].width_single,
                          length=specs[0].length_taper, layer=oplayer)
    if tout is None:
        tout = gf.c.taper(width1=specs[0].width_single, width2=0.2,
                           length=specs[0].length_taper, layer=oplayer)
    return _DispersionRingRow(specs, x=x, y0=y0 + y_offset, dy=dy, label=label,
                             label_layer=label_layer, label_size=20.0,
                             tin=tin, tout=tout, oplayer=oplayer)


__all__ = ["RingCouponSpec", "ring_coupon", "RingCouponRow", "DispersionRingRow"]
