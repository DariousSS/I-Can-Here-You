# 在 TD 的 Textport 里运行：把海洋球专用的形状的纹理换成 /project1/castle_ball_tf
# 优先找名字里带 ball 的形状（在 Kantan 里点中它，把 Name 改成 Ball1）；
# 如果一个都没找到，就用"最后画的那个形状"（所以请把球的长方形留到最后画）。
TEX = '/project1/castle_ball_tf'
if op(TEX) is None:
    print('找不到', TEX, '，没有改动。请先重新运行 gaze_setup.py 安装')
else:
    shapes = []
    for c in op('/project1/kantanMapper/project/allShapes').children:
        p = c.op('parameters')
        if p is not None and hasattr(p.par, 'Texture'):
            shapes.append((c, p))
    names = [str(p.par.Name.eval()) if hasattr(p.par, 'Name') else '' for c, p in shapes]
    print('现有形状名字:', names)
    targets = [sp for sp, nm in zip(shapes, names) if 'ball' in nm.lower()]
    if not targets and shapes:
        targets = [shapes[-1]]
        print('没有名字带 ball 的形状，改用最后画的那个:', names[-1])
    for c, p in targets:
        p.par.Texture = TEX
        p.par.Showtexture = True
    print('已把', len(targets), '个形状设为海洋球纹理', TEX)
