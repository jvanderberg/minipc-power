"""Minimal schematic layout helper for generated, wire-drawn schematics, written through kicad-skills' kicad_sexpr
layer (no s-expression text is formatted here).

Coordinates are millimetres, y pointing down (KiCad sheet coordinates). Keep everything on the 1.27 mm grid.
Usage: build a Sch, place parts (returns Part objects whose .p(pin) gives the pin's connection point), draw wires
between points, add power symbols / labels, then write(). Junctions are added automatically wherever three or more
connection ends meet, or a wire end lands on the interior of another wire.
"""
import kskills  # noqa: F401  (kicad_sexpr on sys.path)
from kicad_sexpr import Schematic, SymbolLibrary, pins_of, symbol_point  # noqa: E402

G = 1.27


def snap(v):
    return round(round(v / G) * G, 4)


# ---------------------------------------------------------------- symbol libraries

class SymLib(SymbolLibrary):
    """A .kicad_sym library under a nickname (kicad_sexpr.SymbolLibrary)."""

    def __init__(self, nickname, path=None, text=None, lib=None):
        src = lib if lib is not None else (SymbolLibrary.from_text(text) if text is not None else SymbolLibrary.load(path))
        super().__init__(src.tree, nickname, path)


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

    def p(self, key):
        """Connection point of a pin, by number or (unique) name."""
        cands = [q for q in self.pins if q.number == str(key)] or [q for q in self.pins if q.name == str(key)]
        if not cands:
            raise KeyError('%s has no pin %s' % (self.ref, key))
        q = cands[0]
        x, y = symbol_point(q.x, q.y, (self.x, self.y), self.rot, self.mirror)
        return (snap(x), snap(y))

    def pin_numbers(self):
        return [q.number for q in self.pins]


