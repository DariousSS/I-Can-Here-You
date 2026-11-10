# 在 TD 的 Textport 里运行：把心率当成"钢琴曲"——心率比基准低/高多少，就弹到 AI 隐藏层的哪一个"键"（见 palette_lucy.json 的 "heart"）。
# 前提：先运行过 pulse_setup.py（有 /project1/arr_pulse：bpm、present），并且 gaze_bridge.py 在跑（重启一次，让它读到新代码）。
# 做了什么：新建 Execute DAT「heart_exec」，每 0.25 秒把 {bpm, base, present} 写进 td_live/gaze_bridge/heart.json；基准 = 戴上后前 20 秒的平均心率。
# 不改 gz_exec 和别的节点。撤销：运行 heart_keys_undo.py。
# Textport 里可用：
#   hk_test(75)   不接硬件假装心率（基准 70）：65=偏低键、70=中间键、85=偏高键
#   hk_real()     回到真实传感器
#   hk_base()     重新记基准（换一位观众）
#   hk_status()   看心率、基准、位置
import os
p = op('/project1')
BRIDGE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge'
if p.op('arr_pulse') is None:
    raise Exception('找不到 arr_pulse：请先运行 pulse_setup.py')

EXEC = '''import json, os, time
BRIDGE = %r
def onFrameEnd(frame):
    host = parent()
    w = op('/project1/arr_pulse')
    if w is None:
        return
    now = absTime.seconds
    s = host.fetch('hk_st', None) or {}
    if s.get('t', -1.0) > now + 0.5:
        s = {}
    dt = min(0.2, max(1e-3, now - s.get('t', now)))
    s['t'] = now
    if now - s.get('w', -9.0) < 0.25:
        host.store('hk_st', s)
        return
    s['w'] = now
    fake = float(host.fetch('hk_fake', 0))
    if fake > 0:
        bpm, present = fake, True
        if s.get('base') is None:
            s['base'] = 70.0
    else:
        bpm = w['bpm'].eval()
        present = w['present'].eval() > 0.5 and 40.0 < bpm < 150.0
    if present and s.get('base') is None:
        s['bsum'] = s.get('bsum', 0.0) + bpm * 0.25
        s['bt'] = s.get('bt', 0.0) + 0.25
        if s['bt'] >= float(host.fetch('hk_base_secs', 20.0)):
            s['base'] = s['bsum'] / s['bt']
    host.store('hk_st', s)
    d = {'bpm': round(float(bpm), 1), 'base': round(float(s.get('base') or 0.0), 1), 'present': 1 if present else 0}
    tmp = os.path.join(BRIDGE, 'heart.json.tmp')
    try:
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(d, fh)
        os.replace(tmp, os.path.join(BRIDGE, 'heart.json'))
    except Exception as e:
        print('heart_exec 写文件出错：', repr(e)[:80])
    return
''' % BRIDGE

ex = p.op('heart_exec') or p.create(executeDAT, 'heart_exec')
ex.nodeX, ex.nodeY = -200, -1950
ex.par.framestart = False
ex.par.frameend = True
ex.par.active = True
ex.text = EXEC

def hk_test(bpm=75):
    p.store('hk_fake', float(bpm))
    print('假心率 =', bpm, '（基准 70）。回到真实传感器：hk_real()')
def hk_real():
    p.store('hk_fake', 0)
    print('已回到真实传感器')
def hk_base():
    s = p.fetch('hk_st', None) or {}
    for key in ('base', 'bsum', 'bt'):
        s.pop(key, None)
    p.store('hk_st', s)
    print('重新记基准：接下来 20 秒保持放松')
def hk_status():
    s = p.fetch('hk_st', None) or {}
    w = op('/project1/arr_pulse')
    print('心率 %.0f | 基准 %s | 有信号 %d' % (w['bpm'].eval(), ('%.1f' % s['base']) if s.get('base') else '（还在记）', w['present'].eval()))
import builtins
for _f in (hk_test, hk_real, hk_base, hk_status):
    setattr(builtins, _f.__name__, _f)
print('OK：心率 -> 隐藏层琴键 已接好。没有硬件先试：hk_test(70)，再 hk_test(62)、hk_test(85)。别忘了重启 gaze_bridge.py。')
