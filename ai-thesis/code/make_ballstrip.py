"""生成"长条形"海洋球动画（3:1，1280x427，30fps，约 3.2 秒）：球从整条底边各处冒出来，把长方形填满，再掉出去。
运行：python make_ballstrip.py     输出：../td_live/ballpit/seq_strip/ball_0000.png ...
"""
import os
import numpy as np
from PIL import Image

W, H, FPS, DUR = 1280, 427, 30, 3.2
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "td_live", "ballpit", "seq_strip")
os.makedirs(D, exist_ok=True)
PAL = [(255, 99, 132), (255, 214, 10), (64, 156, 255), (80, 205, 140), (178, 120, 255), (255, 159, 64), (255, 140, 200)]
rng = np.random.RandomState(9)
_cache = {}


def sprite(ci, r):
    key = (ci, int(round(r / 3.0)))
    if key in _cache:
        return _cache[key]
    R = key[1] * 3.0
    n = int(R * 2 + 6)
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    c = (n - 1) / 2.0
    dx, dy = (xx - c) / R, (yy - c) / R
    d2 = dx * dx + dy * dy
    a = np.clip((1.0 - np.sqrt(d2)) * R, 0, 1)
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    light = np.clip(-dx * 0.45 - dy * 0.6 + nz * 0.65, 0, 1)
    base = np.array(PAL[ci], dtype=np.float32) / 255.0
    rgb = base[None, None, :] * (0.62 + 0.55 * light)[..., None]
    rgb = rgb + (np.exp(-(((dx + 0.35) ** 2 + (dy + 0.42) ** 2) / 0.018)) * 0.75)[..., None]
    rim = np.clip((np.sqrt(d2) - 0.86) / 0.14, 0, 1) ** 2
    rgb = np.clip(rgb * (1 - 0.25 * rim)[..., None], 0, 1)
    _cache[key] = (rgb, a, n)
    return _cache[key]


N = 260
G = 2.3
balls = []
for i in range(N):
    balls.append({
        "ts": 1.5 * (rng.rand() ** 1.4),                       # 前面冒得密，后面稀
        "ci": rng.randint(len(PAL)),
        "x0": rng.uniform(0.02, 0.98),                        # 起点：整条底边各处
        "vx": rng.uniform(-0.18, 0.18),
        "vy": rng.uniform(0.85, 1.75),                        # 向上的初速度（高度/秒）
        "r": rng.uniform(0.11, 0.19),                         # 半径（占条高）
        "grow": rng.uniform(0.0, 0.25),
    })

nf = int(DUR * FPS)
for f in range(nf):
    t = f / FPS
    canvas = np.zeros((H, W, 4), dtype=np.float32)
    live = []
    for b in balls:
        u = t - b["ts"]
        if u < 0:
            continue
        x = b["x0"] + b["vx"] * u
        y = 1.12 - (b["vy"] * u - 0.5 * G * u * u)
        r = (b["r"] + b["grow"] * u * 0.1) * H
        if y > 1.3 or x < -0.1 or x > 1.1:
            continue
        live.append((y, r, x * W, y * H, b["ci"]))
    live.sort()
    for _, r, cx, cy, ci in live:
        rgb, a, n = sprite(ci, r)
        x0, y0 = int(cx - n / 2), int(cy - n / 2)
        sx0, sy0 = max(0, -x0), max(0, -y0)
        ex, ey = min(n, W - x0), min(n, H - y0)
        if ex <= sx0 or ey <= sy0:
            continue
        sub = canvas[y0 + sy0:y0 + ey, x0 + sx0:x0 + ex]
        aa = a[sy0:ey, sx0:ex, None]
        sub[..., :3] = rgb[sy0:ey, sx0:ex] * aa + sub[..., :3] * (1 - aa)
        sub[..., 3:4] = aa + sub[..., 3:4] * (1 - aa)
    a_ = canvas[..., 3:4]
    canvas[..., :3] = np.where(a_ > 1e-4, canvas[..., :3] / np.maximum(a_, 1e-4), 0.0)
    Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(D, "ball_%04d.png" % f))
print("frames:", nf, "->", os.path.abspath(D))
