"""Routes for minipc-power, block by block (coordinates as data; see tools/routing.py).

Layer plan (docs/layout-plan.md):
  F.Cu   parts; power pours per net (VBUS, SW nodes, converter VIN/VOUT, protection chain); GND pour fills the rest
  In1.Cu solid GND plane - no tracks
  In2.Cu VSYS plane (the hub: charger -> 12 V, 5 V, 3.3 V converters, LED, switch pad)
  B.Cu   GND pour; BAT (charger <-> fuse, up to ~5.6 A) as a wide pour; slow signals (EN, status) as tracks
"""
X0, Y0, X1, Y1 = 100.0, 100.0, 152.0, 136.0


def planes(r):
    m = 0.3
    r.rect('GND', 'In1.Cu', X0 + m, Y0 + m, X1 - m, Y1 - m, prio=0, name='GND_PLANE')
    vsys = r.net('U2', '15')
    r.rect(vsys, 'In2.Cu', X0 + m, Y0 + m, X1 - m, Y1 - m, prio=0, name='VSYS_PLANE')
    r.rect('GND', 'F.Cu', X0 + m, Y0 + m, X1 - m, Y1 - m, prio=0, name='GND_TOP')
    r.rect('GND', 'B.Cu', X0 + m, Y0 + m, X1 - m, Y1 - m, prio=0, name='GND_BOTTOM')


AGND = {('R2', '2'), ('R3', '2'), ('R5', '2')}   # charger analog ground: single point at U2's pad, no plane vias


def stitch_pads(r):
    """A via beside every SMD GND and VSYS pad, so every one reaches its plane directly."""
    vsys = r.net('U2', '15')
    for (ref, num), lst in sorted(r.pads.items()):
        p = lst[0]
        if p['th'] or p['net'] not in ('GND', vsys) or ref.startswith(('U', 'J', 'H')) or (ref, num) in AGND:
            continue
        r.via_near(ref, num)




def usb_pd(r):
    """J1 -> U1 (CH224Q, rot 90: CC2/CC1/VBUS/CFG1/PG on the left column) and VBUS to the charger.
    CC1 stays on F.Cu; CC2 crosses under it on B.Cu (J1 has CC1 above CC2, U1 the reverse)."""
    W = 0.2
    cc1 = r.net('U1', '7')
    r.track('F.Cu', W, ('J1', 'A5'), (109.2, 120.25), (109.2, 121.1), ('U1', '7'))
    r.track('F.Cu', W, ('J1', 'B5'), (108.8, 123.25))
    cc2 = r.net('U1', '6')
    r.via((108.8, 123.25), cc2, 0.45, 0.2)
    r.track('B.Cu', W, (108.8, 123.25), (108.8, 121.5), (109.75, 120.55), net=cc2)
    r.via((109.75, 120.55), cc2, 0.45, 0.2)
    r.track('F.Cu', W, (109.75, 120.55), (109.9, 120.7), ('U1', '6'))
    vbus = r.net('U1', '8')
    # second VBUS pad group (A9/B4) -> U1 VBUS pin, and to the main VBUS copper on B.Cu (under the connector)
    r.track('F.Cu', 0.3, ('J1', 'A9'), (109.4, 123.95), (109.4, 121.75))
    r.track('F.Cu', 0.2, (109.4, 121.75), (109.65, 121.5), ('U1', '8'))
    r.track('F.Cu', 0.4, (108.9, 123.95), (108.9, 124.45), net=vbus)     # straight down: clears A12 (GND)
    r.via((108.9, 124.45), vbus)
    r.track('B.Cu', 0.5, (108.9, 124.45), (107.3, 124.45), (107.3, 118.55), (108.95, 118.55), net=vbus)
    r.via((108.95, 118.55), vbus)
    # CFG1 -> R1 (6.8 k to GND)
    r.track('F.Cu', W, ('U1', '9'), (109.95, 121.9), (109.95, 122.9), (110.54, 123.49), ('R1', '1'))
    # U1 exposed pad
    r.via(r.P('U1', '11'), 'GND', 0.45, 0.2, check=False)
    # VBUS copper: connector top group, TVS, charger VBUS cap
    r.zone(vbus, 'F.Cu', [(107.0, 118.65), (109.2, 118.65), (109.2, 115.9), (116.0, 115.9), (116.0, 120.45),
                          (110.0, 120.45), (110.0, 120.0), (109.2, 120.0), (109.2, 119.45), (107.0, 119.45)],
           prio=10, name='VBUS_IN')
    # VHV (U1 pin 1) -> C1 -> charger VBUS pins
    r.track('F.Cu', 0.25, ('U1', '1'), (112.9, 122.3), (113.6, 123.0), ('C1', '1'))
    r.track('F.Cu', 0.3, ('C1', '1'), (114.9, 123.08), (114.9, 121.0), (115.6, 120.955), ('U2', '1'))
    r.track('F.Cu', 0.3, ('C2', '1'), (115.6, 120.0), (115.6, 120.955))
    r.track('F.Cu', 0.25, ('U2', '1'), (117.345, 120.25), ('U2', '24'))


