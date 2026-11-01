"""耦合腔（coupled-cavity）版图组件。

本模块只画“腔与腔直接耦合 / 侧耦合”的典型结构，不涉及有源区或电极：

* :func:`CoupledRingFilter` —— 二阶 add-drop 环滤波器（两个环直接耦合，
  上下各一条总线）；
* :func:`CROW` —— 耦合谐振器光波导（Coupled-Resonator Optical Waveguide），
  N 个环沿 x 方向直接耦合，输入/输出总线分别只耦合首/尾环；
* :func:`SCISSOR` —— 侧耦合谐振器序列（Side-Coupled Integrated Spaced
  Sequence of Resonators），N 个环等间距侧耦合到同一条总线上。

参考文献
--------
* B. E. Little, S. T. Chu, H. A. Haus, J. Foresi, J.-P. Laine,
  "Microring resonator channel dropping filters," J. Lightwave Technol.
  15(6), 998-1005 (1997).  （二阶 add-drop 环滤波器）
* D. D. Smith, H. Chang, K. A. Fuller, A. T. Rosenberger, R. W. Boyd,
  "Coupled-resonator-induced transparency," Phys. Rev. A 69, 063804 (2004).
  （两个直接耦合环的“光分子”/耦合腔诱导透明）
* A. Yariv, Y. Xu, R. K. Lee, A. Scherer, "Coupled-resonator optical
  waveguide: a proposal and analysis," Opt. Lett. 24(11), 711-713 (1999).
  （CROW）
* J. K. S. Poon, J. Scheuer, Y. Xu, A. Yariv, "Designing coupled-resonator
  optical waveguide delay lines," J. Opt. Soc. Am. B 21(9), 1665-1673
  (2004).  （CROW 延迟线设计）
* J. E. Heebner, R. W. Boyd, Q.-H. Park, "SCISSOR solitons and other novel
  propagation effects in microresonator-modified waveguides," J. Opt. Soc.
  Am. B 19(4), 722-731 (2002).  （SCISSOR）

几何约定
--------
* 环用 ``gf.c.ring`` 画成完整圆环，半径指环中心线半径，环宽为 ``WidthRing``；
* 环与总线、环与环之间都留**净间隙**（edge-to-edge gap），不是中心距；
* 所有长度单位 µm，角度单位度；端口方向 0° 朝 +x，逆时针为正。
"""
from __future__ import annotations

from math import isfinite

import gdsfactory as gf

from .BasicDefine import LAYER, Component, GfCStraight, LayerSpec, add_labels_to_ports


def _validate_positive(**values: float) -> None:
    """统一检查几何参数：必须是有限正数。"""
    for name, value in values.items():
        if not isfinite(float(value)) or float(value) <= 0:
            raise ValueError(f"{name} 必须是有限正数，收到 {value!r}")


def _ring(c, radius: float, width: float, layer: LayerSpec, center: tuple[float, float]):
    """在父组件 c 中放一个以 center 为圆心的完整环，返回实例。"""
    ref = c << gf.c.ring(width=width, radius=radius, layer=layer)
    ref.move(center)
    return ref


def _bus(c, length: float, width: float, layer: LayerSpec, center: tuple[float, float]):
    """在父组件 c 中放一条水平直总线，``center`` 是总线几何中心。"""
    ref = c << GfCStraight(length=length, width=width, layer=layer)
    ref.move((center[0] - length / 2, center[1]))
    return ref


def _add_reference_port(c, name: str, center: tuple[float, float], width: float,
                        layer: LayerSpec) -> None:
    """添加一个只用于定位/检查的环心参考端口（不参与光路连接）。"""
    c.add_port(name=name, center=center, width=width, orientation=90, layer=layer)


