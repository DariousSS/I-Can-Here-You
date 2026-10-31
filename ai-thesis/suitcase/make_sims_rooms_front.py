# 画 7 张"模拟人生"风格的正面剖面卧室（1600x820，视角和 bedroom_v4_*.png 一样），一天一张，慢慢搬空。只用 PIL，不烫电脑。
# 用法：python3 make_sims_rooms_front.py   -> 在 game/ 里生成 room_day1.png ~ room_day7.png 和一张总览 rooms_preview.png
import os, math
from PIL import Image, ImageDraw, ImageFilter
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'game')
W, H, S = 1600, 820, 2
OUT = (66, 44, 38)
LW = 5 * S
def sc(v): return int(v * S)
def rr(d, box, r, fill, outline=OUT, w=LW):
    x0, y0, x1, y1 = [sc(v) for v in box]
    d.rounded_rectangle([x0, y0, x1, y1], radius=sc(r), fill=fill, outline=outline, width=w)
def rect(d, box, fill, outline=OUT, w=LW):
    d.rectangle([sc(box[0]), sc(box[1]), sc(box[2]), sc(box[3])], fill=fill, outline=outline, width=w if outline else 0)
def poly(d, pts, fill, outline=OUT, w=LW):
    p = [(sc(x), sc(y)) for x, y in pts]
    d.polygon(p, fill=fill)
    if outline: d.line(p + [p[0]], fill=outline, width=w, joint='curve')
def shade(c, k): return tuple(max(0, min(255, int(v * k))) for v in c)
def glow(im, cx, cy, r, col, a):
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for i in range(24, 0, -1):
        rad = sc(r * i / 24.0); al = int(a * (1 - i / 24.0) ** 1.6 * 255 / 1.0)
        od.ellipse([sc(cx) - rad, sc(cy) - rad, sc(cx) + rad, sc(cy) + rad], fill=col + (min(255, al),))
    im.alpha_composite(ov)
