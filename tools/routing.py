"""Routing as data for minipc-power (kicad-pcb-workflow references/routing.md: no autorouter; every track is chosen
coordinates). Runs in a normal python with shapely (the kicad-skills analysis venv).

Pads are referenced by name: P('U4', '7') is the pad centre, read from board.json (boarddump.py), so routes follow
placement changes. Net names are taken from the pads, never typed, so a route cannot silently use a wrong net.
Vias placed with via_near() / via_field() are clearance-checked against every other-net pad, track and via
(round caps, clearance + radius) before they are accepted.
"""
import json, math
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union

CLR = 0.2            # clearance used when checking new vias and tracks against other nets (net-class max)
HOLE_GAP = 0.1       # extra spacing between any two vias' copper, so drills stay > 0.25 mm apart (board rule)


class Router:
    def __init__(self, board_json):
        self.B = json.load(open(board_json))
        self.pads = {}
        for f in self.B['footprints']:
            for p in f['pads']:
                rings = [Polygon(r, h) if len(r) >= 3 else None for r, h in p['poly']]
                g = unary_union([r for r in rings if r is not None and r.is_valid] or [Point(p['x'], p['y']).buffer(0.1)])
                self.pads.setdefault((f['ref'], p['num']), []).append(dict(p, geom=g))
        self.tracks, self.vias, self.zones, self.keepouts = [], [], [], []
        self.log = []

    # -------------------------------------------------------------- lookups
    def pad(self, ref, num, i=0):
        return self.pads[(ref, str(num))][i]

    def P(self, ref, num, i=0):
        p = self.pad(ref, num, i)
        return (round(p['x'], 4), round(p['y'], 4))

    def net(self, ref, num):
        return self.pad(ref, num)['net']

    def bounds(self, ref, num, i=0):
        return self.pad(ref, num, i)['geom'].bounds          # x0, y0, x1, y1

    # -------------------------------------------------------------- obstacles
    def _obstacles(self, net, layers):
        obs = []
        for (ref, num), lst in self.pads.items():
            for p in lst:
                if p['net'] != net and set(p['layers']) & set(layers) or (p['th'] and p['net'] != net):
                    obs.append(p['geom'])
        for t in self.tracks:
            if t['net'] != net and t['layer'] in layers:
                obs.append(LineString([t['a'], t['b']]).buffer(t['w'] / 2, 8) if t['a'] != t['b'] else Point(t['a']).buffer(t['w'] / 2))
        for v in self.vias:
            if v['net'] != net:
                obs.append(Point(v['at']).buffer(v['size'] / 2, 16))
        return unary_union(obs) if obs else Polygon()

    def seg_ok(self, a, b, net, w, layers):
        obs = self._obstacles(net, layers)
        g = LineString([a, b]).buffer(w / 2 + CLR, 8) if a != b else Point(a).buffer(w / 2 + CLR)
        return not g.intersects(obs)

    def via_ok(self, pt, net, size=0.6):
        obs = self._obstacles(net, ['F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'])
        edge = Polygon(self.B['edge'][0][0]) if self.B.get('edge') else None
        c = Point(pt).buffer(size / 2 + CLR, 16)
        if edge is not None and not edge.buffer(-0.3).contains(Point(pt).buffer(size / 2)):
            return False
        # drilled holes keep apart whatever their net (the obstacle set skips same-net copper)
        for v in self.vias:
            if math.dist(v['at'], pt) < (v['size'] + size) / 2 + HOLE_GAP:
                return False
        return not c.intersects(obs)

    # -------------------------------------------------------------- primitives
    def track(self, layer, width, *pts, net=None):
        """pts: (x, y) or ('REF', 'PIN') pad references; consecutive points become segments."""
        res = []
        for q in pts:
            if isinstance(q, tuple) and len(q) == 2 and isinstance(q[0], str):
                if net is None:
                    net = self.net(*q)
                elif self.net(*q) != net:
                    raise ValueError('track %s touches %s.%s of net %s' % (net, q[0], q[1], self.net(*q)))
                res.append(self.P(*q))
            else:
                res.append((round(q[0], 4), round(q[1], 4)))
        assert net, 'track needs a net (give a pad reference or net=)'
        for a, b in zip(res, res[1:]):
            if a != b:
                self.tracks.append(dict(layer=layer, w=width, a=a, b=b, net=net))
        return res[-1]

    def via(self, pt, net, size=0.6, drill=0.3, check=True):
        if check and not self.via_ok(pt, net, size):
            self.log.append('via REJECTED (clearance) %s at %s' % (net, pt))
            return False
        self.vias.append(dict(at=(round(pt[0], 4), round(pt[1], 4)), net=net, size=size, drill=drill))
        return True

    def via_near(self, ref, num, net=None, size=0.6, drill=0.3, max_r=2.0, prefer=None, link=True, link_w=0.5):
        """Put a via as close as possible to a pad edge (search outward), clearance-checked. prefer: (dx, dy) bias."""
        net = net or self.net(ref, num)
        x0, y0, x1, y1 = self.bounds(ref, num)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        best = None
        r = size / 2 + 0.15
        while r <= max_r and best is None:
            cands = []
            hw, hh = (x1 - x0) / 2, (y1 - y0) / 2
            for k in range(32):
                a = 2 * math.pi * k / 32
                q = (cx + (hw + r) * math.cos(a), cy + (hh + r) * math.sin(a))
                score = r + (0 if prefer is None else -0.3 * (math.cos(a) * prefer[0] + math.sin(a) * prefer[1]))
                cands.append((score, q))
            for score, q in sorted(cands):
                if self.via_ok(q, net, size) and (not link or self.seg_ok((cx, cy), q, net, min(link_w, min(x1 - x0, y1 - y0)),
                                                                          self.pad(ref, num)['layers'][:1] or ['F.Cu'])):
                    best = q
                    break
            r += 0.1
        if best is None:
            self.log.append('no room for a via next to %s.%s (%s)' % (ref, num, net))
            return None
        self.vias.append(dict(at=(round(best[0], 4), round(best[1], 4)), net=net, size=size, drill=drill))
        if link:                                   # short track from the pad centre to the via
            pc = self.P(ref, num)
            w = min(link_w, min(x1 - x0, y1 - y0))
            self.tracks.append(dict(layer=self.pad(ref, num)['layers'][0] if not self.pad(ref, num)['th'] else 'F.Cu',
                                    w=round(w, 3), a=pc, b=(round(best[0], 4), round(best[1], 4)), net=net))
        return best

    def via_field(self, net, x0, y0, x1, y1, pitch=1.0, size=0.6, drill=0.3):
        n = 0
        y = y0
        while y <= y1 + 1e-6:
            x = x0
            while x <= x1 + 1e-6:
                if self.via((x, y), net, size, drill):
                    n += 1
                x += pitch
            y += pitch
        return n

    def zone(self, net, layer, pts, prio=0, solid=True, name='', clearance=0.2, min_thick=0.2):
        self.zones.append(dict(net=net, layer=layer, pts=[(round(x, 4), round(y, 4)) for x, y in pts], prio=prio,
                               solid=solid, name=name, clearance=clearance, min_thick=min_thick))

    def keepout(self, layer, pts, name=''):
        """Rule area that keeps copper pours out (tracks, vias and pads still allowed), e.g. an analog-ground island."""
        self.keepouts.append(dict(layer=layer, pts=[(round(x, 4), round(y, 4)) for x, y in pts], name=name))

    def rect(self, net, layer, x0, y0, x1, y1, **kw):
        self.zone(net, layer, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], **kw)

    # -------------------------------------------------------------- output
    def emit(self, board):
        """Add the routed copper to a kicad_sexpr Board (it owns the file syntax, uuids and escaping)."""
        for t in self.tracks:
            board.segment(t['a'], t['b'], t['w'], t['layer'], t['net'])
        for v in self.vias:
            board.via(v['at'], v['size'], v['drill'], v['net'], free=True)
        for z in self.zones:
            board.zone(z['net'], z['layer'], z['pts'], priority=z['prio'], name=z['name'], clearance=z['clearance'],
                       min_thickness=z['min_thick'], connect_pads='yes' if z['solid'] else None,
                       thermal_gap=0.3, thermal_bridge_width=0.4, island_removal_mode=0)
        for k in self.keepouts:
            board.rule_area(k['layer'], k['pts'], name=k['name'], copperpour=False)
