"""裂缝里的眼睛的 numpy 预览（和 rift_shader.glsl 同样的算法）-> ../outputs_standard/rift_preview.png"""
import math, os
import numpy as np
from PIL import Image
W, H, BLK, SH, WH, XE = 1920, 1080, 6.0, 330.0, 112.0, 150.0
E = [(-26, -270, 46), (24, -180, 60), (-28, -90, 70), (22, 0, 76), (-26, 90, 70), (24, 180, 60), (-22, 270, 46)]
sm = lambda a, b, x: np.clip((x - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((x - a) / (b - a), 0, 1))
def hs(n): return (np.sin(n * 12.9898) * 43758.5453) % 1.0
def slit(P, c, o, T, red, tm):
    out = np.zeros(P.shape[:2] + (4,))
    if o <= 0.01: return out
    dx, dy = P[..., 0] - c[0], P[..., 1] - c[1]
    oh, ow = float(sm(0, .5, o)), float(sm(.2, 1., o))
    halfH, halfW = SH * oh, WH * ow
    t = np.clip(np.abs(dy) / halfH, 0, 1)
    hw = halfW * (1 - t ** 1.5) + (hs(np.floor(dy / BLK) + 7.0) - .5) * .30 * halfW * (1 - t)
    hw = np.maximum(hw, 0)
    lc = np.array([1, 1, 1]) * (1 - red) + np.array([1, .28, .28]) * red
    ax = np.abs(dx)
    inside = (ax < hw) & (np.abs(dy) <= halfH)
    edge = (np.abs(ax - hw) < BLK * .75) & (np.abs(dy) <= halfH + BLK * .5) & (hw > 1)
    out[inside] = (0, 0, 0, 1)
    out[edge] = (*lc, 1)
    eo = float(sm(.45, .9, o))
    if eo > .01:
        for i, (ex, ey, a0) in enumerate(E):
            ec = (ex * ow, ey * oh); a = a0 * eo
            lx, ly = dx - ec[0], dy - ec[1]
            b = a * .5
            tt = (tm + i * 1.3) % 5.0
            bl = 1 - (max(0, 1 - abs(tt - .1) / .12) if tt < .3 else 0)
            h = b * max(.10, bl)
            sx = np.clip(lx / a, -1, 1)
            hh = h * (1 - sx * sx)
            in2 = (np.abs(lx) < a) & (np.abs(ly) < hh)
            ed = (np.abs(lx) < a) & (np.abs(np.abs(ly) - hh) < BLK * .5)
            g = (T[0] - (c[0] + ec[0]), T[1] - (c[1] + ec[1])); gl = math.hypot(*g) + 1e-4
            k = min(1, gl / 500); pc = (g[0] / gl * k * a * .38, g[1] / gl * k * b * .40)
            rr = b * .6
            dd = np.hypot(lx - pc[0], ly - pc[1])
            ring = in2 & (np.abs(dd - rr) < BLK * .5)
            pup = in2 & (dd < max(rr * .42, BLK * 1.2))
            out[in2 | ed] = (0, 0, 0, 1)
            out[ring | pup | ed] = (*lc, 1)
    return out
yy, xx = np.mgrid[0:H, 0:W].astype(float)
fx, fy = xx + .5, (H - 1 - yy) + .5
P = np.stack([(np.floor(fx / BLK) + .5) * BLK, (np.floor(fy / BLK) + .5) * BLK], -1)
cL = slit(P, (XE, 540), 1.0, (700, 540), 0.0, 0.0)
cR = slit(P, (W - XE, 540), 1.0, (1220, 540), 0.85, 0.0)
img = np.zeros((H, W, 4)); img[..., :] = (0.12, 0.09, 0.2, 1)
for c in (cL, cR):
    m = c[..., 3] > .5
    img[m] = c[m]
Image.fromarray((img[..., :3] * 255).astype(np.uint8)).resize((1200, 675), Image.LANCZOS).save(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs_standard", "rift_preview.png"))
print("ok")
