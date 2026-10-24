#!/usr/bin/env python3
"""Insert the routes from tools/route_plan.py into hardware/minipc-power.kicad_pcb (text edit, after gen_board.py and
board_setup.py). Usage: apply_routes.py <board.json from boarddump.py>"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from routing import Router
import route_plan

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, 'hardware', 'minipc-power.kicad_pcb')
r = Router(sys.argv[1])
route_plan.build(r)
t = open(PCB).read()
assert '\n\t(segment\n' not in t and '\n\t(zone\n' not in t, 'board already has routing: regenerate it first'
i = t.rstrip().rfind(')')
t = t[:i] + r.sexpr() + t[i:]
open(PCB, 'w').write(t)
print('routes: %d segments, %d vias, %d zones' % (len(r.tracks), len(r.vias), len(r.zones)))
for line in r.log:
    print('  ' + line)
