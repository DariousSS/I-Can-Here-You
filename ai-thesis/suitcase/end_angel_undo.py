# 还原 end_angel_setup.py：右墙字幕形状改回显示 sc_sub，并删掉 sc_endangel、sc_subfx（没出问题别运行）
p = op('/project1')
fx, sub = p.op('sc_subfx'), p.op('sc_sub')
n = 0
if fx is not None and sub is not None:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        sp = c.op('parameters')
        if sp is None or not hasattr(sp.par, 'Texture'):
            continue
        cur = sp.par.Texture.eval()
        if str(getattr(cur, 'path', cur)) == fx.path:
            sp.par.Texture = sub.path
            n += 1
for nm in ('sc_subfx', 'sc_endangel'):
    o = p.op(nm)
    if o is not None:
        o.destroy()
print('已还原：', n, '个形状改回 sc_sub，sc_subfx / sc_endangel 已删除')
