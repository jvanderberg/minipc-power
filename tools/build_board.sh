#!/usr/bin/env bash
# Full board build: schematic netlist -> footprints/nets -> setup -> routes -> DRC (zones refilled, saved) -> summary.
set -e
cd "$(dirname "$0")/.."
S=${SCRATCH:-/tmp/minipc-build}; mkdir -p "$S"
# git diffs of the board hide zone fills (derived, and KiCad's refill is not deterministic); see tools/fills.py
git config diff.kicad_pcb.textconv "python3 tools/fills.py strip" 2>/dev/null || true
# snapshot the board being replaced: the generators reuse its ids (stable ids -> clean git diffs)
if [ -f hardware/minipc-power.kicad_pcb ]; then cp hardware/minipc-power.kicad_pcb "$S/previous.kicad_pcb"; export PREV_PCB="$S/previous.kicad_pcb"; fi
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
P=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
PY=${PY:-$HOME/.cache/kicad-skills/venv/bin/python}
# Refuse only if KiCad has THIS project open: a lock file here, or a KiCad process holding files in this folder.
# (Any KiCad process anywhere is not a reason: the user may be looking at another copy or another project.)
HW=$(cd hardware && pwd -P)
if ls hardware/*.lck hardware/~*.lck >/dev/null 2>&1; then echo "KiCad has the project open (lock file in hardware/)"; exit 1; fi
for pid in $(pgrep -f 'KiCad.app/Contents/MacOS/(kicad|pcbnew|eeschema)$' 2>/dev/null); do
  if lsof -p "$pid" 2>/dev/null | awk '{print $NF}' | grep -q "^$HW\(/\|$\)"; then echo "KiCad (pid $pid) has files open in hardware/"; exit 1; fi
done
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
# only the zone fills changed (KiCad's refill is not deterministic)? keep the previous file, so git stays clean
if [ -n "${PREV_PCB:-}" ] && ! cmp -s "$PREV_PCB" hardware/minipc-power.kicad_pcb && python3 tools/fills.py same "$PREV_PCB" hardware/minipc-power.kicad_pcb; then
  cp "$PREV_PCB" hardware/minipc-power.kicad_pcb; echo "board unchanged apart from zone fills: kept the previous file"
fi
# every unused / strapped pin needs a recorded datasheet decision (docs/pin-decisions.json)
if python3 ~/git/kicad-skills/skills/kicad-pcb-workflow/scripts/nc_audit.py $S/net.xml --notes docs/pin-decisions.json \
     --require-notes --md docs/pin-decisions.md > $S/nc_audit.txt; then tail -1 $S/nc_audit.txt
else tail -1 $S/nc_audit.txt; echo "pin decisions missing: see docs/pin-decisions.md (TODO rows)"; exit 1; fi
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
