# 在 TD 的 Textport 里运行：列出 Kantan 里每个形状的【你改的名字】【内部编号】【纹理】【位置】【是否显示】（只读，不改任何东西）
Wc, Hc = 1920.0, 1080.0
for c in op('/project1/kantanMapper/project/allShapes').children:
    pr = c.op('parameters')
    if pr is None or not hasattr(pr.par, 'Texture'):
        print(c.name, '| (组，没有纹理)')
        continue
    v = pr.par.Texture.eval()
    tex = '' if v is None else str(getattr(v, 'path', v)).split('/')[-1]
    nm = str(pr.par.Name.eval()) if hasattr(pr.par, 'Name') else '?'
    sc = c.op('script1')
    pts = [(q.x, q.y) for q in sc.points] if sc is not None else []
    if pts:
        x0, x1 = Wc / 2 + min(q[0] for q in pts), Wc / 2 + max(q[0] for q in pts)
        y0, y1 = Hc / 2 - max(q[1] for q in pts), Hc / 2 - min(q[1] for q in pts)
        pos = '左%d 上%d 右%d 下%d' % (x0, y0, x1, y1)
    else:
        pos = '(没有点)'
    print(c.name, '| 名字:', nm, '| 纹理:', tex if tex else '(空)', '|', pos, '|', '显示' if c.par.render.eval() else '隐藏')
