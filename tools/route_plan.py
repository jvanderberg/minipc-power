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


# analog grounds, single point to power ground, no plane vias: charger (at U2's pad) and 12 V boost (AGND pin -> PGND bar)
AGND = {('R2', '2'), ('R3', '2'), ('R5', '2'), ('R11', '2'), ('R12', '2'), ('C13', '2'), ('R14', '2'), ('R25', '2')}


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
    # TS -> NTC pad on B.Cu, above the 3.3 V converter (its PGND via sits in U6's centre) and down beside L4
    r.track('B.Cu', 0.2, (121.3, 124.85), (121.3, 125.6), (136.5, 125.6), (136.5, 131.6), ('J4', '1'), net=ts)
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


def boost12(r):
    """TPS61178 (U4), per datasheet s11 / fig. 36. Bars: VOUT (top), SW, PGND (bottom).
    SW: one pour from the bar's left end to L2 and C11 (BST cap). C_OUT1 (C14, C15) bridge the VOUT bar's copper and
    the PGND bar's copper right at the bar ends (rule 1 loop). DISDRV -> RGATE/CGATE -> P-FET gate along the top;
    VOUT2 (+12V) -> COUT2 and to the output pad on B.Cu. FREQ/ILIM/COMP/FB parts on a separate AGND bus that joins
    PGND only at the AGND pin (rule 7)."""
    sw, vout, gate = r.net('U4', '7'), r.net('U4', '8'), r.net('U4', '9')
    r.zone(sw, 'F.Cu', [(106.85, 107.9), (109.2, 107.9), (109.2, 105.75), (110.75, 105.75), (110.75, 106.45), (109.85, 106.45),
                        (109.85, 107.9), (111.05, 107.9), (111.05, 109.45), (111.55, 109.45), (111.55, 109.75),
                        (111.05, 109.75), (111.05, 111.3), (106.85, 111.3)], prio=10, name='SW12')
    r.zone(vout, 'F.Cu', [(114.6, 108.3), (116.85, 108.3), (116.85, 107.15), (119.0, 107.15), (119.0, 108.3), (121.9, 108.3),
                          (121.9, 111.2), (119.3, 111.2), (119.3, 109.75), (114.6, 109.75)], prio=10, name='VOUT12A')
    r.zone('GND', 'F.Cu', [(114.4, 110.0), (119.1, 110.0), (119.1, 111.4), (120.3, 111.4), (120.3, 115.1), (118.65, 115.1),
                           (118.65, 111.55), (114.4, 111.55)], prio=10, name='PGND12')
    r.via((119.7, 111.85), 'GND')
    p12 = r.net('Q4', '1')
    r.zone(p12, 'F.Cu', [(122.2, 109.0), (126.7, 109.0), (126.7, 110.7), (123.6, 110.7), (123.6, 113.8), (126.7, 113.8),
                         (126.7, 115.4), (121.7, 115.4), (121.7, 111.95), (122.2, 111.95)], prio=10, name='P12V')
    for y in (110.6, 111.4):
        r.via((123.3, y), p12)
    r.track('B.Cu', 0.6, (123.3, 110.6), (123.3, 104.9), ('J6', '1'))                    # +12V -> output pad
    # top-row escapes: BST, VIN, EN, VCC, DISDRV (left to right)
    r.track('F.Cu', 0.25, ('C11', '1'), (111.955, r.P('C11', '1')[1]), ('U4', '13'))
    vsys = r.net('U4', '12')
    r.track('F.Cu', 0.25, ('U4', '12'), (112.455, 106.5), (111.6, 106.5), (111.4, 106.3), (111.4, 105.9))
    r.via((111.4, 105.9), vsys, 0.45, 0.2)                                                  # VIN -> In2 VSYS plane
    en = r.net('U4', '11')
    r.track('F.Cu', 0.2, ('U4', '11'), (112.955, 105.9))
    r.via((112.955, 105.9), en, 0.45, 0.2)
    r.track('F.Cu', 0.25, ('U4', '10'), (113.455, 106.9), (113.9, 106.45), ('C12', '1'))
    r.track('F.Cu', 0.25, ('U4', '9'), (113.955, 107.25), (116.0, 107.25), (116.6, r.P('C16', '2')[1]), ('C16', '2'),
            ('R16', '2'), (122.64, r.P('R16', '2')[1]), ('Q4', '4'))
    # bottom row in pin order: FREQ, AGND, ILIM, COMP, FB
    r.track('F.Cu', 0.2, ('U4', '1'), (111.955, 112.15), (111.6, 112.5), ('R11', '1'))
    r.track('F.Cu', 0.2, ('U4', '3'), (112.955, 112.6), ('R12', '1'))
    r.track('F.Cu', 0.2, ('U4', '4'), (113.455, 112.1), ('R15', '1'))
    r.track('F.Cu', 0.2, ('R15', '2'), ('C13', '1'))
    r.track('F.Cu', 0.2, ('U4', '5'), (113.955, 111.85), (116.5, 111.85), (116.8, 112.15), ('R14', '1'), ('R13', '2'))
    bus = 114.5
    r.track('F.Cu', 0.2, ('U4', '2'), (112.455, 110.2))                                    # single point: AGND -> PGND bar
    r.track('F.Cu', 0.2, ('U4', '2'), (112.455, bus))
    r.track('F.Cu', 0.2, (r.P('R11', '2')[0], bus), (r.P('R14', '2')[0], bus), net='GND')
    for ref in ('R11', 'R12', 'C13', 'R14'):
        r.track('F.Cu', 0.2, (ref, '2'), (r.P(ref, '2')[0], bus))
    r.keepout('F.Cu', [(110.7, 111.65), (118.45, 111.65), (118.45, 115.3), (110.7, 115.3)], name='AGND_12V')
    # FB sense from +12V (after the P-FET, like R_UP in fig. 36) on B.Cu, away from SW
    r13 = r.P('R13', '1')
    r.track('F.Cu', 0.2, ('R13', '1'), (r13[0], 114.75))
    r.via((r13[0], 114.75), p12, 0.45, 0.2)
    r.track('B.Cu', 0.2, (r13[0], 114.75), (123.3, 114.75), (123.3, 111.4), net=p12)


