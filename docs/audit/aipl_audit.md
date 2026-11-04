# AIPLPhMTools audit

- components: 96
- build fail: 0
- with flags: 32
- with WG/CPF overlap: 28

## Flagged components

| component | build | flags | min R < 50 | overlaps |
|---|---|---|---|---|
| Boomerang | OK | optical_port_non_manhattan | 0 | {'(1, 0)': 0.002} |
| Complete_Inverted_Device | OK | - | 0 | {'(1, 0)': 42.35} |
| CoupleDouRaceTrack | OK | - | 0 | {'(1, 0)': 0.031996} |
| CoupleRingDRT1 | OK | optical_port_non_manhattan | 0 | - |
| DBR | OK | width_step_at_joint | 0 | - |
| DoubleRaceTrack | OK | - | 0 | {'(1, 0)': 0.031992} |
| EDBRStrRep | OK | - | 0 | {'(1, 0)': 42.35} |
| EDBRStrRep_InvertTone | OK | - | 0 | {'(1, 0)': 42.35} |
| ExtCavDouRaceTrack | OK | - | 0 | {'(1, 0)': 2.401138} |
| ExtCavTriRing2 | OK | io_port_not_0_180, optical_port_non_manhattan | 0 | - |
| FeedbackRing | OK | optical_port_non_manhattan | 3 | - |
| GfCBendEuler | OK | - | 1 | - |
| OptFeedbackRing | OK | optical_port_non_manhattan | 2 | - |
| OptPDCSagnacLoop | OK | io_port_not_0_180, optical_port_non_manhattan | 0 | - |
| PMZI | OK | io_port_not_0_180 | 0 | - |
| PMZIHSn | OK | io_port_not_0_180 | 0 | - |
| PulleyCoupler2X2 | OK | optical_port_non_manhattan | 0 | - |
| RaceTrackP | OK | - | 0 | {'(1, 0)': 0.015996} |
| RaceTrackS | OK | io_port_not_0_180 | 0 | {'(1, 0)': 0.003998} |
| RaceTrackStrHC | OK | io_port_not_0_180 | 0 | - |
| RingAndIsolator0 | OK | dangling_bend_end | 0 | - |
| RingBoomerang | OK | io_port_not_0_180 | 0 | {'(1, 0)': 0.00225} |
| RingDouBoomerang | OK | optical_port_non_manhattan | 0 | {'(1, 0)': 0.0045} |
| RingPulley2 | OK | io_port_not_0_180, optical_port_non_manhattan | 0 | - |
| RingPulley2ES | OK | io_port_not_0_180, optical_port_non_manhattan | 0 | - |
| RingPulley3 | OK | io_port_not_0_180 | 0 | - |
| RingPulley4 | OK | io_port_not_0_180, optical_port_non_manhattan | 0 | - |
| RingPulleyT2 | OK | io_port_not_0_180, optical_port_non_manhattan | 0 | - |
| RingTriBoomerang | OK | io_port_not_0_180, optical_port_non_manhattan | 0 | {'(1, 0)': 0.00675} |
| SingleRingIsolator0 | OK | dangling_bend_end | 0 | - |
| SingleRingIsolator1 | OK | dangling_bend_end | 0 | - |
| TCCoupleDouRaceTrackT1 | OK | - | 0 | {'(1, 0)': 9.225208} |
| TCCoupleDouRaceTrackT2 | OK | io_port_not_0_180 | 0 | {'(1, 0)': 18.186533} |
| TCCoupleDouRingT1 | OK | optical_port_non_manhattan | 0 | - |
| TCFingerRing1 | OK | - | 0 | {'(1, 0)': 11.772134} |
| TCRaceTrackP | OK | - | 2 | {'(1, 0)': 0.015999} |
| TCRaceTrackS | OK | - | 0 | {'(1, 0)': 0.015999} |
| TCRaceTrackS2 | OK | coincident_ports_not_opposite | 0 | {'(1, 0)': 128.008706} |
| TCRaceTrackS3 | OK | - | 0 | {'(1, 0)': 0.015999} |
| TCRaceTrackS3h | OK | - | 0 | {'(1, 0)': 0.015999} |
| TCRing2 | OK | optical_port_non_manhattan | 0 | {'(1, 0)': 0.0015} |
| TCRing2_2 | OK | optical_port_non_manhattan | 0 | {'(1, 0)': 0.00175} |
| TCRing2_3 | OK | optical_port_non_manhattan | 0 | {'(1, 0)': 0.00425} |
| TCRing4 | OK | - | 0 | {'(1, 0)': 3.596454} |
| TCRingCoupon | OK | io_port_not_0_180 | 0 | - |
| TCRingDCouple | OK | - | 0 | {'(1, 0)': 5.1296} |
| TCRingDouBoomerangT1 | OK | - | 0 | {'(1, 0)': 140.974197} |
| TCRingT2 | OK | optical_port_non_manhattan | 0 | - |
| TCRingTriBoomerangT1 | OK | - | 0 | {'(1, 0)': 298.152333} |
| TCTaperRaceTrackS | OK | - | 0 | {'(1, 0)': 52.682324} |
| TaperRsoa | OK | optical_port_non_manhattan | 0 | - |