class Sch:
    def __init__(self, project, paper='A2', title='', rev='', date=''):
        self.project = project
        self.paper, self.title, self.rev, self.date = paper, title, rev, date
        self.libs = {}
        self.parts = []
        self.wires = []
        self.labels = []
        self.noconnects = []
        self.texts = []
        self.extra_junctions = []
        self.pwr_n = 0

    def lib(self, nickname, path=None, text=None, lib=None):
        self.libs[nickname] = SymLib(nickname, path, text, lib)

    def libsym(self, lib_id):
        nick, name = lib_id.split(':', 1)
        return self.libs[nick].get(name)

    def add(self, lib_id, ref, value, x, y, rot=0, footprint='', lcsc='', fields=None, in_bom=True, on_board=True,
            dnp=False, mirror=None):
        f = dict(fields or {})
        if lcsc:
            f['LCSC'] = lcsc
        p = Part(self, lib_id, ref, value, x, y, rot, pins_of(self.libsym(lib_id), 1, 1), f, footprint, in_bom,
                 on_board, dnp, mirror)
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
            for q in p.pin_numbers():
                pin_pts.add(p.p(q))
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
            for q in p.pin_numbers():
                pt = p.p(q)
                for a, b in self.wires:
                    if pt in (a, b):
                        continue
                    if (a[0] == b[0] == pt[0] and min(a[1], b[1]) < pt[1] < max(a[1], b[1])) or \
                       (a[1] == b[1] == pt[1] and min(a[0], b[0]) < pt[0] < max(a[0], b[0])):
                        bad.append((p.ref, q, pt))
        return bad

    # ------------------------------------------------------------ output

    def _split_wires(self):
        """Split wires at every pin point and wire end lying on their interior, so T-taps are real joints."""
        pts = set()
        for a, b in self.wires:
            pts.add(a); pts.add(b)
        for p in self.parts:
            for q in p.pin_numbers():
                pts.add(p.p(q))
        out = []
        for a, b in self.wires:
            cuts = [pt for pt in pts if pt not in (a, b) and (
                (a[0] == b[0] == pt[0] and min(a[1], b[1]) < pt[1] < max(a[1], b[1])) or
                (a[1] == b[1] == pt[1] and min(a[0], b[0]) < pt[0] < max(a[0], b[0])))]
            seq = sorted([a, b] + cuts, key=lambda q: (q[0] - a[0]) ** 2 + (q[1] - a[1]) ** 2)
            out += [(u, v) for u, v in zip(seq, seq[1:]) if u != v]
        self.wires = out

    def _body_rect(self, lib_id):
        """(x1, y1, x2, y2) of the first rectangle in a library symbol's body, or None."""
        for r in self.libsym(lib_id).walk('rectangle'):
            s, e = r.find('start'), r.find('end')
            return float(s[1]), float(s[2]), float(e[1]), float(e[2])
        return None

    def _field_spots(self, p):
        """Default (ref x, y, value x, y, angle, justify) for a placed part."""
        n = len(set(p.pin_numbers()))
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
        rect = self._body_rect(p.lib_id)
        if rect and p.rot == 0 and not p.mirror:
            x1, y1, x2, y2 = rect
            left, top, bot = p.x + min(x1, x2), p.y - max(y1, y2), p.y - min(y1, y2)
            return left, top - 1.27, left, bot + 2.54, 0, 'left'
        return p.x + 3.81, p.y - 3.81, p.x + 3.81, p.y + 3.81, 90 if p.rot in (90, 270) else 0, 'left'

    def _place(self, sch, p):
        """Place one Part through kicad_sexpr and position its fields the way this generator lays them out."""
        fields = {k: v for k, v in p.fields.items() if not k.startswith('_') and k != 'Datasheet'}
        desc = fields.pop('Description', None)
        sym = sch.add_symbol(p.lib_id, p.ref, p.value, (p.x, p.y), p.rot, p.mirror, footprint=p.footprint,
                             datasheet=p.fields.get('Datasheet', ''), description=desc, fields=fields,
                             in_bom=p.in_bom, on_board=p.on_board, dnp=p.dnp)
        rx, ry, vx, vy, ang, just = self._field_spots(p)
        if '_ref_at' in p.fields:
            rx, ry = p.fields['_ref_at']
        if '_val_at' in p.fields:
            vx, vy = p.fields['_val_at']
        just = p.fields.get('_just', just)
        hide_val = p.fields.get('_hide_value', p.lib_id == 'power:GND')
        sym.set_field('Reference', at=(snap(rx), snap(ry)), angle=ang, justify=[just], hide=p.ref.startswith('#'))
        sym.set_field('Value', at=(snap(vx), snap(vy)), angle=ang, justify=[just], hide=hide_val)
        for k in ('Footprint', 'Datasheet', 'Description'):
            if sym.field(k) is not None:
                sym.set_field(k, at=(p.x, p.y), angle=ang, hide=True, justify=[just])
        for k in fields:
            if k not in p.fields.get('_visible', []):
                sym.set_field(k, at=(p.x, p.y), angle=ang, hide=True, justify=[just])
        for i, k in enumerate(p.fields.get('_visible', [])):     # extra visible fields stacked under the value
            sym.set_field(k, at=(snap(vx), snap(vy + 2.54 * (i + 1))), angle=ang, hide=False, justify=[just])
        return sym

    def build(self):
        """The kicad_sexpr Schematic for everything drawn so far."""
        self._split_wires()
        sch = Schematic.new(self.project, paper=self.paper, title=self.title, date=self.date, rev=self.rev)
        for lib_id in sorted({p.lib_id for p in self.parts}):
            nick, name = lib_id.split(':', 1)
            sch.embed_symbol(lib_id, self.libs[nick])
        for pt in self._junctions():
            sch.junction(pt)
        for pt in self.noconnects:
            sch.no_connect(pt)
        for a, b in self.wires:
            sch.wire(a, b)
        for kind, name, x, y, rot, shape in self.labels:
            if kind == 'label':
                sch.label(name, (x, y), rot)
            else:
                sch.global_label(name, (x, y), rot, shape)
        for s, x, y, size, bold in self.texts:
            sch.text(s, (x, y), size, bold=bold)
        for p in self.parts:
            self._place(sch, p)
        return sch

    def write(self, path):
        self.build().save(path)


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
        for q in p.pin_numbers():
            pt = ('pt',) + p.p(q)
            key = '%s.%s' % (p.ref, q)
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
