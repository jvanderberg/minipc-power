#!/usr/bin/env bash
# Regenerate the board from placement.py and list courtyard overlaps / pad shorts (fast placement loop).
set -e
cd "$(dirname "$0")/.."
S=${SCRATCH:-/tmp}; K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
P=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
$K sch export netlist --format kicadxml -o $S/net.xml hardware/minipc-power.kicad_sch >/dev/null
$P tools/gen_board.py $S/net.xml 2>&1 | grep -v "traits\|wxApp" | tail -1
python3 tools/board_setup.py $S/net.xml >/dev/null
$K pcb drc --format json -o $S/drc_place.json hardware/minipc-power.kicad_pcb >/dev/null 2>&1 || true
rm -f "hardware/~minipc-power.kicad_pcb.lck"
python3 - "$S/drc_place.json" <<'P'
import json, sys, collections
d = json.load(open(sys.argv[1]))
c = collections.Counter(v['type'] for v in d['violations'])
print({k: v for k, v in c.items() if not k.startswith('silk')})
for v in d['violations']:
    if v['type'] in ('courtyards_overlap', 'pth_inside_courtyard', 'shorting_items', 'clearance', 'copper_edge_clearance',
                     'npth_inside_courtyard', 'hole_clearance'):
        print('  %-20s %s' % (v['type'], ' | '.join(i['description'] for i in v['items'])))
P
