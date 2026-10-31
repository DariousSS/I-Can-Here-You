# 撤销：让 /perform 重新显示整个 /project1，并删掉舞台容器
p = op('/project1')
pf = op('/perform')
pf.par.winop = op(p.fetch('sc_prev_perform', '/project1') or '/project1')
if p.op('sc_perfstage') is not None:
    p.op('sc_perfstage').destroy()
print('OK: /perform 已改回', pf.par.winop.eval())
