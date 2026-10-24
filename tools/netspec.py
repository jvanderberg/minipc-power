"""Intended connectivity of minipc-power (the circuit, independent of how it is drawn).

check_netlist(xml) compares KiCad's exported netlist against this: every intended net must be exactly one KiCad net
(no splits) and no KiCad net may contain pins from two intended nets (no shorts). Names are ours; KiCad's names are
reported alongside. Pins not listed must be unconnected (single-pin nets or no-connect).
"""
import xml.etree.ElementTree as ET

NETS = {
    'GND': ['J1.A1', 'J1.A12', 'J1.B1', 'J1.B12', 'J1.SH', 'D1.2', 'C1.2', 'R1.2', 'U1.11',
            'C2.2', 'C3.2', 'R2.2', 'R3.2', 'U2.9', 'U2.6', 'U2.17', 'U2.18', 'U2.25', 'C5.2', 'C6.2', 'C7.2', 'R5.2',
            'Q3.4', 'Q3.7', 'R8.2',
            'R28.2', 'C35.2', 'R30.2', 'C36.2', 'J5.1', 'J15.1', 'J16.1', 'J17.1',
            'C9.2', 'C10.2', 'C37.2', 'C12.2', 'R11.2', 'R12.2', 'U4.6', 'U4.2', 'C14.2', 'C15.2', 'C17.2', 'C18.2', 'C19.2',
            'R14.2', 'C13.2',
            'C20.2', 'C21.2', 'C22.2', 'C23.2', 'C25.2', 'C26.2', 'C27.2', 'R18.2', 'U5.21', 'U5.20', 'C28.2',
            'C29.2', 'R20.2', 'C30.2', 'C31.2', 'Q6.2',
            'C33.2', 'U6.2', 'U6.8', 'U6.3', 'C34.2', 'R25.2'],
    'VBUS': ['J1.A4', 'J1.A9', 'J1.B4', 'J1.B9', 'D1.1', 'C1.1', 'U1.8', 'U1.1', 'U2.24', 'U2.1', 'C2.1'],
    'CC1': ['J1.A5', 'U1.7'], 'CC2': ['J1.B5', 'U1.6'],
    'CFG1': ['U1.9', 'R1.1'],
    'PMID': ['U2.23', 'C3.1'],
    'ILIM': ['U2.8', 'R2.1'], 'ICHG': ['U2.10', 'R3.1'],
    'BTST': ['U2.21', 'C4.1'],
    'SW_CHG': ['U2.19', 'U2.20', 'C4.2', 'L1.1'],
    'VSYS': ['L1.2', 'U2.15', 'U2.16', 'C5.1', 'R6.2', 'J10.1',
             'U4.12', 'C9.1', 'C10.1', 'C37.1', 'L2.1',
             'U5.9', 'C20.1', 'C21.1', 'C22.1', 'C23.1', 'L3.1',
             'U6.10', 'C33.1'],
    'BAT': ['U2.13', 'U2.14', 'C6.1', 'F1.2', 'R7.1', 'R9.1', 'R29.1'],
    'REGN': ['U2.22', 'C7.1', 'R4.1'],
    'TS': ['U2.11', 'R4.2', 'R5.1', 'J4.1'],
    'STAT': ['U2.5', 'LED1.1', 'J11.1'], 'LED_A': ['LED1.2', 'R6.1'],
    'PG_CHG': ['U2.7', 'J12.1'],
    'BATP': ['J2.1', 'F1.1'],
    'BATN': ['J3.1', 'Q1.1', 'Q1.2', 'Q1.5', 'Q1.6', 'Q1.8'],
    'CELLN': ['Q1.4', 'Q1.7', 'U3.6', 'C8.2', 'Q2.4', 'Q2.7', 'R10.2'],
    'Q1G': ['Q1.3', 'R9.2', 'R10.1'],
    'MID': ['Q2.1', 'Q2.2', 'Q2.5', 'Q2.6', 'Q2.8', 'Q3.1', 'Q3.2', 'Q3.5', 'Q3.6', 'Q3.8'],
    'OD': ['U3.1', 'Q2.3'], 'OC': ['U3.3', 'Q3.3'],
    'VDD_P': ['U3.5', 'R7.2', 'C8.1'], 'CS': ['U3.2', 'R8.1'],
    'EN_PAD': ['J9.1', 'R27.1'],
    'EN': ['R27.2', 'R28.1', 'C35.1', 'U4.11', 'U5.2', 'U6.1', 'Q6.1'],
    'VBAT_SENSE': ['R29.2', 'R30.1', 'C36.1', 'J13.1'],
    # 12 V
    'SW12': ['U4.7', 'L2.2', 'C11.2'], 'BST12': ['U4.13', 'C11.1'], 'VCC12': ['U4.10', 'C12.1'],
    'FREQ12': ['U4.1', 'R11.1'], 'ILIM12': ['U4.3', 'R12.1'],
    'VOUT12A': ['U4.8', 'C14.1', 'C15.1', 'Q4.5', 'R16.1', 'C16.1'],
    'GATE12': ['U4.9', 'Q4.4', 'R16.2', 'C16.2'],
    '+12V': ['Q4.1', 'Q4.2', 'Q4.3', 'C17.1', 'C18.1', 'C19.1', 'R13.1', 'J6.1'],
    'FB12': ['U4.5', 'R13.2', 'R14.1'], 'COMP12': ['U4.4', 'R15.1'], 'COMP12RC': ['R15.2', 'C13.1'],
    # 5 V
    'SW5': ['U5.4', 'U5.5', 'U5.6', 'U5.7', 'L3.2', 'R17.2', 'C24.2'], 'FSW5': ['U5.3', 'R17.1'],
    'BOOT5': ['U5.8', 'C24.1'], 'VCC5': ['U5.1', 'C25.1', 'C26.1'], 'SS5': ['U5.10', 'C27.1'],
    'ILIM5': ['U5.19', 'R18.1'],
    'VOUT5A': ['U5.14', 'U5.15', 'U5.16', 'R19.1', 'C30.1', 'C31.1', 'Q5.5', 'R22.1', 'C32.1'],
    'FB5': ['U5.17', 'R19.2', 'R20.1'], 'COMP5': ['U5.18', 'R21.1', 'C29.1'], 'COMP5RC': ['R21.2', 'C28.1'],
    'GATE5': ['Q5.4', 'R22.2', 'C32.2', 'R23.1'], 'Q6D': ['R23.2', 'Q6.3'],
    '+5V': ['Q5.1', 'Q5.2', 'Q5.3', 'J7.1'],
    # 3.3 V
    'L1_33': ['U6.9', 'L4.1'], 'L2_33': ['U6.7', 'L4.2'],
    '+3V3': ['U6.6', 'C34.1', 'R24.1', 'R26.1', 'J8.1'],
    'FB33': ['U6.4', 'R24.2', 'R25.1'], '3V3_PG': ['U6.5', 'R26.2', 'J14.1'],
}


