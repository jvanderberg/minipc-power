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
PAD_PWR_GND = 'TestPoint:TestPoint_THTPad_D2.5mm_Drill1.2mm'     # round = ground / negative
PAD_SIG_GND = 'TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm'

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
    parts = val.split('/')
    f = {'Description': desc}
    if len(parts) > 1 and rot in (0, 180):
        f.update({'Voltage': parts[1], '_visible': ['Voltage']})
    elif len(parts) > 1:
        f['Voltage'] = parts[1]
    return s.add('Device:C', ref, parts[0] + 'F', x, y, rot, footprint=fp, lcsc=lc, fields=f)


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
    return s.add('Connector:TestPoint', ref, label, pt[0], pt[1], 0, footprint=fp, in_bom=False,
                 fields={'_ref_at': (pt[0] + 1.27, pt[1] - 3.81), '_val_at': (pt[0] + 1.27, pt[1] - 6.35)})


def header(t, x, y):
    s.text(t, x, y, 2.0, bold=True)


SP = 10.16          # spacing between neighbouring shunt parts
NC_ = s.nc


def ind(ref, val, mpn, x, y, fp, lcsc, rot=90):
    return s.add('Device:L', ref, val, x, y, rot, footprint=fp, lcsc=lcsc, fields={'Description': mpn})


# ================================================================== A. USB-C input + PD sink
header('USB-C input, PD sink (requests 9 V)', 20.32, 35.56)
J1 = s.add('Connector:USB_C_Receptacle_USB2.0_16P', 'J1', 'USB-C HRO TYPE-C-31-M-12', 35.56, 76.2,
           footprint='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12', lcsc='C165948',
           fields={'_ref_at': (25.4, 50.8), '_val_at': (25.4, 104.14)})
U1 = s.add('minipc:CH224Q', 'U1', 'CH224Q', 96.52, 68.58, footprint='JLCImport:CH224Q_C46061833', lcsc='C46061833')
vb = J1.p('A4')
U1.y += vb[1] - U1.p('VHV')[1]          # align U1's VHV/CC/D rows with the connector
s.wire(vb, U1.p('VHV'))
s.vh((U1.p('VBUS')[0] - 2.54, vb[1]), U1.p('VBUS'))
x_vbus_up = vb[0] + 5.08
y_bus = 45.72
s.wire((x_vbus_up, vb[1]), (x_vbus_up, y_bus))
D1 = s.add('Device:D_Zener', 'D1', 'SMF12A', x_vbus_up + SP, y_bus + 3.81, 270, footprint='Diode_SMD:D_SOD-123F',
           lcsc='C123800', fields={'Description': 'TVS 12 V standoff', '_ref_at': (x_vbus_up + SP + 3.81, y_bus + 2.54),
                                   '_val_at': (x_vbus_up + SP + 3.81, y_bus + 5.08)})
gnd(D1.p('2'))
shunt(C, 'C1', '1u', (x_vbus_up + 2 * SP, y_bus))
s.wire(J1.p('A5'), U1.p('CC1'))
s.wire(J1.p('B5'), U1.p('CC2'))
s.wire(J1.p('A7'), U1.p('DM'))
s.wire(J1.p('B7'), (J1.p('B7')[0] + 2.54, J1.p('B7')[1]), (J1.p('A7')[0] + 2.54, J1.p('A7')[1]))
s.wire(J1.p('A6'), U1.p('DP'))
s.wire(J1.p('B6'), (J1.p('B6')[0] + 2.54, J1.p('B6')[1]), (J1.p('A6')[0] + 2.54, J1.p('A6')[1]))
NC_(J1.p('A8')); NC_(J1.p('B8'))
gnd(J1.p('A1'))
s.wire(J1.p('SH'), J1.p('A1'))
cfg = U1.p('CFG1')
s.wire(cfg, (cfg[0] + 7.62, cfg[1]))
shunt(R, 'R1', '6.8k', (cfg[0] + 7.62, cfg[1]))
for n in ('CFG2', 'CFG3', '~{PG}'):
    NC_(U1.p(n))
