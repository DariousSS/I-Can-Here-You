"""手动让面具马上出现一次（不用等随机间隔；要在万花筒场景里才会出现）。在 Mac 终端运行：python3 test_masks.py"""
import json, os, time
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "td_live", "gaze_bridge")
tmp = os.path.join(d, "mask_test.json.tmp")
with open(tmp, "w", encoding="utf-8") as f:
    json.dump({"t": time.time()}, f)
os.replace(tmp, os.path.join(d, "mask_test.json"))
print("已触发一次面具出现")
