# 在 TD 的 Textport 里运行：把"盖满画布的叠加层"（手/天使/木偶用的那个形状）的颜色改成纯黑，
# 这样它边缘混进来的橙色细线就看不见了。（颜色只影响边缘，不影响里面的画面。）
CANVAS_AREA = 1920 * 1080
done = []
for c in op('/project1/kantanMapper/project/allShapes').children:
    p = c.op('parameters')
    if p is None or not hasattr(p.par, 'Texture'):
        continue
    cur = p.par.Texture.eval()
    path = str(getattr(cur, 'path', cur))
    sc = c.op('script1')
    area = 0.0
    if sc is not None:
        pts = [(q.x, q.y) for q in sc.points]
        if pts:
            area = (max(q[0] for q in pts) - min(q[0] for q in pts)) * (max(q[1] for q in pts) - min(q[1] for q in pts))
    if path in ('/project1/scene_all', '/project1/scene_out', '/project1/hand_out') and area > 0.5 * CANVAS_AREA:
        for nm in ('Colorr', 'Colorg', 'Colorb'):
            if hasattr(p.par, nm):
                getattr(p.par, nm).val = 0.0
        if hasattr(p.par, 'Colora'):
            p.par.Colora.val = 1.0
        done.append(str(p.par.Name.eval()) + '（面积 ' + str(int(area)) + '）')
print('已把这些叠加层的颜色改成黑色:', done if done else '没有找到叠加层')