def boost5(r):
    """TPS61088-Q1 (U5), per datasheet s11 / fig. 21: SW pour from L3 to the left-column SW pins, FSW and BOOT parts
    on it; VIN cap at VIN pin 9; C_IN and C_OUT grounds on a PGND pour tied to the thermal pad's bottom tab; ILIM / COMP
    / FB network top-right in pin order, its grounds via straight into the plane (fig. 21 vias AGND to the plane).
    Load switch Q5 (P-FET, gate pulled down by Q6 from EN) between VOUT5A and the +5V pad."""
    sw, vout, en, vsys = r.net('U5', '4'), r.net('U5', '14'), r.net('U5', '2'), r.net('U5', '9')
    r.zone(sw, 'F.Cu', [(133.1, 107.9), (135.7, 107.9), (135.7, 106.95), (137.55, 106.95), (137.55, 107.95), (136.45, 107.95),
                        (136.45, 109.6), (138.7, 109.6), (138.7, 111.55), (137.4, 111.55), (137.4, 112.15), (136.7, 112.15),
                        (136.7, 111.55), (133.1, 111.55)], prio=10, name='SW5')
    r.zone(vsys, 'F.Cu', [(126.95, 107.8), (130.5, 107.8), (130.5, 112.6), (135.5, 112.6), (135.5, 115.8), (126.95, 115.8)],
           prio=10, name='VSYS_5V')
    r.via_field(vsys, 127.6, 112.0, 130.0, 112.8, pitch=0.8)
    r.zone(vout, 'F.Cu', [(141.6, 110.1), (148.0, 110.1), (148.0, 108.95), (150.7, 108.95), (150.7, 110.1), (151.4, 110.1),
                          (151.4, 112.7), (141.6, 112.7)], prio=10, name='VOUT5A')
    r.zone('GND', 'F.Cu', [(140.3, 112.3), (140.85, 112.3), (140.85, 113.3), (151.4, 113.3), (151.4, 115.75), (135.9, 115.75),
                           (135.9, 113.75), (137.6, 113.75), (137.6, 114.4), (140.3, 114.4)], prio=10, name='PGND5')
    p5 = r.net('Q5', '1')
    r.zone(p5, 'F.Cu', [(147.0, 101.4), (149.9, 101.4), (149.9, 104.3), (151.4, 104.3), (151.4, 106.5), (148.8, 106.5),
                        (148.8, 104.3), (147.0, 104.3)], prio=10, name='P5V')
    # left column: EN, FSW, (SW x4), BOOT, VIN
    r.track('F.Cu', 0.2, ('U5', '2'), (137.9, 108.85), (137.9, 107.75))
    r.via((137.9, 107.75), en, 0.45, 0.2)
    r.track('F.Cu', 0.2, ('R17', '1'), (137.1, 109.0), (137.45, 109.35), ('U5', '3'))
    r.track('F.Cu', 0.2, ('U5', '8'), (137.95, 111.85), (137.75, 112.05), (137.75, r.P('C24', '1')[1]), ('C24', '1'))
    c231 = r.P('C23', '1')
    r.track('F.Cu', 0.3, ('U5', '9'), (c231[0], 112.7), ('C23', '1'))
    r.track('F.Cu', 0.3, (c231[0], 113.5), (r.P('C22', '1')[0], 113.5), ('C22', '1'), net=vsys)
    # top: VCC caps, AGND pin
    r.track('F.Cu', 0.25, ('U5', '1'), (139.55, 107.6), (138.9, 107.0), ('C25', '1'), ('C26', '1'))
    r.track('F.Cu', 0.25, ('U5', '20'), (141.05, 107.3), ('C25', '2'))
    r.track('F.Cu', 0.2, ('U5', '10'), (139.55, 113.2), ('C27', '1'))                       # SS
    # right column: ILIM, COMP, FB fan out to the column in the same order
    r.track('F.Cu', 0.2, ('U5', '19'), (142.45, 108.85), (142.45, r.P('R18', '1')[1]), ('R18', '1'))
    r.track('F.Cu', 0.2, ('U5', '18'), (142.85, 109.35), (142.85, r.P('C29', '1')[1]), ('C29', '1'))
    r.track('F.Cu', 0.2, (142.85, r.P('R21', '1')[1]), ('R21', '1'), net=r.net('U5', '18'))
    r.track('F.Cu', 0.2, ('R21', '2'), ('C28', '1'))
    r19 = r.P('R19', '2')
    r.track('F.Cu', 0.2, ('U5', '17'), (r19[0], r.P('U5', '17')[1]), ('R19', '2'), (r19[0], 109.2), ('R20', '1'))
    # load switch: gate network, Q6 pull-down from EN
    q5g = r.P('Q5', '4')
    r.track('F.Cu', 0.2, ('Q5', '4'), (147.6, q5g[1]), (147.3, r.P('R22', '2')[1]), ('R22', '2'), ('C32', '2'))
    r.track('F.Cu', 0.25, (148.3, 106.95), (147.6, 106.95), (147.2, 106.55), ('R22', '1'), ('C32', '1'), net=vout)
    gate5 = r.net('Q5', '4')
    r.track('F.Cu', 0.2, ('C32', '2'), (145.2, 104.55))
    r.via((145.2, 104.55), gate5, 0.45, 0.2)
    r231 = r.P('R23', '1')
    r.via((r231[0] + 0.75, r231[1]), gate5, 0.45, 0.2)
    r.track('B.Cu', 0.2, (145.2, 104.55), (148.25, 107.6), (r231[0] + 0.75, 107.6 + 1.0), (r231[0] + 0.75, r231[1]), net=gate5)
    r.track('F.Cu', 0.2, ('R23', '1'), (r231[0] + 0.75, r231[1]))
    r.track('F.Cu', 0.2, ('Q6', '3'), ('R23', '2'))
    q61 = r.P('Q6', '1')
    r.track('F.Cu', 0.2, ('Q6', '1'), (q61[0], 115.75))
    r.via((q61[0], 115.75), en, 0.45, 0.2)


