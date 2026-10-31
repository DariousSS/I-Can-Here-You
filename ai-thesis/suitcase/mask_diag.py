# 在 TD 的 Textport 里运行（只读，不改任何东西）：看左面具 / 右脸 / 拉扯 各自现在输出什么颜色，找出左脸为什么是白的
import numpy as np
p = op('/project1')
ex = p.op('sc_exec')
S = ex.fetch('s', {}) if ex is not None else {}
print('故事阶段', S.get('phase'), '| 入侵程度 inv', round(float(S.get('inv', -1)), 2), '| sc_exec 开着吗', None if ex is None else bool(ex.par.active))
for nm in ('mask_R', 'sc_maskR', 'sc_maskL', 'sc_pull'):
    t = p.op(nm)
    if t is None:
        print(nm, '：没有这个节点')
        continue
    try:
        a = t.numpyArray()
        h, w = a.shape[0], a.shape[1]
        ys, xs = np.where(a[:, :, 3] > 0.5)
        mid = a[h // 2, w // 2]
        print(nm, '|', w, 'x', h, '| 正中间 RGBA', [round(float(v), 2) for v in mid], '| 不透明像素占', round(float((a[:, :, 3] > 0.5).mean()), 2), '| 不透明处平均颜色', [round(float(v), 2) for v in a[a[:, :, 3] > 0.5][:, :3].mean(axis=0)] if len(xs) else '无', '| 报错', str(t.errors() or '无')[:80])
    except Exception as e:
        print(nm, '读取失败', repr(e)[:100])
l = p.op('sc_maskL')
if l is not None:
    print('sc_maskL 的 opacity =', l.par.opacity.eval(), '| 输入是', [str(getattr(c.connections[0].owner, 'path', '')) if c.connections else '空' for c in l.inputConnectors])
