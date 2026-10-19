# 在 TD 的 Textport 里运行（只读）：看 Kantan 的输出 / 窗口读的画面 到底是不是黑的 -> td_live/kantan_out_probe.txt
import json
lines = []
p = op('/project1')
try:
    with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/gaze_bridge/audio_fx.json', encoding='utf-8') as f:
        c = json.load(f)
    lines.append('config mapping_on=' + str(c.get('mapping_on')) + ' win_display=' + str(c.get('win_display')))
except Exception as e:
    lines.append('config read error ' + repr(e)[:80])
lines.append('gz_win.winop=' + str(p.op('gz_win').par.winop.eval()) + '  display=' + str(p.op('gz_win').par.display.eval()))
for path in ('/project1/kantanMapper/out1', '/project1/kantanMapper/out2', '/project1/map_sel', '/project1/map_fit', '/project1/gz_final', '/project1/hand_out'):
    o = op(path)
    if o is None:
        lines.append(path + ': NOT FOUND')
        continue
    try:
        a = o.numpyArray()
        lines.append(path + ' size=' + str(o.width) + 'x' + str(o.height) + ' mean rgba=' + str([round(float(a[:, :, i].mean()), 3) for i in range(4)]))
    except Exception as e:
        lines.append(path + ' numpy error ' + repr(e)[:100])
shapes = []
for c_ in op('/project1/kantanMapper/project/allShapes').children:
    pr = c_.op('parameters')
    if pr is not None and hasattr(pr.par, 'Texture'):
        v = pr.par.Texture.eval()
        shapes.append((str(pr.par.Name.eval()), str(getattr(v, 'path', v)), str(pr.par.Showtexture.eval())))
lines.append('shapes (name, texture, showtexture): ' + str(shapes))
with open('/Users/shanzeyang/Desktop/I can Here You/ai-thesis/td_live/kantan_out_probe.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print('kantan out probe written')
