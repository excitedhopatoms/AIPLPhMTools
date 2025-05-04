import gdsfactory as gf
import numpy as np
import csv
from gdsfactory.typings import Layer
from gdsfactory.component import Component
from gdsfactory.path import Path, _fresnel, _rotate_points
from gdsfactory.typings import LayerSpec
from gdsfactory.cross_section import cross_section
from gdsfactory.generic_tech import get_generic_pdk
from gdsfactory.pdk import get_active_pdk
from gdsfactory.typings import Layer, LayerSpec, LayerSpecs ,Optional, Callable
from .BasicDefine import *
# %% OpenPad
def OpenPad(
        WidthOpen:float = 90,
        Enclosure:float = 10,
        openlayer:LayerSpec = LAYER.OPEN,
        elelayer:LayerSpec = LAYER.M1,
        Name = "OpenPad"
)->Component:
    """
    创建一个开放焊盘组件，包含一个中心焊盘和外围的电极层。

    参数：
        WidthOpen: 中心焊盘的宽度（单位：um）。
        Enclosure: 电极层与中心焊盘的间距（单位：um）。
        openlayer: 中心焊盘的层定义。
        elelayer: 电极层的层定义。
        Name: 组件名称。

    返回：
        Component: 生成的开放焊盘组件。

    端口：
        left: 左侧端口。
        right: 右侧端口。
        up: 上侧端口。
        down: 下侧端口。
    """
    c = gf.Component(Name)
    pad = c << gf.c.straight(width = WidthOpen,length=WidthOpen,layer = openlayer)
    outpad = c << gf.geometry.offset(pad,distance=Enclosure,layer=elelayer)
    a_pad = WidthOpen
    #set ports
    c.add_port(name="left", port=pad.ports["o1"],center=[-Enclosure,0])
    c.add_port(name="right", port=pad.ports["o2"],center=[a_pad+Enclosure,0])
    c.add_port(name="up", port=pad.ports["o1"],orientation=90,center=[a_pad/2,a_pad/2+Enclosure])
    c.add_port(name="down", port=pad.ports["o1"], orientation=-90, center=[a_pad/2, -a_pad/2-Enclosure])
    return c

# %% OffsetRamp
@gf.cell
def OffsetRamp(
        length: float = 10.0,
        width1: float = 5.0,
        width2: float | None = 8.0,
        offset: float = 0,
        layer: LayerSpec = LAYER.WG,
        Name="OffsetRamp"
)-> Component:
    """
    创建一个偏移斜坡组件，用于连接不同宽度的波导。

    参数：
        length: 斜坡的长度（单位：um）。
        width1: 斜坡起始端的宽度（单位：um）。
        width2: 斜坡终止端的宽度（单位：um），默认为 width1。
        offset: 输出端中心相对于输入端中心的偏移量（单位：um）。
        layer: 斜坡的层定义。
        Name: 组件名称。

    返回：
        Component: 生成的偏移斜坡组件。

    端口：
        o1: 输入端端口。
        o2: 输出端端口。
    """
    if width2 is None:
        width2 = width1
    xpts = [0, length, length, 0]
    ypts = [width1, width2/2+width1/2+offset, -width2/2+width1/2+offset, 0]
    c = Component(Name)
    c.add_polygon([xpts, ypts], layer=layer)
    c.add_port(
        name="o1", center=[0, width1 / 2], width=width1, orientation=180, layer=layer
    )
    c.add_port(
        name="o2",
        center=[length, width1 / 2+offset],
        width=width2,
        orientation=0,
        layer=layer,
    )
    return c


