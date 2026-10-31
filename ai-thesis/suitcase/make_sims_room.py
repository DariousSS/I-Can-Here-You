# 画"模拟人生"风格的斜 45° 卧室，给盖子用（1600x820，和原来的线条卧室一样大）。只用 PIL，不烫电脑。
# 用法：python3 make_sims_room.py        -> 生成 bedroom_sims_1.png
import math, sys
from PIL import Image, ImageDraw, ImageFont
W, H, SS = 1600, 820, 2
S = 50.0 * SS
OX, OY = 649 * SS, 262 * SS
C30, S30 = math.cos(math.radians(30)), 0.5
def P(x, y, z):
    return (OX + (x - y) * C30 * S, OY + (x + y) * S30 * S - z * S)
OUT = (70, 48, 40)
im = Image.new('RGB', (W * SS, H * SS), (10, 10, 14))
d = ImageDraw.Draw(im)
def poly(pts3, fill, line=True):
    pts = [P(*q) for q in pts3]
    d.polygon(pts, fill=fill)
    if line:
        d.line(pts + [pts[0]], fill=OUT, width=int(2.2 * SS), joint='curve')
def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)
def box(x, y, z, w, dd, h, col, top=None):
    top = top or shade(col, 1.18)
    poly([(x, y, z + h), (x + w, y, z + h), (x + w, y + dd, z + h), (x, y + dd, z + h)], top)
    poly([(x, y + dd, z), (x + w, y + dd, z), (x + w, y + dd, z + h), (x, y + dd, z + h)], shade(col, 0.92))
    poly([(x + w, y, z), (x + w, y + dd, z), (x + w, y + dd, z + h), (x + w, y, z + h)], shade(col, 0.72))
RW, LD, WH = 14.0, 7.0, 4.6
FLOOR_A, FLOOR_B = (214, 170, 120), (200, 154, 106)
for i in range(int(RW)):
    for j in range(int(LD)):
        poly([(i, j, 0), (i + 1, j, 0), (i + 1, j + 1, 0), (i, j + 1, 0)], FLOOR_A if (i + j) % 2 == 0 else FLOOR_B, line=False)
