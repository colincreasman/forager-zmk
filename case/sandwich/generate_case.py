#!/usr/bin/env python3
"""Sandwich top shell for the Forager: the Totemist look on the stock Forager case.

This replaces only the stock 2.2 mm top plate (../enclosed/LTop.stl, RTop.stl). The stock base you
already have, the PCB, the nuts and the four top screws per half stay as they are. In the wells the
new top is the stock plate itself: its switch cut-outs, clip chamfers, switch-puller grooves and
countersinks are copied from the stock top STL, so switches clip in and screws seat exactly as
before. Around the keys a rim rises to just under the keycap tops, so every key sits in a well
(ErgoMech's Totemist, GEIST's TOTEM), and the thumbs sit on a low shelf.

Writes to stl/: forager_<side>_top.stl, forager_report.json, preview pictures and 1:1 paper templates
for checking your stock case against the files this was built from.

Usage:  python generate_case.py [--out DIR] [--sides left right] [--rim MM] [--no-preview]
Requires: pip install manifold3d shapely trimesh numpy matplotlib rtree
"""
import argparse
import json
import math
import os
import re
import sys

import numpy as np
from manifold3d import CrossSection, FillRule, Manifold, Mesh
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import polygonize, unary_union

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sandwich as sw  # noqa: E402

PCB_FILE = os.path.join(HERE, '..', 'pcb', 'forager-pcb.kicad_pcb')
STOCK = os.path.join(HERE, '..', 'enclosed')
STOCK_FILES = {'left': ('LTop.stl', 'LBase.stl'), 'right': ('RTop.stl', 'RBase.stl')}
Z_PCB, Z_PLATE = 1.6, 3.8          # stock frame: PCB bottom at z = 0, top plate 1.6 .. 3.8
TOWARD_USER = (0.0, -1.0)


# ------------------------------------------------------------------ minimal KiCad reader (y down)
_TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


def sparse(text):
    stack = [[]]
    for m in _TOK.finditer(text):
        t = m.group(0)
        if t == '(':
            stack.append([])
        elif t == ')':
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(t[1:-1] if t[0] == '"' else t)
    return stack[0][0]


