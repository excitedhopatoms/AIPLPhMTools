# TC 测试结构同层 WG 重叠审计

审计对象：`AIPLPhMTools.list_components()` 中所有 `TC*` 器件（27 个）。
审计层：`WG (1/0)`；阈值：`0.01 µm²`。
审计方法：对每个 cell 的直接子 instance 两两求 WG Region 交叠；butt joint
只共享边，面积为 0；`ComponentAllAngle` 走 `vinsts`。

可复现脚本：

```bash
python AIPLPhMTools/examples/tc_overlap_audit.py
```

## 本轮已修

| 问题 | 处理 |
|---|---|
| `Crossing_taper` 四条 taper 臂在中心四角互相压住，每处 0.28 µm² | 中心方块取 `max(WidthCross, WidthWg)`，臂偏移取 `WidthCross/2`；自重叠归零 |
| `CoupleDouRaceTrack` 的 **S 型**两环间距少 2×WidthRing，环体交叠 3.8 µm² | `movex(+2*WidthRing + GapCoupleIn)`；S 型交叠归零 |

## 仍需设计确认的重叠

以下为 `area > 0.1 µm²` 的实质性交叠。它们不是“数值噪声”，但多数涉及
P 型跑道环耦合面、Boomerang 共用臂或 TC 引出臂的拓扑，需要先确认设计意图
再改，避免擅自改变器件拓扑。

| 器件 | 面积 (µm²) | 位置 | 说明 |
|---|---:|---|---|
| `TCCoupleDouRaceTrackT1` | 3.832 | (-114.4, 76.4; 117.4, 90.7) | P 型双跑道环环体 |
| `TCCoupleDouRaceTrackT2` | 10.183 | (-118.1, 88.9; 121.1, 276.1) | P 型双跑道环环体 |
| `TCFingerRing1` | 3.721 / 3.722 | (190.3,-485.8; 322.7,-484.8) 等 | Finger 环与引出直波导 |
| `TCRaceTrackS2` | 119.871 | (12494.8,-2223.9; 12632.1,-2221.9) | taper 与输出 bend 长距离交叠 |
| `TCRaceTrackS2` | 8.208 | (11905.6,-1796.6; 11908.4,-1788.2) | 跑道环与 bend |
| `TCRing1DC` | 23.613 | (2885.9,-450.2; 3000.0,-449.8) | 直波导与 taper |
| `TCRing1DC` | 38.639 | (2810.2,-450.4; 2885.9,-449.5) | 直波导与直波导 |
| `TCRing4` | 3.553 | (781.8,-0.9; 783.7,0.9) | 两个 taper 十字交叠 |
| `TCRingDCouple` | 5.129 | (330.6,117.7; 332.8,122.3) | 两个 bend 交叠 |
| `TCRingDouBoomerangT1` | 140.979 | (-375.0,-375.0; 37.0,37.0) | 两个 Boomerang 共用臂，可能是设计意图 |
| `TCRingTriBoomerangT1` | 149.064 ×2 | (-425.0,-425.0; 37.0,37.0) 等 | 三个 Boomerang 共用臂，可能是设计意图 |
| `TCTaperRaceTrackS` | 52.777 | (5820.6,-1624.1; 5839.6,-1620.2) | 锥形跑道环与 taper |

## 小面积接头重叠（0.8–2.0 µm²）

`TCCoupleDouRaceTrackT1/T2`、`TCFingerRing1` 的部分 0.8–2.0 µm² 交叠位于
引出臂与 taper/straight 的接点，表现为 0.8–2 µm 的矩形。它们不是环体互相
压住，更像 `route_single` 末端多走了 0.8–2 µm；可在引出臂定稿时统一裁短。

## 数值级残差（< 0.01 µm²）

`TCRaceTrackP/S/S2/S3/S3h` 各有 0.008 µm² 的细条，位于 ±2014 µm 的端口
附近，属于坐标取整/网格吸附残差，不构成短路。

## 无重叠的 TC 器件

`TCCoupleDouRingT1`、`TCFingerRing1` 以外的 `TCRing` 系列、`TCRing2*`、
`TCRing3`、`TCRingBoomerangT1`、`TCRingCoupon`、`TCRingT1/T2`、
`TCTaperRaceTrackP`、`TCRing1AD` 等为 0。
