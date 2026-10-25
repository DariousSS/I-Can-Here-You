"""用 Lucy 另外生成一批脸（60 张，种子和标准脸、爆开脸都不同），量出"随机脸离标准脸多远"的标尺 -> outputs_standard/deviation_ref.json；
再给 12 张爆开用的脸算好偏离度 -> td_live/burst/burst_dev.json。运行：nice -n 15 python make_deviation_ref.py [张数，默认 60]
"""
import json, os, sys, time
import numpy as np
from PIL import Image
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import lucy_core as M
import deviation as DV

N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
HERE = os.path.dirname(os.path.abspath(__file__))
M.load()
vals = []
t0 = time.time()
for i in range(N):
    im = M.sample(8000 + i * 3, None, 10, 128).convert("RGB")
    vals.append(DV.raw(im))
    if (i + 1) % 10 == 0:
        print("已量", i + 1, "/", N, "张，用时", round(time.time() - t0), "秒", flush=True)
v = np.array(vals)
ref = {"n": N, "min": float(v.min()), "p05": float(np.percentile(v, 5)), "p10": float(np.percentile(v, 10)), "p50": float(np.percentile(v, 50)), "p90": float(np.percentile(v, 90)), "p95": float(np.percentile(v, 95)), "max": float(v.max())}
with open(os.path.join(HERE, "..", "outputs_standard", "deviation_ref.json"), "w", encoding="utf-8") as f:
    json.dump(ref, f, indent=1)
print("标尺:", {k: round(x, 1) for k, x in ref.items() if k != "n"})
DV._C.clear()
out = {}
for k in range(12):
    p = os.path.join(HERE, "..", "td_live", "burst", "face_" + str(k).zfill(2) + ".jpg")
    if os.path.exists(p):
        out[str(k)] = round(DV.deviation(Image.open(p)), 3)
with open(os.path.join(HERE, "..", "td_live", "burst", "burst_dev.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
print("12 张爆开脸的偏离度:", out)
