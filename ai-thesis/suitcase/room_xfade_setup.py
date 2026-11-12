# 在 TD 的 Textport 里运行（一次）：给房间图做"双缓冲"，修复第二天开始时房间闪一下消失。
# 原因：换天时直接改 sc_room 的图片文件，TD 重新读图的那一两帧会输出空白。现在改成两张图轮流：新图先读进后面那张，读好了再切过去。
p = op('/project1')
a = p.op('sc_room')
if a is None:
    print('没有 sc_room，先运行 game_td_setup.py')
else:
    b = p.op('sc_room_B') or p.create(moviefileinTOP, 'sc_room_B')
    b.par.file = a.par.file.eval()
    b.nodeX, b.nodeY = a.nodeX, a.nodeY - 150
    x = p.op('sc_room_x') or p.create(crossTOP, 'sc_room_x')
    x.inputConnectors[0].connect(a)
    x.inputConnectors[1].connect(b)
    x.par.cross = 0
    x.nodeX, x.nodeY = a.nodeX + 150, a.nodeY - 75
    gl = p.op('sc_gamelid')
    gl.inputConnectors[0].connect(x)
    print('OK：sc_gamelid 现在读 sc_room_x（sc_room 和 sc_room_B 轮流）。接着请重新装一次游戏代码（见下一条）')