## All components

| component | ports | size | min R | flags |
|---|---|---|---|---|
| ADRAPRADR | 12 | 792.037x460.7 | - | - |
| Boomerang | 8 | 634.057x634.057 | 77.67 | optical_port_non_manhattan |
| CROW | 8 | 324.6x82.2 | - | - |
| Complete_Inverted_Device | 2 | 510.0x8.0 | - | - |
| CoupleDouRaceTrack | 4 | 465.45x562.87 | - | - |
| CoupleRingDRT1 | 4 | 338.786x415.623 | - | optical_port_non_manhattan |
| CoupledRingFilter | 6 | 260.0x404.6 | - | - |
| Crossing_taper | 4 | 201.0x201.0 | - | - |
| DBR | 2 | 90.0x2.0 | - | width_step_at_joint |
| DMZI | 6 | 1779.424x206.19 | - | - |
| DispersionRingRow | 8 | 4600.0x459.441 | 129.0 | - |
| DoubleRaceTrack | 11 | 602.44x455.871 | - | - |
| DoubleRingMemyshev | 11 | 1195.096x1397.272 | 70.609 | - |
| DoubleRingPulley | 11 | 441.037x206.8 | - | - |
| DoubleRingPulley2HSn | 11 | 441.037x206.8 | - | - |
| DoubleRingPulley2_1HSn | 11 | 991.037x206.8 | 63.548 | - |
| EDBRStrRep | 2 | 110.0x1.1 | - | - |
| EDBRStrRep_InvertTone | 2 | 110.0x8.0 | - | - |
| EDBRStrRep_InvertTone_Full | 2 | 510.0x9.1 | - | - |
| ExtCavDouRaceTrack | 8 | 2059.388x719.88 | 70.609 | - |
| ExtCavDouRing | 8 | 1759.258x691.829 | 54.627 | - |
| ExtCavDouRing2 | 8 | 3027.786x690.808 | 1797.238 | - |
| ExtCavDouRing3 | 11 | 2655.694x706.094 | 101.619 | - |
| ExtCavTriRing | 8 | 1909.258x691.829 | 93.744 | - |
| ExtCavTriRing2 | 14 | 1426.996x1043.593 | 81.09 | io_port_not_0_180, optical_port_non_manhattan |
| ExtCavTriRing2_2 | 8 | 1285.645x1063.932 | - | - |
| ExtCavWang | 8 | 1621.347x834.14 | 67.575 | - |
| FeedbackRing | 6 | 401.361x220.495 | 34.689 | optical_port_non_manhattan |
| GSGELE | 10 | 10000.0x197.0 | - | - |
| GfCBendEuler | 2 | 10.25x10.25 | 7.061 | - |
| GfCStraight | 2 | 10.0x1.0 | - | - |
| GongCavity | 6 | 361.0x359.562 | - | - |
| OffsetRamp | 2 | 10.0x5.0 | - | - |
| OpenPad | 4 | 110.0x110.0 | - | - |
| OptFeedbackRing | 6 | 416.397x243.053 | 34.689 | optical_port_non_manhattan |
| OptMMISagnacLoop | 2 | 188.19x104.9 | 60.033 | - |
| OptPDCSagnacLoop | 2 | 244.178x104.9 | - | io_port_not_0_180, optical_port_non_manhattan |
| PMZI | 4 | 1421.247x389.247 | - | io_port_not_0_180 |
| PMZIHSn | 8 | 1280.671x327.08 | - | io_port_not_0_180 |
| PulleyCoupler2X2 | 4 | 96.794x7.506 | - | optical_port_non_manhattan |
| RaceTrackP | 12 | 209.014x454.871 | - | - |
| RaceTrackS | 14 | 229.436x437.871 | - | io_port_not_0_180 |
| RaceTrackStrHC | 10 | 1139.5x1469.202 | - | io_port_not_0_180 |
| RingAndIsolator0 | 5 | 3000.0x280.174 | 81.978 | dangling_bend_end |
| RingBoomerang | 4 | 646.057x646.057 | 77.67 | io_port_not_0_180 |
| RingCouponRow | 3 | 10000.0x581.878 | 200.0 | - |
| RingDouBoomerang | 20 | 807.445x819.445 | 77.67 | optical_port_non_manhattan |
| RingFinger | 6 | 1192.127x593.003 | - | - |
| RingPulley | 7 | 201.0x204.8 | - | - |
| RingPulley1DC | 7 | 201.0x206.9 | - | - |
| RingPulley1HS | 9 | 2024.0x2223.305 | - | - |
| RingPulley1HSn | 9 | 2024.0x2004.8 | - | - |
| RingPulley2 | 7 | 240.654x202.9 | - | io_port_not_0_180, optical_port_non_manhattan |
| RingPulley2ES | 11 | 240.654x229.496 | - | io_port_not_0_180, optical_port_non_manhattan |
| RingPulley3 | 4 | 210.012x202.9 | - | io_port_not_0_180 |
| RingPulley4 | 4 | 204.9x252.651 | - | io_port_not_0_180, optical_port_non_manhattan |
| RingPulleyT1 | 7 | 201.0x204.8 | - | - |
| RingPulleyT2 | 7 | 240.654x202.9 | - | io_port_not_0_180, optical_port_non_manhattan |
| RingTriBoomerang | 28 | 1066.833x1066.833 | 77.67 | io_port_not_0_180, optical_port_non_manhattan |
| SCISSOR | 6 | 389.0x82.2 | - | - |
| SagnacRing | 4 | 822.236x428.93 | 70.609 | - |
| SingleRingIsolator0 | 5 | 3000.0x280.174 | 73.78 | dangling_bend_end |
| SingleRingIsolator1 | 5 | 3000.0x406.174 | 70.609 | dangling_bend_end |
| TCCoupleDouRaceTrackT1 | 21 | 10000.0x803.69 | 100.0 | - |
| TCCoupleDouRaceTrackT2 | 21 | 5021.0x10000.0 | 70.609 | io_port_not_0_180 |
| TCCoupleDouRingT1 | 4 | 10000.0x497.684 | 100.0 | optical_port_non_manhattan |
| TCFingerRing1 | 3 | 10000.0x597.051 | 141.218 | - |
| TCRaceTrackP | 13 | 5710.423x4028.286 | 20.0 | - |
| TCRaceTrackS | 2 | 7663.849x4241.497 | 529.567 | - |
| TCRaceTrackS2 | 1 | 6013.849x4241.497 | 529.567 | coincident_ports_not_opposite |
| TCRaceTrackS3 | 1 | 5105.423x4241.497 | - | - |
| TCRaceTrackS3h | 1 | 5105.423x4241.497 | - | - |
| TCRing | 3 | 10000.0x671.878 | 200.0 | - |
| TCRing1AD | 5 | 2555.393x677.007 | 105.913 | - |
| TCRing1DC | 5 | 3035.885x1660.873 | 204.944 | - |
| TCRing1_3 | 3 | 10000.0x244.0 | - | - |
| TCRing2 | 4 | 10000.0x1015.327 | 200.0 | optical_port_non_manhattan |
| TCRing2_2 | 4 | 10000.0x927.427 | 200.0 | optical_port_non_manhattan |
| TCRing2_3 | 4 | 10000.0x999.325 | 200.0 | optical_port_non_manhattan |
| TCRing3 | 3 | 10000.5x1266.058 | 145.261 | - |
| TCRing4 | 3 | 10000.5x901.0 | 211.827 | - |
| TCRingBoomerangT1 | 4 | 10000.0x1183.002 | 70.609 | - |
| TCRingCoupon | 10 | 690.712x383.747 | 100.0 | io_port_not_0_180 |
| TCRingDCouple | 3 | 10000.0x1053.735 | 200.0 | - |
| TCRingDouBoomerangT1 | 14 | 10000.0x1459.885 | 70.609 | - |
| TCRingT1 | 3 | 10000.0x581.878 | 200.0 | - |
| TCRingT2 | 4 | 2000.0x937.726 | 200.0 | optical_port_non_manhattan |
| TCRingTriBoomerangT1 | 14 | 4000.0x1797.703 | 70.609 | - |
| TCTaperRaceTrackP | 1 | 5844.896x4245.246 | 529.567 | - |
| TCTaperRaceTrackS | 1 | 6344.896x4028.286 | 529.567 | - |
| TaperRaceTrackPulley | 10 | 309.522x764.306 | - | - |
| TaperRsoa | 2 | 304.459x75.28 | - | optical_port_non_manhattan |
| TriRingPulley | 11 | 591.037x206.8 | - | - |
| WangCavity | 6 | 361.0x359.562 | - | - |
| cir2end | 1 | 150.25x100.75 | - | - |
| ring_coupon | 3 | 10000.0x581.878 | 200.0 | - |