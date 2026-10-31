"""SOI 硅光版图底层定义（AIPLPhMTools.SOITools）—— 12 英寸 SOI，3 层金属。

由 ICRD 项目（202610_SOI_icrd）的 ``ICRDPhMTools/FabBasic.py`` 提炼而来，
层号表与工艺常数保持与那套流片文件一致；PDK 宏目录改为可配置（见末尾
``PDK_DIR``），不再绑定具体项目路径。

本模块只放"与器件无关"的东西，方便集中修改：

  第 1 节  层号表        —— 每一层的 (layer, datatype) 与用途说明
  第 2 节  每层工艺要求  —— 最小宽度 / 最小间距 / 最小曲率半径（机读表）
  第 3 节  工艺常数      —— 波导宽度、开窗宽度、焊盘尺寸等
  第 4 节  最小绘图工具  —— box / add_poly / cosd / sind + PDK 目录

改工艺参数时**只改本文件**；main.py 只调用这里定义的层与常数。
所有长度单位 um，原点在芯片左下角。
"""

from __future__ import annotations

import math
from pathlib import Path

from gdsfactory.generic_tech import get_generic_pdk
from gdsfactory.technology.layer_map import LayerMap
from gdsfactory.typings import LayerSpec

# 激活 gdsfactory 的通用 PDK：本项目只借用它的层号表与多边形容器，
# 不使用任何 PDK 工艺库，也不修改 gdsfactory 包本身。
get_generic_pdk().activate()


class LayerMapUserDef(LayerMap):
    """ICRD 12in SOI 层号表（权威来源：技术文件 technology/gdsii.py）。"""

    # 硅波导
    SIWG: LayerSpec = (600, 1)          # 220 nm Si 波导核心
    SIWG_CLD: LayerSpec = (600, 10)     # Si 刻蚀 / 隔离开窗
    SIWG_TRE: LayerSpec = (600, 11)     # Si 深槽
    SIWG_EC: LayerSpec = (600, 20)      # Si 端面耦合器标记
    # 氮化硅波导
    SIN: LayerSpec = (631, 1)           # 400 nm SiN 波导核心（NWG2）
    SIN_CLD: LayerSpec = (631, 10)      # SiN 刻蚀 / 保护开窗
    SIN_TRE: LayerSpec = (631, 11)      # SiN 深槽
    SIN_EC: LayerSpec = (631, 20)       # SiN 端面耦合器标记
    # 第二层氮化硅（NWG3，200 nm above NWG2）
    SIN3: LayerSpec = (632, 1)          # 400 nm SiN 波导核心（NWG3）
    SIN3_CLD: LayerSpec = (632, 10)     # NWG3 刻蚀 / 保护开窗
    SIN3_TRE: LayerSpec = (632, 11)     # NWG3 深槽
    SIN3_EC: LayerSpec = (632, 20)      # NWG3 端面耦合器标记
    # PN 掺杂
    NLD: LayerSpec = (610, 1)
    PLD: LayerSpec = (611, 1)
    NP: LayerSpec = (612, 1)
    PP: LayerSpec = (613, 1)
    NPP: LayerSpec = (614, 1)
    PPP: LayerSpec = (615, 1)
    # 金属互连
    HT: LayerSpec = (637, 1)            # 旧版 TiN 加热电阻（本项目不再使用）
    TIN: LayerSpec = (639, 1)           # 2026Q4 MPW TiN 加热电阻
    CT: LayerSpec = (640, 1)            # 接触孔
    M1: LayerSpec = (641, 1)
    M2: LayerSpec = (642, 1)
    M3: LayerSpec = (643, 1)
    V1: LayerSpec = (651, 1)
    V2: LayerSpec = (652, 1)
    RV: LayerSpec = (660, 1)            # ALPAD -> M3 焊盘过孔
    ALPAD: LayerSpec = (661, 1)
    COVER: LayerSpec = (662, 1)
    # 工艺标记
    DPT: LayerSpec = (664, 1)
    SINOP: LayerSpec = (665, 1)         # SiN 保护岛（开窗余量）
    FRAME: LayerSpec = (183, 4)
    TEXT: LayerSpec = (161, 6)
    PB: LayerSpec = (674, 20)


