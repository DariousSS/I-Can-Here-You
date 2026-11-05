# 在 TD 的 Textport 里运行：把被子画面里的"人脸万花筒"和"光点"各裁成一块，并把人脸万花筒贴到 sc_bedkantan 里叫「人脸万花筒」的形状上。
# 新建：sc_bed_face（人脸万花筒那一块）、sc_bed_dot（光点那一块），都是从 sc_bedscene 里裁出来的，不改 sc_bedscene。
# 裁的范围和游戏里的 bed_box / bed_dotbox 一致（改了这两个值，重新运行本脚本就跟着变）。
FACE_SHAPE = '人脸万花筒'
DOT_SHAPE = '光点出现区域'         # 光点被抓到时，出现在这个形状里（形状的范围 = 光点能出现的地方）
W, H = 1920, 1200
p = op('/project1')
bs = p.op('sc_bedscene')
ge = op('/project1/sc_game_exec')
cfg = dict(ge.fetch('cfg', {}) or {})
if cfg.get('bed_flip', True):
    cfg['bed_flip'] = False            # 被子画面本身不再转 180 度（裁剪才对得上位置）；倒挂的转向放到 Kantan 后面的 Flip 节点
    ge.store('cfg', cfg)
    print('已把 bed_flip 设成 False（转 180 度改由 sc_bedkantan_rot 负责）')
sv, sel = p.op('sc_viewswitch'), p.op('sc_bedkantan_sel')
if sv is not None and sel is not None:
    rot = p.op('sc_bedkantan_rot') or p.create(flipTOP, 'sc_bedkantan_rot')
    rot.nodeX, rot.nodeY = 2800, -4500
    rot.inputConnectors[0].connect(sel)
    rot.par.flipx = True
    rot.par.flipy = True
    sv.inputConnectors[0].connect(rot)
if bs is None:
    print('找不到 sc_bedscene')
else:
    boxes = (('sc_bed_face', cfg.get('bed_box', (0.025, 0.2, 0.4, 0.8)), 2800, FACE_SHAPE),
             ('sc_bed_dot', cfg.get('bed_dotbox', (0.62, 0.28, 0.94, 0.82)), 3000, DOT_SHAPE))
    made = {}
    for name, (x0, y0, x1, y1), nx, shape_name in boxes:
        c = p.op(name) or p.create(cropTOP, name)
        c.nodeX, c.nodeY = nx, -4600
        c.inputConnectors[0].connect(bs)
        c.par.cropleft, c.par.cropright = x0, x1                  # 裁剪节点的数值是比例（0~1），不是像素
        c.par.cropbottom, c.par.croptop = y0, y1
        made[name] = (c, shape_name)
        print(name, '输出大小：', c.width, 'x', c.height, '（应该是', round((x1 - x0) * W), 'x', round((y1 - y0) * H), '）')
    shapes = op('/project1/sc_bedkantan/kantanMapper/project/allShapes').findChildren(maxDepth=4)
    for name, (c, shape_name) in made.items():
        hit = None
        for s in shapes:
            sp = s.op('parameters')
            if sp is not None and hasattr(sp.par, 'Name') and str(sp.par.Name.eval()).strip() == shape_name:
                hit = sp
        if hit is None:
            print('没找到名字叫「' + shape_name + '」的形状，跳过', name)
        else:
            hit.par.Texture = c.path
            hit.par.Showtexture = True
            print('OK: 形状「' + shape_name + '」的纹理 =', c.path)
