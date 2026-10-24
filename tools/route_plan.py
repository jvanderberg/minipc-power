"""Routes for minipc-power, block by block (coordinates as data; see tools/routing.py).

Layer plan (docs/layout-plan.md):
  F.Cu   parts; power pours per net (VBUS, SW nodes, converter VIN/VOUT, protection chain); GND pour fills the rest
  In1.Cu solid GND plane - no tracks
  In2.Cu VSYS plane (the hub: charger -> 12 V, 5 V, 3.3 V converters, LED, switch pad)
  B.Cu   GND pour; BAT (charger <-> fuse, up to ~5.6 A) as a wide pour; slow signals (EN, status) as tracks
"""
X0, Y0, X1, Y1 = 100.0, 100.0, 152.0, 136.0


def planes(r):
    m = 0.3
    r.rect('GND', 'In1.Cu', X0 + m, Y0 + m, X1 - m, Y1 - m, prio=0, name='GND_PLANE')
    vsys = r.net('U2', '15')
    r.rect(vsys, 'In2.Cu', X0 + m, Y0 + m, X1 - m, Y1 - m, prio=0, name='VSYS_PLANE')
    r.rect('GND', 'F.Cu', X0 + m, Y0 + m, X1 - m, Y1 - m, prio=0, name='GND_TOP')
    r.rect('GND', 'B.Cu', X0 + m, Y0 + m, X1 - m, Y1 - m, prio=0, name='GND_BOTTOM')


def stitch_pads(r):
    """A via beside every SMD GND and VSYS pad, so every one reaches its plane directly."""
    vsys = r.net('U2', '15')
    for (ref, num), lst in sorted(r.pads.items()):
        p = lst[0]
        if p['th'] or p['net'] not in ('GND', vsys) or ref.startswith(('U', 'J', 'H')):
            continue
        r.via_near(ref, num)


def build(r):
    planes(r)
    stitch_pads(r)
