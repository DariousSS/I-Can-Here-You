"""和 giant_face_shader.glsl 同样的规则：额头/左眼/右眼/鼻子/嘴/下巴 6 个零件各取自不同的脸 -> ../outputs_standard/giant_face_parts_preview.png"""
import os, sys
import numpy as np
from PIL import Image
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import lucy_core as M
HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
BOX = (638, 152, 1387, 1083)
PIECES = {'top': (871, 152, 1113, 357), 'mid': (638, 355, 1387, 641), 'bot': (714, 638, 1324, 1083)}
M.load()
seeds = [3021, 3099, 3150, 3207, 3281, 3340, 3401, 3477, 3512, 3560, 3611, 3702]
faces = [np.asarray(M.sample(s, None, 10, 128).convert('RGB').resize((256, 256), Image.LANCZOS)).astype(np.float64) for s in seeds]


def render(pick):
    out = np.zeros((H, W, 3))
    bw, bh = BOX[2] - BOX[0], BOX[3] - BOX[1]
    for name, (x0, y0, x1, y1) in PIECES.items():
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(float)
        fx, fy = (xs + .5 - BOX[0]) / bw, (ys + .5 - BOX[1]) / bh
        part = np.where(fy < .22, 0, np.where(fy < .525, np.where(fx < .5, 1, 2), np.where(fy < .595, 3, np.where(fy < .745, 4, 5))))
        u = np.clip(((.1 + .8 * fx) * 255).astype(int), 0, 255)
        v = np.clip(((fy) * 255).astype(int), 0, 255)
        img = np.zeros(fx.shape + (3,))
        for k in range(6):
            m = part == k
            img[m] = faces[pick[k]][v[m], u[m]]
        d = np.minimum(np.minimum(abs(fy - .22), abs(fy - .525)), np.minimum(abs(fy - .595), abs(fy - .745)))
        d = np.where((fy > .22) & (fy < .525), np.minimum(d, abs(fx - .5)), d)
        img *= (1 - .55 * (d < .004))[..., None]
        out[y0:min(y1, H), x0:x1] = img[:min(y1, H) - y0]
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


tiles = [render(p).crop((540, 100, 1500, 1100)).resize((480, 500), Image.LANCZOS) for p in ([0, 1, 2, 3, 4, 5], [6, 7, 8, 9, 10, 11], [2, 5, 7, 1, 9, 4], [3, 3, 3, 3, 3, 3])]
sheet = Image.new('RGB', (480 * 4 + 30, 500), (20, 16, 30))
for i, t in enumerate(tiles):
    sheet.paste(t, (i * 490, 0))
out = os.path.join(HERE, '..', 'outputs_standard', 'giant_face_parts_preview.png')
sheet.save(out); print(os.path.abspath(out))
