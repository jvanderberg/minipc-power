"""Minimal KiCad 10 schematic writer for generated, wire-drawn schematics.

Coordinates are millimetres, y pointing down (KiCad sheet coordinates). Keep everything on the 1.27 mm grid.
Usage: build a Sch, place parts (returns Part objects whose .p(pin) gives the pin's connection point), draw wires
between points, add power symbols / labels, then write(). Junctions are added automatically wherever three or more
connection ends meet, or a wire end lands on the interior of another wire.
"""
import math, re, uuid

G = 1.27


def snap(v):
    return round(round(v / G) * G, 4)


def uid():
    return str(uuid.uuid4())


def kstr(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'


# ---------------------------------------------------------------- symbol libraries

def _blocks(text, head):
    """Yield (name, start, end) for top-level '(symbol "name"' blocks in a .kicad_sym text."""
    i = 0
    depth = 0
    n = len(text)
    starts = []
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            if c == '\\':
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == '(':
            if depth == 1 and text.startswith(head, i):
                starts.append(i)
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 1 and starts and starts[-1] is not None:
                s = starts[-1]
                name = re.match(r'\(symbol "([^"]+)"', text[s:]).group(1)
                yield name, s, i + 1
                starts[-1] = None
        i += 1


class SymLib:
    def __init__(self, nickname, path=None, text=None):
        self.nick = nickname
        text = text if text is not None else open(path).read()
        self.raw = {name: text[s:e] for name, s, e in _blocks(text, '(symbol "')}

    def get(self, name):
        return self.raw[name]


def pin_list(sym_text):
    """Pins of a symbol block: list of dict(num, name, type, x, y, rot) in symbol coordinates (y up)."""
    out = []
    for m in re.finditer(r'\(pin (\w+) \w+\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)(.*?)\(name "([^"]*)"(.*?)\(number "([^"]*)"',
                         sym_text, re.S):
        out.append(dict(type=m.group(1), x=float(m.group(2)), y=float(m.group(3)), rot=float(m.group(4) or 0),
                        name=m.group(6), num=m.group(8)))
    return out


def embed(lib_id, sym_text):
    """Rename a library symbol block for the schematic's lib_symbols section."""
    name = re.match(r'\(symbol "([^"]+)"', sym_text).group(1)
    return sym_text.replace('(symbol "%s"' % name, '(symbol "%s"' % lib_id, 1)


# ---------------------------------------------------------------- schematic

class Part:
    def __init__(self, sch, lib_id, ref, value, x, y, rot, pins, fields, footprint, in_bom, on_board, dnp, mirror=None):
        self.mirror = mirror
        self.sch, self.lib_id, self.ref, self.value = sch, lib_id, ref, value
        self.x, self.y, self.rot = snap(x), snap(y), rot
        self.pins = pins
        self.fields = fields
        self.footprint = footprint
        self.in_bom, self.on_board, self.dnp = in_bom, on_board, dnp
        self.uuid = uid()

    def p(self, key):
        """Connection point of a pin, by number or (unique) name."""
        cands = [q for q in self.pins if q['num'] == str(key)] or [q for q in self.pins if q['name'] == str(key)]
        if not cands:
            raise KeyError('%s has no pin %s' % (self.ref, key))
        q = cands[0]
        vx, vy = q['x'], -q['y']
        a = math.radians(self.rot)
        x = vx * math.cos(a) + vy * math.sin(a)
        y = -vx * math.sin(a) + vy * math.cos(a)
        if self.mirror == 'x':
            y = -y
        elif self.mirror == 'y':
            x = -x
        return (snap(self.x + x), snap(self.y + y))


class Sch:
    def __init__(self, project, paper='A2', title='', rev='', date=''):
        self.project = project
        self.paper, self.title, self.rev, self.date = paper, title, rev, date
        self.uuid = uid()
        self.libs = {}
        self.used = {}
        self.parts = []
        self.wires = []
        self.labels = []
        self.noconnects = []
        self.texts = []
        self.extra_junctions = []
        self.pwr_n = 0

    def lib(self, nickname, path=None, text=None):
        self.libs[nickname] = SymLib(nickname, path, text)

    def symtext(self, lib_id):
        nick, name = lib_id.split(':', 1)
        return self.libs[nick].get(name)

    def add(self, lib_id, ref, value, x, y, rot=0, footprint='', lcsc='', fields=None, in_bom=True, on_board=True,
            dnp=False, mirror=None):
        t = self.symtext(lib_id)
        self.used[lib_id] = t
        f = dict(fields or {})
        if lcsc:
            f['LCSC'] = lcsc
        p = Part(self, lib_id, ref, value, x, y, rot, pin_list(t), f, footprint, in_bom, on_board, dnp, mirror)
        self.parts.append(p)
        return p

    def power(self, net, x, y, rot=0, lib_id=None):
        """Power symbol at (x, y): GND points down by default, others point up."""
        if lib_id is None:
            lib_id = 'power:GND' if net == 'GND' else 'power:VCC'
        self.pwr_n += 1
        return self.add(lib_id, '#PWR%03d' % self.pwr_n, net, x, y, rot, in_bom=False, on_board=False)

    def wire(self, *pts):
        pts = [(snap(a), snap(b)) for a, b in pts]
        for a, b in zip(pts, pts[1:]):
            if a != b:
                assert a[0] == b[0] or a[1] == b[1], 'non-orthogonal wire %s -> %s' % (a, b)
                self.wires.append((a, b))

    def hv(self, a, b):
        """L-shaped wire: horizontal first, then vertical."""
        self.wire(a, (b[0], a[1]), b)

    def vh(self, a, b):
        """L-shaped wire: vertical first, then horizontal."""
        self.wire(a, (a[0], b[1]), b)

    def label(self, name, x, y, rot=0, kind='label', shape='passive'):
        self.labels.append((kind, name, snap(x), snap(y), rot, shape))

    def nc(self, pt):
        self.noconnects.append((snap(pt[0]), snap(pt[1])))

    def text(self, s, x, y, size=1.27, bold=False):
        self.texts.append((s, snap(x), snap(y), size, bold))

    # ------------------------------------------------------------ junctions

    def _junctions(self):
        ends = {}
        def bump(pt, k=1):
            ends[pt] = ends.get(pt, 0) + k
        for a, b in self.wires:
            bump(a); bump(b)
        pin_pts = set()
        for p in self.parts:
            for q in p.pins:
                pin_pts.add(p.p(q['num']))
        for pt in list(ends):
            if pt in pin_pts:
                bump(pt)
        js = set(pt for pt, n in ends.items() if n >= 3)
        for pt in list(ends) + list(pin_pts):
            for a, b in self.wires:
                if pt in (a, b):
                    continue
                if a[0] == b[0] == pt[0] and min(a[1], b[1]) < pt[1] < max(a[1], b[1]):
                    js.add(pt) if pt in ends else None
                elif a[1] == b[1] == pt[1] and min(a[0], b[0]) < pt[0] < max(a[0], b[0]):
                    js.add(pt) if pt in ends else None
        return sorted(js | set(self.extra_junctions))

    def pin_on_wire_interior(self):
        """Pins that sit on the interior of a wire (they connect to it - usually a mistake unless intended)."""
        bad = []
        for p in self.parts:
            for q in p.pins:
                pt = p.p(q['num'])
                for a, b in self.wires:
                    if pt in (a, b):
                        continue
                    if (a[0] == b[0] == pt[0] and min(a[1], b[1]) < pt[1] < max(a[1], b[1])) or \
                       (a[1] == b[1] == pt[1] and min(a[0], b[0]) < pt[0] < max(a[0], b[0])):
                        bad.append((p.ref, q['num'], pt))
        return bad

    # ------------------------------------------------------------ output

    def _sym_inst(self, p):
        props = [('Reference', p.ref, False), ('Value', p.value, False), ('Footprint', p.footprint, True),
                 ('Datasheet', p.fields.get('Datasheet', ''), True)]
        for k, v in p.fields.items():
            if k != 'Datasheet' and not k.startswith('_') and k not in p.fields.get('_visible', []):
                props.append((k, v, True))
        hide_ref = p.ref.startswith('#')
        out = ['\t(symbol\n\t\t(lib_id %s)\n\t\t(at %s %s %s)\n%s\t\t(unit 1)\n\t\t(exclude_from_sim no)\n'
               '\t\t(in_bom %s)\n\t\t(on_board %s)\n\t\t(dnp %s)\n\t\t(uuid "%s")\n' %
               (kstr(p.lib_id), p.x, p.y, p.rot, '\t\t(mirror %s)\n' % p.mirror if p.mirror else '', 'yes' if p.in_bom else 'no', 'yes' if p.on_board else 'no',
                'yes' if p.dnp else 'no', p.uuid)]
        rx, ry, vx, vy, ang, just = self._field_spots(p)
        if '_ref_at' in p.fields:
            rx, ry = p.fields['_ref_at']
        if '_val_at' in p.fields:
            vx, vy = p.fields['_val_at']
        for k, v, hidden in props:
            if k.startswith('_'):
                continue
            if k == 'Reference':
                at = (rx, ry)
                hid = hide_ref
            elif k == 'Value':
                at = (vx, vy)
                hid = p.fields.get('_hide_value', p.lib_id == 'power:GND')
            else:
                at = (p.x, p.y)
                hid = True
            just = p.fields.get('_just', just)
            out.append('\t\t(property %s %s\n\t\t\t(at %s %s %s)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n'
                       '\t\t\t\t)%s%s\n\t\t\t)\n\t\t)\n' % (kstr(k), kstr(v), snap(at[0]), snap(at[1]), ang,
                                                        '' if just == 'center' else '\n\t\t\t\t(justify %s)' % just,
                                                        '\n\t\t\t\t(hide yes)' if hid else ''))
        for i, k in enumerate(p.fields.get('_visible', [])):     # extra visible fields stacked under the value
            out.append('\t\t(property %s %s\n\t\t\t(at %s %s %s)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n'
                       '\t\t\t\t)%s\n\t\t\t)\n\t\t)\n' % (kstr(k), kstr(p.fields[k]), snap(vx), snap(vy + 2.54 * (i + 1)), ang,
                                                        '' if just == 'center' else '\n\t\t\t\t(justify %s)' % just))
        for q in p.pins:
            out.append('\t\t(pin %s\n\t\t\t(uuid "%s")\n\t\t)\n' % (kstr(q['num']), uid()))
        out.append('\t\t(instances\n\t\t\t(project %s\n\t\t\t\t(path "/%s"\n\t\t\t\t\t(reference %s)\n'
                   '\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n' % (kstr(self.project), self.uuid, kstr(p.ref)))
        return ''.join(out)

    def _split_wires(self):
        """Split wires at every pin point and wire end lying on their interior, so T-taps are real joints."""
        pts = set()
        for a, b in self.wires:
            pts.add(a); pts.add(b)
        for p in self.parts:
            for q in p.pins:
                pts.add(p.p(q['num']))
        out = []
        for a, b in self.wires:
            cuts = [pt for pt in pts if pt not in (a, b) and (
                (a[0] == b[0] == pt[0] and min(a[1], b[1]) < pt[1] < max(a[1], b[1])) or
                (a[1] == b[1] == pt[1] and min(a[0], b[0]) < pt[0] < max(a[0], b[0])))]
            seq = sorted([a, b] + cuts, key=lambda q: (q[0] - a[0]) ** 2 + (q[1] - a[1]) ** 2)
            out += [(u, v) for u, v in zip(seq, seq[1:]) if u != v]
        self.wires = out

    def _field_spots(self, p):
        """Default (ref x, y, value x, y, angle, justify) for a placed part."""
        n = len({q['num'] for q in p.pins})
        if p.ref.startswith('#'):                       # power symbols: text beyond the symbol
            if p.rot == 180:
                return p.x, p.y + 5.08, p.x, p.y + 5.08, 0, 'center'
            return p.x, p.y - 3.81, p.x, p.y - 3.81, 0, 'center'
        if n == 2 or p.lib_id in ('Connector:TestPoint',):
            if p.rot in (90, 270):
                return p.x, p.y - 2.54, p.x, p.y + 2.54, 90, 'center'
            if p.fields.get('_visible'):
                return p.x + 2.54, p.y - 2.54, p.x + 2.54, p.y, 0, 'left'
            return p.x + 2.54, p.y - 1.27, p.x + 2.54, p.y + 1.27, 0, 'left'
        m = re.search(r'\(rectangle\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)', self.symtext(p.lib_id))
        if m and p.rot == 0 and not p.mirror:
            x1, y1, x2, y2 = (float(v) for v in m.groups())
            left, top, bot = p.x + min(x1, x2), p.y - max(y1, y2), p.y - min(y1, y2)
            return left, top - 1.27, left, bot + 2.54, 0, 'left'
        return p.x + 3.81, p.y - 3.81, p.x + 3.81, p.y + 3.81, 90 if p.rot in (90, 270) else 0, 'left'

    def write(self, path):
        self._split_wires()
        o = ['(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n',
             '\t(uuid "%s")\n\t(paper "%s")\n' % (self.uuid, self.paper),
             '\t(title_block\n\t\t(title %s)\n\t\t(date %s)\n\t\t(rev %s)\n\t)\n' % (kstr(self.title), kstr(self.date),
                                                                                kstr(self.rev)),
             '\t(lib_symbols\n']
        for lib_id, t in sorted(self.used.items()):
            o.append('\t\t' + embed(lib_id, t).replace('\n', '\n\t\t').rstrip('\t') + '\n')
        o.append('\t)\n')
        for pt in self._junctions():
            o.append('\t(junction\n\t\t(at %s %s)\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "%s")\n\t)\n' %
                     (pt[0], pt[1], uid()))
        for pt in self.noconnects:
            o.append('\t(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)\n' % (pt[0], pt[1], uid()))
        for a, b in self.wires:
            o.append('\t(wire\n\t\t(pts\n\t\t\t(xy %s %s) (xy %s %s)\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n'
                     '\t\t\t(type default)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (a[0], a[1], b[0], b[1], uid()))
        for kind, name, x, y, rot, shape in self.labels:
            just = 'left' if rot in (0, 90) else 'right'
            if kind == 'label':
                o.append('\t(label %s\n\t\t(at %s %s %s)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
                         '\t\t\t(justify %s bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (kstr(name), x, y, rot, just, uid()))
            else:
                o.append('\t(global_label %s\n\t\t(shape %s)\n\t\t(at %s %s %s)\n\t\t(effects\n\t\t\t(font\n'
                         '\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' %
                         (kstr(name), shape, x, y, rot, just, uid()))
        for s, x, y, size, bold in self.texts:
            o.append('\t(text %s\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n'
                     '\t\t\t\t(size %s %s)%s\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' %
                     (kstr(s), x, y, size, size, '\n\t\t\t\t(bold yes)' if bold else '', uid()))
        for p in self.parts:
            o.append(self._sym_inst(p))
        o.append('\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n')
        open(path, 'w').write(''.join(o))


def find_merges(sch, intended):
    """Union-find over the drawn geometry. intended: {net: ['REF.PIN', ...]}. Reports each wire / name that joins
    two different intended nets, with coordinates, so drawing mistakes can be located."""
    owner = {p: n for n, ps in intended.items() for p in ps}
    parent = {}

    def f(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    tags = {}

    def tag_of(x):
        return tags.get(f(x), set())

    def union(a, b, why):
        ra, rb = f(a), f(b)
        if ra == rb:
            return
        ta, tb = tags.get(ra, set()), tags.get(rb, set())
        if ta and tb and ta != tb:
            print('MERGE %s + %s via %s' % (sorted(ta), sorted(tb), why))
        parent[ra] = rb
        tags[rb] = ta | tb
    for p in sch.parts:
        for q in p.pins:
            pt = ('pt',) + p.p(q['num'])
            key = '%s.%s' % (p.ref, q['num'])
            if p.ref.startswith('#'):
                union(pt, ('name', p.value), 'power symbol %s at %s' % (p.value, pt[1:]))
                continue
            n = owner.get(key)
            if n:
                r = f(pt)
                if tags.get(r) and n not in tags[r]:
                    print('MERGE %s + %s at pin %s %s' % (sorted(tags[r]), n, key, pt[1:]))
                tags[r] = tags.get(r, set()) | {n}
    for kind, name, x, y, rot, shape in sch.labels:
        union(('pt', x, y), ('name', name), 'label %s at %s' % (name, (x, y)))
    for a, b in sch.wires:
        union(('pt',) + a, ('pt',) + b, 'wire %s-%s' % (a, b))
