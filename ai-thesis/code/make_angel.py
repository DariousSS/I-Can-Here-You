"""画"糖果风六翼天使"素材（assets/angel/angel_body.png + angel.json）：中间一只大眼，六片翅膀（上一对V形、中间一对横着、下面一对朝下），翅膀上各有小眼睛。
瞳孔（iris.png）是单独一张图，动画里让它跟着观众的手转。运行：python make_angel.py
"""
import os, math, json, random
from PIL import Image, ImageDraw, ImageOps
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "angel")
os.chdir(D)
S = 2
N = 1500
C = N // 2
OUT = (190, 150, 175, 255)
PAL = [(255, 240, 245, 255), (255, 222, 235, 255), (250, 205, 225, 255), (235, 215, 245, 255), (215, 225, 250, 255)]


def feather_fan(length, span, n, width, offset=0):
    im = Image.new('RGBA', (N * S, N * S), (0, 0, 0, 0))
    items = []
    for i in range(n):
        th = -span / 2 + i * (span / (n - 1))
        L = length * (0.80 + 0.20 * math.cos((th / (span / 2)) * 1.1))
        items.append((L, th, i))
    items.sort(key=lambda t: -t[0])
    for L, th, i in items:
        f = Image.new('RGBA', (int(L * S), int(width * 2 * S)), (0, 0, 0, 0))
        fd = ImageDraw.Draw(f)
        fd.ellipse((0, 0, L * S - 1, width * 2 * S - 1), fill=PAL[(i + offset) % len(PAL)], outline=OUT, width=5 * S // 2)
        fd.line((L * 0.12 * S, width * S, L * 0.9 * S, width * S), fill=(OUT[0], OUT[1], OUT[2], 120), width=3 * S // 2)
        cv = Image.new('RGBA', (N * S, N * S), (0, 0, 0, 0))
        cv.alpha_composite(f, (C * S, C * S - width * S))
        cv = cv.rotate(th, resample=Image.BICUBIC, center=(C * S, C * S))
        im.alpha_composite(cv)
    return im


body = Image.new('RGBA', (N * S, N * S), (0, 0, 0, 0))
eyes = []


def place(angle, length, span, n, width, eye_fracs, offset):
    for mirror in (False, True):
        w = feather_fan(length, span, n, width, offset)
        w = w.rotate(angle, resample=Image.BICUBIC, center=(C * S, C * S))
        if mirror:
            w = ImageOps.mirror(w)
        body.alpha_composite(w)
        for fr in eye_fracs:
            ang = math.radians(angle)
            d = length * fr
            eyes.append((C + (-1 if mirror else 1) * math.cos(ang) * d, C - math.sin(ang) * d, 150, 96))


place(-60, 470, 22, 11, 40, [0.55], 2)       # 下面一对，朝下偏外
place(5, 640, 26, 13, 50, [0.52], 0)         # 中间一对，横着
place(62, 720, 22, 13, 44, [0.38, 0.64], 1)  # 上面一对，向外分开成 V 字
for k in range(18):                           # 中心的一圈小花瓣
    a = k * (360 / 18)
    L = 170
    f = Image.new('RGBA', (int(L * S), 80 * S), (0, 0, 0, 0))
    fd = ImageDraw.Draw(f)
    fd.ellipse((0, 0, L * S - 1, 80 * S - 1), fill=PAL[k % 5], outline=OUT, width=4 * S // 2)
    cv = Image.new('RGBA', (N * S, N * S), (0, 0, 0, 0))
    cv.alpha_composite(f, (C * S, C * S - 40 * S))
    cv = cv.rotate(a, resample=Image.BICUBIC, center=(C * S, C * S))
    body.alpha_composite(cv)
ew = Image.open('eye_white.png')
all_eyes = [(C, C, 330, 214)] + eyes
for (x, y, w, h) in all_eyes:
    e = ew.resize((int(w * S), int(h * S)), Image.LANCZOS)
    body.alpha_composite(e, (int((x - w / 2) * S), int((y - h / 2) * S)))
body = body.resize((N, N), Image.LANCZOS)
body.save('angel_body.png')
meta = json.load(open('angel.json'))
meta['body'] = {'size': N, 'center': [C, C], 'eyes': [[round(x, 1), round(y, 1), w, h] for (x, y, w, h) in all_eyes]}
json.dump(meta, open('angel.json', 'w'))
iris = Image.open('iris.png')
pv = body.copy()
for (x, y, w, h) in all_eyes:
    s = (h * 0.62) / iris.height
    ir = iris.resize((max(2, int(iris.width * s)), max(2, int(iris.height * s))), Image.LANCZOS)
    pv.alpha_composite(ir, (int(x + w * 0.12 - ir.width / 2), int(y + h * 0.10 - ir.height / 2)))
bg = Image.new('RGBA', pv.size, (40, 30, 60, 255))
bg.alpha_composite(pv)
bg.convert('RGB').resize((800, 800)).save(os.path.join(D, '..', '..', 'style_preview', 'angel_draft4.png'))
print('eyes:', len(all_eyes))
