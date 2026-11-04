"""通用“两端器件 + IO 框架”的测试 coupon。

TCRing / TCRaceTrack / TCCoupledCavity 里反复出现同一套外围逻辑：

* 中间是一个带左右端口的 core（环、跑道腔、耦合腔、MZI……）；
* 两端各接 taper，按需弯折/直行；
* 外面再接 tin/tout，最后把 output 对齐到统一总长度；
* 转发 core 的监视端口、加热器端口和中心参考点。

本模块把这段逻辑抽成 :func:`Coupon`。只要一个 Component 有左右两个端口，
就可以放进中间，不再为每种腔复制一套 IO/绕线代码。

``Coupon`` 是**层次化**的：不 flatten，core 保留为子 cell。
"""
from __future__ import annotations

from typing import Any, Sequence

import gdsfactory as gf
import numpy as np

from ..Core.BasicDefine import (
    LAYER,
    Component,
    GfCBendEuler,
    HeaterConfigClass,
    LayerSpec,
    add_labels_to_ports,
    make_cs,
)
from ..Devices.Ring import RingPulleyT1


def _core_component(core: Any) -> Component:
    """Component / ComponentSpec / 字符串 -> Component。"""
    if isinstance(core, Component):
        return core
    return gf.get_component(core)


@gf.cell
def Coupon(
        core: Any,
        core_input: str = "Input",
        core_output: str = "Through",
        io_width: float = 1.0,
        width_in: float | None = None,
        width_out: float | None = None,
        taper_length: float = 150.0,
        bend_radius: float = 100.0,
        position_taper_in: str = "after_bend",
        position_taper_out: str = "before_bend",
        length_total: float = 10000.0,
        core_x: float = 500.0,
        core_rotation: float = 0.0,
        require_opposite_ports: bool = True,
        orientation_tolerance: float = 20.0,
        tin: Any = None,
        tout: Any = None,
        tin_shift_x: float = 0.0,
        center_ports: tuple[str, str] | None = None,
        center_name: str = "RingC",
        center_width: float = 1.0,
        forward_ports: Sequence[str] = (),
        port_prefix: str = "Core",
        label: bool = False,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """把任意“有左右端口”的 core 包装成标准两端测试 coupon。

    参数:
        core: 中间器件，必须有 ``core_input`` / ``core_output`` 两个端口。
        core_input, core_output: core 的左右端口名。
        io_width: 外部单模波导宽度。
        width_in, width_out: core 输入/输出波导宽度；None 时从 core 端口读取。
        taper_length: 外部 → core 的锥形长度。
        bend_radius: 输入/输出弯折半径。
        position_taper_in: 输入侧 taper 位置：
            ``"before_bend"``（taper→bend→core）、
            ``"after_bend"``（bend→taper→core）、``"no_bend"``。
        position_taper_out: 输出侧 taper 位置，语义同上。
        length_total: 输出端对齐到的总长度（输入归一化到 x=0）。
        core_x: core 在父组件中的初始 x 偏移；用于复现原 TC 布局。
        core_rotation: core 整体旋转角（度）。
        require_opposite_ports: 是否要求 core 输入/输出端口方向大致相反
            （默认 True；不一致时说明 core 不是"左右两端"结构）。
        orientation_tolerance: 端口方向容差（度）。
        tin, tout: 外部 IO 组件；None 时直接暴露 taper/bend 端。
        tin_shift_x: 在连接 tin 后再平移的 x（复现旧 TC 的 pos_ring 偏移）。
        center_ports: 两个 core 端口名，用它们的中点生成 ``center_name``。
        center_name: 中心参考端口名。
        center_width: 中心参考端口宽度。
        forward_ports: 需要转发到父组件的 core 端口名。
        port_prefix: 转发 core 端口时的前缀（如 ``"Ring"``）。
        label: 是否给所有端口加文字。
        oplayer: 光学层。

    返回:
        Component，端口至少包含 ``input`` / ``output``；有 tin/tout 时还会
        有 ``inputo2`` / ``outputo1``；并转发 core 端口与中心参考点。
    """
    core_c = _core_component(core)
    if core_input not in core_c.ports or core_output not in core_c.ports:
        raise ValueError(
            f"core 必须同时有 {core_input!r} 和 {core_output!r} 端口；"
            f"实际端口: {[p.name for p in core_c.ports]}"
        )
    if require_opposite_ports:
        a = float(core_c.ports[core_input].orientation)
        b = float(core_c.ports[core_output].orientation)
        diff = abs(((a - b + 180.0) % 360.0) - 180.0)
        if abs(diff - 180.0) > orientation_tolerance:
            raise ValueError(
                f"core 的 {core_input!r} 与 {core_output!r} 应大致相对（180°），"
                f"实际 {a:g}° / {b:g}°，差 {diff:g}°"
            )
    w_in = float(width_in if width_in is not None else core_c.ports[core_input].width)
    w_out = float(width_out if width_out is not None else core_c.ports[core_output].width)
    if w_in <= 0 or w_out <= 0:
        raise ValueError("core 输入/输出端口宽度必须为正")

    sr = gf.Component()
    ring = sr << core_c
    if core_rotation:
        ring.rotate(core_rotation)
    ring.movex(core_x)

    # ---------------- input side ----------------
    if position_taper_in == "before_bend":
        bend_in = sr << GfCBendEuler(width=w_in, angle=-90, radius=bend_radius,
                                     layer=oplayer, with_arc_floorplan=False)
        bend_in.connect("o2", ring.ports[core_input])
        taper_in = sr << gf.c.taper(width1=io_width, width2=w_in,
                                    length=taper_length, layer=oplayer)
        taper_in.connect("o2", bend_in.ports["o1"])
        port_in = taper_in.ports["o1"]
    elif position_taper_in == "after_bend":
        taper_in = sr << gf.c.taper(width1=io_width, width2=w_in,
                                    length=taper_length, layer=oplayer)
        taper_in.connect("o2", ring.ports[core_input])
        bend_in = sr << GfCBendEuler(width=io_width, angle=-90, radius=bend_radius,
                                     layer=oplayer, with_arc_floorplan=False)
        bend_in.connect("o2", taper_in.ports["o1"])
        port_in = bend_in.ports["o1"]
    elif position_taper_in == "no_bend":
        taper_in = sr << gf.c.taper(width1=io_width, width2=w_in,
                                    length=taper_length, layer=oplayer)
        taper_in.connect("o2", ring.ports[core_input])
        port_in = taper_in.ports["o1"]
    else:
        raise ValueError("position_taper_in 必须是 'before_bend' / 'after_bend' / 'no_bend'")

    # ---------------- output side ----------------
    if position_taper_out == "before_bend":
        taper_out = sr << gf.c.taper(width1=w_out, width2=io_width,
                                     length=taper_length, layer=oplayer)
        taper_out.connect("o1", ring.ports[core_output])
        bend_out = sr << GfCBendEuler(width=io_width, angle=90, radius=bend_radius,
                                      layer=oplayer, with_arc_floorplan=False)
        bend_out.connect("o1", taper_out.ports["o2"])
        port_out = bend_out.ports["o2"]
    elif position_taper_out == "after_bend":
        bend_out = sr << GfCBendEuler(width=w_out, angle=90, radius=bend_radius,
                                      layer=oplayer, with_arc_floorplan=False)
        bend_out.connect("o1", ring.ports[core_output])
        taper_out = sr << gf.c.taper(width1=w_out, width2=io_width,
                                     length=taper_length, layer=oplayer)
        taper_out.connect("o1", bend_out.ports["o2"])
        port_out = taper_out.ports["o2"]
    elif position_taper_out == "no_bend":
        taper_out = sr << gf.c.taper(width1=w_out, width2=io_width,
                                    length=taper_length, layer=oplayer)
        taper_out.connect("o1", ring.ports[core_output])
        port_out = taper_out.ports["o2"]
    else:
        raise ValueError("position_taper_out 必须是 'before_bend' / 'after_bend' / 'no_bend'")

    # ---------------- external IO ----------------
    ctin = None
    ctout = None
    if tin is not None:
        ctin = sr << gf.get_component(tin)
        ctin.connect("o2", port_in)
        if tin_shift_x:
            ctin.movex(tin_shift_x)
        gf.routing.route_single_sbend(
            sr, ctin.ports["o2"], port_in,
            cross_section=make_cs(io_width, oplayer),
        )
        sr.add_port("input", port=ctin.ports["o1"])
        sr.add_port("inputo2", port=ctin.ports["o2"])
    else:
        sr.add_port("input", port=port_in)

    if tout is not None:
        ctout = sr << gf.get_component(tout)
        ctout.connect("o1", port_out, allow_width_mismatch=True)
        in_x = ctin.ports["o1"].center[0] if ctin is not None else 0.0
        ctout.movex(length_total - (ctout.ports["o2"].center[0] - in_x))
        gf.routing.route_single_sbend(
            sr, ctout.ports["o1"], port_out,
            cross_section=make_cs(io_width, oplayer),
        )
        sr.add_port("output", port=ctout.ports["o2"])
        sr.add_port("outputo1", port=ctout.ports["o1"])
    else:
        sr.add_port("output", port=port_out)

    # ---------------- center / core ports ----------------
    if center_ports:
        a, b = center_ports
        center = (np.array(core_c.ports[a].center) + np.array(core_c.ports[b].center)) / 2
        # core 可能被旋转/平移；用实例变换后的端口位置
        center = (np.array(ring.ports[a].center) + np.array(ring.ports[b].center)) / 2
        sr.add_port(center_name, center=center, orientation=180,
                    layer=oplayer, width=center_width)
    for name in forward_ports:
        if name in ring.ports:
            sr.add_port(f"{port_prefix}{name}", port=ring.ports[name])

    # ---------------- normalize input x=0 ----------------
    out = gf.Component()
    ref = out << sr
    ref.movex(-sr.ports["input"].center[0])
    for p in ref.ports:
        out.add_port(name=p.name, port=p)
    if label:
        add_labels_to_ports(out)
    return out


@gf.cell
def TCRingCoupon(
        r_ring: float = 120.0,
        width_ring: float = 1.0,
        width_near: float = 2.0,
        width_single: float = 1.0,
        gap_rc: float = 1.0,
        angle_rc: float = 20.0,
        r_euler_min: float = 100.0,
        length_taper: float = 150.0,
        length_total: float = 2000.0,
        position_taper_in: str = "after_bend",
        position_taper_out: str = "before_bend",
        is_ad: bool = True,
        heater_config: HeaterConfigClass | None = None,
        tin: Any = None,
        tout: Any = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """标准两端 ring coupon：把 RingPulleyT1 作为 Coupon 的中间 core。

    这是 :func:`Coupon` 的 ring 示例：中间换成跑道腔、MZI、耦合腔，
    只要它们有 ``Input`` / ``Through`` 这类左右端口，就可以复用同一套外围。
    Add/Drop 和加热器端口会以 ``Ring<原端口名>`` 转发。
    """
    core = RingPulleyT1(
        WidthRing=width_ring, WidthNear=width_near, RadiusRing=r_ring,
        GapRing=gap_rc, AngleCouple=angle_rc, IsAD=is_ad,
        oplayer=oplayer, HeaterConfig=heater_config,
    )
    return Coupon(
        core=core,
        core_input="Input",
        core_output="Through",
        io_width=width_single,
        width_in=width_near,
        width_out=width_near,
        taper_length=length_taper,
        bend_radius=r_euler_min,
        position_taper_in=position_taper_in,
        position_taper_out=position_taper_out,
        length_total=length_total,
        core_x=0.0,
        tin=tin,
        tout=tout,
        center_ports=("RingL", "RingR"),
        center_width=width_ring,
        forward_ports=tuple(p.name for p in core.ports),
        port_prefix="Ring",
        oplayer=oplayer,
    )


__all__ = ["Coupon", "TCRingCoupon"]