@gf.cell
def CoupledRingFilter(
        Radius1: float = 100.0,
        Radius2: float = None,
        WidthRing: float = 1.0,
        WidthBus: float = 0.9,
        GapRing: float = 0.2,
        GapBus: float = 0.3,
        BusExtension: float = 30.0,
        IsAddDrop: bool = True,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """二阶 add-drop 环滤波器（两个直接耦合的环 + 上下总线）。

    版图从下到上依次是：

    * 下总线：Input / Through，与 ring1 侧耦合；
    * ring1 与 ring2：上下直接耦合，净间隙 ``GapRing``；
    * 上总线：Add / Drop，与 ring2 侧耦合（``IsAddDrop=False`` 时不画）。

    这正是 Little 1997 的二阶 microring add-drop filter 画法；当
    ``Radius2 != Radius1`` 时两个腔失谐，可用作 Vernier 耦合腔对
    （Smith 2004 的 coupled-resonator-induced transparency 结构）。

    参数:
        Radius1 (float): 下环中心线半径 (µm)。
        Radius2 (float | None): 上环半径；None 时与 Radius1 相同。
        WidthRing (float): 环波导宽度 (µm)。
        WidthBus (float): 总线波导宽度 (µm)。
        GapRing (float): 两环外沿之间的净间隙 (µm)。越小耦合越强。
        GapBus (float): 环外沿与总线边缘之间的净间隙 (µm)。
        BusExtension (float): 总线在环两侧额外伸出的长度 (µm)。
        IsAddDrop (bool): True 画上总线（四端口）；False 只留 Input/Through。
        oplayer (LayerSpec): 光学波导层。

    端口:
        Input, Through: 下总线两端。
        Add, Drop: 上总线两端（IsAddDrop=True 时）。
        Ring1C, Ring2C: 两个环的圆心参考端口。

    说明:
        环与总线、环与环之间都是“净间隙”，版图不会重叠；可直接把
        ``GapRing`` 从 0.2 扫到 0.6 看耦合区变化。
    """
    if Radius2 is None:
        Radius2 = Radius1
    _validate_positive(Radius1=Radius1, Radius2=Radius2, WidthRing=WidthRing,
                       WidthBus=WidthBus, BusExtension=BusExtension)
    if GapRing <= 0 or GapBus <= 0:
        raise ValueError("GapRing / GapBus 必须为正（净间隙）")

    c = gf.Component()
    r1, r2 = float(Radius1), float(Radius2)
    # 环心 y：让环1外沿与下总线上沿之间恰好留 GapBus
    y1 = r1 + WidthRing / 2 + WidthBus / 2 + GapBus
    # 两环外沿之间恰好留 GapRing
    y2 = y1 + r1 + r2 + WidthRing + GapRing
    ybus2 = y2 + r2 + WidthRing / 2 + GapBus + WidthBus / 2

    bus_len = 2 * max(r1, r2) + 2 * BusExtension
    bus1 = _bus(c, bus_len, WidthBus, oplayer, (0.0, 0.0))
    ring1 = _ring(c, r1, WidthRing, oplayer, (0.0, y1))
    ring2 = _ring(c, r2, WidthRing, oplayer, (0.0, y2))

    c.add_port("Input", port=bus1.ports["o1"])
    c.add_port("Through", port=bus1.ports["o2"])
    _add_reference_port(c, "Ring1C", (0.0, y1), WidthRing, oplayer)
    _add_reference_port(c, "Ring2C", (0.0, y2), WidthRing, oplayer)

    if IsAddDrop:
        bus2 = _bus(c, bus_len, WidthBus, oplayer, (0.0, ybus2))
        c.add_port("Add", port=bus2.ports["o1"])
        c.add_port("Drop", port=bus2.ports["o2"])

    c.info["gap_ring"] = float(GapRing)
    c.info["gap_bus"] = float(GapBus)
    c.info["fsr_ratio"] = (r1 / r2) if r2 else 1.0
    add_labels_to_ports(c)
    return c


@gf.cell
def CROW(
        NumRings: int = 4,
        Radius: float = 40.0,
        WidthRing: float = 1.0,
        WidthBus: float = 0.9,
        GapRing: float = 0.2,
        GapBus: float = 0.3,
        BusExtension: float = 0.4,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """CROW：N 个直接耦合的环排成一条链（Yariv 1999 / Poon 2004）。

    版图约定：

    * 所有环沿 +x 排成一行，圆心距 = ``2*Radius + WidthRing + GapRing``，
      也就是相邻环外沿之间恰好留 ``GapRing``；
    * 只有**首环**和**尾环**下方各有一条短总线，分别作为输入/输出耦合；
    * 中间环只与左右邻居直接耦合，不接触总线。

    参数:
        NumRings (int): 环数（>=2；2 个环就是光分子，>=3 才是典型 CROW）。
        Radius (float): 每个环的中心线半径 (µm)。
        WidthRing (float): 环波导宽度 (µm)。
        WidthBus (float): 端部总线宽度 (µm)。
        GapRing (float): 相邻环外沿之间的净间隙 (µm)。
        GapBus (float): 环外沿与端部总线边缘之间的净间隙 (µm)。
        BusExtension (float): 端部总线在环两侧的额外伸出长度 (µm)；
            会自动限制，避免 2 环时两条总线在中间重叠。
        oplayer (LayerSpec): 光学波导层。

    端口:
        Input, Through: 首环下方总线的两端。
        Output, Add: 尾环下方总线的两端（Output 在右侧）。
        Ring0C … Ring{N-1}C: 每个环的圆心参考端口。

    说明:
        端口名里的 Through/Add 是端部总线的“空闲端”，可用于在线监测或
        继续级联；真正的 CROW 输出请取 ``Output``。
    """
    n = int(NumRings)
    if n < 2:
        raise ValueError("CROW 至少需要 2 个环")
    _validate_positive(Radius=Radius, WidthRing=WidthRing, WidthBus=WidthBus,
                       GapRing=GapRing, GapBus=GapBus)
    if GapRing <= 0 or GapBus <= 0:
        raise ValueError("GapRing / GapBus 必须为正")

    # 2 个环时首尾总线不能在中点重叠：每条总线最多伸出 (Wr+Gap)/2 再留 0.05 余量
    ext = min(float(BusExtension), max((WidthRing + GapRing) / 2 - 0.05, 0.05))
    pitch = 2 * Radius + WidthRing + GapRing
    bus_y = -(Radius + WidthRing / 2 + GapBus + WidthBus / 2)
    bus_len = 2 * Radius + 2 * ext

    c = gf.Component()
    for i in range(n):
        x = i * pitch
        _ring(c, Radius, WidthRing, oplayer, (x, 0.0))
        _add_reference_port(c, f"Ring{i}C", (x, 0.0), WidthRing, oplayer)

    bus_in = _bus(c, bus_len, WidthBus, oplayer, (0.0, bus_y))
    bus_out = _bus(c, bus_len, WidthBus, oplayer, ((n - 1) * pitch, bus_y))
    c.add_port("Input", port=bus_in.ports["o1"])
    c.add_port("Through", port=bus_in.ports["o2"])
    c.add_port("Add", port=bus_out.ports["o1"])
    c.add_port("Output", port=bus_out.ports["o2"])

    c.info["num_rings"] = n
    c.info["pitch"] = float(pitch)
    c.info["gap_ring"] = float(GapRing)
    add_labels_to_ports(c)
    return c


@gf.cell
def SCISSOR(
        NumRings: int = 4,
        Radius: float = 40.0,
        WidthRing: float = 1.0,
        WidthBus: float = 0.9,
        GapBus: float = 0.3,
        RingGap: float = 2.0,
        BusExtension: float = 30.0,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """SCISSOR：N 个环等间距侧耦合到同一条直总线（Heebner 2002）。

    与 :func:`CROW` 的区别：

    * CROW 是“环—环”直接耦合，总线只在首尾；
    * SCISSOR 所有环都只与**同一条总线**侧耦合，环与环之间留
      ``RingGap`` 的净间隙、互不直接耦合。

    参数:
        NumRings (int): 环数。
        Radius (float): 每个环的中心线半径 (µm)。
        WidthRing (float): 环波导宽度 (µm)。
        WidthBus (float): 总线宽度 (µm)。
        GapBus (float): 环外沿与总线上沿之间的净间隙 (µm)。
        RingGap (float): 相邻环外沿之间的净间隙 (µm)；越大越接近独立腔。
        BusExtension (float): 总线在首/尾环之外的伸出长度 (µm)。
        oplayer (LayerSpec): 光学波导层。

    端口:
        Input, Through: 总线两端。
        Ring0C … Ring{N-1}C: 每个环的圆心参考端口。
    """
    n = int(NumRings)
    if n < 1:
        raise ValueError("SCISSOR 至少需要 1 个环")
    _validate_positive(Radius=Radius, WidthRing=WidthRing, WidthBus=WidthBus,
                       GapBus=GapBus, RingGap=RingGap, BusExtension=BusExtension)
    if GapBus <= 0 or RingGap <= 0:
        raise ValueError("GapBus / RingGap 必须为正")

    pitch = 2 * Radius + WidthRing + RingGap
    ring_y = Radius + WidthRing / 2 + GapBus + WidthBus / 2
    span = (n - 1) * pitch
    bus_len = span + 2 * Radius + 2 * BusExtension
    c = gf.Component()

    bus = _bus(c, bus_len, WidthBus, oplayer, (span / 2, 0.0))
    for i in range(n):
        x = i * pitch
        _ring(c, Radius, WidthRing, oplayer, (x, ring_y))
        _add_reference_port(c, f"Ring{i}C", (x, ring_y), WidthRing, oplayer)

    c.add_port("Input", port=bus.ports["o1"])
    c.add_port("Through", port=bus.ports["o2"])
    c.info["num_rings"] = n
    c.info["pitch"] = float(pitch)
    c.info["gap_bus"] = float(GapBus)
    add_labels_to_ports(c)
    return c


__all__ = ["CoupledRingFilter", "CROW", "SCISSOR"]
