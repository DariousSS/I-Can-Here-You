# 在 TD 的 Textport 里运行：做一个"切换画面"的小窗口，按空格键 在"盒盖 / 床"两个画面之间切换。
# 只新建 sc_viewswitch，并让 sc_bedwin_cont 显示它；不改别的。运行后请再运行一次 keyboard_setup.py 让按键生效。
p = op('/project1')
bs, lid, ct = p.op('sc_bedscene'), p.op('sc_gamelid'), p.op('sc_bedwin_cont')
if bs is None or lid is None or ct is None:
    print('缺节点，请先运行 game_td_setup.py 和 second_screen_setup.py')
else:
    sw = p.op('sc_viewswitch') or p.create(switchTOP, 'sc_viewswitch')
    sw.nodeX, sw.nodeY = 2300, -4500
    sw.inputConnectors[0].connect(bs)
    sw.inputConnectors[1].connect(lid)
    sw.par.index = 0
    ct.par.top = sw
    print('OK: 窗口现在显示 sc_viewswitch。0=床，1=盒盖。')
