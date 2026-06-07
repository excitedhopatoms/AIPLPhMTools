from .BasicDefine import *
from .Ring import *


# %% SingleRingIsolator0: SingleRingIsolator:ADD-DROP ring + monitor
@gf.vcell
def SingleRingIsolator0(
        r_ring: float = 120,
        r_euler_false: float = 90,
        width_ring: float = 1,
        width_near1: float = 2,
        width_near2: float = 3,
        width_heat: float = 5,
        width_single: float = 1,
        angle_rc1: float = 20,
        angle_rc2: float = 30,
        angle_th1: float = 60,
        angle_dr: float = 60,
        length_taper: float = 150,
        length_total: float = 3000,
        length_thadd: float = 100,
        pos_ring: float = 1000,
        gap_rc1: float = 1,
        gap_rc2: float = 4,
        gap_ad: float = 30,
        tout: Component = None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    åå»ºä¸ä¸ªåºäºå Add-Drop ç¯å½¢è°æ¯å¨ï¼ä½¿ç¨RingPulley1DCï¼çéç¦»å¨ååç»ä»¶ã?    åå«è¾å¥ï¼tinï¼åä¸ä¸ªè¾åºï¼toutï¼ç»ä»¶ï¼éå¸¸ç¨äºè¿æ¥åæ è¦åå¨ç­IOç»æã?    éè¿è°æ´ç¯çåæ°åè¦åï¼å¯ä»¥å®ç°ç¹å®æ³¢é¿çéç¦»ææ»¤æ³¢åè½ã?
    åæ°:
        r_ring (float): æ ¸å¿ç¯è°æ¯å¨çåå¾?(Âµm)ã?        r_euler_false (float): ç¨äºè¿æ¥è·¯å¾çæ¬§æå¼¯æ²åå¾?(Âµm)ã?        width_ring (float): ç¯åæ³¢å¯¼çå®½åº?(Âµm)ã?        width_near1 (float): ä¸»è¾å?ç´éæ»çº¿å¨è¦ååºçå®½åº¦ (Âµm)ã?        width_near2 (float): Add/Dropæ»çº¿å¨è¦ååºçå®½åº¦ (Âµm)ã?        width_heat (float): ï¼å¦æRingPulley1DCæ¯æï¼å ç­å¨çå®½åº?(Âµm)ã?        width_single (float): å¤é¨åæ¨¡æ³¢å¯¼çå®½åº?(Âµm)ã?        angle_rc1 (float): ä¸»æ»çº¿ä¸ç¯çè¦åè§åº¦ (åº?ã?        angle_rc2 (float): Add/Dropæ»çº¿ä¸ç¯çè¦åè§åº¦ (åº?ã?        angle_th1 (float): Throughç«¯å£å¼åºè·¯å¾çå¼¯æ²è§åº?(åº?ã?        angle_dr (float): Dropç«¯å£å¼åºè·¯å¾çå¼¯æ²è§åº?(åº?ã?        length_taper (float): ä»åæ¨¡æ³¢å¯¼å°è¦åæ»çº¿å®½åº¦çé¥å½¢æ¸åé¿åº?(Âµm)ã?        length_total (float): ç»ä»¶çæ»ç®æ å¸å±é¿åº¦ï¼ç¨äºå¯¹é½æå³ç«¯çIOç»ä»¶ (Âµm)ã?        length_thadd (float): Throughç«¯å£è·¯å¾ä¸çé¢å¤ç´çº¿æ³¢å¯¼é¿åº¦ (Âµm)ã?        pos_ring (float): ç¯çè¾å¥è¦åç¹çå¤§è´Xè½´åæ ?(Âµm)ã?        gap_rc1 (float): ä¸»æ»çº¿ä¸ç¯çè¦åé´é (Âµm)ã?        gap_rc2 (float): Add/Dropæ»çº¿ä¸ç¯çè¦åé´é (Âµm)ã?        gap_ad (float): Dropç«¯å£ç¸å¯¹äºThroughç«¯å£çåç´é´é?(Âµm)ï¼ä¸»è¦å½±åå¸å±ã?        tout (ComponentSpec | None): ç¨äºè¾åºç«¯å£ï¼Through, Add, Dropï¼çç»ä»¶è§æ ¼ï¼ä¾å¦åæ ï¼ã?                                     å¦æä¸?Noneï¼åä¸æ·»å ç¹å®çè¾åºç»ç«¯ç»ä»¶ã?        tin (ComponentSpec | None): ç¨äºè¾å¥ç«¯å£çç»ä»¶è§æ ¼ï¼ä¾å¦åæ ï¼ã?                                    å¦æä¸?Noneï¼åä¸æ·»å ç¹å®çè¾å¥ç»ç«¯ç»ä»¶ã?        oplayer (LayerSpec): åå­¦æ³¢å¯¼å±ã?
    è¿å:
        Component: çæçåç¯éç¦»å¨ååç»ä»¶ã?
    ç«¯å£:
        input: ç»ä»¶çæ»åå­¦è¾å¥ç«¯å£ã?        through: ç»ä»¶çç´éåå­¦ç«¯å£ã?        drop: ç»ä»¶çä¸è½½åå­¦ç«¯å£ã?        add: ç»ä»¶çå¢å åå­¦ç«¯å£ã?        RingC: ç¯ä¸­å¿çåèç¹ï¼æ¦å¿µæ§ç«¯å£ï¼ä¸ç¨äºè¿æ¥ï¼ã?    """
    if tin is None:
        tin = GfCStraight(width=width_single, length=10, layer=oplayer)
    if tout is None:
        tout = GfCStraight(width=width_single, length=10, layer=oplayer)
    sr = ComponentAllAngle()
    # Section CrossSection
    S_near1 = gf.Section(width=width_near1, layer=oplayer, port_names=("o1", "o2"))
    CS_near1 = gf.CrossSection(sections=[S_near1])
    S_near2 = gf.Section(width=width_near2, layer=oplayer, port_names=("o1", "o2"))
    CS_near2 = gf.CrossSection(sections=[S_near2])
    # component
    tinring = sr.create_vinst(tin)
    toutring_th = sr.create_vinst(tout)
    toutring_ad = sr.create_vinst(tout)
    toutring_dr = sr.create_vinst(tout)
    taper_s2n1 = gf.c.taper(width1=width_single, width2=width_near1, length=length_taper, layer=oplayer)
    taper_s2n2 = gf.c.taper(width1=width_single, width2=width_near2, length=length_taper, layer=oplayer)
    taper_s2n_in = sr.create_vinst(taper_s2n1)
    taper_s2n_th = sr.create_vinst(taper_s2n1)
    taper_s2n_ad = sr.create_vinst(taper_s2n2)
    taper_s2n_dr = sr.create_vinst(taper_s2n2)
    ring = sr.create_vinst(RingPulley1DC(
        WidthRing=width_ring, oplayer=oplayer, RadiusRing=r_ring,
        WidthNear1=width_near1, GapRing1=gap_rc1, AngleCouple1=angle_rc1,
        WidthNear2=width_near2, GapRing2=gap_rc2, AngleCouple2=angle_rc2,
        HeaterConfig=HeaterConfigClass(WidthHeat=width_heat)
    ))
    taper_s2n_in.movex(pos_ring - length_taper)
    ring.connect("Input", other=taper_s2n_in.ports["o2"], mirror=True)
    length_tout = abs(toutring_th.ports["o1"].center[0] - toutring_th.ports["o2"].center[0])
    # add
    taper_s2n_ad.connect("o2", other=ring.ports["Add"])
    toutring_ad.connect("o1", other=taper_s2n_ad.ports["o1"])
    toutring_ad.movex(length_total - length_tout - taper_s2n_ad.ports["o1"].center[0])
    # through
    bend_th1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=-angle_th1,
                                    radius=r_euler_false * 1.2))
    bend_th2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=angle_th1,
                                    radius=r_euler_false * 1.2))
    str_th1 = sr.create_vinst(GfCStraight(width=width_near1, layer=oplayer, length=length_thadd))
    bend_th1.connect("o1", other=ring.ports["Through"])
    str_th1.connect("o1", other=bend_th1.ports["o2"])
    bend_th2.connect("o1", other=str_th1.ports["o2"])
    route_off_grid(sr, bend_th2.ports["o1"], bend_th1.ports["o2"], width=width_near1, layer=oplayer, radius=150)
    taper_s2n_th.connect("o2", other=bend_th2.ports["o2"])
    toutring_th.connect("o1", other=taper_s2n_th.ports["o1"])
    toutring_th.movex(length_total - length_tout - taper_s2n_th.ports["o1"].center[0])
    # drop
    taper_s2n_dr.connect("o2", other=ring.ports["Drop"], mirror=True)
    taper_s2n_dr.move([-100, -gap_ad])
    bend_dr1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=-angle_dr,
                                    radius=r_euler_false * 1.2))
    bend_dr2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=angle_dr,
                                    radius=r_euler_false * 1.2))
    bend_dr1.connect("o1", other=ring.ports["Drop"])
    bend_dr2.connect("o1", other=bend_dr1.ports["o2"])
    route_off_grid(sr, taper_s2n_dr.ports["o2"], bend_dr2.ports["o2"], cross_section=CS_near2, radius=120)
    toutring_dr.connect("o1", other=taper_s2n_dr.ports["o1"])
    toutring_dr.movex(length_total - length_tout - taper_s2n_dr.ports["o1"].center[0])
    # route io
    route_off_grid(sr, tinring.ports["o2"], taper_s2n_in.ports["o1"], width=width_single, layer=oplayer, radius=r_euler_false)
    route_off_grid(sr, taper_s2n_ad.ports["o1"], toutring_ad.ports["o1"], width=width_single, layer=oplayer, radius=r_euler_false)
    route_off_grid(sr, taper_s2n_dr.ports["o1"], toutring_dr.ports["o1"], width=width_single, layer=oplayer, radius=r_euler_false)
    route_off_grid(sr, taper_s2n_th.ports["o1"], toutring_th.ports["o1"], width=width_single, layer=oplayer, radius=r_euler_false)
    # add_port
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("through", port=toutring_th.ports["o2"])
    sr.add_port("drop", port=toutring_dr.ports["o2"])
    sr.add_port("add", port=toutring_ad.ports["o2"])
    Rcenter = [ring.ports["RingL"].center[i] / 2 + ring.ports["RingR"].center[i] / 2 for i in range(2)]
    sr.add_port("RingC", port=sr.ports["input"], center=Rcenter)
    add_labels_to_ports(sr)
    return sr


# %% SingleRingIsolator1: SingleRingIsolator:ADD-DROP ring + monitor
@gf.vcell
def SingleRingIsolator1(
        r_ring: float = 120,
        r_euler_false: float = 100,
        r_euler_moni: float = 100,
        width_ring: float = 1,
        width_near1: float = 2,
        width_near2: float = 3,
        width_heat: float = 5,
        width_single: float = 1,
        angle_rc1: float = 20,
        angle_rc2: float = 30,
        angle_th1: float = 60,
        angle_th2: float = 60,
        length_taper: float = 150,
        length_total: float = 3000,
        length_monicouple=100,
        length_thadd: float = 100,
        pos_ring: float = 1000,
        pos_monitor: float = 500,
        gap_rc1: float = 1,
        gap_rc2: float = 4,
        gap_mc: float = 1,
        tout: Component = None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    åå»ºä¸ä¸ªå¸¦çæ§ç«¯å£çå Add-Drop ç¯å½¢è°æ¯å¨éç¦»å¨ååã?    é¤äº `SingleRingIsolator0` çåè½å¤ï¼æ­¤çæ¬å¨ä¸»è¾å¥è·¯å¾æå¢å äºä¸ä¸ªæµè¦åççæ§è·¯å¾ï¼
    ç¨äºå¼åºé¨ååä¿¡å·è¿è¡åççæ§æåé¦ãçæ§è·¯å¾æ«ç«¯å¯ä»¥è¿æ¥å°æ¢æµå¨æå¦ä¸ä¸ªIOç»ä»¶ã?
    åæ°:
        (å¤§é¨ååæ°ä¸ `SingleRingIsolator0` ç¸å)
        r_euler_moni (float): çæ§è·¯å¾ä¸­å¼¯æ²æ³¢å¯¼çåå¾ (Âµm)ã?        angle_th2 (float): Dropç«¯å£å¼åºè·¯å¾çå¼¯æ²è§åº?(åº?ã?(ååæ°åï¼å»ºè®®æ¹ä¸?angle_dr)
        length_monicouple (float): çæ§è·¯å¾ä¸ä¸»è¾å¥è·¯å¾å¹³è¡è¦åçç´çº¿æ®µé¿åº¦ (Âµm)ã?        pos_monitor (float): çæ§è¦åå¨ç¸å¯¹äºæ´ä½è¾å¥èµ·ç¹çå¤§è´Xè½´ä½ç½?(Âµm)ã?        gap_mc (float): ä¸»è¾å¥è·¯å¾ä¸çæ§è·¯å¾ä¹é´çè¦åé´é (Âµm)ã?
    è¿å:
        Component: çæçå¸¦çæ§ç«¯å£çåç¯éç¦»å¨ååç»ä»¶ã?
    ç«¯å£:
        (ä¸?`SingleRingIsolator0` ç±»ä¼¼ï¼é¢å¤å¢å?
        monitor_out: çæ§è·¯å¾çè¾åºç«¯å£ã?    """
    if tin is None:
        tin = GfCStraight(width=width_single, length=10, layer=oplayer)
    if tout is None:
        tout = GfCStraight(width=width_single, length=10, layer=oplayer)
    sr = ComponentAllAngle()
    # Section CrossSection
    S_near1 = gf.Section(width=width_near1, layer=oplayer, port_names=("o1", "o2"))
    CS_near1 = gf.CrossSection(sections=[S_near1])
    S_near2 = gf.Section(width=width_near2, layer=oplayer, port_names=("o1", "o2"))
    CS_near2 = gf.CrossSection(sections=[S_near2])
    # component
    tinring = sr.create_vinst(tin)
    toutring_th = sr.create_vinst(tout)
    toutring_ad = sr.create_vinst(tout)
    toutring_dr = sr.create_vinst(tout)
    taper_s2n1 = gf.c.taper(width1=width_single, width2=width_near1, length=length_taper, layer=oplayer)
    taper_s2n2 = gf.c.taper(width1=width_single, width2=width_near2, length=length_taper, layer=oplayer)
    taper_s2n_in = sr.create_vinst(taper_s2n1)
    taper_s2n_th = sr.create_vinst(taper_s2n1)
    taper_s2n_ad = sr.create_vinst(taper_s2n2)
    taper_s2n_dr = sr.create_vinst(taper_s2n2)
    ring = sr.create_vinst(RingPulley1DC(
        WidthRing=width_ring, oplayer=oplayer, RadiusRing=r_ring,
        WidthNear1=width_near1, GapRing1=gap_rc1, AngleCouple1=angle_rc1,
        WidthNear2=width_near2, GapRing2=gap_rc2, AngleCouple2=angle_rc2,
        HeaterConfig=HeaterConfigClass(WidthHeat=width_heat)
    ))
    taper_s2n_in.movex(pos_ring - length_taper)
    ring.connect("Input", other=taper_s2n_in.ports["o2"], mirror=True)
    length_tout = abs(toutring_th.ports["o1"].center[0] - toutring_th.ports["o2"].center[0])
    # add
    taper_s2n_ad.connect("o2", other=ring.ports["Add"])
    toutring_ad.connect("o1", other=taper_s2n_ad.ports["o1"])
    toutring_ad.movex(length_total - length_tout - taper_s2n_ad.ports["o1"].center[0])
    # through
    bend_th1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=-angle_th1,
                                    radius=r_euler_false * 1.2))
    bend_th2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=angle_th1,
                                    radius=r_euler_false * 1.2))
    bend_th1.connect("o1", other=ring.ports["Through"])
    bend_th2.connect("o1", other=bend_th1.ports["o2"])
    route_off_grid(sr, bend_th2.ports["o1"], bend_th1.ports["o2"], width=width_near1, layer=oplayer, radius=150)
    taper_s2n_th.connect("o2", other=bend_th2.ports["o2"])
    toutring_th.connect("o1", other=taper_s2n_th.ports["o1"])
    toutring_th.movex(length_total - length_tout - taper_s2n_th.ports["o1"].center[0])
    # drop
    taper_s2n_dr.connect("o2", other=ring.ports["Drop"], mirror=True)
    taper_s2n_dr.move([-100, -30])
    bend_dr1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=-angle_th2,
                                    radius=r_euler_false * 1.2))
    bend_dr2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=angle_th2,
                                    radius=r_euler_false * 1.2))
    bend_dr1.connect("o1", other=ring.ports["Drop"])
    bend_dr2.connect("o1", other=bend_dr1.ports["o2"])
    route_off_grid(sr, taper_s2n_dr.ports["o2"], bend_dr2.ports["o2"], cross_section=CS_near2, radius=120)
    toutring_dr.connect("o1", other=taper_s2n_dr.ports["o1"])
    toutring_dr.movex(length_total - length_tout - taper_s2n_dr.ports["o1"].center[0])
    # monitor
    str_moni = sr.create_vinst(GfCStraight(length=length_monicouple, width=width_single, layer=oplayer))
    str_moni.connect("o1", other=taper_s2n_in.ports["o1"])
    str_moni.movey(-width_single - gap_mc)
    taper_moni = sr.create_vinst(OffsetRamp(width1=width_single, width2=0.002, offset=width_single / 2, length=50, layer=oplayer))
    taper_moni.connect("o1", other=str_moni.ports["o1"])
    bend_moni = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_single, radius=r_euler_moni, layer=oplayer, angle=90))
    bend_moni.connect("o1", other=str_moni.ports["o2"])
    toutring_mn = sr.create_vinst(tout)
    toutring_mn.connect("o1", other=toutring_dr.ports["o1"], mirror=True)
    toutring_mn.movey(-127)
    str_moni_out = sr.create_vinst(GfCStraight(width=width_single,
                                    length=toutring_mn.ports["o1"].center[0] - taper_s2n_dr.ports["o1"].center[0]))
    str_moni_out.connect("o2", other=toutring_mn.ports["o1"])
    # route io
    CS_single = gf.CrossSection(sections=[gf.Section(width=width_single, layer=oplayer, port_names=("o1", "o2"))])
    route_off_grid(sr, tinring.ports["o2"], taper_s2n_in.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    route_off_grid(sr, taper_s2n_ad.ports["o1"], toutring_ad.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    route_off_grid(sr, taper_s2n_dr.ports["o1"], toutring_dr.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    route_off_grid(sr, taper_s2n_th.ports["o1"], toutring_th.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    route_off_grid(sr, bend_moni.ports["o2"], str_moni_out.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    # add_port
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("through", port=toutring_th.ports["o2"])
    sr.add_port("drop", port=toutring_dr.ports["o2"])
    sr.add_port("add", port=toutring_ad.ports["o2"])
    Rcenter = [ring.ports["RingL"].center[i] / 2 + ring.ports["RingR"].center[i] / 2 for i in range(2)]
    sr.add_port("RingC", port=sr.ports["input"], center=Rcenter)
    add_labels_to_ports(sr)
    return sr


# %% RingAndIsolator0:Ring and SingleRingIsolator0: ring for comb and ADD-DROP ring
@gf.vcell
def RingAndIsolator0(
        r_ring: float = 120,
        r_euler_false: float = 100,
        width_ring: float = 1,
        width_Cring: float = None,
        width_near1: float = 2,
        width_near2: float = 3,
        width_nearC: float = 4,
        width_heat: float = 5,
        width_single: float = 1,
        angle_rc1: float = 20,
        angle_rc2: float = 30,
        angle_th1: float = 60,
        angle_dr: float = 60,
        angle_Cring: float = 20,
        length_taper: float = 150,
        length_total: float = 3000,
        length_thadd: float = 100,
        pos_ring: float = 1000,
        pos_Cring: float = 300,
        gap_rc1: float = 1,
        gap_rc2: float = 4,
        gap_ad: float = 30,
        gap_Cring: float = 1,
        tout: Component = None,
        tin: Component = None,
        oplayer: LayerSpec = LAYER.WG,
) -> Component:
    """
    åå»ºä¸ä¸ªéæç»ä»¶ï¼åå«ä¸ä¸ªç¨äºåæ¢³çæçç¯å½¢è°æ¯å¨ï¼æ¢³ç¶ç¯ï¼åä¸ä¸?    `SingleRingIsolator0` ç±»åçåç¯éç¦»å¨ååãä¸¤èéå¸¸ä¸²èå¨åä¸åè·¯ä¸­ï¼
    åç»è¿æ¢³ç¶ç¯ï¼åè¿å¥éç¦»å¨ã?
    åæ°:
        (å¤§é¨ååæ°ä¸ `SingleRingIsolator0` ç¸åï¼ç¨äºéç½®éç¦»å¨é¨å)
        width_Cring (float | None): æ¢³ç¶ç¯çæ³¢å¯¼å®½åº¦ (Âµm)ãå¦æä¸º Noneï¼åä½¿ç¨ä¸éç¦»å¨ç¯ç¸åçå®½åº¦ (`width_ring`)ã?        width_nearC (float): æ¢³ç¶ç¯è¦ååºåçæ»çº¿æ³¢å¯¼å®½åº¦ (Âµm)ã?        angle_Cring (float): æ¢³ç¶ç¯çè¦åè§åº¦ (åº?ã?        pos_Cring (float): æ¢³ç¶ç¯è¾å¥è¦åç¹çå¤§è´Xè½´åæ ?(Âµm)ã?        gap_Cring (float): æ¢³ç¶ç¯ä¸æ»çº¿çè¦åé´é (Âµm)ã?
    è¿å:
        Component: çæçæ¢³ç¶ç¯+éç¦»å¨éæç»ä»¶ã?
    ç«¯å£: (ä¸?`SingleRingIsolator0` ç±»ä¼¼)
        input, through, drop, add: ç»ä»¶çä¸»è¦åå­¦ç«¯å£ã?        RingC_iso: éç¦»å¨ç¯ä¸­å¿çåèç¹ã?        RingC_comb: æ¢³ç¶ç¯ä¸­å¿çåèç¹ã?    """
    if tin is None:
        tin = GfCStraight(width=width_single, length=10, layer=oplayer)
    if tout is None:
        tout = GfCStraight(width=width_single, length=10, layer=oplayer)
    sr = ComponentAllAngle()
    if width_Cring == None:
        width_Cring = width_ring
    # Section CrossSection
    S_near1 = gf.Section(width=width_near1, layer=oplayer, port_names=("o1", "o2"))
    CS_near1 = gf.CrossSection(sections=[S_near1])
    S_near2 = gf.Section(width=width_near2, layer=oplayer, port_names=("o1", "o2"))
    CS_near2 = gf.CrossSection(sections=[S_near2])
    # component
    tinring = sr.create_vinst(tin)
    toutring_th = sr.create_vinst(tout)
    toutring_ad = sr.create_vinst(tout)
    toutring_dr = sr.create_vinst(tout)
    taper_s2n1 = gf.c.taper(width1=width_single, width2=width_near1, length=length_taper, layer=oplayer)
    taper_s2n2 = gf.c.taper(width1=width_single, width2=width_near2, length=length_taper, layer=oplayer)
    taper_s2n_in = sr.create_vinst(taper_s2n1)
    taper_s2n_th = sr.create_vinst(taper_s2n1)
    taper_s2n_ad = sr.create_vinst(taper_s2n2)
    taper_s2n_dr = sr.create_vinst(taper_s2n2)
    ring_comb = sr.create_vinst(RingPulley(
        WidthRing=width_Cring, WidthNear=width_nearC,
        RadiusRing=r_ring, GapRing=gap_Cring, AngleCouple=angle_Cring,
        IsAD=False, oplayer=oplayer,
    ))
    ring_iso = sr.create_vinst(RingPulley1DC(
        WidthRing=width_ring, oplayer=oplayer, RadiusRing=r_ring,
        WidthNear1=width_near1, GapRing1=gap_rc1, AngleCouple1=angle_rc1,
        WidthNear2=width_near2, GapRing2=gap_rc2, AngleCouple2=angle_rc2,
        HeaterConfig=HeaterConfigClass(WidthHeat=width_heat)
    ))
    taper_s2n_in.movex(pos_ring - length_taper)
    ring_iso.connect("Input", other=taper_s2n_in.ports["o2"], mirror=True)
    ring_comb.connect("Input", other=taper_s2n_in.ports["o2"], allow_width_mismatch=True, mirror=True)
    ring_comb.movex(pos_Cring - pos_ring)
    length_tout = abs(toutring_th.ports["o1"].center[0] - toutring_th.ports["o2"].center[0])
    # comb ring taper
    taper_s2CRin = sr.create_vinst(gf.c.taper(width2=width_nearC, width1=width_single, length=length_taper, layer=oplayer))
    taper_CRout2s = sr.create_vinst(gf.c.taper(width2=width_single, width1=width_nearC, length=length_taper, layer=oplayer))
    taper_s2CRin.connect("o2", ring_comb.ports["Input"])
    taper_CRout2s.connect("o1", ring_comb.ports["Through"])

    # add
    taper_s2n_ad.connect("o2", other=ring_iso.ports["Add"])
    toutring_ad.connect("o1", other=taper_s2n_ad.ports["o1"])
    toutring_ad.movex(length_total - length_tout - taper_s2n_ad.ports["o1"].center[0])
    # through
    bend_th1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=-angle_th1,
                                     radius=r_euler_false * 1.2))
    bend_th2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near1, layer=oplayer, angle=angle_th1,
                                     radius=r_euler_false * 1.2))
    str_th1 = sr.create_vinst(GfCStraight(width=width_near1, layer=oplayer, length=length_thadd))
    bend_th1.connect("o1", other=ring_iso.ports["Through"])
    str_th1.connect("o1", other=bend_th1.ports["o2"])
    bend_th2.connect("o1", other=str_th1.ports["o2"])
    route_off_grid(sr, bend_th2.ports["o1"], bend_th1.ports["o2"], width=width_near1, layer=oplayer, radius=150)
    taper_s2n_th.connect("o2", other=bend_th2.ports["o2"])
    toutring_th.connect("o1", other=taper_s2n_th.ports["o1"])
    toutring_th.movex(length_total - length_tout - taper_s2n_th.ports["o1"].center[0])
    # drop
    taper_s2n_dr.connect("o2", other=ring_iso.ports["Drop"], mirror=True)
    taper_s2n_dr.move([-100, -gap_ad])
    bend_dr1 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=-angle_dr,
                                     radius=r_euler_false * 1.2))
    bend_dr2 = sr.add_ref_off_grid(gf.c.bend_euler_all_angle(width=width_near2, layer=oplayer, angle=angle_dr,
                                     radius=r_euler_false * 1.2))
    bend_dr1.connect("o1", other=ring_iso.ports["Drop"])
    bend_dr2.connect("o1", other=bend_dr1.ports["o2"])
    route_off_grid(sr, taper_s2n_dr.ports["o2"], bend_dr2.ports["o2"], cross_section=CS_near2, radius=120)
    toutring_dr.connect("o1", other=taper_s2n_dr.ports["o1"])
    toutring_dr.movex(length_total - length_tout - taper_s2n_dr.ports["o1"].center[0])
    # route io
    CS_single = gf.CrossSection(sections=[gf.Section(width=width_single, layer=oplayer, port_names=("o1", "o2"))])
    route_off_grid(sr, tinring.ports["o2"], taper_s2CRin.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    route_off_grid(sr, taper_CRout2s.ports["o2"], taper_s2n_in.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    route_off_grid(sr, taper_s2n_ad.ports["o1"], toutring_ad.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    route_off_grid(sr, taper_s2n_dr.ports["o1"], toutring_dr.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    route_off_grid(sr, taper_s2n_th.ports["o1"], toutring_th.ports["o1"], cross_section=CS_single, radius=r_euler_false)
    # add_port
    sr.add_port("input", port=tinring.ports["o1"])
    sr.add_port("through", port=toutring_th.ports["o2"])
    sr.add_port("drop", port=toutring_dr.ports["o2"])
    sr.add_port("add", port=toutring_ad.ports["o2"])
    Rcenter = [ring_iso.ports["RingL"].center[i] / 2 + ring_iso.ports["RingR"].center[i] / 2 for i in range(2)]
    sr.add_port("RingC", port=sr.ports["input"], center=Rcenter)
    add_labels_to_ports(sr)
    return sr