poly([(0, 0, 0), (RW, 0, 0), (RW, LD, 0), (0, LD, 0)], None) if False else None
d.line([P(0, 0, 0), P(RW, 0, 0), P(RW, LD, 0), P(0, LD, 0), P(0, 0, 0)], fill=OUT, width=int(2.2 * SS))
WALL_R, WALL_L = (247, 205, 190), (232, 184, 172)
poly([(0, 0, 0), (RW, 0, 0), (RW, 0, WH), (0, 0, WH)], WALL_R)
poly([(0, 0, 0), (0, LD, 0), (0, LD, WH), (0, 0, WH)], WALL_L)
poly([(0, 0, 0.55), (RW, 0, 0.55), (RW, 0, 0.7), (0, 0, 0.7)], (170, 120, 96), line=False)
poly([(0, 0, 0.55), (0, LD, 0.55), (0, LD, 0.7), (0, 0, 0.7)], (150, 104, 84), line=False)
# 窗户（右墙）
poly([(2.2, 0, 1.8), (5.2, 0, 1.8), (5.2, 0, 4.0), (2.2, 0, 4.0)], (255, 244, 220))
poly([(2.4, 0, 2.0), (5.0, 0, 2.0), (5.0, 0, 3.8), (2.4, 0, 3.8)], (150, 205, 235))
d.line([P(3.7, 0, 2.0), P(3.7, 0, 3.8)], fill=(255, 244, 220), width=int(3 * SS))
d.line([P(2.4, 0, 2.9), P(5.0, 0, 2.9)], fill=(255, 244, 220), width=int(3 * SS))
poly([(2.0, 0, 1.9), (2.6, 0, 1.9), (2.6, 0, 4.2), (2.0, 0, 4.2)], (232, 120, 120))
poly([(4.8, 0, 1.9), (5.4, 0, 1.9), (5.4, 0, 4.2), (4.8, 0, 4.2)], (232, 120, 120))
# 画框
poly([(7.2, 0, 2.6), (8.6, 0, 2.6), (8.6, 0, 3.9), (7.2, 0, 3.9)], (120, 84, 70))
poly([(7.35, 0, 2.75), (8.45, 0, 2.75), (8.45, 0, 3.75), (7.35, 0, 3.75)], (170, 214, 190))
poly([(9.2, 0, 2.9), (10.4, 0, 2.9), (10.4, 0, 3.8), (9.2, 0, 3.8)], (120, 84, 70))
poly([(9.32, 0, 3.02), (10.28, 0, 3.02), (10.28, 0, 3.68), (9.32, 0, 3.68)], (250, 220, 150))
# 左墙的海报
poly([(0, 2.3, 2.2), (0, 3.9, 2.2), (0, 3.9, 3.9), (0, 2.3, 3.9)], (120, 84, 70))
poly([(0, 2.45, 2.35), (0, 3.75, 2.35), (0, 3.75, 3.75), (0, 2.45, 3.75)], (190, 175, 230))
# 地毯
rug = [(3.2, 2.4, 0.02), (7.8, 2.4, 0.02), (7.8, 5.6, 0.02), (3.2, 5.6, 0.02)]
poly(rug, (150, 190, 170))
poly([(3.7, 2.9, 0.03), (7.3, 2.9, 0.03), (7.3, 5.1, 0.03), (3.7, 5.1, 0.03)], (190, 222, 200), line=False)
# 床：床框 -> 被子 -> 枕头 -> 床头板
box(7.6, 0.25, 0, 5.2, 3.2, 0.9, (150, 104, 84))
box(7.7, 0.35, 0.9, 5.0, 3.0, 0.45, (120, 168, 214))
box(7.7, 0.35, 1.35, 1.7, 3.0, 0.14, (250, 226, 150))
box(11.6, 0.55, 1.35, 0.9, 1.1, 0.25, (255, 255, 255))
box(11.6, 1.95, 1.35, 0.9, 1.1, 0.25, (255, 255, 255))
box(12.8, 0.25, 0, 0.3, 3.2, 2.1, (130, 90, 72))
# 床头柜 + 台灯
box(13.0, 3.7, 0, 0.9, 1.1, 1.3, (170, 120, 96))
box(13.3, 4.0, 1.3, 0.3, 0.4, 0.2, (240, 210, 120))
box(13.15, 3.85, 1.5, 0.6, 0.6, 0.55, (255, 238, 170))
# 衣柜 / 书架（左墙边）
box(0.15, 0.4, 0, 1.0, 1.8, 3.0, (176, 132, 98))
# 行李箱（我）：开着的，在左边
box(1.6, 3.6, 0, 2.6, 1.7, 1.2, (96, 150, 150))
poly([(1.6, 3.6, 1.2), (4.2, 3.6, 1.2), (4.2, 3.6, 2.5), (1.6, 3.6, 2.5)], (120, 178, 176))
d.line([P(1.6, 3.6, 1.35), P(4.2, 3.6, 1.35)], fill=OUT, width=int(2.2 * SS))
box(2.5, 3.9, 1.2, 0.7, 0.4, 0.02, (60, 92, 92))
# 头上的绿色小钻石（plumbbob）
cx, cy, cz = 2.9, 4.45, 3.3
top, bot = P(cx, cy, cz + 0.9), P(cx, cy, cz - 0.1)
l, r = P(cx - 0.35, cy + 0.35, cz + 0.4), P(cx + 0.35, cy - 0.35, cz + 0.4)
f1, f2 = P(cx, cy + 0.5, cz + 0.4), P(cx + 0.5, cy, cz + 0.4)
d.polygon([top, l, bot], fill=(70, 200, 90)); d.polygon([top, f1, bot], fill=(110, 230, 120)); d.polygon([top, r, bot], fill=(50, 160, 70))
for a, b in ((top, l), (l, bot), (bot, r), (r, top), (top, bot)):
    d.line([a, b], fill=(20, 90, 40), width=int(2 * SS))
im = im.resize((W, H), Image.LANCZOS)
d = ImageDraw.Draw(im)
try:
    F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 17)
except Exception:
    F = ImageFont.load_default()
bars = [('Mood', 0.82, (110, 210, 120)), ('Comfort', 0.74, (110, 210, 120)), ('Privacy', 0.9, (110, 210, 120))]
px, py = 24, H - 128
d.rounded_rectangle([px, py, px + 250, py + 108], radius=10, fill=(40, 52, 80), outline=(160, 190, 230), width=2)
for i, (nm, v, c) in enumerate(bars):
    y = py + 14 + i * 30
    d.text((px + 12, y), nm, fill=(235, 240, 250), font=F)
    d.rectangle([px + 100, y + 3, px + 232, y + 19], fill=(22, 30, 50))
    d.rectangle([px + 100, y + 3, px + 100 + int(132 * v), y + 19], fill=c)
d.rounded_rectangle([W - 190, 20, W - 24, 58], radius=10, fill=(40, 52, 80), outline=(160, 190, 230), width=2)
d.text((W - 176, 28), 'Day 1   9:41 AM', fill=(235, 240, 250), font=F)
out = sys.argv[1] if len(sys.argv) > 1 else 'bedroom_sims_1.png'
im.save(out)
print('saved', out, im.size)
