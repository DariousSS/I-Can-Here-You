"""干笔涂抹（油画棒/水粉）质感的 numpy 预览 -> ../outputs_standard/paint_smear_preview.png（和 crayon_mosaic_shader.glsl 的 painterly 模式同样的算法）"""
import os, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
fs = sorted(glob.glob(os.path.join(HERE, '..', 'td_live', 'stack', 'A', 'stack_*.jpg')))
def hsh(x, y): return (np.sin(x * 127.1 + y * 311.7) * 43758.5453) % 1.0
def vn(x, y):
    ix, iy = np.floor(x), np.floor(y); fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = hsh(ix, iy), hsh(ix + 1, iy), hsh(ix, iy + 1), hsh(ix + 1, iy + 1)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy
def samp(a, x, y):
    H, W = a.shape[:2]
    xi = np.clip(x, 0, W - 1.001); yi = np.clip(y, 0, H - 1.001)
    x0, y0 = xi.astype(int), yi.astype(int); fx, fy = (xi - x0)[..., None], (yi - y0)[..., None]
    return (a[y0, x0] * (1 - fx) * (1 - fy) + a[y0, x0 + 1] * fx * (1 - fy) + a[y0 + 1, x0] * (1 - fx) * fy + a[y0 + 1, x0 + 1] * fx * fy)
def paint(img, L, amt=1.0, N=14):
    a = np.asarray(img.convert('RGB'), dtype=np.float64) / 255.0
    H, W = a.shape[:2]; sc = W / 512.0
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    th = np.pi / 2 + (vn(xx * 0.004 / sc, yy * 0.004 / sc) - .5) * 0.7           # 笔触方向：大体向下，只带一点缓慢的歪（变化小，不然会转出涡纹）
    dx, dy = np.cos(th), np.sin(th); px, py = -dy, dx
    bj = (hsh(np.floor(xx / (1.6 * sc)), 3.0) - .5) * 5.0 * sc                   # 每根鬃毛各自的横向偏移 -> 一条条竖向刷痕（用固定的横坐标，不跟着方向转）
    Ls = L * sc
    acc = np.zeros_like(a)
    for t in np.linspace(-.25, .75, N):                                          # 拖尾：主要朝下拖
        acc += samp(a, xx + dx * t * Ls + px * bj, yy + dy * t * Ls + py * bj)
    c = acc / N
    streak = vn(xx * 0.42 / sc, yy * 0.012 / sc) * 0.7 + vn(xx * 1.1 / sc, yy * 0.03 / sc) * 0.3      # 干笔的粗糙条纹：横向变化快、纵向变化慢（固定竖向）
    c *= (0.80 + 0.40 * streak)[..., None]
    # 第二层斜向的涂抹（约 25 度），让笔触不要那么整齐
    th2 = th + 0.45
    d2x, d2y = np.cos(th2), np.sin(th2)
    acc2 = np.zeros_like(a)
    for t in np.linspace(-.2, .6, 9):
        acc2 += samp(a, xx + d2x * t * Ls * 0.8, yy + d2y * t * Ls * 0.8)
    c = c * 0.65 + (acc2 / 9) * 0.35 * (0.8 + 0.4 * streak)[..., None]
    blob = vn(xx * 0.006 / sc, yy * 0.006 / sc) * 0.6 + vn(xx * 0.02 / sc, yy * 0.02 / sc) * 0.4         # 大团大团的深色涂抹
    c *= (0.55 + 0.9 * blob)[..., None]
    lum = c.mean(-1, keepdims=True)
    c = lum + (c - lum) * 0.42                                                  # 降饱和
    shadow, light = np.array([0.02, 0.03, 0.02]), np.array([0.80, 0.79, 0.64])   # 阴影近黑（偏橄榄），高光偏旧纸的灰黄
    c = shadow + (light - shadow) * np.clip(c * 1.1, 0, 1) ** 1.7
    mid = np.clip(1 - np.abs(lum - 0.40) * 3.2, 0, 1)
    c += mid * np.array([0.10, -0.03, 0.03])                                     # 中间调略带暗紫红
    c += mid * (blob[..., None] - .5) * np.array([-0.04, 0.07, -0.04])           # 另一些地方偏橄榄绿
    c += (hsh(xx * 1.3, yy * 1.3) - .5)[..., None] * 0.10                        # 纸面颗粒
    vig = 1 - 0.35 * ((xx / W - .5) ** 2 + (yy / H - .5) ** 2) * 2.2
    c *= vig[..., None]
    return Image.fromarray((np.clip(a * (1 - amt) + c * amt, 0, 1) * 255).astype(np.uint8))
picks = [fs[len(fs) - 1], fs[len(fs) // 2], fs[12]]
S = 320
sheet = Image.new('RGB', (4 * (S + 8) + 8, 3 * (S + 8) + 8), (20, 16, 30))
for r, f in enumerate(picks):
    im = Image.open(f).convert('RGB').resize((S, S), Image.LANCZOS)
    sheet.paste(im, (8, r * (S + 8) + 8))
    for c, L in enumerate((90, 50, 22)):
        sheet.paste(paint(im, L * S / 512.0), (8 + (c + 1) * (S + 8), r * (S + 8) + 8))
out = os.path.join(HERE, '..', 'outputs_standard', 'paint_smear_preview.png')
sheet.save(out); print(os.path.abspath(out))