gnd(U1.p('GND'))
s.text('R1 6.8k selects 9 V (CH224 table 5-1).\nCharger D+/D- are left open on purpose:\nILIM sets the input limit.', 86.36, 109.22)

# ================================================================== B. Charger
header('Charger BQ25606: standalone NVDC, 1.44 A charge, 1.92 A input limit', 142.24, 35.56)
U2 = s.add('minipc:BQ25606', 'U2', 'BQ25606', 210.82, 99.06,
           footprint='Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias',
           lcsc='C374063')
pv = U2.p('VBUS')
x_drop = pv[0] - 35.56
s.wire((x_vbus_up, y_bus), (x_drop, y_bus), (x_drop, pv[1]), pv)
rail('VBUS', (x_drop, y_bus))
s.wire((pv[0] - 2.54, pv[1]), (pv[0] - 2.54, U2.p('VAC')[1]), U2.p('VAC'))
shunt(C, 'C2', '1u', (x_drop + 7.62, pv[1]))
pm = U2.p('PMID')
s.wire(pm, (x_drop + 7.62 + SP, pm[1]))
shunt(C, 'C3', '10u/25V', (x_drop + 7.62 + SP, pm[1]))
for n in ('D+', 'D-', 'VSET', 'NC'):
    NC_(U2.p(n))
il, ic_ = U2.p('ILIM'), U2.p('ICHG')
s.wire(il, (x_drop + 7.62, il[1]))
shunt(R, 'R2', '249', (x_drop + 7.62, il[1]))
s.wire(ic_, (x_drop + 7.62 + SP, ic_[1]))
shunt(R, 'R3', '470', (x_drop + 7.62 + SP, ic_[1]))
ce, otg = U2.p('~{CE}'), U2.p('OTG')
x_ce = ce[0] - 5.08
s.wire(ce, (x_ce, ce[1]), (x_ce, otg[1] + 10.16))
s.wire(otg, (x_ce, otg[1]))
gnd((x_ce, otg[1] + 10.16))
gnd(U2.p('GND'))
s.text('ILIM 249R -> 1.92 A (<= 2 A of an 18 W PD charger)\nICHG 470R -> 1.44 A    VSET open -> 4.208 V',
       x_drop - 12.7, U2.p('NC')[1] + 30.48)
# BTST / SW / L1 / SYS / BAT
bt, sw = U2.p('BTST'), U2.p('SW')
x_l = sw[0] + 17.78
s.wire(bt, (bt[0] + 5.08, bt[1]), (bt[0] + 5.08, bt[1] - 5.08))
C4 = C('C4', '47n', bt[0] + 8.89, bt[1] - 5.08, 90)
s.wire(C4.p('2'), (x_l, C4.p('2')[1]), (x_l, sw[1]))
s.wire(sw, (x_l, sw[1]))
L1 = ind('L1', '2.2uH', 'FXL0630-2R2-M', x_l + 3.81, sw[1], 'JLCImport:FXL0630-2R2-M', 'C167218')
sy, ba = U2.p('SYS'), U2.p('BAT')
x_sys = L1.p('2')[0] + 7.62
s.wire(L1.p('2'), (x_sys, sw[1]), (x_sys, sy[1]), sy)
y_vs = sw[1] - 17.78
s.wire((x_sys, sw[1]), (x_sys, y_vs), (x_sys + 2 * SP, y_vs))
shunt(C, 'C5', '10u/25V', (x_sys + SP, y_vs))
rail('VSYS', (x_sys + 2 * SP, y_vs))
x_bat = x_sys + 3 * SP
s.wire(ba, (x_bat, ba[1]))
shunt(C, 'C6', '10u/10V', (x_bat - SP, ba[1]))
s.wire((x_bat, ba[1]), (x_bat, ba[1] - 7.62))
rail('BAT', (x_bat, ba[1] - 7.62))
# STAT: charge LED to VSYS + pad; PG: label to its pad
st, pg = U2.p('STAT'), U2.p('~{PG}')
x_led = st[0] + 12.7
s.wire(st, (x_led - 3.81, st[1]))
pad('J11', 'CHG', (st[0] + 5.08, st[1]))
LED1 = s.add('Device:LED', 'LED1', 'red', x_led, st[1], 0, footprint='LED_SMD:LED_0603_1608Metric', lcsc='C2286',
             fields={'Description': 'charging indicator', '_ref_at': (x_led, st[1] - 2.54),
                     '_val_at': (x_led, st[1] + 2.54), '_just': 'center'})
