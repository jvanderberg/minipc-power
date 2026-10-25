#!/usr/bin/env python3
"""Setup pass on hardware/minipc-power.kicad_pcb / .kicad_pro after gen_board.py (through kicad_sexpr):
- JLC04161H-7628 stackup (values: kicad-skills jlcpcb-stackups.md, re-check on jlcpcb.com/impedance before ordering)
- the schematic's fields (LCSC, Datasheet, Description, ...) on every footprint, from the netlist
- design rules and net classes in the project file (comfortable JLC values, not minimums)
Usage: python3 tools/board_setup.py <netlist.xml>
"""
import os, sys, xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))
from netspec import NETS
import kskills  # noqa: F401  (kicad_sexpr on sys.path)
from kicad_sexpr import Board, Project, stackup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, 'hardware', 'minipc-power.kicad_pcb')
PRO = os.path.join(ROOT, 'hardware', 'minipc-power.kicad_pro')

# JLC04161H-7628 (kicad-skills jlcpcb-stackups.md): 35 um outer / 15.2 um inner copper, 7628 prepreg + FR4 core
STACKUP = stackup(copper_thickness=[0.035, 0.0152, 0.0152, 0.035],
                  dielectrics=[('prepreg', 0.2104, '7628', 4.4, 0.02), ('core', 1.065, 'FR4', 4.6, 0.02),
                               ('prepreg', 0.2104, '7628', 4.4, 0.02)])

POWER = ['GND', 'VBUS', 'VSYS', 'BAT', 'BATP', 'BATN', 'CELLN', 'MID', 'SW_CHG', 'PMID', 'SW12', 'VOUT12A', '+12V',
         'SW5', 'VOUT5A', '+5V', 'L1_33', 'L2_33', '+3V3']

root = ET.parse(sys.argv[1]).getroot()
missing = []   # BOM parts the schematic gave no datasheet
lcsc = {}      # ref -> {field: value} for every schematic field the footprint must carry (parity checks them)
for c in root.find('components'):
    fields = {f.get('name'): (f.text or '') for f in (c.find('fields') or [])}
    fields = {k: v for k, v in fields.items() if k not in ('Reference', 'Value', 'Footprint')}
    ds = (c.findtext('datasheet') or '').strip()
    if ds not in ('', '~'):
        fields['Datasheet'] = ds       # the netlist keeps it outside <fields>: copied here or it never reaches the board
    elif not any(pr.get('name') == 'exclude_from_bom' for pr in c.findall('property')):
        missing.append(c.get('ref'))
    if fields:
        lcsc[c.get('ref')] = fields
pin2net = {}
for n in root.find('nets'):
    for node in n.findall('node'):
        pin2net['%s.%s' % (node.get('ref'), node.get('pin'))] = n.get('name')

b = Board.load(PCB)
PREV = os.environ.get('PREV_PCB')
if PREV and os.path.exists(PREV):
    b.reuse_ids(PREV)                      # fields added below keep their committed ids
setup = b.tree.find('setup')
if setup.find('stackup') is None:
    b.set_stackup(STACKUP)
# schematic fields (LCSC, Description, ...) on each footprint: set the library's own field, else add a hidden one
added = 0
for f in b.footprints():
    for k, v in lcsc.get(f.ref, {}).items():
        f.set_field(k, v)
        added += 1
if missing:
    sys.exit('BOM parts without a datasheet link in the schematic: %s' % ', '.join(sorted(missing)))
# 3D models the KiCad library references but does not install -> JLCImport models (placement.MODEL_OVERRIDE).
# (pcbnew's FOOTPRINT.Models() returns copies, so assigning m_Filename there does not stick.)
import placement
for fpname, (fn, off, rot) in placement.MODEL_OVERRIDE.items():
    n = 0
    for f in b.footprints():
        for m in f.node.nodes('model'):
            p = str(m[1])
            if p.rsplit('/', 1)[-1] in (fpname + '.step', fpname + '.wrl'):
                m[1] = fn
                m.find('offset').set('xyz', *off)
                m.find('scale').set('xyz', 1, 1, 1)
                m.find('rotate').set('xyz', *rot)
                n += 1
    assert n >= 1, 'model override did not match: ' + fpname
b.save()

pro = Project.load(PRO)
pro.set_rules(max_error=0.005, min_clearance=0.15, min_connection=0.0, min_copper_edge_clearance=0.3,
              min_groove_width=0.0, min_hole_clearance=0.2, min_hole_to_hole=0.25, min_microvia_diameter=0.2,
              min_microvia_drill=0.1, min_resolved_spokes=2, min_silk_clearance=0.0, min_text_height=0.8,
              min_text_thickness=0.12, min_through_hole_diameter=0.2, min_track_width=0.15,
              min_via_annular_width=0.1, min_via_diameter=0.45, solder_mask_to_copper_clearance=0.0,
              use_height_for_length_calcs=True)
pro.set_track_widths([0.2, 0.3, 0.5, 0.8, 1.2, 2.0])
pro.set_via_sizes([[0.6, 0.3], [0.8, 0.4]])
pro.netclass('Default', priority=2147483647, clearance=0.15, track_width=0.2, via_diameter=0.6, via_drill=0.3)
pro.netclass('Power', priority=0, clearance=0.2, track_width=0.8, via_diameter=0.6, via_drill=0.3)
pro.clear_assignments()
assign = {}
for n in POWER:
    k = pin2net.get(NETS[n][0])
    if k:
        assign[k] = 'Power'
        pro.assign(k, 'Power')
pro.save()
open(os.path.join(ROOT, 'hardware', 'minipc-power.kicad_dru'), 'w').write('''(version 1)
# Fine-pitch footprints whose own pads sit closer than the 0.15-0.2 mm net-class clearance
# (KiCad NexFET VSON-8: 0.14 mm gate-source; CH224Q DFN-10 0.4 mm pitch: 0.176 mm). JLC 4-layer minimum is 0.09 mm.
(rule "fine pitch pads"
    (constraint clearance (min 0.12mm))
    (condition "A.Type == 'Pad' && B.Type == 'Pad' && (A.memberOfFootprint('Q4') || A.memberOfFootprint('Q5') || A.memberOfFootprint('U1'))"))
# Tracks escaping U1's 0.4 mm-pitch inner pins sit 0.15 mm from the neighbouring pads and tracks by construction
(rule "U1 escape"
    (constraint clearance (min 0.15mm))
    (condition "A.intersectsCourtyard('U1') && B.intersectsCourtyard('U1')"))
''')
print('stackup ok, fields added:', added, '| Power nets:', sorted(assign))
