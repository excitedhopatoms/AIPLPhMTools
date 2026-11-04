"""AIPLPhMTools.TestStructures 子包。

命名约定：

* ``TC`` 前缀 = Test Coupon（带 tin/tout 引出、四端口的测试/表征结构）。
* ``TCRing*`` = 环形测试；``TCRaceTrack*`` = 跑道测试；
  ``TCCouple*`` = 耦合腔/双环/双跑道测试。
* 后缀 ``T1/T2`` 是同一器件的参数预设，不是不同物理结构；新代码优先调用
  基类或带明确参数的版本，旧名字保留为 thin wrapper。
* ``Coupon`` / ``TCRingCoupon`` 是通用 coupon 框架；``Rows`` 是整行阵列。
"""