LAYER = LayerMapUserDef


def _t(member) -> tuple[int, int]:
    """LayerMap 成员 -> GDS (layer, datatype) 元组。"""
    return (member.layer, member.datatype)


# 模块级层号元组：设计脚本、验证脚本和 klayout 都直接使用 tuple
SIWG = _t(LAYER.SIWG)
SIWG_CLD = _t(LAYER.SIWG_CLD)
SIWG_TRE = _t(LAYER.SIWG_TRE)
SIWG_EC = _t(LAYER.SIWG_EC)
SIN = _t(LAYER.SIN)
SIN_CLD = _t(LAYER.SIN_CLD)
SIN_TRE = _t(LAYER.SIN_TRE)
SIN_EC = _t(LAYER.SIN_EC)
SIN3 = _t(LAYER.SIN3)
SIN3_CLD = _t(LAYER.SIN3_CLD)
SIN3_TRE = _t(LAYER.SIN3_TRE)
SIN3_EC = _t(LAYER.SIN3_EC)
NLD = _t(LAYER.NLD)
PLD = _t(LAYER.PLD)
NP = _t(LAYER.NP)
PP = _t(LAYER.PP)
NPP = _t(LAYER.NPP)
PPP = _t(LAYER.PPP)
HT = _t(LAYER.HT)
TIN = _t(LAYER.TIN)
CT = _t(LAYER.CT)
M1 = _t(LAYER.M1)
M2 = _t(LAYER.M2)
M3 = _t(LAYER.M3)
V1 = _t(LAYER.V1)
V2 = _t(LAYER.V2)
RV = _t(LAYER.RV)
ALPAD = _t(LAYER.ALPAD)
COVER = _t(LAYER.COVER)
DPT = _t(LAYER.DPT)
SINOP = _t(LAYER.SINOP)
FRAME = _t(LAYER.FRAME)
TEXT = _t(LAYER.TEXT)
PB = _t(LAYER.PB)

# --------------------------------------------------------------------------- #
# AIPLPhMTools 风格的层别名：LAYER.WG / LAYER.NWG2 等直接是可绘制的 tuple。
# 器件函数可以写 layer=LAYER.NWG2，和 AIPLPhMTools 的 LAYER.WG 一致。
# --------------------------------------------------------------------------- #
class _LayerAliases:
    WG = SIWG
    NWG2 = SIN
    NWG2_CLD = SIN_CLD
    SIWG_CLD = SIWG_CLD
    SIWG_TRE = SIWG_TRE
    SIN_TRE = SIN_TRE
    SIN_EC = SIN_EC
    NWG3 = SIN3
    NWG3_CLD = SIN3_CLD
    NWG3_TRE = SIN3_TRE
    NWG3_EC = SIN3_EC
    TIN = TIN
    CT = CT
    M1 = M1
    M2 = M2
    M3 = M3
    V1 = V1
    V2 = V2
    RV = RV
    ALPAD = ALPAD
    COVER = COVER
    DPT = DPT
    SINOP = SINOP
    TEXT = TEXT
    PB = PB


LAYER = _LayerAliases


# --------------------------------------------------------------------------- #
# 第 2 节  每层工艺要求（drc / qa_curvature 的判据来源）
# --------------------------------------------------------------------------- #
# 逐层最小宽度/间距：**唯一来源是 drc_rules.yaml**（手册 ICRD SIPH v1p1，
# drc.py 读取），这里不再维护第二份，避免两处漂移。
# 逐层曲率下限：R_*_MIN 常量（qa_curvature.py 强制）。

# PDK 宏单元目录（黑盒，只放 GDS，不改内容）。
# 子库不绑定项目路径：默认取环境变量 SOI_PDK_DIR；也可以直接赋值
# ``soi.FabBasic.PDK_DIR = Path("...")`` 或 ``soi.PDK_DIR = ...``（见 __init__）。
import os

HERE = Path(__file__).resolve().parent
PDK_DIR = Path(os.environ["SOI_PDK_DIR"]) if os.environ.get("SOI_PDK_DIR") else None

