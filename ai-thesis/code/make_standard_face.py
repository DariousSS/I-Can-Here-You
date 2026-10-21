"""用 Lucy 生成 N 张脸，一张张叠起来，看"标准人脸"（平均脸）长什么样。
输出在 ../outputs_standard/：stack_strip.png（叠 1/2/4/8/…/N 张的变化）、standard_face.png（平均脸 512）、variance.png（哪里差别大）、grid_sample.png（用到的脸的样子）
运行：python make_standard_face.py [N，默认 120]
"""
import os, sys, time
import numpy as np
from PIL import Image, ImageDraw
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import lucy_core as M

N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs_standard")
os.makedirs(OUT, exist_ok=True)
M.load()
acc = None
acc2 = None
faces = []
marks = [1, 2, 4, 8, 16, 32, 64, N]
snaps = {}
t0 = time.time()
for i in range(N):
    im = M.sample(1000 + i, None, 10, 128).convert("RGB").resize((128, 128))
    a = np.asarray(im).astype(np.float64)
    acc = a if acc is None else acc + a
    acc2 = a * a if acc2 is None else acc2 + a * a
    if i < 24:
        faces.append(im)
    n = i + 1
    if n in marks:
        snaps[n] = Image.fromarray((acc / n).clip(0, 255).astype(np.uint8))
    if n % 10 == 0:
        print("已生成", n, "/", N, "张，用时", round(time.time() - t0), "秒", flush=True)
mean = acc / N
var = (acc2 / N - mean ** 2).clip(0, None)
std = np.sqrt(var).mean(axis=2)
Image.fromarray(mean.clip(0, 255).astype(np.uint8)).resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "standard_face.png"))
v = (std / max(std.max(), 1e-6) * 255).astype(np.uint8)
Image.fromarray(v).resize((512, 512), Image.LANCZOS).convert("RGB").save(os.path.join(OUT, "variance.png"))
# 叠加过程长条
keys = sorted(snaps)
strip = Image.new("RGB", (len(keys) * 260, 290), (20, 16, 30))
d = ImageDraw.Draw(strip)
for j, k in enumerate(keys):
    strip.paste(snaps[k].resize((256, 256), Image.LANCZOS), (j * 260 + 2, 30))
    d.text((j * 260 + 8, 8), "叠 " + str(k) + " 张" if False else "stack " + str(k), fill=(255, 255, 255))
strip.save(os.path.join(OUT, "stack_strip.png"))
g = Image.new("RGB", (6 * 130, 4 * 130))
for j, f in enumerate(faces):
    g.paste(f, ((j % 6) * 130, (j // 6) * 130))
g.save(os.path.join(OUT, "grid_sample.png"))
print("完成，输出在", os.path.abspath(OUT), "总用时", round(time.time() - t0), "秒")