def check_netlist(xml_path):
    root = ET.parse(xml_path).getroot()
    pin2net = {}
    netpins = {}
    for net in root.find('nets'):
        name = net.get('name')
        pins = ['%s.%s' % (n.get('ref'), n.get('pin')) for n in net.findall('node')]
        pins = [p for p in pins if not p.startswith('#')]
        netpins[name] = pins
        for p in pins:
            pin2net[p] = name
    # two-pin passives are symmetric: accept either orientation
    spec = {k: list(v) for k, v in NETS.items()}
    for ref in {p.split('.')[0] for ps in spec.values() for p in ps}:
        if ref[0] in 'RCLF' and not ref.startswith('LED'):
            a, b = ref + '.1', ref + '.2'
            na = next((n for n, ps in spec.items() if a in ps), None)
            nb = next((n for n, ps in spec.items() if b in ps), None)
            if na and nb and pin2net.get(a) and pin2net.get(a) == pin2net.get(next((q for q in spec[nb] if q != b), b)):
                spec[na] = [b if q == a else q for q in spec[na]]
                spec[nb] = [a if q == b else q for q in spec[nb]]
    errors = []
    seen = set()
    for ours, pins in spec.items():
        kn = {pin2net.get(p, '<unconnected %s>' % p) for p in pins}
        if len(kn) > 1:
            errors.append('SPLIT  %-10s -> %s' % (ours, sorted(kn)))
        for k in kn:
            if k in netpins:
                extra = [p for p in netpins[k] if p not in pins]
                if extra and k not in seen:
                    owners = {}
                    for p in extra:
                        o = next((n for n, ps in spec.items() if p in ps), '<unlisted>')
                        owners.setdefault(o, []).append(p)
                    errors.append('SHORT  %-10s (KiCad %s) also has %s' % (ours, k, owners))
                seen.add(k)
    listed = {p for ps in spec.values() for p in ps}
    for k, pins in netpins.items():
        if len(pins) > 1 and not any(p in listed for p in pins):
            errors.append('UNEXPECTED net %s: %s' % (k, pins))
    return errors


if __name__ == '__main__':
    import sys
    errs = check_netlist(sys.argv[1])
    print('\n'.join(errs) if errs else 'netlist matches netspec')
    sys.exit(1 if errs else 0)