R6 = R('R6', '1k', LED1.p('2')[0] + 3.81 + 2.54, st[1], 90)
s.wire(LED1.p('2'), R6.p('1'))
rail('VSYS', R6.p('2'))
s.wire(pg, (pg[0] + 35.56, pg[1]))
s.label('PG_CHG', pg[0] + 35.56, pg[1])
# REGN cap + RT1/RT2 divider to TS, NTC pad
rg, ts = U2.p('REGN'), U2.p('TS')
x_rt = rg[0] + 7.62
s.wire(rg, (x_rt + SP, rg[1]))
R4, r4b = down_part(R, 'R4', '5.23k', (x_rt, rg[1]))
s.wire(r4b, (x_rt, ts[1]))
shunt(C, 'C7', '4.7u/16V', (x_rt + SP, rg[1]))
s.wire(ts, (x_rt + 2 * SP + 5.08, ts[1]))
shunt(R, 'R5', '30.9k', (x_rt + SP, ts[1]))
pad('J4', 'NTC', (x_rt + 2 * SP + 5.08, ts[1]))
s.text('RT1 5.23k / RT2 30.9k: 0-60 C window\nwith a 103AT NTC from J4 to J5 (GND)', x_rt + 2.54, ts[1] + 15.24)

# ================================================================== C. Cell protection + reverse block
header('1S2P pack: fuse, reverse block, HY2113 protector', 337.82, 35.56)
yc = 134.62
J2 = pad('J2', 'BAT+', (350.52, 58.42), PAD_PWR)
F1 = s.add('Device:Fuse', 'F1', '10A', 360.68, 58.42, 90, footprint='Fuse:Fuse_Littelfuse-NANO2-451_453',
           lcsc='C44479', fields={'Description': 'Littelfuse 0451010.MRL'})
s.wire(J2.p('1'), F1.p('1'))
s.wire(F1.p('2'), (375.92, 58.42))
rail('BAT', (375.92, 58.42))
U3 = s.add('minipc:HY2113', 'U3', 'HY2113-MB1A', 378.46, 104.14, footprint='Package_TO_SOT_SMD:SOT-23-6',
           lcsc='C168772')
vss = U3.p('VSS')
x_celln = vss[0]


def fet_at(ref, val, lcsc, fp, rot, mirror, pin, target):
    q = s.add('minipc:' + val, ref, val, 0, 0, rot, footprint=fp, lcsc=lcsc, mirror=mirror)
    p0 = q.p(pin)
    q.x += target[0] - p0[0]
    q.y += target[1] - p0[1]
    return q