def charger(r):
    """BQ25606 (U2), per datasheet s12 / fig. 12-2: PMID, REGN, BTST caps at their pins; SW node small, straight to L1;
    C_SYS (C5) against SYS pins 15/16 with its ground tied to GND pins 17/18 on top copper; C_BAT under the BAT bar;
    ILIM / ICHG / TS resistors on an analog-ground track that joins power ground only at GND pin 9 -> thermal pad."""
    r.track('F.Cu', 0.3, ('U2', '23'), (117.85, 118.35), net=r.net('U2', '23'))           # PMID -> C3
    r.track('F.Cu', 0.2, ('U2', '22'), (118.35, 118.5), (118.725, 118.125), ('C7', '1'))   # REGN -> C7
    r.track('F.Cu', 0.25, ('U2', '21'), (118.85, 119.05), net=r.net('U2', '21'))          # BTST -> C4
    sw = r.net('U2', '19')
    r.track('F.Cu', 0.25, ('U2', '20'), ('U2', '19'))
    r.track('F.Cu', 0.25, ('U2', '19'), (119.85, 119.05))
    r.zone(sw, 'F.Cu', [(119.55, 118.3), (124.0, 118.3), (124.0, 119.4), (120.4, 119.4), (120.4, 120.6), (119.75, 120.6),
                        (119.75, 119.5), (119.55, 119.5)], prio=10, name='SW_CHG')
    # GND pins into the exposed pad (which has its own thermal vias); 17/18 also out to C_SYS's ground pad
    r.track('F.Cu', 0.25, ('U2', '17'), (119.6, 121.455))
    r.track('F.Cu', 0.2, ('U2', '18'), (119.85, 120.955))       # 0.2 wide: clears SW pin 19 above by 0.2
    r.track('F.Cu', 0.25, ('U2', '18'), (r.P('C5', '2')[0], r.P('U2', '18')[1]))   # into C_SYS's ground pad
    r.track('F.Cu', 0.25, ('U2', '9'), (118.345, 122.8))
    # pin 6 is boxed in by STAT (left), PG (right) and the EP corner: its own via straight down
    x6 = r.P('U2', '6')[0]
    r.track('F.Cu', 0.25, ('U2', '6'), (x6, 124.15))
    r.via((x6, 124.15), 'GND', 0.45, 0.2)
    vsys = r.net('U2', '15')
    r.track('F.Cu', 0.25, ('U2', '16'), ('U2', '15'))
    r.zone(vsys, 'F.Cu', [(120.4, 121.78), (121.5, 121.78), (121.5, 121.15), (126.4, 121.15), (126.4, 115.9), (132.4, 115.9),
                          (132.4, 126.3), (124.3, 126.3), (124.3, 122.63), (120.4, 122.63)], prio=10, name='VSYS_CHG')
    bat = r.net('U2', '13')
    r.track('F.Cu', 0.25, ('U2', '14'), ('U2', '13'))
    r.zone(bat, 'F.Cu', [(120.3, 122.83), (121.1, 122.83), (121.1, 123.05), (124.0, 123.05), (124.0, 124.3), (120.3, 124.3)],
           prio=10, name='BAT_CHG')
    r.via_field(bat, 121.5, 123.6, 122.3, 124.1, pitch=0.7)
    # bottom row: ILIM / ICHG / TS out to their resistors, analog ground down the middle from pin 9
    r.track('F.Cu', 0.2, ('U2', '8'), (117.845, 125.3), ('R2', '1'))                      # ILIM
    r.track('F.Cu', 0.2, ('U2', '10'), (118.845, 125.1), (119.235, 125.49), ('R3', '1'))  # ICHG
    agnd_y = r.P('R2', '2')[1]
    r.track('F.Cu', 0.2, ('U2', '9'), (118.345, agnd_y), ('R2', '2'))
    r.track('F.Cu', 0.2, (118.345, agnd_y), ('R3', '2'), ('R5', '2'), net='GND')
    r.keepout('F.Cu', [(117.1, 124.7), (121.45, 124.7), (121.45, 127.0), (117.1, 127.0)], name='AGND_CHG')
    ts = r.net('U2', '11')
    r.track('F.Cu', 0.2, ('U2', '11'), (119.345, 124.85), (121.3, 124.85))
    r.track('F.Cu', 0.2, (r.P('R5', '1')[0], 124.85), ('R5', '1'), ('R4', '2'), net=ts)
    r.via((121.3, 124.85), ts, 0.45, 0.2)
    r.track('B.Cu', 0.2, (121.3, 124.85), (121.3, 126.0), (122.8, 126.0), (122.8, 127.5), (133.6, 127.5), (134.4, 128.3),
            ('J4', '1'))                                                                   # TS -> NTC pad
    # REGN -> RT1 top (R4 pin 1) on B.Cu
    regn = r.net('U2', '22')
    r.via((120.1, 117.75), regn, 0.45, 0.2)
    r.track('F.Cu', 0.2, ('C7', '1'), (120.1, 117.75))
    r41 = r.P('R4', '1')
    r.via((r41[0], 127.45), regn, 0.45, 0.2)
    r.track('B.Cu', 0.2, (120.1, 117.75), (120.35, 118.0), (120.35, 127.0), (120.8, 127.45), (r41[0], 127.45), net=regn)
    r.track('F.Cu', 0.2, (r41[0], 127.45), ('R4', '1'))
    # STAT -> LED (to VSYS via R6) and the CHG pad
    st = r.net('U2', '5')
    r.track('F.Cu', 0.2, ('U2', '5'), (115.9, 122.955), (115.9, 125.6), (112.2, 125.6), ('LED1', '1'))
    r.track('F.Cu', 0.2, (115.9, 125.6), (115.9, 130.9), (111.8, 130.9), ('J11', '1'), net=st)
    r.track('F.Cu', 0.2, ('LED1', '2'), ('R6', '1'))
    # PG -> J12 on B.Cu
    pg = r.net('U2', '7')
    r.track('F.Cu', 0.2, ('U2', '7'), (117.345, 124.6), (116.85, 125.0))
    r.via((116.85, 125.0), pg, 0.45, 0.2)
    r.track('B.Cu', 0.2, (116.85, 125.0), (116.85, 131.3), ('J12', '1'))


