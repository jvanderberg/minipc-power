#!/usr/bin/env python3
"""Build hardware/minipc-power.kicad_pcb from the schematic's netlist (KiCad has no CLI "update PCB from schematic").

Run with KiCad's bundled python (it has pcbnew):
  $KICAD_PYTHON tools/gen_board.py <netlist.xml>
Footprints come from the libraries named in the schematic; each gets its reference, value, the symbol link (path),
and pad nets. Positions come from tools/placement.py (unplaced parts are staged beside the board). Afterwards run
tools/board_setup.py (plain python) for the stackup, design rules, net classes and LCSC fields.
"""
import os, sys, xml.etree.ElementTree as ET
import pcbnew

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import placement

HW = os.path.join(ROOT, 'hardware')
SYS_FP = '/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
LIBS = {'JLCImport': os.path.join(HW, 'JLCImport.pretty')}
MM = pcbnew.FromMM

root = ET.parse(sys.argv[1]).getroot()
comps = []
for c in root.find('components'):
    ref = c.get('ref')
    fp = c.findtext('footprint') or ''
    if not fp:
        continue
    fields = {f.get('name'): (f.text or '') for f in (c.find('fields') or [])}
    comps.append(dict(ref=ref, value=c.findtext('value') or '', fp=fp, tstamp=c.findtext('tstamps') or '',
                      lcsc=fields.get('LCSC', '')))
pins = {}
for net in root.find('nets'):
    for n in net.findall('node'):
        pins[(n.get('ref'), n.get('pin'))] = net.get('name')

b = pcbnew.CreateEmptyBoard()
b.SetCopperLayerCount(4)
netinfo = {}


def net(name):
    if name.startswith(('Net-(', 'unconnected-(')):
        name = name.replace('/', '{slash}')       # KiCad stores '/' in auto net names as {slash} (file-format.md)
    if name not in netinfo:
        ni = pcbnew.NETINFO_ITEM(b, name)
        b.Add(ni)
        netinfo[name] = ni
    return netinfo[name]


ox, oy = placement.ORIGIN
stage_x, stage_y = ox + placement.BOARD[0] + 15, oy
for i, c in enumerate(sorted(comps, key=lambda c: (c['ref'][0], int(''.join(ch for ch in c['ref'] if ch.isdigit()) or 0)))):
    lib, name = c['fp'].split(':', 1)
    path = LIBS.get(lib, os.path.join(SYS_FP, lib + '.pretty'))
    f = pcbnew.Cast_to_FOOTPRINT(pcbnew.FootprintLoad(path, name).Duplicate(False))
    f.SetFPID(pcbnew.LIB_ID(lib, name))
    f.SetReference(c['ref'])
    f.SetValue(c['value'])
    if c['tstamp']:
        f.SetPath(pcbnew.KIID_PATH('/' + c['tstamp']))
    b.Add(f)
    pl = placement.PLACE.get(c['ref'])
    if pl:
        x, y, rot = pl[0], pl[1], pl[2] if len(pl) > 2 else 0
        f.SetPosition(pcbnew.VECTOR2I(MM(ox + x), MM(oy + y)))
        f.SetOrientationDegrees(rot)
    else:
        col, row = divmod(i, 12)
        f.SetPosition(pcbnew.VECTOR2I(MM(stage_x + col * 10), MM(stage_y + row * 8)))
    for p in f.Pads():
        n = pins.get((c['ref'], p.GetNumber()))
        if n:
            p.SetNet(net(n))

# board outline
w, h = placement.BOARD
r = placement.CORNER_R
seg = []
pts = [(ox + r, oy), (ox + w - r, oy), (ox + w, oy + r), (ox + w, oy + h - r), (ox + w - r, oy + h), (ox + r, oy + h),
       (ox, oy + h - r), (ox, oy + r)]
for a, c2 in ((0, 1), (2, 3), (4, 5), (6, 7)):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I(MM(pts[a][0]), MM(pts[a][1])))
    s.SetEnd(pcbnew.VECTOR2I(MM(pts[c2][0]), MM(pts[c2][1])))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); b.Add(s)
for cx, cy, sa in ((ox + w - r, oy + r, 270), (ox + w - r, oy + h - r, 0), (ox + r, oy + h - r, 90), (ox + r, oy + r, 180)):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(pcbnew.VECTOR2I(MM(cx), MM(cy)))
    import math
    s.SetStart(pcbnew.VECTOR2I(MM(cx + r * math.cos(math.radians(sa))), MM(cy + r * math.sin(math.radians(sa)))))
    s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1)); b.Add(s)

out = os.path.join(HW, 'minipc-power.kicad_pcb')
pcbnew.SaveBoard(out, b)
print('wrote', out, len(comps), 'footprints,', len(netinfo), 'nets,', len(placement.PLACE), 'placed')
