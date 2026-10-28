"""画三个简笔画卧室（黑底线条，适合投影到盖子上）。每个房间里都有同一个行李箱 = 一直在搬家。
输出: bedroom_v4_1.png bedroom_v4_2.png bedroom_v4_3.png bedrooms_sheet.png （1600x820，约等于盖子上那块长方形的比例）"""
import os
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FLOOR, LW = 1600, 820, 650, 7

def suitcase(d, x, c):
    d.rounded_rectangle((x, FLOOR - 150, x + 230, FLOOR), 14, outline=c, width=LW)
    d.arc((x + 80, FLOOR - 190, x + 150, FLOOR - 140), 180, 360, fill=c, width=LW)
    d.line((x + 40, FLOOR - 150, x + 40, FLOOR), fill=c, width=4)
    d.line((x + 190, FLOOR - 150, x + 190, FLOOR), fill=c, width=4)

def bed(d, x, c, flip=False):
    s = -1 if flip else 1
    def X(v): return x + s * v
    d.rectangle((min(X(0), X(40)), FLOOR - 270, max(X(0), X(40)), FLOOR), outline=c, width=LW)
    d.rounded_rectangle((min(X(40), X(600)), FLOOR - 150, max(X(40), X(600)), FLOOR - 60), 10, outline=c, width=LW)
    d.rounded_rectangle((min(X(60), X(230)), FLOOR - 200, max(X(60), X(230)), FLOOR - 150), 20, outline=c, width=LW)
    d.line((X(300), FLOOR - 150, X(300), FLOOR - 60), fill=c, width=4)
    for lx in (X(60), X(580)):
        d.line((lx, FLOOR - 60, lx, FLOOR), fill=c, width=LW)

