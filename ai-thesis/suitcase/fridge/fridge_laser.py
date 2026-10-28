"""激光切割小冰箱（手指榫接，开口朝前 + 一块门板 + 3 个搁板）。输出 SVG（毫米，1:1）+ 预览 PNG。
Trotec Speedy 400：最大板材 1000 x 600 mm。线色：红 #ff0000 = 切断，蓝 #0000ff = 雕刻线（CCI wiki: Creating a file in Illustrator）。
用法:  python3 fridge_laser.py --name small  --w 200 --d 217 --h 583 --t 3 --finger 10
       python3 fridge_laser.py --name bar    --w 500 --d 500 --h 850 --t 4 --finger 20     # 1:1 的小型冰箱
"""
import argparse, os, math
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser()
ap.add_argument('--name', default='small')
ap.add_argument('--w', type=float, default=200.0)      # 宽（外尺寸）
ap.add_argument('--d', type=float, default=217.0)      # 深
ap.add_argument('--h', type=float, default=583.0)      # 高
ap.add_argument('--t', type=float, default=3.0)        # 板厚
ap.add_argument('--finger', type=float, default=10.0)  # 手指榫宽度（大约）
ap.add_argument('--bed_w', type=float, default=1000.0)
ap.add_argument('--bed_h', type=float, default=600.0)
ap.add_argument('--gap', type=float, default=4.0)      # 零件之间的间距
ap.add_argument('--tiers', action='store_true')        # 两层：下层门（装饰）+ 上层投影屏
ap.add_argument('--split', type=float, default=0.42)   # 两层的分界高度（从下往上，占总高的比例）
ap.add_argument('--shelf_at', default='')              # 搁板位置（占总高的比例，逗号分隔）；两层时默认只在分界处放一块隔板
ap.add_argument('--door_gap', type=float, default=2.0) # 上下两扇门之间的缝
ap.add_argument('--no_screen_handle', action='store_true')   # 上层投影屏不要把手
args = ap.parse_args()
W, D, H, T, F = args.w, args.d, args.h, args.t, args.finger
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, args.name)
os.makedirs(OUT, exist_ok=True)

def segs(L, first_finger, inner):
    """沿一条边的手指榫分段 [(起点, 终点, 凹进深度)]。first_finger: 第一段是手指(齐平)还是凹口；inner: 两头各留 T 的空位（三块板交汇的角）"""
    out = []
    a, b = (T, L - T) if inner else (0.0, L)
    if inner:
        out.append((0.0, T, T))
    n = max(3, int(round((b - a) / F)))
    if n % 2 == 0:
        n += 1
    w = (b - a) / n
    for i in range(n):
        finger = (i % 2 == 0) == first_finger
        out.append((a + i * w, a + (i + 1) * w, 0.0 if finger else T))
    if inner:
        out.append((L - T, L, T))
    return out

def flat(L):
    return [(0.0, L, 0.0)]

def panel(A, B, bottom=None, right=None, top=None, left=None):
    """A x B 的矩形板，四条边各自可以有手指榫。每条边 None 或 (first_finger, inner)。返回外轮廓点列表"""
    Ls = [A, B, A, B]
    specs = [bottom, right, top, left]
    S = [segs(Ls[i], *specs[i]) if specs[i] else flat(Ls[i]) for i in range(4)]
    pts = []
    for i in range(4):
        prev_end = S[(i - 1) % 4][-1][2]
        next_start = S[(i + 1) % 4][0][2]
        L = Ls[i]
        seg = list(S[i])
        seg[0] = (prev_end, seg[0][1], seg[0][2])
        seg[-1] = (seg[-1][0], L - next_start, seg[-1][2])
        for s, e, d in seg:
            for t_ in (s, e):
                if i == 0: p = (t_, d)
                elif i == 1: p = (A - d, t_)
                elif i == 2: p = (A - t_, B - d)
                else: p = (d, B - t_)
                if not pts or abs(pts[-1][0] - p[0]) > 1e-6 or abs(pts[-1][1] - p[1]) > 1e-6:
                    pts.append(p)
    return pts

