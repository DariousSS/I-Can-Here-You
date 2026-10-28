# 在 TD 的 Textport 里运行：把盖子形状的纹理还原成改之前的（并停掉 sc_exec）
LID = 'item5'
p = op('/project1')
prev = p.fetch('sc_prev_tex', '/project1/castle_xf')
for c in op('/project1/kantanMapper/project/allShapes').children:
    if c.name == LID and c.op('parameters') is not None:
        c.op('parameters').par.Texture = prev
        print('已还原', LID, '->', prev)
ex = p.op('sc_exec')
if ex is not None:
    ex.par.active = False
prev2 = p.fetch('sc_prev_tex2', {})
for c in op('/project1/kantanMapper/project/allShapes').children:
    if c.name in prev2 and c.op('parameters') is not None:
        c.op('parameters').par.Texture = prev2[c.name]
        print('已还原', c.name, '->', prev2[c.name])
pb = p.fetch('sc_prev_blob', None)
if pb:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        if c.name == pb[0] and c.op('parameters') is not None:
            c.op('parameters').par.Texture = pb[1]
            print('已还原', pb[0], '->', pb[1])
