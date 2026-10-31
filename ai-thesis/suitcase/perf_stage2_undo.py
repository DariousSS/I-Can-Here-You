# 撤销：让 gz_win 重新显示原来的画面，并删除舞台、开关、黑屏
p = op('/project1')
prev = p.fetch('sc_prev_gzwin', '/project1/map_fit') or '/project1/map_fit'
p.op('gz_win').par.winop = op(prev)
for n in ('sc_perfstage', 'sc_perfswitch', 'sc_perfblack'):
    if p.op(n) is not None:
        p.op(n).destroy()
print('OK: gz_win 已改回显示', p.op('gz_win').par.winop.eval())