def rect(x, y, w, h):
    return [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]

def rrect(x, y, w, h, r=2.0, n=6):
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        for k in range(n + 1):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def circle(cx, cy, r, n=36):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]

parts = []     # (name, w, h, cuts[list of closed polylines], engraves[list of closed/open polylines])
# 底板、顶板：W x D（v = 从前到后）；左边、右边、后边 手指(first_finger) 在板上
plate = dict(left=(True, False), right=(True, False), top=(True, False))
for nm in ('bottom', 'top'):
    parts.append((nm, W, D, [panel(W, D, **plate)], []))
# 左右侧板：D x H（u = 从前到后，v = 从下到上）。下边/上边：凹口先；后边：内部手指，凹口先
if args.shelf_at:
    shelf_fr = [float(x) for x in args.shelf_at.split(',')]
elif args.tiers:
    shelf_fr = [args.split]
else:
    shelf_fr = [(k + 1) / 4.0 for k in range(3)]
nshelf = len(shelf_fr)
slot_len = max(8.0, round(W * 0.07))
tab_us = [D * 0.22, D * 0.62]
shelf_vs = [max(T, min(H - 2 * T, fr * H - T / 2)) for fr in shelf_fr]
for nm in ('left', 'right'):
    outline = panel(D, H, bottom=(False, False), top=(False, False), right=(False, True))
    slots = [rect(u, v, slot_len, T) for v in shelf_vs for u in tab_us]
    parts.append((nm, D, H, [outline] + slots, []))
# 后板：W x H。下/上边：凹口先；左右边：内部手指先
back_cut = [panel(W, H, bottom=(False, False), top=(False, False), left=(True, True), right=(True, True))]
back_cut.append(circle(W - max(12.0, W * 0.12), max(14.0, H * 0.05), max(3.0, W * 0.02)))      # 出线孔
parts.append(('back', W, H, back_cut, []))
# 门板
hw = max(5.0, W * 0.035)
if args.tiers:
    gap = args.door_gap
    Hl = args.split * H - gap / 2.0
    Hu = H - Hl - gap
    hl = min(Hl * 0.45, 160.0)
    hx = W - W * 0.12
    hy = Hl - 40.0 - hl                       # SVG 的 y 向下：把手靠近下层门的上边
    handle = rrect(hx, hy, hw, hl, r=hw / 2.2)
    parts.append(('door_lower', W, Hl, [rect(0, 0, W, Hl)], [handle + [handle[0]]]))
    hu = min(Hu * 0.30, 160.0)
    hy_u = Hu - 40.0 - hu                      # 上层门的把手靠近它的下边（和下层把手挨在一起，像真的上冷冻下冷藏冰箱）
    handle_u = rrect(hx, hy_u, hw, hu, r=hw / 2.2)
    parts.append(('screen_upper', W, Hu, [rect(0, 0, W, Hu)], [] if args.no_screen_handle else [handle_u + [handle_u[0]]]))
else:
    seam = H * 0.66
    hl = H * 0.12
    hx = W - W * 0.16
    eng = [[(0, seam), (W, seam)],
           rrect(hx, seam + (H - seam) * 0.20, hw, hl, r=hw / 2.2) + [rrect(hx, seam + (H - seam) * 0.20, hw, hl, r=hw / 2.2)[0]],
           rrect(hx, seam - H * 0.05 - hl * 1.6, hw, hl * 1.6, r=hw / 2.2) + [rrect(hx, seam - H * 0.05 - hl * 1.6, hw, hl * 1.6, r=hw / 2.2)[0]]]
    eng = [[(x, H - y) for x, y in line] for line in eng]
    parts.append(('door', W, H, [rect(0, 0, W, H)], eng))
