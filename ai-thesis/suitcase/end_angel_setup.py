# 在 TD 的 Textport 里运行：给第 7 天结尾准备"巨大的天使"（只建天使本身 sc_endangel；放在哪由你在 Kantan 里画的长方形决定，见 end_angel_shape.py）。
# 如果之前运行过旧版（把右墙字幕改成了 sc_subfx），这里会先还原回 sc_sub 再删掉 sc_subfx。
BASE = '/Users/shanzeyang/Desktop/I can Here You/ai-thesis/suitcase'
import os
p = op('/project1')
sub, fx = p.op('sc_sub'), p.op('sc_subfx')
if fx is not None and sub is not None:
    for c in op('/project1/kantanMapper/project/allShapes').children:
        sp = c.op('parameters')
        if sp is not None and hasattr(sp.par, 'Texture'):
            cur = sp.par.Texture.eval()
            if str(getattr(cur, 'path', cur)) == fx.path:
                sp.par.Texture = sub.path
                print('右墙字幕', c.name, '已改回显示 sc_sub')
    fx.destroy()
img = p.op('sc_ang_img') or p.create(moviefileinTOP, 'sc_ang_img')
img.par.file = os.path.normpath(BASE + '/../assets/angel/wings_pixel_base.png')
ea = p.op('sc_endangel') or p.create(glslTOP, 'sc_endangel')
ea.inputConnectors[0].connect(img)
ea.par.outputresolution = 'custom'
ea.par.resolutionw = 1080
ea.par.resolutionh = 1080
ea.par.vec0name = 'uA'
ea.par.vec1name = 'uB'
ea.par.vec0valuex = 1.0           # 形状宽高比（end_angel_shape.py 会按你画的长方形改）
ea.par.vec0valuey = 0.0
ea.par.vec0valuez = 0.0           # 警报 0 = 白色天使
ea.par.vec0valuew = 0.0           # 整体亮度 0 = 看不见（结尾才亮）
ea.par.vec1valuex = 0.5
ea.par.vec1valuey = 0.5
ea.par.vec1valuez = 1.3           # 天使大小倍数（end_angel_size）
ea.par.vec1valuew = 0.0
px = p.op('sc_endangel_pixel')
if px is not None:
    px.text = open(BASE + '/angel_shader.glsl', encoding='utf-8').read()
ea.nodeX, ea.nodeY = 1700, -3600
er = str(ea.errors() or '').strip()
print('OK: 天使着色器有错：' + er[:300] if er else 'OK: sc_endangel 已建好，没有着色器报错。接下来：在 Kantan 里画长方形并改名为 endangel，然后运行 end_angel_shape.py')
