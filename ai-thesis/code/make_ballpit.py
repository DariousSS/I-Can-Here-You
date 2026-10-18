"""生成儿童乐园"海洋球池"透明图（RGBA）：底部一堆糖果色球 + 边缘几颗飘着的球。
运行：python make_ballpit.py [宽 高]    输出：../td_live/ballpit/ballpit.png
"""
import os
import sys
import numpy as np
from PIL import Image

W = int(sys.argv[1]) if len(sys.argv) > 2 else 1920
H = int(sys.argv[2]) if len(sys.argv) > 2 else 1080
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "td_live", "ballpit", "ballpit.png")
PAL = [(255, 99, 132), (255, 214, 10), (64, 156, 255), (80, 205, 140), (178, 120, 255), (255, 159, 64), (255, 140, 200)]
rng = np.random.RandomState(11)
canvas = np.zeros((H, W, 4), dtype=np.float32)


def draw_ball(cx, cy, r, col, alpha=1.0):
    x0, x1 = max(0, int(cx - r - 2)), min(W, int(cx + r + 3))
    y0, y1 = max(0, int(cy - r - 2)), min(H, int(cy + r + 3))
    if x1 <= x0 or y1 <= y0:
        return
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = (xx - cx) / r, (yy - cy) / r
    d2 = dx * dx + dy * dy
    inside = np.clip((1.0 - np.sqrt(d2)) * r, 0, 1)                    # 抗锯齿边缘
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    light = np.clip((-dx * 0.45 - dy * 0.6 + nz * 0.65), 0, 1)           # 左上角打光
    base = np.array(col, dtype=np.float32) / 255.0
    shade = 0.62 + 0.55 * light
    rgb = base[None, None, :] * shade[..., None]
    hl = np.exp(-(((dx + 0.35) ** 2 + (dy + 0.42) ** 2) / 0.018))        # 高光
    rgb = rgb + (hl * 0.75)[..., None]
    rim = np.clip((np.sqrt(d2) - 0.86) / 0.14, 0, 1) ** 2                # 边缘略暗，更立体
    rgb = rgb * (1 - 0.25 * rim)[..., None]
    a = (inside * alpha)[..., None]
    patch = canvas[y0:y1, x0:x1]
    patch[..., :3] = rgb * a + patch[..., :3] * (1 - a)
    patch[..., 3:4] = a + patch[..., 3:4] * (1 - a)


R = H * 0.065
balls = []
step = R * 1.75
cols = int(W / step) + 3
for i in range(cols):
    x = i * step - R
    surf = H * 0.80 - (np.sin(i * 0.55) * 0.5 + np.sin(i * 1.3 + 1.0) * 0.5) * R * 1.2 - 0.9 * R * (1 + np.cos(i / cols * 2 * np.pi)) * 0.35
    k = 0
    y = surf
    while y < H + R:
        balls.append((x + rng.uniform(-R * 0.25, R * 0.25) + (R * 0.85 if k % 2 else 0), y + rng.uniform(-R * 0.2, R * 0.2), R * rng.uniform(0.92, 1.08), PAL[rng.randint(len(PAL))]))
        y += step * 0.85
        k += 1
balls.sort(key=lambda b: b[1])                                           # 先画靠上（靠后）的，再画靠下的
for cx, cy, r, col in balls:
    draw_ball(cx, cy, r, col)
for cx, cy, r in [(W * 0.07, H * 0.38, R * 1.1), (W * 0.93, H * 0.30, R * 0.9), (W * 0.05, H * 0.58, R * 0.7), (W * 0.95, H * 0.55, R * 1.0)]:
    draw_ball(cx, cy, r, PAL[rng.randint(len(PAL))], 0.95)               # 边缘飘着的球（别挡住中间）
os.makedirs(os.path.dirname(OUT), exist_ok=True)
a_ = canvas[..., 3:4]
canvas[..., :3] = np.where(a_ > 1e-4, canvas[..., :3] / np.maximum(a_, 1e-4), 0.0)     # 还原成直通 alpha，边缘不发黑
Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8), "RGBA").save(OUT)
print("done", len(balls), "balls ->", os.path.abspath(OUT))