# 搁板：(W-2T) x (D-T)，左右各 2 个榫穿过侧板的槽
SW, SD = W - 2 * T, D - T
for k in range(nshelf):
    outline = [(0, 0)]
    pts = [(0, 0), (SW, 0)]
    # 右边（向上）：榫伸出 T
    r_pts, l_pts = [], []
    for u in tab_us:
        r_pts += [(SW, u), (SW + T, u), (SW + T, u + slot_len), (SW, u + slot_len)]
    for u in reversed(tab_us):
        l_pts += [(0, u + slot_len), (-T, u + slot_len), (-T, u), (0, u)]
    poly = [(0, 0), (SW, 0)] + r_pts + [(SW, SD), (0, SD)] + l_pts
    parts.append(('shelf%d' % (k + 1), SW + 2 * T, SD, [[(x + T, y) for x, y in poly]], []))

# ---- 排板（简单的"行排"，可旋转 90 度），一张板 1000 x 600 ----
M, G = 5.0, args.gap
BW, BH = args.bed_w - 2 * M, args.bed_h - 2 * M
sheets = []
def place(parts_sorted):
    for p in parts_sorted:
        nm, w, h = p[0], p[1], p[2]
        orients = [(w, h, 0), (h, w, 90)]
        orients = [o for o in orients if o[0] <= BW and o[1] <= BH]
        if not orients:
            raise SystemExit('零件 %s (%.0f x %.0f) 比板材 %.0f x %.0f 还大，放不下：请缩小冰箱，或把这块板拆成两块。' % (nm, w, h, BW, BH))
        done = False
        for sh in sheets:                                           # 先试着塞进已有的行
            for ow, oh, rot in orients:
                for row in sh['rows']:
                    if row['h'] >= oh and row['x'] + ow <= BW:
                        sh['items'].append((p, row['x'], row['y'], rot)); row['x'] += ow + G; done = True; break
                if done: break
            if done: break
        if not done:                                                # 再试着在已有的板上开新的一行（选"站得高"的方向，这样后面的零件能并排）
            for sh in sheets:
                for ow, oh, rot in sorted(orients, key=lambda o: -o[1]):
                    if sh['y'] + oh <= BH:
                        row = {'y': sh['y'], 'h': oh, 'x': ow + G}
                        sh['rows'].append(row); sh['y'] += oh + G
                        sh['items'].append((p, 0.0, row['y'], rot)); done = True; break
                if done: break
        if not done:
            ow, oh, rot = sorted(orients, key=lambda o: -o[1])[0]
            sh = {'rows': [], 'items': [], 'y': oh + G}
            sh['rows'].append({'y': 0.0, 'h': oh, 'x': ow + G})
            sh['items'].append((p, 0.0, 0.0, rot))
            sheets.append(sh)
place(sorted(parts, key=lambda p: -(p[1] * p[2])))

def xf(pt, p, ox, oy, rot):
    x, y = pt
    if rot == 90:
        x, y = p[2] - y, x          # 旋转 90 度后宽高互换
    return (x + ox + M, y + oy + M)

PX = 2.0
for si, sh in enumerate(sheets):
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="%.0fmm" height="%.0fmm" viewBox="0 0 %.0f %.0f">' % (args.bed_w, args.bed_h, args.bed_w, args.bed_h),
           '<rect x="0" y="0" width="%.0f" height="%.0f" fill="none" stroke="#cccccc" stroke-width="0.2"/>' % (args.bed_w, args.bed_h)]
    img = Image.new('RGB', (int(args.bed_w * PX), int(args.bed_h * PX)), (250, 248, 242))
    dr = ImageDraw.Draw(img)
    for p, ox, oy, rot in sh['items']:
        nm = p[0]
        for poly, col, hexcol, closed in [(c, (200, 30, 30), '#ff0000', True) for c in p[3]] + [(e, (40, 60, 220), '#0000ff', False) for e in p[4]]:
            q = [xf(pt, p, ox, oy, rot) for pt in poly]
            d = 'M ' + ' L '.join('%.3f %.3f' % pt for pt in q) + (' Z' if closed else '')
            svg.append('<path d="%s" fill="none" stroke="%s" stroke-width="0.1"/>' % (d, hexcol))
            pp = [(x * PX, y * PX) for x, y in q]
            dr.line(pp + ([pp[0]] if closed else []), fill=col, width=2)
        cx, cy = xf((p[1] / 2.0, p[2] / 2.0), p, ox, oy, rot)
        dr.text((cx * PX - 14, cy * PX - 5), nm, fill=(110, 110, 110))
    svg.append('</svg>')
    open(os.path.join(OUT, 'sheet%d.svg' % (si + 1)), 'w', encoding='utf-8').write('\n'.join(svg))
    img.save(os.path.join(OUT, 'sheet%d_preview.png' % (si + 1)))

