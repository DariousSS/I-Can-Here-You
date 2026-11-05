# 在 TD 的 Textport 里运行：做红蓝格子纹理，并贴到被子 Kantan（sc_bedkantan）里的两个形状上：
#   「格子初始」= 待机/封面时铺满的红蓝格子（门打开、游戏开始后消失）
#   「行李箱」   = 手在盖子房间里碰到行李箱时，这个形状亮一下
# 新建：sc_checker（格子）、sc_chk_main（给格子初始，亮度由游戏控制）、sc_chk_suit（给行李箱，亮度由游戏控制）。运行后请再运行一次 game_td_setup.py 让游戏代码生效。
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
p = op('/project1')
ck = p.op('sc_checker') or p.create(glslTOP, 'sc_checker')
ck.par.outputresolution = 'custom'
ck.par.resolutionw = 1920
ck.par.resolutionh = 1200
try:
    ck.seq.vec.numBlocks = 1
except Exception as e:
    print('vec 序列设置失败：', repr(e)[:80])
ck.par.vec0name = 'uC'
ck.par.vec0valuex, ck.par.vec0valuey, ck.par.vec0valuez = 14.0, 1.0, 0.0
ck.nodeX, ck.nodeY = 3200, -4600
px = p.op('sc_checker_pixel')
if px is not None:
    px.text = open(BASE + '/checker_shader.glsl', encoding='utf-8').read()
er = str(ck.errors() or '').strip()
print('sc_checker 着色器报错：' + er[:300] if er else 'sc_checker 着色器没有报错')
for name, nx in (('sc_chk_main', 3400), ('sc_chk_suit', 3600)):
    lv = p.op(name) or p.create(levelTOP, name)
    lv.nodeX, lv.nodeY = nx, -4600
    lv.inputConnectors[0].connect(ck)
    lv.par.brightness1 = 0.0
shapes = op('/project1/sc_bedkantan/kantanMapper/project/allShapes').findChildren(maxDepth=4)
for shape_name, tex in (('行李箱', '/project1/sc_chk_suit'),):       # 「格子初始」不贴纹理，显示 Kantan 自带的测试线框
    hit = None
    for s in shapes:
        sp = s.op('parameters')
        if sp is not None and hasattr(sp.par, 'Name') and str(sp.par.Name.eval()).strip() == shape_name:
            hit = sp
    if hit is None:
        print('没找到名字叫「' + shape_name + '」的形状，跳过')
    else:
        hit.par.Texture = tex
        hit.par.Showtexture = True
        print('OK: 形状「' + shape_name + '」的纹理 =', tex)