J3 = pad('J3', 'BAT-', (350.52, yc), PAD_PWR_GND)
Q1 = fet_at('Q1', 'CSD13202Q2', 'C187839', 'Package_SON:Texas_DQK', 90, None, '1', (360.68, yc))
s.wire(J3.p('1'), Q1.p('1'))
s.wire(Q1.p('4'), (x_celln, yc))
s.wire(vss, (x_celln, yc))
Q2 = fet_at('Q2', 'CSD13202Q2', 'C187839', 'Package_SON:Texas_DQK', 270, None, '4', (x_celln + SP, yc))
s.wire((x_celln, yc), Q2.p('4'))
Q3 = fet_at('Q3', 'CSD13202Q2', 'C187839', 'Package_SON:Texas_DQK', 90, 'x', '1', (Q2.p('1')[0] + SP, yc))
s.wire(Q2.p('1'), Q3.p('1'))
s.wire(Q3.p('4'), (Q3.p('4')[0] + 7.62, yc))
gnd((Q3.p('4')[0] + 7.62, yc))
Q2.fields.update({'_ref_at': (Q2.x - 5.08, yc + 7.62), '_val_at': (Q2.x - 5.08, yc + 10.16), '_just': 'left'})
Q3.fields.update({'_ref_at': (Q3.x + 3.81, yc - 7.62), '_val_at': (Q3.x + 3.81, yc - 5.08), '_just': 'left'})
Q1.fields.update({'_ref_at': (Q1.x + 5.08, yc - 10.16), '_val_at': (Q1.x + 5.08, yc - 7.62), '_just': 'left'})
s.text('pack- = board GND', Q3.p('4')[0] + 2.54, yc + 10.16)
oc, od = U3.p('OC'), U3.p('OD')
s.wire(oc, (Q3.p('3')[0], oc[1]), Q3.p('3'))
s.wire(od, (Q2.p('3')[0], od[1]), Q2.p('3'))
vdd, cs = U3.p('VDD'), U3.p('CS')
x_vdd = vdd[0] - SP - 2.54
s.wire(vdd, (x_vdd - 10.16, vdd[1]))
R7 = R('R7', '330', x_vdd, vdd[1] - 3.81)
rail('BAT', R7.p('1'))
C8 = C('C8', '100n', x_vdd - 10.16, vdd[1] + 3.81)
s.wire(C8.p('2'), (x_vdd - 10.16, yc - 15.24), (x_celln, yc - 15.24))
NC_(U3.p('NC'))
s.wire(cs, (cs[0] - 5.08, cs[1]))
r8 = shunt(R, 'R8', '2k', (cs[0] - 5.08, cs[1]))
r8.fields.update({'_just': 'right', '_ref_at': (r8.x - 2.54, r8.y - 1.27), '_val_at': (r8.x - 2.54, r8.y + 1.27)})
qg = Q1.p('3')
s.wire(qg, (qg[0], qg[1] + 10.16))
R10 = R('R10', '1M', qg[0] + 3.81 + 2.54, qg[1] + 5.08, 90)
s.wire((qg[0], qg[1] + 5.08), R10.p('1'))
s.wire(R10.p('2'), (x_celln, qg[1] + 5.08), (x_celln, yc))
R9 = R('R9', '10k', qg[0] - 3.81 - 2.54, qg[1] + 10.16, 90)
s.wire((qg[0], qg[1] + 10.16), R9.p('2'))
rail('BAT', R9.p('1'))
s.text('Q1: a reversed pack turns it off and its body diode\nblocks, so U3 never sees reverse voltage.\n'
       'Trip: 250 mV / (Q2+Q3) = ~8 A hot ... ~15 A cold.', 345.44, yc + 33.02)

# ================================================================== D. Pads, enable, sense
header('Solder pads, enable switch, battery sense', 452.12, 35.56)
xp = 462.28
pad('J9', 'EN (switch)', (xp, 58.42))
pad('J10', 'VSYS (switch)', (xp + 30.48, 58.42))
rail('VSYS', (xp + 30.48, 50.8))
s.wire((xp + 30.48, 50.8), (xp + 30.48, 58.42))
R27 = R('R27', '1k', xp + 2.54 + 3.81, 66.04, 90)
s.wire((xp, 58.42), (xp, 66.04), R27.p('1'))
x_en = R27.p('2')[0] + 5.08
s.wire(R27.p('2'), (x_en + 2 * SP + 5.08, 66.04))
shunt(R, 'R28', '100k', (x_en, 66.04))
shunt(C, 'C35', '100n', (x_en + SP, 66.04))
s.label('EN', x_en + 2 * SP + 5.08, 66.04)
s.text('Switch closed = on: U4, U5, U6 run and Q6 closes the 5 V switch.\nCharging works with the switch open.',
       xp - 2.54, 86.36)
