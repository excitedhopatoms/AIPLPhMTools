"""双圆相接的 300 nm SiN spiral 腔中心线（revision 8）。

结构
----
两个相同的双螺旋圆（直径 300 um，中心距 306 um）镜像相对放置：每个圆
是一条「外圈 -> 中心 Z 折 -> 外圈」的双臂螺旋，双臂交替绕行，相邻波导
中心距 6.0 um（1.0 um 芯 + 5.0 um 间隙，按用户要求）。两个圆的**下端**
用一条水平直线相连（两端切向本来就朝同一方向，接头 C1），两个**上端**
各沿切线向外延伸 100 um，停在耦合总线下方 0.6 um 处，作为腔的两个
耦合端口。整条中心线是一条连续开放的 hairpin：

    端口西 (1655)  ──圆1 外圈(上) → 中心 Z → 外圈(下)──  下连线
                  ──圆2 外圈(下) → 中心 Z → 外圈(上)──  端口东 (2165)

腔长 = 2 x 单圆 + 下连线 + 两条耦合延伸；光在耦合总线内闭合环路。

曲率：所有圆弧 R >= 52 um（Z 折半径 = R0/2 = 52.5；最内圈 105 um；
两臂 150..105 um）。直线段不产生曲率。

用法::

    from ICRDPhMTools import Spiral
    pts, info = Spiral.centerline()
    rmin, _ = Spiral.curvature_radius(pts)
"""

import math

import numpy as np

from .FabBasic import W_SPIRAL   # 芯宽的唯一真源在 FabBasic

# =========================================================================== #
# 自由参数（只有这几个可以独立调）
# =========================================================================== #
GAP      = 6.0          # 相邻波导边缘间隙  <-- 你要调的就是这个
R_OUT    = 170.0        # 外臂最外圈中心线半径
T1       = 4.0          # 外臂圈数（设计目标：FSR 由它决定）
FLAT     = 0.02         # rad，外端等半径圆弧 -> 端面 90 度
CX       = 1800.0       # 两圆心 x（世界系；仅 main.py 用）
R_MIN_SIN = 52.0        # SiN 曲率规则（工艺常数，不要动）

# =========================================================================== #
# 派生参数（全部表达式，不手写）
# =========================================================================== #
ADJ        = W_SPIRAL + GAP                 # 相邻中心距
PITCH_TURN = 2.0 * ADJ                      # 同一条臂每圈半径下降量
R_OUT2     = R_OUT - ADJ                    # 内臂最外圈半径
R_IN       = R_OUT - T1 * PITCH_TURN        # 两臂共同内半径
T2         = T1 - 0.5                       # 内臂圈数（恒等式，见下）
DX         = 2.0 * R_OUT + ADJ              # 两圆心距（最外缘间距 = GAP）
R_MAX_CORE = R_OUT + 0.5 * W_SPIRAL         # 腔体最外芯边



def _dP(psi, r, dr):
    return np.array([dr * math.cos(psi) - r * math.sin(psi),
                     dr * math.sin(psi) + r * math.cos(psi)])


def _arc_pts(P, th, al, R, n):
    kap = (1.0 if al >= 0 else -1.0) / R
    nn = np.array([-math.sin(th), math.cos(th)])
    C = np.asarray(P, float) + nn / kap
    v = np.asarray(P, float) - C
    out = []
    for i in range(n + 1):
        a = al * i / n
        ca, sa = math.cos(a), math.sin(a)
        out.append(C + np.array([ca * v[0] - sa * v[1], sa * v[0] + ca * v[1]]))
    return np.array(out)


