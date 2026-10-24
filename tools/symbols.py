"""Redrawn IC symbols for minipc-power: pins grouped by function (inputs left, outputs right, supplies top,
ground bottom) and real pin types. Pin numbers match the JLCImport footprints, checked against each datasheet's pin
table. Duplicate pins (SW, SYS, BAT, VOUT, GND) are stacked on one connection point; the extra copies are hidden.
"""
import re
from schgen import kstr, SymLib

DEVICE = SymLib('Device', '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Device.kicad_sym')

L = 2.54  # pin length and pitch


def _pin(typ, x, y, rot, name, num, hide=False):
    return ('\t\t\t(pin %s line\n\t\t\t\t(at %s %s %s)\n\t\t\t\t(length %s)%s\n\t\t\t\t(name %s\n\t\t\t\t\t(effects\n'
            '\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t\t(number %s\n'
            '\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n'
            '\t\t\t\t)\n\t\t\t)\n') % (typ, round(x, 4), round(y, 4), rot, L, '\n\t\t\t\t(hide yes)' if hide else '',
                                      kstr(name), kstr(num))


def ic(name, half_w, left=(), right=(), top=(), bottom=(), ref='U', desc='', top_pitch=L):
    """Each side is a list of entries (name, [numbers], type) or None for an empty slot.
    left/right are listed top to bottom, top/bottom left to right."""
    # an empty row under the top pins and above the bottom pins keeps their (vertical) names off the side names
    rows = max(len(left), len(right), 1) + (2 if top else 0) + (2 if bottom else 0)
    half_h = (rows + 1) * L / 2
    half_h = round(half_h / 1.27) * 1.27
    pins = []

    def side(entries, xy, rot):
        for i, e in enumerate(entries):
            if e is None:
                continue
            pname, nums, typ = e
            x, y = xy(i)
            for k, n in enumerate(nums):
                pins.append(_pin(typ, x, y, rot, pname, n, hide=k > 0))
    y0 = half_h - L - (2 * L if top else 0)
    side(left, lambda i: (-half_w - L, y0 - i * L), 0)
    side(right, lambda i: (half_w + L, y0 - i * L), 180)
    # top/bottom pins right-aligned so the left half stays free for the reference and value text
    x0 = half_w - L - (len(top) - 1) * top_pitch
    side(top, lambda i: (x0 + i * top_pitch, half_h + L), 270)
    x0b = half_w - L - (len(bottom) - 1) * L
    side(bottom, lambda i: (x0b + i * L, -half_h - L), 90)
    body = ('\t\t(symbol %s\n\t\t\t(rectangle\n\t\t\t\t(start %s %s)\n\t\t\t\t(end %s %s)\n\t\t\t\t(stroke\n'
            '\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type background)\n'
            '\t\t\t\t)\n\t\t\t)\n\t\t)\n') % (kstr(name + '_0_1'), -half_w, half_h, half_w, -half_h)
    prop = lambda k, v, y, hide: ('\t\t(property %s %s\n\t\t\t(at 0 %s 0)\n\t\t\t(effects\n\t\t\t\t(font\n'
                                  '\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)%s\n\t\t\t)\n\t\t)\n') % (
        kstr(k), kstr(v), y, '\n\t\t\t\t(hide yes)' if hide else '')
    return ('(symbol %s\n\t\t(pin_names\n\t\t\t(offset 0.508)\n\t\t)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n'
            '\t\t(on_board yes)\n' % kstr(name) +
            prop('Reference', ref, half_h + 1.27, False) + prop('Value', name, -half_h - 1.27, False) +
            prop('Footprint', '', 0, True) + prop('Datasheet', '', 0, True) + prop('Description', desc, 0, True) +
            body + '\t\t(symbol %s\n' % kstr(name + '_1_1') + ''.join(pins) + '\t\t)\n\t\t(embedded_fonts no)\n\t)')


PI, PO, PW, IN, OUT, BI, PA, NC, OC = ('power_in', 'power_out', 'power_in', 'input', 'output', 'bidirectional',
                                        'passive', 'no_connect', 'open_collector')

