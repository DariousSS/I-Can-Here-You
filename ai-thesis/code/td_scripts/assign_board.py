# 在 TD 的 Textport 里运行：把你在 Kantan 里新画的"棋盘方块"指给 board_only（只在棋盘场景才出现，平时透明，不会盖住城堡）
# 自动找：纹理还不是已知纹理、面积够大的新形状（只有一个的时候直接指派）。有好几个时，把 NAME 改成你那个方块的名字。
NAME = None
TEX = '/project1/board_only'          # 将来桌子上改用 /project1/table_out（平时是方形万花筒）
KNOWN = ('/project1/castle_xf', '/project1/castle_tri', '/project1/castle_ball_tf', '/project1/scene_all', '/project1/scene_out', '/project1/hand_out', '/project1/mask_L', '/project1/mask_R', '/project1/dev_L', '/project1/dev_R', '/project1/castle_pc_top', '/project1/castle_pc_mid', '/project1/castle_pc_bot', '/project1/table_out', '/project1/board_only')
if op('/project1/board_only') is None:
    print('找不到 board_only，请先重新运行 gaze_setup.py 安装')
else:
    shapes = []
    for c in op('/project1/kantanMapper/project/allShapes').children:
        p = c.op('parameters')
        if p is None or not hasattr(p.par, 'Texture'):
            continue
        nm = str(p.par.Name.eval())
        v = p.par.Texture.eval()
        path = str(getattr(v, 'path', v) or '')
        sc = c.op('script1')
        pts = [(q.x, q.y) for q in sc.points] if sc is not None else []
        area = (max(q[0] for q in pts) - min(q[0] for q in pts)) * (max(q[1] for q in pts) - min(q[1] for q in pts)) if pts else 0.0
        shapes.append((nm, path, area, p))
    if NAME:
        cand = [t for t in shapes if t[0] == NAME]
    else:
        cand = [t for t in shapes if t[1] not in KNOWN and t[2] > 50000]
        print('候选:', [(t[0], t[1].split('/')[-1] or '(没纹理)', int(t[2])) for t in cand])
    if len(cand) != 1:
        print('需要刚好 1 个新方块，现在是', len(cand), '个。请在 Kantan 里画好那一个，或者把上面的 NAME 改成它的名字再运行。所有形状:', [t[0] for t in shapes])
    else:
        cand[0][3].par.Texture = TEX
        cand[0][3].par.Showtexture = True
        print('已把', cand[0][0], '指给', TEX.split('/')[-1])
