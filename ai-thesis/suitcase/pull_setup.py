# 在 TD 的 Textport 里运行：入侵时两张脸之间的"电视机故障拉扯"。需要一个盖满整张画布的形状来显示它（默认 item15）
PULL = 'item15'
RIGHT = 'item19'     # 右边那张一直说话的脸
LEFTM = 'item18'     # 左边挂着的面具
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
p = op('/project1')
boxes = {}
shp = None
for c in op('/project1/kantanMapper/project/allShapes').children:
    pr = c.op('parameters')
    if pr is None or not hasattr(pr.par, 'Texture'):
        continue
    if c.name in (RIGHT, LEFTM):
        pts = [(q.x, q.y) for q in c.op('script1').points]
        x0, x1 = 960.0 + min(q[0] for q in pts), 960.0 + max(q[0] for q in pts)
        y0, y1 = 540.0 - max(q[1] for q in pts), 540.0 - min(q[1] for q in pts)
        boxes[c.name] = ((x0 + x1) / 2.0 / 1920.0, 1.0 - (y0 + y1) / 2.0 / 1080.0, (y1 - y0) / 2.0 / 1080.0)
    if c.name == PULL:
        shp = c
if shp is None or len(boxes) != 2:
    print('找不到形状：', PULL, RIGHT, LEFTM, '（找到的：', list(boxes), '）')
else:
    pl = p.op('sc_pull') or p.create(glslTOP, 'sc_pull')
    pl.inputConnectors[0].connect(p.op('mask_R'))
    pl.par.outputresolution = 'custom'
    pl.par.resolutionw = 1920
    pl.par.resolutionh = 1080
    pl.par.vec0name = 'uP'
    pl.par.vec0valuex, pl.par.vec0valuey = boxes[RIGHT][0], boxes[RIGHT][1]
    pl.par.vec0valuez, pl.par.vec0valuew = boxes[LEFTM][0], boxes[LEFTM][1]
    pl.par.vec1name = 'uQ'
    pl.par.vec1valuex, pl.par.vec1valuey = boxes[RIGHT][2], boxes[LEFTM][2]
    pl.par.vec1valuez = 0.0
    pl.par.vec1valuew = 0.0
    px = p.op('sc_pull_pixel')
    if px is not None:
        px.text = open(BASE + '/pull_shader.glsl', encoding='utf-8').read()
    pl.nodeX, pl.nodeY = 1500, -3200
    par = shp.op('parameters').par
    cur = par.Texture.eval()
    cur = str(getattr(cur, 'path', cur))
    if cur != '/project1/sc_pull':
        p.store('sc_prev_pull', (shp.name, cur))
    par.Texture = '/project1/sc_pull'
    par.Showtexture = True
    shp.par.render = True
    print('OK: 拉扯特效已接到', PULL, '| 右脸中心', [round(v, 3) for v in boxes[RIGHT]], '左面具中心', [round(v, 3) for v in boxes[LEFTM]])
