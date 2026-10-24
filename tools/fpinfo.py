"""List pads of .kicad_mod files: number, type, position, size (merges multi-line pad blocks)."""
import re, sys, collections
for path in sys.argv[1:]:
    t = open(path).read()
    pads = re.findall(r'\(pad\s+"([^"]*)"\s+(\w+)\s+(\w+)\s*\(at\s+([-\d.]+)\s+([-\d.]+)[^)]*\)\s*\(size\s+([\d.]+)\s+([\d.]+)\)', t)
    byn = collections.OrderedDict()
    for n, typ, shp, x, y, w, h in pads:
        byn.setdefault(n, []).append((typ, float(x), float(y), float(w), float(h)))
    print('==', path.split('/')[-1], 'courtyard' if 'CrtYd' in t else 'NO courtyard')
    for n, lst in byn.items():
        typ, x, y, w, h = max(lst, key=lambda p: p[3] * p[4])
        print('  %-6s x%-2d %-4s (%6.3f,%6.3f) %5.2fx%-5.2f' % (n or '""', len(lst), typ, x, y, w, h))