# --------------------------------------------------------------------------- #
# 第 3 节  工艺常数（改版图尺寸先看这里）
# --------------------------------------------------------------------------- #
DIE_W, DIE_H = 3000.0, 500.0      # 芯片尺寸（um）

# ---- 波导芯宽（同一物理量只写一次；环/螺旋/走线都引用这里） --------------
W_SIN = 1.0            # PDK 标准单模 SiN 走线宽度（MMI / 臂 / PDK 端口）
W_RING = 1.5           # 环腔芯宽（NWG3）
W_RINGBUS = 0.858      # 环的耦合总线宽（pulley，NWG2）
W_SPIRAL = 2.0         # spiral 腔芯宽（NWG3；Spiral.py 用的是这一条的副本）
W_SPIRALBUS = 1.0      # spiral 耦合总线宽（NWG2）
W_SI = 0.45            # Si 波导 / 过渡器端口宽度
W_PHASE = 0.60         # PN 相位段条宽（0.45 -> 0.60 用锥形过渡）

# ---- 宽度类工艺参数 ------------------------------------------------------
W_TIN = 5.00           # TiN 加热条设计宽度（方阻大 -> 宽条降低阻值）
TIN_CLEAR = 2.00       # TiN 与 SiN 芯的最小间隔（MPW 建议）
M_LEAD_W = 20.0        # 电流主干线宽（Mx.5：>10 um 由厂方插槽）
PAD_SMALL = 70.0       # 小焊盘（加热/相位探针）
COVER_SMALL = 55.0     # 小焊盘 COVER 开窗
PAD_METAL = 9.6        # 焊盘 M1/M2 转接板（Mx.5 <= 10 um）
RV_PAD = 20.0          # ALPAD -> M3 过孔板（RV.1 >= 3 um）

# ---- 版图顶点密度（只影响多边形采样，不改中心线/宽度）--------------------
ARC_STEP_DEG = 0.2                # 光路圆弧（Route.turn/t/s_bend）角步长
ANNULUS_STEP_DEG = 0.5            # add_annulus 默认角步长（金属/TiN 环带）
BUFFER_RES = 12                   # shapely buffer 每 1/4 圆的段数
SIMPLIFY_TOL = 0.002              # buffer 后 simplify 容差 um
SPIRAL_N = 9600                   # 螺旋中心线采样点数（曲率审计按它，别随便改）

SIN_CLD_W = 17.0                  # SiN 下方 631/10 与 600/10 开窗宽度
SINOP_EXTRA = 0.8                # SINOP 超出 SiN 核心的余量
# 隔离开窗在**开放端**（走线末端）沿切向多伸出的长度 (µm)。NWG2.5/NWG3.5/
# SIWG.5 要求芯外 0.1 µm 都有开窗；走线端点与相邻窗口以极小夹角相交时，
# 不延伸就会在端面留 0.01~0.2 µm 的细缝。芯片端面那头传 0（见 Facet.py）。
CLD_END_EXT = 0.2
CLD_HALF = SIN_CLD_W / 2.0
SI_CLD_W = 10                   # Si 核心两侧 600/10 隔离开窗宽度
SI_CLD_HALF = SI_CLD_W / 2.0

# 逐层曲率半径策略（qa_curvature.py 的判据）
R_SI_MIN = 10.0                   # 600/1 SIWG 规则最小值
R_SIN_MIN = 50.0                  # 631/1 NWG2 规则最小值
R_SI = 11.0                       # 非谐振 Si 走线设计值
R_SIN = 52.0                      # 非谐振 SiN 走线设计值


# --------------------------------------------------------------------------- #
# 第 4 节  最小绘图工具（所有器件都基于这几个函数）
# --------------------------------------------------------------------------- #
def box(c, x0: float, y0: float, x1: float, y1: float, layer) -> None:
    """轴对齐矩形。"""
    c.add_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=layer)


def add_poly(c, pts, layer) -> None:
    """按顶点列表添加多边形（坐标自动转 float）。"""
    c.add_polygon([(float(x), float(y)) for x, y in pts], layer=layer)



def cosd(a: float) -> float:
    """角度制余弦。"""
    return math.cos(math.radians(a))


def sind(a: float) -> float:
    """角度制正弦。"""
    return math.sin(math.radians(a))