def _zfold(pa, ha, pb, hb):
    """中心 Z 折：四段四分之一圆弧，端点 pa->pb，两端 C1。

    两个臂终端对径、航向平行。沿实际臂航向起弧，四段圆弧半径
    R = d/4。
    """
    d = math.dist(pa, pb)
    u = (np.asarray(pb, float) - np.asarray(pa, float)) / d
    n = np.array([-u[1], u[0]])
    ha = np.asarray(ha, float); ha /= np.linalg.norm(ha)
    hb = np.asarray(hb, float); hb /= np.linalg.norm(hb)
    if ha @ hb < 1 - 1e-5:
        raise RuntimeError("Z terminals must have parallel headings")
    phi = math.atan2(ha @ n, ha @ u)
    hloc = np.array([math.cos(phi), math.sin(phi)])

    def build(R, L=0.0):
        P = np.array([-d / 2, 0.0]); th = phi
        pts = [P.copy()]
        for al in (-math.pi / 2, -math.pi / 2, math.pi / 2, math.pi / 2):
            arc = _arc_pts(P, th, al, R, 40)
            pts.extend(arc[1:]); P = arc[-1]; th += al
        if abs(L) > 1e-12:
            pts.append(P + L * hloc)
        return np.array(pts)

    from scipy.optimize import brentq
    L = 0.0
    for _ in range(3):
        f = lambda R: build(R, L)[-1, 0] - d / 2
        R = brentq(f, d / 4 - 0.3, d / 4 + 0.3, xtol=1e-14)
        res = np.array([d / 2, 0.0]) - build(R, L)[-1]
        L += res @ hloc
    loc = build(R, L)
    if R < R_MIN_SIN:
        raise RuntimeError(f"Z radius {R:.2f} below SiN limit")
    world = loc @ np.column_stack([u, n]).T + (np.asarray(pa, float) + np.asarray(pb, float)) / 2.0
    if math.dist(world[0], pa) > 1e-6:
        raise RuntimeError("Z fold start mismatch")
    if math.dist(world[-1], pb) > 1e-6:
        raise RuntimeError(f"Z fold end mismatch {math.dist(world[-1], pb)}")
    return world


def _zjoin(x0, y_top, y_bot, R, n=240):
    """两段半圆组成的 S 形内连接（NWG SiN 弯角规则 R >= 50）。

    端点 (x0, y_top) 与 (x0, y_bot) 同轴；上半圆圆心 (x0, y_top-R)，下半圆
    圆心 (x0, y_bot+R)，两段在 (x0, y_top-2R) 相切且切向水平。两端航向
    相同（与两条臂的端面切向一致），曲率半径 R。
    """
    out = []
    c1 = np.array([x0, y_top - R])
    for i in range(n + 1):
        a = math.pi / 2 + math.pi * i / n
        out.append(c1 + R * np.array([math.cos(a), math.sin(a)]))
    c2 = np.array([x0, y_bot + R])
    for i in range(1, n + 1):
        a = math.pi / 2 - math.pi * i / n
        out.append(c2 + R * np.array([math.cos(a), math.sin(a)]))
    return np.array(out)


def arms(n=9600):
    """两条同向（CCW）臂，外端都在顶部，局部坐标圆心在 (0,0)。

    外臂 r = 156 -> 108（4.0 圈），内臂 r = 150 -> 108（3.5 圈）；两条臂
    处处相距 6.0（5.0 间隙），都在 +y 顶部结束、朝 +x 引出。内端分别在
    (0,+108) 和 (0,-108)，用一条竖直直径段相连。

    外端先走一小段**等半径**圆弧（FLAT rad）：半径若一开始就在减小，
    外端切向会偏离水平 0.7°，端面就不是正好 90°，与顶部两条水平 link
    交接处会出现一条发丝状楔形缝。这里让外端切向严格水平。
    """
    b = PITCH_TURN / (2 * math.pi)
    out = []
    for R, T in ((R_OUT, T1), (R_OUT2, T2)):
        ps = np.linspace(0.0, 2 * math.pi * T, int(n / 4.0 * T) + 1)
        # 起始角往回挪半格：这样第一段弦严格水平，外端的端面正好 90°
        step = ps[1] - ps[0]
        a = math.pi / 2 + ps - step / 2.0
        r = R - b * np.maximum(0.0, ps - FLAT)
        out.append(np.column_stack([r * np.cos(a), r * np.sin(a)]))
    # push the two inner ends 0.4 um towards the circle centre so the S
    # connector overlaps the arm ends instead of butting them
    out[0][-1] = (0.4, R_IN)
    out[1][-1] = (0.4, -R_IN)
    return out[0], out[1]


def circle(n=9600):
    """一个圆的**完整**中心线（局部坐标，两端在顶部，朝 +x 引出）。

    包含两条臂和中间的 S 形连接，因此整体做 x 镜像时 S 连接会跟着一起
    镜像——右圆直接取 ``circle()`` 的镜像即可，不会出现连接切向错位。
    """
    A1, A2 = arms(n)
    zj = _zjoin(0.0, R_IN, -R_IN, R_IN / 2.0)
    return np.vstack([A1, zj[1:], A2[::-1][1:]])


