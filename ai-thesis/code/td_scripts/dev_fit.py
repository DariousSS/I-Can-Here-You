# 在 TD 的 Textport 里运行：量你画的两个"数字长方形"的宽高比，把数字的画布改成同样的比例（数字就不会被压扁或拉长）
# 画布宽固定 640，高 = 640 * 形状高 / 形状宽；比例存进 dev_res.json，以后重装也会沿用
import json
BR = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge'
got = {}
for c in op('/project1/kantanMapper/project/allShapes').children:
    p = c.op('parameters')
    if p is None or not hasattr(p.par, 'Texture'):
        continue
    v = p.par.Texture.eval()
    nm = str(getattr(v, 'path', v)).split('/')[-1]
    if nm in ('dev_L', 'dev_R'):
        sc = c.op('script1')
        pts = [(q.x, q.y) for q in sc.points] if sc is not None else []
        if pts:
            w = max(q[0] for q in pts) - min(q[0] for q in pts)
            h = max(q[1] for q in pts) - min(q[1] for q in pts)
            got[nm] = (w, h)
            print(nm, '形状大小 宽', int(w), '高', int(h), '比例', round(w / max(h, 1), 2))
if not got:
    print('没找到指向 dev_L / dev_R 的形状，请先运行 assign_dev.py')
else:
    for nm, (w, h) in got.items():
        t = op('/project1/dev_txt_' + nm[-1])
        t.par.resolutionw = 640
        t.par.resolutionh = max(60, int(round(640.0 * h / max(w, 1.0))))
        print(nm, '画布改成 640 x', t.par.resolutionh.eval())
    w, h = got.get('dev_L', got.get('dev_R'))
    with open(BR + '/dev_res.json', 'w', encoding='utf-8') as f:
        json.dump({'w': 640, 'h': max(60, int(round(640.0 * h / max(w, 1.0))))}, f)
