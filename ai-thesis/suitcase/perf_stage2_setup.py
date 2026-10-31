# 在 TD 的 Textport 里运行：让"表演模式"真正用的窗口 gz_win 显示一个舞台容器，舞台里是开关 sc_perfswitch：
#   0 = 原来的装置画面（map_fit），1 = 黑屏。按反斜杠键 \ 切换（keyboard_setup.py 里）。
# 撤销：运行 perf_stage2_undo.py（或 op('/project1/gz_win').par.winop = op('/project1/map_fit')）
p = op('/project1')
gz = p.op('gz_win')
src = gz.par.winop.eval() if gz is not None else None
if gz is None or src is None:
    print('找不到 gz_win 或它没有显示的对象，没改任何东西')
elif src.name == 'sc_perfstage':
    print('已经装好了（gz_win 已在显示舞台）')
else:
    # 先把之前误改的地方还原
    pf = op('/perform')
    if pf is not None and pf.par.winop.eval() is not None and pf.par.winop.eval().name == 'sc_perfstage':
        pf.par.winop = p
    if p.op('out1') is not None and p.par.top.eval() is not None and p.par.top.eval().name == 'sc_perfswitch':
        p.par.top = p.op('out1')
    w, h = src.width, src.height
    bk = p.op('sc_perfblack') or p.create(constantTOP, 'sc_perfblack')
    bk.par.outputresolution = 'custom'
    bk.par.resolutionw, bk.par.resolutionh = w, h
    bk.par.colorr = bk.par.colorg = bk.par.colorb = 0
    if hasattr(bk.par, 'alpha'):
        bk.par.alpha = 1
    sw = p.op('sc_perfswitch') or p.create(switchTOP, 'sc_perfswitch')
    sw.inputConnectors[0].connect(src)
    sw.inputConnectors[1].connect(bk)
    sw.par.index = 0
    st = p.op('sc_perfstage') or p.create(containerCOMP, 'sc_perfstage')
    st.nodeX, st.nodeY = 2900, -4600
    st.par.w, st.par.h = w, h
    st.par.top = sw
    st.par.topfill = 'best'
    p.store('sc_prev_gzwin', src.path)
    gz.par.winop = st
    print('OK: gz_win 现在显示舞台。原来显示：', src.path, '分辨率', w, h, '| 切换键：反斜杠 \\')
