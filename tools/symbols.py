"""Redrawn IC symbols for minipc-power: pins grouped by function (inputs left, outputs right, supplies top,
ground bottom) and real pin types. Pin numbers match the JLCImport footprints, checked against each datasheet's pin
table. Duplicate pins (SW, SYS, BAT, VOUT, GND) are stacked on one connection point; the extra copies are hidden.
Built with kicad_sexpr's library-symbol builders (no s-expression text formatted here).
"""
from schgen import SymLib
from kicad_sexpr import Node, SymbolLibrary, lib_pin, lib_property, lib_rectangle, lib_symbol

DEVICE = SymLib('Device', '/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Device.kicad_sym')

L = 2.54  # pin length and pitch

# Datasheet link for each redrawn symbol: the manufacturer's page for the exact part where one is canonical (TI
# symlinks), else the LCSC page JLCImport put on the symbol this one replaces. library() refuses a symbol without one.
_TI = 'https://www.ti.com/lit/ds/symlink/%s.pdf'
DATASHEETS = {
    'CH224Q': 'https://www.lcsc.com/datasheet/C46061833.pdf', 'BQ25606': _TI % 'bq25606',
    'HY2113': 'https://www.lcsc.com/datasheet/C168772.pdf', 'TPS61178': _TI % 'tps61178',
    'TPS61088-Q1': _TI % 'tps61088-q1', 'TPS63802': _TI % 'tps63802',
    'CSD13202Q2': _TI % 'csd13202q2', 'CSD25404Q3': _TI % 'csd25404q3',
    '2N7002': 'https://www.lcsc.com/datasheet/C8545.pdf',
}


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
                pins.append(lib_pin(typ, round(x, 4), round(y, 4), rot, pname, n, length=L, hide=k > 0))
    y0 = half_h - L - (2 * L if top else 0)
    side(left, lambda i: (-half_w - L, y0 - i * L), 0)
    side(right, lambda i: (half_w + L, y0 - i * L), 180)
    # top/bottom pins right-aligned so the left half stays free for the reference and value text
    x0 = half_w - L - (len(top) - 1) * top_pitch
    side(top, lambda i: (x0 + i * top_pitch, half_h + L), 270)
    x0b = half_w - L - (len(bottom) - 1) * L
    side(bottom, lambda i: (x0b + i * L, -half_h - L), 90)
    props = [lib_property('Reference', ref, 0, half_h + 1.27), lib_property('Value', name, 0, -half_h - 1.27),
             lib_property('Footprint', '', hide=True), lib_property('Datasheet', DATASHEETS.get(name, ''), hide=True),
             lib_property('Description', desc, hide=True)]
    return lib_symbol(name, props, {(0, 1): [lib_rectangle(-half_w, half_h, half_w, -half_h)], (1, 1): pins})


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
    # TPS61088-Q1 VQFN-20 RHL (SLVSE52A pin functions); thermal pad 21 = PGND. NC 11/12 are passive: the pin table says
    # to connect them to the ground plane for heat
    'TPS61088-Q1': ic('TPS61088-Q1', 8.89,
                      left=[('VIN', ['9'], PI), ('EN', ['2'], IN), None, ('MODE', ['13'], IN), ('SS', ['10'], PA),
                            ('ILIM', ['19'], PA), None, ('NC', ['11'], PA), ('NC', ['12'], PA)],
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


def fet(base, name, D, G, S, desc=''):
    """Copy a Device:Q_NMOS / Q_PMOS symbol and renumber its D/G/S pins to the footprint's pad numbers; extra pads
    become hidden pins stacked on the same point."""
    sym = base.deepcopy()
    old = str(sym[1])
    sym[1] = name
    for sub in sym.nodes('symbol'):
        sub[1] = name + str(sub[1])[len(old):]
    for letter, nums in (('D', D), ('G', G), ('S', S)):
        hits = [(sub, p) for sub in sym.nodes('symbol') for p in sub.nodes('pin') if p.find('name')[1] == letter]
        assert len(hits) == 1, (name, letter)
        sub, pin = hits[0]
        pin.find('number')[1] = nums[0]
        pos = sub.index(pin)
        for k, n in enumerate(nums[1:], 1):
            extra = pin.deepcopy()
            extra.find('number')[1] = n
            extra.remove_all('hide')
            extra.insert(extra.index(extra.find('length')) + 1, Node('hide', True))
            sub.insert(pos + k, extra)
    for p in sym.nodes('property'):
        if p[1] == 'Value':
            p[2] = name
        elif p[1] == 'Description':
            p[2] = desc
        elif p[1] == 'Datasheet':
            p[2] = DATASHEETS.get(name, '')
    return sym


def library():
    lib = SymbolLibrary.new('minipc')
    lib.tree.set('generator', 'minipc_symbols')
    missing = sorted(set(SYMBOLS) - set(DATASHEETS))
    if missing:
        raise SystemExit('symbols without a datasheet link (add them to DATASHEETS): %s' % ', '.join(missing))
    for sym in SYMBOLS.values():
        lib.add(sym)
    return lib


SYMBOLS['CSD13202Q2'] = fet(DEVICE.get('Q_NMOS'), 'CSD13202Q2', D=['1', '2', '5', '6', '8'], G=['3'], S=['4', '7'],
                            desc='12 V N-FET, TI DQK (KiCad Package_SON:Texas_DQK pads)')
SYMBOLS['CSD25404Q3'] = fet(DEVICE.get('Q_PMOS'), 'CSD25404Q3', D=['1', '2', '3'], G=['4'], S=['5'],
                            desc='-20 V P-FET, KiCad NexFET VSON-8 (source pins 5-8 merged into pad 5)')
SYMBOLS['2N7002'] = fet(DEVICE.get('Q_NMOS'), '2N7002', D=['3'], G=['1'], S=['2'], desc='SOT-23: 1 G, 2 S, 3 D')
