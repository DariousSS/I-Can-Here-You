# 在 TD 的 Textport 里运行：让 Kantan 里所有"真正的形状"都显示画面（而不是显示自己的颜色）
n = 0
for c in op('/project1/kantanMapper/project/allShapes').children:
    p = c.op('parameters')
    if p is not None and hasattr(p.par, 'Showtexture'):
        p.par.Showtexture = True
        n += 1
print('已让', n, '个形状显示画面')
