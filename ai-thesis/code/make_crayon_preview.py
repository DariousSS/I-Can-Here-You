"""蜡笔马赛克的 numpy 预览（和 crayon_mosaic_shader.glsl 同样的算法）-> ../outputs_standard/crayon_mosaic_preview.png"""
import os, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
fs = sorted(glob.glob(os.path.join(HERE, '..', 'td_live', 'stack', 'A', 'stack_*.jpg')))
def hsh(x, y): return (np.sin(x * 127.1 + y * 311.7) * 43758.5453) % 1.0
def vnoise(x, y):
    ix, iy = np.floor(x), np.floor(y); fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = hsh(ix, iy), hsh(ix + 1, iy); c, d = hsh(ix, iy + 1), hsh(ix + 1, iy + 1)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy
def crayon(img, B, amt=1.0, t=0.0):
    a = np.asarray(img.convert('RGB'), dtype=np.float64) / 255.0
    H, W = a.shape[:2]; sc = W / 512.0; B = max(B * sc, 2.0)
    yy, xx = np.mgrid[0:H, 0:W].astype(float); px, py = xx + .5, yy + .5
    wx = (vnoise(px * .035 / sc + t * .15, py * .035 / sc) - .5) * B * .9
    wy = (vnoise(px * .035 / sc + 17.3 - t * .1, py * .035 / sc + 17.3) - .5) * B * .9
    qx, qy = px + wx, py + wy
    cx, cy = np.floor(qx / B), np.floor(qy / B)
    jx, jy = (hsh(cx, cy) - .5) * .45 * B, (hsh(cx + 7.7, cy + 7.7) - .5) * .45 * B
    c0x, c0y = (cx + .5) * B + jx - wx * .5, (cy + .5) * B + jy - wy * .5
    acc = np.zeros((H, W, 3))
    for ox, oy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        sx = np.clip((c0x + ox * B * .28).astype(int), 0, W - 1); sy = np.clip((c0y + oy * B * .28).astype(int), 0, H - 1)
        acc += a[sy, sx]
    col = acc * .25
    lum = (col * np.array([.299, .587, .114])).sum(-1, keepdims=True)
    col = lum + (col - lum) * 1.45
    col = np.floor(col * 9 + .5) / 9
    grain = vnoise(px * .9 / sc, py * .9 / sc) * .6 + vnoise(px * 2.7 / sc, py * 2.7 / sc) * .4
    col *= (.86 + .26 * grain)[..., None]
    hatch = np.sin((px / sc * .74 + py / sc * .67) * .85 + hsh(cx, cy) * 6.2831) * .5 + .5
    col *= (.90 + .20 * hatch)[..., None]
    fx, fy = (qx / B) % 1.0, (qy / B) % 1.0
    edge = np.minimum(np.minimum(fx, 1 - fx), np.minimum(fy, 1 - fy))
    e = np.clip(edge / .14, 0, 1); e = e * e * (3 - 2 * e)
    col *= (.88 + .12 * e)[..., None]
    return Image.fromarray(((a * (1 - amt) + col * amt).clip(0, 1) * 255).astype(np.uint8))
picks = [fs[len(fs) - 1], fs[len(fs) // 2], fs[12]]
sheet = Image.new('RGB', (4 * 330, 3 * 330), (20, 16, 30))
for r, f in enumerate(picks):
    im = Image.open(f).convert('RGB').resize((320, 320), Image.LANCZOS)
    sheet.paste(im, (5, r * 330 + 5))
    for c, B in enumerate((72, 40, 20)):
        sheet.paste(crayon(im, B * 320 / 512.0 * (512 / 320) * 0 + B * 320 / 512.0 * 1.0), (5 + (c + 1) * 330, r * 330 + 5))
out = os.path.join(HERE, '..', 'outputs_standard', 'crayon_mosaic_preview.png')
sheet.save(out); print(os.path.abspath(out))
