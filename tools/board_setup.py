#!/usr/bin/env python3
"""Text pass on hardware/minipc-power.kicad_pcb / .kicad_pro after gen_board.py:
- JLC04161H-7628 stackup (values: kicad-skills jlcpcb-stackups.md, re-check on jlcpcb.com/impedance before ordering)
- hidden LCSC property on every footprint (from the schematic netlist)
- design rules and net classes in the project file (comfortable JLC values, not minimums)
Usage: python3 tools/board_setup.py <netlist.xml>
"""
import json, os, sys, uuid, xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))
from netspec import NETS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, 'hardware', 'minipc-power.kicad_pcb')
PRO = os.path.join(ROOT, 'hardware', 'minipc-power.kicad_pro')

STACKUP = '''		(stackup
			(layer "F.SilkS"
				(type "Top Silk Screen")
			)
			(layer "F.Paste"
				(type "Top Solder Paste")
			)
			(layer "F.Mask"
				(type "Top Solder Mask")
				(thickness 0.01)
				(material "LPI")
				(epsilon_r 3.8)
				(loss_tangent 0)
			)
			(layer "F.Cu"
				(type "copper")
				(thickness 0.035)
			)
			(layer "dielectric 1"
				(type "prepreg")
				(thickness 0.2104)
				(material "7628")
				(epsilon_r 4.4)
				(loss_tangent 0.02)
			)
			(layer "In1.Cu"
				(type "copper")
				(thickness 0.0152)
			)
			(layer "dielectric 2"
				(type "core")
				(thickness 1.065)
				(material "FR4")
				(epsilon_r 4.6)
				(loss_tangent 0.02)
			)
			(layer "In2.Cu"
				(type "copper")
				(thickness 0.0152)
			)
			(layer "dielectric 3"
				(type "prepreg")
				(thickness 0.2104)
				(material "7628")
				(epsilon_r 4.4)
				(loss_tangent 0.02)
			)
			(layer "B.Cu"
				(type "copper")
				(thickness 0.035)
			)
			(layer "B.Mask"
				(type "Bottom Solder Mask")
				(thickness 0.01)
				(material "LPI")
				(epsilon_r 3.8)
				(loss_tangent 0)
			)
			(layer "B.Paste"
				(type "Bottom Solder Paste")
			)
			(layer "B.SilkS"
				(type "Bottom Silk Screen")
			)
			(copper_finish "ENIG")
			(dielectric_constraints no)
		)
'''

POWER = ['GND', 'VBUS', 'VSYS', 'BAT', 'BATP', 'BATN', 'CELLN', 'MID', 'SW_CHG', 'PMID', 'SW12', 'VOUT12A', '+12V',
         'SW5', 'VOUT5A', '+5V', 'L1_33', 'L2_33', '+3V3']

root = ET.parse(sys.argv[1]).getroot()
lcsc = {}      # ref -> {field: value} for every schematic field the footprint must carry (parity checks them)
for c in root.find('components'):
    fields = {f.get('name'): (f.text or '') for f in (c.find('fields') or [])}
    fields = {k: v for k, v in fields.items() if k not in ('Reference', 'Value', 'Footprint')}
    if fields:
        lcsc[c.get('ref')] = fields
pin2net = {}
for n in root.find('nets'):
    for node in n.findall('node'):
        pin2net['%s.%s' % (node.get('ref'), node.get('pin'))] = n.get('name')

t = open(PCB).read()
if '(stackup' not in t:
    i = t.index('\t(setup\n') + len('\t(setup\n')
    t = t[:i] + STACKUP + t[i:]
# LCSC property inside each footprint, right after its Reference property block
out, pos, added = [], 0, 0
import re
for m in re.finditer(r'\n\t\(footprint "[^"]+"', t):
    pass