def draw_room(day):
    im = Image.new('RGBA', (W * S, H * S), (12, 12, 16, 255)); d = ImageDraw.Draw(im)
    tints = {1: None, 2: None, 3: (255, 150, 90, 38), 4: (20, 30, 90, 110), 5: (120, 125, 140, 55), 6: (255, 220, 160, 25), 7: (255, 255, 255, 30)}
    wallc = {1: (247, 205, 190), 2: (247, 205, 190), 3: (246, 196, 176), 4: (232, 190, 182), 5: (236, 214, 206), 6: (240, 204, 190), 7: (244, 218, 208)}[day]
    rect(d, (0, 0, W, 650), wallc, outline=None)
    rect(d, (0, 560, W, 650), shade(wallc, 0.97), outline=None)
    rect(d, (0, 622, W, 650), (170, 120, 96), outline=None)
    d.line([(0, sc(622)), (sc(W), sc(622))], fill=OUT, width=LW)
    rect(d, (0, 650, W, H), (214, 170, 120), outline=None)
    for x in range(0, W, 200): d.line([(sc(x), sc(650)), (sc(x - 60), sc(H))], fill=(190, 148, 102), width=3 * S)
    d.line([(0, sc(650)), (sc(W), sc(650))], fill=OUT, width=LW)
    # 窗户
    sky = {1: (150, 205, 235), 2: (160, 210, 238), 3: (250, 170, 110), 4: (24, 30, 70), 5: (176, 184, 196), 6: (170, 214, 238), 7: (235, 245, 252)}[day]
    rect(d, (270, 160, 630, 470), (255, 244, 220))
    rect(d, (288, 178, 612, 452), sky)
    if day == 4:
        d.ellipse([sc(520), sc(200), sc(570), sc(250)], fill=(250, 245, 210), outline=OUT, width=LW // 2)
    if day in (1, 2, 6): d.ellipse([sc(510), sc(205), sc(570), sc(265)], fill=(255, 238, 170), outline=OUT, width=LW // 2)
    d.line([(sc(450), sc(178)), (sc(450), sc(452))], fill=(255, 244, 220), width=7 * S)
    d.line([(sc(288), sc(315)), (sc(612), sc(315))], fill=(255, 244, 220), width=7 * S)
    cur = (232, 120, 120) if day != 7 else (214, 150, 150)
    if day <= 5:
        rr(d, (228, 140, 280, 500), 6, cur); rr(d, (622, 140, 674, 500), 6, cur)
    else:
        rr(d, (228, 140, 262, 500), 6, cur); rr(d, (638, 140, 672, 500), 6, cur)
    # 挂画
    if day <= 5:
        rect(d, (940, 150, 1050, 300), (120, 84, 70)); rect(d, (952, 162, 1038, 288), (170, 214, 190))
        d.polygon([(sc(952), sc(288)), (sc(985), sc(230)), (sc(1010), sc(260)), (sc(1038), sc(215)), (sc(1038), sc(288))], fill=(120, 180, 140))
        if day == 5:
            pass
        rect(d, (1090, 190, 1200, 310), (120, 84, 70)); rect(d, (1102, 202, 1188, 298), (250, 220, 150))
        d.ellipse([sc(1126), sc(226), sc(1164), sc(264)], fill=(240, 150, 110))
    elif day == 6:
        poly(d, [(944, 160), (1050, 140), (1058, 290), (952, 306)], (120, 84, 70)); poly(d, [(958, 172), (1042, 158), (1046, 280), (962, 292)], (170, 214, 190))
        rect(d, (1130, 220, 1140, 224), (190, 150, 130), outline=None)
    else:
        for (x, y) in ((985, 215), (1145, 250)):
            d.rectangle([sc(x - 38), sc(y - 52), sc(x + 38), sc(y + 52)], fill=shade(wallc, 0.93))
    # 门 + 铃铛（门铃：贴在门上方）
    dx0, dx1 = 1470, 1590
    rect(d, (dx0 - 10, 140, dx1 + 10, 650), (150, 104, 84))
    if day in (3, 4):
        poly(d, [(dx0, 150), (dx0 + 56, 164), (dx0 + 56, 640), (dx0, 650)], (196, 150, 118))
        rect(d, (dx0 + 56, 150, dx1, 650), (30, 26, 34), outline=None)
    elif day == 7:
        rect(d, (dx0, 150, dx1, 650), (255, 252, 236), outline=None)
        poly(d, [(dx0, 150), (dx0 + 30, 164), (dx0 + 30, 640), (dx0, 650)], (196, 150, 118))
    else:
        rect(d, (dx0, 150, dx1, 650), (196, 150, 118)); rect(d, (dx0 + 18, 176, dx1 - 18, 380), shade((196, 150, 118), 0.92)); rect(d, (dx0 + 18, 410, dx1 - 18, 620), shade((196, 150, 118), 0.92))
        d.ellipse([sc(dx1 - 34), sc(400), sc(dx1 - 20), sc(414)], fill=(240, 210, 120), outline=OUT, width=LW // 2)
    bx, by = 1530, 118
    tape = (235, 235, 225)
    if day == 5:
        rect(d, (bx - 26, 96, bx + 8, 108), tape, w=LW // 2)
        poly(d, [(bx + 6, 104), (bx + 22, 124), (bx + 10, 148), (bx - 4, 130)], (240, 200, 90))
    else:
        rect(d, (bx - 26, 128, bx + 26, 140), tape, w=LW // 2)
        poly(d, [(bx - 16, by + 26), (bx - 12, by), (bx + 12, by), (bx + 16, by + 26)], (240, 200, 90))
        d.ellipse([sc(bx - 5), sc(by + 24), sc(bx + 5), sc(by + 34)], fill=(180, 130, 40), outline=OUT, width=LW // 3)
    if day == 4:
        for k, a in enumerate((0.6, 1.1)):
            r = 34 + k * 22
            d.arc([sc(bx - r), sc(by - r + 20), sc(bx + r), sc(by + r + 20)], 200, 340, fill=(250, 220, 120), width=LW // 2)
            d.arc([sc(bx - r), sc(by - r + 20), sc(bx + r), sc(by + r + 20)], 20, 160, fill=(250, 220, 120), width=LW // 2)
    # 床头柜 + 台灯
    rect(d, (690, 540, 790, 650), (170, 120, 96)); rect(d, (706, 560, 774, 628), shade((170, 120, 96), 0.9), w=LW // 2)
    lamp_on = day in (3, 4, 5, 6)
    poly(d, [(705, 540), (775, 540), (760, 466), (720, 466)], (255, 238, 170) if lamp_on else (230, 214, 160))
    if day <= 5:
        rect(d, (726, 520, 748, 540), (240, 210, 120)) if False else None
    # 床
    if day <= 6:
        rect(d, (850, 590, 1396, 650), (150, 104, 84))
        rr(d, (840, 500, 1400, 596), 18, (120, 168, 214))
        for x in range(880, 1400, 90): d.line([(sc(x), sc(502)), (sc(x), sc(594))], fill=(100, 148, 196), width=3 * S)
        d.line([(sc(842), sc(540)), (sc(1398), sc(540))], fill=(100, 148, 196), width=3 * S)
        rect(d, (1400, 380, 1442, 650), (130, 90, 72))
        if day <= 5:
            rr(d, (1210, 446, 1384, 502), 24, (255, 255, 255))
        if day == 6:
            rr(d, (846, 500, 1100, 596), 18, (250, 226, 150))
    else:
        rect(d, (850, 590, 1396, 650), (150, 104, 84)); rr(d, (840, 520, 1400, 596), 18, (236, 232, 224)); rect(d, (1400, 380, 1442, 650), (130, 90, 72))
    # 行李箱（我）：第 1~5 天在，第 6 天打包好，第 7 天没了
    if day <= 5:
        rr(d, (120, 500, 350, 650), 20, (96, 150, 150))
        d.line([(sc(160), sc(502)), (sc(160), sc(648))], fill=OUT, width=LW); d.line([(sc(310), sc(502)), (sc(310), sc(648))], fill=OUT, width=LW)
        d.arc([sc(196), sc(450), sc(274), sc(520)], 180, 360, fill=OUT, width=LW)
        rect(d, (220, 540, 252, 566), (240, 200, 90), w=LW // 2)
    elif day == 6:
        rr(d, (110, 470, 360, 650), 20, (96, 150, 150))
        d.line([(sc(160), sc(472)), (sc(160), sc(648))], fill=OUT, width=LW); d.line([(sc(310), sc(472)), (sc(310), sc(648))], fill=OUT, width=LW)
        d.arc([sc(196), sc(420), sc(274), sc(490)], 180, 360, fill=OUT, width=LW)
        rr(d, (130, 535, 340, 552), 6, (232, 120, 120), w=LW // 2)
    if day == 2:
        rect(d, (712, 512, 752, 540), (232, 120, 120), w=LW // 2)
    if day == 6:
        pass
    # 灯光和时间
    if lamp_on: glow(im, 740, 500, 260, (255, 220, 140), 0.5)
    if tints[day]:
        ov = Image.new('RGBA', im.size, tints[day]); im.alpha_composite(ov)
    if day == 4:
        glow(im, 1525, 150, 150, (250, 220, 120), 0.35)
    im = im.convert('RGB').resize((W, H), Image.LANCZOS)
    return im
os.makedirs(OUTDIR, exist_ok=True)
imgs = []
for day in range(1, 8):
    im = draw_room(day); p = os.path.join(OUTDIR, 'room_day%d.png' % day); im.save(p); imgs.append(im); print('saved', p)
sheet = Image.new('RGB', (W // 2 * 2 + 30, (H // 2) * 4 + 50), (30, 30, 36))
for i, im in enumerate(imgs):
    t = im.resize((W // 2, H // 2), Image.LANCZOS); sheet.paste(t, (10 + (i % 2) * (W // 2 + 10), 10 + (i // 2) * (H // 2 + 10)))
sheet.save(os.path.join(OUTDIR, 'rooms_preview.png')); print('preview saved')
