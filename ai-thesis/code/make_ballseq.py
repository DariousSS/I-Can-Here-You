"""生成"海洋球喷出来"的透明帧动画（1280x720，30fps，约 3.2 秒）+ 对应音效。
球从屏幕下方中间喷出，向两边飞，越飞越大（朝观众飞来），最后全部掉出屏幕。
运行：python make_ballseq.py     输出：../td_live/ballpit/seq/ball_0000.png ...  和 ball_sfx.wav
"""
import os
import wave
import numpy as np
from PIL import Image
from scipy.signal import butter, lfilter

W, H, FPS, DUR = 1280, 720, 30, 3.2
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "td_live", "ballpit")
SEQ = os.path.join(D, "seq")
os.makedirs(SEQ, exist_ok=True)
PAL = [(255, 99, 132), (255, 214, 10), (64, 156, 255), (80, 205, 140), (178, 120, 255), (255, 159, 64), (255, 140, 200)]
rng = np.random.RandomState(5)

# ---------- 球的外观（带缓存，半径量化到 3 像素）----------
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


# ---------- 球的运动 ----------
N = 170
balls = []
for i in range(N):
    ts = 1.9 * (rng.rand() ** 1.7)                        # 前面喷得密，后面越来越稀
    side = rng.choice([-1, 1])
    balls.append({
        "ts": ts, "ci": rng.randint(len(PAL)),
        "x0": 0.5 + rng.uniform(-0.12, 0.12),             # 起点（占宽度的比例）
        "vx": side * rng.uniform(0.12, 0.85) / 1.0,       # 横向速度（宽度/秒）
        "vy": rng.uniform(0.55, 1.20),                    # 向上的初速度（高度/秒）
        "r0": rng.uniform(0.040, 0.062),                  # 起始半径（占高度比例，远处小）
        "grow": rng.uniform(0.9, 1.7),                    # 变大的速度（朝观众飞来）
    })
G = 2.0                                                   # 重力（高度/秒²）

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
        y = 1.04 - (b["vy"] * u - 0.5 * G * u * u)         # 1.04 = 屏幕下方一点点
        r = (b["r0"] + b["grow"] * u * 0.055) * H
        if x < -0.15 or x > 1.15 or y > 1.2:
            continue
        live.append((r, x * W, y * H, b["ci"]))
    live.sort()                                            # 小的（远的）先画
    for r, cx, cy, ci in live:
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
    Image.fromarray((np.clip(canvas, 0, 1) * 255).astype(np.uint8), "RGBA").save(os.path.join(SEQ, "ball_%04d.png" % f))
print("frames:", nf)

# ---------- 音效 ----------
SR = 44100
total = int(SR * (DUR + 0.4))
y = np.zeros(total, dtype=np.float64)


def add(sig, t0):
    i = int(t0 * SR)
    j = min(total, i + len(sig))
    if i < total:
        y[i:j] += sig[:j - i]


def tock(freq, dur, amp):                                  # 塑料球"嗒"：带通噪声 + 很短的低频体
    n = int(SR * dur)
    tt = np.arange(n) / SR
    noise = np.random.RandomState(int(freq * 1000) % 99991).randn(n)
    bb, aa = butter(2, [max(200.0, freq * 0.6) / (SR / 2), min(9000.0, freq * 1.6) / (SR / 2)], btype="band")
    nz = lfilter(bb, aa, noise) * np.exp(-tt * 70)
    body = np.sin(2 * np.pi * freq * 0.5 * tt) * np.exp(-tt * 45)
    return amp * (nz * 1.2 + body * 0.5)


for b in balls:                                            # 每个球在空中最高点后落到"池面"附近弹几下
    u_land = 2 * b["vy"] / G
    t_hit = b["ts"] + u_land * rng.uniform(0.85, 1.0)
    if t_hit < DUR + 0.2:
        for k in range(rng.randint(1, 4)):
            add(tock(rng.uniform(900, 2800), 0.12, rng.uniform(0.05, 0.14) / (k + 1)), t_hit + k * rng.uniform(0.08, 0.2))

# 老虎机"中奖"铃声：上行琶音，故意走音 + 颤音，更诡异
for k, (semi, t0) in enumerate([(0, 0.00), (4, 0.10), (7, 0.20), (12, 0.30), (16, 0.42), (19, 0.54), (24, 0.68)]):
    f0 = 523.25 * 2 ** ((semi - 0.35) / 12.0)              # -0.35 个半音：略微走音
    n = int(SR * 1.1)
    tt = np.arange(n) / SR
    env = np.exp(-tt * 3.2) * (1 - np.exp(-tt * 400))
    trem = 1 + 0.25 * np.sin(2 * np.pi * 6.5 * tt)
    bell = (np.sin(2 * np.pi * f0 * tt) + 0.5 * np.sin(2 * np.pi * f0 * 2.76 * tt) + 0.25 * np.sin(2 * np.pi * f0 * 5.4 * tt)) * env * trem
    add(0.16 * bell, t0)

y = y / max(1e-6, np.abs(y).max()) * 0.9
with wave.open(os.path.join(D, "ball_sfx.wav"), "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(y, -1, 1) * 32767).astype("<i2").tobytes())
print("sfx done")
