# 回退 hint_setup.py：sc_sub 重新直接接回原来的字幕，删掉提示层（没出问题别运行）
p = op('/project1')
prev = op(p.fetch('sc_prev_sub_src', '/project1/sc_sub_txt'))
lv = p.op('sc_sub')
if lv is not None and prev is not None:
    lv.inputConnectors[0].connect(prev)
for n in ('sc_hint_mix', 'sc_hint_txt'):
    if p.op(n) is not None:
        p.op(n).destroy()
print('已回退')