SYMBOLS = {
    # CH224Q (WCH) DFN-10: pin table in the CH224 datasheet (4-1)
    'CH224Q': ic('CH224Q', 7.62,
                 left=[('VBUS', ['8'], PA), ('VHV', ['1'], PA), None, ('CC1', ['7'], BI), ('CC2', ['6'], BI),
                       None, ('DM', ['5'], BI), None, ('DP', ['4'], BI)],
                 right=[('CFG1', ['9'], IN), ('CFG2', ['2'], IN), ('CFG3', ['3'], IN), None, ('~{PG}', ['10'], OC)],
                 bottom=[('GND', ['11'], PI)], desc='USB PD sink controller'),
    # BQ25606 VQFN-24 (SLUSCK6C table 7-1)
    'BQ25606': ic('BQ25606', 10.16,
                  left=[('VBUS', ['24'], PI), ('VAC', ['1'], IN), ('PMID', ['23'], PA), None, ('D+', ['3'], BI),
                        ('D-', ['4'], BI), None, ('ILIM', ['8'], PA), ('ICHG', ['10'], PA), ('VSET', ['12'], PA),
                        ('~{CE}', ['9'], IN), ('OTG', ['6'], IN), ('NC', ['2'], NC)],
                  right=[('BTST', ['21'], PA), ('SW', ['19', '20'], PO), None, ('SYS', ['15', '16'], PO),
                         ('BAT', ['13', '14'], PA), None, None, ('STAT', ['5'], OC), None, ('~{PG}', ['7'], OC),
                         None, ('REGN', ['22'], PO), None, None, None, None, ('TS', ['11'], IN)],
                  bottom=[('GND', ['17', '18', '25'], PI)], desc='Standalone 3 A NVDC charger'),
    # HY2113 SOT-23-6 (DS-HY2113-V16 pin table)
    'HY2113': ic('HY2113', 5.08,
                 left=[('VDD', ['5'], PA), ('CS', ['2'], IN), ('NC', ['4'], NC)],
                 right=[('OC', ['3'], OUT), ('OD', ['1'], OUT)],
                 bottom=[('VSS', ['6'], PA)], desc='1-cell Li-ion protector'),
    # TPS61178 VQFN-HR-13 (SLVSDA7E pin functions)
    'TPS61178': ic('TPS61178', 8.89,
                   left=[('VIN', ['12'], PI), ('EN', ['11'], IN), None, ('FREQ/SYNC', ['1'], PA),
                         ('ILIMIT', ['3'], PA), ('COMP', ['4'], PA)],
                   right=[('SW', ['7'], PO), ('VOUT', ['8'], PO), ('DISDRV', ['9'], OUT), None, None, None, None,
                          ('FB', ['5'], IN)],
                   top=[('VCC', ['10'], PO), ('BST', ['13'], PA)],
                   bottom=[('PGND', ['6'], PI), ('AGND', ['2'], PI)], desc='20 V sync boost, load disconnect'),
    # TPS61088-Q1 VQFN-20 RHL (SLVSE52A pin functions); thermal pad 21 = PGND
    'TPS61088-Q1': ic('TPS61088-Q1', 8.89,
                      left=[('VIN', ['9'], PI), ('EN', ['2'], IN), None, ('MODE', ['13'], IN), ('SS', ['10'], PA),
                            ('ILIM', ['19'], PA), None, ('NC', ['11'], NC), ('NC', ['12'], NC)],
                      right=[('SW', ['4', '5', '6', '7'], PO), None, ('FSW', ['3'], PA), None, ('BOOT', ['8'], PA),
                             None, ('VOUT', ['14', '15', '16'], PO), None, None, ('FB', ['17'], IN),
                             ('COMP', ['18'], PA)],
                      top=[('VCC', ['1'], PO)],
                      bottom=[('PGND', ['21'], PI), ('AGND', ['20'], PI)], desc='10 A sync boost'),
    # TPS63802 VSON-10 DLA
    'TPS63802': ic('TPS63802', 7.62,
                   left=[('VIN', ['10'], PI), ('EN', ['1'], IN), ('PG', ['5'], OC), ('MODE', ['2'], IN)],
                   right=[('VOUT', ['6'], PO), None, None, ('FB', ['4'], IN)],
                   top=[('L1', ['9'], PA), ('L2', ['7'], PA)],
                   bottom=[('GND', ['8'], PI), ('AGND', ['3'], PI)], desc='2 A buck-boost', top_pitch=7.62),
}


def fet(base_text, name, D, G, S, desc=''):
    """Copy a Device:Q_NMOS / Q_PMOS symbol and renumber its D/G/S pins to the footprint's pad numbers; extra pads
    become hidden pins stacked on the same point."""
    t = base_text
    base = re.match(r'\(symbol "([^"]+)"', t).group(1)
    t = t.replace('(symbol "%s"' % base, '(symbol "%s"' % name, 1).replace('"%s_' % base, '"%s_' % name)
    for letter, nums in (('D', D), ('G', G), ('S', S)):
        m = re.search(r'(\t*)\(pin (\w+) (\w+)\s*\(at [^)]*\)\s*\(length [^)]*\)\s*\(name "%s".*?\(number "%s"(.*?)\n\1\)\n' % (letter, letter), t, re.S)
        blk = m.group(0)
        new = blk.replace('(number "%s"' % letter, '(number "%s"' % nums[0])
        for n in nums[1:]:
            extra = blk.replace('(number "%s"' % letter, '(number "%s"' % n)
            extra = re.sub(r'(\(length [^)]*\))', r'\1\n\t\t\t\t(hide yes)', extra, count=1)
            new += extra
        t = t.replace(blk, new)
    t = re.sub(r'\(property "Value" "[^"]*"', '(property "Value" "%s"' % name, t, count=1)
    t = re.sub(r'\(property "Description" "[^"]*"', '(property "Description" "%s"' % desc, t, count=1)
    return t


def library_text():
    return '(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "minipc_symbols")\n\t' + \
        '\n\t'.join(SYMBOLS.values()) + '\n)\n'


SYMBOLS['CSD13202Q2'] = fet(DEVICE.get('Q_NMOS'), 'CSD13202Q2', D=['1', '2', '5', '6', '8'], G=['3'], S=['4', '7'],
                            desc='12 V N-FET, TI DQK (KiCad Package_SON:Texas_DQK pads)')
SYMBOLS['CSD25404Q3'] = fet(DEVICE.get('Q_PMOS'), 'CSD25404Q3', D=['1', '2', '3'], G=['4'], S=['5'],
                            desc='-20 V P-FET, KiCad NexFET VSON-8 (source pins 5-8 merged into pad 5)')
SYMBOLS['2N7002'] = fet(DEVICE.get('Q_NMOS'), '2N7002', D=['3'], G=['1'], S=['2'], desc='SOT-23: 1 G, 2 S, 3 D')
