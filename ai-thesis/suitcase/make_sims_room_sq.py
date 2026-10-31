# 画"模拟人生"风格的斜 45° 卧室，正方形版（给正方形的行李箱盖子用，1000x1000）。只用 PIL，不烫电脑。
# 用法：python3 make_sims_room_sq.py [输出文件名] [边长像素，默认 1000]
import math, sys
from PIL import Image, ImageDraw, ImageFont
N = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
SS = 2
RW, LD, WH = 6.0, 6.0, 4.4
S = N * 0.0885 * SS
OX, OY = N * 0.5 * SS, N * 0.04 * SS + WH * S
C30, S30 = math.cos(math.radians(30)), 0.5
def P(x, y, z):
    return (OX + (x - y) * C30 * S, OY + (x + y) * S30 * S - z * S)
OUT = (70, 48, 40)
im = Image.new('RGB', (N * SS, N * SS), (10, 10, 14))
d = ImageDraw.Draw(im)
LW = max(2, int(2.2 * SS * N / 1000))
def poly(pts3, fill, line=True):
    pts = [P(*q) for q in pts3]
    d.polygon(pts, fill=fill)
    if line:
        d.line(pts + [pts[0]], fill=OUT, width=LW, joint='curve')
def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)
def box(x, y, z, w, dd, h, col, top=None):
    top = top or shade(col, 1.18)
    poly([(x, y, z + h), (x + w, y, z + h), (x + w, y + dd, z + h), (x, y + dd, z + h)], top)
    poly([(x, y + dd, z), (x + w, y + dd, z), (x + w, y + dd, z + h), (x, y + dd, z + h)], shade(col, 0.92))
    poly([(x + w, y, z), (x + w, y + dd, z), (x + w, y + dd, z + h), (x + w, y, z + h)], shade(col, 0.72))
FA, FB = (214, 170, 120), (200, 154, 106)
for i in range(int(RW)):
    for j in range(int(LD)):
        poly([(i, j, 0), (i + 1, j, 0), (i + 1, j + 1, 0), (i, j + 1, 0)], FA if (i + j) % 2 == 0 else FB, line=False)
