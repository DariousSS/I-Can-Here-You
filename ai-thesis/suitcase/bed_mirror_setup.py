# 在 TD 的 Textport 里运行：在第二个场景左床方块里加"镜像字"（左右反写，要用镜子才读得懂）。
# 新建 sc_mirror_txt（Text TOP）→ sc_mirror_flip（Flip TOP，左右翻转）→ 接到 sc_bedscene 的输入 0（原来是天使，现在不用）。
# 换句子：op('/project1/sc_mirror_txt').par.text = 'I just wanted to see.'
p = op('/project1')
bs = p.op('sc_bedscene')
if bs is None:
    print('找不到 sc_bedscene，请先运行 second_screen_setup.py')
else:
    t = p.op('sc_mirror_txt') or p.create(textTOP, 'sc_mirror_txt')
    t.nodeX, t.nodeY = 2200, -4500
    t.par.text = "I'm in my own room."
    for k, v in (('outputresolution', 'custom'), ('resolutionw', 640), ('resolutionh', 120), ('fontsizex', 56), ('alignx', 'center'), ('aligny', 'center'),
                 ('fontcolorr', 1), ('fontcolorg', 1), ('fontcolorb', 1), ('bgcolorr', 0), ('bgcolorg', 0), ('bgcolorb', 0), ('bgalpha', 1)):
        try:
            setattr(t.par, k, v)
        except Exception as e_:
            print('文字参数没设成', k, repr(e_)[:60])
    f = p.op('sc_mirror_flip') or p.create(flipTOP, 'sc_mirror_flip')
    f.nodeX, f.nodeY = 2400, -4500
    f.inputConnectors[0].connect(t)
    try:
        f.par.flipx = True
    except Exception as e_:
        print('Flip 参数没设成：', repr(e_)[:80])
    try:
        bs.seq.vec.numBlocks = 9
        bs.par.vec8name = 'uT'
    except Exception as e_:
        print('vec 序列设置失败：', repr(e_)[:80])
    bs.inputConnectors[0].connect(f)
    px = p.op('sc_bedscene_pixel')
    if px is not None:
        px.text = open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase/bed_shader.glsl', encoding='utf-8').read()
    er = str(bs.errors() or '').strip()
    print('OK: 镜像字已加入第二个场景 | 着色器报错：' + er[:300] if er else 'OK: 镜像字已加入第二个场景，没有着色器报错')
