"""board_shader.glsl 的 numpy 预览 -> ../outputs_standard/board_preview.png"""
import json, os
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
N = 960
SEG = [63, 6, 91, 79, 102, 109, 125, 7, 127, 111]
faces = [np.asarray(Image.open(os.path.join(HERE, '..', 'td_live', 'burst', 'face_%02d.jpg' % i)).convert('RGB').resize((256, 256)), dtype=np.float64) / 255 for i in range(12)]
faces.append(faces[3])
faces.append(np.asarray(Image.open(os.path.join(HERE, '..', 'outputs_standard', 'standard_face.png')).convert('RGB').resize((256, 256)), dtype=np.float64) / 255)
faces.append(np.asarray(Image.open(os.path.join(HERE, '..', 'outputs_standard', 'fairface', 'avg_all.png')).convert('RGB').resize((256, 256)), dtype=np.float64) / 255)
bd = json.load(open(os.path.join(HERE, '..', 'td_live', 'burst', 'burst_dev.json')))
def sample(k, u, v):
    a = faces[k]; x = np.clip((u * 255).astype(int), 0, 255); y = np.clip(((1 - v) * 255).astype(int), 0, 255)
    return a[y, x]
def hs(x, y): return (np.sin(x * 127.1 + y * 311.7) * 43758.5453) % 1.0
def seg_rect(px, py, cx, cy, hx, hy): return ((np.abs(px - cx) < hx) & (np.abs(py - cy) < hy)).astype(float)
def glyph(n, px, py):
    inb = (px >= 0) & (px <= 1) & (py >= 0) & (py <= 1)
    b = SEG[n]; r = np.zeros_like(px)
    for bit, (cx, cy, hx, hy) in enumerate([(.5, .93, .40, .07), (.92, .72, .08, .23), (.92, .28, .08, .23), (.5, .07, .40, .07), (.08, .28, .08, .23), (.08, .72, .08, .23), (.5, .5, .40, .07)]):
        if (b >> bit) & 1: r = np.maximum(r, seg_rect(px, py, cx, cy, hx, hy))
    return r * inb
cells = {}
for r in range(4):
    for c in range(4):
        i = r * 4 + c; white = (r + c) % 2 == 0
        cells[i] = (13, 2, -1) if i == 0 else (14, 2, -1) if i == 15 else (0, 3, -1) if i == 6 else None
rng = np.random.default_rng(4)
for i in range(16):
    r, c = divmod(i, 4); white = (r + c) % 2 == 0
    if cells[i] is None:
        k = int(rng.integers(0, 12))
        cells[i] = (k, 0, float(bd[str(k)])) if white else (k, 1, -1)
yy, xx = np.mgrid[0:N, 0:N].astype(float); uvx, uvy = (xx + .5) / N, 1 - (yy + .5) / N
gx, gy = uvx * 4, (1 - uvy) * 4
ccx, ccy = np.clip(gx.astype(int), 0, 3), np.clip(gy.astype(int), 0, 3)
cux, cuy = gx % 1.0, 1 - (gy % 1.0)
col = np.zeros((N, N, 3))
for i in range(16):
    r, c = divmod(i, 4); white = (r + c) % 2 == 0
    m = (ccx == c) & (ccy == r); k, kind, dev = cells[i]
    base = np.array([.93, .91, .96]) if white else np.array([.07, .055, .11])
    cl = np.tile(base, (N, N, 1))
    qx, qy = (cux - .5) / .88 + .5, (cuy - .5) / .88 + .5
    inf = (qx > 0) & (qx < 1) & (qy > 0) & (qy < 1)
    if kind == 0 or kind == 2:
        f = sample(k, qx, qy); cl[inf] = f[inf]
    elif kind == 1:
        bl = 12.0; idx_x, idx_y = np.floor(qx * bl), np.floor(qy * bl)
        jx, jy = (hs(idx_x, idx_y) - .5) * .6 / bl, (hs(idx_x + 3.7, idx_y + 3.7) - .5) * .6 / bl
        c0 = sample(k, (idx_x + .5) / bl + jx, (idx_y + .5) / bl + jy)
        lum = (c0 * np.array([.299, .587, .114])).sum(-1, keepdims=True)
        c0 = lum + (c0 - lum) * 1.4; c0 = np.floor(c0 * 7 + .5) / 7; c0 = c0 * (.85 + .25 * hs(np.floor(qx * 80), np.floor(qy * 80)))[..., None]
        cl[inf] = c0[inf]
    else:
        d = np.maximum(np.abs(cux - .5), np.abs(cuy - .5)); fr = ((d > .40) & (d < .44)).astype(float)
        e = np.hypot((cux - .5) / .19, (cuy - .5) / .27); ov = (np.abs(e - 1) < .07).astype(float)
        cl = cl * (1 - np.maximum(fr, ov * .8))[..., None] + np.maximum(fr, ov * .8)[..., None]
    if kind == 0 and dev >= 0:
        v = min(dev, .99); d1 = int(v * 10); d2 = int((v * 10 % 1) * 10)
        bg = (cux > .03) & (cux < .36) & (cuy > .03) & (cuy < .21)
        cl[bg] = cl[bg] * .2 + np.array([.08, .06, .12]) * .8
        gyy = (cuy - .06) / .12
        dg = glyph(0, (cux - .05) / .065, gyy)
        dg = np.maximum(dg, seg_rect(cux, gyy, .128, .07, .008, .07))
        dg = np.maximum(dg, glyph(d1, (cux - .15) / .065, gyy)); dg = np.maximum(dg, glyph(d2, (cux - .24) / .065, gyy))
        t = np.clip((v - .3) / .6, 0, 1); nc = np.array([.55, 1, .8]) * (1 - t) + np.array([1, .35, .4]) * t
        cl = cl * (1 - dg)[..., None] + nc * dg[..., None]
    if i == 10:
        e2 = np.maximum(np.abs(cux - .5), np.abs(cuy - .5)); cl[e2 > .455] = (.2, .95, .9)
    if i == 5:
        e2 = np.maximum(np.abs(cux - .5), np.abs(cuy - .5)); mm = (e2 > .425) & (e2 < .48); cl[mm] = cl[mm] * .5 + np.array([1, .2, .7]) * .5
    col[m] = cl[m]
gap = np.minimum(np.minimum(gx % 1, 1 - gx % 1), np.minimum(gy % 1, 1 - gy % 1))
col *= (0.85 + 0.15 * np.clip(gap / .01, 0, 1))[..., None]
out = os.path.join(HERE, '..', 'outputs_standard', 'board_preview.png')
Image.fromarray((col.clip(0, 1) * 255).astype(np.uint8)).save(out); print(os.path.abspath(out))
