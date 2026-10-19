# 在 TD 的 Textport 里运行：把"手/木偶/天使"专用的形状的纹理换成 /project1/scene_all
# 自动挑选：排除城堡方块（castle_xf）和海洋球（castle_ball_tf）之后，面积最大的那个形状（就是盖满画布的那个）。
# 如果有名字里带 hand 的形状，优先用它。
TEX = '/project1/scene_all'
if op(TEX) is None:
    print('找不到', TEX, '，没有改动。请先重新运行 gaze_setup.py 安装')
else:
    cands = []
    for c in op('/project1/kantanMapper/project/allShapes').children:
        p = c.op('parameters')
        if p is None or not hasattr(p.par, 'Texture'):
            continue
        cur = p.par.Texture.eval()
        path = str(getattr(cur, 'path', cur))
        nm = str(p.par.Name.eval()) if hasattr(p.par, 'Name') else ''
        if path in ('/project1/castle_xf', '/project1/castle_ball_tf') or 'ball' in nm.lower():
            continue
        sc = c.op('script1')
        area = 0.0
        if sc is not None:
            pts = [(q.x, q.y) for q in sc.points]
            if pts:
                area = (max(q[0] for q in pts) - min(q[0] for q in pts)) * (max(q[1] for q in pts) - min(q[1] for q in pts))
        cands.append((area, nm, c, p))
    for area, nm, c, p in cands:
        print('候选:', nm, '面积', int(area), '（盖满画布约 2073600）')
    named = [t for t in cands if 'hand' in t[1].lower()]
    pick = named[0] if named else (max(cands, key=lambda t: t[0]) if cands else None)
    if pick is None:
        print('没有找到可用的形状，没有改动')
    else:
        pick[3].par.Texture = TEX
        pick[3].par.Showtexture = True
        print('已把', pick[1], '设为手/木偶/天使纹理', TEX, '；面积', int(pick[0]))
        if pick[0] < 1000000:
            print('注意：这个形状面积太小，可能没有盖满画布，天使会显示不全。请在 Kantan 里把它的大小改成 1920 x 1080')
