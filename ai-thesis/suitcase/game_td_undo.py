# 在 TD 的 Textport 里运行：退出游戏。盖子的纹理换回原来的卧室（sc_lid），重新打开原来的字幕引擎，暂停游戏。
p = op('/project1')
ex = p.op('sc_game_exec')
if ex is not None:
    ex.par.active = False
for c in op('/project1/kantanMapper/project/allShapes').children:
    if c.name == 'item5' and c.op('parameters') is not None:
        c.op('parameters').par.Texture = '/project1/sc_lid'
pc = p.fetch('sc_prev_count', None)
if pc:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        if c.name == pc[0] and c.op('parameters') is not None:
            c.op('parameters').par.Texture = pc[1]
pk = p.fetch('sc_prev_cal', None)
if pk:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        if c.name == pk[0] and c.op('parameters') is not None:
            c.op('parameters').par.Texture = pk[1]
pz = p.fetch('sc_prev_intro', None)
if pz:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        if c.name == pz[0] and c.op('parameters') is not None:
            c.op('parameters').par.Texture = pz[1]
old = p.op('sc_sub_exec')
if old is not None:
    old.par.active = True
    old.store('S', None)
print('OK: 已退出游戏：盖子回到原来的卧室，字幕引擎恢复（从头开始）')
