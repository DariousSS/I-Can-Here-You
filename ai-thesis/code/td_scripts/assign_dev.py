# 在 TD 的 Textport 里运行：把你在 Kantan 里新画的两个小长方形，指给"偏离度数字"
#  - 找：纹理还不是已知纹理、面积不大的新形状（取最靠左的两个里：x 更靠左的 -> dev_L 左面具的数字，靠右的 -> dev_R 右面具的数字）
#  - 如果新形状多于两个，按你要的名字指：把下面的 NAMES 改成 ('Rectangle20', 'Rectangle21')（左, 右），再运行
NAMES = None
KNOWN = ('/project1/castle_xf', '/project1/castle_tri', '/project1/castle_ball_tf', '/project1/scene_all', '/project1/scene_out', '/project1/hand_out', '/project1/mask_L', '/project1/mask_R', '/project1/dev_L', '/project1/dev_R', '/project1/castle_pc_top', '/project1/castle_pc_mid', '/project1/castle_pc_bot')
CANVAS_AREA = 1920 * 1080
if op('/project1/dev_L') is None:
    print('找不到 dev_L，请先重新运行 gaze_setup.py 安装')
else:
    shapes = []
    for c in op('/project1/kantanMapper/project/allShapes').children:
        p = c.op('parameters')
        if p is None or not hasattr(p.par, 'Texture'):
            continue
        nm = str(p.par.Name.eval()) if hasattr(p.par, 'Name') else ''
        cur = p.par.Texture.eval()
        path = str(getattr(cur, 'path', cur))
        sc = c.op('script1')
        area, cx = 0.0, 0.0
        if sc is not None:
            pts = [(q.x, q.y) for q in sc.points]
            if pts:
                area = (max(q[0] for q in pts) - min(q[0] for q in pts)) * (max(q[1] for q in pts) - min(q[1] for q in pts))
                cx = (max(q[0] for q in pts) + min(q[0] for q in pts)) / 2.0
        shapes.append((nm, path, area, cx, p))
    if NAMES:
        cand = [t for t in shapes if t[0] in NAMES]
        cand.sort(key=lambda t: NAMES.index(t[0]))
    else:
        cand = [t for t in shapes if t[1] not in KNOWN and 200 < t[2] < 0.1 * CANVAS_AREA]
        print('数字候选:', [(t[0], int(t[2])) for t in cand])
        cand = sorted(cand, key=lambda t: t[3])[:2] if len(cand) == 2 else cand
    if len(cand) != 2:
        print('需要刚好 2 个新形状，现在是', len(cand), '个。请在 Kantan 里在两个面具旁边各画一个小长方形（别的形状不要新增），再运行；或者改 NAMES。')
    else:
        cand[0][4].par.Texture = '/project1/dev_L'
        cand[0][4].par.Showtexture = True
        cand[1][4].par.Texture = '/project1/dev_R'
        cand[1][4].par.Showtexture = True
        print('左面具的数字:', cand[0][0], '| 右面具的数字:', cand[1][0])
