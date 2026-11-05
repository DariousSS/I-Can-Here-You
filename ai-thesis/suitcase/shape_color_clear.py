# 在 TD 的 Textport 里运行：把被子 Kantan 里这几个形状自己的底色设成黑色 + 透明（纹理没贴上时也不会投出彩色块）。只改底色，不动纹理和位置。
NAMES = ('光点出现区域', '人脸万花筒', '行李箱')
shapes = op('/project1/sc_bedkantan/kantanMapper/project/allShapes').findChildren(maxDepth=4)
for s in shapes:
    sp = s.op('parameters')
    if sp is None or not hasattr(sp.par, 'Name'):
        continue
    nm = str(sp.par.Name.eval()).strip()
    if nm not in NAMES:
        continue
    cps = [q for q in sp.pars() if 'color' in q.name.lower()]
    print(nm, '底色参数:', [(q.name, round(float(q.eval()), 3)) for q in cps])
    for q in cps:
        q.val = 0.0
    print('  → 已设为 0（黑色、透明）')
