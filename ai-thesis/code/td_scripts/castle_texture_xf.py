# 在 TD 的 Textport 里运行：把 Kantan 里所有"真正的形状"的纹理换成 /project1/castle_xf（方形脸 <-> 黑白注意力图）
# 名字里带 ball 的形状（海洋球专用）会被跳过，不会被改掉。
TEX = '/project1/castle_xf'
if op(TEX) is None:
    print('找不到', TEX, '，没有改动。请先重新运行 gaze_setup.py 安装')
else:
    n = 0
    skipped = 0
    for c in op('/project1/kantanMapper/project/allShapes').children:
        p = c.op('parameters')
        if p is not None and hasattr(p.par, 'Texture'):
            nm = str(p.par.Name.eval()) if hasattr(p.par, 'Name') else ''
            cur = p.par.Texture.eval()
            if 'ball' in nm.lower() or str(getattr(cur, 'path', cur)) == '/project1/castle_ball_tf':
                skipped += 1
                continue
            p.par.Texture = TEX
            n += 1
    print('已把', n, '个形状的纹理设为', TEX, '；跳过海洋球形状', skipped, '个')
