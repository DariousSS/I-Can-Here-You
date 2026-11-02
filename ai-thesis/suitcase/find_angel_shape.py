# 只读：列出 Kantan 里所有形状的名字、纹理、是否显示、位置大小，找出显示天使（sc_left）的那个
for c in op('/project1/kantanMapper/project/allShapes').children:
    sp = c.op('parameters')
    if sp is None or not hasattr(sp.par, 'Texture'):
        continue
    cur = sp.par.Texture.eval()
    sc = c.op('script1')
    box = ''
    if sc is not None and len(sc.points):
        xs = [q.x for q in sc.points]
        ys = [q.y for q in sc.points]
        box = '位置 x %d~%d y %d~%d' % (min(xs), max(xs), min(ys), max(ys))
    print(c.name, '| 名字:', sp.par.Name.eval() if hasattr(sp.par, 'Name') else '-', '| 纹理:', getattr(cur, 'path', cur), '| 显示:', c.par.render.eval() if hasattr(c.par, 'render') else '-', '|', box)
