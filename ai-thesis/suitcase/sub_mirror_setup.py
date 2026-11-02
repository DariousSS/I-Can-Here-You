# 在 TD 的 Textport 里运行：把右墙上"按琴键后打出来的字"整个左右反写（观众背对墙，举镜子才读得懂）。
# 做法：新建 sc_sub_flip（Flip TOP，左右翻转，吃 sc_sub 的画面），把 Kantan 里原来显示 sc_sub 的形状改成显示 sc_sub_flip。
# 原来的纹理会记下来，sub_mirror_undo.py 可以还原。别的形状、别的节点都不动。
p = op('/project1')
sub = p.op('sc_sub')
if sub is None:
    print('找不到 sc_sub（右墙字幕），没有改动')
else:
    f = p.op('sc_sub_flip') or p.create(flipTOP, 'sc_sub_flip')
    f.nodeX, f.nodeY = sub.nodeX + 200, sub.nodeY
    f.inputConnectors[0].connect(sub)
    try:
        f.par.flipx = True
    except Exception as e_:
        print('Flip 参数没设成：', repr(e_)[:80])
    changed = []
    for c in op('/project1/kantanMapper/project/allShapes').children:
        sp = c.op('parameters')
        if sp is None or not hasattr(sp.par, 'Texture'):
            continue
        cur = sp.par.Texture.eval()
        path = str(getattr(cur, 'path', cur))
        if path == sub.path:
            sp.par.Texture = f.path
            sp.par.Showtexture = True
            changed.append(c.name)
    f.store('changed', changed)
    print('OK: 右墙字幕已改成左右反写（形状：' + ', '.join(changed) + '）' if changed else '没找到显示 sc_sub 的 Kantan 形状，Flip 已建好但墙上还没有改，请把这行输出贴给我')
