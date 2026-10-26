"""
A small shaded renderer, so a build123d model can be looked at as a picture
without opening a CAD program. It needs only numpy and Pillow.

render([(shape, (r, g, b)), ...], "out.png", eye=(x, y, z), target=(x, y, z))

The view is orthographic. Faces are shaded smooth, with an ink line drawn at
every crease and outline, in the line style of the other drawings.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

INK = np.array([0.067, 0.067, 0.067])
PAPER = (255, 255, 255)
FONTS = ["/System/Library/Fonts/Supplemental/Georgia.ttf", "/usr/share/fonts/TTF/DejaVuSerif.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"]


def _font(size):
    """Georgia on a Mac, like the other drawings; a serif that's to hand elsewhere."""
    for f in FONTS:
        if Path(f).exists():
            return ImageFont.truetype(f, size)
    return ImageFont.load_default(size)


def _mesh(shape, tolerance):
    verts, tris = shape.tessellate(tolerance, 0.25)
    v = np.array([(p.X, p.Y, p.Z) for p in verts], dtype=float)
    t = np.array(tris, dtype=int).reshape(-1, 3)
    # Smooth normals: average each triangle's normal onto its corners. Faces don't share
    # corners in build123d's mesh, so creases between faces stay sharp.
    fn = np.cross(v[t[:, 1]] - v[t[:, 0]], v[t[:, 2]] - v[t[:, 0]])
    vn = np.zeros_like(v)
    for k in range(3):
        np.add.at(vn, t[:, k], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)
    return v, t, vn


