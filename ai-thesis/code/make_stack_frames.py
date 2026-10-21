"""生成"脸一张张叠成标准人脸"的帧序列：3 种叠加顺序（A/B/C），每种 NF 帧，最后一帧都是同一张平均脸。
输出：../td_live/stack/A|B|C/stack_0000.jpg ...  和 ../td_live/stack/stack.json
运行：python make_stack_frames.py [脸的张数，默认 120]
"""
import os, sys, json, time, math
import numpy as np
from PIL import Image
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import lucy_core as M

N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
NF = 144
SIZE = 256
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "td_live", "stack")
os.makedirs(OUT, exist_ok=True)
M.load()
faces = []
t0 = time.time()
for i in range(N):
    im = M.sample(1000 + i, None, 10, 128).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
    faces.append(np.asarray(im).astype(np.float64))
    if (i + 1) % 20 == 0:
        print("已生成", i + 1, "/", N, "张，用时", round(time.time() - t0), "秒", flush=True)
rng = np.random.RandomState(5)
orders = {"A": list(range(N)), "B": list(rng.permutation(N)), "C": list(rng.permutation(N))}
for name, order in orders.items():
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    seq = [faces[j] for j in order]
    cum = np.cumsum(np.array(seq), axis=0)
    for f in range(NF):
        n = math.exp(math.log(N) * f / (NF - 1))              # 1 -> N，开头叠得快，后面慢慢收敛
        k = min(N - 1, int(math.floor(n)))
        frac = n - math.floor(n)
        total = cum[k - 1] if k >= 1 else 0.0
        if k < N:
            img = (total + frac * seq[k] + 0.0) / (k + frac) if k >= 1 else (seq[0] * (1 - 0) if f == 0 else (seq[0] + frac * seq[1]) / (1 + frac))
        else:
            img = cum[N - 1] / N
        Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(d, "stack_" + str(f).zfill(4) + ".jpg"), quality=90)
    print("顺序", name, "完成", flush=True)
json.dump({"NF": NF, "sets": list(orders.keys()), "N": N}, open(os.path.join(OUT, "stack.json"), "w"))
print("完成，输出在", os.path.abspath(OUT), "总用时", round(time.time() - t0), "秒")
