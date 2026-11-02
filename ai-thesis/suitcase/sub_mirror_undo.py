# 还原 sub_mirror_setup.py：把右墙字幕的形状改回显示 sc_sub，并删掉 sc_sub_flip（没出问题别运行）
p = op('/project1')
f = p.op('sc_sub_flip')
sub = p.op('sc_sub')
n = 0
if f is not None and sub is not None:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        sp = c.op('parameters')
        if sp is None or not hasattr(sp.par, 'Texture'):
            continue
        cur = sp.par.Texture.eval()
        if str(getattr(cur, 'path', cur)) == f.path:
            sp.par.Texture = sub.path
            n += 1
if f is not None:
    f.destroy()
print('已还原：', n, '个形状改回 sc_sub，sc_sub_flip 已删除')
