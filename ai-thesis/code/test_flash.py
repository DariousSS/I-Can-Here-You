"""手动触发一次"海洋球涌上来"（不用等诡异的声音）。在 Mac 终端运行：python3 test_flash.py"""
import json, os, time
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "td_live", "gaze_bridge")
tmp = os.path.join(d, "flash.json.tmp")
with open(tmp, "w", encoding="utf-8") as f:
    json.dump({"n": 0, "t": time.time()}, f)
os.replace(tmp, os.path.join(d, "flash.json"))
print("已触发一次海洋球")
