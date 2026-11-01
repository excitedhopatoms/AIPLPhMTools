"""组件装配工具：把"绝对坐标绘制"的旧块包装成带端口的 Component，
并用 gdsfactory 的 ``reference.connect()`` 把它们串起来。

用法::

    W = block("Input", draw_fn, origin=(433.3, 398.4), ports={
        "out": (433.3, 398.4, 0, 0.45, SIWG),
        "in":  (306.15, 318.4, 180, 0.45, SIWG),
    })
    ref = parent << W
    ref.connect("out", upstream.ports["si"])

``origin`` 是包装后位于 (0,0) 的基准点（通常取某个端口），
其余端口坐标会自动减去 ``origin``。这样旧块内部的绝对坐标不用重写，
但顶层位置完全由端口连接决定，改参数时下游自动跟随。
"""
from __future__ import annotations

import gdsfactory as gf
from gdsfactory.component import Component


def wrap(name: str, body, origin, ports) -> Component:
    """把已画好的 body（绝对坐标）包装成以 origin 为原点的 Component。"""
    comp = gf.Component(name)
    ref = comp << body
    ref.move((-float(origin[0]), -float(origin[1])))
    for nm, (x, y, ang, width, layer) in ports.items():
        comp.add_port(
            name=nm,
            center=(float(x) - float(origin[0]), float(y) - float(origin[1])),
            orientation=float(ang),
            width=float(width),
            layer=layer,
        )
    return comp


def block(name: str, draw, origin, ports) -> Component:
    """把 draw(c) 画出的绝对几何包装成以 origin 为原点的 Component。

    ports: {name: (x, y, orientation, width, layer)}
    """
    body = gf.Component(f"{name}__body")
    draw(body)
    return wrap(name, body, origin, ports)


_GDS_CACHE = {}


def import_cached(gds_path):
    """同一个 GDS 只导入一次，避免重复 cell 名冲突。"""
    key = str(gds_path)
    if key not in _GDS_CACHE:
        _GDS_CACHE[key] = gf.import_gds(gds_path)
    return _GDS_CACHE[key]


def pdk(name: str, gds_path, ports) -> Component:
    """把 PDK 黑盒导入成一个带端口的 Component（端口用局部坐标给出）。

    ports: {name: (x, y, orientation, width, layer)}
    """
    comp = gf.Component(name)
    comp << import_cached(gds_path)
    for nm, (x, y, ang, width, layer) in ports.items():
        comp.add_port(
            name=nm,
            center=(float(x), float(y)),
            orientation=float(ang),
            width=float(width),
            layer=layer,
        )
    return comp


def place_connected(parent, comp, port: str, target_port):
    """实例化 comp，并用 connect 把 port 接到 target_port，返回 reference。"""
    ref = parent << comp
    ref.connect(port, target_port)
    return ref
