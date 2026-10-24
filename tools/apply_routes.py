#!/usr/bin/env python3
"""Add the routes from tools/route_plan.py to hardware/minipc-power.kicad_pcb (after gen_board.py and
board_setup.py), through kicad-skills' kicad_sexpr layer. Usage: apply_routes.py <board.json from boarddump.py>"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import kskills  # noqa: F401  (kicad_sexpr on sys.path)
from kicad_sexpr import Board
from routing import Router
import route_plan

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(ROOT, 'hardware', 'minipc-power.kicad_pcb')
r = Router(sys.argv[1])
route_plan.build(r)
b = Board.load(PCB)
assert not b.items('segment') and not b.items('zone'), 'board already has routing: regenerate it first'
r.emit(b)
b.save()
print('routes: %d segments, %d vias, %d zones' % (len(r.tracks), len(r.vias), len(r.zones)))
for line in r.log:
    print('  ' + line)
