# 在 TD 的 Textport 里运行：让"表演模式"(/perform) 显示一个舞台容器，舞台里是 sc_perfswitch（0=装置画面 out1，1=黑屏）。
# 先确保已运行过 perf_blackout_setup.py（它建 sc_perfswitch / sc_perfblack）。
# 撤销：运行 perf_stage_undo.py（或 op('/perform').par.winop = op('/project1')）
p = op('/project1')
sw = p.op('sc_perfswitch')
pf = op('/perform')
if sw is None or pf is None:
    print('缺 sc_perfswitch 或 /perform：请先运行 perf_blackout_setup.py')
else:
    # 把 project1 的背景改回原来的 out1，避免两个地方同时改（开关只在舞台里用）
    if p.par.top.eval() == sw and p.op('out1') is not None:
        p.par.top = p.op('out1')
    st = p.op('sc_perfstage') or p.create(containerCOMP, 'sc_perfstage')
    st.nodeX, st.nodeY = 2900, -4600
    st.par.w, st.par.h = 1920, 1200
    st.par.top = sw
    st.par.topfill = 'best'
    p.store('sc_prev_perform', pf.par.winop.eval().path if pf.par.winop.eval() else '/project1')
    pf.par.winop = st
    print('OK: /perform 现在显示', pf.par.winop.eval(), '| 开关当前页：', sw.par.index.eval(), '(0=装置, 1=黑屏)')
    print('输入 0 是：', sw.inputs[0] if sw.inputs else None, '| 分辨率', sw.inputs[0].width, sw.inputs[0].height if sw.inputs else '')
