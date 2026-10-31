# 在 TD 的 Textport 里运行：在左边的形状（默认 item4，云朵所在的那个）里放一个天使，平时白色安静，到了"从来没有发生"那一句变大变红
# 做法：新建三个节点 sc_ang_img（天使底图）-> sc_angel（画天使）-> sc_left（天使叠在云朵上面），再把 item4 的纹理改成 sc_left。可随时用 angel_undo.py 还原
SHAPE = 'item4'
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
import os
p = op('/project1')
shp = None
for c in op('/project1/kantanMapper/project/allShapes').children:
    if c.name == SHAPE and c.op('parameters') is not None and hasattr(c.op('parameters').par, 'Texture'):
        shp = c
if shp is None:
    print('找不到形状', SHAPE)
elif p.op('sc_blob') is None:
    print('找不到 sc_blob（云朵）：请先把云朵装好')
else:
    img = p.op('sc_ang_img') or p.create(moviefileinTOP, 'sc_ang_img')
    img.par.file = os.path.normpath(BASE + '/../assets/angel/wings_pixel_base.png')
    img.nodeX, img.nodeY = 1500, -3400
    ag = p.op('sc_angel') or p.create(glslTOP, 'sc_angel')
    ag.inputConnectors[0].connect(img)
    ag.par.outputresolution = 'custom'
    ag.par.resolutionw = 1920
    ag.par.resolutionh = 1080
    ag.par.vec0name = 'uA'
    ag.par.vec1name = 'uB'
    ag.par.vec0valuex = 1.0
    ag.par.vec0valuey = 0.0
    ag.par.vec0valuez = 0.0
    ag.par.vec0valuew = 0.55
    ag.par.vec1valuex = 0.5
    ag.par.vec1valuey = 0.0
    ag.par.vec1valuez = 0.95
    ag.par.vec1valuew = 0.0
    px = p.op('sc_angel_pixel')
    if px is not None:
        px.text = open(BASE + '/angel_shader.glsl', encoding='utf-8').read()
    ag.nodeX, ag.nodeY = 1700, -3400
    lf = p.op('sc_left') or p.create(overTOP, 'sc_left')
    lf.inputConnectors[0].connect(ag)
    lf.inputConnectors[1].connect(p.op('sc_blob'))
    lf.nodeX, lf.nodeY = 1900, -3400
    par = shp.op('parameters').par
    cur = par.Texture.eval()
    cur = str(getattr(cur, 'path', cur))
    if cur != '/project1/sc_left':
        p.store('sc_prev_left', (shp.name, cur))
    par.Texture = '/project1/sc_left'
    par.Showtexture = True
    shp.par.render = True
    er = str(ag.errors() or '').strip()
    print('OK: 天使已放进', SHAPE, '（叠在云朵上面）')
    if er:
        print('但天使着色器有错：', er[:300])
    else:
        print('着色器编译没有报错。接下来重新运行一次 suitcase_setup.py，让天使会听字幕的"警报"')
