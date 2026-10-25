"""手动让"巨大拼脸"场景马上出现一次（约 22 秒后回到万花筒）。在 Mac 终端运行：python3 test_giant.py"""
import json, os, time
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "td_live", "gaze_bridge")
tmp = os.path.join(d, "giant_test.json.tmp")
with open(tmp, "w", encoding="utf-8") as f:
    json.dump({"t": time.time()}, f)
os.replace(tmp, os.path.join(d, "giant_test.json"))
print("已触发一次巨大拼脸")