def buckboost33(r):
    """TPS63802 (U6), per datasheet s12 / fig. 12-1 and WEBENCH d36: C_IN on VIN, C_OUT on VOUT, short L1 / L2 pours to
    the upright inductor; PGND through a via in the IC centre, where the control ground (MODE, AGND pins, R25) joins it
    (rule 2); FB / PG / EN on the left, away from L1 / L2 (rule 4)."""
    l1, l2, pg, en = r.net('U6', '9'), r.net('U6', '7'), r.net('U6', '5'), r.net('U6', '1')
    p33 = r.net('U6', '6')
    r.track('F.Cu', 0.3, ('U6', '9'), (131.6, r.P('U6', '9')[1]))
    r.zone(l1, 'F.Cu', [(131.45, 126.55), (135.2, 126.55), (135.2, 127.25), (131.45, 127.25)], prio=10, name='L1_33')
    r.track('F.Cu', 0.3, ('U6', '7'), (131.6, r.P('U6', '7')[1]))
    r.zone(l2, 'F.Cu', [(131.45, 127.95), (135.2, 127.95), (135.2, 129.0), (131.45, 129.0)], prio=10, name='L2_33')
    r.via((129.72, 127.35), 'GND', 0.45, 0.2)                          # PGND pin 8 + GND pins 2/3 -> In1, at the IC
    r.track('F.Cu', 0.3, ('C33', '1'), (r.P('U6', '10')[0], 125.2), (r.P('U6', '10')[0], 126.5))   # VIN (stops short of L1)
    r.track('F.Cu', 0.3, ('U6', '6'), (130.2, 129.2), (129.3, 129.2), ('C34', '1'))         # VOUT -> C_OUT
    r.track('F.Cu', 0.5, ('C34', '1'), (128.6, 131.4), ('J8', '1'))                         # -> +3V3 pad
    # control ground node: MODE (pin 2, tied low), AGND (pin 3), R25 bottom
    r.track('F.Cu', 0.2, ('U6', '2'), (128.6, r.P('U6', '2')[1]), (128.6, r.P('U6', '3')[1]), ('U6', '3'))
    r.track('F.Cu', 0.2, ('R25', '2'), (128.6, r.P('R25', '2')[1]))
    r.track('F.Cu', 0.2, ('U6', '4'), (128.3, r.P('U6', '4')[1]), ('R25', '1'), (127.3, r.P('R24', '2')[1]), ('R24', '2'))
    r.track('F.Cu', 0.25, (125.89, 132.3), ('R26', '2'), ('R24', '1'), net=p33)             # FB top / PG pull-up from +3V3
    r.keepout('F.Cu', [(125.2, 126.95), (128.75, 126.95), (128.75, 130.3), (125.2, 130.3)], name='AGND_3V3')
    # PG -> pull-up and the PG3 pad (B.Cu); EN
    r.track('F.Cu', 0.2, ('U6', '5'), (128.88, r.P('U6', '5')[1]), (128.45, 129.03), (128.45, 129.15))
    r.via((128.45, 129.15), pg, 0.45, 0.2)
    r.track('F.Cu', 0.2, (128.45, 129.15), (127.5, r.P('R26', '1')[1]), ('R26', '1'))
    r.track('B.Cu', 0.2, (128.45, 129.15), (124.9, 129.15), (124.9, 131.6), ('J14', '1'), net=pg)   # around J8 (THT)
    r.track('F.Cu', 0.2, ('U6', '1'), (128.0, 126.45))
    r.via((128.0, 126.45), en, 0.45, 0.2)


def build(r):
    planes(r)
    usb_pd(r)
    charger(r)
    protection(r)
    boost12(r)
    boost5(r)
    buckboost33(r)
    stitch_pads(r)          # last, so the stitching vias avoid the routed copper
