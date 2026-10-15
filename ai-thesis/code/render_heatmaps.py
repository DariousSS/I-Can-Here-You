"""
把已保存的注意力数据画成图（不需要重新让模型画画）。

默认画"纯热力图"：背景不垫最终图，只看注意力本身。
  - 总览图里最左边那一列放最终图，只是给你对照用，热力图本身是干净的
  - 配色：暗紫(几乎没听) -> 橙 -> 浅黄(听得最多)；每张图单独拉伸到 0~1
  - 热力图本来只有 64x64 个格子，这里用平滑放大，所以看起来是柔和的

用法：
  python render_heatmaps.py outputs_attention/某个运行文件夹
  python render_heatmaps.py --all                    # 把所有运行都重新画一遍
  python render_heatmaps.py --all --overlay          # 另外画一份"叠在最终图上"的旧样式
"""
import argparse
import glob
import json
import os
import re

import numpy as np
from PIL import Image, ImageDraw

OUT_ROOT = "/Users/shanzeyang/Desktop/I can Here You/ai-thesis/outputs_attention"

# 近似 inferno 配色：0 -> 黑紫，1 -> 浅黄
_STOPS = np.array([0.00, 0.25, 0.50, 0.75, 1.00])
_COLORS = np.array([[0.00, 0.00, 0.02],
                    [0.34, 0.06, 0.43],
                    [0.73, 0.21, 0.33],
                    [0.98, 0.55, 0.04],
                    [0.99, 1.00, 0.64]])


def colorize(m01):
    out = np.stack([np.interp(m01, _STOPS, _COLORS[:, c]) for c in range(3)], axis=-1)
    return (out * 255).astype(np.uint8)


def slug(text, n=50):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:n]


def heat_image(m01, size, final=None, overlay=False):
    heat = Image.fromarray(colorize(m01)).resize((size, size), Image.BICUBIC)
    if not overlay:
        return heat
    base = final.convert("L").convert("RGB").resize((size, size))
    return Image.blend(base, heat, 0.65)