def find(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def find1(node, name):
    r = find(node, name)
    return r[0] if r else None


def arc3(p1, p2, p3, seg=0.25):
    (x1, y1), (x2, y2), (x3, y3) = p1, p2, p3
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-12:
        return [p1, p3]
    ux = ((x1 * x1 + y1 * y1) * (y2 - y3) + (x2 * x2 + y2 * y2) * (y3 - y1) + (x3 * x3 + y3 * y3) * (y1 - y2)) / d
    uy = ((x1 * x1 + y1 * y1) * (x3 - x2) + (x2 * x2 + y2 * y2) * (x1 - x3) + (x3 * x3 + y3 * y3) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    a1, a2, a3 = (math.atan2(y - uy, x - ux) for x, y in (p1, p2, p3))
    s13, s12 = (a3 - a1) % (2 * math.pi), (a2 - a1) % (2 * math.pi)
    sweep = s13 if s12 <= s13 else -(2 * math.pi - s13)
    n = max(4, int(abs(sweep) * r / seg))
    pts = [(ux + r * math.cos(a1 + sweep * i / n), uy + r * math.sin(a1 + sweep * i / n)) for i in range(n + 1)]
    pts[0], pts[-1] = p1, p3
    return pts


def fp_to_board(f, lx, ly):
    a = math.radians(f['rot'])
    return (f['x'] + lx * math.cos(a) + ly * math.sin(a), f['y'] - lx * math.sin(a) + ly * math.cos(a))


def edge_cuts(pcb):
    """Board outline from Edge.Cuts lines and arcs, including those drawn inside footprints (the
    mouse bites that join the two halves)."""
    pt = lambda n: (float(n[1]), float(n[2]))

    def poly(g, tf):
        if g[0].endswith('_line'):
            pl = [pt(find1(g, 'start')), pt(find1(g, 'end'))]
        else:
            pl = arc3(pt(find1(g, 'start')), pt(find1(g, 'mid')), pt(find1(g, 'end')))
        return [tf(*p) for p in pl]
    lines = []
    on_edge = lambda g: (find1(g, 'layer') or [None, None])[1] == 'Edge.Cuts'
    for g in pcb:
        if isinstance(g, list) and g and g[0] in ('gr_line', 'gr_arc') and on_edge(g):
            lines.append(poly(g, lambda x, y: (x, y)))
    for node in find(pcb, 'footprint'):
        at = find1(node, 'at')
        f = dict(x=float(at[1]), y=float(at[2]), rot=float(at[3]) if len(at) > 3 else 0.0)
        for g in node:
            if isinstance(g, list) and g and g[0] in ('fp_line', 'fp_arc') and on_edge(g):
                lines.append(poly(g, lambda x, y, f=f: fp_to_board(f, x, y)))
    reps = []

    def snap(p):
        for q in reps:
            if math.hypot(p[0] - q[0], p[1] - q[1]) < 0.02:
                return q
        reps.append(p)
        return p
    segs = []
    for pl in lines:
        pl = list(pl)
        pl[0], pl[-1] = snap(pl[0]), snap(pl[-1])
        segs.append(LineString(pl))
    faces = list(polygonize(unary_union(segs)))
    keep = [f for f in faces if sum(Polygon(g.exterior).contains(f.representative_point()) for g in faces if g is not f) % 2 == 0]
    return unary_union(keep)


def footprints(pcb):
    out = []
    for f in find(pcb, 'footprint'):
        at = find1(f, 'at')
        out.append(dict(lib=f[1], x=float(at[1]), y=float(at[2]), rot=float(at[3]) if len(at) > 3 else 0.0))
    return out


# ------------------------------------------------------------------ stock case
def load_stl(path):
    import trimesh
    m = trimesh.load(path)
    solid = Manifold(Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))
    assert solid.status().name == 'NoError', (path, solid.status())
    return solid


def shapely_slice(solid, z):
    out = Polygon()
    for r in solid.slice(z).to_polygons():
        if len(r) >= 3:
            out = out.symmetric_difference(Polygon(r))
    return out


def round_holes(g, dmin, dmax):
    """Centres and diameters of the round holes in g with a diameter between dmin and dmax."""
    out = []
    for p in sw.polys(g):
        for h in p.interiors:
            hp = Polygon(h)
            d = 2 * math.sqrt(hp.area / math.pi)
            if dmin <= d <= dmax and hp.minimum_rotated_rectangle.area < 1.35 * hp.area:
                out.append((hp.centroid.x, hp.centroid.y, d))
    return out


class Half:
    def __init__(self, side, rim):
        self.side = side
        top_f, base_f = STOCK_FILES[side]
        self.stock_top = load_stl(os.path.join(STOCK, top_f))
        self.stock_base = load_stl(os.path.join(STOCK, base_f))
        # the stock base's straight wall (z -0.18 .. 1.4) carries the case outline
        self.outline = max(sw.polys(shapely_slice(self.stock_base, 1.0)), key=lambda q: q.area)
        self.outline = Polygon(self.outline.exterior).simplify(0.005)
        top_outline = Polygon(max(sw.polys(shapely_slice(self.stock_top, 1.97)), key=lambda q: q.area).exterior)
        self.outline_match = round(self.outline.hausdorff_distance(top_outline), 3)

        pcb = sparse(open(PCB_FILE).read())
        inside = (lambda x: x < 0) if side == 'left' else (lambda x: x > 0)
        fps = [f for f in footprints(pcb) if inside(f['x'])]
        from shapely.geometry import box
        half_plane = box(-1e4, -1e4, 0, 1e4) if side == 'left' else box(0, -1e4, 1e4, 1e4)
        board = max(sw.polys(edge_cuts(pcb).intersection(half_plane)), key=lambda g: g.area)
        board = Polygon([(x, -y) for x, y in board.exterior.coords])               # KiCad y down -> y up
        self.board = max(sw.polys(board.intersection(self.outline)), key=lambda g: g.area)   # no panel tabs
        self.keys = []
        for f in fps:
            if 'choc' in f['lib'].lower():
                a = math.radians(f['rot'])
                ang = f['rot'] % 180
                self.keys.append(sw.Key((f['x'], -f['y']), (math.cos(a), math.sin(a)), thumb=min(ang, 180 - ang) > 18))
        self.nuts = [(f['x'], -f['y']) for f in fps if 'nut' in f['lib'].lower()]

        # stock plate features, checked against the PCB: switch cut-outs (below the puller grooves,
        # which join a column's cut-outs higher up) and top-screw countersinks
        cut_sec = shapely_slice(self.stock_top, 2.2)
        cuts = [Polygon(h) for p in sw.polys(cut_sec) for h in p.interiors if Polygon(h).area > 150]
        self.cutout_offset = round(max(min(Point(k.c).distance(c.centroid) for c in cuts) for k in self.keys), 3)
        csk = round_holes(shapely_slice(self.stock_top, Z_PLATE - 0.02), 3.5, 5.5)
        self.screws = [dict(c=(x, y), bore=round(d + 0.3, 2)) for x, y, d in csk]
        self.screw_to_nut = round(max(min(math.dist(s['c'], n) for n in self.nuts) for s in self.screws), 3)

        # plate cuts = whatever the stock top lacks inside its outline, in the plate's thickness
        inner = self.outline.buffer(-2.6, join_style=1)
        footprint = self.stock_top.slice(Z_PLATE - 0.01)
        filled = self.stock_top + footprint.extrude(0.3).translate([0, 0, Z_PLATE - 0.02])
        self.plate_cuts = sw.prism(inner, Z_PCB - 0.05, Z_PLATE + 0.2) - filled

        self.sandwich = sw.Sandwich(self.outline, Z_PCB, self.keys, TOWARD_USER, self.plate_cuts,
                                    screws=self.screws, rim=rim)
        self.top = sw.trim_thin(self.sandwich.build(), 0.8)
        self.sandwich.info['trimmed_mm3'] = round(self.sandwich.solid.volume() - self.top.volume(), 2)

    def check(self):
        against = {'stock base': self.stock_base, 'PCB': sw.prism(self.board, 0, Z_PCB),
                   'switches': sw.switches(self.keys, Z_PCB), 'keycaps, full travel': sw.keycap_sweep(self.keys, Z_PCB)}
        r = sw.report('top', self.top, against)
        # in the wells the new top must be the stock plate: compare the two between the PCB and the plate top.
        # Exact before trimming; trimming then drops the stock plate's few slivers under 0.8 mm (JLC's minimum).
        box = sw.prism(self.sandwich.wells.buffer(-0.05), Z_PCB, Z_PLATE)
        b = self.stock_top ^ box
        diff = lambda top: round(((top ^ box) - b).volume() + (b - (top ^ box)).volume(), 3)
        r['plate_vs_stock_mm3'] = diff(self.sandwich.solid)
        r['thin_slivers_removed_mm3'] = diff(self.top)
        r['outline_vs_stock_top_mm'] = self.outline_match
        r['cutouts_vs_pcb_mm'] = self.cutout_offset
        r['screws_vs_nuts_mm'] = self.screw_to_nut
        r['closed_pockets'] = sw.closed_pockets(self.top, self.outline, Z_PCB, self.sandwich.rim_h)
        r['ok'] = (r['ok'] and r['plate_vs_stock_mm3'] < 0.05 and self.cutout_offset < 0.1 and self.screw_to_nut < 0.1
                   and not r['closed_pockets'])
        return r


def template_svg(halves, path):
    """1:1 drawing of each stock top: outline, switch holes and screw holes, with a 50 mm scale bar."""
    m, gap = 10.0, 12.0
    blocks, y = [], m + 14
    W = 2 * m + max(h.outline.bounds[2] - h.outline.bounds[0] for h in halves)
    for h in halves:
        x0, y0, x1, y1 = h.outline.bounds
        tr = lambda x, yy, ox=m - x0, oy=y + y1: (x + ox, oy - yy)          # y up -> SVG y down
        d = lambda g: ' '.join('M' + ' L'.join('%.3f,%.3f' % tr(*p) for p in ring.coords[:-1]) + ' Z'
                               for q in sw.polys(g) for ring in [q.exterior, *q.interiors])
        plate = shapely_slice(h.stock_top, 3.0)
        blocks.append(f'<text x="{m}" y="{y - 3:.2f}" font-family="sans-serif" font-size="3.4" font-weight="bold">'
                      f'{h.side.upper()} top plate, seen from above: {x1 - x0:.1f} x {y1 - y0:.1f} mm</text>')
        blocks.append(f'<path d="{d(plate)}" fill="#e6e6e6" fill-rule="evenodd" stroke="#000" stroke-width="0.2"/>')
        for s in h.screws:
            cx, cy = tr(*s['c'])
            blocks.append(f'<path d="M{cx - 1.5:.3f},{cy:.3f} h3 M{cx:.3f},{cy - 1.5:.3f} v3" stroke="#c0392b" stroke-width="0.2"/>')
        y += (y1 - y0) + gap
    head = [f'<rect width="{W:.3f}" height="{y:.3f}" fill="#fff"/>',
            f'<text x="{m}" y="{m}" font-family="sans-serif" font-size="3.4" font-weight="bold">'
            'Forager stock top plates, 1:1 (print at 100 %, check the 50 mm bar)</text>',
            f'<path d="M{m},{m + 5} h50 M{m},{m + 3.5} v3 M{m + 50},{m + 3.5} v3" stroke="#000" stroke-width="0.3"/>',
            f'<text x="{m + 53}" y="{m + 6}" font-family="sans-serif" font-size="2.6">50 mm. Lay your top plate on its outline: '
            'edges, switch holes and the red screw crosses must line up.</text>']
    with open(path, 'w') as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.3f}mm" height="{y:.3f}mm" viewBox="0 0 {W:.3f} {y:.3f}">\n'
                + '\n'.join(head + blocks) + '\n</svg>\n')