R29 = R('R29', '470k', xp + 2.54, 104.14)
rail('BAT', R29.p('1'))
s.wire(R29.p('2'), (xp + 2.54, 111.76), (xp + 2.54 + 2 * SP + 5.08, 111.76))
shunt(R, 'R30', '1M', (xp + 2.54 + SP, 111.76))
shunt(C, 'C36', '100n', (xp + 2.54 + 2 * SP, 111.76))
pad('J13', 'VBAT_SENSE', (xp + 2.54 + 2 * SP + 5.08, 111.76))
s.text('2.96 V at 4.35 V, 3 uA', xp + 7.62, 101.6)
pad('J12', 'PG_CHG', (xp, 142.24)); s.wire((xp, 142.24), (xp, 147.32)); s.label('PG_CHG', xp, 147.32, 270)
pad('J14', '3V3_PG', (xp + 20.32, 142.24)); s.wire((xp + 20.32, 142.24), (xp + 20.32, 147.32)); s.label('3V3_PG', xp + 20.32, 147.32, 270)
for i, ref in enumerate(('J5', 'J15', 'J16', 'J17')):
    x = xp + 45.72 + i * SP
    pad(ref, 'GND' if ref != 'J5' else 'NTC-', (x, 142.24), PAD_PWR_GND if ref != 'J5' else PAD_SIG_GND)
    gnd((x, 142.24))
for i, ref in enumerate(('H1', 'H2')):
    s.add('Mechanical:MountingHole', ref, 'M2', xp + i * 15.24, 167.64, footprint='MountingHole:MountingHole_2.2mm_M2', in_bom=False)

# ================================================================== E. 12 V boost (TPS61178)
header('12 V / 0.5 A boost TPS61178 (WEBENCH design 33)', 20.32, 200.66)
U4 = s.add('minipc:TPS61178', 'U4', 'TPS61178', 101.6, 254.0, footprint='JLCImport:TPS61178RNWR', lcsc='C127918')
vin, sw4 = U4.p('VIN'), U4.p('SW')
y_top = 220.98
x_in = vin[0] - 40.64
x_sw = sw4[0] + 15.24
rail('VSYS', (x_in, y_top))
L2 = ind('L2', '3.3uH', 'FXL0630-3R3-M', x_sw - 8.89, y_top, 'JLCImport:FXL0630-3R3-M', 'C167219')
s.wire((x_in, y_top), L2.p('1'))
s.wire(L2.p('2'), (x_sw, y_top), (x_sw, sw4[1]), sw4)
s.wire((vin[0] - 5.08, y_top), (vin[0] - 5.08, vin[1]), vin)
shunt(C, 'C9', '22u/25V', (x_in + SP, y_top))
shunt(C, 'C10', '22u/25V', (x_in + 2 * SP, y_top))
bst, vcc = U4.p('BST'), U4.p('VCC')
y_b = y_top + 12.7
s.wire(bst, (bst[0], y_b), (x_sw - 10.16, y_b))
C11 = C('C11', '100n', x_sw - 10.16 + 3.81, y_b, 90)
s.wire(C11.p('2'), (x_sw, y_b))
y_v = y_top + 7.62
s.wire(vcc, (vcc[0], y_v), (vcc[0] - SP, y_v))
shunt(C, 'C12', '4.7u/16V', (vcc[0] - SP, y_v))
en4 = U4.p('EN')
s.wire(en4, (en4[0] - 17.78, en4[1])); s.label('EN', en4[0] - 17.78, en4[1], 180)
fr, ilm, comp = U4.p('FREQ/SYNC'), U4.p('ILIMIT'), U4.p('COMP')
s.wire(fr, (fr[0] - 25.4, fr[1]))
shunt(R, 'R11', '169k', (fr[0] - 25.4, fr[1]))
s.wire(ilm, (ilm[0] - 15.24, ilm[1]))
shunt(R, 'R12', '162k', (ilm[0] - 15.24, ilm[1]))
s.wire(comp, (comp[0] - 5.08, comp[1]))
R15, r15b = down_part(R, 'R15', '44.2k', (comp[0] - 5.08, comp[1]))
shunt(C, 'C13', '1.8n', r15b)
gnd(U4.p('PGND')); gnd(U4.p('AGND'))
vo, dis, fb = U4.p('VOUT'), U4.p('DISDRV'), U4.p('FB')
x_d = dis[0] + 15.24
c14x = x_d + 12.7
x_q = c14x + 4 * SP
s.wire(vo, (x_q, vo[1]))
shunt(C, 'C14', '4.7u/25V', (c14x, vo[1]))
shunt(C, 'C15', '4.7u/25V', (c14x + SP, vo[1]))
Q4 = fet_at('Q4', 'CSD25404Q3', 'C2865523', 'Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET', 270, 'x', '5',
            (x_q, vo[1]))
