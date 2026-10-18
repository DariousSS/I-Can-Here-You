# 在 TD 的 Textport 里运行：把 Kantan 里所有"真正的形状"的纹理换成 /project1/gz_switch（方形的脸）
TEX = '/project1/gz_switch'
if op(TEX) is None:
    print('找不到', TEX, '，没有改动')
else:
    n = 0
    for c in op('/project1/kantanMapper/project/allShapes').children:
        p = c.op('parameters')
        if p is not None and hasattr(p.par, 'Texture'):
            p.par.Texture = TEX
            n += 1
    print('已把', n, '个形状的纹理设为', TEX)
