# 在 TD 的 Textport 里运行：给"每个琴键是不同的句子 / Press one"的提示单独做一层字（不同字体、更大），叠在右墙字幕上。
# 做的事：复制字幕的 Text TOP 成 sc_hint_txt（居中、更大、换字体），再用一个 Add TOP（sc_sub_mix）把它和字幕叠在一起，交给 sc_sub。
# 回退：运行 hint_undo.py
p = op('/project1')
txt, lv = p.op('sc_sub_txt'), p.op('sc_sub')
if txt is None or lv is None:
    print('找不到 sc_sub_txt / sc_sub，没有改动')
elif p.op('sc_hint_txt') is not None:
    print('sc_hint_txt 已经存在，没有重复创建')
else:
    src = lv.inputConnectors[0].connections[0].owner if lv.inputConnectors[0].connections else None
    h = p.copy(txt, name='sc_hint_txt')
    h.nodeX, h.nodeY = txt.nodeX, txt.nodeY - 150
    h.par.text = ' '
    try:
        h.par.aligny = 'center'
        h.par.alignx = 'center'
    except Exception as e:
        print('对齐设置失败（不影响）', repr(e)[:60])
    try:
        h.par.font = 'Georgia'
        h.par.fontsizex = 70
    except Exception as e:
        print('字体设置失败（不影响）', repr(e)[:60])
    mix = p.create(addTOP, 'sc_hint_mix')
    mix.nodeX, mix.nodeY = txt.nodeX + 200, txt.nodeY - 75
    mix.inputConnectors[0].connect(src if src is not None else txt)
    mix.inputConnectors[1].connect(h)
    lv.inputConnectors[0].connect(mix)
    p.store('sc_prev_sub_src', src.path if src is not None else txt.path)
    print('OK: 已建好 sc_hint_txt + sc_hint_mix，sc_sub 现在显示 ', (src or txt).name, ' + 提示字')
