#!/usr/bin/env python3
"""Generate hardware/minipc-power.kicad_sch: wired blocks (real wires inside each block, power symbols for rails,
labels only where a net leaves its block). Values and their derivations: docs/power-design.md.

Run from the repo root:  python3 tools/gen_schematic.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from schgen import Sch, SymLib, G
import symbols

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HW = os.path.join(ROOT, 'hardware')
KS = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols'

s = Sch('minipc-power', paper='A2', title='minipc-power: USB-C PD / 1S2P power board', rev='1', date='2026-10-24')
s.lib('Device', os.path.join(KS, 'Device.kicad_sym'))
s.lib('power', os.path.join(KS, 'power.kicad_sym'))
s.lib('Connector', os.path.join(KS, 'Connector.kicad_sym'))
s.lib('Mechanical', os.path.join(KS, 'Mechanical.kicad_sym'))
s.lib('minipc', text=symbols.library_text())

# ------------------------------------------------------------------ footprints / parts
R0402, C0402, C0603, C0805, C1206, C1210 = ('Resistor_SMD:R_0402_1005Metric', 'Capacitor_SMD:C_0402_1005Metric',
    'Capacitor_SMD:C_0603_1608Metric', 'Capacitor_SMD:C_0805_2012Metric', 'Capacitor_SMD:C_1206_3216Metric',
    'Capacitor_SMD:C_1210_3225Metric')
PAD_PWR = 'TestPoint:TestPoint_THTPad_2.5x2.5mm_Drill1.2mm'
PAD_SIG = 'TestPoint:TestPoint_THTPad_2.0x2.0mm_Drill1.0mm'

RES = {'6.8k': 'C25917', '249': 'C25096', '470': 'C25117', '5.23k': 'C25907', '30.9k': 'C270615', '1k': 'C11702',
       '10k': 'C25744', '1M': 'C26083', '330': 'C25104', '2k': 'C4109', '169k': 'C25758', '162k': 'C54068',
       '732k': 'C27016', '80.6k': 'C25921', '44.2k': 'C25895', '178k': 'C26995', '267k': 'C270622',
       '69.8k': 'C26985', '220k': 'C25767', '28.7k': 'C26972', '100k': 'C25741', '511k': 'C64042', '91k': 'C4147',
       '470k': 'C25790'}
CAP = {  # value -> (footprint, LCSC, description)
    '100n': (C0402, 'C1525', '100nF 16V X7R'), '1u': (C0603, 'C15849', '1uF 50V X5R'),
    '10u/25V': (C0805, 'C15850', '10uF 25V X5R'), '10u/10V': (C0603, 'C19702', '10uF 10V X5R'),
    '4.7u/16V': (C0603, 'C19666', '4.7uF 16V X5R'), '4.7u/25V': (C0805, 'C1779', '4.7uF 25V X5R'),
    '22u/25V': (C0805, 'C45783', '22uF 25V X5R'), '22u/6.3V': (C0603, 'C59461', '22uF 6.3V X5R'),
    '22u/25V/1210': (C1210, 'C52306', '22uF 25V X5R'), '47u/16V': (C1210, 'C77101', '47uF 16V X5R'),
    '47n': (C0402, 'C307434', '47nF 16V X7R'), '10n': (C0402, 'C15195', '10nF 50V X7R'),
    '1.8n': (C0402, 'C107024', '1.8nF 50V X7R'), '22n': (C0402, 'C337699', '22nF 50V X7R'),
    '680p': (C0402, 'C307451', '680pF 50V C0G'), '33p': (C0402, 'C70465', '33pF 50V C0G'),
}


def R(ref, val, x, y, rot=0):
    return s.add('Device:R', ref, val, x, y, rot, footprint=R0402, lcsc=RES[val])


def C(ref, val, x, y, rot=0):
    fp, lc, desc = CAP[val]
    return s.add('Device:C', ref, val.split('/')[0].replace('u', 'uF').replace('n', 'nF').replace('p', 'pF') +
                 ('' if '/' not in val else ' ' + val.split('/')[1]), x, y, rot, footprint=fp, lcsc=lc,
                 fields={'Description': desc})


def gnd(pt):
    s.power('GND', pt[0], pt[1])


def rail(net, pt, rot=0):
    s.power(net, pt[0], pt[1], rot)


def down_part(maker, ref, val, top):
    """Vertical two-pin part (R or C, rot 0) whose pin 1 sits at `top`; returns (part, bottom point)."""
    p = maker(ref, val, top[0], top[1] + 3.81)
    return p, p.p('2')


def shunt(maker, ref, val, top):
    """Vertical part from `top` to GND."""
    p, b = down_part(maker, ref, val, top)
    gnd(b)
    return p


def pad(ref, label, pt, fp=PAD_SIG):
    return s.add('Connector:TestPoint', ref, label, pt[0], pt[1], 0, footprint=fp,
                 fields={'_ref_at': (pt[0] + 1.27, pt[1] - 3.81), '_val_at': (pt[0] + 1.27, pt[1] - 6.35)})


def header(t, x, y):
    s.text(t, x, y, 2.0, bold=True)


# ================================================================== A. USB-C input + PD sink
header('USB-C input, PD sink (requests 9 V)', 20.32, 35.56)
J1 = s.add('Connector:USB_C_Receptacle_USB2.0_16P', 'J1', 'USB-C (HRO TYPE-C-31-M-12)', 35.56, 76.2,
           footprint='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', lcsc='C165948')
U1 = s.add('minipc:CH224Q', 'U1', 'CH224Q', 91.44, 68.58, footprint='JLCImport:CH224Q_C46061833',
           lcsc='C46061833')
vb = J1.p('A4')                                   # VBUS on the connector
x_tie = U1.p('VBUS')[0] - 2.54
s.wire(vb, U1.p('VHV'))                           # connector VBUS -> U1 VHV (same row)
s.vh((x_tie, vb[1]), U1.p('VBUS'))
# VBUS riser to a bus above the block; TVS and VHV cap hang off the bus, clear of the CC/D lines
x_vbus_up = vb[0] + 5.08
y_bus = 45.72
s.wire((x_vbus_up, vb[1]), (x_vbus_up, y_bus))
D1 = s.add('Device:D_Zener', 'D1', 'SMF12A', x_vbus_up + 7.62, y_bus + 3.81, 270, footprint='Diode_SMD:D_SOD-123F',
           lcsc='C123800', fields={'Description': 'TVS 12 V standoff'})
gnd(D1.p('2'))
C1 = shunt(C, 'C1', '1u', (x_vbus_up + 15.24, y_bus))
# CC / D+ / D-
s.wire(J1.p('A5'), U1.p('CC1'))
s.wire(J1.p('B5'), U1.p('CC2'))
s.wire(J1.p('A7'), U1.p('DM'))
s.wire(J1.p('B7'), (J1.p('B7')[0] + 2.54, J1.p('B7')[1]), (J1.p('A7')[0] + 2.54, J1.p('A7')[1]))
s.wire(J1.p('A6'), U1.p('DP'))
s.wire(J1.p('B6'), (J1.p('B6')[0] + 2.54, J1.p('B6')[1]), (J1.p('A6')[0] + 2.54, J1.p('A6')[1]))
s.nc(J1.p('A8')); s.nc(J1.p('B8'))
gnd(J1.p('A1'))
s.wire(J1.p('SH'), J1.p('A1'))
# CFG1 -> 6.8k (9 V); CFG2/3 float; PG unused
cfg = U1.p('CFG1')
s.wire(cfg, (cfg[0] + 5.08, cfg[1]))
shunt(R, 'R1', '6.8k', (cfg[0] + 5.08, cfg[1]))
for n in ('CFG2', 'CFG3', '~{PG}'):
    s.nc(U1.p(n))
gnd(U1.p('GND'))
s.text('R1 6.8k = 9 V request (CH224 table 5-1)', 101.6, 96.52)

# ================================================================== B. Charger
header('Charger BQ25606 (standalone NVDC, 1.44 A charge, 1.92 A input limit)', 129.54, 35.56)
U2 = s.add('minipc:BQ25606', 'U2', 'BQ25606', 170.18, 83.82,
           footprint='Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias',
           lcsc='C374063')
pv = U2.p('VBUS')
x_drop = pv[0] - 17.78
s.wire((x_vbus_up, y_bus), (x_drop, y_bus), (x_drop, pv[1]), pv)
rail('VBUS', (x_drop, y_bus))
s.wire((pv[0] - 2.54, pv[1]), (pv[0] - 2.54, U2.p('VAC')[1]), U2.p('VAC'))
shunt(C, 'C2', '1u', (x_drop + 5.08, pv[1]))
pm = U2.p('PMID')
s.wire(pm, (pm[0] - 7.62, pm[1]))
shunt(C, 'C3', '10u/25V', (pm[0] - 7.62, pm[1]))
for n in ('D+', 'D-', 'VSET', 'NC'):
    s.nc(U2.p(n))
il, ic_ = U2.p('ILIM'), U2.p('ICHG')
s.wire(il, (il[0] - 12.7, il[1]))
shunt(R, 'R2', '249', (il[0] - 12.7, il[1]))
s.wire(ic_, (ic_[0] - 7.62, ic_[1]))
shunt(R, 'R3', '470', (ic_[0] - 7.62, ic_[1]))
ce, otg = U2.p('~{CE}'), U2.p('OTG')
s.wire(ce, (ce[0] - 2.54, ce[1]), (otg[0] - 2.54, otg[1] + 7.62))
s.wire(otg, (otg[0] - 2.54, otg[1]))
gnd((otg[0] - 2.54, otg[1] + 7.62))
gnd(U2.p('GND'))
# BTST / SW / inductor / SYS / BAT
bt, sw = U2.p('BTST'), U2.p('SW')
x_l = sw[0] + 12.7
s.wire(bt, (bt[0] + 5.08, bt[1]), (bt[0] + 5.08, bt[1] - 5.08))
C4 = C('C4', '47n', bt[0] + 8.89, bt[1] - 5.08, 90)
s.wire(C4.p('2'), (x_l, C4.p('2')[1]), (x_l, sw[1]))
s.wire(sw, (x_l, sw[1]))
L1 = s.add('Device:L', 'L1', '2.2uH FXL0630-2R2-M', x_l + 3.81, sw[1], 90, footprint='JLCImport:FXL0630-2R2-M',
           lcsc='C167218', fields={'_ref_at': (x_l + 1.27, sw[1] - 3.81), '_val_at': (x_l - 2.54, sw[1] + 3.81)})
sy, ba = U2.p('SYS'), U2.p('BAT')
x_sys = L1.p('2')[0] + 5.08
s.wire(L1.p('2'), (x_sys, sw[1]), (x_sys, sy[1]), sy)
y_vs = sw[1] - 15.24
s.wire((x_sys, sw[1]), (x_sys, y_vs), (x_sys + 10.16, y_vs))
shunt(C, 'C5', '10u/25V', (x_sys + 5.08, y_vs))
rail('VSYS', (x_sys + 10.16, y_vs))
x_bat = x_sys + 17.78
s.wire(ba, (x_bat, ba[1]))
shunt(C, 'C6', '10u/10V', (x_bat - 7.62, ba[1]))
s.wire((x_bat, ba[1]), (x_bat, ba[1] - 7.62))
rail('BAT', (x_bat, ba[1] - 7.62))
# REGN / TS divider / NTC pad
rg, ts = U2.p('REGN'), U2.p('TS')
x_rt = rg[0] + 10.16
s.wire(rg, (x_rt, rg[1]))
shunt(C, 'C7', '4.7u/16V', (rg[0] + 5.08, rg[1]))
R4, r4b = down_part(R, 'R4', '5.23k', (x_rt, rg[1]))
s.wire(r4b, (x_rt, ts[1]))
s.wire(ts, (x_rt + 12.7, ts[1]))
shunt(R, 'R5', '30.9k', (x_rt + 5.08, ts[1]))
J4 = pad('J4', 'NTC', (x_rt + 12.7, ts[1]))
s.text('NTC 10k B3435 (103AT) from J4 to J5 (GND), taped to the pack', x_rt - 7.62, ts[1] + 15.24)
# STAT LED + pad, PG pad
st, pg = U2.p('STAT'), U2.p('~{PG}')
x_led = st[0] + 7.62
s.wire(st, (x_led, st[1]))
LED1 = s.add('Device:LED', 'LED1', 'red (charging)', x_led + 3.81, st[1], 0, footprint='LED_SMD:LED_0603_1608Metric',
             lcsc='C2286', fields={'_ref_at': (x_led + 1.27, st[1] - 2.54), '_val_at': (x_led + 1.27, st[1] + 3.81)})
R6 = R('R6', '1k', LED1.p('2')[0] + 3.81, st[1], 90)
s.wire(R6.p('2'), (R6.p('2')[0] + 2.54, st[1]), (R6.p('2')[0] + 2.54, st[1] - 5.08))
rail('VSYS', (R6.p('2')[0] + 2.54, st[1] - 5.08))
s.wire((x_led - 2.54, st[1]), (x_led - 2.54, st[1] + 7.62))
pad('J11', 'CHG', (x_led - 2.54, st[1] + 7.62))
s.wire(pg, (pg[0] + 15.24, pg[1]))
s.label('PG_CHG', pg[0] + 15.24, pg[1])

# ================================================================== C. Cell protection + reverse block
header('1S2P pack: reverse block, HY2113 protector, fuse', 259.08, 35.56)
yc = 132.08                                  # low-side chain row
J2 = pad('J2', 'BAT+', (264.16, 63.5), PAD_PWR)
F1 = s.add('Device:Fuse', 'F1', '10A 0451010', 271.78, 63.5, 90, footprint='Fuse:Fuse_Littelfuse-NANO2-451_453',
           lcsc='C44479', fields={'_ref_at': (269.24, 60.96), '_val_at': (266.7, 68.58)})
s.wire(J2.p('1'), F1.p('1'))
s.wire(F1.p('2'), (284.48, 63.5), (284.48, 58.42))
rail('BAT', (284.48, 58.42))
# HY2113 sits above the chain, VSS straight down to CELL-
U3 = s.add('minipc:HY2113', 'U3', 'HY2113-MB1A', 297.18, 104.14, footprint='Package_TO_SOT_SMD:SOT-23-6',
           lcsc='C168772')
vss = U3.p('VSS')
x_celln = vss[0]
J3 = pad('J3', 'BAT-', (256.54, yc), PAD_PWR)
Q1 = s.add('minipc:CSD13202Q2', 'Q1', 'CSD13202Q2', 0, 0, 90, footprint='Package_SON:Texas_DQK', lcsc='C187839')
# place Q1 so that its D lands on the chain row, ~10 mm right of J3
dq = Q1.p('1'); Q1.x += 264.16 - dq[0]; Q1.y += yc - dq[1]
s.wire(J3.p('1'), Q1.p('1'))
s.wire(Q1.p('4'), (x_celln, yc))
s.wire(vss, (x_celln, yc))
Q2 = s.add('minipc:CSD13202Q2', 'Q2', 'CSD13202Q2', 0, 0, 270, footprint='Package_SON:Texas_DQK', lcsc='C187839')
sq = Q2.p('4'); Q2.x += x_celln + 5.08 - sq[0]; Q2.y += yc - sq[1]
s.wire((x_celln, yc), Q2.p('4'))
Q3 = s.add('minipc:CSD13202Q2', 'Q3', 'CSD13202Q2', 0, 0, 90, footprint='Package_SON:Texas_DQK', lcsc='C187839',
           mirror='x')
dq3 = Q3.p('1'); Q3.x += Q2.p('1')[0] + 7.62 - dq3[0]; Q3.y += yc - dq3[1]
s.wire(Q2.p('1'), Q3.p('1'))
s.wire(Q3.p('4'), (Q3.p('4')[0] + 5.08, yc))
gnd((Q3.p('4')[0] + 5.08, yc))
s.text('pack- = board GND', Q3.p('4')[0] + 2.54, yc + 7.62)
# gates
oc, od = U3.p('OC'), U3.p('OD')
s.wire(oc, (Q3.p('3')[0], oc[1]), Q3.p('3'))
s.wire(od, (Q2.p('3')[0], od[1]), Q2.p('3'))
# VDD filter, CS resistor
vdd, cs = U3.p('VDD'), U3.p('CS')
x_vdd = vdd[0] - 7.62
s.wire(vdd, (x_vdd, vdd[1]))
R7 = R('R7', '330', x_vdd, vdd[1] - 3.81)
s.wire(R7.p('1'), (x_vdd, R7.p('1')[1] - 2.54))
rail('BAT', (x_vdd, R7.p('1')[1] - 2.54))
C8 = C('C8', '100n', x_vdd - 5.08, vdd[1] + 3.81)
s.wire((x_vdd, vdd[1]), (x_vdd - 5.08, vdd[1]), C8.p('1'))
s.wire(C8.p('2'), (x_vdd - 5.08, yc - 7.62), (x_celln, yc - 7.62))
s.nc(U3.p('NC'))
s.wire(cs, (cs[0] - 2.54, cs[1]))
R8 = R('R8', '2k', cs[0] - 2.54 - 3.81, cs[1], 270)
s.wire(R8.p('2'), (R8.p('2')[0] - 2.54, cs[1]), (R8.p('2')[0] - 2.54, cs[1] + 2.54))
gnd((R8.p('2')[0] - 2.54, cs[1] + 2.54))
# Q1 gate: 10k from BAT, 1M gate-source
qg = Q1.p('3')
s.wire(qg, (qg[0], qg[1] + 5.08))
R10 = R('R10', '1M', qg[0] + 3.81, qg[1] + 5.08, 90)
s.wire(R10.p('2'), (x_celln, qg[1] + 5.08), (x_celln, yc))
s.wire((qg[0], qg[1] + 5.08), (qg[0], qg[1] + 10.16))
R9 = R('R9', '10k', qg[0] - 3.81, qg[1] + 10.16, 90)
s.wire(R9.p('1'), (R9.p('1')[0] - 2.54, qg[1] + 10.16), (R9.p('1')[0] - 2.54, qg[1] + 5.08))
rail('BAT', (R9.p('1')[0] - 2.54, qg[1] + 5.08))
s.text('Reversed pack: Q1 off, body diode blocks, U3 never sees reverse voltage', 256.54, yc + 25.4)

# ================================================================== D. Pads, enable, sense, mechanics
header('Solder pads, enable switch, battery sense', 381.0, 35.56)
xp = 391.16
pad('J9', 'EN (to switch)', (xp, 58.42))
pad('J10', 'VSYS (to switch)', (xp + 25.4, 58.42))
rail('VSYS', (xp + 25.4, 53.34))
s.wire(J9 := (xp, 58.42), (xp, 58.42))
R27 = R('R27', '1k', xp + 3.81 + 2.54, 63.5, 90)
s.wire((xp, 58.42), (xp, 63.5), R27.p('1'))
s.wire((xp + 25.4, 53.34), (xp + 25.4, 58.42))
x_en = R27.p('2')[0] + 5.08
s.wire(R27.p('2'), (x_en + 10.16, 63.5))
shunt(R, 'R28', '100k', (x_en, 63.5))
shunt(C, 'C35', '100n', (x_en + 5.08, 63.5))
s.label('EN', x_en + 10.16, 63.5)
s.text('Switch closed = on. EN high: U4, U5, U6 run and Q6 closes the 5 V switch.', xp - 2.54, 78.74)
# battery sense
R29 = R('R29', '470k', xp + 2.54, 96.52)
rail('BAT', (xp + 2.54, R29.p('1')[1]))
s.wire(R29.p('2'), (xp + 2.54, 104.14), (xp + 17.78, 104.14))
shunt(R, 'R30', '1M', (xp + 7.62, 104.14))
shunt(C, 'C36', '100n', (xp + 12.7, 104.14))
pad('J13', 'VBAT_SENSE', (xp + 17.78, 104.14))
s.text('2.96 V at 4.35 V; 3 uA', xp + 20.32, 99.06)
# status / ground / NTC ground pads
pad('J12', 'PG_CHG', (xp, 129.54)); s.label('PG_CHG', xp, 129.54)
pad('J14', '3V3_PG', (xp + 15.24, 129.54)); s.label('3V3_PG', xp + 15.24, 129.54)
for i, ref in enumerate(('J5', 'J15', 'J16', 'J17')):
    x = xp + 35.56 + i * 10.16
    pad(ref, 'GND' if ref != 'J5' else 'NTC-', (x, 129.54), PAD_PWR if ref != 'J5' else PAD_SIG)
    gnd((x, 129.54))
for i, ref in enumerate(('H1', 'H2')):
    s.add('Mechanical:MountingHole', ref, 'M2', xp + i * 15.24, 152.4, footprint='MountingHole:MountingHole_2.2mm_M2')

# ================================================================== E. 12 V boost (TPS61178)
header('12 V / 0.5 A boost TPS61178 (WEBENCH design 33)', 20.32, 190.5)
U4 = s.add('minipc:TPS61178', 'U4', 'TPS61178', 88.9, 243.84, footprint='JLCImport:TPS61178RNWR', lcsc='C127918')
vin, sw4 = U4.p('VIN'), U4.p('SW')
y_top = 210.82
x_in = vin[0] - 30.48
rail('VSYS', (x_in, y_top))
x_sw = sw4[0] + 12.7
L2 = s.add('Device:L', 'L2', '3.3uH FXL0630-3R3-M', x_sw - 8.89, y_top, 90, footprint='JLCImport:FXL0630-3R3-M',
           lcsc='C167219', fields={'_ref_at': (x_sw - 11.43, y_top - 3.81), '_val_at': (x_sw - 16.51, y_top - 6.35)})
s.wire((x_in, y_top), L2.p('1'))
s.wire(L2.p('2'), (x_sw, y_top), (x_sw, sw4[1]), sw4)
s.wire((vin[0] - 5.08, y_top), (vin[0] - 5.08, vin[1]), vin)
shunt(C, 'C9', '22u/25V', (x_in + 5.08, y_top))
shunt(C, 'C10', '22u/25V', (x_in + 10.16, y_top))
# BST cap: BST (top, right) -> up -> right -> cap down onto the SW vertical
bst, vcc = U4.p('BST'), U4.p('VCC')
y_b = y_top + 5.08
s.wire(bst, (bst[0], y_b), (x_sw - 10.16, y_b))
C11 = C('C11', '100n', x_sw - 10.16 + 3.81, y_b, 90)
s.wire(C11.p('2'), (x_sw, y_b))
# VCC cap: VCC (top, left) -> up -> left, cap hangs clear of the VIN drop
y_v = y_top + 10.16
s.wire(vcc, (vcc[0], y_v), (vcc[0] - 7.62, y_v))
shunt(C, 'C12', '4.7u/16V', (vcc[0] - 7.62, y_v))
# EN, FREQ, ILIMIT, COMP on the left
s.wire(U4.p('EN'), (U4.p('EN')[0] - 15.24, U4.p('EN')[1]))
s.label('EN', U4.p('EN')[0] - 15.24, U4.p('EN')[1], 180)
fr, ilm, comp = U4.p('FREQ/SYNC'), U4.p('ILIMIT'), U4.p('COMP')
s.wire(fr, (fr[0] - 15.24, fr[1]))
shunt(R, 'R11', '169k', (fr[0] - 15.24, fr[1]))
s.wire(ilm, (ilm[0] - 10.16, ilm[1]))
shunt(R, 'R12', '162k', (ilm[0] - 10.16, ilm[1]))
s.wire(comp, (comp[0] - 5.08, comp[1]))
R15, r15b = down_part(R, 'R15', '44.2k', (comp[0] - 5.08, comp[1]))
shunt(C, 'C13', '1.8n', r15b)
gnd(U4.p('PGND')); gnd(U4.p('AGND'))
# VOUT (pre-switch) caps, disconnect P-FET with Rgate/Cgate, output caps, FB divider at the FB pin
vo, dis, fb = U4.p('VOUT'), U4.p('DISDRV'), U4.p('FB')
x_d = dis[0] + 5.08
x_q = vo[0] + 38.1
s.wire(vo, (x_q, vo[1]))
shunt(C, 'C14', '4.7u/25V', (x_d + 5.08, vo[1]))
shunt(C, 'C15', '4.7u/25V', (x_d + 10.16, vo[1]))
Q4 = s.add('minipc:CSD25404Q3', 'Q4', 'CSD25404Q3', 0, 0, 270, footprint='Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET',
           lcsc='C2865523', mirror='x')
q4s = Q4.p('5'); Q4.x += x_q - q4s[0]; Q4.y += vo[1] - q4s[1]
y_g = vo[1] + 12.7
R16, r16b = down_part(R, 'R16', '178k', (x_d + 17.78, vo[1]))
C16, c16b = down_part(C, 'C16', '22n', (x_d + 22.86, vo[1]))
s.wire(r16b, (r16b[0], y_g)); s.wire(c16b, (c16b[0], y_g))
s.wire(dis, (x_d, dis[1]), (x_d, y_g), (Q4.p('4')[0], y_g), Q4.p('4'))
q4d = Q4.p('1')
x_out = q4d[0] + 25.4
s.wire(q4d, (x_out, q4d[1]))
for i, ref in enumerate(('C17', 'C18', 'C19')):
    shunt(C, ref, '22u/25V/1210', (q4d[0] + 5.08 + i * 5.08, q4d[1]))
rail('+12V', (x_out, q4d[1]))
pad('J6', '+12V OUT', (x_out, q4d[1]), PAD_PWR)
# FB divider right at the FB pin; top from +12V (after the switch, as in datasheet fig. 22)
x_fb = fb[0] + 2.54
s.wire(fb, (x_fb, fb[1]))
R13 = R('R13', '732k', x_fb, fb[1] - 3.81)
rail('+12V', R13.p('1'))
shunt(R, 'R14', '80.6k', (x_fb, fb[1]))
s.text('FB senses after Q4 (VOUT2)', x_fb + 2.54, fb[1] + 12.7)

# ================================================================== F. 5 V boost (TPS61088-Q1) + load switch
header('5 V / 2.5 A boost TPS61088-Q1 (WEBENCH design 37) + load switch', 220.98, 190.5)
U5 = s.add('minipc:TPS61088-Q1', 'U5', 'TPS61088-Q1', 289.56, 245.11,
           footprint='Package_DFN_QFN:Texas_VQFN-RHL-20_ThermalVias', lcsc='C1850341')
vin5, sw5, fsw, boot = U5.p('VIN'), U5.p('SW'), U5.p('FSW'), U5.p('BOOT')
y5 = 213.36
x_in5 = vin5[0] - 33.02
x_sw5 = sw5[0] + 12.7
rail('VSYS', (x_in5, y5))
L3 = s.add('Device:L', 'L3', '1uH FXL0630-1R0-M', x_sw5 - 8.89, y5, 90, footprint='JLCImport:FXL0630-1R0-M',
           lcsc='C167216', fields={'_ref_at': (x_sw5 - 11.43, y5 - 3.81), '_val_at': (x_sw5 - 16.51, y5 - 6.35)})
s.wire((x_in5, y5), L3.p('1'))
s.wire((vin5[0] - 5.08, y5), (vin5[0] - 5.08, vin5[1]), vin5)
for i, (ref, v) in enumerate((('C20', '10u/25V'), ('C21', '10u/25V'), ('C22', '10u/25V'), ('C23', '100n'))):
    shunt(C, ref, v, (x_in5 + 5.08 + i * 5.08, y5))
s.wire(L3.p('2'), (x_sw5, y5), (x_sw5, boot[1]))
s.wire(sw5, (x_sw5, sw5[1]))
R17 = R('R17', '267k', fsw[0] + 2.54 + 3.81, fsw[1], 90)       # FSW resistor goes to SW (datasheet s8.3.3)
s.wire(fsw, R17.p('1')); s.wire(R17.p('2'), (x_sw5, fsw[1]))
C24 = C('C24', '100n', boot[0] + 2.54 + 3.81, boot[1], 90)
s.wire(boot, C24.p('1')); s.wire(C24.p('2'), (x_sw5, boot[1]))
vcc5 = U5.p('VCC')
y_vcc5 = y5 + 5.08
s.wire(vcc5, (vcc5[0], y_vcc5), (vcc5[0] - 10.16, y_vcc5))
shunt(C, 'C25', '1u', (vcc5[0] - 5.08, y_vcc5))
shunt(C, 'C26', '1u', (vcc5[0] - 10.16, y_vcc5))
en5 = U5.p('EN')
s.wire(en5, (en5[0] - 15.24, en5[1])); s.label('EN', en5[0] - 15.24, en5[1], 180)
s.nc(U5.p('MODE')); s.nc(U5.p('11')); s.nc(U5.p('12'))
ss, il5 = U5.p('SS'), U5.p('ILIM')
s.wire(ss, (ss[0] - 10.16, ss[1]))
shunt(C, 'C27', '10n', (ss[0] - 10.16, ss[1]))
s.wire(il5, (il5[0] - 5.08, il5[1]))
shunt(R, 'R18', '69.8k', (il5[0] - 5.08, il5[1]))
gnd(U5.p('PGND')); gnd(U5.p('AGND'))
fb5, cp5, vo5 = U5.p('FB'), U5.p('COMP'), U5.p('VOUT')
# COMP network close to the pin
s.wire(cp5, (cp5[0] + 10.16, cp5[1]))
R21, r21b = down_part(R, 'R21', '28.7k', (cp5[0] + 5.08, cp5[1]))
shunt(C, 'C28', '680p', r21b)
shunt(C, 'C29', '33p', (cp5[0] + 10.16, cp5[1]))
# VOUT (pre-switch): FB divider, output caps, load switch
x_fb = vo5[0] + 17.78
x_v5 = vo5[0] + 40.64
s.wire(vo5, (x_v5, vo5[1]))
R19, r19b = down_part(R, 'R19', '220k', (x_fb, vo5[1]))
s.wire(fb5, r19b)
s.wire(r19b, (x_fb + 5.08, r19b[1]))
shunt(R, 'R20', '69.8k', (x_fb + 5.08, r19b[1]))
shunt(C, 'C30', '47u/16V', (vo5[0] + 27.94, vo5[1]))
shunt(C, 'C31', '47u/16V', (vo5[0] + 33.02, vo5[1]))
Q5 = s.add('minipc:CSD25404Q3', 'Q5', 'CSD25404Q3', 0, 0, 270, footprint='Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET',
           lcsc='C2865523', mirror='x')
q5s = Q5.p('5'); Q5.x += x_v5 + 12.7 - q5s[0]; Q5.y += vo5[1] - q5s[1]
s.wire((x_v5, vo5[1]), Q5.p('5'))
q5g = Q5.p('4')
R22 = R('R22', '100k', x_v5, vo5[1] + 3.81)
C32 = C('C32', '10n', x_v5 + 5.08, vo5[1] + 3.81)
y_g5 = R22.p('2')[1]
s.wire(R22.p('2'), C32.p('2'), (q5g[0], y_g5), q5g)
R23 = R('R23', '10k', q5g[0], y_g5 + 3.81)
Q6 = s.add('minipc:2N7002', 'Q6', '2N7002', 0, 0, 0, footprint='Package_TO_SOT_SMD:SOT-23', lcsc='C8545')
q6d = Q6.p('3'); Q6.x += R23.p('2')[0] - q6d[0]; Q6.y += R23.p('2')[1] + 2.54 - q6d[1]
s.wire(R23.p('2'), Q6.p('3'))
gnd(Q6.p('2'))
s.wire(Q6.p('1'), (Q6.p('1')[0] - 7.62, Q6.p('1')[1])); s.label('EN', Q6.p('1')[0] - 7.62, Q6.p('1')[1], 180)
q5d = Q5.p('1')
s.wire(q5d, (q5d[0] + 10.16, q5d[1]))
rail('+5V', (q5d[0] + 10.16, q5d[1]))
pad('J7', '+5V OUT', (q5d[0] + 10.16, q5d[1]), PAD_PWR)

# ================================================================== G. 3.3 V buck-boost (TPS63802)
header('3.3 V / 1.5 A buck-boost TPS63802 (WEBENCH design 36)', 449.58, 190.5)
U6 = s.add('minipc:TPS63802', 'U6', 'TPS63802', 495.3, 241.3, footprint='JLCImport:TPS63802DLAR', lcsc='C2845237')
vin6 = U6.p('VIN')
x_in6 = vin6[0] - 17.78
rail('VSYS', (x_in6, vin6[1] - 7.62))
s.wire((x_in6, vin6[1] - 7.62), (x_in6, vin6[1]), vin6)
shunt(C, 'C33', '22u/6.3V', (x_in6 + 7.62, vin6[1]))
l1, l2 = U6.p('L1'), U6.p('L2')
y_l4 = l1[1] - 7.62
L4 = s.add('Device:L', 'L4', '0.47uH FXL0530-R47-M', (l1[0] + l2[0]) / 2, y_l4, 90,
           footprint='JLCImport:FXL0530-R47-M', lcsc='C475515',
           fields={'_ref_at': (l1[0] - 2.54, y_l4 - 3.81), '_val_at': (l1[0] - 7.62, y_l4 - 6.35)})
s.wire(l1, (l1[0], y_l4), L4.p('1')) if L4.p('1')[0] != l1[0] else s.wire(l1, L4.p('1'))
s.wire(l2, (l2[0], y_l4), L4.p('2')) if L4.p('2')[0] != l2[0] else s.wire(l2, L4.p('2'))
en6, md6, pg6 = U6.p('EN'), U6.p('MODE'), U6.p('PG')
s.wire(en6, (en6[0] - 12.7, en6[1])); s.label('EN', en6[0] - 12.7, en6[1], 180)
s.wire(md6, (md6[0] - 2.54, md6[1]), (md6[0] - 2.54, md6[1] + 12.7))
gnd((md6[0] - 2.54, md6[1] + 12.7))
x_pg = pg6[0] - 7.62
s.wire(pg6, (x_pg - 7.62, pg6[1]))
R26 = R('R26', '100k', x_pg, pg6[1] + 3.81, 180)
rail('+3V3', R26.p('1'), 180)
s.label('3V3_PG', x_pg - 7.62, pg6[1], 180)
gnd(U6.p('GND')); gnd(U6.p('AGND'))
vo6, fb6 = U6.p('VOUT'), U6.p('FB')
x_fb6 = vo6[0] + 5.08
s.wire(vo6, (x_fb6 + 22.86, vo6[1]))
R24, r24b = down_part(R, 'R24', '511k', (x_fb6, vo6[1]))
s.wire(fb6, r24b)
s.wire(r24b, (x_fb6 + 5.08, r24b[1]))
shunt(R, 'R25', '91k', (x_fb6 + 5.08, r24b[1]))
shunt(C, 'C34', '22u/25V', (x_fb6 + 12.7, vo6[1]))
rail('+3V3', (x_fb6 + 22.86, vo6[1]))
pad('J8', '+3V3 OUT', (x_fb6 + 22.86, vo6[1]), PAD_PWR)

# ------------------------------------------------------------------ power flags (rails fed only through passives)
for i, net in enumerate(('VBUS', 'BAT', '+12V', '+5V', 'GND')):
    x, y = 391.16 + i * 15.24, 172.72
    s.add('power:PWR_FLAG', '#FLG%02d' % (i + 1), 'PWR_FLAG', x, y, in_bom=False, on_board=False)
    s.wire((x, y), (x, y + 5.08))
    s.power(net, x, y + 5.08, 180 if net != 'GND' else 0)

# ------------------------------------------------------------------ write
open(os.path.join(HW, 'minipc.kicad_sym'), 'w').write(symbols.library_text())
tbl = os.path.join(HW, 'sym-lib-table')
t = open(tbl).read()
if '"minipc"' not in t:
    t = t.rstrip().rstrip(')') + '  (lib (name "minipc")(type "KiCad")(uri "${KIPRJMOD}/minipc.kicad_sym")(options "")(descr "redrawn symbols"))\n)\n'
    open(tbl, 'w').write(t)
out = os.path.join(HW, 'minipc-power.kicad_sch')
s.write(out)
bad = s.pin_on_wire_interior()
print('wrote', out, '| parts', len([p for p in s.parts if not p.ref.startswith('#')]), '| wires', len(s.wires))
if bad:
    print('PINS ON WIRE INTERIORS (check):', bad)
