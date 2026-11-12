# 在 TD 的 Textport 里运行（一次）：把线框书分成「书本左边」「书本右边」两个形状，各画一半。
# 柜子打开前后距离不一样，所以左右两边在 Kantan 里分开摆；整本书共用同一套书脊和翻页，翻页能从左边那个形状翻到右边那个形状。
# 新建：sc_book_L（左半边）、sc_book_R（右半边）。原来的 sc_book 和它的形状不删，只是把原来的「翻页书/书本」形状关掉（render 关）。
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
NAME_L, NAME_R = '书本左边', '书本右边'
p = op('/project1')
shapes = op('/project1/kantanMapper/project/allShapes').findChildren(maxDepth=4)
hit = {}
for c in shapes:
    sp = c.op('parameters')
    if sp is not None and hasattr(sp.par, 'Name'):
        nm = str(sp.par.Name.eval()).strip()
        if nm in (NAME_L, NAME_R):
            hit[nm] = c
if len(hit) != 2 or p.op('sc_book') is None or p.op('sc_book_pixel') is None:
    print('缺东西：需要 Kantan 里有「书本左边」「书本右边」两个形状，并且已经装过 book_setup.py（有 sc_book）。现在找到的形状：', list(hit.keys()))
else:
    def size(c):
        q = [(a.x, a.y) for a in c.op('script1').points]
        return max(a[0] for a in q) - min(a[0] for a in q), max(a[1] for a in q) - min(a[1] for a in q)
    wl, hl = size(hit[NAME_L])
    wr, hr = size(hit[NAME_R])
    asp = (wl + wr) / max(1.0, (hl + hr) / 2.0)           # 整本摊开的书的宽高比
    BH = 1080
    BW = int(round(BH * asp))
    bk = p.op('sc_book')
    ct = p.op('sc_cover_txt')
    ct.par.resolutionw, ct.par.resolutionh = BW, BH
    bk.par.resolutionw, bk.par.resolutionh = BW, BH
    for t in (bk,):
        try:
            t.seq.vec.numBlocks = 4
        except Exception as e:
            print('vec 序列设置失败：', repr(e)[:80])
        t.par.vec3name = 'uH'
        t.par.vec3valuex = 0.0
    for nm, half, nx in (('sc_book_L', 1.0, 2500), ('sc_book_R', 2.0, 2700)):
        t = p.op(nm) or p.create(glslTOP, nm)
        t.par.outputresolution = 'custom'
        t.par.resolutionw, t.par.resolutionh = int(BW / 2), BH
        t.inputConnectors[0].connect(ct)
        try:
            t.seq.vec.numBlocks = 4
        except Exception as e:
            print('vec 序列设置失败：', repr(e)[:80])
        for i, n in enumerate(('uF', 'uP', 'uC', 'uH')):
            setattr(t.par, 'vec%dname' % i, n)
        t.par.vec3valuex = half
        t.par.pixeldat = p.op('sc_book_pixel')            # 三个 GLSL 共用同一份着色器
        t.nodeX, t.nodeY = nx, -5000
    p.op('sc_book_pixel').text = open(BASE + '/book_shader.glsl', encoding='utf-8').read()
    for name, tex in ((NAME_L, '/project1/sc_book_L'), (NAME_R, '/project1/sc_book_R')):
        sp = hit[name].op('parameters')
        sp.par.Texture = tex
        sp.par.Showtexture = True
        hit[name].par.render = True
    for c in shapes:                                      # 关掉原来整块的书形状，免得叠在一起
        sp = c.op('parameters')
        if sp is not None and hasattr(sp.par, 'Name') and str(sp.par.Name.eval()).strip() in ('翻页书', '书本'):
            c.par.render = False
    p.store('bk_geo', (BW, BH))
    ge = op('/project1/sc_game_exec')
    G = ge.fetch('G', None)
    if G:
        G['bklr_paths'] = None
        G['bkshape_path'] = None
    print('OK：书已分成左右两半。整本宽高比', round(asp, 2), '（左', int(wl), 'x', int(hl), '，右', int(wr), 'x', int(hr), '）')
    print('着色器报错：', repr(p.op('sc_book_L').errors()), repr(p.op('sc_book_R').errors()))
