"""手动切到"棋盘"场景。在 Mac 终端运行：
    python3 test_board.py          # 只看棋盘（约 45 秒后回到万花筒）
    python3 test_board.py hit      # 命中测试：看亮着洋红色框的格子，共 24 个，每个 3 秒，结束后在 TD Textport 打印命中率
"""
import json, os, sys, time
mode = sys.argv[1] if len(sys.argv) > 1 else "show"
d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "td_live", "gaze_bridge")
tmp = os.path.join(d, "board_test.json.tmp")
with open(tmp, "w", encoding="utf-8") as f:
    json.dump({"t": time.time(), "mode": mode}, f)
os.replace(tmp, os.path.join(d, "board_test.json"))
print("已触发棋盘：", mode)
