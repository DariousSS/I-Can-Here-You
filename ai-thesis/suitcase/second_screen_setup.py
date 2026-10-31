# 在 TD 的 Textport 里运行：做"第二台投影仪（床）"的画面 sc_bedscene，和一个把它显示出来的窗口。
# 画面：天使一直在 + 每收集一个光点，被子上多一个光点（游戏代码会自动写光点）。只新建 sc_bed* / sc_win2 这几个节点，不改原来的任何东西。
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
p = op('/project1')
if p.op('sc_angel') is None:
    print('找不到 sc_angel（天使）：请先装好天使 angel_setup.py')
else:
    bs = p.op('sc_bedscene') or p.create(glslTOP, 'sc_bedscene')
    bs.inputConnectors[0].connect(p.op('sc_angel'))
    bs.par.outputresolution = 'custom'
    bs.par.resolutionw = 1920
    bs.par.resolutionh = 1200
    try:
        bs.seq.vec.numBlocks = 9
    except Exception as e_:
        print('sc_bedscene 的 vec 序列设置失败：', repr(e_)[:80])
    names = ['uS', 'uA'] + ['uD' + str(i) for i in range(7)]
    for i, nm in enumerate(names):
        setattr(bs.par, 'vec%dname' % i, nm)
    px = p.op('sc_bedscene_pixel')
    if px is not None:
        px.text = open(BASE + '/bed_shader.glsl', encoding='utf-8').read()
    bs.nodeX, bs.nodeY = 2100, -4300
    er = str(bs.errors() or '').strip()
    print('OK: 已新建 sc_bedscene（第二台投影仪的画面）', '| 着色器报错：' + er[:200] if er else '')
    # ---- 窗口：容器里放这个画面，再用窗口把容器投到另一个屏幕 ----
    ct = p.op('sc_bedwin_cont') or p.create(containerCOMP, 'sc_bedwin_cont')
    ct.nodeX, ct.nodeY = 2300, -4300
    for nm, v in (('w', 1920), ('h', 1200)):
        if hasattr(ct.par, nm):
            setattr(ct.par, nm, v)
        else:
            print('容器没有参数', nm)
    if hasattr(ct.par, 'top'):
        ct.par.top = bs
    else:
        print('容器没有 top 参数：请把容器里的背景画面手动设成 sc_bedscene。容器的参数名：', [x.name for x in ct.pars()][:60])
    wn = p.op('sc_win2') or p.create(windowCOMP, 'sc_win2')
    wn.nodeX, wn.nodeY = 2500, -4300
    if hasattr(wn.par, 'winop'):
        wn.par.winop = ct
    else:
        print('窗口没有 winop 参数')
    nmon = len(monitors)
    print('电脑现在认出', nmon, '个屏幕：', [(m.index, m.width, m.height) for m in monitors])
    print('窗口的相关参数名，请把下面这一行发给 Claude：')
    print([(x.name, x.eval()) for x in wn.pars() if any(k in x.name.lower() for k in ('mon', 'win', 'open', 'size', 'pos', 'border', 'top'))])
