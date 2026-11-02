# 在 TD 的 Textport 里运行：把第二个场景（sc_bedscene）升级成"房间放大地图 + 木头手 + 光点物品"。
# 只改 sc_bedscene，新建 sc_woodhand（木头手图）；并让表演模式舞台开关的第 1 路显示 sc_bedscene（空格键/反斜杠 \ 切换）。
# 先要运行过 second_screen_setup.py 和 perf_stage2_setup.py。
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis'
p = op('/project1')
bs, room = p.op('sc_bedscene'), p.op('sc_room')
if bs is None or room is None:
    print('缺 sc_bedscene 或 sc_room：请先运行 second_screen_setup.py 和 game_td_setup.py')
else:
    hd = p.op('sc_woodhand') or p.create(moviefileinTOP, 'sc_woodhand')
    hd.par.file = BASE + '/assets/hand/hand_sprite.png'
    hd.nodeX, hd.nodeY = 1900, -4300
    kal = p.op('castle_xf') or p.op('gz_switch') or p.op('gz_over')
    bs.inputConnectors[1].connect(kal if kal is not None else room)
    print('第二个场景输入 1（左床方块的万花筒人脸）=', kal.name if kal is not None else '没找到，暂用房间图')
    bs.inputConnectors[2].connect(hd)
    try:
        bs.seq.vec.numBlocks = 8
    except Exception as e_:
        print('vec 序列设置失败：', repr(e_)[:80])
    for i, nm in enumerate(['uS', 'uA', 'uD', 'uH', 'uR', 'uP', 'uL', 'uK']):
        setattr(bs.par, 'vec%dname' % i, nm)
    px = p.op('sc_bedscene_pixel')
    if px is not None:
        px.text = open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase/bed_shader.glsl', encoding='utf-8').read()
    er = str(bs.errors() or '').strip()
    print('OK: sc_bedscene 已升级 | 着色器报错：' + er[:300] if er else 'OK: sc_bedscene 已升级，没有着色器报错')
    sw = p.op('sc_perfswitch')
    if sw is not None:
        sw.inputConnectors[1].connect(bs)
        print('OK: 表演模式开关的第 1 路 = sc_bedscene（第二个场景），第 0 路 = 装置画面')

