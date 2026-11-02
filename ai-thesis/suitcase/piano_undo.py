# 还原 piano_setup.py：钢琴书形状的纹理改回原来的，删掉 sc_piano（没出问题别运行）
p = op('/project1')
prev = p.fetch('sc_prev_piano', None)
if prev:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        if c.name == prev[0]:
            c.op('parameters').par.Texture = prev[1]
o = p.op('sc_piano')
if o is not None:
    o.destroy()
print('已还原')
