#!/usr/bin/env python3
"""Build hardware/minipc-power.kicad_pcb from the schematic's netlist (KiCad has no CLI "update PCB from schematic").

Plain python3, through kicad-skills' kicad_sexpr layer (no pcbnew, no hand-formatted s-expressions):
  python3 tools/gen_board.py <netlist.xml>
Footprints come from the libraries named in the schematic; each gets its reference, value, the symbol link (path),
and pad nets. Positions come from tools/placement.py (unplaced parts are staged beside the board). Afterwards run
tools/board_setup.py for the stackup, design rules, net classes and schematic fields.
"""
import os, sys, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import placement
import kskills  # noqa: F401  (kicad_sexpr on sys.path)
from kicad_sexpr import Board, board_net_name

HW = os.path.join(ROOT, 'hardware')
SYS_FP = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
LIBS = {'JLCImport': os.path.join(HW, 'JLCImport.pretty')}

root = ET.parse(sys.argv[1]).getroot()
comps = []
for c in root.find('components'):
    fp = c.findtext('footprint') or ''
    if fp:
        comps.append(dict(ref=c.get('ref'), value=c.findtext('value') or '', fp=fp, tstamp=c.findtext('tstamps') or ''))
pins = {}
for net in root.find('nets'):
    for n in net.findall('node'):
        pins.setdefault(n.get('ref'), {})[n.get('pin')] = board_net_name(net.get('name'))

b = Board.new(copper_layers=4)
ox, oy = placement.ORIGIN
stage_x, stage_y = ox + placement.BOARD[0] + 15, oy


def refnum(c):
    return (c['ref'][0], int(''.join(ch for ch in c['ref'] if ch.isdigit()) or 0))


for i, c in enumerate(sorted(comps, key=refnum)):
    lib, name = c['fp'].split(':', 1)
    path = os.path.join(LIBS.get(lib, os.path.join(SYS_FP, lib + '.pretty')), name + '.kicad_mod')
    pl = placement.PLACE.get(c['ref'])
    if pl:
        at, rot = (ox + pl[0], oy + pl[1]), (pl[2] if len(pl) > 2 else 0)
    else:
        col, row = divmod(i, 12)
        at, rot = (stage_x + col * 10, stage_y + row * 8), 0
    f = b.add_footprint(path, c['fp'], c['ref'], c['value'], at, rot,
                        path='/' + c['tstamp'] if c['tstamp'] else None, pad_nets=pins.get(c['ref'], {}))
    # component references: off the silkscreen (dense assembled board), kept on F.Fab for the assembly drawing
    f.set_field('Reference', c['ref'], hide=True)
    for t in f.node.nodes('fp_text'):
        if str(t[2]) == '${REFERENCE}' and str(t.get('layer')) == 'F.Fab':
            t.remove_all('hide')

# solder-pad labels on both silkscreens (wires may be soldered from either side)
for ref, (text, dx, dy, *rot) in placement.PAD_LABELS.items():
    x, y = b.footprint(ref).at
    for layer in ('F.SilkS', 'B.SilkS'):
        b.gr_text(text, (x + dx, y + dy), layer, size=1.0, thickness=0.15, angle=rot[0] if rot else 0)
for text, x, y in placement.SILK_NOTES:
    for layer in ('F.SilkS', 'B.SilkS'):
        b.gr_text(text, (ox + x, oy + y), layer, size=1.0, thickness=0.15)

# board outline
w, h = placement.BOARD
b.outline_rect(ox, oy, w, h, corner_radius=placement.CORNER_R, width=0.1)

out = os.path.join(HW, 'minipc-power.kicad_pcb')
b.save(out)
print('wrote', out, len(comps), 'footprints,', len(b.nets()), 'nets,', len(placement.PLACE), 'placed')
