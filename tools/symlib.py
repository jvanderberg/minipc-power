"""Tiny s-expression reader for KiCad symbol libraries: list symbols and their pins."""
import re

def tokenize(s):
    return re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+', s)

def parse(s):
    toks = tokenize(s); pos = 0
    def rd():
        nonlocal pos
        t = toks[pos]; pos += 1
        if t == '(':
            lst = []
            while toks[pos] != ')':
                lst.append(rd())
            pos += 1
            return lst
        return t[1:-1].replace('\\"', '"') if t.startswith('"') else t
    out = []
    while pos < len(toks):
        out.append(rd())
    return out

def find(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]

def symbols(path):
    root = parse(open(path).read())[0]
    return {s[1]: s for s in find(root, 'symbol')}

def pins(sym):
    res = []
    def walk(n):
        for c in n:
            if isinstance(c, list):
                if c and c[0] == 'pin':
                    at = find(c, 'at')[0]
                    name = find(c, 'name')[0][1]; num = find(c, 'number')[0][1]
                    length = float(find(c, 'length')[0][1])
                    res.append(dict(type=c[1], name=name, num=num, x=float(at[1]), y=float(at[2]),
                                    rot=float(at[3]) if len(at) > 3 else 0.0, length=length))
                else:
                    walk(c)
    walk(sym)
    return res

if __name__ == '__main__':
    import sys
    lib = symbols(sys.argv[1])
    for name in sys.argv[2:] or lib:
        print('==', name)
        for p in sorted(pins(lib[name]), key=lambda p: int(p['num']) if p['num'].isdigit() else 999):
            print('  %-4s %-12s %-14s (%6.2f,%6.2f) r%3d' % (p['num'], p['name'], p['type'], p['x'], p['y'], p['rot']))
