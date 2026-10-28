"""油画效果（不用 AI 模型）的 numpy 预览：顺着形状走的笔触 + Kuwahara 油画滤镜 + 厚涂的高低光影 + 暗沉的颜色和纸面颗粒
-> ../outputs_standard/oil_preview.png"""
import os, glob
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, uniform_filter, map_coordinates
HERE = os.path.dirname(os.path.abspath(__file__))
fs = sorted(glob.glob(os.path.join(HERE, '..', 'td_live', 'stack', 'A', 'stack_*.jpg')))

def flow_smear(a, L, N=9):
    """沿着形状的切线方向拖（结构张量求方向）= 笔触顺着脸的轮廓走"""
    g = a.mean(-1)
    gs = gaussian_filter(g, 2.0)
    gy, gx = np.gradient(gs)
    jxx, jyy, jxy = gaussian_filter(gx * gx, 4), gaussian_filter(gy * gy, 4), gaussian_filter(gx * gy, 4)
    th = 0.5 * np.arctan2(2 * jxy, jxx - jyy)          # 梯度方向
    tx, ty = -np.sin(th), np.cos(th)                    # 切线方向（垂直于梯度）
    H, W = g.shape
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    acc = np.zeros_like(a)
    for t in np.linspace(-.5, .5, N):
        for c in range(3):
            acc[..., c] += map_coordinates(a[..., c], [yy + ty * t * L, xx + tx * t * L], order=1, mode='nearest')
    return acc / N

def kuwahara(a, r):
    """经典 Kuwahara：每个像素取周围四个象限里"最平"的那个象限的平均色（边缘被保住，里面被抹成一块一块的色）"""
    out = np.zeros_like(a)
    H, W = a.shape[:2]
    lum = a.mean(-1)
    k = r + 1
    means, varis = [], []
    for dy, dx in ((-r // 2 - 1, -r // 2 - 1), (-r // 2 - 1, r // 2 + 1), (r // 2 + 1, -r // 2 - 1), (r // 2 + 1, r // 2 + 1)):
        m = np.stack([uniform_filter(a[..., c], k, mode='nearest') for c in range(3)], -1)
        m2 = uniform_filter(lum * lum, k, mode='nearest'); ml = uniform_filter(lum, k, mode='nearest')
        v = m2 - ml * ml
        m = np.roll(m, (-dy, -dx), axis=(0, 1)); v = np.roll(v, (-dy, -dx), axis=(0, 1))
        means.append(m); varis.append(v)
    means, varis = np.stack(means), np.stack(varis)
    idx = varis.argmin(0)
    for i in range(4):
        out += means[i] * (idx == i)[..., None]
    return out

def hsh(x, y): return (np.sin(x * 127.1 + y * 311.7) * 43758.5453) % 1.0

def oil(img, strength=1.0, L=14, r=5):
    a = np.asarray(img.convert('RGB'), dtype=np.float64) / 255.0
    H, W = a.shape[:2]
    s = flow_smear(a, L * strength)
    k = kuwahara(s, r)
    c = a * (1 - strength) + k * strength
    # 厚涂：把明度当作高度，算法线，左上打光（亮的笔脊、暗的沟）
    h = gaussian_filter(c.mean(-1), 1.2)
    gy, gx = np.gradient(h)
    shade = np.clip(0.5 + (-gx * 0.7 - gy * 0.7) * 14.0, 0, 1)
    c = c * (0.72 + 0.56 * shade)[..., None]
    # 颜色：降饱和、压暗、偏橄榄 / 暗紫红
    lum = c.mean(-1, keepdims=True)
    c = lum + (c - lum) * 0.62
    shadow, light = np.array([0.03, 0.035, 0.03]), np.array([0.86, 0.83, 0.70])
    c = shadow + (light - shadow) * np.clip(c, 0, 1) ** 1.45
    mid = np.clip(1 - np.abs(lum - 0.42) * 3, 0, 1)
    c += mid * np.array([0.07, -0.02, 0.02])
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    c += (hsh(xx * 1.3, yy * 1.3) - .5)[..., None] * 0.07                          # 纸面颗粒
    c *= (1 - 0.30 * ((xx / W - .5) ** 2 + (yy / H - .5) ** 2) * 2.2)[..., None]   # 暗角
    return Image.fromarray((np.clip(c, 0, 1) * 255).astype(np.uint8))

picks = [fs[len(fs) - 1], fs[len(fs) // 2], fs[12]]
S = 320
sheet = Image.new('RGB', (4 * (S + 8) + 8, 3 * (S + 8) + 8), (20, 16, 30))
for r_, f in enumerate(picks):
    im = Image.open(f).convert('RGB').resize((S, S), Image.LANCZOS)
    sheet.paste(im, (8, r_ * (S + 8) + 8))
    for c_, (st, L, rr) in enumerate(((1.0, 26, 8), (1.0, 16, 5), (0.8, 10, 3))):
        sheet.paste(oil(im, st, L * S / 512.0, rr), (8 + (c_ + 1) * (S + 8), r_ * (S + 8) + 8))
out = os.path.join(HERE, '..', 'outputs_standard', 'oil_preview.png')
sheet.save(out); print(os.path.abspath(out))
