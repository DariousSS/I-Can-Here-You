"""画"像素风线框天使"（只有白色勾线，里面透明）：一对垂坠的羽翼 + 中间一只杏仁眼。瞳孔是单独一张图，动画里会移动。
输出：assets/angel/wings_pixel_base.png（线框翅膀+眼睛轮廓+虹膜圈）、pupil_pixel.png（瞳孔）、angel.json 里的 pixel 段。
运行：python make_angel_line.py
"""
import os, math, json
import numpy as np
from PIL import Image, ImageDraw

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "angel")
os.chdir(D)
G = 224            # 逻辑像素网格
PX = 6             # 每个逻辑像素放大成 6x6（最近邻，保持方块感）
W = (255, 255, 255, 255)
grid = np.zeros((G, G, 4), dtype=np.uint8)


def put(x, y):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < G and 0 <= y < G:
        grid[y, x] = W


def seg(p0, p1):
    x0, y0 = int(round(p0[0])), int(round(p0[1]))
    x1, y1 = int(round(p1[0])), int(round(p1[1]))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        put(x0, y0)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def quad(p0, p1, p2, n=40):
    pts = [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]
    for a, b in zip(pts, pts[1:]):
        seg(a, b)


def leaf(base, ang_deg, length, width):
    """一片羽毛的轮廓：从 base 出发朝 ang_deg 方向（屏幕上逆时针为正）、长 length 的尖叶形。"""
    a = math.radians(ang_deg)
    ux, uy = math.cos(a), -math.sin(a)
    nx, ny = -uy, ux
    tip = (base[0] + ux * length, base[1] + uy * length)
    mid = (base[0] + ux * length * 0.45, base[1] + uy * length * 0.45)
    quad(base, (mid[0] + nx * width * 1.9, mid[1] + ny * width * 1.9), tip)
    quad(base, (mid[0] - nx * width * 1.9, mid[1] - ny * width * 1.9), tip)


EC = (112.0, 104.0)     # 眼睛中心
# ---------- 右翼（左翼是它的镜像）----------
def cubic(p0, p1, p2, p3, n=60):
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 3 * p0[0] + 3 * (1 - t) ** 2 * t * p1[0] + 3 * (1 - t) * t * t * p2[0] + t ** 3 * p3[0],
                    (1 - t) ** 3 * p0[1] + 3 * (1 - t) ** 2 * t * p1[1] + 3 * (1 - t) * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def poly(pts):
    for u, v in zip(pts, pts[1:]):
        seg(u, v)


def right_wing():
    # 第一排：长飞羽，向右下垂坠
    piv = (128.0, 100.0)
    n = 9
    for i in range(n):
        ang = -82 + i * (92.0 / (n - 1))
        L = 108 - 26 * (i / (n - 1)) ** 1.2
        leaf(piv, ang, L, 5.6)
    # 第二排：次级飞羽
    piv2 = (130.0, 92.0)
    for i in range(7):
        ang = -55 + i * (100.0 / 6)
        leaf(piv2, ang, 66 - 12 * (i / 6.0), 5.0)
    # 第三排：覆羽（短，像毛茸茸的肩膀）
    piv3 = (132.0, 88.0)
    for i in range(8):
        ang = -10 + i * (82.0 / 7)
        leaf(piv3, ang, 34 - 4 * (i / 7.0), 4.4)
    # 肩膀的外轮廓弧线
    quad((126, 96), (140, 56), (176, 34))
    quad((176, 34), (194, 30), (200, 44))


right_wing()
right = grid.copy()
grid[:] = 0
left = right[:, ::-1].copy()                       # 左翼 = 右翼镜像
grid = np.maximum(right, left)
# 把中间一块清空，给眼睛留位置
for y in range(G):
    for x in range(G):
        if ((x - EC[0]) / 40.0) ** 2 + ((y - EC[1]) / 22.0) ** 2 < 1.0:
            grid[y, x] = 0
# ---------- 眼睛：杏仁形外轮廓 + 虹膜圈 ----------
quad((84, 104), (112, 80), (140, 104))
quad((84, 104), (112, 128), (140, 104))
for k in range(360):                               # 虹膜圈（圆）
    a = math.radians(k)
    put(EC[0] + 13 * math.cos(a), EC[1] + 13 * math.sin(a))
base = Image.fromarray(grid, 'RGBA').resize((G * PX, G * PX), Image.NEAREST)
base.save('wings_pixel_base.png')
# ---------- 瞳孔（单独一张，会动）：白色实心圆盘 + 右上一个小黑点当高光 ----------
pr = 6
ps = Image.new('RGBA', (2 * pr + 3, 2 * pr + 3), (0, 0, 0, 0))
pa = np.zeros((ps.height, ps.width, 4), dtype=np.uint8)
c0 = pr + 1
for y in range(ps.height):
    for x in range(ps.width):
        if (x - c0) ** 2 + (y - c0) ** 2 <= pr * pr + 1:
            pa[y, x] = W
for (hx, hy) in ((c0 + 2, c0 - 3), (c0 + 3, c0 - 3), (c0 + 2, c0 - 2), (c0 + 3, c0 - 2)):
    pa[hy, hx] = (0, 0, 0, 0)                      # 高光：镂空的小方块
pupil = Image.fromarray(pa, 'RGBA').resize((ps.width * PX, ps.height * PX), Image.NEAREST)
pupil.save('pupil_pixel.png')
# ---------- 瞳孔能走的范围（杏仁眼开口内）----------
hwid, hhei = 30.0, 17.0
def inside(x, y):
    t = (x - EC[0]) / hwid
    return abs(t) < 1 and abs(y - EC[1]) <= hhei * (1 - t * t) ** 0.8
rng = []
Rp = pr + 1.5
for deg in range(0, 360, 15):
    ca, sa = math.cos(math.radians(deg)), -math.sin(math.radians(deg))
    best = 0.0
    for r in np.arange(0, 40, 0.25):
        px_, py_ = EC[0] + ca * r, EC[1] + sa * r
        if all(inside(px_ + Rp * math.cos(math.radians(g)), py_ + Rp * math.sin(math.radians(g))) for g in range(0, 360, 20)):
            best = float(r)
        else:
            break
    rng.append(round(best * PX, 1))                # 换成输出像素
meta = json.load(open('angel.json'))
meta['pixel_photo_backup'] = meta.get('pixel')
meta['pixel'] = {'w': G * PX, 'h': G * PX, 'eye_cx': EC[0] * PX, 'eye_cy': EC[1] * PX, 'pupil_r': pr * PX, 'pupil_w': pupil.width, 'pupil_h': pupil.height, 'range_deg_step': 15, 'range': rng}
json.dump(meta, open('angel.json', 'w'))
# 预览
bg = Image.new('RGBA', base.size, (12, 10, 20, 255))
bg.alpha_composite(base)
for (ox, oy) in ((0, 0),):
    bg.alpha_composite(pupil, (int(EC[0] * PX - pupil.width / 2), int(EC[1] * PX - pupil.height / 2)))
bg.convert('RGB').resize((900, 900), Image.NEAREST).save(os.path.join(D, '..', '..', 'style_preview', 'angel_line1.png'))
print('travel (px):', dict(zip(range(0, 360, 15), rng)))