def render(parts, path, eye, target, size=(1400, 900), tolerance=0.08, margin=0.06, up=(0, 0, 1), scale=None, ss=3):
    """Render parts, a list of (shape, rgb with 0..1 channels), to a PNG.
    scale: pixels per millimeter; by default the parts are fitted to the picture.
    Returns the scale used, so a set of pictures can share one."""
    eye, target, up = (np.array(a, dtype=float) for a in (eye, target, up))
    f = target - eye
    f /= np.linalg.norm(f)
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    light = np.array([-0.35, -0.55, 0.75])
    light /= np.linalg.norm(light)
    fill = np.array([0.6, 0.3, 0.4])
    fill /= np.linalg.norm(fill)

    parts = [(s, rgb) for s, rgb in parts if s is not None and s.faces()]  # a cut can leave nothing of a part
    meshes = [(_mesh(s, tolerance), np.array(rgb, dtype=float)) for s, rgb in parts]
    pts = np.concatenate([m[0][0] for m in meshes])
    sx, sy = (pts - eye) @ r, (pts - eye) @ u
    W, H = size[0] * ss, size[1] * ss
    if scale is None:
        scale = min(size[0] * (1 - 2 * margin) / np.ptp(sx), size[1] * (1 - 2 * margin) / np.ptp(sy))
    k = scale * ss
    cx, cy = (sx.min() + sx.max()) / 2, (sy.min() + sy.max()) / 2

    depth = np.full((H, W), np.inf)
    normal = np.zeros((H, W, 3))
    color = np.ones((H, W, 3))
    ident = np.full((H, W), -1, dtype=int)

    for pid, ((v, t, vn), rgb) in enumerate(meshes):
        X = W / 2 + ((v - eye) @ r - cx) * k
        Y = H / 2 - ((v - eye) @ u - cy) * k
        Z = (v - eye) @ f
        for a, b, c in t:
            xs, ys = X[[a, b, c]], Y[[a, b, c]]
            x0, x1 = int(max(np.floor(xs.min()), 0)), int(min(np.ceil(xs.max()), W - 1))
            y0, y1 = int(max(np.floor(ys.min()), 0)), int(min(np.ceil(ys.max()), H - 1))
            if x1 < x0 or y1 < y0:
                continue
            den = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
            if abs(den) < 1e-9:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / den
            w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / den
            w2 = 1 - w0 - w1
            inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not inside.any():
                continue
            z = w0 * Z[a] + w1 * Z[b] + w2 * Z[c]
            win = depth[y0 : y1 + 1, x0 : x1 + 1]
            hit = inside & (z < win)
            if not hit.any():
                continue
            win[hit] = z[hit]
            n = w0[..., None] * vn[a] + w1[..., None] * vn[b] + w2[..., None] * vn[c]
            normal[y0 : y1 + 1, x0 : x1 + 1][hit] = n[hit]
            color[y0 : y1 + 1, x0 : x1 + 1][hit] = rgb
            ident[y0 : y1 + 1, x0 : x1 + 1][hit] = pid

    covered = np.isfinite(depth)
    n = normal / np.maximum(np.linalg.norm(normal, axis=2, keepdims=True), 1e-12)
    n[(n @ f) > 0] *= -1  # light both sides of a thin wall alike
    lit = 0.5 + 0.42 * np.clip(n @ light, 0, 1) + 0.16 * np.clip(n @ fill, 0, 1)
    img = np.where(covered[..., None], np.clip(color * lit[..., None], 0, 1), 1.0)

    # Ink lines where the surface folds, where one part meets another, and at outlines.
    d = np.where(covered, depth, depth[covered].max() + 50 if covered.any() else 0)
    edge = np.zeros((H, W), dtype=bool)
    for dy, dx in ((0, 1), (1, 0)):
        a, b = (slice(None, H - dy), slice(None, W - dx)), (slice(dy, None), slice(dx, None))
        crease = (n[a] * n[b]).sum(axis=2) < 0.82
        jump = np.abs(d[a] - d[b]) > 1.2
        other = ident[a] != ident[b]
        e = (crease | jump | other) & (covered[a] | covered[b])
        edge[a] |= e
    if ss > 2:  # about one output pixel wide
        edge = np.array(Image.fromarray((edge * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
    img[edge] = img[edge] * 0.15 + INK * 0.85

    out = Image.fromarray((img * 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    out.save(path)
    return scale


def sheet(path, title, panels, note="Drawn from the CAD model.", date=None, columns=None):
    """Put several pictures on one sheet, side by side, each with a caption under it.
    panels: (png path, caption lines). The sheet is framed like the other drawings."""
    imgs = []
    for p, _ in panels:  # trim the paper around each picture, keeping its scale
        img = Image.open(p).convert("RGB")
        box = Image.eval(img, lambda v: 255 - v).getbbox()
        imgs.append(img.crop((box[0] - 20, box[1] - 20, box[2] + 20, box[3] + 20)) if box else img)
    columns = columns or len(imgs)
    rows = (len(imgs) + columns - 1) // columns
    cw = max(i.width for i in imgs)
    ch = max(i.height for i in imgs)
    cap_h = 30 + 26 * max(len(c) for _, c in panels)
    W = 60 + columns * cw + (columns - 1) * 30 + 60
    H = 130 + rows * (ch + cap_h + 30)
    s = Image.new("RGB", (W, H), PAPER)
    g = ImageDraw.Draw(s)
    small, big, cap = _font(16), _font(30), _font(19)
    g.text((60, 40), "THE MACHINE", font=small, fill=(17, 17, 17))
    g.text((60, 66), title, font=big, fill=(17, 17, 17))
    g.text((W - 60, 40), note, font=small, fill=(17, 17, 17), anchor="ra")
    if date:
        g.text((W - 60, 64), date, font=small, fill=(17, 17, 17), anchor="ra")
    g.line((60, 112, W - 60, 112), fill=(17, 17, 17), width=1)
    for i, (img, (_, lines)) in enumerate(zip(imgs, panels)):
        x = 60 + (i % columns) * (cw + 30)
        y = 130 + (i // columns) * (ch + cap_h + 30)
        s.paste(img, (x + (cw - img.width) // 2, y))
        for j, line in enumerate(lines):
            g.text((x + cw / 2, y + ch + 16 + 26 * j), line, font=cap, fill=(17, 17, 17), anchor="ma")
    s.save(Path(path))