def circle_perimeter(n=9600):
    """一个圆（两条臂 + S 连接）的中心线长度 (um)。

    FabDefine 用它把整条闭合腔的周长写成派生量：
    ``2*circle_perimeter() + 2*(DX + 0.4)``，改 R_OUT/GAP/T1 时自动跟随。
    """
    c = circle(n)
    return float(np.sum(np.linalg.norm(np.diff(c, axis=0), axis=1)))


def centerline(n=9600, ext=0.0, link_y=0.0):
    """返回 (points, info)：左圆两条臂 + 内部竖直直径段。

    ``link_y`` 是腔体**上端水平 link** 的 y（默认 0 = 纯局部坐标，不含芯片
    上的绝对高度）；圆心 y = ``link_y - R_OUT``，下端 link 在 ``link_y - ADJ``。
    绝对位置由 main.py 根据 FabDefine.SPIRAL_LINK_Y 自己加偏移，
    所以 Spiral.py 不再需要认识芯片坐标。
    """
    A1, A2 = arms(n)
    x1 = CX - DX / 2.0
    ycen = link_y - R_OUT
    off = np.array([x1, ycen])
    # S 形内连接：两段半圆，半径 R_IN/2 = 54 um（SiN 弯角 >= 50），
    # 两端切向与两条臂的端面一致（朝 -x），全部落在 r < R_IN 的空腔内。
    zj = _zjoin(0.0, R_IN, -R_IN, R_IN / 2.0)
    p_out = np.vstack([A1, zj, A2[::-1][1:]]) + off
    perim = float(np.sum(np.linalg.norm(np.diff(p_out, axis=0), axis=1)))
    info = dict(perimeter=perim, R_out=R_OUT, R_in=R_IN, gap=GAP,
                adj_pitch=ADJ, turns_per_arm=(T1, T2), z_radius=0.0,
                centers=((x1, ycen), (x1 + DX, ycen)), dx=DX, ext=ext,
                ports=((x1, link_y - ADJ), (x1, link_y)),
                link_y=(link_y - ADJ, link_y), top_y=link_y,
                length_circle=perim)
    return p_out, info


def curvature_radius(pts):
    """连续三点的最小外接圆半径（适用于非均匀采样）。"""
    p = np.asarray(pts, float)
    d = np.linalg.norm(np.diff(p, axis=0), axis=1)
    keep = np.concatenate([[True], d > 1e-9])
    p = p[keep]
    a = np.linalg.norm(p[2:] - p[:-2], axis=1)
    b = np.linalg.norm(p[1:-1] - p[:-2], axis=1)
    c = np.linalg.norm(p[2:] - p[1:-1], axis=1)
    v1 = p[1:-1] - p[:-2]
    v2 = p[2:] - p[1:-1]
    cross = np.abs(v1[:, 0] * v2[:, 1] - v1[:, 1] * v2[:, 0])
    rad = np.full_like(a, np.inf)
    good = cross > 1e-12
    rad[good] = a[good] * b[good] * c[good] / (2.0 * cross[good])
    return float(rad.min()), rad


if __name__ == "__main__":
    pts, info = centerline()
    Rmin, _ = curvature_radius(pts)
    print(info)
    print(f"Rmin={Rmin:.2f}  bbox x {pts[:,0].min():.1f}..{pts[:,0].max():.1f} "
          f"y {pts[:,1].min():.1f}..{pts[:,1].max():.1f}")
    from shapely.geometry import LineString
    ls = LineString(pts)
    print("simple:", ls.is_simple, "length:", ls.length)
    # closest approach between non-adjacent parts of the centreline
    from scipy.spatial import cKDTree
    tree = cKDTree(pts)
    d, idx = tree.query(pts, k=2)
    step = d[:, 1]
    print(f"point step min/mean/max = {step.min():.4f}/{step.mean():.4f}/"
          f"{step.max():.4f}")
    # subsample and check pairwise distance excluding a local index window
    sub = pts[::3]
    tree2 = cKDTree(sub)
    bad = []
    for i, p in enumerate(sub):
        for j in tree2.query_ball_point(p, 6.0):
            if abs(i - j) > 40:
                bad.append((i * 3, j * 3, float(np.linalg.norm(sub[i] - sub[j]))))
                break
    if bad:
        print(f"non-adjacent approach < 6.0 um: {len(bad)} points; worst "
              f"{min(b[2] for b in bad):.3f} at index {min(bad, key=lambda b: b[2])}")
    else:
        print("no non-adjacent approach below 6.0 um")

