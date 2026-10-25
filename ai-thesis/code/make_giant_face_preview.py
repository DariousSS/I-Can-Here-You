"""城堡上的巨大拼脸预览：用 Lucy 生成几张脸，城堡三块各自显示"大脸的一部分"，每块取自不同的脸；做照片版和像素版。
输出 ../outputs_standard/giant_face_preview.png（上：照片版，下：像素版）
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import lucy_core as M

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
BOX = (638, 152, 1387, 1083)                                    # 城堡整体范围（来自 castle_box_probe：Rectangle4/5/14）
PIECES = {'top': (871, 152, 1113, 357), 'mid': (638, 355, 1387, 641), 'bot': (714, 638, 1324, 1083)}
M.load()
seeds = [3021, 3099, 3150, 3207, 3281]
faces = [M.sample(s, None, 10, 128).convert('RGB') for s in seeds]


def face_to_box(im, pixel=False):
    """把一张 128x128 的脸放到城堡整体范围（只取中间 80% 宽，宽高比和城堡一致）。"""
    w = 128
    cw = int(w * 0.80)
    crop = im.crop(((w - cw) // 2, 0, (w - cw) // 2 + cw, w))
    bw, bh = BOX[2] - BOX[0], BOX[3] - BOX[1]
    if pixel:
        small = crop.resize((cw // 2, w // 2), Image.BOX).quantize(colors=16, method=Image.MEDIANCUT).convert('RGB')
        return small.resize((bw, bh), Image.NEAREST)
    return crop.resize((bw, bh), Image.LANCZOS)


def build(pixel, picks):
    canvas = Image.new('RGB', (W, H), (0, 0, 0))
    for (name, rect), k in zip(PIECES.items(), picks):
        big = face_to_box(faces[k], pixel)
        x0, y0, x1, y1 = rect
        canvas.paste(big.crop((x0 - BOX[0], y0 - BOX[1], x1 - BOX[0], y1 - BOX[1])), (x0, y0))
    return canvas


a = build(False, [0, 1, 2])
b = build(True, [0, 1, 2])
sheet = Image.new('RGB', (1920, 1080 + 10), (30, 24, 50))
sheet.paste(a.resize((960, 540), Image.LANCZOS), (0, 0))
sheet.paste(b.resize((960, 540), Image.LANCZOS), (960, 0))
c = build(False, [3, 3, 3]); d = build(True, [3, 3, 3])
sheet.paste(c.resize((960, 540), Image.LANCZOS), (0, 550))
sheet.paste(d.resize((960, 540), Image.LANCZOS), (960, 550))
out = os.path.join(HERE, '..', 'outputs_standard', 'giant_face_preview.png')
sheet.save(out)
print(os.path.abspath(out))