blocks = list(re.finditer(r'\t\t\(property "Reference" "([^"]+)"', t))
for m in reversed(blocks):
    ref = m.group(1)
    if ref not in lcsc:
        continue
    start = t.rfind('\n\t(footprint ', 0, m.start())
    end = t.find('\n\t(footprint ', m.start())
    seg = t[start:end if end > 0 else len(t)]
    prop = ''
    for k, v in lcsc[ref].items():
        if '(property "%s"' % k in seg:          # library already has the field (e.g. empty Description): set its value
            new_seg = re.sub(r'\(property "%s" "(?:\\.|[^"\\])*"' % re.escape(k),
                             lambda _m: '(property "%s" "%s"' % (k, v.replace('\\', '\\\\').replace('"', '\\"')), seg, count=1)
            if new_seg != seg:
                t = t.replace(seg, new_seg, 1)
                seg = new_seg
                added += 1
            continue
        prop += ('\t\t(property "%s" "%s"\n\t\t\t(at 0 0 0)\n\t\t\t(layer "F.Fab")\n\t\t\t(hide yes)\n\t\t\t(uuid "%s")\n'
                 '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1 1)\n\t\t\t\t\t(thickness 0.15)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n') % (
            k, v.replace('"', '\\"'), uuid.uuid4())
        added += 1
    t = t[:m.start()] + prop + t[m.start():]
# 3D models the KiCad library references but does not install -> JLCImport models (placement.MODEL_OVERRIDE).
# Done as text: pcbnew's FOOTPRINT.Models() returns copies, so assigning m_Filename there does not stick.
import placement
for fpname, (fn, off, rot) in placement.MODEL_OVERRIDE.items():
    pat = re.compile(r'\(model "[^"]*/%s\.(?:step|wrl)"\s*\(offset\s*\(xyz [^)]*\)\s*\)\s*\(scale\s*\(xyz [^)]*\)\s*\)'
                     r'\s*\(rotate\s*\(xyz [^)]*\)\s*\)' % re.escape(fpname))
    new = '(model "%s"\n\t\t\t(offset\n\t\t\t\t(xyz %s %s %s)\n\t\t\t)\n\t\t\t(scale\n\t\t\t\t(xyz 1 1 1)\n\t\t\t)\n' \
          '\t\t\t(rotate\n\t\t\t\t(xyz %s %s %s)\n\t\t\t)' % ((fn,) + tuple(off) + tuple(rot))
    t, n = pat.subn(lambda _m: new, t)
    assert n >= 1, 'model override did not match: ' + fpname
open(PCB, 'w').write(t)

pro = json.load(open(PRO))
ds = pro.setdefault('board', {}).setdefault('design_settings', {})
ds['rules'] = {
    'max_error': 0.005, 'min_clearance': 0.15, 'min_connection': 0.0, 'min_copper_edge_clearance': 0.3,
    'min_groove_width': 0.0, 'min_hole_clearance': 0.2, 'min_hole_to_hole': 0.25, 'min_microvia_diameter': 0.2,
    'min_microvia_drill': 0.1, 'min_resolved_spokes': 2, 'min_silk_clearance': 0.0, 'min_text_height': 0.8,
    'min_text_thickness': 0.12, 'min_through_hole_diameter': 0.2, 'min_track_width': 0.15,
    'min_via_annular_width': 0.1, 'min_via_diameter': 0.45, 'solder_mask_to_copper_clearance': 0.0,
    'use_height_for_length_calcs': True}
ds['track_widths'] = [0.0, 0.2, 0.3, 0.5, 0.8, 1.2, 2.0]
ds['via_dimensions'] = [{'diameter': 0.0, 'drill': 0.0}, {'diameter': 0.6, 'drill': 0.3}, {'diameter': 0.8, 'drill': 0.4}]
base = {'bus_width': 12, 'diff_pair_gap': 0.25, 'diff_pair_via_gap': 0.25, 'diff_pair_width': 0.2, 'line_style': 0,
        'microvia_diameter': 0.3, 'microvia_drill': 0.1, 'pcb_color': 'rgba(0, 0, 0, 0.000)',
        'schematic_color': 'rgba(0, 0, 0, 0.000)', 'tuning_profile': '', 'wire_width': 6}
ns = pro.setdefault('net_settings', {})
ns['classes'] = [dict(base, name='Default', priority=2147483647, clearance=0.15, track_width=0.2, via_diameter=0.6,
                      via_drill=0.3),
                 dict(base, name='Power', priority=0, clearance=0.2, track_width=0.8, via_diameter=0.6, via_drill=0.3)]
ns['meta'] = {'version': 5}
assign = {}
for n in POWER:
    k = pin2net.get(NETS[n][0])
    if k:
        assign[k] = 'Power'
ns['netclass_assignments'] = assign
ns['netclass_patterns'] = []
json.dump(pro, open(PRO, 'w'), indent=2)
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
