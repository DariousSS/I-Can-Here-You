# 回退 my_view_setup.py：形状「我的视角」的纹理换回原来的，删掉 sc_my_exec / sc_my / sc_my_txt（没出问题别运行）
p = op('/project1')
prev = p.fetch('sc_prev_my', None)
if prev:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        if c.name == prev[0]:
            c.op('parameters').par.Texture = prev[1]
for n in ('sc_my_exec', 'sc_my', 'sc_my_txt'):
    if p.op(n) is not None:
        p.op(n).destroy()
print('已回退')
