# 在 TD 的 Textport 里运行：列出所有"城堡纹理"(castle_xf) 的形状在 1920x1080 画布上的位置（左, 上, 右, 下），天使就是照着它们躲开的（只读）
import time
Wc, Hc = 1920.0, 1080.0
rows = []
for c in op('/project1/kantanMapper/project/allShapes').children:
    pr = c.op('parameters')
    if pr is None or not hasattr(pr.par, 'Texture'):
        continue
    v = pr.par.Texture.eval()
    if str(getattr(v, 'path', v)) not in ('/project1/castle_xf', '/project1/castle_pc_top', '/project1/castle_pc_mid', '/project1/castle_pc_bot', '/project1/table_out'):
        continue
    sc = c.op('script1')
    pts = [(q.x, q.y) for q in sc.points] if sc is not None else []
    if not pts:
        continue
    x0, x1 = Wc / 2 + min(q[0] for q in pts), Wc / 2 + max(q[0] for q in pts)
    y0, y1 = Hc / 2 - max(q[1] for q in pts), Hc / 2 - min(q[1] for q in pts)
    rows.append((str(pr.par.Name.eval()), int(x0), int(y0), int(x1), int(y1), int((x1 - x0) * (y1 - y0)), bool(pr.par.Showtexture.eval())))
for r in rows:
    print(r[0], '| 左', r[1], '上', r[2], '右', r[3], '下', r[4], '| 面积', r[5], '| 显示' if r[6] else '| 没显示', '| 【很小，天使会忽略】' if r[5] < 3000 else '')
print('共', len(rows), '个。屏幕上真正能看见的城堡方块应该是 3 个左右；如果有名字对不上的、位置在很左或很右的，那就是多余的形状（可以在 Kantan 里选中按 Delete 删掉）')
