"""手动触发一次木偶戏（两只手吊着兔子）。在 Mac 终端运行：python3 test_puppet.py"""
import json, os, time
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "td_live", "gaze_bridge")
tmp = os.path.join(d, "puppet_test.json.tmp")
with open(tmp, "w", encoding="utf-8") as f:
    json.dump({"t": time.time()}, f)
os.replace(tmp, os.path.join(d, "puppet_test.json"))
print("已触发一次木偶戏")
