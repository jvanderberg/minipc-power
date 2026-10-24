#!/usr/bin/env python3
"""Zone fills (filled_polygon) are derived data that KiCad recomputes on every refill, and its refill is not always
deterministic (the same board refills to one of two equally valid results). So that git shows only real changes:

  fills.py strip FILE          print FILE without filled_polygon blocks (git textconv for *.kicad_pcb diffs)
  fills.py same OLD NEW        exit 0 if OLD and NEW differ only inside filled_polygon blocks
"""
import re, sys

FILL = re.compile(r'\n(\t+)\(filled_polygon\n.*?\n\1\)', re.S)


def strip(text):
    return FILL.sub('', text)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'strip' and len(sys.argv) == 3:
        sys.stdout.write(strip(open(sys.argv[2], encoding='utf-8').read()))
    elif cmd == 'same' and len(sys.argv) == 4:
        a, b = (strip(open(p, encoding='utf-8').read()) for p in sys.argv[2:4])
        sys.exit(0 if a == b else 1)
    else:
        sys.exit(__doc__)