Q4.fields.update({'_ref_at': (Q4.x - 2.54, vo[1] - 5.08), '_val_at': (Q4.x - 2.54, vo[1] - 7.62)})
y_g = vo[1] + 17.78
R16, r16b = down_part(R, 'R16', '178k', (c14x + 2 * SP, vo[1]))
C16, c16b = down_part(C, 'C16', '22n', (c14x + 3 * SP, vo[1]))
s.wire(r16b, (r16b[0], y_g)); s.wire(c16b, (c16b[0], y_g))
s.wire(dis, (x_d, dis[1]), (x_d, y_g), (Q4.p('4')[0], y_g), Q4.p('4'))
q4d = Q4.p('1')
x_out = q4d[0] + 3 * SP + 12.7
s.wire(q4d, (x_out, q4d[1]))
for i, ref in enumerate(('C17', 'C18', 'C19')):
    shunt(C, ref, '22u/25V/1210', (q4d[0] + 5.08 + i * SP, q4d[1]))
s.wire((x_out - 7.62, q4d[1]), (x_out - 7.62, q4d[1] - 5.08))
rail('+12V', (x_out - 7.62, q4d[1] - 5.08))
pad('J6', '+12V OUT', (x_out, q4d[1]), PAD_PWR)
x_fb = fb[0] + 2.54
s.wire(fb, (x_fb, fb[1]))
R13 = R('R13', '732k', x_fb, fb[1] - 3.81)
rail('+12V', R13.p('1'))
shunt(R, 'R14', '80.6k', (x_fb, fb[1]))
s.text('FB senses after Q4 (VOUT2), as in datasheet fig. 22.\nRgate/Cgate: Vgs = 178k x 55 uA = 9.8 V, ~0.5 ms turn-on.',
       x_d + 7.62, y_g + 12.7)

# ================================================================== F. 5 V boost (TPS61088-Q1) + load switch
header('5 V / 2.5 A boost TPS61088-Q1 (WEBENCH design 37) + load switch', 233.68, 200.66)
U5 = s.add('minipc:TPS61088-Q1', 'U5', 'TPS61088-Q1', 314.96, 256.54,
           footprint='Package_DFN_QFN:Texas_VQFN-RHL-20_ThermalVias', lcsc='C1850341')
U5.fields.update({'_ref_at': (U5.x - 8.89, U5.y - 21.59 - 3.81), '_val_at': (U5.x - 8.89, U5.y - 21.59 - 1.27)})
vin5, sw5, fsw, boot = U5.p('VIN'), U5.p('SW'), U5.p('FSW'), U5.p('BOOT')
y5 = 220.98
x_in5 = vin5[0] - 50.8
x_sw5 = sw5[0] + 22.86
rail('VSYS', (x_in5, y5))
L3 = ind('L3', '1uH', 'FXL0630-1R0-M', x_sw5 - 8.89, y5, 'JLCImport:FXL0630-1R0-M', 'C167216')
s.wire((x_in5, y5), L3.p('1'))
s.wire((vin5[0] - 5.08, y5), (vin5[0] - 5.08, vin5[1]), vin5)
for i, (ref, v) in enumerate((('C20', '10u/25V'), ('C21', '10u/25V'), ('C22', '10u/25V'), ('C23', '100n'))):
    shunt(C, ref, v, (x_in5 + SP + i * SP, y5))
