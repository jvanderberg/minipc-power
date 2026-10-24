#!/usr/bin/env python3
"""Add an F.CrtYd rectangle to .kicad_mod files that have none (JLCImport footprints ship without courtyards).

Courtyard = bounding box of pads and body graphics (F.Fab / F.SilkS lines, rects, circles, arcs) + margin, rounded
outward to 0.01 mm. Usage: add_courtyard.py [--margin 0.25] file.kicad_mod ...
"""
import argparse, math, re, uuid

ap = argparse.ArgumentParser()
ap.add_argument('files', nargs='+')
ap.add_argument('--margin', type=float, default=0.25)
a = ap.parse_args()

for path in a.files:
    t = open(path).read()
    if 'F.CrtYd' in t:
        print('skip (has courtyard):', path)
        continue
    xs, ys = [], []
    for m in re.finditer(r'\(pad\s+"[^"]*"\s+\w+\s+\w+\s*\(at\s+([-\d.]+)\s+([-\d.]+)(?:\s+([-\d.]+))?\)\s*\(size\s+([\d.]+)\s+([\d.]+)\)', t):
        x, y, rot, w, h = float(m.group(1)), float(m.group(2)), float(m.group(3) or 0), float(m.group(4)), float(m.group(5))
        r = math.radians(rot)
        hw = abs(w / 2 * math.cos(r)) + abs(h / 2 * math.sin(r))
        hh = abs(w / 2 * math.sin(r)) + abs(h / 2 * math.cos(r))
        xs += [x - hw, x + hw]; ys += [y - hh, y + hh]
    for m in re.finditer(r'\(fp_(?:line|rect|arc|circle|poly)(.*?)\(layer "F\.(?:Fab|SilkS)"\)', t, re.S):
        for xm, ym in re.findall(r'\((?:start|end|mid|center|xy)\s+([-\d.]+)\s+([-\d.]+)\)', m.group(1)):
            xs.append(float(xm)); ys.append(float(ym))
    if not xs:
        print('no geometry:', path)
        continue
    x0, x1 = math.floor((min(xs) - a.margin) * 100) / 100, math.ceil((max(xs) + a.margin) * 100) / 100
    y0, y1 = math.floor((min(ys) - a.margin) * 100) / 100, math.ceil((max(ys) + a.margin) * 100) / 100
    rect = ('\t(fp_rect\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type solid)\n\t\t)\n'
            '\t\t(fill no)\n\t\t(layer "F.CrtYd")\n\t\t(uuid "%s")\n\t)\n') % (x0, y0, x1, y1, uuid.uuid4())
    m = re.search(r'\n[ \t]*\(pad ', t)      # tab-indented (KiCad) or space-indented (JLCImport) files
    assert m, path
    i = m.start()
    t = t[:i + 1] + rect + t[i + 1:]
    open(path, 'w').write(t)
    print('courtyard %6.2f x %-6.2f %s' % (x1 - x0, y1 - y0, path.split('/')[-1]))
