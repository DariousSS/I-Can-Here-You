# 在 TD 的 Textport 里运行：只读不改。打印每个 Kantan 形状现在用的纹理、有没有显示纹理、有没有开着；再打印几个相关节点的报错和入侵状态。
p = op('/project1')
print('---- 形状 ----')
for c in op('/project1/kantanMapper/project/allShapes').children:
    pr = c.op('parameters')
    if pr is None or not hasattr(pr.par, 'Texture'):
        continue
    v = pr.par.Texture.eval()
    tex = '（空）' if v is None else str(getattr(v, 'path', v))
    try:
        label = str(pr.par.Name.eval())
    except Exception:
        label = ''
    try:
        show = pr.par.Showtexture.eval()
    except Exception:
        show = '?'
    print(c.name, '|', label, '| 纹理:', tex, '| 显示纹理:', show, '| 开着:', c.par.render.eval())
print('---- 节点报错（空 = 没有错）----')
for nm in ('sc_pull', 'sc_maskL', 'sc_maskR', 'mask_R', 'sc_blob', 'sc_left', 'sc_angel', 'sc_gamelid', 'sc_room'):
    n = p.op(nm)
    print(nm, '|', '没有这个节点' if n is None else (str(n.errors() or '').strip()[:120] or 'OK'))
ex = p.op('sc_exec')
s = ex.fetch('s', None) if ex is not None else None
if s:
    print('---- 故事状态 ---- 阶段:', s.get('phase'), '| 入侵程度:', round(s.get('inv', 0.0), 2), '| 房间故障:', round(s.get('gl', 0.0), 2))
g = p.op('sc_game_exec')
print('游戏:', '没装' if g is None else ('开着' if g.par.active else '暂停'), '| 字幕引擎:', '没有' if p.op('sc_sub_exec') is None else ('开着' if p.op('sc_sub_exec').par.active else '暂停'))
