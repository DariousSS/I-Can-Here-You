"""凝视校准测试：依次看 中间/左/右/上/下，记录 TD 写进 params.json 的目光数字。
只读文件，很轻，不开模型。运行前 TD 要开着、摄像头开着。
"""
import json, time, os, statistics

BRIDGE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge'
PARAMS = BRIDGE + '/params.json'
STEPS = [('center', '屏幕中间'), ('left', '屏幕最左边'), ('right', '屏幕最右边'),
         ('up', '屏幕最上边'), ('down', '屏幕最下边')]
SEC = 3.0


def read():
    try:
        with open(PARAMS) as f:
            j = json.load(f)
        g = j['gaze']
        return g['x'], g['y'], g['on'], j.get('dbg') or {}
    except Exception:
        return None


def mean_xy():
    xs, ys, dbgs = [], [], []
    t0 = time.time()
    time.sleep(0.8)                      # 给眼睛一点时间到位
    while time.time() - t0 < SEC + 0.8:
        r = read()
        if r and r[2]:
            xs.append(r[0]); ys.append(r[1]); dbgs.append(r[3])
        time.sleep(0.1)
    if not xs:
        return None
    keys = set().union(*[d.keys() for d in dbgs]) if dbgs else set()
    dm = {k: statistics.mean([d[k] for d in dbgs if k in d]) for k in keys}
    dsd = {k: statistics.pstdev([d[k] for d in dbgs if k in d]) for k in keys}
    return statistics.mean(xs), statistics.mean(ys), statistics.pstdev(xs), statistics.pstdev(ys), dm, dsd


print('提示：头尽量别动，只动眼睛。每一步先看好位置，再按回车，然后保持看着不动约 4 秒。')
print('这里的"左/右"指你自己看屏幕时的左/右。\n')
res = {}
for key, label in STEPS:
    input(f'→ 请把眼睛看向【{label}】，看好后按回车：')
    m = mean_xy()
    if m is None:
        print('   没读到数据（脸没被检测到？）。先退出，检查 TD 和摄像头。')
        raise SystemExit
    res[key] = m
    print(f'   {label}: x={m[0]:.3f}  y={m[1]:.3f}   （抖动 x±{m[2]:.3f} y±{m[3]:.3f}）\n')

cx, cy = res['center'][0], res['center'][1]
dx = res['right'][0] - res['left'][0]
dy = res['down'][1] - res['up'][1]
print('========= 结果 =========')
print(f'左右范围（右-左）x: {dx:+.3f}   上下范围（下-上）y: {dy:+.3f}')
print('理想：左右范围 ≈ +0.6 以上、上下范围 ≈ +0.6 以上（正数=方向对）。')
print('负数 = 方向反了；绝对值很小 = 灵敏度不够。')
print(f'中间点: x={cx:.3f} y={cy:.3f}（理想接近 0.5）')

print('\n--- 上下候选信号（"下-上"的差；绝对值越大、并且比抖动大很多的越好）---')
for k in sorted(res['up'][4]):
    d = res['down'][4][k] - res['up'][4][k]
    noise = max(res['up'][5][k], res['down'][5][k], 1e-9)
    print(f'{k:14s} 下-上 = {d:+.4f}   抖动≈{noise:.4f}   比值={abs(d)/noise:.1f}')
print('\n--- 左右候选信号（"右-左"的差）---')
for k in sorted(res['left'][4]):
    d = res['right'][4][k] - res['left'][4][k]
    noise = max(res['left'][5][k], res['right'][5][k], 1e-9)
    print(f'{k:14s} 右-左 = {d:+.4f}   抖动≈{noise:.4f}   比值={abs(d)/noise:.1f}')

out = {k: {'x': v[0], 'y': v[1], 'dbg': v[4]} for k, v in res.items()}
with open(BRIDGE + '/calibration_test.json', 'w') as f:
    json.dump(out, f, indent=1)
print('\n已保存到 td_live/gaze_bridge/calibration_test.json，不用发给我，告诉我"测完了"我自己读。')
