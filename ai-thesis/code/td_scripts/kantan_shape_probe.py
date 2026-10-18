# 在 TD 的 Textport 里运行（只读）：-> td_live/kantan_shape_probe.txt
lines = []
p = op('/project1')
o = p.op('gz_over')
try:
    a = o.numpyArray()
    lines.append('gz_over size=' + str(o.width) + 'x' + str(o.height) + ' mean rgba=' + str([round(float(a[:, :, i].mean()), 3) for i in range(4)]))
except Exception as e:
    lines.append('gz_over read error ' + repr(e)[:100])
k = p.op('kantanMapper')
try:
    for c in k.op('project').findChildren(depth=3):
        names = [pp.name for pp in c.customPars]
        if any(n.lower() in ('texture', 'showtexture') for n in names):
            d = {}
            for pp in c.customPars:
                if pp.name.lower() in ('name', 'texture', 'showtexture', 'textureid', 'color', 'colorr', 'fliptexture', 'textureorientation', 'type', 'visible', 'layer'):
                    try:
                        d[pp.name] = pp.eval()
                    except Exception:
                        pass
            lines.append('SHAPE ' + c.path + ' ' + str(d))
except Exception as e:
    lines.append('shape scan error ' + repr(e)[:120])
for nm in ('out1', 'out2'):
    t = k.op(nm)
    try:
        a = t.numpyArray()
        lines.append(nm + ' size=' + str(t.width) + 'x' + str(t.height) + ' mean rgb=' + str([round(float(a[:, :, i].mean()), 3) for i in range(3)]))
    except Exception as e:
        lines.append(nm + ' error ' + repr(e)[:100])
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/kantan_shape_probe.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('kantan shape probe written')