def render_run(run_dir, overlay=False):
    data = np.load(os.path.join(run_dir, "data", "attention_maps.npz"))
    meta = {"timesteps", "seed", "prompt"}
    words = [k for k in data.files if k not in meta]
    timesteps = [int(t) for t in data["timesteps"]]
    rounds = len(timesteps)
    final = Image.open(os.path.join(run_dir, "final.png")).convert("RGB")
    suffix = "_overlay" if overlay else ""

    # ----- 总览图：每行一个词，每列一轮 -----
    show = sorted(set(np.linspace(0, rounds - 1, 6).round().astype(int).tolist()))
    CELL, HEAD, LEFT, FOOT = 256, 24, 170, 34
    W = LEFT + CELL * (1 + len(show))
    H = HEAD + CELL * len(words) + FOOT
    sheet = Image.new("RGB", (W, H), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    d.text((LEFT + 8, 6), "final image (reference)", fill=(255, 255, 255))
    for k, s in enumerate(show):
        d.text((LEFT + CELL * (k + 1) + 8, 6), f"round {s + 1}/{rounds} (t={timesteps[s]})", fill=(255, 255, 255))
    for r, w in enumerate(words):
        y = HEAD + CELL * r
        d.text((8, y + CELL // 2), w, fill=(255, 255, 255))
        sheet.paste(final.resize((CELL, CELL)), (LEFT, y))
        for k, s in enumerate(show):
            sheet.paste(heat_image(data[w][s], CELL, final, overlay), (LEFT + CELL * (k + 1), y))
    # 图例
    gy = HEAD + CELL * len(words) + 10
    bar = colorize(np.tile(np.linspace(0, 1, 300), (12, 1)))
    sheet.paste(Image.fromarray(bar), (LEFT, gy))
    d.text((LEFT + 310, gy), "dark = not listening   bright = listening most   (each map is scaled 0-1 on its own)",
           fill=(200, 200, 200))
    sheet.save(os.path.join(run_dir, f"attention_overview{suffix}.png"))

    # ----- 小人书：每个词一个 GIF，每帧一轮 -----
    fb = os.path.join(run_dir, f"flipbooks{suffix}")
    os.makedirs(fb, exist_ok=True)
    for w in words:
        frames = []
        for s in range(rounds):
            im = heat_image(data[w][s], 384, final, overlay)
            ImageDraw.Draw(im).text((8, 6), f"{w}  round {s + 1}/{rounds}  t={timesteps[s]}", fill=(255, 255, 255))
            frames.append(im)
        frames[0].save(os.path.join(fb, f"{slug(w)}.gif"), save_all=True,
                       append_images=frames[1:], duration=200, loop=0)
    render_share(run_dir)
    return words


LINE_COLORS = [(255, 99, 71), (80, 200, 255), (140, 230, 120), (240, 200, 60),
               (200, 130, 255), (255, 160, 200), (120, 220, 220), (220, 160, 100)]


def render_share(run_dir):
    """谁抢到的注意力多：每轮每张词卡分到的比例（不算开头卡；真正的词加起来 = 100%）。"""
    path = os.path.join(run_dir, "data", "attention_share.json")
    if not os.path.exists(path):
        return
    info = json.load(open(path, encoding="utf-8"))
    tokens = info["tokens"]
    n = info["rounds"]
    W, H, L, R, T, B = 900, 460, 60, 210, 40, 40
    img = Image.new("RGB", (W, H), (20, 20, 20))
    d = ImageDraw.Draw(img)
    d.text((L, 10), "who gets the attention: share of each word card per round "
                    "(start card excluded; real words add up to 100%)", fill=(230, 230, 230))
    d.rectangle([L, T, W - R, H - B], outline=(90, 90, 90))
    top = max(0.1, max(max(v) for v in tokens.values()) * 1.1)
    for frac in (0, 0.25, 0.5, 0.75, 1):
        y = H - B - frac * (H - B - T)
        d.line([(L, y), (W - R, y)], fill=(40, 40, 40))
        d.text((8, y - 6), f"{top * frac * 100:.0f}%", fill=(160, 160, 160))
    for i, (name, v) in enumerate(tokens.items()):
        col = LINE_COLORS[i % len(LINE_COLORS)]
        pts = [(L + k / (n - 1) * (W - R - L), H - B - v[k] / top * (H - B - T)) for k in range(n)]
        d.line(pts, fill=col, width=3)
        d.text((W - R + 12, T + 18 * i), f"{name.split(':', 1)[1]:<12} avg {sum(v) / n * 100:4.1f}%", fill=col)
    start = sum(info["start_card"]) / n
    d.text((W - R + 12, H - B - 30), f"start card eats {start * 100:.0f}%", fill=(150, 150, 150))
    d.text((W - R + 12, H - B - 14), "of ALL attention", fill=(150, 150, 150))
    if info.get("erase"):
        d.text((W - R + 12, T + 18 * len(tokens) + 10),
               f"erased '{info['erase']}' {info['erase_level'] * 100:.0f}%", fill=(255, 80, 80))
        d.text((W - R + 12, T + 18 * len(tokens) + 26), "(numbers = before erasing)", fill=(255, 80, 80))
    d.text((L, H - B + 8), "round 1 (early, noisy)", fill=(160, 160, 160))
    d.text((W - R - 110, H - B + 8), f"round {n} (late)", fill=(160, 160, 160))
    img.save(os.path.join(run_dir, "attention_share.png"))


def render_erase_strip(out_root, prompt, seed, erase, levels, folders):
    """擦词对比：同一种子，从不擦到全擦，最终图排成一排。"""
    cells = [(lv, os.path.join(out_root, f, "final.png")) for lv, f in zip(levels, folders)]
    cells = [(lv, p) for lv, p in cells if os.path.exists(p)]
    if not cells:
        return None
    C, HEAD = 320, 50
    sheet = Image.new("RGB", (C * len(cells), C + HEAD), (12, 12, 12))
    d = ImageDraw.Draw(sheet)
    d.text((8, 6), f"prompt: {prompt}    erasing: '{erase}'    seed {seed}", fill=(255, 255, 255))
    for k, (lv, p) in enumerate(cells):
        d.text((C * k + 8, 28), "original" if lv == 0 else f"'{erase}' erased {lv * 100:.0f}%",
               fill=(255, 220, 120) if lv == 0 else (255, 120, 120))
        sheet.paste(Image.open(p).convert("RGB").resize((C, C)), (C * k, HEAD))
    out_dir = os.path.join(out_root, "_erase")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{slug(prompt, 40)}_erase-{slug(erase, 20)}_seed{seed}.png")
    sheet.save(path)
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", nargs="?", help="某次运行的文件夹")
    ap.add_argument("--all", action="store_true", help="处理 outputs_attention 下所有运行")
    ap.add_argument("--overlay", action="store_true", help="叠在最终图上（旧样式），文件名带 _overlay")
    a = ap.parse_args()
    if a.all:
        runs = sorted(os.path.dirname(os.path.dirname(p))
                      for p in glob.glob(os.path.join(OUT_ROOT, "*", "data", "attention_maps.npz")))
    elif a.run_dir:
        runs = [a.run_dir]
    else:
        ap.error("请给一个运行文件夹，或使用 --all")
    for r in runs:
        w = render_run(r, overlay=a.overlay)
        print(f"已画好: {os.path.basename(r)}  词: {w}")
