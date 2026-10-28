# 在 TD 的 Textport 里运行：item4 直接用原来的万花筒纹理（castle_xf），前面只加一个"透明度"节点 sc_cloud：平时很淡，入侵时变亮
ITEM = 'item4'
p = op('/project1')
cl = p.op('sc_cloud') or p.create(levelTOP, 'sc_cloud')
cl.inputConnectors[0].connect(p.op('castle_xf'))
cl.par.opacity = 0.15
cl.nodeX, cl.nodeY = 1500, -3000
done = False
for c in op('/project1/kantanMapper/project/allShapes').children:
    pr = c.op('parameters')
    if c.name == ITEM and pr is not None and hasattr(pr.par, 'Texture'):
        cur = pr.par.Texture.eval()
        cur = str(getattr(cur, 'path', cur))
        if cur != '/project1/sc_cloud':
            p.store('sc_prev_cloud', (c.name, cur))
        pr.par.Texture = '/project1/sc_cloud'
        pr.par.Showtexture = True
        print('OK:', c.name, ':', cur, '-> sc_cloud（万花筒）')
        done = True
if not done:
    print('没找到形状', ITEM)
print('接下来运行 suitcase_setup.py，让它跟着入侵变亮')
