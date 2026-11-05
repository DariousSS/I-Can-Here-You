# 在 TD 的 Textport 里运行：整个竖屏的线框书。你在 Kantan 里画的、名字叫「翻页书」的长方形（盖满整个屏幕）显示这本书。
# 书只是线框：两页的轮廓 + 装订线 + 一页纸翻过去的动画；字不在书里，还是在你原来的两个长方形（右 = 她们的话 / 字幕那块，左 =「我的视角」）。
# 按钢琴中间偏左的键 → 从左往右翻；偏右的键 → 从右往左翻。书只在听故事的时候出现。
# 这个脚本也会清掉上一版（字在书里）建的节点，并把右墙字幕那块恢复成原来的字幕。
# 回退：运行 book_undo.py。
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
SHAPE_NAME = '翻页书'
ALT_NAMES = ('翻页书', '书本')      # 这两个名字的形状都认
p = op('/project1')
shapes = op('/project1/kantanMapper/project/allShapes').findChildren(maxDepth=4)    # 包括被拖进组（图层）里面的形状
# 1. 清掉上一版：形状的纹理换回原来的，再删节点
prev = p.fetch('sc_prev_wall', None)
if prev:
    for c in shapes:
        if c.name == prev[0]:
            c.op('parameters').par.Texture = prev[1]
    p.unstore('sc_prev_wall')
for n in ('sc_wall', 'sc_bk_sa', 'sc_bk_sb', 'sc_bk_la', 'sc_bk_ra', 'sc_bk_lb', 'sc_bk_rb'):
    if p.op(n) is not None:
        p.op(n).destroy()
# 2. 找「翻页书」
hit = None
for c in shapes:
    sp = c.op('parameters')
    if sp is not None and hasattr(sp.par, 'Name') and str(sp.par.Name.eval()).strip() in ALT_NAMES:
        hit = c
if hit is None:
    print('找不到名字叫', SHAPE_NAME, '的形状，没有建书。在 Kantan 里把你画的长方形 Name 改成它')
else:
    pts = [(q.x, q.y) for q in hit.op('script1').points]
    asp = 16.0 / 9.0
    if pts:
        bw = max(q[0] for q in pts) - min(q[0] for q in pts)
        bh = max(q[1] for q in pts) - min(q[1] for q in pts)
        if bw > 1 and bh > 1:
            asp = bw / bh
    BH = 1080
    BW = int(round(BH * asp))
    bk = p.op('sc_book') or p.create(glslTOP, 'sc_book')
    bk.par.outputresolution = 'custom'
    bk.par.resolutionw, bk.par.resolutionh = BW, BH
    ct = p.op('sc_cover_txt') or p.create(textTOP, 'sc_cover_txt')      # 封面上的书名（想改字：op('/project1/sc_cover_txt').par.text = '...'）
    ct.par.outputresolution = 'custom'
    ct.par.resolutionw, ct.par.resolutionh = BW, BH
    if str(ct.par.text.eval()).strip().lower() in ('', 'derivative'):
        ct.par.text = ' '                                     # 新建的 Text 节点默认写着 derivative，清成空白；书名你自己定
    for k, v in (('fontsizex', max(40, int(BW * 0.17))), ('fontcolorr', 1.0), ('fontcolorg', 1.0), ('fontcolorb', 1.0), ('alignx', 'center'), ('aligny', 'center'), ('font', 'Georgia')):
        try:
            setattr(ct.par, k, v)
        except Exception as e:
            print('封面字', k, '设置失败（不影响）', repr(e)[:50])
    ct.nodeX, ct.nodeY = 2300, -4900
    bk.inputConnectors[0].connect(ct)
    try:
        bk.seq.vec.numBlocks = 3
    except Exception as e:
        print('vec 序列设置失败：', repr(e)[:80])
    bk.par.vec0name = 'uF'
    bk.par.vec1name = 'uP'
    bk.par.vec2name = 'uC'
    bk.par.vec0valuex, bk.par.vec0valuey, bk.par.vec0valuez, bk.par.vec0valuew = 1.0, 1.0, BW / float(BH), 0.0
    bk.par.vec1valuex, bk.par.vec1valuey, bk.par.vec1valuez, bk.par.vec1valuew = 1.0, 0.0025, 0.085, 0.06
    bk.nodeX, bk.nodeY = 2500, -4800
    px = p.op('sc_book_pixel')
    if px is not None:
        px.text = open(BASE + '/book_shader.glsl', encoding='utf-8').read()
    sp = hit.op('parameters')
    cur = sp.par.Texture.eval()
    cur = str(getattr(cur, 'path', cur))
    if cur != '/project1/sc_book':
        p.store('sc_prev_book', (hit.name, cur))
    sp.par.Texture = '/project1/sc_book'
    sp.par.Showtexture = True
    hit.par.render = True
    p.store('bk_geo', (BW, BH))
    er = str(bk.errors() or '').strip()
    print('OK: 线框书已放进形状「' + SHAPE_NAME + '」，画布', BW, 'x', BH, '（宽高比', round(asp, 2), '）')
    print('着色器报错：' + er[:300] if er else '着色器没有报错')
    print('提示：如果书盖住了别的字，在 Kantan 左边的 Shapes 列表里把「翻页书」拖到最下面或最上面试试')
