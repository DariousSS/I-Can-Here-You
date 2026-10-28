"""给翅膀图中间的空白补一圈放射状羽毛（像素风，6x6 格），生成 assets/angel/wings_pixel_filled.png（原图 wings_pixel_base.png 不动）。
预览：../outputs_standard/angel_filled_preview.png（左：原图，右：补完）
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
src = Image.open(os.path.join(HERE, '..', 'assets', 'angel', 'wings_pixel_base.png')).convert('RGBA')
PX = 6
G = src.width // PX
a = np.asarray(src)[..., 3] > 128
grid = a[PX // 2::PX, PX // 2::PX]                           # 224x224：每个像素格是不是白线
CX, CY = 672.0 / PX, 624.0 / PX                              # 大眼睛中心（格）
new = Image.new('L', (G, G), 0)
d = ImageDraw.Draw(new)
rng = np.random.default_rng(5)
for ang in list(range(24, 157, 6)) + list(range(204, 337, 6)):          # 上方一扇、下方一扇
    th = math.radians(ang + rng.uniform(-1.5, 1.5))
    c, s = math.cos(th), math.sin(th)
    r0 = (118 + 58 * abs(c)) / PX                                         # 从眼睛（杏仁形+圆）外面开始
    R = (300 + 120 * rng.random() + (60 if 60 < ang % 360 < 120 else 0)) / PX if ang < 180 else (260 + 120 * rng.random()) / PX
    d.line([CX + c * r0, CY - s * r0, CX + c * R, CY - s * R], fill=255, width=1)
add = np.asarray(new) > 128
# 只补在空白处：该格原来没有线，并且离已有的翅膀线不太近（不堆叠）
from scipy.ndimage import binary_dilation
free = ~binary_dilation(grid, iterations=1)
ys, xs = np.mgrid[0:G, 0:G]
inside = (np.abs(xs - CX) < 300 / PX) & (np.abs(ys - CY) < 300 / PX)
add &= free & inside
res = grid | add
out = np.zeros((G * PX, G * PX, 4), np.uint8)
big = np.kron(res, np.ones((PX, PX), bool))
out[big] = (255, 255, 255, 255)
Image.fromarray(out, 'RGBA').save(os.path.join(HERE, '..', 'assets', 'angel', 'wings_pixel_filled.png'))
bg = (30, 24, 50, 255)
A = Image.new('RGBA', src.size, bg); A.alpha_composite(src)
B = Image.new('RGBA', src.size, bg); B.alpha_composite(Image.open(os.path.join(HERE, '..', 'assets', 'angel', 'wings_pixel_filled.png')))
sheet = Image.new('RGB', (1100, 560), (14, 10, 22))
sheet.paste(A.convert('RGB').resize((540, 540), Image.NEAREST), (5, 10)); sheet.paste(B.convert('RGB').resize((540, 540), Image.NEAREST), (555, 10))
sheet.save(os.path.join(HERE, '..', 'outputs_standard', 'angel_filled_preview.png'))
print('ok')
