# 在 TD 的 Textport 里运行：字幕下面的小钢琴。观众按哪个键，屏幕上对应的琴键就亮一下（打字期间一直亮，打完慢慢暗掉）。
# 用 Kantan 里名字叫"钢琴书"的形状（你画的那个长方形）。新建 sc_piano（GLSL TOP），把"钢琴书"的纹理从 sc_black 换成 sc_piano（旧纹理记下来，piano_undo.py 可还原）。
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
SHAPE_NAME = '钢琴书'
p = op('/project1')
hit = None
for c in op('/project1/kantanMapper/project/allShapes').children:
    sp = c.op('parameters')
    if sp is not None and hasattr(sp.par, 'Name') and str(sp.par.Name.eval()).strip() == SHAPE_NAME:
        hit = c
if hit is None:
    print('找不到名字叫', SHAPE_NAME, '的形状，没有改动。在 Kantan 里把你画的长方形 Name 改成它')
else:
    pts = [(q.x, q.y) for q in hit.op('script1').points]
    asp = 3.0
    if pts:
        bw = max(q[0] for q in pts) - min(q[0] for q in pts)
        bh = max(q[1] for q in pts) - min(q[1] for q in pts)
        if bw > 1 and bh > 1:
            asp = bw / bh
    pn = p.op('sc_piano') or p.create(glslTOP, 'sc_piano')
    pn.par.outputresolution = 'custom'
    pn.par.resolutionh = 256
    pn.par.resolutionw = max(128, int(round(256 * asp)))
    try:
        pn.seq.vec.numBlocks = 3
    except Exception as e_:
        print('vec 序列设置失败：', repr(e_)[:80])
    pn.par.vec0name = 'uP'
    pn.par.vec1name = 'uS'
    pn.par.vec2name = 'uV'
    pn.par.vec0valuex = asp
    pn.par.vec0valuey = 0.0
    pn.par.vec0valuez = 0.0
    pn.par.vec0valuew = 0.0
    pn.par.vec2valuex = 0.0
    px = p.op('sc_piano_pixel')
    if px is not None:
        px.text = open(BASE + '/piano_shader.glsl', encoding='utf-8').read()
    pn.nodeX, pn.nodeY = 2000, -4300
    sp = hit.op('parameters')
    cur = sp.par.Texture.eval()
    cur = str(getattr(cur, 'path', cur))
    if cur != '/project1/sc_piano':
        p.store('sc_prev_piano', (hit.name, cur))
    sp.par.Texture = '/project1/sc_piano'
    sp.par.Showtexture = True
    hit.par.render = True
    er = str(pn.errors() or '').strip()
    print('OK: 钢琴已放进形状「' + SHAPE_NAME + '」（' + hit.name + '），宽高比', round(asp, 2), '| 着色器报错：' + er[:300] if er else 'OK: 钢琴已放进形状「' + SHAPE_NAME + '」（' + hit.name + '），宽高比 ' + str(round(asp, 2)) + '，着色器没有报错')
