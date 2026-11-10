# 在 TD 的 Textport 里运行：撤销 heart_keys_setup.py（删掉 heart_exec，并让 heart.json 失效；桥接程序 3 秒后就不再按心率琴键）。
import os
p = op('/project1')
o = p.op('heart_exec')
if o is not None:
    o.destroy()
for key in ('hk_st', 'hk_fake', 'hk_base_secs'):
    try:
        p.unstore(key)
    except Exception:
        pass
try:
    os.remove('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge/heart.json')
except Exception:
    pass
print('已撤销：心率不再控制隐藏层。')