def window(d, x, y, w, h, c, moon=True, city=False):
    d.rectangle((x, y, x + w, y + h), outline=c, width=LW)
    d.line((x + w // 2, y, x + w // 2, y + h), fill=c, width=4)
    d.line((x, y + h // 2, x + w, y + h // 2), fill=c, width=4)
    if moon:
        d.ellipse((x + w - 110, y + 30, x + w - 50, y + 90), outline=c, width=5)
    if city:
        for i, bh in enumerate((70, 110, 60, 90, 120)):
            bx = x + 14 + i * (w - 28) // 5
            d.rectangle((bx, y + h - bh, bx + (w - 28) // 5 - 8, y + h), outline=c, width=3)

def lamp(d, x, c):
    d.rectangle((x, FLOOR - 110, x + 100, FLOOR), outline=c, width=LW)
    d.polygon([(x + 15, FLOOR - 110), (x + 85, FLOOR - 110), (x + 70, FLOOR - 180), (x + 30, FLOOR - 180)], outline=c)
    d.line((x + 50, FLOOR - 110, x + 50, FLOOR - 100), fill=c, width=4)

def desk(d, x, c):
    d.line((x, FLOOR - 190, x + 300, FLOOR - 190), fill=c, width=LW)
    d.line((x + 20, FLOOR - 190, x + 20, FLOOR), fill=c, width=LW)
    d.line((x + 280, FLOOR - 190, x + 280, FLOOR), fill=c, width=LW)
    d.polygon([(x + 90, FLOOR - 190), (x + 210, FLOOR - 190), (x + 190, FLOOR - 270), (x + 110, FLOOR - 270)], outline=c)

def plant(d, x, c):
    d.polygon([(x, FLOOR), (x + 80, FLOOR), (x + 70, FLOOR - 70), (x + 10, FLOOR - 70)], outline=c)
    for dx, dy in ((10, -140), (40, -190), (70, -140)):
        d.line((x + 40, FLOOR - 70, x + dx, FLOOR + dy + 70), fill=c, width=5)
        d.ellipse((x + dx - 18, FLOOR + dy + 40, x + dx + 18, FLOOR + dy + 80), outline=c, width=4)


import math
def desk_lamp(d, x, c):
    y = FLOOR - 190
    d.line((x, y, x + 30, y - 60), fill=c, width=5)
    d.line((x + 30, y - 60, x + 80, y - 95), fill=c, width=5)
    d.polygon([(x + 70, y - 85), (x + 112, y - 105), (x + 132, y - 72), (x + 92, y - 55)], outline=c)

def shelf(d, x, y, c, w=260):
    d.line((x, y, x + w, y), fill=c, width=LW)
    bx = x + 20
    for bw, bh in ((26, 80), (22, 100), (30, 70), (24, 90), (28, 60)):
        if bx + bw > x + w - 10:
            break
        d.rectangle((bx, y - bh, bx + bw, y), outline=c, width=4)
        bx += bw + 10

def boxes(d, x, c):
    d.rectangle((x, FLOOR - 130, x + 170, FLOOR), outline=c, width=LW)
    d.line((x + 85, FLOOR - 130, x + 85, FLOOR - 95), fill=c, width=5)
    d.rectangle((x + 20, FLOOR - 250, x + 150, FLOOR - 130), outline=c, width=LW)
    d.line((x + 85, FLOOR - 250, x + 85, FLOOR - 215), fill=c, width=5)

def clothes_rail(d, x, c, w=220):
    d.line((x, FLOOR - 330, x + w, FLOOR - 330), fill=c, width=LW)
    d.line((x, FLOOR - 330, x, FLOOR), fill=c, width=LW)
    d.line((x + w, FLOOR - 330, x + w, FLOOR), fill=c, width=LW)
    for i in range(4):
        hx = x + 30 + i * 50
        d.polygon([(hx - 16, FLOOR - 320), (hx + 16, FLOOR - 320), (hx + 20, FLOOR - 190), (hx - 20, FLOOR - 190)], outline=c)

def frames(d, x, y, c):
    d.rectangle((x, y, x + 110, y + 150), outline=c, width=5)
    d.rectangle((x + 150, y + 40, x + 260, y + 160), outline=c, width=5)

def curtains(d, x, y, w, h, c):
    d.rectangle((x - 50, y - 30, x - 6, y + h + 40), outline=c, width=4)
    d.rectangle((x + w + 6, y - 30, x + w + 50, y + h + 40), outline=c, width=4)

def string_lights(d, c):
    pts = [(60 + i * 95, 80 + int(34 * math.sin(i * 0.7))) for i in range(17)]
    d.line(pts, fill=c, width=3)
    for px, py in pts[1::2]:
        d.ellipse((px - 7, py + 2, px + 7, py + 16), outline=c, width=3)

def room(n):
    cols = {1: (255, 190, 110), 2: (130, 205, 205), 3: (225, 150, 165), 4: (150, 210, 140), 5: (190, 160, 235)}
    c = cols[n]
    img = Image.new('RGB', (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line((0, FLOOR, W, FLOOR), fill=c, width=LW)
    bed(d, 1440, c, flip=True)
    if n == 1:
        window(d, 280, 170, 340, 290, c); curtains(d, 280, 170, 340, 290, c); lamp(d, 690, c); suitcase(d, 120, c); frames(d, 940, 150, c)
    elif n == 2:
        window(d, 360, 150, 360, 280, c, moon=False, city=True); desk(d, 420, c); desk_lamp(d, 650, c); suitcase(d, 90, c); shelf(d, 900, 300, c)
    elif n == 3:
        string_lights(d, c); window(d, 560, 190, 280, 300, c); plant(d, 430, c); suitcase(d, 90, c)
        d.ellipse((760, FLOOR - 20, 1560, FLOOR + 50), outline=c, width=4)
    elif n == 4:
        boxes(d, 110, c); suitcase(d, 420, c); window(d, 980, 160, 300, 240, c, moon=False)
        d.line((700, 0, 700, 210), fill=c, width=4)
        d.polygon([(650, 290), (750, 290), (730, 210), (670, 210)], outline=c)
    else:
        desk(d, 100, c); desk_lamp(d, 330, c); suitcase(d, 470, c); lamp(d, 730, c); shelf(d, 520, 230, c); frames(d, 960, 150, c)
    glow = img.filter(ImageFilter.GaussianBlur(10))
    return Image.blend(img, glow, 0.5)

imgs = []
for n in (1, 2, 3, 4, 5):
    im = room(n)
    im.save(os.path.join(HERE, 'bedroom_v4_%d.png' % n)); imgs.append(im)
sheet = Image.new('RGB', (3 * 550 + 10, 2 * 290 + 10), (30, 30, 30))
for i, im in enumerate(imgs):
    sheet.paste(im.resize((540, 277)), (10 + (i % 3) * 550, 10 + (i // 3) * 290))
sheet.save(os.path.join(HERE, 'bedrooms_sheet.png')); print('ok')
