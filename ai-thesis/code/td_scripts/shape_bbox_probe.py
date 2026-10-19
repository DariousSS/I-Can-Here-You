# 在 TD 的 Textport 里运行（只读）：每个 Kantan 形状的纹理、是否显示画面、在画布上占的范围 -> td_live/shape_bbox_probe.txt
lines = ['Kantan 画布 1920x1080，原点在中心：盖满画布的形状 bbox 应该约 (-960, -540) 到 (960, 540)']
root = op('/project1/kantanMapper/project/allShapes')
for c in root.children:
    pr = c.op('parameters')
    if pr is None or not hasattr(pr.par, 'Texture'):
        continue
    v = pr.par.Texture.eval()
    nm = str(pr.par.Name.eval())
    show = pr.par.Showtexture.eval() if hasattr(pr.par, 'Showtexture') else '?'
    sc = c.op('script1')
    bb = None
    if sc is not None:
        pts = [(q.x, q.y) for q in sc.points]
        if pts:
            bb = (round(min(p[0] for p in pts)), round(min(p[1] for p in pts)), round(max(p[0] for p in pts)), round(max(p[1] for p in pts)))
    lines.append(nm + ' | texture=' + str(getattr(v, 'path', v)) + ' | showtexture=' + str(show) + ' | bbox=' + str(bb))
for path in ('/project1/kantanMapper/out1', '/project1/scene_all', '/project1/angel_fade'):
    o = op(path)
    try:
        a = o.numpyArray()
        lines.append(path + ' size=' + str(o.width) + 'x' + str(o.height) + ' mean rgba=' + str([round(float(a[:, :, i].mean()), 4) for i in range(4)]))
    except Exception as e:
        lines.append(path + ' error ' + repr(e)[:80])
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/shape_bbox_probe.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('shape bbox probe written')
