# 在 TD 的 Textport 里运行：列出 Kantan 里每个形状的名字、用的纹理、在 1920x1080 画布上的位置（只读，不改任何东西）
Wc, Hc = 1920.0, 1080.0
for c in op('/project1/kantanMapper/project/allShapes').children:
    pr = c.op('parameters')
    if pr is None or not hasattr(pr.par, 'Texture'):
        continue
    v = pr.par.Texture.eval()
    tex = str(getattr(v, 'path', v)).split('/')[-1]
    sc = c.op('script1')
    pts = [(q.x, q.y) for q in sc.points] if sc is not None else []
    if pts:
        x0, x1 = Wc / 2 + min(q[0] for q in pts), Wc / 2 + max(q[0] for q in pts)
        y0, y1 = Hc / 2 - max(q[1] for q in pts), Hc / 2 - min(q[1] for q in pts)
        pos = '左%d 上%d 右%d 下%d' % (x0, y0, x1, y1)
    else:
        pos = '(没有点)'
    print(c.name, '->', tex, '|', pos, '|', '显示' if pr.par.Showtexture.eval() else '没显示')
