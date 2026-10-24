#!/usr/bin/env bash
# Full board build: schematic netlist -> footprints/nets -> setup -> routes -> DRC (zones refilled, saved) -> summary.
set -e
cd "$(dirname "$0")/.."
S=${SCRATCH:-/tmp/minipc-build}; mkdir -p "$S"
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
P=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
PY=${PY:-$HOME/.cache/kicad-skills/venv/bin/python}
bash ~/git/kicad-skills/skills/kicad-pcb-workflow/scripts/kicad_open.sh hardware >/dev/null || { echo "KiCad has the project open"; exit 1; }
$K sch export netlist --format kicadxml -o $S/net.xml hardware/minipc-power.kicad_sch >/dev/null
$P tools/gen_board.py $S/net.xml 2>&1 | grep -v "traits\|wxApp" | tail -1
python3 tools/board_setup.py $S/net.xml >/dev/null
$P ~/git/kicad-skills/skills/kicad-board-review/scripts/boarddump.py hardware/minipc-power.kicad_pcb $S/pack0 2>&1 | grep -v "traits\|wxApp" >/dev/null
$PY tools/apply_routes.py $S/pack0/board.json
python3 ~/git/kicad-skills/skills/kicad-pcb-workflow/scripts/sexp.py check hardware/minipc-power.kicad_pcb
for pass in 1 2; do
  $K pcb drc --refill-zones --save-board --schematic-parity --format json -o $S/drc.json hardware/minipc-power.kicad_pcb >/dev/null 2>&1 || true
done
rm -f "hardware/~minipc-power.kicad_pcb.lck"
python3 - "$S/drc.json" <<'P'
import json, sys, collections
d = json.load(open(sys.argv[1]))
# The only accepted warning: J1's own outline crosses the board edge (the USB-C receptacle overhangs it by design).
# Everything else is reported; silk is not filtered (a blanket silk filter once hid labels printed over footprints).
def accepted(v):
    return v['type'] == 'silk_edge_clearance' and any(i['description'].startswith('Segment of J1 ') for i in v['items'])
viol = [v for v in d['violations'] if not accepted(v)]
c = collections.Counter(v['type'] for v in viol)
print('violations:', dict(sorted(c.items())))
un = collections.Counter()
for v in d.get('unconnected_items', []):
    n = v['items'][0]['description'].split('[')[1].split(']')[0] if '[' in v['items'][0]['description'] else '?'
    un[n] += 1
print('unconnected: %d  %s' % (len(d.get('unconnected_items', [])), dict(un.most_common(40))))
print('parity: %d' % len(d.get('schematic_parity', [])))
for v in viol:
    if v['type'].startswith('silk') or v['type'] in ('clearance', 'shorting_items', 'tracks_crossing', 'hole_clearance', 'copper_edge_clearance', 'courtyards_overlap', 'via_dangling', 'track_dangling'):
        print('  %-18s %s' % (v['type'], ' | '.join(i['description'] for i in v['items'])))
P
