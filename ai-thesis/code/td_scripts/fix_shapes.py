# 在 TD 的 Textport 里运行：把 Kantan 里被点错纹理的"城堡部件"改回 /project1/castle_xf
# 规则：
#   - 海洋球形状（纹理 castle_ball_tf 或名字带 ball）：不动
#   - 面积特别大的形状（盖满画布的那个，手/天使/木偶用的）：不动
#   - 大小是零的形状（只是一个点）：不动，只提醒你把它删掉
#   - 其余所有形状：纹理一律设成 castle_xf，并让它显示画面
TEX = '/project1/castle_xf'
CANVAS_AREA = 1920 * 1080
if op(TEX) is None:
    print('找不到', TEX, '，没有改动。请先重新运行 gaze_setup.py 安装')
else:
    changed, kept, zero = [], [], []
    for c in op('/project1/kantanMapper/project/allShapes').children:
        p = c.op('parameters')
        if p is None or not hasattr(p.par, 'Texture'):
            continue
        nm = str(p.par.Name.eval()) if hasattr(p.par, 'Name') else ''
        cur = p.par.Texture.eval()
        path = str(getattr(cur, 'path', cur))
        sc = c.op('script1')
        area = 0.0
        if sc is not None:
            pts = [(q.x, q.y) for q in sc.points]
            if pts:
                area = (max(q[0] for q in pts) - min(q[0] for q in pts)) * (max(q[1] for q in pts) - min(q[1] for q in pts))
        if area < 50:
            zero.append(nm)
            continue
        if path in ('/project1/mask_L', '/project1/mask_R', '/project1/castle_tri'):
            kept.append(nm + '（面具/可淡出的三角形）')
            continue
        if path == '/project1/castle_ball_tf' or 'ball' in nm.lower():
            kept.append(nm + '（海洋球）')
            continue
        if area > 0.5 * CANVAS_AREA:
            kept.append(nm + '（盖满画布的叠加层）')
            continue
        if path != TEX:
            p.par.Texture = TEX
            changed.append(nm + '：' + path.split('/')[-1] + ' -> castle_xf')
        p.par.Showtexture = True
    print('已改回城堡纹理:', changed if changed else '没有需要改的')
    print('没动:', kept)
    if zero:
        print('这些形状大小是零（只是一个点），请在 Kantan 里选中它们按 Delete 删掉:', zero)
    print('提醒：盖满画布的叠加层是否存在？', '有' if any('叠加层' in k for k in kept) else '没有！请在 Kantan 里重新画一个盖满画布的长方形，再运行 castle_texture_hand.py')
