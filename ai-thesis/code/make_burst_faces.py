"""生成"爆开的大脸"用的 12 张不同的脸（256x256）-> ../td_live/burst/face_00.jpg ... face_11.jpg
运行：python make_burst_faces.py [张数，默认 12]
"""
import os, sys, time
from PIL import Image
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import lucy_core as M
N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "td_live", "burst")
os.makedirs(OUT, exist_ok=True)
M.load()
t0 = time.time()
for i in range(N):
    im = M.sample(5000 + i * 7, None, 10, 128).convert("RGB").resize((256, 256), Image.LANCZOS)
    im.save(os.path.join(OUT, "face_" + str(i).zfill(2) + ".jpg"), quality=92)
print("完成", N, "张，用时", round(time.time() - t0), "秒 ->", os.path.abspath(OUT))
