"""翅膀上的小眼睛：用 numpy 画一张预览（叠在 wings_pixel_base.png 上），同时把眼睛的位置表写进 GLSL 着色器 angel_eyes_shader.glsl。
眼睛位置表 EYES：左翅 8 只 (x, y, a)，x/y 是翅膀图(1344x1344)里的像素坐标（y 向下），a 是眼睛的半宽；右翅是左翅左右镜像。
运行：python make_angel_eyes.py   -> 预览 ../outputs_standard/angel_eyes_preview.png ，着色器 angel_eyes_shader.glsl
"""
import math, os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = 1344.0
CX, CY = 672.0, 624.0          # 中央大眼睛（angel.json 里的 eye_cx, eye_cy，y 向下）
LEFT = [(412, 500, 60), (255, 592, 76), (165, 716, 68), (352, 742, 60), (405, 930, 58), (300, 1075, 52), (225, 870, 60), (398, 392, 50), (110, 560, 46), (500, 860, 42), (360, 1185, 40)]
EYES = []
for (x, y, a) in LEFT:
    EYES.append((x, y, a))
for (x, y, a) in LEFT:
    EYES.append((IMG - x, y, a))
ASPECT = 0.50                  # 眼睛半高 / 半宽


def ang_of(x, y):
    """眼睛的倾斜角：沿着从中央大眼睛向外的放射方向（y 向上坐标）。"""
    return math.atan2(-(y - CY), x - CX)


def render(Tx, Ty, size=1344, blink_t=0.0, line=6.0, alert=1.0):
    """像素着色器的 numpy 版本。Tx, Ty：视线目标（翅膀图像素坐标，y 向下）。返回 RGBA。"""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    s = size / IMG
    px, py = xx / s + 0.5 / s, (size - 1 - yy) / s + 0.5 / s      # 图像坐标，y 向上
    px, py = (np.floor(px / 6.0) + 0.5) * 6.0, (np.floor(py / 6.0) + 0.5) * 6.0    # 对齐翅膀的 6x6 像素格（像素风）
    out = np.zeros((size, size, 4))
    for i, (ex, ey, a) in enumerate(EYES):
        eyu = IMG - ey
        ang = ang_of(ex, ey)
        ca, sa = math.cos(ang), math.sin(ang)
        dx, dy = px - ex, py - eyu
        lx, ly = dx * ca + dy * sa, -dx * sa + dy * ca
        b = a * ASPECT
        ph = (i * 1.7) % 5.0
        t = (blink_t + ph) % 5.5
        bl = 1.0 - (max(0.0, 1.0 - abs(t - 0.1) / 0.12) if t < 0.3 else 0.0)
        ti = 0.12 + 0.70 * ((i * 0.618) % 1.0)
        opn = float(np.clip((alert - ti) / 0.16, 0, 1)); opn = opn * opn * (3 - 2 * opn)
        h = b * max(0.10, bl) * opn
        sx = np.clip(lx / a, -1, 1)
        hh = h * (1 - sx * sx)
        if opn < 0.02:
            lid = -b * 0.40 * (1 - sx * sx)
            out[(np.abs(lx) < a) & (np.abs(ly - lid) < line / 2)] = (1, 1, 1, 1)
            continue
        inside = (np.abs(lx) < a) & (np.abs(ly) < hh)
        edge = (np.abs(lx) < a * 1.02) & (np.abs(np.abs(ly) - hh) < line / 2) & (np.abs(lx) < a)
        tgx, tgy = Tx - ex, (IMG - Ty) - eyu
        d = math.hypot(tgx, tgy) + 1e-6
        nx, ny = tgx / d, tgy / d
        k = min(1.0, d / 500.0)
        lnx, lny = nx * ca + ny * sa, -nx * sa + ny * ca
        pcx, pcy = lnx * k * a * 0.38, lny * k * b * 0.40
        rr = b * 0.60
        dd = np.hypot(lx - pcx, ly - pcy)
        ring = inside & (np.abs(dd - rr) < line / 2)
        pup = inside & (dd < max(rr * 0.42, 7.0))
        out[inside] = (0, 0, 0, 1)
        out[ring | pup | edge] = (1, 1, 1, 1)
    return out


def write_shader():
    rows = ",\n".join("    vec4(%.1f, %.1f, %.1f, %.5f)" % (x, IMG - y, a, ang_of(x, y)) for (x, y, a) in EYES)
    src = open(os.path.join(HERE, "angel_eyes_shader.template.glsl"), encoding="utf-8").read()
    src = src.replace("//__EYES__", rows).replace("//__N__", str(len(EYES)))
    with open(os.path.join(HERE, "angel_eyes_shader.glsl"), "w", encoding="utf-8") as f:
        f.write(src)
    print("着色器已写入 angel_eyes_shader.glsl，眼睛", len(EYES), "只")


if __name__ == "__main__":
    base = Image.open(os.path.join(HERE, "..", "assets", "angel", "wings_pixel_base.png")).convert("RGBA")
    bg = Image.new("RGBA", base.size, (30, 24, 50, 255))
    bg.alpha_composite(base)
    tiles = []
    for al in (0.0, 0.55, 1.0):
        e = Image.fromarray((render(300, 150, alert=al) * 255).astype(np.uint8), "RGBA")
        t = bg.copy()
        t.alpha_composite(e)
        tiles.append(t.convert("RGB").resize((560, 560), Image.LANCZOS))
    sheet = Image.new("RGB", (560 * 3 + 20, 560), (20, 16, 30))
    for j, t in enumerate(tiles):
        sheet.paste(t, (j * 570, 0))
    out = os.path.join(HERE, "..", "outputs_standard", "angel_eyes_preview.png")
    sheet.save(out)
    print(os.path.abspath(out))
    write_shader()
