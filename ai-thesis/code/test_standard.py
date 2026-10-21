"""手动触发一次"标准人脸"流程（脸叠加 -> 手点 -> 打散 -> 回到万花筒）。在 Mac 终端运行：python3 test_standard.py"""
import json, os, time
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "td_live", "gaze_bridge")
tmp = os.path.join(d, "std_test.json.tmp")
with open(tmp, "w", encoding="utf-8") as f:
    json.dump({"t": time.time()}, f)
os.replace(tmp, os.path.join(d, "std_test.json"))
print("已触发一次标准人脸流程")
