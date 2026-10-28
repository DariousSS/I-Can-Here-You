# 在 TD 的 Textport 里运行：把 hide_old_shapes.py 换掉的旧纹理还原
p = op('/project1')
saved = p.fetch('sc_hidden', {})
for c in op('/project1/kantanMapper/project/allShapes').children:
    if c.name in saved and c.op('parameters') is not None:
        c.op('parameters').par.Texture = saved[c.name]
        print(c.name, '已还原为', saved[c.name])
