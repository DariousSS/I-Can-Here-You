# 在 TD 的 Textport 里运行：把你在 Kantan 里画的"结尾天使"长方形（Layer 里的 Name 改成 endangel）接上 sc_endangel，并按它的比例画天使。
p = op('/project1')
ea = p.op('sc_endangel')
if ea is None:
    print('找不到 sc_endangel，请先运行 end_angel_setup.py')
else:
    hit = None
    for c in op('/project1/kantanMapper/project/allShapes').children:
        sp = c.op('parameters')
        if sp is not None and hasattr(sp.par, 'Name') and str(sp.par.Name.eval()).strip().lower() == 'endangel':
            hit = c
    if hit is None:
        print('没找到名字叫 endangel 的形状：在 Kantan 里点中你画的长方形，把左边 Layer 里的 Name 改成 endangel，再运行一次')
    else:
        sc = hit.op('script1')
        pts = [(q.x, q.y) for q in sc.points] if sc is not None else []
        asp = 1.0
        if pts:
            bw = max(q[0] for q in pts) - min(q[0] for q in pts)
            bh = max(q[1] for q in pts) - min(q[1] for q in pts)
            if bw > 1 and bh > 1:
                asp = bw / bh
        ea.par.resolutionh = 1080
        ea.par.resolutionw = int(round(1080 * asp))
        ea.par.vec0valuex = asp
        sp = hit.op('parameters')
        sp.par.Texture = ea.path
        sp.par.Showtexture = True
        hit.par.render = True
        print('OK: 形状 endangel 已显示天使，宽高比', round(asp, 2), '（天使平时亮度 0，看不到，只有第 7 天结尾才出现）')