s.wire(L3.p('2'), (x_sw5, y5), (x_sw5, boot[1]))
s.wire(sw5, (x_sw5, sw5[1]))
R17 = R('R17', '267k', fsw[0] + 2.54 + 3.81, fsw[1], 90)
s.wire(fsw, R17.p('1')); s.wire(R17.p('2'), (x_sw5, fsw[1]))
C24 = C('C24', '100n', boot[0] + 2.54 + 3.81, boot[1], 90)
s.wire(boot, C24.p('1')); s.wire(C24.p('2'), (x_sw5, boot[1]))
R17.fields.update({'_ref_at': (R17.x, fsw[1] - 2.54), '_val_at': (x_sw5 + 7.62, fsw[1])})
C24.fields.update({'_ref_at': (C24.x, boot[1] + 2.54), '_val_at': (x_sw5 + 7.62, boot[1])})
vcc5 = U5.p('VCC')
y_vcc5 = y5 + 7.62
s.wire(vcc5, (vcc5[0], y_vcc5), (vcc5[0] + 2 * 7.62, y_vcc5))
shunt(C, 'C25', '1u', (vcc5[0] + 7.62, y_vcc5))
shunt(C, 'C26', '1u', (vcc5[0] + 2 * 7.62, y_vcc5))
en5 = U5.p('EN')
s.wire(en5, (en5[0] - 20.32, en5[1])); s.label('EN', en5[0] - 20.32, en5[1], 180)
NC_(U5.p('MODE')); NC_(U5.p('11')); NC_(U5.p('12'))
ss, il5 = U5.p('SS'), U5.p('ILIM')
s.wire(ss, (ss[0] - 2 * SP, ss[1]))
shunt(C, 'C27', '10n', (ss[0] - 2 * SP, ss[1]))
s.wire(il5, (il5[0] - SP, il5[1]))
shunt(R, 'R18', '69.8k', (il5[0] - SP, il5[1]))
gnd(U5.p('PGND')); gnd(U5.p('AGND'))
fb5, cp5, vo5 = U5.p('FB'), U5.p('COMP'), U5.p('VOUT')
s.wire(cp5, (cp5[0] + 5.08 + SP, cp5[1]))
R21, r21b = down_part(R, 'R21', '28.7k', (cp5[0] + 5.08, cp5[1]))
shunt(C, 'C28', '680p', r21b)
shunt(C, 'C29', '33p', (cp5[0] + 5.08 + SP, cp5[1]))
x_fb5 = x_sw5 + 7.62
x_v5 = x_fb5 + 4 * SP
s.wire(vo5, (x_v5, vo5[1]))
R19, r19b = down_part(R, 'R19', '220k', (x_fb5, vo5[1]))
s.wire(fb5, r19b)
s.wire(r19b, (x_fb5 + SP, r19b[1]))
shunt(R, 'R20', '69.8k', (x_fb5 + SP, r19b[1]))
shunt(C, 'C30', '47u/16V', (x_fb5 + 2 * SP, vo5[1]))
shunt(C, 'C31', '47u/16V', (x_fb5 + 3 * SP, vo5[1]))
Q5 = fet_at('Q5', 'CSD25404Q3', 'C2865523', 'Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET', 270, 'x', '5',
            (x_v5 + 2 * SP, vo5[1]))
Q5.fields.update({'_ref_at': (Q5.x - 2.54, vo5[1] - 5.08), '_val_at': (Q5.x - 2.54, vo5[1] - 7.62)})
s.wire((x_v5, vo5[1]), Q5.p('5'))
q5g = Q5.p('4')
R22, r22b = down_part(R, 'R22', '100k', (x_v5, vo5[1]))
C32, c32b = down_part(C, 'C32', '10n', (x_v5 + SP, vo5[1]))
y_g5 = vo5[1] + 15.24
s.wire(r22b, (r22b[0], y_g5), (q5g[0], y_g5), q5g)
s.wire(c32b, (c32b[0], y_g5))
R23, r23b = down_part(R, 'R23', '10k', (q5g[0], y_g5))
Q6 = fet_at('Q6', '2N7002', 'C8545', 'Package_TO_SOT_SMD:SOT-23', 0, None, '3', (r23b[0], r23b[1] + 2.54))
s.wire(r23b, Q6.p('3'))
gnd(Q6.p('2'))
s.wire(Q6.p('1'), (Q6.p('1')[0] - 7.62, Q6.p('1')[1])); s.label('EN', Q6.p('1')[0] - 7.62, Q6.p('1')[1], 180)
q5d = Q5.p('1')
s.wire(q5d, (q5d[0] + 22.86, q5d[1]))
s.wire((q5d[0] + 15.24, q5d[1]), (q5d[0] + 15.24, q5d[1] - 5.08))
rail('+5V', (q5d[0] + 15.24, q5d[1] - 5.08))
pad('J7', '+5V OUT', (q5d[0] + 22.86, q5d[1]), PAD_PWR)
s.text('ILIM = 550000 / 69.8k = 7.9 A (-Q1 has a 0.6 V ILIM reference)\nFSW 267k (to SW) = 594 kHz, SS 10 nF = 2.4 ms',
       vin5[0] - 30.48, U5.p('PGND')[1] + 27.94)