# %% GSGELE
@gf.cell
def GSGELE(
        WidthG:float = 80,
        WidthS:float = 25,
        GapGS:float = 6,
        LengthEle:float = 10000,
        IsPad:bool = False,
        Is2Pad:bool =False,
        PitchPad:float = 100,
        WidthOpen:float = 40,
        Enclosure:float = 10,
        openlayer:LayerSpec = LAYER.OPEN,
        elelayer:LayerSpec = LAYER.M1,
        Name = "GSGELE"
)->Component:
    """
    创建一个GSG电极组件，支持焊盘和双焊盘配置。

    参数：
        WidthG: G电极的宽度（单位：um）。
        WidthS: S电极的宽度（单位：um）。
        GapGS: G电极与S电极之间的间距（单位：um）。
        LengthEle: 电极的长度（单位：um）。
        IsPad: 是否添加焊盘。
        Is2Pad: 是否添加双焊盘。
        PitchPad: 焊盘之间的间距（单位：um）。
        WidthOpen: 焊盘的宽度（单位：um）。
        Enclosure: 焊盘外围的电极层间距（单位：um）。
        openlayer: 焊盘的层定义。
        elelayer: 电极的层定义。
        Name: 组件名称。

    返回：
        Component: 生成的GSG电极组件。

    端口：
        Oin1: 第一个输入端口。
        Oout1: 第一个输出端口。
        Oin2: 第二个输入端口。
        Oout2: 第二个输出端口。
        Gin1: 第一个G电极输入端口。
        Gout1: 第一个G电极输出端口。
        Sin: S电极输入端口。
        Sout: S电极输出端口。
        Gin2: 第二个G电极输入端口。
        Gout2: 第二个G电极输出端口。
    """
    c = gf.Component(Name)
    deltags = GapGS+WidthS/2+WidthG/2
    Greff = gf.c.straight(width = WidthG,length = LengthEle,layer = elelayer)
    Sreff = gf.c.straight(width = WidthS,length = LengthEle,layer = elelayer)
    S1 = c << Sreff
    G1 = c << Greff
    G2 = c << Greff
    G1.movey(deltags)
    G2.movey(-deltags)
    c.add_port(name="Oin1", port=S1.ports["o1"], center=[0, GapGS / 2 + WidthS / 2])
    c.add_port(name="Oout1", port=S1.ports["o2"], center=[0, GapGS / 2 + WidthS / 2])
    c.add_port(name="Oin2", port=S1.ports["o1"], center=[0, -GapGS / 2 - WidthS / 2])
    c.add_port(name="Oout2", port=S1.ports["o2"], center=[0, -GapGS / 2 - WidthS / 2])
    c.add_port(name="Gin1", port=G1.ports["o2"])
    c.add_port(name="Gout1", port=G1.ports["o1"])
    c.add_port(name="Sin", port=S1.ports["o2"])
    c.add_port(name="Sout", port=S1.ports["o1"])
    c.add_port(name="Gin2", port=G2.ports["o2"])
    c.add_port(name="Gout2", port=G2.ports["o1"])
    GSGPadarray = gf.Component()
    GSGPad1 = GSGPadarray << OpenPad(WidthOpen=WidthOpen, Enclosure=Enclosure, elelayer=elelayer,
                                     openlayer=openlayer)
    GSGPad2 = GSGPadarray << OpenPad(WidthOpen=WidthOpen, Enclosure=Enclosure, elelayer=elelayer,
                                     openlayer=openlayer)
    GSGPad3 = GSGPadarray << OpenPad(WidthOpen=WidthOpen, Enclosure=Enclosure, elelayer=elelayer,
                                     openlayer=openlayer)
    GSGPad2.movey(PitchPad)
    GSGPad3.movey(PitchPad * 2)
    GSGPadarray.add_port("Pr1", port=GSGPad1.ports["right"])
    GSGPadarray.add_port("Pl1", port=GSGPad1.ports["left"])
    GSGPadarray.add_port("Pr2", port=GSGPad2.ports["right"])
    GSGPadarray.add_port("Pl2", port=GSGPad2.ports["left"])
    GSGPadarray.add_port("Pr3", port=GSGPad3.ports["right"])
    GSGPadarray.add_port("Pl3", port=GSGPad3.ports["left"])
    if Is2Pad:
        IsPad=True
        GPa2 = c << GSGPadarray
        GPa2.connect("Pl1", destination=c.ports["Gout1"]).move([-PitchPad / 3, PitchPad / 5])
        # Gin1
        pos_diff = GPa2.ports["Pl1"].center - c.ports["Gout1"].center
        G2Pa21 = c << OffsetRamp(length=PitchPad / 3, width1=WidthOpen + 2 * Enclosure, width2=80, offset=-pos_diff[1],
                                layer=elelayer)
        G2Pa21.connect("o2", destination=c.ports["Gout1"])
        # Sin
        pos_diff = GPa2.ports["Pl2"].center - c.ports["Sout"].center
        G2Pa22 = c << OffsetRamp(length=PitchPad / 3, width1=WidthOpen + 2 * Enclosure, width2=25, offset=-pos_diff[1],
                                layer=elelayer)
        G2Pa22.connect("o2", destination=c.ports["Sout"])
        # Gin2
        pos_diff = GPa2.ports["Pl3"].center - c.ports["Gout2"].center
        G2Pa23 = c << OffsetRamp(length=PitchPad / 3, width1=WidthOpen + 2 * Enclosure, width2=80, offset=-pos_diff[1],
                                layer=elelayer)
        G2Pa23.connect("o2", destination=c.ports["Gout2"])
    if IsPad:
        GPa = c << GSGPadarray
        GPa.connect("Pr1", destination=c.ports["Gin1"]).move([PitchPad/3, PitchPad/5])
        # Gin1
        pos_diff = GPa.ports["Pr1"].center - c.ports["Gin1"].center
        G2Pa1 = c << OffsetRamp(length=PitchPad/3, width1=WidthOpen+2*Enclosure, width2=80, offset=pos_diff[1], layer=elelayer)
        G2Pa1.connect("o2", destination=c.ports["Gin1"])
        # Sin
        pos_diff = GPa.ports["Pr2"].center - c.ports["Sin"].center
        G2Pa2 = c << OffsetRamp(length=PitchPad/3, width1=WidthOpen+2*Enclosure, width2=25, offset=pos_diff[1], layer=elelayer)
        G2Pa2.connect("o2", destination=c.ports["Sin"])
        # Gin2
        pos_diff = GPa.ports["Pr3"].center - c.ports["Gin2"].center
        G2Pa3 = c << OffsetRamp(length=PitchPad/3, width1=WidthOpen+2*Enclosure, width2=80, offset=pos_diff[1], layer=elelayer)
        G2Pa3.connect("o2", destination=c.ports["Gin2"])
    return c


__all__=['OffsetRamp','OpenPad','GSGELE']