def protection(r):
    """J2 BAT+ -> F1 -> BAT; J3 BAT- -> Q1 (reverse block) -> CELLN -> Q2 (DSG) -> MID -> Q3 (CHG) -> GND.
    ~5.6 A worst case (15 W out at 3.0 V): every link in the chain is a pour across a facing-column gap."""
    batp, bat = r.net('F1', '1'), r.net('F1', '2')
    r.zone(batp, 'F.Cu', [(144.5, 119.5), (151.5, 119.5), (151.5, 123.6), (144.5, 123.6)], prio=10, name='BATP')
    r.zone(bat, 'F.Cu', [(139.5, 119.5), (143.3, 119.5), (143.3, 124.9), (139.5, 124.9)], prio=10, name='BAT_FUSE')
    r.via_field(bat, 140.2, 123.8, 141.8, 124.6, pitch=0.8)
    # BAT on B.Cu from the fuse to the charger (20 mm x 3.6 mm, ~3 mOhm)
    r.zone(bat, 'B.Cu', [(120.7, 121.0), (148.2, 121.0), (148.2, 124.6), (120.7, 124.6)], prio=10, name='BAT_BOTTOM')
    mid, celln, batn = r.net('Q2', '1'), r.net('Q1', '4'), r.net('J3', '1')
    r.zone(mid, 'F.Cu', [(140.0, 125.5), (143.4, 125.5), (143.4, 128.5), (140.0, 128.5)], prio=11, name='MID')
    r.zone(celln, 'F.Cu', [(143.6, 124.8), (145.2, 124.8), (145.2, 125.6), (145.85, 125.6), (145.85, 128.6), (147.75, 128.6),
                           (147.75, 130.4), (144.2, 130.4), (144.2, 128.6), (143.6, 128.6)], prio=11, name='CELLN')
    r.zone(batn, 'F.Cu', [(145.95, 125.4), (151.5, 125.4), (151.5, 128.3), (145.95, 128.3)], prio=10, name='BATN')
    # Q3 source -> GND
    for y in (126.9, 127.75, 128.6):
        r.via((138.95, y), 'GND')
    # gates: Q1 from BAT via R9 (R10 to CELLN), Q2 / Q3 from the HY2113
    q1g = r.P('Q1', '3')
    r.track('F.Cu', 0.25, ('R9', '2'), ('R10', '1'), (q1g[0], r.P('R10', '1')[1]), ('Q1', '3'))
    q2g = r.P('Q2', '3')
    r.track('F.Cu', 0.2, ('Q2', '3'), (q2g[0], 129.4), ('U3', '1'))
    q3g = r.net('Q3', '3')
    r.track('F.Cu', 0.2, ('Q3', '3'), (138.2, 125.7))
    r.via((138.2, 125.7), q3g, 0.45, 0.2)
    r.track('B.Cu', 0.2, (138.2, 125.7), (138.2, 131.3), (141.4, 131.3), (142.2, 132.1), (142.2, 132.5), net=q3g)
    r.via((142.2, 132.5), q3g, 0.45, 0.2)
    r.track('F.Cu', 0.2, (142.2, 132.5), (142.75, 131.95), ('U3', '3'))
    r.track('F.Cu', 0.2, ('U3', '2'), ('R8', '1'))                                    # CS
    c81 = r.P('C8', '1')
    r.track('F.Cu', 0.25, ('U3', '5'), (c81[0], r.P('U3', '5')[1]), ('C8', '1'), ('R7', '2'))   # VDD
    r71 = r.P('R7', '1')
    r.track('F.Cu', 0.3, ('R7', '1'), (r71[0], r71[1] + 1.0))
    r.via((r71[0], r71[1] + 1.0), bat)
    r.track('B.Cu', 0.4, (r71[0], r71[1] + 1.0), (147.9, r71[1] + 1.0), (147.9, 124.4), net=bat)


def build(r):
    planes(r)
    usb_pd(r)
    charger(r)
    protection(r)
    stitch_pads(r)          # last, so the stitching vias avoid the routed copper
