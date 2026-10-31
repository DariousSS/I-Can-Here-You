# 在 TD 的 Textport 里运行：表演模式（/perform 显示 /project1）里，空格在"装置画面"和"黑屏"之间切换。
# 只新建 sc_perfblack / sc_perfswitch 两个节点，并把 /project1 的背景从 out1 换成 sc_perfswitch；
# 撤销：运行 perf_blackout_undo.py（或 op('/project1').par.top = op('/project1/out1')）
p = op('/project1')
orig = p.op('out1')
if orig is None:
    print('找不到 /project1/out1，没有改任何东西')
else:
    bk = p.op('sc_perfblack') or p.create(constantTOP, 'sc_perfblack')
    bk.nodeX, bk.nodeY = 2500, -4600
    bk.par.outputresolution = 'custom'
    bk.par.resolutionw = max(orig.width, 16)
    bk.par.resolutionh = max(orig.height, 16)
    bk.par.colorr = bk.par.colorg = bk.par.colorb = 0
    sw = p.op('sc_perfswitch') or p.create(switchTOP, 'sc_perfswitch')
    sw.nodeX, sw.nodeY = 2700, -4600
    sw.inputConnectors[0].connect(orig)
    sw.inputConnectors[1].connect(bk)
    sw.par.index = 0
    if p.par.top.eval() != sw:
        p.store('sc_prev_top', p.par.top.eval().path if p.par.top.eval() else '')
        p.par.top = sw
    print('OK: /project1 背景 =', p.par.top.eval(), '| 空格切换：0=装置画面，1=黑屏')