d.line([P(0, 0, 0), P(RW, 0, 0), P(RW, LD, 0), P(0, LD, 0), P(0, 0, 0)], fill=OUT, width=LW)
poly([(0, 0, 0), (RW, 0, 0), (RW, 0, WH), (0, 0, WH)], (247, 205, 190))
poly([(0, 0, 0), (0, LD, 0), (0, LD, WH), (0, 0, WH)], (232, 184, 172))
poly([(0, 0, 0.5), (RW, 0, 0.5), (RW, 0, 0.65), (0, 0, 0.65)], (170, 120, 96), line=False)
poly([(0, 0, 0.5), (0, LD, 0.5), (0, LD, 0.65), (0, 0, 0.65)], (150, 104, 84), line=False)
poly([(3.3, 0, 1.9), (5.4, 0, 1.9), (5.4, 0, 4.0), (3.3, 0, 4.0)], (255, 244, 220))
poly([(3.5, 0, 2.1), (5.2, 0, 2.1), (5.2, 0, 3.8), (3.5, 0, 3.8)], (150, 205, 235))
d.line([P(4.35, 0, 2.1), P(4.35, 0, 3.8)], fill=(255, 244, 220), width=LW + 1)
d.line([P(3.5, 0, 2.95), P(5.2, 0, 2.95)], fill=(255, 244, 220), width=LW + 1)
poly([(3.15, 0, 2.0), (3.65, 0, 2.0), (3.65, 0, 4.15), (3.15, 0, 4.15)], (232, 120, 120))
poly([(5.05, 0, 2.0), (5.55, 0, 2.0), (5.55, 0, 4.15), (5.05, 0, 4.15)], (232, 120, 120))
poly([(1.0, 0, 2.6), (2.4, 0, 2.6), (2.4, 0, 3.9), (1.0, 0, 3.9)], (120, 84, 70))
poly([(1.15, 0, 2.75), (2.25, 0, 2.75), (2.25, 0, 3.75), (1.15, 0, 3.75)], (170, 214, 190))
poly([(0, 1.0, 2.3), (0, 2.5, 2.3), (0, 2.5, 3.9), (0, 1.0, 3.9)], (120, 84, 70))
poly([(0, 1.15, 2.45), (0, 2.35, 2.45), (0, 2.35, 3.75), (0, 1.15, 3.75)], (190, 175, 230))
poly([(1.9, 2.6, 0.02), (4.3, 2.6, 0.02), (4.3, 5.0, 0.02), (1.9, 5.0, 0.02)], (150, 190, 170))
poly([(2.15, 2.85, 0.03), (4.05, 2.85, 0.03), (4.05, 4.75, 0.03), (2.15, 4.75, 0.03)], (190, 222, 200), line=False)
box(2.0, 0.25, 0, 0.7, 0.7, 1.0, (170, 120, 96))
box(2.15, 0.4, 1.0, 0.4, 0.4, 0.5, (255, 238, 170))
box(2.9, 0.2, 0, 2.7, 2.3, 0.8, (150, 104, 84))
box(3.0, 0.3, 0.8, 2.5, 2.1, 0.4, (120, 168, 214))
box(3.0, 0.3, 1.2, 1.2, 2.1, 0.12, (250, 226, 150))
box(5.0, 0.5, 1.2, 0.45, 0.8, 0.22, (255, 255, 255))
box(5.0, 1.4, 1.2, 0.45, 0.8, 0.22, (255, 255, 255))
box(5.6, 0.2, 0, 0.3, 2.3, 1.9, (130, 90, 72))
poly([(0.5, 3.1, 1.1), (0.5, 5.3, 1.1), (0.5, 5.3, 2.5), (0.5, 3.1, 2.5)], (120, 178, 176))
box(0.5, 3.1, 0, 1.4, 2.2, 1.1, (96, 150, 150))
d.line([P(0.5, 3.4, 1.15), P(0.5, 5.0, 1.15)], fill=OUT, width=LW)
box(1.0, 3.9, 1.1, 0.4, 0.8, 0.03, (60, 92, 92))
cx, cy, cz = 1.2, 4.2, 3.0
top, bot = P(cx, cy, cz + 0.9), P(cx, cy, cz - 0.1)
l, r = P(cx - 0.35, cy + 0.35, cz + 0.4), P(cx + 0.35, cy - 0.35, cz + 0.4)
f1 = P(cx, cy + 0.5, cz + 0.4)
d.polygon([top, l, bot], fill=(70, 200, 90)); d.polygon([top, f1, bot], fill=(110, 230, 120)); d.polygon([top, r, bot], fill=(50, 160, 70))
for a, b in ((top, l), (l, bot), (bot, r), (r, top), (top, bot)):
    d.line([a, b], fill=(20, 90, 40), width=LW)
im = im.resize((N, N), Image.LANCZOS)
d = ImageDraw.Draw(im)
try:
    F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', max(11, int(N * 0.021)))
except Exception:
    F = ImageFont.load_default()
u = N / 1000.0
if len(sys.argv) > 3 and sys.argv[3] == 'noui':
    out = sys.argv[1]; im.save(out); print('saved', out, im.size); sys.exit(0)
bars = [('Mood', 0.82), ('Comfort', 0.74), ('Privacy', 0.9)]
px, py = int(14 * u), int(N - 126 * u)
d.rounded_rectangle([px, py, px + int(236 * u), py + int(112 * u)], radius=int(10 * u), fill=(40, 52, 80), outline=(160, 190, 230), width=2)
for i, (nm, v) in enumerate(bars):
    y = py + int((14 + i * 32) * u)
    d.text((px + int(12 * u), y), nm, fill=(235, 240, 250), font=F)
    d.rectangle([px + int(96 * u), y + int(3 * u), px + int(222 * u), y + int(19 * u)], fill=(22, 30, 50))
    d.rectangle([px + int(96 * u), y + int(3 * u), px + int((96 + 126 * v) * u), y + int(19 * u)], fill=(110, 210, 120))
d.rounded_rectangle([N - int(176 * u), int(14 * u), N - int(14 * u), int(52 * u)], radius=int(10 * u), fill=(40, 52, 80), outline=(160, 190, 230), width=2)
d.text((N - int(164 * u), int(22 * u)), 'Day 1   9:41 AM', fill=(235, 240, 250), font=F)
out = sys.argv[1] if len(sys.argv) > 1 else 'bedroom_sims_sq1.png'
im.save(out)
print('saved', out, im.size)