def pictures(out, halves):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    shell, base, cap, gold, green = (0.93, 0.93, 0.92), (0.80, 0.80, 0.78), (0.95, 0.94, 0.88), (0.85, 0.65, 0.25), (0.15, 0.45, 0.25)
    h = halves[0]
    pcb = sw.prism(h.board, 0, Z_PCB)
    caps = sw.keycaps(h.keys, Z_PCB)
    fig, ax = plt.subplots(2, 2, figsize=(17, 12.5), dpi=90)
    sw.render(ax[0, 0], [(h.stock_base, base), (h.top, shell), (caps, cap)], sw.look(28, -100),
              f'{h.side.capitalize()} half with the sandwich top, stock base, MBK-size keycaps')
    sw.render(ax[0, 1], [(h.stock_base, base), (h.stock_top, shell), (caps, cap)], sw.look(28, -100),
              'The same half with its stock top plate')
    H, (x0, x1, y0, y1) = sw.heightmap(h.top)
    im = ax[1, 0].imshow(H - Z_PCB, origin='lower', extent=[x0, x1, y0, y1], cmap='viridis')
    fig.colorbar(im, ax=ax[1, 0], shrink=0.8, label='height above the PCB (mm)')
    ax[1, 0].set_title('Sandwich top from above: rim (yellow), thumb shelf and well floors (purple)', fontsize=10)
    ax[1, 0].set_aspect('equal')
    ax[1, 0].axis('off')
    sw.render(ax[1, 1], [(h.stock_base, base), (pcb, green), (sw.switches(h.keys, Z_PCB), gold),
                         (h.top.translate([0, 0, 22]), shell)], sw.look(35, -60), 'Sandwich top lifted off')
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'forager_preview.png'))
    plt.close(fig)

    main = [k for k in h.keys if not k.thumb]
    xm = np.median([k.c[0] for k in main])
    col = sorted(main, key=lambda k: abs(k.c[0] - xm))[:3]
    home = sorted(col, key=lambda k: k.c[1])[1]
    thumb = max([k for k in h.keys if k.thumb], key=lambda k: abs(k.c[0]))
    style = lambda c: dict(facecolor=c, edgecolor='k', lw=0.5)
    fig, ax = plt.subplots(2, 2, figsize=(16, 8.5), dpi=100)
    for j, (name, tp) in enumerate((('Stock Forager top (enclosed)', h.stock_top), ('Sandwich top (Totemist-style)', h.top))):
        parts = [(h.stock_base, style('#b9b9b4')), (pcb, style('#2a7a3e')), (tp, style('#ececea'))]
        sw.profile(ax[0, j], home, Z_PCB, parts, f'{name}: middle-finger column, you are on the right', TOWARD_USER, span=34)
        sw.profile(ax[1, j], thumb, Z_PCB, parts, f'{name}: outer thumb key, you are on the right', TOWARD_USER, span=24)
    s = h.sandwich
    for a in ax.flat:
        a.set_ylim(-5.5, 14.5)
    for a in ax[:, 1]:
        a.axhline(s.info['rim_z'], color='#d62728', lw=0.8, ls=':')
        a.text(a.get_xlim()[0] + 0.5, s.info['rim_z'] - 0.9, f'sandwich rim {s.info["rim_above_pcb"]:.2f} mm above the PCB',
               color='#d62728', fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'forager_profile.png'))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=os.path.join(HERE, 'stl'))
    ap.add_argument('--sides', nargs='+', default=['left', 'right'])
    ap.add_argument('--rim', type=float, default=sw.TOTEM['rim'],
                    help=f'rim height above the PCB top (default {sw.TOTEM["rim"]}, like the TOTEM/Totemist; '
                         f'{sw.MBK["top"]} = level with MBK keycap tops)')
    ap.add_argument('--no-preview', action='store_true')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    report, halves, ok = dict(rim_above_pcb=a.rim, mbk_top_above_pcb=sw.MBK['top'], halves={}), [], True
    for side in a.sides:
        print(f'[{side}] building ...')
        h = Half(side, a.rim)
        r = h.check()
        print(f"  top pieces={r['pieces']} vol={r['volume_cm3']}cm3 size={r['size_mm']} gaps={r['gap_mm']} "
              f"clash={ {k: v for k, v in r['clash_mm3'].items() if v > 1e-3} }")
        print(f"  plate in the wells vs stock plate: {r['plate_vs_stock_mm3']} mm3 different before trimming, "
              f"{r['thin_slivers_removed_mm3']} mm3 of sub-0.8 mm slivers trimmed; outline vs stock top "
              f"{r['outline_vs_stock_top_mm']} mm; cut-outs vs PCB {r['cutouts_vs_pcb_mm']} mm; "
              f"{len(h.screws)} top screws, {r['screws_vs_nuts_mm']} mm from their nuts -> {'OK' if r['ok'] else 'CHECK'}")
        r['stl_ok'] = sw.write_stl(h.top, os.path.join(a.out, f'forager_{side}_top.stl'))
        print(f"  wrote forager_{side}_top.stl, watertight after reload: {r['stl_ok']}")
        ok &= r['ok'] and r['stl_ok']
        report['halves'][side] = dict(top=r, shell=h.sandwich.info, screws=h.screws)
        halves.append(h)
    template_svg(halves, os.path.join(a.out, 'forager_stock_top_template_1to1.svg'))
    with open(os.path.join(a.out, 'forager_report.json'), 'w') as fh:
        json.dump(report, fh, indent=1, default=str)
    if not a.no_preview:
        pictures(a.out, halves)
    print('done ->', a.out, '' if ok else '  (some checks FAILED: see above)')
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
