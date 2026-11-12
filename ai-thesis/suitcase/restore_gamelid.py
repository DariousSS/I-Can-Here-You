# 在 TD 的 Textport 里运行：把盖子形状（item5）的纹理改回游戏版 sc_gamelid（新版模拟人生房间 + 光点）
p = op('/project1')
if p.op('sc_gamelid') is None:
    print('没有 sc_gamelid：请先运行 game_td_setup.py')
else:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        if c.name == 'item5':
            c.op('parameters').par.Texture = '/project1/sc_gamelid'
            c.op('parameters').par.Showtexture = True
            c.par.render = True
            print('OK：盖子 item5 纹理 = sc_gamelid')