# ================================================================== G. 3.3 V buck-boost (TPS63802)
header('3.3 V / 1.5 A buck-boost TPS63802 (WEBENCH design 36)', 20.32, 312.42)
U6 = s.add('minipc:TPS63802', 'U6', 'TPS63802', 76.2, 365.76, footprint='JLCImport:TPS63802DLAR', lcsc='C2845237')
vin6 = U6.p('VIN')
x_vs6 = vin6[0] - 25.4
y_vs6 = vin6[1] - 12.7
rail('VSYS', (x_vs6, y_vs6))
s.wire((x_vs6, y_vs6), (vin6[0] - 5.08, y_vs6), (vin6[0] - 5.08, vin6[1]), vin6)
shunt(C, 'C33', '22u/6.3V', (x_vs6 + SP, y_vs6))
l1, l2 = U6.p('L1'), U6.p('L2')
y_l4 = l1[1] - 10.16
L4 = ind('L4', '0.47uH', 'FXL0530-R47-M', (l1[0] + l2[0]) / 2, y_l4, 'JLCImport:FXL0530-R47-M', 'C475515')
s.wire(l1, (l1[0], y_l4), L4.p('1'))
s.wire(l2, (l2[0], y_l4), L4.p('2'))
L4.fields.update({'_ref_at': (L4.x, y_l4 - 3.81), '_val_at': (L4.x, y_l4 - 6.35)})
en6, pg6, md6 = U6.p('EN'), U6.p('PG'), U6.p('MODE')
s.wire(en6, (en6[0] - 17.78, en6[1])); s.label('EN', en6[0] - 17.78, en6[1], 180)
x_pg = pg6[0] - 7.62
s.wire(pg6, (x_pg - SP, pg6[1]))
R26 = R('R26', '100k', x_pg, pg6[1] + 3.81)
rail('+3V3', R26.p('2'), 180)
s.label('3V3_PG', x_pg - SP, pg6[1], 180)
s.wire(md6, (md6[0] - 2.54, md6[1]), (md6[0] - 2.54, md6[1] + 12.7))
gnd((md6[0] - 2.54, md6[1] + 12.7))
gnd(U6.p('GND')); gnd(U6.p('AGND'))
vo6, fb6 = U6.p('VOUT'), U6.p('FB')
x_fb6 = vo6[0] + 5.08
x_o6 = x_fb6 + 3 * SP
s.wire(vo6, (x_o6, vo6[1]))
R24, r24b = down_part(R, 'R24', '511k', (x_fb6, vo6[1]))
s.wire(fb6, r24b)
s.wire(r24b, (x_fb6 + SP, r24b[1]))
shunt(R, 'R25', '91k', (x_fb6 + SP, r24b[1]))
shunt(C, 'C34', '22u/25V', (x_fb6 + 2 * SP, vo6[1]))
s.wire((x_o6 - 7.62, vo6[1]), (x_o6 - 7.62, vo6[1] - 5.08))
rail('+3V3', (x_o6 - 7.62, vo6[1] - 5.08))
pad('J8', '+3V3 OUT', (x_o6, vo6[1]), PAD_PWR)

# ------------------------------------------------------------------ power flags (rails fed only through passives)
for i, net in enumerate(('VBUS', 'BAT', '+12V', '+5V', 'GND')):
    x, y = 500.38 + i * 10.16, 162.56
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
