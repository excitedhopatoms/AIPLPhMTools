import numpy as np
import gdsfactory as gf
from gdsfactory.generic_tech import get_generic_pdk
from gdsfactory.typings import Layer, LayerSpec, LayerSpecs ,Optional, Callable
from gdsfactory.component import Component
import FabBasic_hjh_G7v1k as md
import FabDefine_YD300nmSiN as FD
PDK = get_generic_pdk()
PDK.activate()
# layer define
LAYER = FD.LayerMapUserDef()
S_wg0 = gf.Section(width=1, offset=0, layer=LAYER.WG, port_names=("o1", "o2"))
CS_wg0 = gf.CrossSection(sections=[S_wg0])
if __name__ == '__main__':
    # test0 = md.TCCoupleRingDRT1(r_ring2=20,r_ring1=240)
    # test0.show()
    test = gf.Component("test")
    test1 = test << gf.c.bend_euler(angle=350,radius=100,width=2,layer=LAYER.WG)
    test.show()
    # DBR=list(range(3))
    # name = '8nm08091'
    # DBR[0] = md.DBRFromCsvOffset(CSVName='D:/Mask_Download/202501_SiN300_YD#4/300nmSiN DBR/'+name+'.csv',Offset=0)
    # DBR[0].write_gds('D:/Mask_Download/202501_SiN300_YD#4/300nmSiN DBR/'+name+'Offset0.gds')
    # DBR[0].show()
