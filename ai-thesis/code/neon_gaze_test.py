"""Pupil Labs Neon 视线连接测试（在实验室里、Neon 的手机和你的 Mac 在同一个网络时运行）。
作用：只验证"Mac 能不能收到 Neon 的实时视线"，打印每秒 10 次的视线位置（场景相机画面里的像素坐标）。不保存任何东西。

用法（在 Mac 终端；第一次要先装库，装之前请先问我或问实验室老师）：
    python -m pip install pupil-labs-realtime-api
    python neon_gaze_test.py

说明：接口名字是我按官方文档的写法写的，第一次运行如果报错，把完整的报错发给我，我再改。
"""
import sys
import time

try:
    from pupil_labs.realtime_api.simple import discover_one_device
except Exception as e:
    print("还没装 pupil-labs-realtime-api（或导入失败）:", repr(e))
    print("装法： python -m pip install pupil-labs-realtime-api")
    sys.exit(1)

print("正在找 Neon（手机上要打开 Neon Companion app，并且和这台电脑在同一个 WiFi / 热点里）……")
device = discover_one_device(max_search_duration_seconds=15)
if device is None:
    print("15 秒内没找到设备。检查：1) 手机 app 开着 2) 同一个网络 3) 网络是否阻止设备互相发现（学校 WiFi 常见）")
    sys.exit(2)
print("找到设备:", device)

t_end = time.time() + 20
n = 0
try:
    while time.time() < t_end:
        g = device.receive_gaze_datum()
        n += 1
        if n % 10 == 0:
            print("视线 x=%.0f y=%.0f  （场景相机像素）" % (g.x, g.y))
        time.sleep(0.01)
finally:
    device.close()
print("共收到", n, "个视线数据，约 20 秒。")