# ---- 正面示意图 + 和桌子/行李箱的比例图 ----
S = min(900.0 / H, 520.0 / W)
im = Image.new('RGB', (int(W * S + 160), int(H * S + 100)), (250, 248, 242))
dr = ImageDraw.Draw(im)
x0, y0 = 80, 50
dr.rectangle((x0, y0, x0 + W * S, y0 + H * S), outline=(60, 60, 60), width=3, fill=(238, 232, 222))
if args.tiers:
    ys = y0 + H * S - (args.split * H) * S
    dr.rectangle((x0 + 6, y0 + 6, x0 + W * S - 6, ys - 4), fill=(255, 255, 255), outline=(150, 150, 150))
    dr.text((x0 + 20, y0 + 20), 'upper tier: projection screen', fill=(120, 120, 120))
    dr.text((x0 + 20, ys + 14), 'lower tier: door, to decorate', fill=(120, 120, 120))
    if not args.no_screen_handle:
        dr.rounded_rectangle((x0 + (W - W * 0.12) * S, ys - (40 + hu) * S - 4, x0 + (W - W * 0.12 + hw) * S, ys - 44 * S), radius=3, outline=(40, 60, 220), width=2)
    dr.rounded_rectangle((x0 + (W - W * 0.12) * S, ys + 40 * S, x0 + (W - W * 0.12 + hw) * S, ys + (40 + hl) * S), radius=3, outline=(40, 60, 220), width=2)
dr.text((x0, 20), '%s  front view: %.0f x %.0f x %.0f mm (W x D x H), board %.0f mm' % (args.name, W, D, H, T), fill=(60, 60, 60))
im.save(os.path.join(OUT, 'front_view.png'))
# 比例图：1200 mm 的桌子，左边行李箱（估计 600 宽 x 约 560 高，盖子打开），右边冰箱
k = 0.62
TW = 1200
sc = Image.new('RGB', (int(TW * k) + 120, int((H + 140) * k) + 80), (250, 248, 242))
dd = ImageDraw.Draw(sc)
bx, by = 60, int((H + 60) * k) + 20
dd.rectangle((bx, by, bx + TW * k, by + 28 * k), fill=(190, 150, 100), outline=(100, 80, 50))
dd.rectangle((bx + 30 * k, by - 170 * k, bx + 630 * k, by), outline=(120, 60, 50), width=2, fill=(190, 150, 140))
dd.rectangle((bx + 70 * k, by - 170 * k - 400 * k, bx + 590 * k, by - 170 * k), outline=(120, 120, 120), width=2)
dd.text((bx + 200 * k, by - 90 * k), 'suitcase (assumed 600 wide)', fill=(80, 40, 30))
fx = bx + 640 * k
dd.rectangle((fx, by - H * k, fx + W * k, by), outline=(60, 60, 60), width=3, fill=(238, 232, 222))
if args.tiers:
    ys2 = by - args.split * H * k
    dd.rectangle((fx + 5, by - H * k + 5, fx + W * k - 5, ys2 - 3), fill=(255, 255, 255), outline=(150, 150, 150))
dd.text((fx + 10, by - H * k - 16), 'fridge %.0f x %.0f' % (W, H), fill=(60, 60, 60))
dd.text((bx, by + 36 * k + 6), 'table 1200 mm', fill=(100, 80, 50))
sc.save(os.path.join(OUT, 'scale_view.png'))
print('%s: %d sheet(s) of %.0f x %.0f mm  -> %s' % (args.name, len(sheets), args.bed_w, args.bed_h, OUT))
for si, sh in enumerate(sheets):
    print('  sheet%d: ' % (si + 1) + ', '.join(p[0] for p, *_ in sh['items']))
