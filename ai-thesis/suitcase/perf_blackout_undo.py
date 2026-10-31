# 撤销：把 /project1 的背景改回 out1，删除 sc_perfswitch / sc_perfblack
p = op('/project1')
prev = p.fetch('sc_prev_top', '/project1/out1') or '/project1/out1'
p.par.top = op(prev)
for n in ('sc_perfswitch', 'sc_perfblack'):
    if p.op(n) is not None:
        p.op(n).destroy()
print('OK: /project1 背景已改回', p.par.top.eval())
